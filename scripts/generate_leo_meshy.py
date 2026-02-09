#!/usr/bin/env python3
"""
Generate Leo 3D model using Meshy API (image-to-3D).

Uses Leo's approved turnaround image as input to generate a production-quality
3D model with PBR textures and rigging-ready topology.

Usage:
    MESHY_API_KEY=your_key python scripts/generate_leo_meshy.py
"""

import json
import os
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

MESHY_API_BASE = "https://api.meshy.ai/openapi/v1"
LEO_TURNAROUND_URL = "https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/characters/leo/leo_turnaround_APPROVED.png"
OUTPUT_DIR = Path("output/leo_meshy")


def get_api_key():
    key = os.environ.get("MESHY_API_KEY", "")
    if not key:
        print("ERROR: MESHY_API_KEY environment variable not set")
        sys.exit(1)
    return key


def meshy_request(method, endpoint, api_key, data=None):
    """Make a request to the Meshy API."""
    url = f"{MESHY_API_BASE}/{endpoint}"
    headers = {
        "Authorization": f"Bearer {api_key}",
    }

    if data is not None:
        headers["Content-Type"] = "application/json"
        body = json.dumps(data).encode("utf-8")
    else:
        body = None

    req = urllib.request.Request(url, data=body, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        print(f"API Error {e.code}: {error_body}")
        raise


def create_image_to_3d_task(api_key):
    """Submit an image-to-3D generation task."""
    payload = {
        "image_url": LEO_TURNAROUND_URL,
        "ai_model": "meshy-6",
        "topology": "quad",
        "target_polycount": 50000,
        "should_texture": True,
        "enable_pbr": True,
        "texture_prompt": "Young boy character, approximately 5 years old, wearing green dinosaur pajamas with dinosaur pattern, holding a small brown T-Rex plush toy. Pixar-style 3D animated character with warm skin tones, big expressive eyes, messy brown hair. Soft fabric texture on pajamas.",
        "symmetry_mode": "auto",
    }

    print("Submitting image-to-3D task to Meshy...")
    print(f"  Image URL: {LEO_TURNAROUND_URL}")
    print(f"  AI Model: {payload['ai_model']}")
    print(f"  Topology: {payload['topology']}")
    print(f"  Target polycount: {payload['target_polycount']}")
    print(f"  PBR enabled: {payload['enable_pbr']}")

    result = meshy_request("POST", "image-to-3d", api_key, payload)
    task_id = result.get("result")
    print(f"Task created: {task_id}")
    return task_id


def poll_task(api_key, task_id, poll_interval=10, max_wait=600):
    """Poll task status until completion."""
    print(f"\nPolling task {task_id} (max {max_wait}s)...")
    elapsed = 0

    while elapsed < max_wait:
        result = meshy_request("GET", f"image-to-3d/{task_id}", api_key)
        status = result.get("status", "UNKNOWN")
        progress = result.get("progress", 0)

        print(f"  [{elapsed:>3}s] Status: {status}, Progress: {progress}%")

        if status == "SUCCEEDED":
            print("Task completed successfully!")
            return result
        elif status in ("FAILED", "CANCELED"):
            print(f"Task {status}!")
            print(f"  Error: {result.get('task_error', {})}")
            sys.exit(1)

        time.sleep(poll_interval)
        elapsed += poll_interval

    print(f"Timeout after {max_wait}s")
    sys.exit(1)


def download_file(url, dest_path):
    """Download a file from URL."""
    dest_path = Path(dest_path)
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"  Downloading: {dest_path.name}")
    urllib.request.urlretrieve(url, str(dest_path))
    size_mb = dest_path.stat().st_size / (1024 * 1024)
    print(f"    Saved: {dest_path} ({size_mb:.1f} MB)")
    return dest_path


def download_model_files(task_result):
    """Download all model files and textures."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    model_urls = task_result.get("model_urls", {})
    texture_urls = task_result.get("texture_urls", [])

    downloaded = {}

    # Download model files
    print("\nDownloading model files...")
    for fmt, url in model_urls.items():
        if url and fmt in ("glb", "fbx"):
            dest = OUTPUT_DIR / f"leo_meshy.{fmt}"
            download_file(url, dest)
            downloaded[fmt] = dest

    # Download texture maps
    if texture_urls:
        print("\nDownloading texture maps...")
        tex_dir = OUTPUT_DIR / "textures"
        tex_dir.mkdir(exist_ok=True)
        for tex in texture_urls:
            if isinstance(tex, dict):
                for tex_type, tex_url in tex.items():
                    if tex_url:
                        ext = tex_url.rsplit(".", 1)[-1].split("?")[0]
                        dest = tex_dir / f"leo_{tex_type}.{ext}"
                        download_file(tex_url, dest)
            elif isinstance(tex, str):
                name = tex.rsplit("/", 1)[-1].split("?")[0]
                download_file(tex, tex_dir / name)

    # Save task result for reference
    result_path = OUTPUT_DIR / "task_result.json"
    with open(result_path, "w") as f:
        json.dump(task_result, f, indent=2)
    print(f"\nTask result saved to {result_path}")

    return downloaded


def main():
    api_key = get_api_key()

    # Check if we're resuming a previous task
    if len(sys.argv) > 1 and sys.argv[1].strip():
        task_id = sys.argv[1].strip()
        print(f"Resuming task: {task_id}")
    else:
        task_id = create_image_to_3d_task(api_key)

    # Poll until done
    result = poll_task(api_key, task_id)

    # Download files
    downloaded = download_model_files(result)

    print("\n=== Generation Complete ===")
    print(f"Output directory: {OUTPUT_DIR}")
    for fmt, path in downloaded.items():
        print(f"  {fmt}: {path}")

    print("\nNext steps:")
    print("  1. Import GLB into Blender to verify quality")
    print("  2. Generate preview renders")
    print("  3. Upload to R2")

    return task_id


if __name__ == "__main__":
    main()
