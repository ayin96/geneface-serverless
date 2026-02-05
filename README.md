# GeneFace++ Serverless - RunPod

Real-time lip-sync video generation using GeneFace++ on RunPod Serverless.

## Deploy to RunPod

### Option 1: GitHub (Recommended)
1. Push this repo to your GitHub
2. Go to RunPod → Serverless → Deploy
3. Select "Import GitHub Repository"
4. Connect your GitHub and select this repo
5. Configure:
   - GPU: RTX 3090 or A100 (24GB+ VRAM recommended)
   - Max Workers: 1-3
   - Idle Timeout: 5 seconds

### Option 2: Docker Hub
1. Build and push image:
```bash
docker build -t yourusername/geneface-serverless .
docker push yourusername/geneface-serverless
```
2. Go to RunPod → Serverless → Deploy
3. Select "Import from Docker Registry"
4. Enter: `yourusername/geneface-serverless`

## API Usage

### Request
```json
{
  "input": {
    "audio": "<base64_encoded_audio_or_url>",
    "avatar": "may",
    "return_base64": true
  }
}
```

### Response
```json
{
  "audio_duration_seconds": 10.5,
  "processing_time_seconds": 8.2,
  "realtime_factor": 1.28,
  "video_base64": "<base64_encoded_mp4>",
  "video_size_mb": 2.5
}
```

### Python Example
```python
import runpod
import base64

runpod.api_key = "your_api_key"
endpoint = runpod.Endpoint("your_endpoint_id")

# Read audio file
with open("input.mp3", "rb") as f:
    audio_base64 = base64.b64encode(f.read()).decode()

# Run job
result = endpoint.run_sync({
    "input": {
        "audio": audio_base64,
        "avatar": "may"
    }
})

# Save video
video_data = base64.b64decode(result["video_base64"])
with open("output.mp4", "wb") as f:
    f.write(video_data)
```

## Supported Avatars
- `may` (default) - Female avatar from GeneFace++ demo

## Custom Avatar Training
To use your own avatar:
1. Train GeneFace++ with your video (see GeneFace++ docs)
2. Add checkpoint to `checkpoints/motion2video_nerf/your_avatar_torso`
3. Rebuild Docker image
4. Call API with `"avatar": "your_avatar"`

## Pricing Estimate
- RTX 3090: ~$0.30/hr
- 10-second audio ≈ 8 seconds processing
- Cost per 10s video: ~$0.0007 (less than 1 cent)

## Notes
- First request may be slow (cold start ~30-60s)
- Subsequent requests are much faster
- Use "Active Workers" > 0 to avoid cold starts (costs more)
