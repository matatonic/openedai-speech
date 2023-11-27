FROM nvidia/cuda:11.8.0-base-ubuntu22.04

ENV COQUI_TOS_AGREED=1

#python3.11 
RUN apt-get update && \
    apt-get install --no-install-recommends -y python3-pip wget ffmpeg && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

#RUN git clone https://github.com/matatonic/openedai-api-audio-speech /app
RUN mkdir -p /app/voices
COPY *.py *.yaml *.txt *.md *.sh /app/
COPY ./voices/alloy.wav /app/voices/alloy.wav
WORKDIR /app
RUN pip install -r requirements.txt

RUN ./download_voices_tts-1.sh
RUN ./download_voices_tts-1-hd.sh

CMD python3 main.py
