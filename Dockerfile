FROM python:3.11-slim

RUN --mount=type=cache,target=/root/.cache/pip pip install -U pip

ARG TARGETPLATFORM
RUN <<EOF
apt-get update
apt-get install --no-install-recommends -y curl ffmpeg
if [ "$TARGETPLATFORM" != "linux/amd64" ]; then
	apt-get install --no-install-recommends -y build-essential
	curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
fi

# for deepspeed support - image +7.5GB, over the 10GB ghcr.io limit, and no noticable gain in speed or VRAM usage?
#curl -O https://developer.download.nvidia.com/compute/cuda/repos/debian11/x86_64/cuda-keyring_1.1-1_all.deb
#dpkg -i cuda-keyring_1.1-1_all.deb
#rm cuda-keyring_1.1-1_all.deb
#apt-get install --no-install-recommends -y libaio-dev build-essential cuda-toolkit

apt-get clean
rm -rf /var/lib/apt/lists/*
EOF
#ENV CUDA_HOME=/usr/local/cuda
ENV PATH="/root/.cargo/bin:${PATH}"

WORKDIR /app
RUN mkdir -p voices config

ARG USE_ROCM
ENV USE_ROCM=${USE_ROCM}

COPY requirements*.txt /app/
RUN if [ "${USE_ROCM}" = "1" ]; then mv /app/requirements-rocm.txt /app/requirements.txt; fi
RUN --mount=type=cache,target=/root/.cache/pip pip install -r requirements.txt

COPY *.py *.sh *.default.yaml README.md LICENSE /app/

ARG PRELOAD_MODEL
ENV PRELOAD_MODEL=${PRELOAD_MODEL}
ENV TTS_HOME=voices
ENV HF_HOME=voices
ENV COQUI_TOS_AGREED=1

CMD bash startup.sh
