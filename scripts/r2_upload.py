#!/usr/bin/env python3
"""
Upload assets to Cloudflare R2 storage.

Usage:
    from r2_upload import upload_file, upload_directory

    # Upload a single file
    url = upload_file("output.png", "characters/family/gabe.png")

    # Upload a directory
    urls = upload_directory("./output/", "characters/family/")
"""

import subprocess
import os
from pathlib import Path
from typing import Optional, List, Tuple

R2_BUCKET = "rex-assets"
R2_PUBLIC_URL = "https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev"


def upload_file(local_path: str, r2_path: str) -> str:
    """
    Upload a single file to R2.

    Args:
        local_path: Path to local file
        r2_path: Destination path in R2 (e.g., "characters/family/gabe.png")

    Returns:
        Public URL of uploaded file
    """
    local_path = Path(local_path)
    if not local_path.exists():
        raise FileNotFoundError(f"File not found: {local_path}")

    r2_dest = f"r2:{R2_BUCKET}/{r2_path}"

    # Use rclone to upload
    result = subprocess.run(
        ["rclone", "copyto", str(local_path), r2_dest],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(f"Upload failed: {result.stderr}")

    public_url = f"{R2_PUBLIC_URL}/{r2_path}"
    print(f"Uploaded: {public_url}")
    return public_url


def upload_directory(local_dir: str, r2_prefix: str) -> List[Tuple[str, str]]:
    """
    Upload all files in a directory to R2.

    Args:
        local_dir: Path to local directory
        r2_prefix: Destination prefix in R2 (e.g., "characters/family/")

    Returns:
        List of (filename, public_url) tuples
    """
    local_dir = Path(local_dir)
    if not local_dir.is_dir():
        raise NotADirectoryError(f"Not a directory: {local_dir}")

    r2_dest = f"r2:{R2_BUCKET}/{r2_prefix.rstrip('/')}"

    # Use rclone to upload directory
    result = subprocess.run(
        ["rclone", "copy", str(local_dir), r2_dest, "--progress"],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(f"Upload failed: {result.stderr}")

    # Return list of uploaded files and their URLs
    uploaded = []
    for file in local_dir.iterdir():
        if file.is_file():
            r2_path = f"{r2_prefix.rstrip('/')}/{file.name}"
            public_url = f"{R2_PUBLIC_URL}/{r2_path}"
            uploaded.append((file.name, public_url))
            print(f"Uploaded: {public_url}")

    return uploaded


def get_public_url(r2_path: str) -> str:
    """Get the public URL for an R2 path."""
    return f"{R2_PUBLIC_URL}/{r2_path}"


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <local_path> <r2_path>")
        print(f"Example: {sys.argv[0]} output.png characters/family/gabe.png")
        sys.exit(1)

    local_path = sys.argv[1]
    r2_path = sys.argv[2]

    if os.path.isdir(local_path):
        upload_directory(local_path, r2_path)
    else:
        upload_file(local_path, r2_path)
