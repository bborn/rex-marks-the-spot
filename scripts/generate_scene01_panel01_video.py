#!/usr/bin/env python3
"""
Generate animated video clip from Scene 1, Panel 01 storyboard using Google Veo.

This script uses image-to-video generation to animate the establishing shot
of the cozy living room scene with subtle motion and atmospheric effects.

Usage:
    python3 scripts/generate_scene01_panel01_video.py

Requirements:
    - GEMINI_API_KEY environment variable set
    - google-genai Python package installed
    - rclone configured for R2 uploads

Notes:
    - Veo has content safety filters that may block prompts mentioning children.
      The prompts focus on the environment/atmosphere and let the image provide
      the character context.
    - Veo 2 supports enhance_prompt; Veo 3/3.1 do not.
    - Veo 3 duration must be 4-8 seconds.
    - Rate limits: ~1 generation per minute on the free tier.
    - Videos are returned as download URIs, not inline bytes.
"""

import os
import sys
import time
import json
import requests
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from google import genai
from google.genai import types

OUTPUT_DIR = PROJECT_ROOT / "output" / "scene01-panel01-mvp"
PANEL_IMAGE = OUTPUT_DIR / "scene-01-panel-01.png"
PANEL_URL = "https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/storyboards/act1/panels/scene-01-panel-01.png"
R2_PREFIX = "animation-tests/scene01-panel01-mvp"

# Prompts avoid mentioning children/people explicitly to avoid content safety blocks.
# The input image provides the character context.
PROMPTS = {
    "atmospheric": (
        "Pixar-style 3D animated establishing shot of a cozy living room on a stormy evening. "
        "Camera slowly pushes in. Warm lamplight flickers softly, casting golden shadows. "
        "Rain streams down the window glass while lightning flashes outside. "
        "TV screen casts shifting blue glow across the room. "
        "Toy dinosaurs on the hardwood floor. Rich warm color palette. "
        "Cinematic lighting, high quality 3D animation, movie scene."
    ),
    "cinematic": (
        "A beautifully lit 3D animated Pixar-quality interior scene. "
        "Camera performs a very slow, smooth push-in through a cozy family living room. "
        "Warm golden light from table lamps creates a gentle glow. "
        "Outside the large window, a dramatic thunderstorm rages with streaking rain "
        "and occasional lightning flashes illuminating the dark sky. "
        "The TV flickers with soft blue light. Plastic dinosaur toys on the floor. "
        "Warm amber interior contrasts with cool blue storm outside. "
        "Subtle light animation. High-end cinematic 3D animation, shallow depth of field."
    ),
    "storm_focus": (
        "Pixar-quality 3D animated establishing shot. A cozy family living room at night. "
        "Camera slowly pushes in. Warm golden lamplight flickers across the room. "
        "Through the large window, a dramatic thunderstorm - rain streams down glass, "
        "lightning cracks across the sky. TV casts shifting blue glow. "
        "Toy dinosaurs on the hardwood floor. Rich warm amber tones contrasting with "
        "cool blue storm light outside. Subtle atmospheric animation. "
        "High-end cinematic 3D animation quality."
    ),
}

NEGATIVE_PROMPT = "blurry, low quality, distorted, morphing, glitchy, unnatural movement, shaky camera"


