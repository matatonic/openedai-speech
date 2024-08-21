# OpenedAI Speech

An OpenAI API compatible text to speech server.

* Compatible with the OpenAI audio/speech API
* Serves the [/v1/audio/speech endpoint](https://platform.openai.com/docs/api-reference/audio/createSpeech)
* Not affiliated with OpenAI in any way, does not require an OpenAI API Key
* A free, private, text-to-speech server with custom voice cloning

Full Compatibility:
* `tts-1`: `alloy`, `echo`, `fable`, `onyx`, `nova`, and `shimmer` (configurable)
* `tts-1-hd`:  `alloy`, `echo`, `fable`, `onyx`, `nova`, and `shimmer` (configurable, uses OpenAI samples by default)
* response_format: `mp3`, `opus`, `aac`, `flac`, `wav` and `pcm`
* speed 0.25-4.0 (and more)

Details:
* Model `tts-1` via [piper tts](https://github.com/rhasspy/piper) (very fast, runs on cpu)
  * You can map your own [piper voices](https://rhasspy.github.io/piper-samples/) via the `voice_to_speaker.yaml` configuration file
* Model `tts-1-hd` via [coqui-ai/TTS](https://github.com/coqui-ai/TTS) xtts_v2 voice cloning (fast, but requires around 4GB GPU VRAM)
  * Custom cloned voices can be used for tts-1-hd, See: [Custom Voices Howto](#custom-voices-howto)
  * 🌐 [Multilingual](#multilingual) support with automatic language detection (optional)
  * [Custom fine-tuned model support](#custom-fine-tuned-model-support)
  * Configurable [generation parameters](#generation-parameters)
  * Streamed output while generating
* Occasionally, certain words or symbols may sound incorrect, you can fix them with regex via `pre_process_map.yaml`
* Tested with python 3.9-3.11, piper does not install on python 3.12 yet


If you find a better voice match for `tts-1` or `tts-1-hd`, please let me know so I can update the defaults.

## Recent Changes

Version 0.19.0, 2024-08-21

* Rename docker services to more sensible names
* Additional default voices for tts-1-hd/xtts
* Refined and simplified configuration file (backward compatible), see: `voice_to_speaker.default.yaml` and [Custom Voices Howto](#custom-voices-howto)
* xtts: Automatic use of wav files in `voices/` with no additional configuration needed, just copy the wav file into `voices/` and the voice is available.
* piper: Automatic model selection based on language detection (model: auto), it selects the highest quality model available.
* piper: Simpler automatic downloading of piper models if they are not found on the system.
* Include Facebook fasttext language detection for better, faster language detection
* 🌐 [Multilingual](#multilingual) support for Piper (38 languages) with automatic language detection and automatic model selection.
* Additional controls for the use of language detection
* Thanks [@thiswillbeyourgithub](https://github.com/thiswillbeyourgithub), [@RodolfoCastanheira](https://github.com/RodolfoCastanheira)

Version 0.18.2, 2024-08-16

* Fix docker building for amd64, refactor github actions again, free up more disk space

Version 0.18.1, 2024-08-15

* refactor github actions

Version 0.18.0, 2024-08-15

* Allow folders of wav samples in xtts. Samples will be combined, allowing for mixed voices and collections of small samples. Still limited to 30 seconds total. Thanks [@nathanhere](https://github.com/nathanhere).
* Fix missing yaml requirement in -min image
* fix fr_FR-tom-medium and other 44khz piper voices (detect non-default sample rates)
* minor updates

Version 0.17.2, 2024-07-01

* fix -min image (re: langdetect)

Version 0.17.1, 2024-07-01

* fix ROCm (add langdetect to requirements-rocm.txt)
* Fix zh-cn for xtts

Version 0.17.0, 2024-07-01

* Automatic language detection, thanks [@RodolfoCastanheira](https://github.com/RodolfoCastanheira)

Version 0.16.0, 2024-06-29

* Multi-client safe version. Audio generation is synchronized in a single process. The estimated 'realtime' factor of XTTS on a GPU is roughly 1/3, this means that multiple streams simultaneously, or `speed` over 2, may experience audio underrun (delays or pauses in playback). This makes multiple clients possible and safe, but in practice 2 or 3 simultaneous streams is the maximum without audio underrun.

Version 0.15.1, 2024-06-27

* Remove deepspeed from requirements.txt, it's too complex for typical users. A more detailed deepspeed install document will be required.

Version 0.15.0, 2024-06-26

* Switch to [coqui-tts](https://github.com/idiap/coqui-ai-TTS) (updated fork), updated simpler dependencies, torch 2.3, etc.
* Resolve cuda threading issues

Version 0.14.1, 2024-06-26

* Make deepspeed possible (`--use-deepspeed`), but not enabled in pre-built docker images (too large). Requires the cuda-toolkit installed, see the Dockerfile comment for details

Version 0.14.0, 2024-06-26

* Added `response_format`: `wav` and `pcm` support
* Output streaming (while generating) for `tts-1` and `tts-1-hd`
* Enhanced [generation parameters](#generation-parameters) for xtts models (temperature, top_p, etc.)
* Idle unload timer (optional) - doesn't work perfectly yet
* Improved error handling

Version 0.13.0, 2024-06-25

* Added [Custom fine-tuned XTTS model support](#custom-fine-tuned-model-support)
* Initial prebuilt arm64 image support (Apple M-series, Raspberry Pi - MPS is not supported in XTTS/torch), thanks [@JakeStevenson](https://github.com/JakeStevenson), [@hchasens](https://github.com/hchasens)
* Initial attempt at AMD GPU (ROCm 5.7) support
* Parler-tts support removed
* Move the *.default.yaml to the root folder
* Run the docker as a service by default (`restart: unless-stopped`)
* Added `audio_reader.py` for streaming text input and reading long texts

Version 0.12.3, 2024-06-17

* Additional logging details for BadRequests (400)

Version 0.12.2, 2024-06-16

* Fix :min image requirements (numpy<2?)

Version 0.12.0, 2024-06-16

* Improved error handling and logging
* Restore the original alloy tts-1-hd voice by default, use alloy-alt for the old voice.

Version 0.11.0, 2024-05-29

* 🌐 [Multilingual](#multilingual) support (16 languages) with XTTS
* Remove high Unicode filtering from the default `config/pre_process_map.yaml`
* Update Docker build & app startup. thanks @justinh-rahb
* Fix: "Plan failed with a cudnnException"
* Remove piper cuda support

Version: 0.10.1, 2024-05-05

* Remove `runtime: nvidia` from docker-compose.yml, this assumes nvidia/cuda compatible runtime is available by default. thanks [@jmtatsch](https://github.com/jmtatsch)

Version: 0.10.0, 2024-04-27

* Pre-built & tested docker images, smaller docker images (8GB or 860MB)
* Better upgrades: reorganize config files under `config/`, voice models under `voices/`
* **Compatibility!** If you customized your `voice_to_speaker.yaml` or `pre_process_map.yaml` you need to move them to the `config/` folder.
* default listen host to 0.0.0.0

Version: 0.9.0, 2024-04-23

* Fix bug with yaml and loading UTF-8
* New sample text-to-speech application `say.py`
* Smaller docker base image
* Add beta [parler-tts](https://huggingface.co/parler-tts/parler_tts_mini_v0.1) support (you can describe very basic features of the speaker voice), See: (https://www.text-description-to-speech.com/) for some examples of how to describe voices. Voices can be defined in the `voice_to_speaker.default.yaml`. Two example [parler-tts](https://huggingface.co/parler-tts/parler_tts_mini_v0.1) voices are included in the `voice_to_speaker.default.yaml` file. `parler-tts` is experimental software and is kind of slow. The exact voice will be slightly different each generation but should be similar to the basic description.

...

Version: 0.7.3, 2024-03-20

* Allow different xtts versions per voice in `voice_to_speaker.yaml`, ex. xtts_v2.0.2
* Quality: Fix xtts sample rate (24000 vs. 22050 for piper) and pops


## Installation instructions

### Create a `speech.env` environment file

Copy the `sample.env` to `speech.env` (customize if needed)
```bash
cp sample.env speech.env
```

#### Defaults
```bash
TTS_HOME=voices
HF_HOME=voices
#PRELOAD_MODEL=xtts
#PRELOAD_MODEL=xtts_v2.0.2
#EXTRA_ARGS=--log-level DEBUG --unload-timer 300
#USE_ROCM=1
```

### Option A: Manual installation
```shell
# install curl and ffmpeg
sudo apt install curl ffmpeg
# Create & activate a new virtual environment (optional but recommended)
python -m venv .venv
source .venv/bin/activate
# Install the Python requirements
# - use requirements-rocm.txt for AMD GPU (ROCm support)
# - use requirements-min.txt for piper only (CPU only)
pip install -U -r requirements.txt
# run the server
bash startup.sh
```

> On first run, the voice models will be downloaded automatically. This might take a while depending on your network connection.

### Option B: Docker Image (*recommended*)

#### Nvidia GPU (cuda)

```shell
docker compose up
```

#### AMD GPU (ROCm support)

```shell
docker compose -f docker-compose.rocm.yml up
```

#### ARM64 (Apple M-series, Raspberry Pi)

> XTTS only has CPU support here and will be very slow, you can use the Nvidia image for XTTS with CPU (slow), or use the piper only image (recommended)

#### CPU only, No GPU (piper only)

> For a minimal docker image with only piper support (1.2GB vs. 8GB).

```shell
docker compose -f docker-compose.min.yml up
```

## Server Options

```shell
usage: speech.py [-h] [--xtts_device XTTS_DEVICE] [--preload PRELOAD] [--unload-timer UNLOAD_TIMER] [--piper-supported-languages PIPER_SUPPORTED_LANGUAGES]
                 [--xtts-supported-languages XTTS_SUPPORTED_LANGUAGES] [--use-deepspeed] [-P PORT] [-H HOST] [-L {DEBUG,INFO,WARNING,ERROR,CRITICAL}]

OpenedAI Speech API Server

options:
  -h, --help            show this help message and exit
  --xtts_device XTTS_DEVICE
                        Set the device for the xtts model. The special value of 'none' will use piper for all models. (default: cuda)
  --preload PRELOAD     Preload a model (Ex. 'xtts' or 'xtts_v2.0.2'). By default it's loaded on first use. (default: None)
  --unload-timer UNLOAD_TIMER
                        Idle unload timer for the XTTS model in seconds, Ex. 900 for 15 minutes (default: None)
  --piper-supported-languages PIPER_SUPPORTED_LANGUAGES
                        Comma separated list of supported languages for piper (default: ar,ca,cs,cy,da,de,el,en,es,fa,fi,fr,hu,is,it,ka,kk,lb,ne,nl,no,pl,pt,ro,ru,sk,sl,sr,sv,sw,tr,uk,vi,zh)
  --xtts-supported-languages XTTS_SUPPORTED_LANGUAGES
                        Comma separated list of supported languages for xtts (default: ar,cs,de,en,es,fr,hi,hu,it,ja,ko,nl,pl,pt,ru,tr,zh-cn)
  --use-deepspeed       Use deepspeed with xtts (this option is unsupported) (default: False)
  -P PORT, --port PORT  Server tcp port (default: 8000)
  -H HOST, --host HOST  Host to listen on, Ex. 0.0.0.0 (default: 0.0.0.0)
  -L {DEBUG,INFO,WARNING,ERROR,CRITICAL}, --log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        Set the log level (default: INFO)
```


## Sample Usage

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
curl -s http://localhost:8000/v1/audio/speech -H "Content-Type: application/json" -d '{
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

with client.audio.speech.with_streaming_response.create(
  model="tts-1",
  voice="alloy",
  input="Today is a wonderful day to build something people love!"
) as response:
  response.stream_to_file("speech.mp3")
```

Also see the `say.py` sample application for an example of how to use the openai-python API.

```shell
# play the audio, requires 'pip install playsound'
python say.py -t "The quick brown fox jumped over the lazy dog." -p
# save to a file in flac format
python say.py -t "The quick brown fox jumped over the lazy dog." -m tts-1-hd -v onyx -f flac -o fox.flac
```

You can also try the included `audio_reader.py` for listening to longer text and streamed input.

Example usage:
```bash
python audio_reader.py -s 2 < LICENSE # read the software license - fast
```

FYI, The opening line of this file, "GNU AFFERO GENERAL PUBLIC LICENSE", is incorrectly identified as Ukranian by fasttext.

To prevent this kind of behavior, or if you only use a single or small set of languages, you can set the following option on the command line options in the `speech.env` file:

```
EXTRA_ARGS="--xtts-supported-languages en --piper-supported-languages en"
```

Setting this to a single language will disable auto-detection and identify all input as that language.

## OpenAI API Documentation and Guide

* [OpenAI Text to speech guide](https://platform.openai.com/docs/guides/text-to-speech)
* [OpenAI API Reference](https://platform.openai.com/docs/api-reference/audio/createSpeech)


## Custom Voices Howto

### Piper

  1. Select the piper voice and model from the [piper samples](https://rhasspy.github.io/piper-samples/)
  2. Update the `config/voice_to_speaker.yaml` with a new section for the voice, for example:
```yaml
...
tts-1:
  ryan:
    model: en_US-ryan-high
    language: en
```
Some models are multi-speaker and require setting a speaker id:
```yaml
...
tts-1:
  p6544:
    model: en_US-libritts-high
    speaker: 9
    language: en
```
  3. New models will be downloaded as needed, or you can download them in advance with `download_voices_tts-1.sh`. For example:
```shell
bash download_voices_tts-1.sh en_US-ryan-high
```

### Coqui XTTS v2

Coqui XTTS v2 voice cloning can work with as little as 6 seconds of clear audio. To create a custom voice clone, you must prepare a WAV file sample of the voice.

#### Guidelines for preparing good sample files for Coqui XTTS v2
* Mono (single channel) 22050 Hz WAV file
* 6-30 seconds long - longer isn't always better (I've had some good results with as little as 4 seconds)
* low noise (no hiss or hum)
* No partial words, breathing, laughing, music or backgrounds sounds
* An even speaking pace with a variety of words is best, like in interviews or audiobooks.
* Audio longer than 30 seconds will be silently truncated.

You can use FFmpeg to prepare your audio files, here are some examples:

```shell
# convert a multi-channel audio file to mono, set sample rate to 22050 hz, trim to 6 seconds, and output as WAV file.
ffmpeg -i input.mp3 -ac 1 -ar 22050 -t 6 -y me.wav
# use a simple noise filter to clean up audio, and select a start time start for sampling.
ffmpeg -i input.wav -af "highpass=f=200, lowpass=f=3000" -ac 1 -ar 22050 -ss 00:13:26.2 -t 6 -y me.wav
# A more complex noise reduction setup, including volume adjustment
ffmpeg -i input.mkv -af "highpass=f=200, lowpass=f=3000, volume=5, afftdn=nf=25" -ac 1 -ar 22050 -ss 00:13:26.2 -t 6 -y me.wav
```

Once your WAV file is prepared, save it in the `/voices/` directory. If you don't require any further customization, your voice is ready to use and is available by using the name of the wav file as the voice (without the '.wav' part). New in version 0.19.0 - adding xtts voices to the config file is no longer required, but still supported.

To update the `config/voice_to_speaker.yaml` and adjust the default settings,
For example:

```yaml
...
tts-1-hd:
  me:
    speaker: voices/me-v4.wav # this could be you, 'me-v4' would also be available without any customization.
    speed: 1.2 # speed it up
```

You can also use a sub folder for multiple audio samples to combine small samples or to mix different samples together.

For example:

```yaml
...
tts-1-hd:
  mixed:
    speaker: voices/mixed
```

Where the `voices/mixed/` folder contains multiple wav files. The total audio length is still limited to 30 seconds.

## Multilingual

The openai API doesn't offer any support for setting a language, so languages are auto-detected by default. This is mostly accurate but sometimes the detection is wrong, especially for very short sentences. You can disable language auto-detection by setting the language for a voice in the `config/voice_to_speaker.yaml` file.

```
tts-1:
  alloy:
    language: en # fixed to en, and auto-detection is disabled
    model: en_US-libritts_r-medium
    speaker: 79
tts-1-hd:
  alloy:
    language: en # fixed to en, and auto-detection is disabled
```

You can also limit the possible languages detected using server startup commands with the `--piper-supported-languages` and `--xtts-supported-languages`. Setting this to a single language will disable/limit language auto detection for all models of that type.

### Piper

Language auto-detection and multilingual support for piper was added in version 0.19.0. Out of the box, with the publicly available piper models, piper supports 38 languages: `ar`, `ca`, `cs`, `cy`, `da`, `de`, `el`, `en`, `es`, `fa`, `fi`, `fr`, `hu`, `is`, `it`, `ka`, `kk`, `lb`, `ne`, `nl`, `no`, `pl`, `pt`, `ro`, `ru`, `sk`, `sl`, `sr`, `sv`, `sw`, `tr`, `uk`, `vi`, `zh`.

Piper itself doesn't support multiple languages in a model, but by using language auto detection and the large selection of models from piper, a model can be automatically selected for a language. This is enabled by default, and can be customized or disabled by using the configuration file `config/voice_to_speaker.yaml`.

```yaml
tts-1:
  alloy:
    language: auto # If you don't set a specific language, the language will be auto detected
    # When using language "auto", any detected languages missing a model will have a model automatically chosen and downloaded if needed
    # if you don't like the automatically chosen voices, you can select and configure your own language entries
    en:
      model: en_US-libritts_r-medium # This model will be automatically downloaded it it doesn't exist yet
      speaker: 79 # 64, 79, 80, 101, 130
    fr:
      model: fr_FR-siwis-medium
```

This can produce surprising and erroneous results when languages are incorrectly identified. Many languages only support a single voice (Arabic, Chinese, etc.).

### XTTS

Multilingual cloning support was added in version 0.11.0.

Coqui XTTSv2 has support for multiple languages: English (`en`), Spanish (`es`), French (`fr`), German (`de`), Italian (`it`), Portuguese (`pt`), Polish (`pl`), Turkish (`tr`), Russian (`ru`), Dutch (`nl`), Czech (`cs`), Arabic (`ar`), Chinese (`zh-cn`), Hungarian (`hu`), Korean (`ko`), Japanese (`ja`), and Hindi (`hi`). When not set, an attempt will be made to automatically detect the language, falling back to English (`en`).

Unfortunately the OpenAI API does not support language, but you can create your own custom speaker voice and set the language for that.

1) Create the WAV file for your speaker, as in [Custom Voices Howto](#custom-voices-howto)
2) Add the voice to `config/voice_to_speaker.yaml` and include the correct Coqui `language` code for the speaker. For example:

```yaml
  xunjiang:
    model: xtts
    speaker: voices/xunjiang.wav
    language: zh-cn
```

3) Don't remove all high unicode characters in your `config/pre_process_map.yaml`! If you have these lines, you will need to remove them. For example:

Remove:
```yaml
- - '[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F700-\U0001F77F\U0001F780-\U0001F7FF\U0001F800-\U0001F8FF\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF\U00002702-\U000027B0\U000024C2-\U0001F251]+'
  - ''
```

These lines were added to the `config/pre_process_map.yaml` config file by default before version 0.11.0:

4) Your new multi-lingual speaker voice is ready to use!


## Custom Fine-Tuned Model Support

### Piper

Custom fine-tuned piper models can be installed like any other piper model into the `voices/` folder. Just copy the `<model name>.onnx` and `<model name>.onnx.json` files into the `voices/` folder and configure them in the `config/voice_to_speaker.yaml`, like in this example:

```yaml
tts-1:
  custom:
    model: voices/custom.onnx # The voices/custom.onnx.json file must also be present.
    #speaker: 2 # set the default speaker if needed
    language: en # disable language auto detection
```

### XTTS

Adding a custom xtts model is simple. Here is an example of how to add a custom fine-tuned 'halo' XTTS model.

1) Save the model folder under `voices/` (4 files are required, `config.json`, `vocab.json`, `model.pth` and a `sample.wav`)
```
openedai-speech$ ls voices/halo/
config.json  vocab.json  model.pth  sample.wav
```
2) Add the custom voice entry under the `tts-1-hd` section of `config/voice_to_speaker.yaml`:
```yaml
tts-1-hd:
  halo:
    model: halo # This name is required to be unique
    speaker: voices/halo/sample.wav # voice sample is required
    model_path: voices/halo
```
3) The model will be loaded when you access the voice for the first time (`--preload` doesn't work with custom models yet)

## Generation Parameters

The generation of XTTSv2 voices can be fine tuned with the following options (defaults included below):

```yaml
tts-1-hd:
  alloy:
    model: xtts
    speaker: voices/alloy.wav
    enable_text_splitting: True
    length_penalty: 1.0
    repetition_penalty: 10
    speed: 1.0
    temperature: 0.75
    top_k: 50
    top_p: 0.85
```

### Attribution

[Facebook Inc's fasttext language detection](https://fasttext.cc/docs/en/language-identification.html) model (lid.176.ftz) is provided unmodified and is distributed under the [Creative Commons Attribution-Share-Alike License 3.0](https://creativecommons.org/licenses/by-sa/3.0/)