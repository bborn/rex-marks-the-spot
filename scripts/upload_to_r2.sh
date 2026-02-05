#!/bin/bash
# Upload assets to Cloudflare R2 instead of committing to git
# Usage: ./scripts/upload_to_r2.sh <local_path> [r2_prefix]
# Example: ./scripts/upload_to_r2.sh assets/characters/family/action-poses/ characters/family/action-poses/

set -e

R2_BUCKET="rex-assets"
R2_PUBLIC_URL="https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev"

LOCAL_PATH="${1:?Usage: $0 <local_path> [r2_prefix]}"
R2_PREFIX="${2:-$(dirname "$LOCAL_PATH" | sed 's|^assets/||')}"

# Check if rclone is configured
if ! rclone listremotes | grep -q "^r2:"; then
    echo "ERROR: rclone 'r2' remote not configured"
    echo "Run: rclone config"
    exit 1
fi

echo "Uploading: $LOCAL_PATH"
echo "To: r2:$R2_BUCKET/$R2_PREFIX"

# Upload files
if [ -d "$LOCAL_PATH" ]; then
    rclone copy "$LOCAL_PATH" "r2:$R2_BUCKET/$R2_PREFIX" --progress
else
    rclone copy "$LOCAL_PATH" "r2:$R2_BUCKET/$(dirname "$R2_PREFIX")/" --progress
fi

echo ""
echo "Upload complete!"
echo "Public URL: $R2_PUBLIC_URL/$R2_PREFIX"

# List uploaded files
echo ""
echo "Uploaded files:"
rclone ls "r2:$R2_BUCKET/$R2_PREFIX"
