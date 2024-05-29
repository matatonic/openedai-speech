#!/bin/sh
models=${*:-"en_GB-northern_english_male-medium en_US-libritts_r-medium"} # en_US-ryan-high
piper --update-voices --data-dir voices --download-dir voices --model x 2> /dev/null
for i in $models ; do
    [ ! -e "voices/$i.onnx" ] && piper --data-dir voices --download-dir voices --model $i < /dev/null > /dev/null
done
