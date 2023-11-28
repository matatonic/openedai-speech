FROM nvidia/cuda:11.8.0-base-ubuntu22.04

RUN apt-get update && \
    apt-get install --no-install-recommends -y python-is-python3 python3-pip ffmpeg && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

#RUN git clone https://github.com/matatonic/openedai-speech /app
RUN mkdir -p /app/voices
COPY *.py *.yaml *.txt *.md *.sh LICENSE /app/
WORKDIR /app

RUN pip install -r requirements.txt
RUN ./download_voices_tts-1.sh
RUN ./download_voices_tts-1-hd.sh

ENV COQUI_TOS_AGREED=1
CMD python main.py --host 0.0.0.0 --port 8000 --preload_xtts
