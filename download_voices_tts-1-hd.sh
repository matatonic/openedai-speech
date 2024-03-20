#!/bin/sh
export COQUI_TOS_AGREED=1
model="xtts" # others are possible, ex. xtts_v2.0.2
python -c "from TTS.utils.manage import ModelManager; ModelManager().download_model('$model')"
./download_samples.sh