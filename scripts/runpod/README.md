# RunPod GPU Cloud - ComfyUI Video Generation

GPU cloud infrastructure for AI video/image generation using ComfyUI.

## Quick Start

### 1. Set up credentials

```bash
# Get your API key from https://www.runpod.io/console/user/settings
export RUNPOD_API_KEY="your_key_here"
# Or save permanently:
echo "your_key_here" > ~/.runpod_api_key
```

### 2. Launch a pod

```bash
# Default: RTX 4090 (24GB VRAM, ~$0.44/hr Community Cloud)
python scripts/runpod/launch_pod.py

# Alternative: A100 80GB (~$0.64/hr)
python scripts/runpod/launch_pod.py --gpu a100-80

# Check availability first
python scripts/runpod/launch_pod.py --availability
```

### 3. Set up models and nodes (on the pod)

SSH into the pod and run the setup script:

```bash
# Copy setup script to pod
scp scripts/runpod/pod_setup.sh root@<pod-ip>:/workspace/

# Or pipe it directly
ssh root@<pod-ip> -p <port> 'bash -s' < scripts/runpod/pod_setup.sh
```

### 4. Run tests

```bash
python scripts/runpod/test_pod.py                    # Run all tests
python scripts/runpod/test_pod.py --list-models       # Check installed models
python scripts/runpod/test_pod.py --test wan_t2v      # Quick Wan 2.1 test
```

## Cost Management

**RunPod bills per-second. ALWAYS stop the pod when not in use.**

```bash
# Stop pod (preserves data, stops GPU billing)
python scripts/runpod/launch_pod.py --stop

# Restart pod
python scripts/runpod/launch_pod.py --start

# Check status
python scripts/runpod/launch_pod.py --status

# Terminate (DELETES all data)
python scripts/runpod/launch_pod.py --terminate
```

### Cost estimates

| Action | Cost |
|--------|------|
| RTX 4090 running | ~$0.44/hr |
| A100 80GB running | ~$0.64/hr |
| Pod stopped (volume only) | ~$0.10/GB/month |
| 100GB volume (stopped) | ~$10/month |

**Tip:** Stop the pod after each session. A 2-hour session costs ~$0.88 (4090) vs $10+/month for volume storage.

## Installed Components

### Models (downloaded by pod_setup.sh)
- **Wan 2.1 T2V 14B** - High quality text-to-video (needs 24GB+ VRAM)
- **Wan 2.1 T2V 1.3B** - Fast text-to-video (lower VRAM)
- **Wan 2.1 I2V 14B** - Image-to-video
- **Wan 2.1 VAE + Text Encoder** - Required for all Wan workflows
- **CLIP Vision Models** - For IP-Adapter character conditioning
- **IP-Adapter Plus (SDXL)** - Character reference image conditioning
- **ControlNet Depth/Canny (SDXL)** - Structure-guided generation

### Custom Nodes
- **Capybara** - T2V, T2I, TI2I, TV2V generation (key for video-to-video pipeline)
- **ComfyUI-Manager** - Extension management
- **comfyui_controlnet_aux** - ControlNet preprocessors
- **ComfyUI_IPAdapter_plus** - Character reference conditioning
- **ComfyUI-VideoHelperSuite** - Video I/O utilities
- **ComfyUI-WanVideoWrapper** - Additional Wan model support

## Workflow Templates

Saved in `scripts/runpod/workflows/`:

| File | Description |
|------|-------------|
| `wan21_t2v_basic.json` | Wan 2.1 text-to-video (basic test) |
| `capybara_t2v.json` | Capybara text-to-video |
| `capybara_tv2v.json` | Capybara video-to-video (load input video first) |

Load these in ComfyUI UI via the "Load" button, or use `test_pod.py` to run via API.

## Architecture

```
Rex Server (this machine)          RunPod Cloud GPU
┌─────────────────────┐           ┌──────────────────────┐
│  launch_pod.py      │──API───>  │  RTX 4090 / A100     │
│  test_pod.py        │──HTTP──>  │  ComfyUI (port 8188) │
│  pod_setup.sh       │──SSH───>  │  Models + Nodes      │
│                     │           │  Character refs       │
│  rclone (R2)        │           │  Generated outputs    │
└─────────────────────┘           └──────────────────────┘
        │                                   │
        └───── R2 bucket ──────────────────┘
              (asset storage)
```

## Production Pipeline Vision

1. Render low-quality scene in Blender (on rex server)
2. Upload render to RunPod pod
3. Use ControlNet (depth map from render) + IP-Adapter (character ref) to style-transfer
4. Or use Capybara TV2V to transform the render into animation
5. Download result and upload to R2

This gives us: Blender camera control + AI animation quality.
