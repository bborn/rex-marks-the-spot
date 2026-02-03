#!/bin/bash
# Convert rendered frames to video using ffmpeg
#
# Usage:
#   ./scripts/frames_to_video.sh renders/test_animation/frame_ 24 output.mp4
#
# Arguments:
#   $1 - Frame path prefix (e.g., renders/test_animation/frame_)
#   $2 - Framerate (default: 24)
#   $3 - Output file (default: renders/test_animation.mp4)

FRAME_PREFIX="${1:-renders/test_animation/frame_}"
FRAMERATE="${2:-24}"
OUTPUT="${3:-renders/test_animation.mp4}"

# Check if ffmpeg is available
if ! command -v ffmpeg &> /dev/null; then
    echo "Error: ffmpeg is not installed"
    echo "Install with: sudo apt install ffmpeg"
    exit 1
fi

# Check if frames exist
FIRST_FRAME="${FRAME_PREFIX}0001.png"
if [ ! -f "$FIRST_FRAME" ]; then
    echo "Error: No frames found at ${FRAME_PREFIX}*.png"
    echo "First expected frame: $FIRST_FRAME"
    exit 1
fi

# Count frames
FRAME_COUNT=$(ls -1 ${FRAME_PREFIX}*.png 2>/dev/null | wc -l)
echo "Found $FRAME_COUNT frames"

# Create output directory if needed
OUTPUT_DIR=$(dirname "$OUTPUT")
mkdir -p "$OUTPUT_DIR"

echo "Converting frames to video..."
echo "  Input: ${FRAME_PREFIX}%04d.png"
echo "  Framerate: $FRAMERATE fps"
echo "  Output: $OUTPUT"

ffmpeg -y -framerate "$FRAMERATE" \
    -i "${FRAME_PREFIX}%04d.png" \
    -c:v libx264 \
    -preset medium \
    -crf 18 \
    -pix_fmt yuv420p \
    -movflags +faststart \
    "$OUTPUT"

if [ $? -eq 0 ]; then
    echo ""
    echo "Video created successfully: $OUTPUT"

    # Get video info
    DURATION=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$OUTPUT" 2>/dev/null)
    FILESIZE=$(du -h "$OUTPUT" | cut -f1)

    echo "  Duration: ${DURATION}s"
    echo "  File size: $FILESIZE"
else
    echo "Error: ffmpeg conversion failed"
    exit 1
fi
