#!/usr/bin/env python3
"""
Regenerate Scene 01, Panel 05 (Jenny close-up) start and end frames.

Fix: Jenny has DARK BROWN curly hair in a messy ponytail, NOT blonde.
Uses Jenny's approved turnaround as reference image.
"""

import os
import sys
import time
import subprocess
from pathlib import Path

from google import genai
from google.genai import types
from PIL import Image
import io

# Configuration
MODEL = "gemini-2.5-flash-image"
DELAY_BETWEEN_REQUESTS = 12  # seconds

SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
JENNY_REF = Path("/tmp/char-refs/jenny_turnaround_APPROVED.png")
OUTPUT_DIR = PROJECT_DIR / "tmp" / "scene01-panel05-regen"
R2_DEST = "r2:rex-assets/storyboards/v2/scene-01/"
R2_PUBLIC = "https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/storyboards/v2/scene-01"

# Jenny's CORRECT description (from approved turnaround)
JENNY_DESC = (
    "Match this character EXACTLY from the reference turnaround. "
    "Dark curly hair in a messy ponytail, brown skin, coral pink hoodie, "
    "gray leggings, white sneakers. She is a teenager completely absorbed in her phone."
)

STYLE_SUFFIX = (
    "Pixar-style 3D animation, warm cozy living room lighting, "
    "cinematic quality, 16:9 widescreen aspect ratio"
)

# Panel 05 start and end frames
FRAMES = {
    "start": {
        "filename": "scene-01-panel-05-start.png",
        "prompt": (
            f"Close-up shot of a teenage babysitter girl. {JENNY_DESC} "
            "She sits in a cozy armchair, head tilted down, staring at her phone screen "
            "with a slight smirk. Phone screen casts a soft blue-white glow on her face. "
            "Warm fireplace light in the blurred background. Shallow depth of field. "
            "She is completely oblivious to the family chaos around her. "
            f"{STYLE_SUFFIX}"
        ),
    },
    "end": {
        "filename": "scene-01-panel-05-end.png",
        "prompt": (
            f"Close-up shot of a teenage babysitter girl. {JENNY_DESC} "
            "She sits in a cozy armchair, tapping her phone screen and smirking. "
            "She briefly glances up with a bored expression then looks back at her phone. "
            "Phone screen glow on her face, warm amber background lighting from fireplace. "
            "Shallow depth of field. Completely disengaged from surroundings. "
            f"{STYLE_SUFFIX}"
        ),
    },
}

TARGET_ASPECT = 16 / 9


def image_to_part(img_path):
    """Convert an image file to a genai Part."""
    img = Image.open(img_path)
    max_dim = 2048
    if max(img.size) > max_dim:
        ratio = max_dim / max(img.size)
        new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
        img = img.resize(new_size, Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return types.Part.from_bytes(data=buf.getvalue(), mime_type="image/png")


def crop_to_16_9(img_path):
    """Crop image to 16:9 aspect ratio (center crop)."""
    img = Image.open(img_path)
    w, h = img.size
    current_aspect = w / h

    if abs(current_aspect - TARGET_ASPECT) < 0.01:
        return  # Already correct

    if current_aspect > TARGET_ASPECT:
        # Too wide, crop width
        new_w = int(h * TARGET_ASPECT)
        left = (w - new_w) // 2
        img = img.crop((left, 0, left + new_w, h))
    else:
        # Too tall, crop height
        new_h = int(w / TARGET_ASPECT)
        top = (h - new_h) // 2
        img = img.crop((0, top, w, top + new_h))

    img.save(img_path)
    print(f"  Cropped to 16:9: {img.size[0]}x{img.size[1]}")


def generate_frame(frame_key, frame_info, client, jenny_ref_part):
    """Generate a single frame."""
    filename = frame_info["filename"]
    output_path = OUTPUT_DIR / filename

    print(f"\n{'='*60}")
    print(f"Generating panel 05 {frame_key} frame")
    print(f"  File: {filename}")

    ref_note = (
        "Use this character reference turnaround to draw the EXACT same character. "
        "She has dark brown/black curly hair in a messy ponytail, brown skin, "
        "coral/salmon pink zip-up hoodie, gray leggings, white sneakers. "
        "DO NOT change her hair color. DO NOT make her blonde. "
        "Generate this scene:\n\n"
    )

    content_parts = [
        jenny_ref_part,
        types.Part.from_text(text=ref_note + frame_info["prompt"]),
    ]

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=content_parts,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
            ),
        )

        if hasattr(response, "candidates") and response.candidates:
            for part in response.candidates[0].content.parts:
                if part.inline_data is not None:
                    img_bytes = part.inline_data.data
                    with open(output_path, "wb") as f:
                        f.write(img_bytes)
                    size_kb = len(img_bytes) / 1024
                    print(f"  Generated: {filename} ({size_kb:.0f} KB)")

                    # Apply 16:9 crop
                    crop_to_16_9(output_path)
                    return output_path
                elif part.text:
                    print(f"  Text response: {part.text[:200]}")

        print("  FAILED: No image data in response")
        return None

    except Exception as e:
        print(f"  ERROR: {e}")
        return None


def upload_to_r2(local_path):
    """Upload a single file to R2."""
    try:
        result = subprocess.run(
            ["rclone", "copy", str(local_path), R2_DEST],
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode == 0:
            url = f"{R2_PUBLIC}/{local_path.name}"
            print(f"  Uploaded: {url}")
            return url
        else:
            print(f"  Upload error: {result.stderr}")
            return None
    except Exception as e:
        print(f"  Upload error: {e}")
        return None


def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY not set")
        sys.exit(1)

    if not JENNY_REF.exists():
        print(f"ERROR: Jenny reference not found: {JENNY_REF}")
        sys.exit(1)

    print(f"Jenny reference: {JENNY_REF}")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    client = genai.Client(api_key=api_key)
    print(f"Model: {MODEL}")

    jenny_ref_part = image_to_part(JENNY_REF)
    print("Loaded Jenny turnaround reference")

    results = {}
    frame_keys = ["start", "end"]

    for i, key in enumerate(frame_keys):
        frame_info = FRAMES[key]
        result_path = generate_frame(key, frame_info, client, jenny_ref_part)
        results[key] = result_path

        if i < len(frame_keys) - 1:
            print(f"\n  Waiting {DELAY_BETWEEN_REQUESTS}s for rate limit...")
            time.sleep(DELAY_BETWEEN_REQUESTS)

    # Upload
    print(f"\n{'='*60}")
    print("Uploading to R2...")
    urls = {}
    for key, path in results.items():
        if path and path.exists():
            url = upload_to_r2(path)
            if url:
                urls[key] = url

    # Summary
    print(f"\n{'='*60}")
    print(f"SUMMARY: {len(urls)}/2 frames generated and uploaded")
    for key, url in urls.items():
        print(f"  {key}: {url}")

    failed = [k for k in frame_keys if k not in urls]
    if failed:
        print(f"  FAILED: {', '.join(failed)}")

    return 0 if len(urls) == 2 else 1


if __name__ == "__main__":
    sys.exit(main())
