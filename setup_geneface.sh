#!/bin/bash
# GeneFace++ Quick Setup Script for RunPod
# Template: runpod/pytorch:2.0.1-py3.10-cuda11.8.0-devel-ubuntu22.04

set -e

echo "=== GeneFace++ Setup Script ==="
echo "Step 1: Installing system dependencies..."
apt-get update && apt-get install -y ffmpeg ninja-build

echo "Step 2: Cloning GeneFace++..."
cd /workspace
git clone https://github.com/yerfor/GeneFacePlusPlus.git
cd GeneFacePlusPlus

echo "Step 3: Installing Python dependencies..."
pip install pytorch3d -f https://dl.fbaipublicfiles.com/pytorch3d/packaging/wheels/py310_cu118_pyt201/download.html
pip install tensorboardX lpips face_alignment mediapipe transformers librosa soundfile gradio gdown

echo "Step 4: Building CUDA extensions..."
bash docs/prepare_env/install_ext.sh

echo "Step 5: Downloading pretrained models..."
mkdir -p checkpoints
gdown --folder "1M6CQH52lG_yZj7oCMaepn3Qsvb-8W2pT" -O checkpoints/
gdown --folder "1o4t5YIw7w4cMUN4bgU9nPf6IyWVG1bEk" -O deep_3drecon/BFM/

echo "=== Setup Complete! ==="
echo ""
echo "To test with 1-minute audio:"
echo "  ffmpeg -i 'your_audio.mp3' -t 60 -y /workspace/test_1min.wav"
echo "  python inference/genefacepp_infer.py \\"
echo "    --a2m_ckpt=checkpoints/audio2motion_vae \\"
echo "    --torso_ckpt=checkpoints/motion2video_nerf/may_torso \\"
echo "    --drv_aud=/workspace/test_1min.wav \\"
echo "    --out_name=/workspace/output.mp4"
