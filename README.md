openedai API for audio/speech
-----------------------------

This is an API clone of the OpenAI API for text to speech audio generation.

This is v0.1, so please excuse the rough docs and configuration.

It currently supports 'tts-1' via piper tts (fast, ~1 sec latency), and 'tts-1-hd' via xtts_v2 (slow, also uses a couple gigs of gpu vram).

Installation instructions:
--------------------------

```pip install -r requirements.txt```

To download voices in advance:

for the tts-1 model:
```shell
piper --update-voices --data-dir voices --download-dir voices --model en_US-libritts_r-medium < /dev/null > /dev/null
piper --data-dir voices --download-dir voices --model en_GB-northern_english_male-medium < /dev/null > /dev/null
```

for tts-1-hd:
```shell
COQUI_TOS_AGREED=1
tts --model_name "tts_models/multilingual/multi-dataset/xtts_v2" --text "." --language_idx en > /dev/null
```

Run the server, it listens on ```port 8000``` by default:

```python main.py```

API Usage
---------

You can use it like this:

```shell
curl http://localhost:8000/v1/audio/speech -H "Content-Type: application/json" -d '{
    "model": "tts-1",
    "input": "The quick brown fox jumped over the lazy dog.",
    "voice": "alloy",
    "response_format": "mp3",
    "speed": 1.0
  }' > speech.mp3
```

Or just like this:


```shell
curl http://localhost:8000/v1/audio/speech -H "Content-Type: application/json" -d '{
    "input": "The quick brown fox jumped over the lazy dog."}' > speech.mp3
```




Or like this example from the [OpenAI Text to speech guide](https://platform.openai.com/docs/guides/text-to-speech):

```python
import openai

client = openai.OpenAI(
  # This part is not needed if you set these environment variables before import openai
  # export OPENAI_API_KEY=sk-11111111111
  # export OPENAI_BASE_URL=http://localhost:8000/v1
  api_key = "sk-111111111",
  base_url = "http://localhost:8000/v1",
)

response = client.audio.speech.create(
  model="tts-1",
  voice="alloy",
  input="Today is a wonderful day to build something people love!"
)

response.stream_to_file("speech.mp3")
```

Docker support
--------------

You can run the server via docker like so:
```shell
docker compose build
docker compose up
```

By default it will build a minimal docker image with piper and tts-1 support only. You can edit docker-compose.yml to change this.

Voice sounds bad on some words or symbols? Check out ```pre_process_map.yaml``` and add a regular express to replace it with something that sounds right.

Want to change the voices or add your own? Check out ```voice_to_speaker.yaml```. I tried to map the voices to something similar to the OpenAI voices, but some are better than others.

If you find a better voice match, please let me know so I can update the defaults.

Voice models for tts-1-hd/xtts2 are incomplete, you can add your own WAV file samples to make more voices, see allow.wav for a sample.