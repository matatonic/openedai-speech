#!/bin/sh
# default openai voices
for i in alloy echo fable onyx nova shimmer; do
	[ ! -e "voices/$i.wav" ] && curl -s https://cdn.openai.com/API/docs/audio/$i.wav | ffmpeg -loglevel error -i - -ar 22050 -ac 1 voices/$i.wav
done

# include the chatgpt voices also
sample=speech # story, poem, info and recipe are alternate samples.
for i in sky juniper cove ember breeze; do
	[ ! -e "voices/$i.wav" ] && curl -s https://cdn.openai.com/new-voice-and-image-capabilities-in-chatgpt/hd/$sample-$i.mp3 | ffmpeg -loglevel error -i - -ar 22050 -ac 1 voices/$i.wav
done
