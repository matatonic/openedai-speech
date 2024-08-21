@echo off
for %%i in (alloy echo fable onyx nova shimmer) do (
    if not exist "voices\%%i.wav" (
        curl -s https://cdn.openai.com/API/docs/audio/%%i.wav | ffmpeg -loglevel error -i - -ar 22050 -ac 1 voices\%%i.wav
    )
)


for %%i in (sky juniper cove ember breeze) do (
    if not exist "voices\%%i.wav" (
        curl -s https://cdn.openai.com/new-voice-and-image-capabilities-in-chatgpt/hd/speech-%%i.mp3 | ffmpeg -loglevel error -i - -ar 22050 -ac 1 voices\%%i.wav
    )
)
