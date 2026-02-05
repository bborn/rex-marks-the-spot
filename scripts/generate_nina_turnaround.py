#!/usr/bin/env python3
"""
Generate Nina (mom) character turnaround sheets - casual/everyday look.

Nina specs (from task):
- Age: Late 30s
- Body: Normal mom body (warm, approachable, NOT glamorous)
- Hair: Brown, shoulder-length, natural waves
- Face: Warm kind eyes, gentle features
- Skin: Medium/tan complexion
- Outfit: Casual comfortable (blouse or sweater, jeans, comfortable shoes)
- Wedding ring

Two variations:
- V1: Warm blouse + jeans
- V2: Cozy sweater + casual pants
"""

import os
import sys
import time
from pathlib import Path
from google import genai
from google.genai import types

OUTPUT_DIR = Path("/tmp/nina_turnaround_output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

MODEL = "gemini-2.5-flash-image"

PROMPTS = {
    "v1": """CHARACTER TURNAROUND SHEET with EXACTLY 4 views of the SAME character arranged in a HORIZONTAL ROW on a clean white background.

The character is Nina, a warm and relatable mom in her late 30s, for a Pixar-style 3D animated family movie.

CHARACTER DESIGN (must be IDENTICAL in all 4 views):
- NORMAL MOM BODY: Average build, soft and approachable figure, NOT a model or gym body. She looks like a real warm mom.
- SHOULDER-LENGTH BROWN HAIR with natural loose waves, parted slightly to one side
- WARM KIND EYES, hazel-brown, with gentle expression and slight laugh lines
- Heart-shaped face with soft features, warm genuine smile
- MEDIUM/TAN SKIN COMPLEXION (olive-warm tone, not pale)
- Age appears late 30s - mature but youthful energy
- Average height for a woman (5'6")

OUTFIT (casual everyday):
- Soft TEAL/SAGE GREEN BLOUSE, slightly loose and comfortable fit, rolled-up sleeves
- MEDIUM BLUE JEANS, relaxed fit (not skinny, not baggy)
- TAN/BROWN LEATHER FLATS (comfortable, simple)
- GOLD WEDDING RING on left hand (subtle but visible)
- Small simple stud earrings

LAYOUT - 4 VIEWS IN A ROW, LEFT TO RIGHT:
VIEW 1 (leftmost): FRONT view - facing directly at camera, relaxed natural stance, arms at sides
VIEW 2: THREE-QUARTER view - body rotated 45 degrees to the right, warm smile
VIEW 3: SIDE PROFILE view - full side profile facing right
VIEW 4 (rightmost): BACK view - facing away from camera, hair waves visible

Professional animation model sheet format. 3D Pixar/Dreamworks cartoon style, NOT realistic.
All 4 views must show the EXACT SAME character. Clean white background.
She radiates warmth, patience, and quiet inner strength - a relatable working mom.""",

    "v2": """CHARACTER TURNAROUND SHEET with EXACTLY 4 views of the SAME character arranged in a HORIZONTAL ROW on a clean white background.

The character is Nina, a warm and relatable mom in her late 30s, for a Pixar-style 3D animated family movie.

CHARACTER DESIGN (must be IDENTICAL in all 4 views):
- NORMAL APPROACHABLE MOM BODY: Soft average build, NOT athletic or glamorous. She looks like a real everyday mom.
- BROWN SHOULDER-LENGTH HAIR with gentle natural waves, soft and touchable
- WARM HAZEL EYES with kindness and a hint of tiredness (busy mom energy)
- Round-ish face with soft cheekbones, gentle smile with slight dimples
- WARM TAN/OLIVE SKIN TONE (medium complexion)
- Late 30s - relatable, warm, approachable
- Average height (5'6")

OUTFIT (cozy casual):
- Soft BURGUNDY/WINE-COLORED KNIT SWEATER, slightly oversized and cozy
- DARK WASH JEANS, straight fit, comfortable
- WHITE LOW-TOP SNEAKERS (simple, clean)
- GOLD WEDDING RING on left hand
- Delicate thin gold necklace

LAYOUT - 4 VIEWS IN A ROW, LEFT TO RIGHT:
VIEW 1 (leftmost): FRONT view - facing camera, hands relaxed at sides, warm inviting expression
VIEW 2: THREE-QUARTER view - turned 45 degrees, showing depth of character
VIEW 3: SIDE PROFILE view - full side profile facing right, showing hair wave detail
VIEW 4 (rightmost): BACK view - facing away, hair and outfit details from behind

Professional animation model sheet format. 3D Pixar/Dreamworks cartoon style, NOT realistic.
All 4 views must show the EXACT SAME character. Clean white background.
She conveys patience, warmth, and fierce protective love - a mom you'd want to be friends with."""
}


def generate_image(client, prompt: str, version: str, retry_count: int = 3) -> str | None:
    """Generate a single turnaround image using Gemini."""
    print(f"\n{'='*60}")
    print(f"Generating Nina turnaround {version}")
    print(f"{'='*60}")

    output_path = OUTPUT_DIR / f"nina_turnaround_{version}.png"

    for attempt in range(retry_count):
        try:
            print(f"  Using model: {MODEL}")
            print(f"  Attempt {attempt + 1}/{retry_count}...")

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
                    print(f"  SUCCESS: Saved to {output_path}")
                    return str(output_path)

            print(f"  WARNING: No image in response")
            if attempt < retry_count - 1:
                print(f"  Waiting 10 seconds before retry...")
                time.sleep(10)

        except Exception as e:
            print(f"  ERROR (attempt {attempt + 1}/{retry_count}): {e}")
            if attempt < retry_count - 1:
                print(f"  Waiting 10 seconds before retry...")
                time.sleep(10)

    return None


def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY environment variable not set")
        sys.exit(1)

    client = genai.Client(api_key=api_key)

    print("=" * 60)
    print("Nina Character Turnaround Generator (Casual Look)")
    print("=" * 60)
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"Model: {MODEL}")

    results = {}

    # Generate V1
    results["v1"] = generate_image(client, PROMPTS["v1"], "v1")

    # Rate limiting
    print("\nWaiting 10 seconds before next generation...")
    time.sleep(10)

    # Generate V2
    results["v2"] = generate_image(client, PROMPTS["v2"], "v2")

    # Summary
    print("\n" + "=" * 60)
    print("GENERATION SUMMARY")
    print("=" * 60)

    for version, path in results.items():
        status = "SUCCESS" if path else "FAILED"
        print(f"  {version}: {status}")
        if path:
            print(f"         Path: {path}")

    return [p for p in results.values() if p]


if __name__ == "__main__":
    generated = main()
    if generated:
        print(f"\nGenerated {len(generated)} images successfully")
        sys.exit(0)
    else:
        print("\nNo images generated")
        sys.exit(1)
