#!/bin/bash

[ -f speech.env ] && . speech.env

echo "First startup may download 2GB of speech models. Please wait."

bash download_voices_tts-1.sh
bash download_voices_tts-1-hd.sh $PRELOAD_MODEL

python speech.py ${PRELOAD_MODEL:+--preload $PRELOAD_MODEL} $EXTRA_ARGS $@
