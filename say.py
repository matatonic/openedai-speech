#!/usr/bin/env python

import sys
import os
import tempfile
import argparse

try:
    import dotenv
    dotenv.load_dotenv(override=True)
except ImportError:
    pass

try:
    from playsound import playsound
except ImportError:
    playsound = None

import openai


def parse_args(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--model", type=str, default="tts-1")#, choices=["tts-1", "tts-1-hd"])
    parser.add_argument("-v", "--voice", type=str, default="alloy")#, choices=["alloy", "echo", "fable", "onyx", "nova", "shimmer"])
    parser.add_argument("-f", "--format", type=str, default="mp3", choices=["mp3", "aac", "opus", "flac"])
    parser.add_argument("-s", "--speed", type=float, default=1.0)
    parser.add_argument("-i", "--input", type=str)
    
    if playsound is None:
        parser.add_argument("-o", "--output", type=str) # required
        parser.add_argument("-p", "--playsound", type=None, default=None, help="python playsound not found. pip install playsound")
    else:
        parser.add_argument("-o", "--output", type=str, default=None) # not required
        parser.add_argument("-p", "--playsound", action="store_true")

    args = parser.parse_args(argv)

    return args


if __name__ == "__main__":
    args = parse_args(sys.argv[1:])

    if args.playsound and playsound is None:
        print("playsound module not found, audio will not be played, use -o <filename> to save output to a file. pip install playsound")
        sys.exit(1)

    if not args.playsound and not args.output:
        print("Must select one of playsound (-p) or output file name (-o)")
        sys.exit(1)


    client = openai.OpenAI(
        # This part is not needed if you set these environment variables before import openai
        # export OPENAI_API_KEY=sk-11111111111
        # export OPENAI_BASE_URL=http://localhost:8000/v1
        api_key = os.environ.get("OPENAI_API_KEY", "sk-ip"),
        base_url = os.environ.get("OPENAI_BASE_URL", "http://localhost:8000/v1"),
    )

    if args.playsound and args.output is None:
        tf, args.output = file_path = tempfile.mkstemp(suffix='.wav')
    else:
        tf = None

    with client.audio.speech.with_streaming_response.create(
        model=args.model,
        voice=args.voice,
        speed=args.speed,
        response_format=args.format,
        input=args.input,
    ) as response:
        response.stream_to_file(args.output)

    if args.playsound:
        playsound(args.output)
    
    if tf:
        os.unlink(args.output)
