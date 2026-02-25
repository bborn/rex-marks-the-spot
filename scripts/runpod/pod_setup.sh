#!/bin/bash
# Pod Setup Script - Run this ON the RunPod pod after launch.
#
# This script installs all required models, custom nodes, and character
# references for the Rex Marks the Spot video generation pipeline.
#
# Usage (on the pod via SSH or terminal):
#   bash /workspace/pod_setup.sh
#
# Or remotely:
#   ssh root@<pod-ip> -p <port> 'bash -s' < scripts/runpod/pod_setup.sh

set -euo pipefail

echo "============================================"
echo "  Rex Marks the Spot - ComfyUI Pod Setup"
echo "============================================"

# Paths - RunPod ComfyUI template uses /workspace
COMFYUI_DIR="${COMFYUI_DIR:-/workspace/ComfyUI}"
MODELS_DIR="$COMFYUI_DIR/models"
CUSTOM_NODES_DIR="$COMFYUI_DIR/custom_nodes"

# Verify ComfyUI exists
if [ ! -d "$COMFYUI_DIR" ]; then
    echo "ERROR: ComfyUI not found at $COMFYUI_DIR"
    echo "Expected the RunPod ComfyUI template. Check your pod setup."
    exit 1
fi

echo "ComfyUI found at: $COMFYUI_DIR"
echo ""

# ============================================
# 1. Install Custom Nodes
# ============================================
echo "--- Installing Custom Nodes ---"
cd "$CUSTOM_NODES_DIR"

install_node() {
    local repo_url="$1"
    local dir_name="$2"
    if [ -d "$dir_name" ]; then
        echo "  [exists] $dir_name - updating..."
        cd "$dir_name" && git pull --ff-only 2>/dev/null || true && cd ..
    else
        echo "  [install] $dir_name"
        git clone "$repo_url" "$dir_name"
    fi
}

# ComfyUI Manager (may already be installed in template)
install_node "https://github.com/ltdrdata/ComfyUI-Manager.git" "ComfyUI-Manager"

# Capybara - video generation (t2v, t2i, ti2i, tv2v)
install_node "https://github.com/xgen-universe/Capybara.git" "Capybara"

# ControlNet Auxiliary Preprocessors (depth, normal, canny, etc.)
install_node "https://github.com/Fannovel16/comfyui_controlnet_aux.git" "comfyui_controlnet_aux"

# IP-Adapter Plus (character reference conditioning)
install_node "https://github.com/cubiq/ComfyUI_IPAdapter_plus.git" "ComfyUI_IPAdapter_plus"

# Video Helper Suite (video I/O)
install_node "https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git" "ComfyUI-VideoHelperSuite"

# Wan Video Nodes (additional Wan model support)
install_node "https://github.com/kijai/ComfyUI-WanVideoWrapper.git" "ComfyUI-WanVideoWrapper"

