# ComfyUI Setup on Rex Server

## Server Specs
- **CPU:** AMD EPYC-Rome, 16 cores
- **RAM:** 30 GB
- **Disk:** 338 GB (275+ GB free after model downloads)
- **GPU:** None (CPU-only mode) - **GPU required for practical video generation**
- **OS:** Ubuntu Linux 6.8.0-90-generic

## Access
- **Web UI:** http://5.161.224.250:8188
- **Installation:** /home/rex/ComfyUI
- **Service:** `sudo systemctl {start|stop|restart|status} comfyui`

## Installed Components

### Core
- ComfyUI 0.15.0
- PyTorch 2.10.0+cpu
- Python 3.12.3

### Custom Nodes (Extensions)
| Extension | Purpose | Status |
|-----------|---------|--------|
| ComfyUI-Manager | Extension management UI | Working |
| comfyui_controlnet_aux | ControlNet preprocessors (depth, normal, etc.) | Working |
| ComfyUI_IPAdapter_plus | Character reference image conditioning | Working |
| Capybara (xgen-universe) | T2V, T2I, TI2I, TV2V generation | Working |
| ComfyUI-VideoHelperSuite | Video loading/saving utilities | Working |

### Downloaded Models
| Model | Size | Path |
|-------|------|------|
| Wan 2.1 T2V 1.3B (bf16) | 2.84 GB | models/diffusion_models/ |
| UMT5-XXL text encoder (fp8) | 6.74 GB | models/text_encoders/ |
| Wan 2.1 VAE | 0.25 GB | models/vae/ |

### Available Node Types (784 total)
- **Capybara (5):** CapybaraLoadPipeline, CapybaraLoadVideo, CapybaraLoadRewriteModel, CapybaraRewriteInstruction, CapybaraGenerate
- **ControlNet (14):** Full preprocessing and application pipeline
- **IPAdapter (35):** Full suite including FaceID, tiled, batch, style composition
- **Wan (29):** T2V, I2V, camera control, tracking, VACE, and more

## GPU Requirement

**This server currently has NO GPU.** ComfyUI runs in CPU-only mode. Video generation
models like Wan 2.1 and Capybara require a GPU (minimum 8GB VRAM, recommended 24GB+)
for practical use. Running on CPU would take hours per short video clip.

### To add GPU support:
1. Migrate to a GPU-enabled VM or add a GPU to this server
2. Install CUDA toolkit and drivers
3. Reinstall PyTorch with CUDA: `pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124`
4. Restart ComfyUI service (it auto-detects GPU)

## Management

```bash
# Service control
sudo systemctl start comfyui
sudo systemctl stop comfyui
sudo systemctl restart comfyui
sudo systemctl status comfyui

# View logs
sudo journalctl -u comfyui -f

# Manual start (for debugging)
cd /home/rex/ComfyUI
./start_comfyui.sh

# Install new extensions via CLI
cd /home/rex/ComfyUI/custom_nodes
git clone <extension-repo-url>
sudo systemctl restart comfyui
```

## Additional Models to Download (When GPU Available)

For the movie production pipeline, these additional models would be useful:

```bash
# Wan 2.1 14B (higher quality, needs 24GB+ VRAM)
# HunyuanVideo 1.5 checkpoints (for Capybara)
# ControlNet models (depth, normal map)
# IP-Adapter models (for character conditioning)
```

These can be downloaded via ComfyUI-Manager UI or manually to the models/ directories.
