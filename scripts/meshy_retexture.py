#!/usr/bin/env python3
"""
Add PBR textures to Gabe and Nina 3D models using Meshy API retexture endpoint.
"""

import os
import sys
import json
import time
import base64
import requests
import subprocess
from pathlib import Path

API_KEY = os.environ.get("MESHY_API_KEY", "msy_q4AqQoQJGHP29nljRUMj0aHxzT95LnsVUlpj")
BASE_URL = "https://api.meshy.ai/openapi/v1"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}

WORK_DIR = Path(__file__).parent.parent / "tmp_models"
OUTPUT_DIR = Path(__file__).parent.parent / "tmp_models" / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def file_to_base64_data_uri(filepath: Path, mime_type: str) -> str:
    """Convert a file to a base64 data URI."""
    with open(filepath, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")
    return f"data:{mime_type};base64,{data}"


def submit_retexture(model_path: Path, style_image_path: Path, text_prompt: str, name: str) -> str:
    """Submit a retexture task to Meshy API."""
    print(f"\n{'='*60}")
    print(f"Submitting retexture for: {name}")
    print(f"  Model: {model_path}")
    print(f"  Style image: {style_image_path}")
    print(f"  Text prompt: {text_prompt}")
    print(f"{'='*60}")

    # Convert model to base64 data URI
    model_uri = file_to_base64_data_uri(model_path, "model/gltf-binary")
    print(f"  Model base64 size: {len(model_uri)} chars")

    # Convert style image to base64 data URI
    image_uri = file_to_base64_data_uri(style_image_path, "image/png")
    print(f"  Image base64 size: {len(image_uri)} chars")

    payload = {
        "model_url": model_uri,
        "image_style_url": image_uri,
        "text_style_prompt": text_prompt,
        "enable_original_uv": True,
        "enable_pbr": True,
        "ai_model": "meshy-5",
    }

    print(f"  Submitting to {BASE_URL}/retexture ...")
    resp = requests.post(f"{BASE_URL}/retexture", headers=HEADERS, json=payload, timeout=120)
    print(f"  Response status: {resp.status_code}")

    if resp.status_code != 200 and resp.status_code != 202:
        print(f"  ERROR: {resp.text}")
        # Try without image style, just text
        print("  Retrying with text_style_prompt only (no image)...")
        payload.pop("image_style_url")
        resp = requests.post(f"{BASE_URL}/retexture", headers=HEADERS, json=payload, timeout=120)
        print(f"  Retry response status: {resp.status_code}")
        if resp.status_code != 200 and resp.status_code != 202:
            print(f"  RETRY ERROR: {resp.text}")
            sys.exit(1)

    result = resp.json()
    task_id = result.get("result", result.get("id", ""))
    print(f"  Task ID: {task_id}")
    return task_id


def poll_task(task_id: str, name: str, max_wait: int = 600) -> dict:
    """Poll a retexture task until it completes."""
    print(f"\nPolling task {task_id} for {name}...")
    start = time.time()

    while time.time() - start < max_wait:
        resp = requests.get(f"{BASE_URL}/retexture/{task_id}", headers=HEADERS, timeout=30)
        if resp.status_code != 200:
            print(f"  Poll error: {resp.status_code} - {resp.text}")
            time.sleep(10)
            continue

        data = resp.json()
        status = data.get("status", "UNKNOWN")
        progress = data.get("progress", 0)
        print(f"  [{name}] Status: {status}, Progress: {progress}%")

        if status == "SUCCEEDED":
            print(f"  Task completed successfully!")
            return data
        elif status in ("FAILED", "CANCELED"):
            print(f"  Task {status}!")
            print(f"  Details: {json.dumps(data, indent=2)}")
            return data

        time.sleep(15)

    print(f"  Timeout after {max_wait}s!")
    return {"status": "TIMEOUT"}


def download_results(task_data: dict, name: str) -> dict:
    """Download the textured model and textures."""
    files = {}

    # Download GLB
    model_urls = task_data.get("model_urls", {})
    if model_urls.get("glb"):
        glb_path = OUTPUT_DIR / f"{name}_textured_meshy.glb"
        print(f"  Downloading GLB to {glb_path}...")
        resp = requests.get(model_urls["glb"], timeout=120)
        with open(glb_path, "wb") as f:
            f.write(resp.content)
        files["glb"] = glb_path
        print(f"  GLB saved: {glb_path.stat().st_size} bytes")

    # Download FBX
    if model_urls.get("fbx"):
        fbx_path = OUTPUT_DIR / f"{name}_textured_meshy.fbx"
        print(f"  Downloading FBX to {fbx_path}...")
        resp = requests.get(model_urls["fbx"], timeout=120)
        with open(fbx_path, "wb") as f:
            f.write(resp.content)
        files["fbx"] = fbx_path
        print(f"  FBX saved: {fbx_path.stat().st_size} bytes")

    # Download texture maps
    texture_urls = task_data.get("texture_urls", [])
    if isinstance(texture_urls, list):
        for tex in texture_urls:
            for map_type in ["base_color", "metallic", "normal", "roughness"]:
                url = tex.get(map_type, "")
                if url:
                    tex_path = OUTPUT_DIR / f"{name}_{map_type}.png"
                    print(f"  Downloading {map_type} texture...")
                    resp = requests.get(url, timeout=60)
                    with open(tex_path, "wb") as f:
                        f.write(resp.content)
                    files[map_type] = tex_path

    return files


def upload_to_r2(local_path: Path, r2_path: str):
    """Upload a file to R2."""
    print(f"  Uploading {local_path.name} to r2:rex-assets/{r2_path}")
    subprocess.run(
        ["rclone", "copy", str(local_path), f"r2:rex-assets/{r2_path}"],
        check=True,
    )


def main():
    characters = {
        "gabe": {
            "model": WORK_DIR / "gabe.glb",
            "style_image": WORK_DIR / "gabe_turnaround_APPROVED.png",
            "text_prompt": (
                "Pixar-style 3D cartoon character. Middle-aged dad with stocky build. "
                "Rectangular black-framed glasses. Short brown hair with slight gray. "
                "Light stubble on jaw. Blue and green plaid flannel shirt. "
                "Dark khaki pants. Brown leather belt. Warm skin tones. "
                "Friendly, slightly tired expression."
            ),
            "r2_path": "3d-models/characters/gabe/",
        },
        "nina": {
            "model": WORK_DIR / "nina.glb",
            "style_image": WORK_DIR / "nina_turnaround_APPROVED.png",
            "text_prompt": (
                "Pixar-style 3D cartoon character. Mom in her late 30s. "
                "Auburn reddish-brown wavy hair past shoulders. "
                "Light freckles on cheeks and nose. Green knit sweater with subtle texture. "
                "Dark fitted jeans. Small gold stud earrings. "
                "Warm olive skin tones. Kind, confident expression."
            ),
            "r2_path": "3d-models/characters/nina/",
        },
    }

    results = {}

    # Submit both tasks
    for name, config in characters.items():
        task_id = submit_retexture(
            config["model"],
            config["style_image"],
            config["text_prompt"],
            name,
        )
        results[name] = {"task_id": task_id, "config": config}

    # Poll both tasks
    for name, data in results.items():
        task_data = poll_task(data["task_id"], name)
        data["task_data"] = task_data

        if task_data.get("status") == "SUCCEEDED":
            # Download results
            files = download_results(task_data, name)
            data["files"] = files

            # Upload to R2
            for file_type, local_path in files.items():
                if file_type in ("glb", "fbx"):
                    upload_to_r2(local_path, data["config"]["r2_path"])

            # Upload texture maps
            for map_type in ["base_color", "metallic", "normal", "roughness"]:
                if map_type in files:
                    upload_to_r2(
                        files[map_type],
                        f"{data['config']['r2_path']}textures/",
                    )
        else:
            print(f"\n  WARNING: {name} task did not succeed: {task_data.get('status')}")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for name, data in results.items():
        status = data.get("task_data", {}).get("status", "UNKNOWN")
        print(f"  {name}: {status}")
        if "files" in data:
            for ftype, fpath in data["files"].items():
                print(f"    {ftype}: {fpath}")

    # Save results JSON
    results_file = OUTPUT_DIR / "retexture_results.json"
    save_data = {}
    for name, data in results.items():
        save_data[name] = {
            "task_id": data["task_id"],
            "status": data.get("task_data", {}).get("status"),
            "model_urls": data.get("task_data", {}).get("model_urls", {}),
            "texture_urls": data.get("task_data", {}).get("texture_urls", []),
        }
    with open(results_file, "w") as f:
        json.dump(save_data, f, indent=2)
    print(f"\nResults saved to {results_file}")


if __name__ == "__main__":
    main()
