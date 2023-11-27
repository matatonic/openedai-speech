#!/bin/sh
COQUI_TOS_AGREED=1
tts --model_name "tts_models/multilingual/multi-dataset/xtts_v2" --text "Done" --language_idx "en" --speaker_wav voices/alloy.wav --pipe_out | \
	ffmpeg -f s16le -ar 22050 -ac 1 -i - > /dev/null
rm -f tts_output.wav
