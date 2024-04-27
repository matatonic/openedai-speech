#!/bin/sh
export COQUI_TOS_AGREED=1
export TTS_HOME=voices

MODELS=${*:-xtts}
for model in $MODELS; do
	python -c "from TTS.utils.manage import ModelManager; ModelManager().download_model('$model')"
done
./download_samples.sh