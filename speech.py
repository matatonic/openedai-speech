#!/usr/bin/env python3
import argparse
import contextlib
import gc
import os
import queue
import re
import subprocess
import sys
import threading
import time
import yaml
import json

from fastapi.responses import StreamingResponse
from loguru import logger
from openedai import OpenAIStub, BadRequestError, ServiceUnavailableError
from pydantic import BaseModel
import uvicorn

@contextlib.asynccontextmanager
async def lifespan(app):
    yield
    gc.collect()
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()
    except:
        pass

app = OpenAIStub(lifespan=lifespan)
xtts = None
args = None

def unload_model():
    import torch, gc
    global xtts
    if xtts:
        logger.info("Unloading model")
        xtts.xtts.to('cpu') # this was required to free up GPU memory... 
        del xtts
        xtts = None
        gc.collect()
        torch.cuda.empty_cache()
        torch.cuda.ipc_collect()

class xtts_wrapper():
    check_interval: int = 1 # too aggressive?

    def __init__(self, model_name, device, model_path=None, unload_timer=None):
        self.model_name = model_name
        self.unload_timer = unload_timer
        self.last_used = time.time()
        self.timer = None
        self.lock = threading.Lock()

        logger.info(f"Loading model {self.model_name} to {device}")

        if model_path is None:
            model_path = ModelManager().download_model(model_name)[0]

        config_path = os.path.join(model_path, 'config.json')
        config = XttsConfig()
        config.load_json(config_path)
        self.xtts = Xtts.init_from_config(config)
        self.xtts.load_checkpoint(config, checkpoint_dir=model_path, use_deepspeed=args.use_deepspeed)  # XXX there are no prebuilt deepspeed wheels??
        self.xtts = self.xtts.to(device=device)
        self.xtts.eval()

        if self.unload_timer:
            logger.info(f"Setting unload timer to {self.unload_timer} seconds")
            self.last_used = time.time()
            self.check_idle()

    def check_idle(self):
        with self.lock:
            if time.time() - self.last_used >= self.unload_timer:
                print("Unloading TTS model due to inactivity")
                unload_model()
            else:
                # Reschedule the check
                self.timer = threading.Timer(self.check_interval, self.check_idle)
                self.timer.daemon = True
                self.timer.start()

    def tts(self, text, language, audio_path, **hf_generate_kwargs):
        with torch.no_grad():
            self.last_used = time.time()
            tokens = 0
            try:
                with self.lock:
                    logger.debug(f"generating [{language}]: {[text]}")

                    gpt_cond_latent, speaker_embedding = self.xtts.get_conditioning_latents(audio_path=audio_path) # not worth caching calls, it's < 0.001s after model is loaded
                    pcm_stream = self.xtts.inference_stream(text, language, gpt_cond_latent, speaker_embedding, **hf_generate_kwargs)
                    self.last_used = time.time()

                while True:
                    with self.lock:
                        yield next(pcm_stream).cpu().numpy().tobytes()
                        self.last_used = time.time()
                    tokens += 1

            except StopIteration:
                pass

            finally:
                logger.debug(f"Generated {tokens} tokens in {time.time() - self.last_used:.2f}s @ {tokens / (time.time() - self.last_used):.2f} T/s")
                self.last_used = time.time()

def default_exists(filename: str):
    if not os.path.exists(filename):
        fpath, ext = os.path.splitext(filename)
        basename = os.path.basename(fpath)
        default = f"{basename}.default{ext}"
        
        logger.info(f"{filename} does not exist, setting defaults from {default}")

        with open(default, 'r', encoding='utf8') as from_file:
            with open(filename, 'w', encoding='utf8') as to_file:
                to_file.write(from_file.read())

# Read pre process map on demand so it can be changed without restarting the server
def preprocess(raw_input):
    #logger.debug(f"preprocess: before: {[raw_input]}")
    default_exists('config/pre_process_map.yaml')
    with open('config/pre_process_map.yaml', 'r', encoding='utf8') as file:
        pre_process_map = yaml.safe_load(file)
        for a, b in pre_process_map:
            raw_input = re.sub(a, b, raw_input)
    
    raw_input = raw_input.strip()
    #logger.debug(f"preprocess: after: {[raw_input]}")
    return raw_input