def download_video(uri: str, filepath: Path) -> bool:
    """Download a video from a Gemini API URI."""
    api_key = os.environ.get("GEMINI_API_KEY")
    dl_url = f"{uri}&key={api_key}" if "?" in uri else f"{uri}?key={api_key}"
    resp = requests.get(dl_url, stream=True)
    if resp.status_code == 200:
        total = 0
        with open(filepath, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
                total += len(chunk)
        size_mb = total / (1024 * 1024)
        print(f"  Saved: {filepath.name} ({size_mb:.1f} MB)")
        return True
    else:
        print(f"  Download failed: {resp.status_code}")
        return False


def generate_video(model_name: str, prompt: str, duration: int = 5,
                   output_prefix: str = "scene01-panel01"):
    """Generate video from the panel image using specified Veo model."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY not set")
        sys.exit(1)

    client = genai.Client(api_key=api_key)

    with open(PANEL_IMAGE, "rb") as f:
        image_bytes = f.read()

    image = types.Image(image_bytes=image_bytes, mime_type="image/png")

    config_kwargs = {
        "aspect_ratio": "16:9",
        "number_of_videos": 1,
        "duration_seconds": duration,
        "negative_prompt": NEGATIVE_PROMPT,
    }

    # Veo 2 supports enhance_prompt; Veo 3+ does not
    if "veo-2" in model_name:
        config_kwargs["enhance_prompt"] = True

    config = types.GenerateVideosConfig(**config_kwargs)

    print(f"\nGenerating with {model_name} ({duration}s)...")
    print(f"  Prompt: {prompt[:100]}...")
    print(f"  Started: {datetime.now().strftime('%H:%M:%S')}")

    operation = client.models.generate_videos(
        model=model_name,
        prompt=prompt,
        image=image,
        config=config,
    )

    poll_count = 0
    while not operation.done:
        poll_count += 1
        print(f"  Polling #{poll_count} ({poll_count * 15}s)...")
        time.sleep(15)
        operation = client.operations.get(operation)

    print(f"  Completed: {datetime.now().strftime('%H:%M:%S')}")

    if operation.error:
        print(f"  Error: {operation.error}")
        return []

    if not operation.response or not operation.result:
        print("  No response received")
        return []

    saved_files = []
    generated_videos = operation.result.generated_videos or []
    print(f"  Generated {len(generated_videos)} video(s)")

    for i, gv in enumerate(generated_videos):
        video = gv.video
        if not video:
            continue

        model_short = model_name.replace("veo-", "veo").replace(".0-generate-001", "").replace(".1-generate-preview", "1")
        filename = f"{output_prefix}-{model_short}-v{i + 1}.mp4"
        filepath = OUTPUT_DIR / filename

        if hasattr(video, "uri") and video.uri:
            if download_video(video.uri, filepath):
                saved_files.append(filepath)
        elif hasattr(video, "video_bytes") and video.video_bytes:
            with open(filepath, "wb") as f:
                f.write(video.video_bytes)
            size_mb = len(video.video_bytes) / (1024 * 1024)
            print(f"  Saved: {filename} ({size_mb:.1f} MB)")
            saved_files.append(filepath)

    return saved_files


def upload_to_r2(files: list):
    """Upload generated files to R2."""
    from r2_upload import upload_file

    uploaded = []
    for filepath in files:
        r2_path = f"{R2_PREFIX}/{filepath.name}"
        try:
            url = upload_file(str(filepath), r2_path)
            uploaded.append((filepath.name, url))
        except Exception as e:
            print(f"  Upload failed for {filepath.name}: {e}")
    return uploaded


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if not PANEL_IMAGE.exists():
        print("Downloading panel image from R2...")
        import subprocess
        subprocess.run(["curl", "-sL", "-o", str(PANEL_IMAGE), PANEL_URL], check=True)

    all_files = []

    # Generation plan: multiple models and prompts with rate limit delays
    generations = [
        ("veo-2.0-generate-001", PROMPTS["atmospheric"], 5, "Veo 2 atmospheric (5s)"),
        ("veo-2.0-generate-001", PROMPTS["cinematic"], 8, "Veo 2 cinematic (8s)"),
        ("veo-3.0-generate-001", PROMPTS["atmospheric"], 8, "Veo 3 atmospheric (8s, with audio)"),
        ("veo-3.1-generate-preview", PROMPTS["storm_focus"], 8, "Veo 3.1 storm focus (8s, with audio)"),
    ]

    for model, prompt, duration, desc in generations:
        print(f"\n{'=' * 60}")
        print(f"Generation: {desc}")
        print(f"{'=' * 60}")
        try:
            files = generate_video(model, prompt, duration=duration)
            all_files.extend(files)
        except Exception as e:
            print(f"  FAILED: {e}")

        # Rate limit: wait between generations
        if model != generations[-1][0]:
            print("  Waiting 60s for rate limit...")
            time.sleep(60)

    if not all_files:
        print("\nNo videos were generated successfully.")
        return

    print(f"\n{'=' * 60}")
    print("Uploading to R2...")
    print(f"{'=' * 60}")

    all_files_with_source = [PANEL_IMAGE] + all_files
    uploaded = upload_to_r2(all_files_with_source)

    report = {
        "task": "Scene 1 Panel 01 MVP Animation",
        "generated_at": datetime.now().isoformat(),
        "panel_source": PANEL_URL,
        "prompts": PROMPTS,
        "negative_prompt": NEGATIVE_PROMPT,
        "generations": [
            {"filename": f.name, "size_mb": round(f.stat().st_size / (1024 * 1024), 2)}
            for f in all_files
        ],
        "uploads": [{"name": n, "url": u} for n, u in uploaded],
    }

    report_path = OUTPUT_DIR / "generation_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\n{'=' * 60}")
    print("SUMMARY")
    print(f"{'=' * 60}")
    print(f"Generated {len(all_files)} video(s)")
    for name, url in uploaded:
        print(f"  {name}: {url}")


if __name__ == "__main__":
    main()
