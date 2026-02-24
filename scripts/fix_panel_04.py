#!/usr/bin/env python3
"""Fix Scene 1 Panel 04 - Gabe body build wrong.

Regenerates Panel 04 with correct Gabe character design:
- Stocky, soft around middle (NOT tall/lean/angular)
- Round, friendly face (NOT chiseled jaw)
- Prominent rectangular glasses (signature feature)
- Background Leo should be visibly blonde
- 16:9 aspect ratio
- 3D Pixar render style consistent with turnarounds
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
MODEL = "gemini-2.0-flash-exp-image-generation"

SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
CHAR_REF_DIR = PROJECT_DIR / "tmp" / "char-refs"
OUTPUT_DIR = PROJECT_DIR / "tmp" / "scene01-panels"
R2_DEST = "r2:rex-assets/storyboards/act1/panels/"
R2_DEST_ALT = "r2:rex-assets/storyboards/act1/scene-01/"
R2_PUBLIC = "https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/storyboards/act1/panels"

FILENAME = "scene-01-panel-04.png"

# Very specific prompt emphasizing Gabe's correct build
PROMPT = """Generate a 3D Pixar-style animated movie storyboard panel. 16:9 widescreen cinematic aspect ratio.

SCENE: Two-shot of married parents getting ready for a formal date night, medium shot from waist up.

THE MAN (screen right):
- CRITICAL: He must be STOCKY and SOFT around the middle - a desk-job dad bod, NOT lean or athletic
- Round, friendly face with warm expression - NOT angular or chiseled
- PROMINENT rectangular glasses with dark frames - this is his most recognizable feature, make them clearly visible
- Dark brown wavy hair, slightly messy, hint of gray at temples
- Five o'clock shadow stubble
- Wearing a slightly rumpled black tuxedo with loosened dark tie
- Checking his watch impatiently, frustrated body language about running late
- His body proportions should match the reference sheet - broad shoulders but noticeably soft/round midsection

THE WOMAN (screen left):
- Elegant auburn/red-brown wavy shoulder-length hair
- Green eyes, freckles
- Wearing a black dress with small earrings
- Composed despite chaos, still getting ready
- Graceful and put-together

BACKGROUND:
- Cozy family living room, warm amber evening lighting
- Two children visible on the couch: a girl with dark curly hair (8yo) and a BLONDE boy (5yo) in green dino pajamas - the boy's BLONDE hair must be clearly visible
- A teen babysitter in an armchair absorbed in her phone

STYLE: 3D Pixar/Disney animated film, rich cinematic lighting, warm color palette, comedy staging showing the husband's impatience vs wife's composure. High quality render matching the character reference sheets provided."""


def image_to_part(img_path):
    """Convert an image file to a genai Part."""
    img = Image.open(img_path)
    max_dim = 2048
    if max(img.size) > max_dim:
        ratio = max_dim / max(img.size)
        new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
        img = img.resize(new_size, Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    data = buf.getvalue()
    return types.Part.from_bytes(data=data, mime_type='image/png')


def generate_attempt(client, model_name, ref_parts, attempt_num):
    """Make one generation attempt."""
    print(f"\n  Attempt {attempt_num} with model: {model_name}")

    ref_instruction = (
        "IMPORTANT: Use these character reference turnaround sheets to match the characters EXACTLY. "
        "The man MUST match the stocky, soft-around-the-middle body build shown in his reference sheet. "
        "Do NOT make him tall, lean, or angular. His rectangular glasses must be prominent. "
        "Match the woman's face, hair color, and proportions from her reference sheet.\n\n"
    )

    content_parts = ref_parts + [types.Part.from_text(text=ref_instruction + PROMPT)]

    try:
        response = client.models.generate_content(
            model=model_name,
            contents=content_parts,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
            ),
        )

        if hasattr(response, "candidates") and response.candidates:
            for part in response.candidates[0].content.parts:
                if part.inline_data is not None:
                    return part.inline_data.data
                elif part.text:
                    print(f"  Text: {part.text[:200]}")

        print("  No image data in response")
        return None

    except Exception as e:
        print(f"  ERROR: {e}")
        return None


def upload_to_r2(local_path):
    """Upload to both R2 paths."""
    urls = []
    for dest in [R2_DEST, R2_DEST_ALT]:
        try:
            result = subprocess.run(
                ["rclone", "copy", str(local_path), dest],
                capture_output=True, text=True, timeout=60
            )
            if result.returncode == 0:
                print(f"  Uploaded to: {dest}")
                urls.append(dest)
            else:
                print(f"  Upload error ({dest}): {result.stderr}")
        except Exception as e:
            print(f"  Upload error ({dest}): {e}")
    return urls


def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY not set")
        sys.exit(1)

    # Check character refs
    gabe_ref = CHAR_REF_DIR / "gabe_turnaround_APPROVED.png"
    nina_ref = CHAR_REF_DIR / "nina_turnaround_APPROVED.png"

    for ref_path, name in [(gabe_ref, "Gabe"), (nina_ref, "Nina")]:
        if ref_path.exists():
            print(f"  {name} ref: OK ({ref_path.stat().st_size // 1024} KB)")
        else:
            print(f"  {name} ref: MISSING - {ref_path}")
            sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / FILENAME

    # Load reference images
    print("\nLoading character references...")
    ref_parts = [
        image_to_part(gabe_ref),
        image_to_part(nina_ref),
    ]
    print("  References loaded")

    # Initialize client
    client = genai.Client(api_key=api_key)

    print(f"\n{'='*60}")
    print("Fixing Scene 1 Panel 04 - Gabe body build")
    print(f"{'='*60}")

    # Try up to 3 attempts
    best_image = None
    for attempt in range(1, 4):
        img_data = generate_attempt(client, MODEL, ref_parts, attempt)
        if img_data:
            best_image = img_data
            size_kb = len(img_data) / 1024
            print(f"  SUCCESS: Got image ({size_kb:.0f} KB)")

            # Save it
            with open(output_path, "wb") as f:
                f.write(img_data)
            print(f"  Saved to: {output_path}")
            break
        else:
            if attempt < 3:
                print(f"  Retrying in 12s...")
                time.sleep(12)

    if not best_image:
        print("\nFAILED: Could not generate image after all attempts")
        sys.exit(1)

    # Upload to R2
    print(f"\nUploading to R2...")
    upload_to_r2(output_path)

    print(f"\n{'='*60}")
    print(f"Panel 04 regenerated successfully!")
    print(f"  Local: {output_path}")
    print(f"  R2: {R2_PUBLIC}/{FILENAME}")
    print(f"{'='*60}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
