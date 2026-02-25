# RunPod GPU Cloud - ComfyUI Video Generation

GPU cloud infrastructure for AI video/image generation using ComfyUI.

## Current Pod

| Detail | Value |
|--------|-------|
| **Pod ID** | `b0zwt2jb434e97` |
| **GPU** | NVIDIA L40S (48 GB VRAM) |
| **ComfyUI URL** | https://b0zwt2jb434e97-8188.proxy.runpod.net |
| **SSH** | `ssh -i ~/.ssh/id_ed25519 root@60.249.37.148 -p 26374` |
| **Cost** | $0.79/hr |
| **PyTorch** | 2.6.0+cu124 |
| **Image** | runpod/pytorch:2.4.0-py3.11-cuda12.4.1 (upgraded to PyTorch 2.6) |
| **Volume** | 100 GB persistent at /workspace |

**STOP THE POD when not in use:**
```bash
python scripts/runpod/launch_pod.py --stop
```

## Quick Start

### Managing the pod

```bash
# Set API key (already saved at ~/.runpod_api_key)
export RUNPOD_API_KEY="your_key_here"

# Check status
python scripts/runpod/launch_pod.py --status

# Stop pod (saves $$$, preserves volume data)
python scripts/runpod/launch_pod.py --stop

# Restart stopped pod
python scripts/runpod/launch_pod.py --start

# Terminate (DESTROYS all data)
python scripts/runpod/launch_pod.py --terminate
```

### After restarting the pod

ComfyUI doesn't auto-start. SSH in and start it:

```bash
ssh -i ~/.ssh/id_ed25519 root@60.249.37.148 -p 26374
cd /workspace/ComfyUI && python main.py --listen 0.0.0.0 --port 8188 &
```

Note: SSH port changes on restart - check `python scripts/runpod/launch_pod.py --status` for the new port.

### Running test workflows

```bash
# Via SSH (recommended - proxy blocks POST requests):
ssh -i ~/.ssh/id_ed25519 root@<ip> -p <port>
cd /workspace/ComfyUI
# Queue workflows via localhost:8188

# Or use the web UI:
# Open the ComfyUI proxy URL in your browser
```

## Cost Management

**RunPod bills per-second. ALWAYS stop the pod when not in use.**

| Action | Cost |
|--------|------|
| L40S running | $0.79/hr |
| RTX 4090 running | ~$0.44/hr |
| Pod stopped (volume only) | ~$0.10/GB/month |
| 100 GB volume stopped | ~$10/month |

**Tip:** Stop after each session. A 2-hour session = ~$1.58 on L40S.

## Installed Components

### Models
| Model | Size | Purpose |
|-------|------|---------|
| Wan 2.1 T2V 1.3B (bf16) | 2.7 GB | Fast text-to-video |
| UMT5-XXL (fp8 scaled) | 6.3 GB | Text encoder for Wan |
| Wan 2.1 VAE | 243 MB | Video decode |
| CLIP Vision ViT-H-14 | 2.4 GB | IP-Adapter image encoding |
| Capybara (full model) | 45 GB | T2V, T2I, TI2I, TV2V |

### Custom Nodes (6 installed)
| Node | Purpose | Status |
|------|---------|--------|
| Capybara | T2V, T2I, TI2I, TV2V generation | 5 nodes loaded |
| ComfyUI-Manager | Extension management | Working |
| comfyui_controlnet_aux | ControlNet preprocessors | Working |
| ComfyUI_IPAdapter_plus | Character reference conditioning | Working |
| ComfyUI-VideoHelperSuite | Video I/O utilities | Working |
| ComfyUI-WanVideoWrapper | Wan 2.1 model support | 139 nodes loaded |

### Character References (uploaded)
All approved turnaround sheets are at `/workspace/ComfyUI/input/character_references/`:
- gabe_turnaround_APPROVED.png
- nina_turnaround_APPROVED.png
- mia_turnaround_APPROVED_ALT.png
- leo_turnaround_APPROVED.png
- ruben_turnaround_APPROVED.png
- jenny_turnaround_APPROVED.png
- jetplane_turnaround_APPROVED.png

## Test Results

### Wan 2.1 T2V (1.3B) - PASSED
- Resolution: 480x320, 33 frames, 20 steps
- Generation time: **20 seconds** on L40S
- Output: https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/comfyui-tests/wan21_t2v_test_00001.mp4
- Workflow: Uses native ComfyUI nodes (CLIPLoader type=wan + KSampler)

### Capybara T2V - PASSED
- Resolution: 480p 16:9, 33 frames, 20 steps
- Generation time: **3 minutes** on L40S (includes model loading)
- Output: https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/comfyui-tests/capybara_t2v_test_00001.mp4
- Model: 45 GB Capybara checkpoint at /workspace/capybara_model

### Capybara TV2V (Video-to-Video) - PASSED
- Input: Wan 2.1 T2V output, prompt-guided style transfer
- Generation time: **2 minutes** on L40S
- Output: https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/comfyui-tests/capybara_tv2v_test_00001.mp4
- This is the key capability for the Blender-render-to-AI-polish pipeline

## Workflow Templates

Saved in `scripts/runpod/workflows/`:

| File | Description | Status |
|------|-------------|--------|
| `wan21_t2v_basic.json` | Wan 2.1 T2V (native ComfyUI nodes) | TESTED |
| `capybara_t2v.json` | Capybara text-to-video | Untested |
| `capybara_tv2v.json` | Capybara video-to-video | Untested |

## Architecture

```
Rex Server (this machine)          RunPod Cloud GPU (L40S 48GB)
┌─────────────────────┐           ┌──────────────────────┐
│  launch_pod.py      │──API───>  │  ComfyUI 0.15.0      │
│  pod_setup.sh       │──SSH───>  │  Wan 2.1 T2V 1.3B    │
│                     │           │  Capybara (45GB)      │
│  rclone (R2)        │           │  Character refs       │
└─────────────────────┘           └──────────────────────┘
        │                                   │
        └───── R2 bucket ──────────────────┘
              (asset storage)
```

## Known Issues & Setup Notes

1. **RunPod proxy blocks POST** - Cannot queue workflows via the proxy URL. Use SSH + localhost:8188 for API calls, or use the web UI for interactive work.
2. **WanVideoWrapper text encoder** - The fp8_scaled text encoder isn't supported by WanVideoWrapper nodes. Use built-in ComfyUI `CLIPLoader(type=wan)` instead.
3. **PyTorch upgrade required** - Base image has PyTorch 2.4 but Capybara needs 2.6. Pod is upgraded to 2.6.0+cu124.
4. **Package version pinning** - Critical combo: `torch==2.6.0, diffusers==0.36.0, transformers==4.49.0, torchao==0.8.0`. Other combos cause import chain failures.
5. **ComfyUI doesn't auto-start** - Must be started manually after pod restart.

## Production Pipeline Vision

1. Render low-quality scene in Blender (on rex server)
2. Upload render to RunPod pod
3. Use ControlNet (depth map from render) + IP-Adapter (character ref) to style-transfer
4. Or use Capybara TV2V to transform the render into animation
5. Download result and upload to R2

This gives us: Blender camera control + AI animation quality.