# Install Python dependencies for custom nodes
echo ""
echo "--- Installing Python dependencies for custom nodes ---"
for req_file in "$CUSTOM_NODES_DIR"/*/requirements.txt; do
    if [ -f "$req_file" ]; then
        echo "  Installing deps from: $(basename $(dirname $req_file))"
        pip install -r "$req_file" --quiet 2>/dev/null || echo "  Warning: some deps failed for $req_file"
    fi
done

# ============================================
# 2. Download Models
# ============================================
echo ""
echo "--- Downloading Models ---"

download_model() {
    local url="$1"
    local dest="$2"
    local filename=$(basename "$dest")
    if [ -f "$dest" ]; then
        echo "  [exists] $filename"
        return
    fi
    mkdir -p "$(dirname "$dest")"
    echo "  [download] $filename..."
    wget -q --show-progress -O "$dest" "$url" || {
        echo "  ERROR downloading $filename"
        rm -f "$dest"
        return 1
    }
}

# --- Wan 2.1 Models ---
echo ""
echo "= Wan 2.1 Video Models ="

# Wan 2.1 T2V 14B (higher quality, needs 24GB+ VRAM)
download_model \
    "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/diffusion_models/wan2.1_t2v_14B_bf16-00001-of-00003.safetensors" \
    "$MODELS_DIR/diffusion_models/wan2.1_t2v_14B_bf16-00001-of-00003.safetensors"

download_model \
    "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/diffusion_models/wan2.1_t2v_14B_bf16-00002-of-00003.safetensors" \
    "$MODELS_DIR/diffusion_models/wan2.1_t2v_14B_bf16-00002-of-00003.safetensors"

download_model \
    "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/diffusion_models/wan2.1_t2v_14B_bf16-00003-of-00003.safetensors" \
    "$MODELS_DIR/diffusion_models/wan2.1_t2v_14B_bf16-00003-of-00003.safetensors"

# Wan 2.1 T2V 1.3B (faster, lower VRAM)
download_model \
    "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/diffusion_models/wan2.1_t2v_1.3B_bf16.safetensors" \
    "$MODELS_DIR/diffusion_models/wan2.1_t2v_1.3B_bf16.safetensors"

# Wan 2.1 I2V 14B (image-to-video)
download_model \
    "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/diffusion_models/wan2.1_i2v_720p_14B_bf16-00001-of-00003.safetensors" \
    "$MODELS_DIR/diffusion_models/wan2.1_i2v_720p_14B_bf16-00001-of-00003.safetensors"

download_model \
    "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/diffusion_models/wan2.1_i2v_720p_14B_bf16-00002-of-00003.safetensors" \
    "$MODELS_DIR/diffusion_models/wan2.1_i2v_720p_14B_bf16-00002-of-00003.safetensors"

download_model \
    "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/diffusion_models/wan2.1_i2v_720p_14B_bf16-00003-of-00003.safetensors" \
    "$MODELS_DIR/diffusion_models/wan2.1_i2v_720p_14B_bf16-00003-of-00003.safetensors"

# Wan text encoders and VAE
download_model \
    "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors" \
    "$MODELS_DIR/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors"

download_model \
    "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors" \
    "$MODELS_DIR/vae/wan_2.1_vae.safetensors"

# --- CLIP Vision (for IP-Adapter) ---
echo ""
echo "= CLIP Vision Models (for IP-Adapter) ="

mkdir -p "$MODELS_DIR/clip_vision"

download_model \
    "https://huggingface.co/h94/IP-Adapter/resolve/main/models/image_encoder/model.safetensors" \
    "$MODELS_DIR/clip_vision/CLIP-ViT-H-14-laion2B-s32B-b79K.safetensors"

download_model \
    "https://huggingface.co/h94/IP-Adapter/resolve/main/sdxl_models/image_encoder/model.safetensors" \
    "$MODELS_DIR/clip_vision/CLIP-ViT-bigG-14-laion2B-39B-b160k.safetensors"

# --- IP-Adapter Models ---
echo ""
echo "= IP-Adapter Models ="

mkdir -p "$MODELS_DIR/ipadapter"

download_model \
    "https://huggingface.co/h94/IP-Adapter/resolve/main/sdxl_models/ip-adapter-plus_sdxl_vit-h.safetensors" \
    "$MODELS_DIR/ipadapter/ip-adapter-plus_sdxl_vit-h.safetensors"

download_model \
    "https://huggingface.co/h94/IP-Adapter/resolve/main/sdxl_models/ip-adapter-plus-face_sdxl_vit-h.safetensors" \
    "$MODELS_DIR/ipadapter/ip-adapter-plus-face_sdxl_vit-h.safetensors"

# --- ControlNet Models ---
echo ""
echo "= ControlNet Models ="

mkdir -p "$MODELS_DIR/controlnet"

# Depth ControlNet for SDXL
download_model \
    "https://huggingface.co/diffusers/controlnet-depth-sdxl-1.0/resolve/main/diffusion_pytorch_model.fp16.safetensors" \
    "$MODELS_DIR/controlnet/controlnet-depth-sdxl-fp16.safetensors"

# Canny ControlNet for SDXL
download_model \
    "https://huggingface.co/diffusers/controlnet-canny-sdxl-1.0/resolve/main/diffusion_pytorch_model.fp16.safetensors" \
    "$MODELS_DIR/controlnet/controlnet-canny-sdxl-fp16.safetensors"

echo ""
echo "--- Model download complete ---"

# ============================================
# 3. Download Character Reference Images
# ============================================
echo ""
echo "--- Downloading Character References ---"

CHAR_REF_DIR="$COMFYUI_DIR/input/character_references"
mkdir -p "$CHAR_REF_DIR"

R2_BASE="https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev"

download_model "$R2_BASE/characters/gabe/gabe_turnaround_APPROVED.png" \
    "$CHAR_REF_DIR/gabe_turnaround_APPROVED.png"

download_model "$R2_BASE/characters/nina/nina_turnaround_APPROVED.png" \
    "$CHAR_REF_DIR/nina_turnaround_APPROVED.png"

download_model "$R2_BASE/characters/mia/mia_turnaround_APPROVED_ALT.png" \
    "$CHAR_REF_DIR/mia_turnaround_APPROVED_ALT.png"

download_model "$R2_BASE/characters/leo/leo_turnaround_APPROVED.png" \
    "$CHAR_REF_DIR/leo_turnaround_APPROVED.png"

# Also download other characters for future use
download_model "$R2_BASE/characters/ruben/ruben_turnaround_APPROVED.png" \
    "$CHAR_REF_DIR/ruben_turnaround_APPROVED.png"

download_model "$R2_BASE/characters/jenny/jenny_turnaround_APPROVED.png" \
    "$CHAR_REF_DIR/jenny_turnaround_APPROVED.png"

download_model "$R2_BASE/characters/jetplane/jetplane_turnaround_APPROVED.png" \
    "$CHAR_REF_DIR/jetplane_turnaround_APPROVED.png"

echo ""
echo "Character references saved to: $CHAR_REF_DIR"

# ============================================
# 4. Verify Installation
# ============================================
echo ""
echo "--- Verification ---"

echo "Custom Nodes installed:"
ls -1d "$CUSTOM_NODES_DIR"/*/ | while read dir; do
    echo "  $(basename "$dir")"
done

echo ""
echo "Models downloaded:"
find "$MODELS_DIR" -name "*.safetensors" -o -name "*.bin" -o -name "*.ckpt" | sort | while read f; do
    size=$(du -sh "$f" | cut -f1)
    echo "  $size  $(echo "$f" | sed "s|$MODELS_DIR/||")"
done

echo ""
echo "Character references:"
ls -la "$CHAR_REF_DIR/" 2>/dev/null || echo "  (none found)"

echo ""
echo "Disk usage:"
df -h /workspace | tail -1

echo ""
echo "============================================"
echo "  Setup complete!"
echo "  Restart ComfyUI to load new nodes:"
echo "    systemctl restart comfyui"
echo "    # or kill and restart the ComfyUI process"
echo "============================================"
