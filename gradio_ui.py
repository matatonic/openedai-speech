import gradio as gr
import os
import requests
import subprocess
import datetime

def process_audio(recording, voice, filter):
    os.makedirs(f'./voices/{voice}', exist_ok=True)
    now = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")
    input_file = recording
    output_file = f'./voices/{voice}/{voice}-{now}.wav'

    if (filter):
        ffmpeg_command = [
            'ffmpeg',
            '-y',
            '-i', input_file,
            '-af', 'highpass=f=200, lowpass=f=3000',
            '-ac', '1',
            '-ar', '22050',
            output_file
        ]
    else:
        ffmpeg_command = [
            'ffmpeg',
            '-y',
            '-i', input_file,
            '-ac', '1',
            '-ar', '22050',
            output_file
        ]

    try:
        subprocess.run(ffmpeg_command, check=True, capture_output=True, text=True)
        print(f"File processed and saved as {output_file}")
        return output_file
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while processing the file: {e}")
        print(f"FFmpeg error output: {e.stderr}")

def tts(voice: gr.Text, text: gr.Text, recording: gr.Audio, filter: gr.Checkbox, persist: gr.Checkbox, file: gr.FileExplorer, url: str):
    # Input validation
    if not voice or not voice.strip():
        voice = 'upload'
    if not text or not text.strip():
        text = 'You have to type something in the Text to Speech box.'

    voice = voice.lower()
    output_file = process_audio(recording, voice, filter)
    
    headers = {
        "Authorization": f"Bearer no-api-key-needed",
        "Content-Type": "application/json"
    }
    data = {
        "model": "tts-1-hd",
        "input": text,
        "voice": voice
    }
    
    url = f"{url}/v1/audio/speech"
    response = requests.post(url, headers=headers, json=data)

    # Delete sample unless chosen to commit
    if (not persist):
        os.remove(output_file)
    
    if response.status_code == 200:
        return response.content
    return None

voice = gr.Text(
    label="Voice name. Will be lowercased. No spaces.",
    info="You can use multiple recordings of the same person (same voice name) to improve quality.",
    placeholder="stephen_fry",
    autofocus=True,
    max_length=20,
    max_lines=1
)

text = gr.Text(
    label="Text to speak.",
    info="The voice recorded below, merged with preexisting ones, if any, will speak the text you enter here.",
    show_copy_button=True,
    value="Hello, nice to meet you!"
)

recording = gr.Audio(
    type="filepath",
    sources=['microphone', 'upload'],
    label="Your voice, 4-30s, avoid noise.",
    show_download_button=True,
    min_length=4,
    max_length=30
)

filter = gr.Checkbox(
    label="Noise Filter",
    info="Use as a last resort. A silent atmosphere is preferred."
)

persist = gr.Checkbox(
    label="Persist Voice",
    info="Persist the voice to disk, so it can be used elsewhere (like Open WebUI)."
)

files = gr.FileExplorer(
    label="A list of existing voices. Selecting a file has no action. This is informational, only.",
    file_count="single",
    glob="**/*.wav",
    root_dir="./voices",
    height=200
)

generated = gr.Audio(
    label="Generated Speech",
    autoplay=True,
    container=True,
    # streaming=True,
    format="mp3"
)

def gradio_app(url: str = "http://127.0.0.1:8000/v1/audio/speech") -> gr.Blocks:
    def tts_wrapper(*args):
        return tts(*args, url)

    ui = gr.Interface(
        title="Text to Speech (TTS) Tester",
        description="Enter text and record your voice to test it.",
        fn=tts_wrapper,
        inputs=[
            voice,
            text,
            recording,
            filter,
            persist,
            files
        ],
        outputs=[generated],
        allow_flagging=False
    )

    return ui