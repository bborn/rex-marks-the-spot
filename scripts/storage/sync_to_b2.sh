#!/bin/bash
# Sync local renders to Backblaze B2
# Usage: ./sync_to_b2.sh [--dry-run]

set -euo pipefail

B2_BUCKET="${B2_BUCKET:-fairy-dino-assets}"
LOCAL_RENDERS="${LOCAL_RENDERS:-./renders}"
REMOTE_PATH="renders/$(date +%Y-%m)"

DRY_RUN=""
if [[ "${1:-}" == "--dry-run" ]]; then
    DRY_RUN="--dry-run"
    echo "DRY RUN MODE - no files will be transferred"
fi

# Check if rclone is installed
if ! command -v rclone &> /dev/null; then
    echo "Error: rclone is not installed. Install with: curl https://rclone.org/install.sh | sudo bash"
    exit 1
fi

# Check if B2 remote is configured
if ! rclone listremotes | grep -q "^b2:$"; then
    echo "Error: B2 remote not configured in rclone."
    echo "Run: rclone config"
    echo "Or copy scripts/storage/rclone_config_template.conf to ~/.config/rclone/rclone.conf"
    exit 1
fi

# Check if local renders directory exists
if [[ ! -d "$LOCAL_RENDERS" ]]; then
    echo "Warning: Local renders directory does not exist: $LOCAL_RENDERS"
    echo "Creating empty directory..."
    mkdir -p "$LOCAL_RENDERS"
fi

echo "========================================"
echo "Syncing renders to Backblaze B2"
echo "========================================"
echo "Source: $LOCAL_RENDERS"
echo "Destination: b2:$B2_BUCKET/$REMOTE_PATH"
echo "========================================"

rclone sync $DRY_RUN \
    --progress \
    --transfers 8 \
    --checkers 16 \
    --exclude "*.tmp" \
    --exclude "**/cache/**" \
    --exclude "**/.DS_Store" \
    --min-size 1k \
    "$LOCAL_RENDERS" \
    "b2:$B2_BUCKET/$REMOTE_PATH"

echo ""
echo "========================================"
echo "Sync complete!"
echo "========================================"
echo ""
echo "Current B2 bucket usage:"
rclone size "b2:$B2_BUCKET" 2>/dev/null || echo "Could not retrieve bucket size"
