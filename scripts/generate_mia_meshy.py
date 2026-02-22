#!/usr/bin/env python3
"""
Generate Mia 3D model using Meshy API (image-to-3D) with auto-rigging.

Uses Mia's approved turnaround image as input to generate a production-quality
3D model with PBR textures, quad topology, and humanoid rigging.

Usage:
    MESHY_API_KEY=your_key python scripts/generate_mia_meshy.py
    MESHY_API_KEY=your_key python scripts/generate_mia_meshy.py <task_id>          # resume generation
    MESHY_API_KEY=your_key python scripts/generate_mia_meshy.py --rig <task_id>    # rig existing model
"""

import json
import os
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

MESHY_API_BASE = "https://api.meshy.ai/openapi/v1"
MIA_TURNAROUND_URL = "https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/characters/mia/mia_turnaround_APPROVED.png"
OUTPUT_DIR = Path("output/mia_meshy")

# Mia is 8 years old, approximately 1.2m tall
MIA_HEIGHT_METERS = 1.2


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
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        print(f"API Error {e.code}: {error_body}")
        raise


def create_image_to_3d_task(api_key):
    """Submit an image-to-3D generation task for Mia."""
    payload = {
        "image_url": MIA_TURNAROUND_URL,
        "ai_model": "meshy-6",
        "topology": "quad",
        "target_polycount": 80000,
        "should_texture": True,
        "enable_pbr": True,
        "texture_prompt": (
            "8-year-old girl character with dark brown CURLY hair in a HIGH ponytail "
            "with pink fabric scrunchie. Light tan/olive skin, large brown expressive eyes. "
            "Wearing pink cotton t-shirt with white star pattern, blue denim jeans with "
            "natural wear, red canvas sneakers. Hair has natural volume and defined curls "
            "with shine. Smooth skin texture. Pixar-style 3D animation character with "
            "slight stylization. Natural lighting, no harsh shadows."
        ),
        "symmetry_mode": "auto",
    }

    print("Submitting image-to-3D task to Meshy...")
    print(f"  Image URL: {MIA_TURNAROUND_URL}")
    print(f"  AI Model: {payload['ai_model']}")
    print(f"  Topology: {payload['topology']}")
    print(f"  Target polycount: {payload['target_polycount']}")
    print(f"  PBR enabled: {payload['enable_pbr']}")

    result = meshy_request("POST", "image-to-3d", api_key, payload)
    task_id = result.get("result")
    print(f"Task created: {task_id}")
    return task_id


def poll_task(api_key, task_id, endpoint_prefix="image-to-3d", poll_interval=15, max_wait=900):
    """Poll task status until completion."""
    print(f"\nPolling task {task_id} (max {max_wait}s)...")
    elapsed = 0

    while elapsed < max_wait:
        result = meshy_request("GET", f"{endpoint_prefix}/{task_id}", api_key)
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


def download_model_files(task_result, prefix="mia_meshy"):
    """Download all model files and textures."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    model_urls = task_result.get("model_urls", {})
    texture_urls = task_result.get("texture_urls", [])

    downloaded = {}

    # Download model files
    print("\nDownloading model files...")
    for fmt, url in model_urls.items():
        if url and fmt in ("glb", "fbx"):
            dest = OUTPUT_DIR / f"{prefix}.{fmt}"
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
                        dest = tex_dir / f"mia_{tex_type}.{ext}"
                        download_file(tex_url, dest)
            elif isinstance(tex, str):
                name = tex.rsplit("/", 1)[-1].split("?")[0]
                download_file(tex, tex_dir / name)

    # Save task result for reference
    result_path = OUTPUT_DIR / f"{prefix}_task_result.json"
    with open(result_path, "w") as f:
        json.dump(task_result, f, indent=2)
    print(f"\nTask result saved to {result_path}")

    return downloaded


def create_rigging_task(api_key, model_task_id):
    """Submit a rigging task for the generated model."""
    payload = {
        "input_task_id": model_task_id,
        "height_meters": MIA_HEIGHT_METERS,
    }

    print(f"\nSubmitting rigging task...")
    print(f"  Input task: {model_task_id}")
    print(f"  Height: {MIA_HEIGHT_METERS}m")

    result = meshy_request("POST", "rigging", api_key, payload)
    rig_task_id = result.get("result")
    print(f"Rigging task created: {rig_task_id}")
    return rig_task_id


def download_rigged_model(task_result):
    """Download rigged model files."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    downloaded = {}
    result = task_result.get("result", task_result)

    # Download rigged character files
    for key in ("rigged_character_glb_url", "rigged_character_fbx_url"):
        url = result.get(key)
        if url:
            fmt = "glb" if "glb" in key else "fbx"
            dest = OUTPUT_DIR / f"mia_rigged.{fmt}"
            download_file(url, dest)
            downloaded[f"rigged_{fmt}"] = dest

    # Download basic animations if available
    anim_dir = OUTPUT_DIR / "animations"
    anims = result.get("basic_animations", {})
    for key, url in anims.items():
        if url and isinstance(url, str) and not key.endswith("_armature_glb_url"):
            anim_dir.mkdir(exist_ok=True)
            ext = "glb" if "glb" in key else "fbx"
            name = key.replace("_url", "").replace("_glb", "").replace("_fbx", "")
            dest = anim_dir / f"mia_{name}.{ext}"
            download_file(url, dest)
            downloaded[name] = dest

    # Save rigging result
    result_path = OUTPUT_DIR / "rigging_task_result.json"
    with open(result_path, "w") as f:
        json.dump(task_result, f, indent=2)
    print(f"\nRigging result saved to {result_path}")

    return downloaded


