#!/bin/sh
export COQUI_TOS_AGREED=1
model="tts_models/multilingual/multi-dataset/xtts_v2"
python -c "from TTS.utils.manage import ModelManager; ModelManager().download_model('$model')"
$(cd voices/ && ./download_samples.sh)