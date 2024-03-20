FROM nvidia/cuda:11.8.0-base-ubuntu22.04

RUN apt-get update && \
    apt-get install --no-install-recommends -y ffmpeg curl python-is-python3 python3-pip && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

#RUN git clone https://github.com/matatonic/openedai-speech /app
RUN mkdir -p /app/voices
# default clone of the default voice is really bad, use a better default
COPY voices/alloy-alt.wav /app/voices/
WORKDIR /app
COPY requirements.txt /app/
RUN pip install -r requirements.txt
COPY *.py *.yaml *.txt *.md *.sh LICENSE /app/

RUN ./download_voices_tts-1.sh
RUN ./download_voices_tts-1-hd.sh

ENV COQUI_TOS_AGREED=1
CMD python main.py --host 0.0.0.0 --port 8000 --preload xtts
