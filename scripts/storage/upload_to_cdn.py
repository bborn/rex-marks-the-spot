#!/usr/bin/env python3
"""Upload approved assets to Cloudflare R2 for public CDN delivery.

This script syncs approved public-facing assets to Cloudflare R2 for CDN delivery.
It's designed to be run manually or as part of a CI/CD pipeline after assets are approved.

Usage:
    python upload_to_cdn.py [--dry-run] [--verbose]

Environment Variables:
    R2_BUCKET: Override the default R2 bucket name (default: fairy-dino-public)

Prerequisites:
    1. Install rclone: curl https://rclone.org/install.sh | sudo bash
    2. Configure R2 remote in ~/.config/rclone/rclone.conf (see rclone_config_template.conf)
"""

import subprocess
import sys
import os
from pathlib import Path
from typing import List, Tuple

# Configuration
R2_BUCKET = os.environ.get("R2_BUCKET", "fairy-dino-public")

# Asset mappings: (local_path, remote_path)
# Uses glob patterns for flexible matching
PUBLIC_ASSETS: List[Tuple[str, str]] = [
    # Character concept art for website
    ("./assets/characters/*/concept-art/*.png", "website/characters/"),
    ("./assets/characters/*/concept-art/*.jpg", "website/characters/"),

    # Final video renders
    ("./renders/final/*.mp4", "website/videos/"),
    ("./renders/final/*.webm", "website/videos/"),

    # Trailer and teasers
    ("./video/trailers/*.mp4", "website/trailers/"),

    # Press kit materials
    ("./press-kit/*", "press-kit/"),

    # Social media assets
    ("./social/exports/*.png", "social/"),
    ("./social/exports/*.mp4", "social/"),
]


def check_rclone() -> bool:
    """Check if rclone is installed and R2 remote is configured."""
    try:
        result = subprocess.run(
            ["rclone", "listremotes"],
            capture_output=True,
            text=True,
            check=True
        )
        if "r2:" not in result.stdout:
            print("Error: R2 remote not configured in rclone.")
            print("Run: rclone config")
            print("Or copy scripts/storage/rclone_config_template.conf to ~/.config/rclone/rclone.conf")
            return False
        return True
    except FileNotFoundError:
        print("Error: rclone is not installed.")
        print("Install with: curl https://rclone.org/install.sh | sudo bash")
        return False
    except subprocess.CalledProcessError as e:
        print(f"Error checking rclone: {e}")
        return False


def sync_to_r2(local_pattern: str, remote_path: str, dry_run: bool = False, verbose: bool = False) -> bool:
    """Sync files matching pattern to R2.

    Args:
        local_pattern: Glob pattern for local files (e.g., "./renders/final/*.mp4")
        remote_path: Destination path in R2 bucket
        dry_run: If True, show what would be synced without actually syncing
        verbose: If True, show detailed output

    Returns:
        True if sync was successful, False otherwise
    """
    local_path = Path(local_pattern)
    parent_dir = local_path.parent
    file_pattern = local_path.name

    # Check if parent directory exists
    if not parent_dir.exists():
        if verbose:
            print(f"  Skipping: {parent_dir} does not exist")
        return True

    # Check if there are any matching files
    matching_files = list(parent_dir.glob(file_pattern))
    if not matching_files:
        if verbose:
            print(f"  Skipping: No files matching {file_pattern} in {parent_dir}")
        return True

    cmd = [
        "rclone", "copy",
        "--include", file_pattern,
        str(parent_dir),
        f"r2:{R2_BUCKET}/{remote_path}",
        "--progress",
    ]

    if dry_run:
        cmd.append("--dry-run")

    if verbose:
        cmd.append("-v")

    try:
        print(f"  Syncing {len(matching_files)} file(s)...")
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"  Error syncing: {e}")
        return False


def main():
    """Main entry point."""
    dry_run = "--dry-run" in sys.argv
    verbose = "--verbose" in sys.argv or "-v" in sys.argv

    print("========================================")
    print("Uploading assets to Cloudflare R2 CDN")
    print("========================================")
    print(f"Bucket: {R2_BUCKET}")
    if dry_run:
        print("Mode: DRY RUN (no files will be transferred)")
    print("========================================")
    print()

    # Check prerequisites
    if not check_rclone():
        sys.exit(1)

    # Sync each asset type
    success_count = 0
    fail_count = 0

    for local_pattern, remote_path in PUBLIC_ASSETS:
        print(f"Processing: {local_pattern} -> {remote_path}")
        if sync_to_r2(local_pattern, remote_path, dry_run, verbose):
            success_count += 1
        else:
            fail_count += 1
        print()

    # Summary
    print("========================================")
    print("CDN sync complete!")
    print(f"  Successful: {success_count}")
    print(f"  Failed: {fail_count}")
    print("========================================")

    # Show bucket size
    if not dry_run:
        print()
        print("Current R2 bucket usage:")
        try:
            subprocess.run(["rclone", "size", f"r2:{R2_BUCKET}"], check=False)
        except Exception:
            print("Could not retrieve bucket size")

    sys.exit(0 if fail_count == 0 else 1)


if __name__ == "__main__":
    main()
