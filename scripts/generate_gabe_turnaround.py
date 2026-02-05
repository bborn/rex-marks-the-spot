#!/usr/bin/env python3
"""
Gabe Character Turnaround Generator

Generates versioned turnaround sheets for Gabe (dad character) in
"Fairy Dinosaur Date Night" using Gemini image generation.

Usage:
    python scripts/generate_gabe_turnaround.py [version]

    version: v1, v3 (default: v3)

Outputs to: assets/characters/turnarounds/
Upload to R2: rclone copyto <file> r2:rex-assets/characters/gabe/gabe_turnaround_<version>.png
"""

import os
import sys
from pathlib import Path
import time

from google import genai
from google.genai import types

# Configuration
OUTPUT_DIR = Path(__file__).parent.parent / "assets" / "characters" / "turnarounds"
MODEL = "gemini-2.5-flash-image"  # Gemini 2.5 Flash with image generation

# Gabe turnaround prompts by version
GABE_VERSIONS = {
    "v1": {
        "description": "Original Gabe design - plaid shirt, khaki pants, dad bod",
        "prompt": """Professional character turnaround sheet for 3D modeling reference.
Pixar/Dreamworks animation style, father character early 40s named Gabe.
Short dark brown hair, slightly receding hairline, with some texture.
Warm brown eyes behind thick rectangular dark-framed glasses.
Oval face tending toward square jaw, five o'clock shadow stubble.
Dad bod build - noticeably soft around the middle, chubby belly visible through shirt.
Wearing a casual plaid button-up shirt (blue and green plaid pattern),
khaki pants, brown casual shoes.

Show FOUR views in a horizontal row on white background:
- FRONT view (facing camera, arms at sides)
- 3/4 view (turned 45 degrees)
- SIDE view (full profile)
- BACK view (facing away)

Character must be identical in all views. Clean white background.
Professional animation studio reference quality.
Warm, approachable dad archetype. Height 6'0", dad bod build.""",
    },
    "v3": {
        "description": "V3 refinements: trimmer belly, thinner glasses, wavier hair",
        "prompt": """Professional character turnaround sheet for 3D modeling reference.
Pixar/Dreamworks animation style, father character early 40s named Gabe.

HAIR: Short dark brown hair with a slightly receding hairline. Hair has natural WAVY TEXTURE
with some body and movement to it - styled but effortless, NOT flat or nerdy. A few waves
fall across the forehead naturally. Hints of gray at the temples.

FACE: Oval face tending toward square jaw. Five o'clock shadow stubble. Warm brown eyes.
THIN-RIMMED modern rectangular glasses - sleek metal or thin acetate frames, NOT thick
chunky nerd glasses. The frames should look stylish and contemporary.

BODY: Dad bod build but SLIGHTLY TRIMMED DOWN - still soft around the middle with a gentle
belly, but not overly chubby. More of a "used to work out, enjoys good food" build than
a round potbelly. Broad shoulders, average height 6'0".

OUTFIT: Casual plaid button-up shirt (blue and green plaid pattern) with sleeves rolled to
forearms. Khaki pants with brown belt. Brown casual shoes.

EXPRESSION: Warm, approachable, slightly tired but kind. The cool dad who tries.

Show FOUR views in a horizontal row on white background:
- FRONT view (facing camera, arms relaxed at sides)
- 3/4 view (turned 45 degrees, showing depth of build)
- SIDE view (full profile, showing the moderate dad bod silhouette)
- BACK view (facing away, showing hair texture from behind)

Character must be IDENTICAL in all four views - same proportions, same outfit, same details.
Clean white background. Professional animation studio character model sheet quality.
Pixar-level stylized 3D character design. NOT photorealistic - stylized animated movie look.""",
    },
}


def generate_turnaround(client, version: str) -> bool:
    """Generate a turnaround sheet for Gabe."""
    if version not in GABE_VERSIONS:
        print(f"ERROR: Unknown version '{version}'. Available: {list(GABE_VERSIONS.keys())}")
        return False

    info = GABE_VERSIONS[version]
    print(f"\n{'='*60}")
    print(f"Generating Gabe turnaround: {version}")
    print(f"Description: {info['description']}")
    print(f"Model: {MODEL}")
    print(f"{'='*60}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"gabe_turnaround_{version}.png"

    try:
        print("  Generating image...")
        response = client.models.generate_content(
            model=MODEL,
            contents=f"Generate an image: {info['prompt']}",
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
            ),
        )

        # Extract image from response
        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                with open(output_path, "wb") as f:
                    f.write(part.inline_data.data)
                print(f"  SUCCESS: Saved to {output_path}")
                print(f"  File size: {output_path.stat().st_size / 1024:.1f} KB")
                return True

        print("  ERROR: No image data in response")
        # Print any text parts for debugging
        for part in response.candidates[0].content.parts:
            if part.text:
                print(f"  Response text: {part.text[:200]}")
        return False

    except Exception as e:
        print(f"  ERROR: {e}")
        return False


def main():
    """Main entry point."""
    # Parse version argument
    version = sys.argv[1] if len(sys.argv) > 1 else "v3"

    # Initialize client
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY environment variable not set")
        sys.exit(1)

    client = genai.Client(api_key=api_key)

    print("=" * 60)
    print("Gabe Turnaround Sheet Generator")
    print("=" * 60)
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"Version: {version}")

    success = generate_turnaround(client, version)

    if success:
        output_path = OUTPUT_DIR / f"gabe_turnaround_{version}.png"
        print(f"\nDone! Upload with:")
        print(f"  rclone copyto {output_path} r2:rex-assets/characters/gabe/gabe_turnaround_{version}.png")
    else:
        print("\nGeneration failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
