@echo off
set COQUI_TOS_AGREED=1
set TTS_HOME=voices

for %%i in (%*) do (
    python -c "from TTS.utils.manage import ModelManager; ModelManager().download_model('%%i')"
)
call download_samples.bat
