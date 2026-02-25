#!/usr/bin/env python3
"""
Batch generate Veo 3 animated clips for all Scene 1 panels (02-09).
Panel 01 was already generated separately.

Uses the "natural descriptive prompt" approach which produces the least
character drift (finding from panel 01 experiments).
"""

import os
import sys
import time
import json
import requests
from pathlib import Path
from datetime import datetime

from google import genai
from google.genai import types

PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output" / "scene01-panels"
R2_PREFIX = "animation-tests/scene01-all-panels"

# Panel-specific prompts - natural descriptive style (proven best for consistency)
PANELS = {
    "02": {
        "desc": "1B: Medium shot Leo on couch with dinosaur toys",
        "prompt": (
            "Pixar-style 3D animated medium shot. A small boy sitting cross-legged "
            "on a cozy couch, hugging a plush green dinosaur toy. He watches TV contentedly, "
            "the screen casting a soft colorful glow on his face. Plastic dinosaur toys "
            "are scattered around him on the couch cushions. Warm living room with "
            "bookshelves in the background. Camera holds steady with a very subtle push in. "
            "Gentle ambient lighting. Cinematic 3D animation quality."
        ),
        "duration": 6,
    },
    "03": {
        "desc": "1C: Tracking shot Nina walking through house",
        "prompt": (
            "Pixar-style 3D animated tracking shot. An elegant woman in a black dress "
            "walks briskly through a warmly lit home interior, putting on an earring with "
            "one hand while carrying a small purse in the other. Camera smoothly tracks "
            "alongside her as she moves from left to right. Warm amber lamplight, "
            "fireplace glow visible. She looks focused and slightly hurried but graceful. "
            "Cinematic smooth camera movement, movie-quality 3D animation."
        ),
        "duration": 8,
    },
    "04": {
        "desc": "1D: Two-shot Gabe and Nina talking",
        "prompt": (
            "Pixar-style 3D animated two-shot. A couple in formal evening wear - "
            "the man in a black tuxedo with glasses, the woman in a sleek black dress - "
            "stand together in their warmly lit living room. They talk animatedly, "
            "the man checking his watch impatiently while the woman gestures expressively. "
            "Warm table lamp light in background. Subtle character animation. "
            "Cinematic framing, movie-quality 3D animation."
        ),
        "duration": 8,
    },
    "05": {
        "desc": "1E: Close-up Jenny on phone",
        "prompt": (
            "Pixar-style 3D animated close-up shot. A teenage girl with blonde hair "
            "in a ponytail sits in an armchair, looking down at her phone with a slight "
            "smile. Phone screen casts a soft blue-white glow on her face. Warm fireplace "
            "light in the blurred background. She occasionally taps the screen and smirks. "
            "Shallow depth of field, warm cozy atmosphere. "
            "Cinematic lighting, movie-quality 3D animation."
        ),
        "duration": 6,
    },
    "06": {
        "desc": "1F: Close-up TV screen flickering",
        "prompt": (
            "Pixar-style 3D animated close-up of a television screen showing a colorful "
            "cartoon with cute round characters in a forest scene. The TV image occasionally "
            "jitters with static lines rolling through. Lightning flashes reflect on the "
            "screen surface. Brief flickers of blue-white static interrupt the cartoon. "
            "Living room furniture visible at edges of frame. "
            "Cinematic quality, atmospheric lighting."
        ),
        "duration": 4,
    },
    "07": {
        "desc": "1G: Over-the-shoulder kids watching TV",
        "prompt": (
            "Pixar-style 3D animated over-the-shoulder shot from behind a couch. "
            "Two silhouetted figures sit on the couch watching a large TV screen showing "
            "a colorful dinosaur cartoon. In the background through a doorway, two adults "
            "in formal wear are visible - the man adjusting his tie, the woman checking "
            "her purse. Warm amber living room lighting. TV glow illuminates the scene. "
            "The figures on the couch shift slightly. "
            "Cinematic framing, movie-quality 3D animation."
        ),
        "duration": 8,
    },
    "08": {
        "desc": "1H: Close-up Mia - 'Promise?'",
        "prompt": (
            "Pixar-style 3D animated close-up. A young girl with dark curly hair and "
            "big expressive brown eyes looks up with a worried, earnest expression. "
            "She wears a pink star-pattern shirt. Lightning flashes through a window "
            "behind her, briefly illuminating the scene with blue-white light. "
            "Camera slowly pushes in toward her face. Her expression is vulnerable "
            "and pleading. Emotional, cinematic lighting with warm and cool contrast. "
            "Movie-quality 3D animation, Pixar emotional close-up style."
        ),
        "duration": 8,
    },
    "09": {
        "desc": "1I: Close-up Gabe hesitates",
        "prompt": (
            "Pixar-style 3D animated close-up two-shot. A man with dark hair and "
            "rectangular glasses in a black tuxedo shows conflicted emotion on his face - "
            "slight guilt and hesitation. Beside him, a woman with auburn hair in a black "
            "dress gives him a sharp sideways glance. Warm ambient lighting from table lamps. "
            "Subtle facial animation - the man swallows nervously, the woman raises an eyebrow. "
            "Cinematic shallow depth of field, movie-quality 3D animation."
        ),
        "duration": 8,
    },
}

