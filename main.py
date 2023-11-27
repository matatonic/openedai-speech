#!/usr/bin/env python3
import subprocess
import yaml
import re
import io
import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import uvicorn
from pydantic import BaseModel
import numpy as np
import torch
#import TTS
from TTS.api import TTS
from TTS.config import load_config
from TTS.utils.manage import ModelManager
from TTS.utils.synthesizer import Synthesizer
from TTS.utils.audio.numpy_transforms import save_wav

piper_cuda = False # onnxruntime-gpu not working for me, but cpu is fast enough
xtts_device = 'cuda'

app = FastAPI()

class FakeBufferedIO(io.BytesIO):
    def __init__(self):
        self.buffer = self

class xtts_wrapper():
    def __init__(self, model_name):

        self.xtts = TTS(model_name=model_name, progress_bar=False, gpu=True).to(xtts_device)
        """
        vocoder_path, vocoder_config_path = None, None
        tts_loc = Path(TTS.__file__).parent / '.models.json'
        manager = ModelManager(tts_loc)
        model_path, config_path, model_item = manager.download_model(model_name)
        if not config_path:
            config_path = os.path.join(model_path, "config.json")
        #print(model_path, config_path, model_item)
        #vocoder_path, vocoder_config_path, _ = manager.download_model(model_item["default_vocoder"])
        
        self.xtts_synthesizer = Synthesizer(
            tts_checkpoint=model_path,
            tts_config_path=config_path,
            #tts_speakers_file=None,
            #tts_languages_file=None,
            #vocoder_checkpoint=vocoder_path,
            #vocoder_config=vocoder_config_path,
            #encoder_checkpoint="",
            #encoder_config="",
            use_cuda=xtts_cuda,
        )

        self.use_multi_speaker = hasattr(self.xtts_synthesizer.tts_model, "num_speakers") and (
            self.xtts_synthesizer.tts_model.num_speakers > 1 or self.xtts_synthesizer.tts_speakers_file is not None
        )
        self.speaker_manager = getattr(self.xtts_synthesizer.tts_model, "speaker_manager", None)

        self.use_multi_language = hasattr(self.xtts_synthesizer.tts_model, "num_languages") and (
            self.xtts_synthesizer.tts_model.num_languages > 1 or self.xtts_synthesizer.tts_languages_file is not None
        )
        self.language_manager = getattr(self.xtts_synthesizer.tts_model, "language_manager", None)
        """

    def tts(self, text, speaker_wav, speed):
        io_ret = FakeBufferedIO()
        file_path = self.xtts.tts_to_file(
            text,
            language='en',
            speaker_wav=speaker_wav,
            speed=speed,
            pipe_out=io_ret,
        )
        
        #self.xtts.synthesizer.save_wav(wav, path='tts_output.wav', pipe_out=io_ret)
        return io_ret

xtts = xtts_wrapper("tts_models/multilingual/multi-dataset/xtts_v2")

def preprocess(raw_input):
    with open('pre_process_map.yaml', 'r') as file:
        pre_process_map = yaml.safe_load(file)
        for a, b in pre_process_map:
            raw_input = re.sub(a, b, raw_input)
    return raw_input

def map_voice_to_speaker(voice: str, model: str):
    with open('voice_to_speaker.yaml', 'r') as file:
        voice_map = yaml.safe_load(file)
        return voice_map[model][voice]['model'], voice_map[model][voice]['speaker'], 

class GenerateSpeechRequest(BaseModel):
    model: str = "tts-1" # or "tts-1-hd"
    input: str
    voice: str = "alloy"  # alloy, echo, fable, onyx, nova, and shimmer
    response_format: str = "mp3" # mp3, opus, aac, flac
    speed: float = 1.0 # 0.25 - 4.0

@app.post("/v1/audio/speech") #, response_model=StreamingResponse)
async def generate_speech(request: GenerateSpeechRequest):
    input_text = preprocess(request.input)
    model = request.model
    voice = request.voice
    response_format = request.response_format
    speed = request.speed

    # Set the Content-Type header based on the requested format
    if response_format == "mp3":
        media_type = "audio/mpeg"
    elif response_format == "opus":
        media_type = "audio/ogg;codecs=opus"
    elif response_format == "aac":
        media_type = "audio/aac"
    elif response_format == "flac":
        media_type = "audio/x-flac"

    # Convert the output to the desired format using ffmpeg
    ffmpeg_args = ["ffmpeg", "-loglevel", "error", "-f", "s16le", "-ar", "22050", "-ac", "1", "-i", "-"]

    if response_format == "mp3":
        ffmpeg_args.extend(["-f", "mp3", "-c:a", "libmp3lame", "-ab", "64k"]) # 32k or 64k?
    elif response_format == "opus":
        ffmpeg_args.extend(["-f", "ogg", "-c:a", "libopus"])
    elif response_format == "aac":
        ffmpeg_args.extend(["-f", "adts", "-c:a", "aac", "-ab", "64k"])
    elif response_format == "flac":
        ffmpeg_args.extend(["-f", "flac", "-c:a", "flac"])
     #"-hwaccel:auto"

    tts_io_out = None

    if model == 'tts-1':
        piper_model, speaker = map_voice_to_speaker(voice, model)
        tts_args = ["piper", "--model", str(piper_model), "--data-dir", "voices", "--download-dir", "voices", "--output-raw"]
        if piper_cuda:
            tts_args.extend(["--cuda"])
        if speaker:
            tts_args.extend(["--speaker", str(speaker)])
        if speed != 1.0:
            tts_args.extend(["--length-scale", f"{1.0/speed}"])

        tts_proc = subprocess.Popen(tts_args, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        tts_proc.stdin.write(bytearray(input_text.encode('utf-8')))
        tts_proc.stdin.close()
        tts_io_out = tts_proc.stdout
        
    elif model == 'tts-1-hd':
        tts_model, speaker = model, speaker = map_voice_to_speaker(voice, model)

        #tts_args = ["tts", "--text", input_text, "--use_cuda", "USE_CUDA", "--model_name", str(tts_model), "--language_idx", "en", "--pipe_out" ]
        #if speaker:
        #    tts_args.extend(["--speaker_wav", str(speaker)])
        if speed > 2.0: # tts has a max speed of 2.0
            ffmpeg_args.extend(["-af", "atempo=2.0"]) 
            speed = min(speed / 2.0, 2.0)
        #if speed != 1.0:
        #     tts_args.extend(["--speed", str(speed)])
        if speed == 1.0:
            speed = None

        tts_io_out = xtts.tts(text=input_text, speaker_wav=speaker, speed=speed)
        
#        if torch.is_tensor(wav):
#            wav = wav.cpu().numpy()
#        if isinstance(wav, list):
#            wav = np.array(wav)

        #tts_io_out = io.BytesIO()
        #save_wav(wav, tts_io_out)
        
        #tts_proc = subprocess.Popen(tts_args, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    
    # Pipe the output from piper to the input of ffmpeg
    ffmpeg_args.extend(["-"])
    ffmpeg_proc = subprocess.Popen(ffmpeg_args, stdin=tts_io_out, stdout=subprocess.PIPE)

    #print(" ".join(tts_args))
    #print(" ".join(ffmpeg_args))

    return StreamingResponse(content=ffmpeg_proc.stdout, media_type=media_type)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) # , root_path=cwd, access_log=False, log_level="info", ssl_keyfile="cert.pem", ssl_certfile="cert.pem")