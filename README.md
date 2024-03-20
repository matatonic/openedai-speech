OpenedAI Speech
---------------

An OpenAI API compatible text to speech server.

* Compatible with the OpenAI audio/speech API
* Serves the [/v1/audio/speech endpoint](https://platform.openai.com/docs/api-reference/audio/createSpeech)
* Does not connect to the OpenAI API and does not require an OpenAI API Key
* Not affiliated with OpenAI in any way
* A free, private, text-to-speech server with custom voice cloning

Full Compatibility:
* `tts-1`: `alloy`, `echo`, `fable`, `onyx`, `nova`, and `shimmer` (configurable)
* `tts-1-hd`:  `alloy`, `echo`, `fable`, `onyx`, `nova`, and `shimmer` (configurable, uses OpenAI samples by default)
* response_format: `mp3`, `opus`, `aac`, or `flac`
* speed 0.25-4.0 (and more)

Details:
* model 'tts-1' via [piper tts](https://github.com/rhasspy/piper) (fast, can use cpu)
* model 'tts-1-hd' via [coqui-ai/TTS](https://github.com/coqui-ai/TTS) xtts_v2 voice cloning (fast, uses almost 4GB GPU VRAM)
* Can be run without TTS/xtts_v2, entirely on cpu
* Custom cloned voices can be used for tts-1-hd, just save a WAV file in `/voices/`
* You can map your own [piper voices](https://rhasspy.github.io/piper-samples/) and xtts_v2 speaker clones via `voice_to_speaker.yaml`
* Sometimes certain words or symbols will sound bad, you can fix them with regex via `pre_process_map.yaml`

If you find a better voice match for `tts-1` or `tts-1-hd`, please let me know so I can update the defaults.

Version: 0.7.3, 2024-03-20

* Allow different xtts versions per voice in `voice_to_speaker.yaml`, ex. xtts_v2.0.2
* Quality: Fix xtts sample rate (24000 vs. 22050 for piper) and pops
* use CUDA 12.2-base in Dockerfile

API Documentation
-----------------

* [OpenAI Text to speech guide](https://platform.openai.com/docs/guides/text-to-speech)
* [OpenAI API Reference](https://platform.openai.com/docs/api-reference/audio/createSpeech)


Installation instructions
-------------------------

```shell
# Install the Python requirements
pip install -r requirements.txt
# install ffmpeg & curl
sudo apt install ffmpeg curl
# Download the voice models:
# for tts-1
bash download_voices_tts-1.sh
# and for tts-1-hd
bash download_voices_tts-1-hd.sh
```

Usage
-----

```
usage: main.py [-h] [--piper_cuda] [--xtts_device XTTS_DEVICE] [--preload PRELOAD] [-P PORT]
               [-H HOST]

OpenedAI Speech API Server

options:
  -h, --help            show this help message and exit
  --piper_cuda          Enable cuda for piper. Note: --cuda/onnxruntime-gpu is not working for me,
                        but cpu is fast enough (default: False)
  --xtts_device XTTS_DEVICE
                        Set the device for the xtts model. The special value of 'none' will use
                        piper for all models. (default: cuda)
  --preload PRELOAD     Preload a model (Ex. 'xtts' or 'xtts_v2.0.2'). By default it's loaded on
                        first use. (default: None)
  -P PORT, --port PORT  Server tcp port (default: 8000)
  -H HOST, --host HOST  Host to listen on, Ex. 0.0.0.0 (default: localhost)
```

Sample API Usage
----------------

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

If you want a minimal docker image with piper support only (900MB vs. 13GB, see: Dockerfile.min). You can edit the `docker-compose.yml` to change this.

Custom Voices Howto
-------------------

Custom voices should be mono 22050 hz sample rate WAV files with low noise (no background music, etc.) and not contain any partial words. Sample voices for xtts should be at least 6 seconds, but can be longer, but longer doesn't always produce better results.

You can use FFmpeg to process your audio files and prepare them for xtts, here are some examples:

```shell
# convert a multi-channel audio file to mono, set sample rate to 22050 hz, trim to 6 seconds, and output as WAV file.
ffmpeg -i input.mp3 -ac 1 -ar 22050 -t 6 -y me.wav
# use a simple noise filter to clean up audio, and select a start time start for sampling.
ffmpeg -i input.wav -af "highpass=f=200, lowpass=f=3000" -ac 1 -ar 22050 -ss 00:13:26.2 -t 6 -y me.wav
# A more complex noise reduction setup with volume adjustment
ffmpeg -i input.mkv -af "highpass=f=200, lowpass=f=3000, volume=5, afftdn=nf=25" -ac 1 -ar 22050 -ss 00:13:26.2 -t 6 -y me.wav
```

Once you WAV file is prepared, save it in the voices/ folder and update the `voice_to_speaker.yaml` file with the new file name.

For example:

```yaml
...
tts-1-hd:
  me:
    model: xtts_v2.0.2 # you can specify different xtts versions
    speaker: voices/me.wav # this could be you
```