NEGATIVE_PROMPT = "blurry, low quality, distorted, morphing, glitchy, unnatural movement"


def generate_panel(client, panel_id, panel_info):
    """Generate a single panel's video clip."""
    image_path = OUTPUT_DIR / f"scene-01-panel-{panel_id}.png"
    if not image_path.exists():
        print(f"  ERROR: Image not found: {image_path}")
        return None

    with open(image_path, "rb") as f:
        image_bytes = f.read()

    image = types.Image(image_bytes=image_bytes, mime_type="image/png")

    config = types.GenerateVideosConfig(
        aspect_ratio="16:9",
        number_of_videos=1,
        duration_seconds=panel_info["duration"],
        negative_prompt=NEGATIVE_PROMPT,
    )

    print(f"  Generating ({panel_info['duration']}s)...")
    operation = client.models.generate_videos(
        model="veo-3.0-generate-001",
        prompt=panel_info["prompt"],
        image=image,
        config=config,
    )

    poll_count = 0
    while not operation.done:
        poll_count += 1
        print(f"    Polling #{poll_count} ({poll_count * 15}s)...")
        time.sleep(15)
        for attempt in range(3):
            try:
                operation = client.operations.get(operation)
                break
            except Exception as e:
                if attempt < 2:
                    time.sleep(5)
                else:
                    raise

    if operation.error:
        print(f"  Error: {operation.error}")
        return None

    if not operation.response or not operation.result:
        print("  No response")
        return None

    generated = operation.result.generated_videos or []
    if not generated:
        print("  No videos generated")
        return None

    video = generated[0].video
    if not video or not hasattr(video, "uri") or not video.uri:
        print("  No video URI")
        return None

    # Download
    api_key = os.environ.get("GEMINI_API_KEY")
    dl_url = f"{video.uri}&key={api_key}" if "?" in video.uri else f"{video.uri}?key={api_key}"
    resp = requests.get(dl_url, stream=True)
    if resp.status_code != 200:
        print(f"  Download failed: {resp.status_code}")
        return None

    filename = f"scene01-panel{panel_id}-veo3.mp4"
    filepath = OUTPUT_DIR / filename
    total = 0
    with open(filepath, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)
            total += len(chunk)

    size_mb = total / (1024 * 1024)
    print(f"  Saved: {filename} ({size_mb:.1f} MB)")
    return filepath


def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY not set")
        sys.exit(1)

    client = genai.Client(api_key=api_key)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    results = {}
    panel_ids = sorted(PANELS.keys())

    for i, panel_id in enumerate(panel_ids):
        panel_info = PANELS[panel_id]
        print(f"\n{'=' * 60}")
        print(f"Panel {panel_id}: {panel_info['desc']}")
        print(f"{'=' * 60}")

        try:
            filepath = generate_panel(client, panel_id, panel_info)
            if filepath:
                results[panel_id] = {
                    "filename": filepath.name,
                    "size_mb": round(filepath.stat().st_size / (1024 * 1024), 2),
                    "status": "success",
                }
            else:
                results[panel_id] = {"status": "failed"}
        except Exception as e:
            print(f"  EXCEPTION: {e}")
            results[panel_id] = {"status": "error", "error": str(e)}

        # Rate limit delay between generations (skip after last)
        if i < len(panel_ids) - 1:
            print("  Waiting 60s for rate limit...")
            time.sleep(60)

    # Summary
    success = sum(1 for r in results.values() if r.get("status") == "success")
    print(f"\n{'=' * 60}")
    print(f"COMPLETE: {success}/{len(panel_ids)} panels generated")
    print(f"{'=' * 60}")

    for pid, r in sorted(results.items()):
        status = r.get("status")
        if status == "success":
            print(f"  Panel {pid}: {r['filename']} ({r['size_mb']} MB)")
        else:
            print(f"  Panel {pid}: {status} - {r.get('error', '')}")

    # Save results
    report_path = OUTPUT_DIR / "batch_generation_report.json"
    with open(report_path, "w") as f:
        json.dump({
            "generated_at": datetime.now().isoformat(),
            "model": "veo-3.0-generate-001",
            "panels": results,
        }, f, indent=2)


if __name__ == "__main__":
    main()
