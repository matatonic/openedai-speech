#!/usr/bin/env python

import sys
import os
import atexit
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
    parser = argparse.ArgumentParser(
        description='Text to speech using the OpenAI API',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("-m", "--model", type=str, default="tts-1", help="The model to use")#, choices=["tts-1", "tts-1-hd"])
    parser.add_argument("-v", "--voice", type=str, default="alloy", help="The voice of the speaker")#, choices=["alloy", "echo", "fable", "onyx", "nova", "shimmer"])
    parser.add_argument("-f", "--format", type=str, default="mp3", choices=["mp3", "aac", "opus", "flac"], help="The output audio format")
    parser.add_argument("-s", "--speed", type=float, default=1.0, help="playback speed, 0.25-4.0")
    parser.add_argument("-t", "--text", type=str, default=None, help="Provide text to read on the command line")
    parser.add_argument("-i", "--input", type=str, default=None, help="Read text from a file (default is to read from stdin)")
    
    if playsound is None:
        parser.add_argument("-o", "--output", type=str, help="The filename to save the output to") # required
        parser.add_argument("-p", "--playsound", type=None, default=None, help="python playsound not found. pip install playsound")
    else:
        parser.add_argument("-o", "--output", type=str, default=None, help="The filename to save the output to") # not required
        parser.add_argument("-p", "--playsound", action="store_true", help="Play the audio")

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

    if args.input is None and args.text is None:
        text = sys.stdin.read()
    elif args.text:
        text = args.text
    elif args.input:
        if os.path.exists(args.input):
            with open(args.input, 'r') as f:
                text = f.read()
        else:
            print(f"Warning! File not found: {args.input}\nFalling back to old behavior for -i")
            text = args.input

    client = openai.OpenAI(
        # This part is not needed if you set these environment variables before import openai
        # export OPENAI_API_KEY=sk-11111111111
        # export OPENAI_BASE_URL=http://localhost:8000/v1
        api_key = os.environ.get("OPENAI_API_KEY", "sk-ip"),
        base_url = os.environ.get("OPENAI_BASE_URL", "http://localhost:8000/v1"),
    )

    if args.playsound and args.output is None:
        _, args.output = tempfile.mkstemp(suffix='.wav')
        
        def cleanup():
            os.unlink(args.output)

        atexit.register(cleanup)

    with client.audio.speech.with_streaming_response.create(
        model=args.model,
        voice=args.voice,
        speed=args.speed,
        response_format=args.format,
        input=text,
    ) as response:
        response.stream_to_file(args.output)

        if args.playsound:
            playsound(args.output)
