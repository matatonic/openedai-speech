#!/bin/bash

URL=${1:-http://localhost:8000/v1/audio/speech}

curl -s $URL -H "Content-Type: application/json" -d "{
    \"model\": \"tts-1\",
    \"input\": \"I'm going to play you the original voice, followed by the piper voice and finally the X T T S version 2 voice\",
    \"voice\": \"echo\",
    \"speed\": 1.0
  }" | mpv --really-quiet -

for voice in alloy echo fable onyx nova shimmer ; do

echo $voice

curl -s $URL -H "Content-Type: application/json" -d "{
    \"model\": \"tts-1\",
    \"input\": \"original\",
    \"voice\": \"echo\",
    \"speed\": 1.0
  }" | mpv --really-quiet -

curl -s https://cdn.openai.com/API/docs/audio/$voice.wav | mpv --really-quiet -

curl -s $URL -H "Content-Type: application/json" -d "{
    \"model\": \"tts-1\",
    \"input\": \"The quick brown fox jumped over the lazy dog. This voice is called $voice, how do you like this voice?\",
    \"voice\": \"$voice\",
    \"speed\": 1.0
  }" | mpv --really-quiet -

curl -s $URL -H "Content-Type: application/json" -d "{
    \"model\": \"tts-1-hd\",
    \"input\": \"The quick brown fox jumped over the lazy dog. This HD voice is called $voice, how do you like this voice?\",
    \"voice\": \"$voice\",
    \"speed\": 1.0
  }" | mpv --really-quiet -

done

curl -s $URL -H "Content-Type: application/json" -d "{
    \"model\": \"tts-1\",
    \"input\": \"the slowest voice\",
    \"voice\": \"onyx\",
    \"speed\": 0.25
  }" | mpv --really-quiet -

curl -s $URL -H "Content-Type: application/json" -d "{
    \"model\": \"tts-1-hd\",
    \"input\": \"the slowest HD voice\",
    \"voice\": \"onyx\",
    \"speed\": 0.25
  }" | mpv --really-quiet -

curl -s $URL -H "Content-Type: application/json" -d "{
    \"model\": \"tts-1\",
    \"input\": \"And this is how fast it can go, the fastest voice\",
    \"voice\": \"nova\",
    \"speed\": 4.0
  }" | mpv --really-quiet -

curl -s $URL -H "Content-Type: application/json" -d "{
    \"model\": \"tts-1-hd\",
    \"input\": \"And this is how fast it can go, the fastest HD voice\",
    \"voice\": \"nova\",
    \"speed\": 4.0
  }" | mpv --really-quiet -