def upload_to_r2():
    """Upload all generated files to R2."""
    import subprocess

    print("\n=== Uploading to R2 ===")
    r2_base = "r2:rex-assets/3d-models/characters/mia"

    # Upload model files
    for f in OUTPUT_DIR.glob("mia_*.glb"):
        dest = f"{r2_base}/{f.name}"
        print(f"  Uploading {f.name}...")
        subprocess.run(["rclone", "copyto", str(f), dest], check=True)

    for f in OUTPUT_DIR.glob("mia_*.fbx"):
        dest = f"{r2_base}/{f.name}"
        print(f"  Uploading {f.name}...")
        subprocess.run(["rclone", "copyto", str(f), dest], check=True)

    # Upload textures
    tex_dir = OUTPUT_DIR / "textures"
    if tex_dir.exists():
        print("  Uploading textures...")
        subprocess.run(
            ["rclone", "copy", str(tex_dir), f"{r2_base}/textures/"],
            check=True,
        )

    # Upload animations
    anim_dir = OUTPUT_DIR / "animations"
    if anim_dir.exists():
        print("  Uploading animations...")
        subprocess.run(
            ["rclone", "copy", str(anim_dir), f"{r2_base}/animations/"],
            check=True,
        )

    r2_public = "https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/3d-models/characters/mia"
    print(f"\nR2 public URL base: {r2_public}")
    return r2_public


def main():
    api_key = get_api_key()

    # Parse arguments
    rig_mode = False
    resume_task_id = None

    args = sys.argv[1:]
    if args and args[0] == "--rig":
        rig_mode = True
        if len(args) > 1:
            resume_task_id = args[1].strip()
        else:
            print("ERROR: --rig requires a model task ID")
            sys.exit(1)
    elif args and args[0].strip():
        resume_task_id = args[0].strip()

    # Step 1: Generate 3D model
    if rig_mode:
        model_task_id = resume_task_id
        print(f"Skipping generation, using existing model task: {model_task_id}")
    elif resume_task_id:
        model_task_id = resume_task_id
        print(f"Resuming generation task: {model_task_id}")
        result = poll_task(api_key, model_task_id)
        downloaded = download_model_files(result)
        print("\n=== Generation Complete ===")
        for fmt, path in downloaded.items():
            print(f"  {fmt}: {path}")
    else:
        model_task_id = create_image_to_3d_task(api_key)
        result = poll_task(api_key, model_task_id)
        downloaded = download_model_files(result)
        print("\n=== Generation Complete ===")
        for fmt, path in downloaded.items():
            print(f"  {fmt}: {path}")

    # Step 2: Auto-rig the model
    print("\n" + "=" * 50)
    print("Starting auto-rigging...")
    print("=" * 50)

    rig_task_id = create_rigging_task(api_key, model_task_id)
    rig_result = poll_task(api_key, rig_task_id, endpoint_prefix="rigging")
    rigged = download_rigged_model(rig_result)

    print("\n=== Rigging Complete ===")
    for name, path in rigged.items():
        print(f"  {name}: {path}")

    # Step 3: Upload to R2
    r2_url = upload_to_r2()

    print("\n" + "=" * 50)
    print("=== ALL DONE ===")
    print("=" * 50)
    print(f"Model task ID: {model_task_id}")
    print(f"Rig task ID: {rig_task_id}")
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"R2 URL: {r2_url}")
    print("\nNext steps:")
    print("  1. Import mia_rigged.glb into Blender to verify quality")
    print("  2. Check hair (curly ponytail), textures, and rig")
    print("  3. Render preview images")

    return model_task_id, rig_task_id


if __name__ == "__main__":
    main()
