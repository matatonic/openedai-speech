#!/bin/sh
export COQUI_TOS_AGREED=1
python -c "from TTS.utils.manage import ModelManager; ModelManager().download_model('$PRELOAD_MODEL')"
./download_samples.sh