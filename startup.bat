@echo off

set /p < speech.env

call download_voices_tts-1.bat
call download_voices_tts-1-hd.bat %PRELOAD_MODEL%

python speech.py %PRELOAD_MODEL:+--preload %PRELOAD_MODEL% %EXTRA_ARGS%