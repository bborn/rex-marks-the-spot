#!/usr/bin/env python3
"""
Generate Leo turnaround sheet v3/v4 with CORRECT appearance.

Leo should have:
- Fair/light skin (Caucasian, like his sister Mia)
- Sandy blonde/light brown hair with slight wave (NOT dark curly hair)
- Blue eyes
- 5 years old boy
- Chubby cheeks, cheerful expression
- Outfit: Green dinosaur t-shirt, khaki cargo shorts, red sneakers

Style: Pixar 3D animation, character turnaround sheet
"""

import os
import sys
import time
from pathlib import Path

from google import genai
from google.genai import types


OUTPUT_DIR = Path(__file__).parent.parent / "output" / "leo_turnaround"

# Leo turnaround prompt - CORRECTED appearance
LEO_PROMPT_V3 = """3D animated Pixar-style character turnaround sheet.
Fictional cartoon 5-year-old Caucasian boy character for animated family movie.
Fair light skin tone, same as his older sister.
Sandy blonde light brown hair with slight wave, messy cowlick at crown.
Big bright blue eyes, wide and expressive.
Round cherubic face with chubby cheeks, gap-toothed cheerful smile.
Small button nose, light pink lips.
Cartoon stylized proportions: oversized head, short limbs.

OUTFIT: Bright green t-shirt with cartoon dinosaur print on front, khaki cargo shorts with side pockets, bright red sneakers with white soles.

Character turnaround reference sheet showing FOUR views in a horizontal row:
- FRONT view (facing camera, arms relaxed at sides)
- THREE-QUARTER view (turned 45 degrees to the right)
- SIDE profile view (facing left)
- BACK view (facing away)

SAME character in all four views. Consistent design across all poses.
Clean white background. Professional animation studio model sheet.
Adorable, energetic, mischievous expression.
Pixar/Disney animated movie style. Highly stylized, NOT realistic."""

LEO_PROMPT_V4 = """Character turnaround model sheet, Pixar 3D animation style.
Cute cartoon boy character, age 5, for animated family film.
Light Caucasian skin tone, fair complexion with rosy cheeks.
Sandy blonde wavy hair, slightly messy and tousled with cowlick sticking up.
Large bright blue sparkling eyes with catchlights.
Round baby face, chubby cheeks, adorable gap-toothed grin.
Cheerful, energetic, playful expression.

CLOTHING: Green dinosaur t-shirt (T-Rex graphic), khaki cargo shorts, red sneakers.

Professional character model sheet with FOUR VIEWS arranged horizontally:
1. FRONT VIEW - facing forward, friendly pose
2. 3/4 VIEW - turned slightly right
3. SIDE VIEW - full profile
4. BACK VIEW - facing away

Same character design in every view. Consistent proportions.
White studio background. Clean reference sheet format.
Stylized cartoon aesthetic, big head small body.
Cute and lovable kid character design."""


def generate_leo_turnaround(client, version: str, prompt: str) -> Path:
    """Generate Leo turnaround sheet."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"leo_turnaround_{version}.png"

    print(f"\n{'='*60}")
    print(f"Generating Leo turnaround {version}")
    print(f"{'='*60}")
    print(f"Output: {output_path}")

    # Use gemini-2.0-flash-exp-image-generation for child characters
    model = "gemini-2.0-flash-exp-image-generation"

    try:
        print(f"  Using model: {model}")
        print(f"  Generating image...")

        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
            ),
        )

        # Extract image from response
        if response.candidates:
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'inline_data') and part.inline_data:
                    image_data = part.inline_data.data
                    with open(output_path, 'wb') as f:
                        f.write(image_data)
                    print(f"  SUCCESS: Saved to {output_path}")
                    return output_path

        print(f"  ERROR: No image in response")
        print(f"  Response: {response}")
        return None

    except Exception as e:
        print(f"  ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Generate Leo turnaround v3 and v4."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY environment variable not set")
        sys.exit(1)

    client = genai.Client(api_key=api_key)

    print("="*60)
    print("Leo Turnaround Generator - Corrected Version")
    print("="*60)
    print("Leo should have:")
    print("  - Fair/light skin (Caucasian)")
    print("  - Sandy blonde/light brown wavy hair")
    print("  - Blue eyes")
    print("  - 5 years old, chubby cheeks")
    print("  - Green dinosaur t-shirt, khaki shorts, red sneakers")
    print("="*60)

    results = []

    # Generate v3
    result = generate_leo_turnaround(client, "v3", LEO_PROMPT_V3)
    results.append(("v3", result))

    # Wait between requests (rate limiting)
    print("\nWaiting 10 seconds before next generation...")
    time.sleep(10)

    # Generate v4
    result = generate_leo_turnaround(client, "v4", LEO_PROMPT_V4)
    results.append(("v4", result))

    # Summary
    print("\n" + "="*60)
    print("GENERATION SUMMARY")
    print("="*60)

    for version, path in results:
        status = "SUCCESS" if path else "FAILED"
        print(f"  {version}: {status}")
        if path:
            print(f"       -> {path}")

    success_count = sum(1 for _, p in results if p)
    print(f"\n{success_count}/2 images generated successfully")

    if success_count > 0:
        print("\nNext step: Upload to R2 using:")
        print("  rclone copy output/leo_turnaround/leo_turnaround_v3.png r2:rex-assets/characters/leo/")
        print("  rclone copy output/leo_turnaround/leo_turnaround_v4.png r2:rex-assets/characters/leo/")

    sys.exit(0 if success_count == 2 else 1)


if __name__ == "__main__":
    main()
