#!/usr/bin/env python3
import subprocess
import yaml
import re
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import uvicorn
from pydantic import BaseModel

piper_cuda = False # onnxruntime-gpu not working for me, but cpu is fast enough

app = FastAPI()

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

    tts_args = []
    tts_proc = None

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
    elif model == 'tts-1-hd':
        #tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2", progress_bar=False).to(device)
        #tts.tts_to_file(text=ttstext, file_path=output_filename, speaker_wav=self.speaker_wav)
        tts_model, speaker = model, speaker = map_voice_to_speaker(voice, model)
        tts_args = ["tts", "--text", input_text, "--use_cuda", "USE_CUDA", "--model_name", str(tts_model), "--language_idx", "en", "--pipe_out" ]
        if speaker:
            tts_args.extend(["--speaker_wav", str(speaker)])
        if speed > 2.0: # tts has a max speed of 2.0
            ffmpeg_args.extend(["-af", "atempo=2.0"]) 
            speed = min(speed / 2.0, 2.0)
        if speed != 1.0:
             tts_args.extend(["--speed", str(speed)])

        tts_proc = subprocess.Popen(tts_args, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    
    # Pipe the output from piper to the input of ffmpeg
    ffmpeg_args.extend(["-"])
    ffmpeg_proc = subprocess.Popen(ffmpeg_args, stdin=tts_proc.stdout, stdout=subprocess.PIPE)
    tts_proc.stdin.close()

    #print(" ".join(tts_args))
    #print(" ".join(ffmpeg_args))

    return StreamingResponse(content=ffmpeg_proc.stdout, media_type=media_type)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) # , root_path=cwd, access_log=False, log_level="info", ssl_keyfile="cert.pem", ssl_certfile="cert.pem")