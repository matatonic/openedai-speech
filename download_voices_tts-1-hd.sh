#!/bin/sh
export COQUI_TOS_AGREED=1
export TTS_HOME=voices

for model in $*; do
	python -c "from TTS.utils.manage import ModelManager; ModelManager().download_model('$model')"
done
./download_samples.sh