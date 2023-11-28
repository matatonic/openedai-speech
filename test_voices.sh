#!/bin/sh

curl -s http://localhost:8000/v1/audio/speech  -H "Content-Type: application/json"   -d "{
    \"model\": \"tts-1\",
    \"input\": \"I'm going to play you the original voice, followed by the piper voice and finally the X T T S version 2 voice\",
    \"voice\": \"echo\",
    \"speed\": 1.0
  }" | mpv --really-quiet -

for voice in  alloy echo fable onyx nova shimmer ; do

echo $voice

curl -s http://localhost:8000/v1/audio/speech  -H "Content-Type: application/json"   -d "{
    \"model\": \"tts-1\",
    \"input\": \"original\",
    \"voice\": \"echo\",
    \"speed\": 1.0
  }" | mpv --really-quiet -

wget -q https://cdn.openai.com/API/docs/audio/$voice.wav -O - | mpv --really-quiet -

curl -s http://localhost:8000/v1/audio/speech  -H "Content-Type: application/json"   -d "{
    \"model\": \"tts-1\",
    \"input\": \"The quick brown fox jumped over the lazy dog. This voice is called $voice, how do you like this voice?\",
    \"voice\": \"$voice\",
    \"speed\": 1.0
  }" | mpv --really-quiet -

curl -s http://localhost:8000/v1/audio/speech  -H "Content-Type: application/json"   -d "{
    \"model\": \"tts-1-hd\",
    \"input\": \"The quick brown fox jumped over the lazy dog. This HD voice is called $voice, how do you like this voice?\",
    \"voice\": \"$voice\",
    \"speed\": 1.0
  }" | mpv --really-quiet -

done

