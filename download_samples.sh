#!/bin/sh
for i in alloy echo fable onyx nova shimmer; do
	curl -s https://cdn.openai.com/API/docs/audio/$i.wav | ffmpeg -loglevel error -i - -ar 22050 -ac 1 voices/$i.wav
done
