#!/usr/bin/env python

import argparse
import os
import shutil
import yaml

print("!! WARNING EXPERIMENTAL !! - THIS TOOL WILL ERASE ALL COMMENTS FROM THE CONFIG FILES .. OR WORSE!!")

parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)

parser.add_argument('sample', action='store', help="Set the wav sample file")
parser.add_argument('-n', '--name', action='store', help="Set the name for the voice (by default will use the WAV file name)")
parser.add_argument('-l', '--language', action='store', default="auto", help="Set the language for the voice",
                    choices=['auto', 'en', 'es', 'fr', 'de', 'it', 'pt', 'pl', 'tr', 'ru', 'nl', 'cs', 'ar', 'zh-cn', 'ja', 'hu', 'ko', 'hi'])
parser.add_argument('--openai-model', action='store', default="tts-1-hd", help="Set the openai model for the voice")
parser.add_argument('--xtts-model', action='store', default="xtts", help="Set the xtts model for the voice (if using a custom model, also set model_path)")
parser.add_argument('--model-path', action='store', default=None, help="Set the path for a custom xtts model")
parser.add_argument('--config-path', action='store', default="config/voice_to_speaker.yaml", help="Set the config file path")
parser.add_argument('--voice-path', action='store', default="voices", help="Set the default voices file path")
parser.add_argument('--default-path', action='store', default="voice_to_speaker.default.yaml", help="Set the default config file path")

args = parser.parse_args()

basename = os.path.basename(args.sample)
name_noext, ext = os.path.splitext(basename)

if not args.name:
    args.name = name_noext
else:
    basename = f"{args.name}.wav"

dest_file = os.path.join(args.voice_path, basename)
if args.sample != dest_file:
    shutil.copy2(args.sample, dest_file)

if not os.path.exists(args.config_path):
    shutil.copy2(args.default_path, args.config_path)

with open(args.config_path, 'r', encoding='utf8') as file:
    voice_map = yaml.safe_load(file)

model_conf = voice_map.get(args.openai_model, {})
model_conf[args.name] = {
    'model': args.xtts_model,
    'speaker': os.path.join(args.voice_path, basename),
    'language': args.language,
}
if args.model_path:
    model_conf[args.name]['model_path'] = args.model_path
voice_map[args.openai_model] = model_conf

with open(args.config_path, 'w', encoding='utf8') as ofile:
    yaml.safe_dump(voice_map, ofile, default_flow_style=False, allow_unicode=True)

print(f"Updated: {args.config_path}")
print(f"Added voice: {args.openai_model}/{args.name}")
print(f"Added section:")
print(f"{args.openai_model}:")
print(f"  {args.name}:")
print(f"    model: {model_conf[args.name]['model']}")
print(f"    speaker: {model_conf[args.name]['speaker']}")
print(f"    language: {model_conf[args.name]['language']}")