# Read voice map on demand so it can be changed without restarting the server
def map_voice_to_speaker(voice: str, model: str):
    default_exists('config/voice_to_speaker.yaml')
    with open('config/voice_to_speaker.yaml', 'r', encoding='utf8') as file:
        voice_map = yaml.safe_load(file)
        try:
            return voice_map[model][voice]

        except KeyError as e:
            raise BadRequestError(f"Error loading voice: {voice}, KeyError: {e}", param='voice')

class GenerateSpeechRequest(BaseModel):
    model: str = "tts-1" # or "tts-1-hd"
    input: str
    voice: str = "alloy"  # alloy, echo, fable, onyx, nova, and shimmer
    response_format: str = "mp3" # mp3, opus, aac, flac
    speed: float = 1.0 # 0.25 - 4.0

def build_ffmpeg_args(response_format, input_format, sample_rate):
    # Convert the output to the desired format using ffmpeg
    if input_format == 'WAV':
        ffmpeg_args = ["ffmpeg", "-loglevel", "error", "-f", "WAV", "-i", "-"]
    else:
        ffmpeg_args = ["ffmpeg", "-loglevel", "error", "-f", input_format, "-ar", sample_rate, "-ac", "1", "-i", "-"]
    
    if response_format == "mp3":
        ffmpeg_args.extend(["-f", "mp3", "-c:a", "libmp3lame", "-ab", "64k"])
    elif response_format == "opus":
        ffmpeg_args.extend(["-f", "ogg", "-c:a", "libopus"])
    elif response_format == "aac":
        ffmpeg_args.extend(["-f", "adts", "-c:a", "aac", "-ab", "64k"])
    elif response_format == "flac":
        ffmpeg_args.extend(["-f", "flac", "-c:a", "flac"])
    elif response_format == "wav":
        ffmpeg_args.extend(["-f", "wav", "-c:a", "pcm_s16le"])
    elif response_format == "pcm": # even though pcm is technically 'raw', we still use ffmpeg to adjust the speed
        ffmpeg_args.extend(["-f", "s16le", "-c:a", "pcm_s16le"])

    return ffmpeg_args

