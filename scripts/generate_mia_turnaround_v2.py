#!/usr/bin/env python3
"""
Generate Mia character turnaround V2 with specific fixes.

FIXES FROM V1:
1. ONE ponytail (single ponytail, not two pigtails)
2. PINK top (not yellow)
3. Natural/asymmetric hair curls (not symmetrical)
4. DARKER brown hair

KEEP FROM V1:
- Overall Pixar style
- Jeans and red sneakers
- 4-angle turnaround layout
- 8 year old girl proportions
"""

import os
import sys
import time
from pathlib import Path

from google import genai
from google.genai import types

# Initialize client
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# Output directory
OUTPUT_DIR = Path(__file__).parent.parent / "output" / "mia_turnaround"

# Base prompt with the specific fixes applied
BASE_PROMPT = """3D animated cartoon character model sheet, stylized like Pixar animation.

Fictional cartoon girl character for animated family movie, approximately 8 years old.
Stylized proportions with large expressive eyes typical of animated films.

HAIR: Dark chocolate brown hair (rich dark brown, NOT light brown) styled in a SINGLE ponytail
(ONE ponytail on the back of the head, NOT pigtails or two ponytails). Hair has natural-looking
soft curls that fall asymmetrically with some strands loose around the face. The curls should
look organic and imperfect, not symmetrical.

FACE: Cartoon style face with soft features, big expressive warm brown eyes, light freckles
across nose and cheeks, cheerful but slightly worried expression.

OUTFIT:
- PINK t-shirt (bright bubblegum pink color) with a simple design
- Blue denim jeans (casual kid's style)
- Red sneakers with white soles

Show FOUR cartoon character views in a horizontal row on clean white background:
- FRONT view (facing camera directly, arms relaxed at sides)
- THREE-QUARTER view (turned 45 degrees to show depth)
- SIDE profile view (full profile showing ponytail)
- BACK view (showing single ponytail from behind)

Same stylized cartoon character must be IDENTICAL in all four views - consistent design.
Professional animation studio model sheet / character reference quality.
Clean white background with no other elements.
Cartoon/animated style, NOT realistic or photorealistic.
Stylized animated movie character design, warm and appealing."""


# Two variations with slight differences for director choice
VARIATIONS = [
    {
        "name": "v2a",
        "suffix": "Mia has an energetic, curious expression. Her pink shirt is a solid bright pink. " +
                 "The single ponytail is medium-length reaching mid-back, secured with a turquoise hair tie.",
    },
    {
        "name": "v2b",
        "suffix": "Mia has a warm, friendly smile. Her pink shirt has a small white star pattern. " +
                 "The single ponytail is slightly higher on her head, with a pink scrunchie.",
    },
]


def generate_turnaround(prompt: str, name: str) -> bool:
    """Generate a single turnaround sheet."""
    output_path = OUTPUT_DIR / f"mia_turnaround_{name}.png"

    print(f"\nGenerating: {name}")
    print(f"  Output: {output_path}")

    try:
        # Use Gemini 2.5 Flash Image generation (minimum per CLAUDE.md)
        response = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=f"Generate an image: {prompt}",
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
            ),
        )

        # Extract and save the image from the response
        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                image_data = part.inline_data.data
                with open(output_path, "wb") as f:
                    f.write(image_data)
                print(f"  ✓ Saved successfully")
                return True

        print(f"  ✗ No image in response")
        return False

    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def main():
    """Generate Mia turnaround variations."""
    print("=" * 60)
    print("Mia Character Turnaround V2 Generator")
    print("=" * 60)
    print("\nFixes applied:")
    print("  1. Single ponytail (not two)")
    print("  2. Pink top (not yellow)")
    print("  3. Natural asymmetric hair curls")
    print("  4. Darker brown hair")
    print("\nKept from V1:")
    print("  - Pixar style")
    print("  - Jeans and red sneakers")
    print("  - 4-angle turnaround layout")
    print("  - 8 year old proportions")
    print()

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {OUTPUT_DIR}")

    # Generate each variation
    results = []
    for i, variation in enumerate(VARIATIONS):
        full_prompt = BASE_PROMPT + "\n\n" + variation["suffix"]
        success = generate_turnaround(full_prompt, variation["name"])
        results.append((variation["name"], success))

        # Rate limiting between requests (8+ seconds as noted in CLAUDE.md)
        if i < len(VARIATIONS) - 1:
            print("\n  Waiting 10 seconds for rate limiting...")
            time.sleep(10)

    # Summary
    print("\n" + "=" * 60)
    print("GENERATION SUMMARY")
    print("=" * 60)

    for name, success in results:
        status = "✓ SUCCESS" if success else "✗ FAILED"
        print(f"  mia_turnaround_{name}.png: {status}")

    successful = sum(1 for _, s in results if s)
    print(f"\n  Total: {successful}/{len(results)} successful")

    # List generated files
    if OUTPUT_DIR.exists():
        print("\nGenerated files:")
        for f in sorted(OUTPUT_DIR.glob("*.png")):
            size_kb = f.stat().st_size / 1024
            print(f"  - {f.name} ({size_kb:.1f} KB)")

    return 0 if successful == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
