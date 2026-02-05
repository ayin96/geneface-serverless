FROM nvidia/cuda:11.7.1-cudnn8-devel-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Install system dependencies (Python 3.10 is default in Ubuntu 22.04)
RUN apt-get update && apt-get install -y \
    python3 \
    python3-dev \
    python3-pip \
    git \
    ffmpeg \
    libsndfile1 \
    libasound2-dev \
    portaudio19-dev \
    libgl1-mesa-glx \
    wget \
    ninja-build \
    && rm -rf /var/lib/apt/lists/*

# Set Python 3 as default
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3 1
RUN update-alternatives --install /usr/bin/pip pip /usr/bin/pip3 1

# Upgrade pip
RUN pip install --upgrade pip

# Install PyTorch with CUDA 11.7
RUN pip install torch==2.0.1 torchvision==0.15.2 torchaudio==2.0.2 --index-url https://download.pytorch.org/whl/cu117

# Install pytorch3d (build from source for CUDA 11.7 + PyTorch 2.0.1)
RUN pip install "git+https://github.com/facebookresearch/pytorch3d.git@stable"

# Install tensorboardX
RUN pip install tensorboardX

# Clone GeneFace++
WORKDIR /app
RUN git clone https://github.com/yerfor/GeneFacePlusPlus.git

WORKDIR /app/GeneFacePlusPlus

# Install Python dependencies
RUN pip install cython openmim==0.3.9
RUN mim install mmcv==2.1.0
RUN pip install -r docs/prepare_env/requirements.txt || true

# Install critical dependencies for inference (requirements.txt may fail silently)
RUN pip install soundfile librosa gdown runpod einops kornia \
    face_alignment trimesh PyMCubes lpips mediapipe decord timm \
    pretrainedmodels faiss-cpu pytorch_lightning transformers \
    opencv-python-headless scipy scikit-image configargparse \
    praat-parselmouth moviepy pillow av beartype torchdiffeq

# Build torch-ngp extensions
RUN bash docs/prepare_env/install_ext.sh || true

# Download pretrained models
RUN mkdir -p checkpoints && \
    gdown --folder "1M6CQH52lG_yZj7oCMaepn3Qsvb-8W2pT" -O checkpoints/ || true

# Download 3DMM BFM model
RUN gdown --folder "1o4t5YIw7w4cMUN4bgU9nPf6IyWVG1bEk" -O deep_3drecon/BFM/ || true

# Copy handler
COPY handler.py /app/handler.py

# Set environment
ENV PYTHONPATH=/app/GeneFacePlusPlus

WORKDIR /app

CMD ["python", "-u", "handler.py"]
