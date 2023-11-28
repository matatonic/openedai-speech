#!/bin/sh
for i in echo fable onyx nova shimmer; do
	wget -q https://cdn.openai.com/API/docs/audio/$i.wav -O - | ffmpeg -loglevel error -i - -ar 22050 -ac 1 voices/$i.wav
done

# in testing alloy sounded REALY BAD after cloning. Save it anyways, but use another as the default.
wget -q https://cdn.openai.com/API/docs/audio/alloy.wav -O - | ffmpeg -loglevel error -i - -ar 22050 -ac 1 voices/alloy0.wav
