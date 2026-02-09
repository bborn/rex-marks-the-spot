#!/bin/bash
# Full pipeline to generate Leo 3D model with Meshy, render previews, and upload to R2.
#
# Usage:
#   MESHY_API_KEY=your_key ./scripts/run_leo_pipeline.sh
#
# Or to resume an existing Meshy task:
#   MESHY_API_KEY=your_key ./scripts/run_leo_pipeline.sh <task_id>

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
OUTPUT_DIR="$PROJECT_DIR/output/leo_meshy"

if [ -z "${MESHY_API_KEY:-}" ]; then
    echo "ERROR: MESHY_API_KEY environment variable not set"
    exit 1
fi

echo "=== Leo 3D Model Generation Pipeline ==="
echo ""

# Step 1: Generate model with Meshy
echo "--- Step 1: Generate 3D model with Meshy API ---"
cd "$PROJECT_DIR"
if [ -n "${1:-}" ]; then
    python3 scripts/generate_leo_meshy.py "$1"
else
    python3 scripts/generate_leo_meshy.py
fi

# Step 2: Verify model files exist
echo ""
echo "--- Step 2: Verify model files ---"
GLB_FILE="$OUTPUT_DIR/leo_meshy.glb"
FBX_FILE="$OUTPUT_DIR/leo_meshy.fbx"

if [ ! -f "$GLB_FILE" ]; then
    echo "ERROR: GLB file not found at $GLB_FILE"
    exit 1
fi
echo "GLB: $(du -h "$GLB_FILE" | cut -f1)"
[ -f "$FBX_FILE" ] && echo "FBX: $(du -h "$FBX_FILE" | cut -f1)" || echo "FBX: not generated"

# Step 3: Render preview images in Blender
echo ""
echo "--- Step 3: Render preview images ---"
PREVIEW_DIR="$OUTPUT_DIR/previews"
mkdir -p "$PREVIEW_DIR"

blender --background --python scripts/render_leo_previews.py -- "$GLB_FILE" "$PREVIEW_DIR" 2>&1 | \
    grep -E "(Rendering|Saved|Imported|Error)" || true

echo "Preview renders:"
ls -la "$PREVIEW_DIR/"*.png 2>/dev/null || echo "  No preview images generated"

# Step 4: Upload to R2
echo ""
echo "--- Step 4: Upload to R2 ---"

echo "Uploading GLB..."
rclone copyto "$GLB_FILE" "r2:rex-assets/3d-models/characters/leo/leo_meshy.glb"
echo "  -> https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/3d-models/characters/leo/leo_meshy.glb"

if [ -f "$FBX_FILE" ]; then
    echo "Uploading FBX..."
    rclone copyto "$FBX_FILE" "r2:rex-assets/3d-models/characters/leo/leo_meshy.fbx"
    echo "  -> https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/3d-models/characters/leo/leo_meshy.fbx"
fi

if ls "$PREVIEW_DIR/"*.png 1> /dev/null 2>&1; then
    echo "Uploading previews..."
    rclone copy "$PREVIEW_DIR/" "r2:rex-assets/3d-models/characters/previews/"
    for f in "$PREVIEW_DIR/"*.png; do
        echo "  -> https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/3d-models/characters/previews/$(basename "$f")"
    done
fi

echo ""
echo "=== Pipeline Complete ==="
echo ""
echo "R2 URLs:"
echo "  GLB: https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/3d-models/characters/leo/leo_meshy.glb"
echo "  FBX: https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/3d-models/characters/leo/leo_meshy.fbx"
echo "  Previews: https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/3d-models/characters/previews/"
