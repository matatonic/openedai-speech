#!/bin/sh
piper --update-voices --data-dir voices --download-dir voices --model en_GB-northern_english_male-medium < /dev/null > /dev/null
piper --data-dir voices --download-dir voices --model en_US-libritts_r-medium < /dev/null > /dev/null
