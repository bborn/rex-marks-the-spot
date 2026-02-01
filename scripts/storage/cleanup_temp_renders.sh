#!/bin/bash
# Remove temporary renders older than 7 days
# Run via cron: 0 2 * * * /path/to/cleanup_temp_renders.sh
#
# This script cleans up:
# - *.tmp files
# - *_test_* files (test renders)
# - *_preview_* files (preview renders)
# - cache directories

set -euo pipefail

RENDERS_DIR="${RENDERS_DIR:-./renders}"
DAYS_OLD="${DAYS_OLD:-7}"
DRY_RUN=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN="true"
            shift
            ;;
        --days)
            DAYS_OLD="$2"
            shift 2
            ;;
        --dir)
            RENDERS_DIR="$2"
            shift 2
            ;;
        *)
            echo "Usage: $0 [--dry-run] [--days N] [--dir PATH]"
            exit 1
            ;;
    esac
done

echo "========================================"
echo "Cleaning up temporary renders"
echo "========================================"
echo "Directory: $RENDERS_DIR"
echo "Older than: $DAYS_OLD days"
if [[ -n "$DRY_RUN" ]]; then
    echo "Mode: DRY RUN (no files will be deleted)"
fi
echo "========================================"

if [[ ! -d "$RENDERS_DIR" ]]; then
    echo "Warning: Renders directory does not exist: $RENDERS_DIR"
    exit 0
fi

# Count files before cleanup
TEMP_FILES=$(find "$RENDERS_DIR" -type f \( -name "*.tmp" -o -name "*_test_*" -o -name "*_preview_*" \) -mtime +$DAYS_OLD 2>/dev/null | wc -l)
CACHE_DIRS=$(find "$RENDERS_DIR" -type d -name "cache" 2>/dev/null | wc -l)

echo "Found $TEMP_FILES temporary files older than $DAYS_OLD days"
echo "Found $CACHE_DIRS cache directories"
echo ""

if [[ "$TEMP_FILES" -gt 0 ]]; then
    echo "Temporary files to clean:"
    if [[ -n "$DRY_RUN" ]]; then
        find "$RENDERS_DIR" -type f \( -name "*.tmp" -o -name "*_test_*" -o -name "*_preview_*" \) -mtime +$DAYS_OLD -print
    else
        find "$RENDERS_DIR" -type f \( -name "*.tmp" -o -name "*_test_*" -o -name "*_preview_*" \) -mtime +$DAYS_OLD -print -delete
    fi
fi

echo ""
echo "========================================"
echo "Cleanup complete!"
echo "========================================"

# Show disk usage after cleanup
if [[ -d "$RENDERS_DIR" ]]; then
    echo "Current renders directory size:"
    du -sh "$RENDERS_DIR" 2>/dev/null || echo "Could not determine size"
fi
