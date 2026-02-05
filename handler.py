"""
GeneFace++ Serverless Handler for RunPod
Accepts audio input, generates lip-synced video output
"""

import runpod
import os
import sys
import base64
import tempfile
import subprocess
import time
import traceback

# Add GeneFace++ to path
sys.path.insert(0, '/app/GeneFacePlusPlus')
os.environ['PYTHONPATH'] = '/app/GeneFacePlusPlus'

def download_audio(audio_input: str, temp_dir: str) -> str:
    """Download or decode audio from URL or base64"""
    audio_path = os.path.join(temp_dir, "input_audio.wav")

    if audio_input.startswith('http://') or audio_input.startswith('https://'):
        # Download from URL
        subprocess.run(['wget', '-q', '-O', audio_path, audio_input], check=True)
    elif audio_input.startswith('data:'):
        # Base64 data URL
        header, encoded = audio_input.split(',', 1)
        audio_data = base64.b64decode(encoded)
        with open(audio_path, 'wb') as f:
            f.write(audio_data)
    else:
        # Assume raw base64
        audio_data = base64.b64decode(audio_input)
        with open(audio_path, 'wb') as f:
            f.write(audio_data)

    # Convert to WAV if needed (ffmpeg)
    wav_path = os.path.join(temp_dir, "input_converted.wav")
    subprocess.run([
        'ffmpeg', '-y', '-i', audio_path,
        '-ar', '16000', '-ac', '1',
        wav_path
    ], check=True, capture_output=True)

    return wav_path


def generate_video(audio_path: str, output_path: str, avatar: str = "may") -> str:
    """Generate lip-synced video using GeneFace++"""

    os.chdir('/app/GeneFacePlusPlus')

    # Build inference command
    cmd = [
        'python', 'inference/genefacepp_infer.py',
        f'--a2m_ckpt=checkpoints/audio2motion_vae',
        f'--head_ckpt=',
        f'--torso_ckpt=checkpoints/motion2video_nerf/{avatar}_torso',
        f'--drv_aud={audio_path}',
        f'--out_name={output_path}'
    ]

    # Run inference
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        env={**os.environ, 'PYTHONPATH': '/app/GeneFacePlusPlus'}
    )

    if result.returncode != 0:
        raise Exception(f"Inference failed: {result.stderr}")

    return output_path


def handler(event):
    """
    RunPod Serverless Handler

    Input:
        - audio: base64 encoded audio or URL
        - avatar: (optional) avatar name, default "may"
        - return_base64: (optional) return video as base64, default True

    Output:
        - video_base64: base64 encoded MP4 video (if return_base64=True)
        - video_url: URL to download video (if using RunPod storage)
        - duration_seconds: processing time
    """

    start_time = time.time()

    try:
        # Get input
        job_input = event.get('input', {})
        audio_input = job_input.get('audio')
        avatar = job_input.get('avatar', 'may')
        return_base64 = job_input.get('return_base64', True)

        if not audio_input:
            return {"error": "Missing 'audio' in input"}

        # Create temp directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Download/decode audio
            print(f"[1/3] Processing audio input...")
            audio_path = download_audio(audio_input, temp_dir)

            # Get audio duration
            probe_result = subprocess.run([
                'ffprobe', '-v', 'quiet', '-show_entries',
                'format=duration', '-of', 'csv=p=0', audio_path
            ], capture_output=True, text=True)
            audio_duration = float(probe_result.stdout.strip()) if probe_result.stdout.strip() else 0

            # Generate video
            print(f"[2/3] Generating lip-sync video (audio: {audio_duration:.1f}s)...")
            output_path = os.path.join(temp_dir, "output.mp4")
            generate_video(audio_path, output_path, avatar)

            # Prepare output
            print(f"[3/3] Preparing output...")
            processing_time = time.time() - start_time

            result = {
                "audio_duration_seconds": audio_duration,
                "processing_time_seconds": round(processing_time, 2),
                "realtime_factor": round(audio_duration / processing_time, 2) if processing_time > 0 else 0
            }

            if return_base64:
                with open(output_path, 'rb') as f:
                    video_data = f.read()
                result["video_base64"] = base64.b64encode(video_data).decode('utf-8')
                result["video_size_mb"] = round(len(video_data) / (1024 * 1024), 2)

            print(f"Done! Processing took {processing_time:.1f}s for {audio_duration:.1f}s audio ({result['realtime_factor']}x realtime)")

            return result

    except Exception as e:
        traceback.print_exc()
        return {
            "error": str(e),
            "traceback": traceback.format_exc()
        }


# Start RunPod serverless
runpod.serverless.start({"handler": handler})