@app.post("/v1/audio/speech", response_class=StreamingResponse)
async def generate_speech(request: GenerateSpeechRequest):
    global xtts, args
    if len(request.input) < 1:
        raise BadRequestError("Empty Input", param='input')

    input_text = preprocess(request.input)

    if len(input_text) < 1:
        raise BadRequestError("Input text empty after preprocess.", param='input')

    model = request.model
    voice = request.voice
    response_format = request.response_format.lower()
    speed = request.speed

    # Set the Content-Type header based on the requested format
    if response_format == "mp3":
        media_type = "audio/mpeg"
    elif response_format == "opus":
        media_type = "audio/ogg;codec=opus" # codecs?
    elif response_format == "aac":
        media_type = "audio/aac"
    elif response_format == "flac":
        media_type = "audio/x-flac"
    elif response_format == "wav":
        media_type = "audio/wav"
    elif response_format == "pcm":
        if model == 'tts-1': # piper
            media_type = "audio/pcm;rate=22050"
        elif model == 'tts-1-hd': # xtts
            media_type = "audio/pcm;rate=24000"
    else:
        raise BadRequestError(f"Invalid response_format: '{response_format}'", param='response_format')

    ffmpeg_args = None

    # Use piper for tts-1, and if xtts_device == none use for all models.
    if model == 'tts-1' or args.xtts_device == 'none':
        voice_map = map_voice_to_speaker(voice, 'tts-1')
        try:
            piper_model = voice_map['model']

        except KeyError as e:
            raise ServiceUnavailableError(f"Configuration error: tts-1 voice '{voice}' is missing 'model:' setting. KeyError: {e}")

        speaker = voice_map.get('speaker', None)

        tts_args = ["piper", "--model", str(piper_model), "--data-dir", "voices", "--download-dir", "voices", "--output-raw"]
        if speaker:
            tts_args.extend(["--speaker", str(speaker)])
        if speed != 1.0:
            tts_args.extend(["--length-scale", f"{1.0/speed}"])

        tts_proc = subprocess.Popen(tts_args, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        tts_proc.stdin.write(bytearray(input_text.encode('utf-8')))
        tts_proc.stdin.close()

        try:
            with open(f"{piper_model}.json", 'r') as pvc_f:
                conf = json.load(pvc_f)
                sample_rate = str(conf['audio']['sample_rate'])

        except:
            sample_rate = '22050'
  
        ffmpeg_args = build_ffmpeg_args(response_format, input_format="s16le", sample_rate=sample_rate)

        # Pipe the output from piper/xtts to the input of ffmpeg
        ffmpeg_args.extend(["-"])
        ffmpeg_proc = subprocess.Popen(ffmpeg_args, stdin=tts_proc.stdout, stdout=subprocess.PIPE)

        return StreamingResponse(content=ffmpeg_proc.stdout, media_type=media_type)
    # Use xtts for tts-1-hd
    elif model == 'tts-1-hd':
        voice_map = map_voice_to_speaker(voice, 'tts-1-hd')
        try:
            tts_model = voice_map.pop('model')
            speaker = voice_map.pop('speaker')

        except KeyError as e:
            raise ServiceUnavailableError(f"Configuration error: tts-1-hd voice '{voice}' is missing setting. KeyError: {e}")

        if xtts and xtts.model_name != tts_model:
            unload_model()

        tts_model_path = voice_map.pop('model_path', None) # XXX changing this on the fly is ignored if you keep the same name

        if xtts is None:
            xtts = xtts_wrapper(tts_model, device=args.xtts_device, model_path=tts_model_path, unload_timer=args.unload_timer)

        ffmpeg_args = build_ffmpeg_args(response_format, input_format="f32le", sample_rate="24000")

        # tts speed doesn't seem to work well
        speed = voice_map.pop('speed', speed)
        if speed < 0.5:
            speed = speed / 0.5
            ffmpeg_args.extend(["-af", "atempo=0.5"]) 
        if speed > 1.0:
            ffmpeg_args.extend(["-af", f"atempo={speed}"]) 
            speed = 1.0

        # Pipe the output from piper/xtts to the input of ffmpeg
        ffmpeg_args.extend(["-"])

        language = voice_map.pop('language', 'auto')
        if language == 'auto':
            try:
                language = detect(input_text)
                if language not in [
                    'en', 'es', 'fr', 'de', 'it', 'pt', 'pl', 'tr',
                    'ru', 'nl', 'cs', 'ar', 'zh-cn', 'hu', 'ko', 'ja', 'hi'
                ]:
                    logger.debug(f"Detected language {language} not supported, defaulting to en")
                    language = 'en'
                else:
                    logger.debug(f"Detected language: {language}")
            except:
                language = 'en'
                logger.debug(f"Failed to detect language, defaulting to en")

        comment = voice_map.pop('comment', None) # ignored.

        hf_generate_kwargs = dict(
            speed=speed,
            **voice_map,
        )

        hf_generate_kwargs['enable_text_splitting'] = hf_generate_kwargs.get('enable_text_splitting', True) # change the default to true

        if hf_generate_kwargs['enable_text_splitting']:
            if language == 'zh-cn':
                split_lang = 'zh'
            else:
                split_lang = language
            all_text = split_sentence(input_text, split_lang, xtts.xtts.tokenizer.char_limits[split_lang])
        else:
            all_text = [input_text]

        ffmpeg_proc = subprocess.Popen(ffmpeg_args, stdin=subprocess.PIPE, stdout=subprocess.PIPE)

        in_q = queue.Queue() # speech pcm 
        ex_q = queue.Queue() # exceptions

        def get_speaker_samples(samples: str) -> list[str]:
            if os.path.isfile(samples):
                audio_path = [samples]
            elif os.path.isdir(samples):
                audio_path = [os.path.join(samples, sample) for sample in os.listdir(samples) if os.path.isfile(os.path.join(samples, sample))]

                if len(audio_path) < 1:
                    logger.error(f"No files found: {samples}")
                    raise ServiceUnavailableError(f"Invalid path: {samples}")
            else:
                logger.error(f"Invalid path: {samples}")
                raise ServiceUnavailableError(f"Invalid path: {samples}")
            
            return audio_path

        def exception_check(exq: queue.Queue):
            try:
                e = exq.get_nowait()
            except queue.Empty:
                return
            
            raise e

        def generator():
            # text -> in_q

            audio_path = get_speaker_samples(speaker)
            logger.debug(f"{voice} wav samples: {audio_path}")

            try:
                for text in all_text:
                    for chunk in xtts.tts(text=text, language=language, audio_path=audio_path, **hf_generate_kwargs):
                        exception_check(ex_q)
                        in_q.put(chunk)

            except BrokenPipeError as e: # client disconnect lands here
                logger.info("Client disconnected - 'Broken pipe'")

            except Exception as e:
                logger.error(f"Exception: {repr(e)}")
                raise e
        
            finally:
                in_q.put(None) # sentinel

        def out_writer(): 
            # in_q -> ffmpeg
            try:
                while True:
                    chunk = in_q.get()
                    if chunk is None: # sentinel
                        break
                    ffmpeg_proc.stdin.write(chunk) # BrokenPipeError from here on client disconnect

            except Exception as e: # BrokenPipeError
                ex_q.put(e)  # we need to get this exception into the generation loop
                ffmpeg_proc.kill()
                return
            
            finally:
                ffmpeg_proc.stdin.close()

        generator_worker = threading.Thread(target=generator, daemon=True)
        generator_worker.start()

        out_writer_worker = threading.Thread(target=out_writer, daemon=True)
        out_writer_worker.start()

        def cleanup():
            ffmpeg_proc.kill()
            del generator_worker
            del out_writer_worker

        return StreamingResponse(content=ffmpeg_proc.stdout, media_type=media_type, background=cleanup)
    else:
        raise BadRequestError("No such model, must be tts-1 or tts-1-hd.", param='model')


# We return 'mps' but currently XTTS will not work with mps devices as the cuda support is incomplete
def auto_torch_device():
    try:
        import torch
        return 'cuda' if torch.cuda.is_available() else 'mps' if ( torch.backends.mps.is_available() and torch.backends.mps.is_built() ) else 'cpu'
    
    except:
        return 'none'

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='OpenedAI Speech API Server',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('--xtts_device', action='store', default=auto_torch_device(), help="Set the device for the xtts model. The special value of 'none' will use piper for all models.")
    parser.add_argument('--preload', action='store', default=None, help="Preload a model (Ex. 'xtts' or 'xtts_v2.0.2'). By default it's loaded on first use.")
    parser.add_argument('--unload-timer', action='store', default=None, type=int, help="Idle unload timer for the XTTS model in seconds, Ex. 900 for 15 minutes")
    parser.add_argument('--use-deepspeed', action='store_true', default=False, help="Use deepspeed with xtts (this option is unsupported)")
    parser.add_argument('--no-cache-speaker', action='store_true', default=False, help="Don't use the speaker wav embeddings cache")
    parser.add_argument('-P', '--port', action='store', default=8000, type=int, help="Server tcp port")
    parser.add_argument('-H', '--host', action='store', default='0.0.0.0', help="Host to listen on, Ex. 0.0.0.0")
    parser.add_argument('-L', '--log-level', default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], help="Set the log level")

    args = parser.parse_args()

    default_exists('config/pre_process_map.yaml')
    default_exists('config/voice_to_speaker.yaml')

    logger.remove()
    logger.add(sink=sys.stderr, level=args.log_level)

    if args.xtts_device != "none":
        import torch
        from TTS.tts.configs.xtts_config import XttsConfig
        from TTS.tts.models.xtts import Xtts
        from TTS.utils.manage import ModelManager
        from TTS.tts.layers.xtts.tokenizer import split_sentence
        from langdetect import detect

    if args.preload:
        xtts = xtts_wrapper(args.preload, device=args.xtts_device, unload_timer=args.unload_timer)

    app.register_model('tts-1')
    app.register_model('tts-1-hd')

    uvicorn.run(app, host=args.host, port=args.port)
