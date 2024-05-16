FROM python:3.11-slim

ENV COQUI_TOS_AGREED=1

RUN apt-get update && \
    apt-get install --no-install-recommends -y curl git ffmpeg && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app
RUN mkdir -p voices config

COPY *.sh *.py *.yaml *.md LICENSE requirements.txt /app/
COPY config/* /app/config/

RUN chmod +x /app/init.sh && \
    chmod +x /app/download_voices_tts-1.sh && \
    chmod +x /app/download_voices_tts-1-hd.sh

RUN pip install -r requirements.txt

CMD ["/bin/bash", "-c", "/app/init.sh && python speech.py"]
