@echo off
set models=%* 
if "%models%" == "" set models=en_GB-northern_english_male-medium en_US-libritts_r-medium

piper --update-voices --data-dir voices --download-dir voices --model x 2> nul
for %%i in (%models%) do (
    if not exist "voices\%%i.onnx" piper --data-dir voices --download-dir voices --model %%i > nul
)
