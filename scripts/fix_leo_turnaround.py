#!/usr/bin/env python3
"""
Fix Leo Turnaround - Correct skin tone to match sibling Mia.

Leo was incorrectly generated with dark skin but should match his sister Mia
who has a light brown/tan skin tone (Latina appearance).

Generates 2 variations with corrected skin tone.
"""

import os
import sys
from pathlib import Path
import time
import base64

from google import genai
from google.genai import types

# Configuration
OUTPUT_DIR = Path(__file__).parent.parent / "assets" / "characters" / "leo"
# Use Gemini image generation model
MODEL = "gemini-2.0-flash-exp-image-generation"

# Corrected Leo prompt with skin tone matching Mia
LEO_PROMPT = """3D animated cartoon character model sheet, stylized like Pixar animation.

CHARACTER: Leo, 5-year-old boy for animated family movie.
IMPORTANT - SKIN TONE: Light brown/tan skin tone (Latina/mixed heritage), matching his 8-year-old sister Mia. NOT dark skinned.

PHYSICAL FEATURES:
- Light brown/tan skin (same as his sister Mia)
- Dark brown curly messy hair (similar texture to Mia's hair)
- Large expressive brown eyes
- Round cherubic face with soft features
- Small nose, full cheeks
- Big cheerful smile

OUTFIT (MUST INCLUDE ALL):
- Green t-shirt with dinosaur graphic on front
- Khaki/tan cargo shorts
- Red sneakers with white soles

PROPORTIONS:
- 5-year-old child proportions
- Oversized head (Pixar-style cute)
- Stubby limbs
- Approximately 3.5 heads tall

STYLE:
- Pixar/Disney 3D animation style
- Stylized, NOT realistic
- Clean professional character design

TURNAROUND LAYOUT - Show FOUR views in a row on pure white background:
1. FRONT view (facing camera directly)
2. THREE-QUARTER view (turned 45 degrees)
3. SIDE view (full profile)
4. BACK view (facing away)

Same character in all four views. Professional animation model sheet reference.
Clean white background throughout."""


def generate_leo_variation(client, variation_num: int) -> bool:
    """Generate a single Leo turnaround variation."""
    print(f"\n{'='*60}")
    print(f"Generating Leo turnaround variation {variation_num}")
    print(f"{'='*60}")

    output_path = OUTPUT_DIR / f"leo_turnaround_v{variation_num}_fixed.png"

    try:
        print(f"  Using model: {MODEL}")
        print(f"  Generating image...")

        response = client.models.generate_content(
            model=MODEL,
            contents=f"Generate an image: {LEO_PROMPT}",
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
            ),
        )

        # Extract image from response
        for part in response.candidates[0].content.parts:
            if hasattr(part, 'inline_data') and part.inline_data:
                # Save the image
                OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

                image_data = part.inline_data.data
                with open(output_path, 'wb') as f:
                    f.write(image_data)
                print(f"  SUCCESS: Saved to {output_path}")
                return True

        print(f"  ERROR: No image in response")
        return False

    except Exception as e:
        print(f"  ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main entry point."""
    # Initialize client
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY environment variable not set")
        sys.exit(1)

    client = genai.Client(api_key=api_key)

    print("="*60)
    print("Leo Turnaround Fix - Correct Skin Tone")
    print("="*60)
    print(f"Output directory: {OUTPUT_DIR}")
    print("Generating 2 variations with light brown skin tone (matching Mia)")

    # Generate 2 variations
    results = []
    for i in range(1, 3):
        success = generate_leo_variation(client, i)
        results.append(success)

        # Rate limiting - wait 10 seconds between requests (Gemini requirement)
        if i < 2:
            print("\n  Waiting 10 seconds (rate limit)...")
            time.sleep(10)

    # Print summary
    print("\n" + "="*60)
    print("GENERATION SUMMARY")
    print("="*60)

    success_count = sum(results)
    print(f"  Generated: {success_count}/2 variations")

    if OUTPUT_DIR.exists():
        print("\nGenerated files:")
        for f in sorted(OUTPUT_DIR.glob("*_fixed.png")):
            print(f"  - {f.name}")

    sys.exit(0 if success_count > 0 else 1)


if __name__ == "__main__":
    main()
