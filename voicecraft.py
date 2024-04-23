import argparse, pickle
import logging
import os, random
import numpy as np
import torch
import torchaudio

from data.tokenizer import (
    AudioTokenizer,
    TextTokenizer,
    tokenize_audio,
    tokenize_text
)

from models import voicecraft
import argparse, time, tqdm



class vo_wrapper():
    def __init__(self, model_name, device):
        self.model_name = model_name
        self.xtts = TTS(model_name=model_name, progress_bar=False).to(device)

    def tts(self, text, speaker_wav, speed):
        tf, file_path = tempfile.mkstemp(suffix='.wav')

        file_path = self.xtts.tts_to_file(
            text,
            language='en',
            speaker_wav=speaker_wav,
            speed=speed,
            file_path=file_path,
        )

        os.unlink(file_path)
        return tf

