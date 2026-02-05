#!/usr/bin/env python3
"""
Gabe Character Turnaround Sheet Generator

Generates 2 variations of Gabe (dad) character turnaround sheets
using Gemini 2.5 Flash image generation.

Outputs are uploaded to R2:
  r2:rex-assets/characters/gabe/gabe_turnaround_v1.png
  r2:rex-assets/characters/gabe/gabe_turnaround_v2.png

Usage:
    python scripts/generate_gabe_turnaround.py
"""

import os
import sys
import time
import subprocess
from pathlib import Path

from google import genai
from google.genai import types

# Configuration
MODEL = "gemini-2.5-flash-image"
OUTPUT_DIR = Path(__file__).parent.parent / "output" / "characters" / "gabe"
R2_PATH = "characters/gabe"

# Two variation prompts for Gabe
VARIATIONS = [
    {
        "filename": "gabe_turnaround_v1.png",
        "prompt": """Professional character turnaround model sheet for 3D animation production.
Pixar-style 3D animated character design of a dad character named Gabe, early 40s.

BODY: Normal dad body, soft around the middle, NOT muscular. Average height, slightly doughy build from a desk job. Relaxed posture.
HAIR: Dark brown hair, slightly thinning on top with a receding hairline. Neatly combed but not fussy.
FACE: Black-framed rectangular glasses. Light stubble (5 o'clock shadow). Warm friendly expression with tired eyes. Light/fair complexion.
OUTFIT: Casual blue and green plaid button-up shirt (untucked), khaki pants, brown casual shoes, silver wristwatch on left wrist.

Show FOUR character views in a horizontal row on a clean white background:
- FRONT view (facing camera, arms relaxed at sides)
- THREE-QUARTER view (turned 45 degrees to the right)
- SIDE view (full profile facing right)
- BACK view (facing away from camera)

The SAME character must appear in ALL four views with consistent proportions, clothing, and colors.
Professional animation studio model sheet quality. Clean white background.
Pixar/Dreamworks stylized 3D animation aesthetic. Warm, approachable dad character.""",
    },
    {
        "filename": "gabe_turnaround_v2.png",
        "prompt": """Professional character turnaround reference sheet, Pixar 3D animation style.
Dad character named Gabe for animated family movie. Age early 40s.

PHYSICAL BUILD: Typical dad bod - soft around the midsection, not athletic. Average height with slightly rounded shoulders from desk work.
HAIR: Dark brown, thinning at the crown with a noticeable receding hairline. Short and practical cut.
FACE: Wears black-framed glasses (slightly rounded rectangular). Has a five o'clock shadow stubble. Kind eyes but looks a bit worn out. Fair skin with slight warmth.
CLOTHING: Solid light blue casual button-up shirt with sleeves slightly rolled up, khaki chino pants, dark brown leather casual shoes, watch on left wrist.

Four views arranged horizontally on white background:
- FRONT VIEW: Facing camera directly, relaxed stance, slight warm smile
- 3/4 VIEW: Angled 45 degrees, showing depth of the character design
- SIDE PROFILE: Full side view facing right, showing silhouette
- BACK VIEW: Turned away, showing back of shirt, hair thinning visible

Identical character across all four views. Consistent design, proportions, and color palette.
Clean white background. Professional animation character model sheet.
Stylized Pixar/Dreamworks 3D look - NOT photorealistic. Warm, lovable, slightly frumpy dad archetype.""",
    },
]


def generate_image(client, prompt: str, output_path: Path) -> bool:
    """Generate a single turnaround image using Gemini 2.5 Flash."""
    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=f"Generate an image: {prompt}",
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
            ),
        )

        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                image_data = part.inline_data.data
                with open(output_path, "wb") as f:
                    f.write(image_data)
                print(f"  Saved to {output_path}")
                return True

        print("  No image in response")
        return False

    except Exception as e:
        print(f"  Error: {e}")
        return False


def upload_to_r2(local_path: Path, r2_filename: str) -> str:
    """Upload a file to R2 and return the public URL."""
    r2_dest = f"r2:rex-assets/{R2_PATH}/"
    print(f"  Uploading {local_path.name} to {r2_dest}")

    result = subprocess.run(
        ["rclone", "copyto", str(local_path), f"r2:rex-assets/{R2_PATH}/{r2_filename}"],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(f"  Upload error: {result.stderr}")
        return ""

    url = f"https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/{R2_PATH}/{r2_filename}"
    print(f"  Uploaded: {url}")
    return url


def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY not set")
        sys.exit(1)

    client = genai.Client(api_key=api_key)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("Gabe Character Turnaround Generator")
    print("=" * 60)
    print(f"Model: {MODEL}")
    print(f"Output: {OUTPUT_DIR}")
    print(f"Variations: {len(VARIATIONS)}")
    print()

    results = []

    for i, variation in enumerate(VARIATIONS, 1):
        print(f"[{i}/{len(VARIATIONS)}] Generating {variation['filename']}...")
        output_path = OUTPUT_DIR / variation["filename"]

        success = generate_image(client, variation["prompt"], output_path)
        if success:
            url = upload_to_r2(output_path, variation["filename"])
            results.append({"file": variation["filename"], "success": True, "url": url})
        else:
            results.append({"file": variation["filename"], "success": False, "url": ""})

        # Rate limit delay between requests
        if i < len(VARIATIONS):
            print("  Waiting 10s for rate limit...")
            time.sleep(10)

    # Summary
    print()
    print("=" * 60)
    print("RESULTS")
    print("=" * 60)
    for r in results:
        status = "OK" if r["success"] else "FAILED"
        print(f"  [{status}] {r['file']}")
        if r["url"]:
            print(f"         {r['url']}")

    success_count = sum(1 for r in results if r["success"])
    print(f"\n  {success_count}/{len(VARIATIONS)} generated successfully")

    return 0 if success_count == len(VARIATIONS) else 1


if __name__ == "__main__":
    sys.exit(main())
