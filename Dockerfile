FROM ubuntu:22.04

ENV COQUI_TOS_AGREED=1
ENV PRELOAD_MODEL=xtts

RUN apt-get update && \
    apt-get install --no-install-recommends -y ffmpeg curl python-is-python3 python3-pip

#RUN git clone https://github.com/matatonic/openedai-speech /app
RUN mkdir -p /app/voices
# default clone of the default voice is really bad, use a better default
COPY voices/alloy-alt.wav /app/voices/
WORKDIR /app
COPY *.txt /app/
RUN pip install -r requirements.txt
COPY *.sh /app/
RUN ./download_voices_tts-1.sh
RUN ./download_voices_tts-1-hd.sh
COPY *.py *.yaml *.md LICENSE /app/

RUN apt-get clean && rm -rf /var/lib/apt/lists/*

CMD python speech.py --host 0.0.0.0 --port 8000 --preload $PRELOAD_MODEL
