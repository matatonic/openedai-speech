FROM python:3.11-slim

ENV COQUI_TOS_AGREED=1

RUN apt-get update && \
    apt-get install --no-install-recommends -y curl git ffmpeg

RUN mkdir -p /app/voices
WORKDIR /app
COPY *.txt /app/
RUN --mount=type=cache,target=/root/.cache/pip pip install -r requirements.txt
COPY *.sh *.py *.yaml *.md LICENSE config /app/

RUN apt-get clean && rm -rf /var/lib/apt/lists/*

ENV CLI_COMMAND="python speech.py"
CMD $CLI_COMMAND
