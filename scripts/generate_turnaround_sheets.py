#!/usr/bin/env python3
"""
Character Turnaround Sheet Generator

Generates character turnaround reference sheets for "Fairy Dinosaur Date Night"
using Google's Gemini/Imagen APIs.

IMPORTANT: Due to content filters, different models work for different characters:
- Adult characters (Gabe, Nina, Ruben) and creatures (Jetplane): Use Imagen 4
- Child characters (Mia, Leo): Use Gemini 2.0 Flash Image Generation

Usage:
    python scripts/generate_turnaround_sheets.py

Outputs turnaround sheets to: assets/characters/turnarounds/
"""

import os
import sys
from pathlib import Path
import time
import base64

from google import genai
from google.genai import types

# Configuration
OUTPUT_DIR = Path(__file__).parent.parent / "assets" / "characters" / "turnarounds"
MODEL = "imagen-4.0-generate-001"  # Use Imagen 4 for best quality


# Character turnaround prompts
TURNAROUND_PROMPTS = {
    "mia": {
        "name": "Mia Bornsztein",
        "role": "8-year-old girl protagonist",
        "prompt": """3D animated cartoon character model sheet, stylized like Pixar animation.
Fictional cartoon girl character for animated family movie, approx age 8.
Stylized proportions with large expressive eyes typical of animated films.
Warm brown cartoon hair in ponytail with turquoise hair tie.
Cartoon style face with soft features, big expressive eyes.
Cartoon outfit: purple star t-shirt, denim shorts, pink sneakers.

Show FOUR cartoon character views in a row on white background:
- FRONT view facing camera
- THREE-QUARTER view turned
- SIDE profile view
- BACK view

Same stylized cartoon character in all views. Professional animation model sheet.
Clean white background. Cartoon/animated style, NOT realistic.
Stylized animated movie character design.""",
    },

    "leo": {
        "name": "Leo Bornsztein",
        "role": "5-year-old boy protagonist",
        "prompt": """3D animated cartoon character model sheet, stylized like Pixar animation.
Fictional cartoon boy character for animated family movie, young kid approx age 5.
Highly stylized proportions with oversized head and very large cartoon eyes.
Messy cartoon brown hair with cowlick sticking up.
Round cartoon face with freckles and big smile.
Cartoon outfit: green dinosaur t-shirt, khaki shorts, blue velcro sneakers.

Show FOUR cartoon character views in a row on white background:
- FRONT view facing camera
- THREE-QUARTER view turned
- SIDE profile view
- BACK view

Same stylized cartoon character in all views. Professional animation model sheet.
Clean white background. Cartoon/animated style, NOT realistic.
Cute stylized animated movie character design, exaggerated proportions.""",
    },

    "gabe": {
        "name": "Gabe Bornsztein",
        "role": "Father, late 30s",
        "prompt": """Professional character turnaround sheet for 3D modeling reference.
Pixar/Dreamworks animation style, father character age 38 named Gabe.
Short dark brown hair with hints of gray at temples.
Warm brown eyes behind rectangular dark-framed glasses.
Oval face tending toward square jaw, five o'clock shadow stubble.
Wearing white dress shirt with sleeves rolled up, loosened dark blue tie,
charcoal dress pants, brown dress shoes.

Show FOUR views in a horizontal row on white background:
- FRONT view (facing camera, arms at sides)
- 3/4 view (turned 45 degrees)
- SIDE view (full profile)
- BACK view (facing away)

Character must be identical in all views. Clean white background.
Professional animation studio reference quality.
Workaholic dad archetype, slightly stressed but warm expression.
Height 6'0", average build slightly soft from desk job.""",
    },

    "nina": {
        "name": "Nina Bornsztein",
        "role": "Mother, late 30s",
        "prompt": """Professional character turnaround sheet for 3D modeling reference.
Pixar/Dreamworks animation style, mother character age 37 named Nina.
Shoulder-length dark brown hair with elegant soft waves.
Beautiful hazel-green eyes with warm expression.
Heart-shaped face with defined cheekbones, refined features.
Wearing elegant burgundy wine-colored knee-length cocktail dress,
strappy gold heels, simple gold earrings and thin bracelet.

Show FOUR views in a horizontal row on white background:
- FRONT view (facing camera, arms at sides)
- 3/4 view (turned 45 degrees)
- SIDE view (full profile)
- BACK view (facing away)

Character must be identical in all views. Clean white background.
Professional animation studio reference quality.
Graceful, elegant presence, patient but strong.
Height 5'7", fit elegant proportions.""",
    },

    "ruben": {
        "name": "Ruben Romanovsky",
        "role": "Fairy Godfather",
        "prompt": """Professional character turnaround sheet for 3D modeling reference.
Pixar/Dreamworks animation style, depressed fairy godfather named Ruben.
Appears 50s, wild unkempt silvery gray hair going everywhere.
Tired blue-gray eyes with heavy dark bags underneath.
Long drawn face that was once handsome, prominent nose, perpetual stubble.
Translucent iridescent blue-purple fairy wings, currently drooping sadly.
Wearing faded purple moth-eaten vest over wrinkled cream shirt,
worn baggy trousers, scuffed pointed curled fairy shoes.
Holding dented magic wand with tape-wrapped handle.

Show FOUR views in a horizontal row on white background:
- FRONT view (facing camera, arms at sides, wings visible)
- 3/4 view (turned 45 degrees, wing detail visible)
- SIDE view (full profile, wing silhouette)
- BACK view (facing away, wings prominently displayed)

Character must be identical in all views. Clean white background.
Professional animation studio reference quality.
Washed-up, world-weary but with hidden nobility.
Height 5'9" but hunched posture, lanky build.""",
    },

    "jetplane": {
        "name": "Jetplane",
        "role": "Dinosaur Companion",
        "prompt": """Professional character turnaround sheet for 3D modeling reference.
Pixar/Dreamworks animation style, adorable dinosaur creature named Jetplane.
Described as chicken-puppy-lizard hybrid. Round huggable body shape.
Soft teal-green scales, cream-colored belly, warm orange fluffy neck ruff.
HUGE amber puppy-like eyes with multiple catchlights for expressiveness.
Soft coral-pink floppy ear-frills that express emotion.
Small cute T-Rex style arms, stubby legs with pink toe beans visible.
Expressive tail with orange fluffy tuft at end.

Show FOUR views in a horizontal row on white background:
- FRONT view (facing camera, showing round body and big eyes)
- 3/4 view (turned 45 degrees, best merchandising angle)
- SIDE view (full profile, dinosaur silhouette)
- BACK view (facing away, tail and back details)

Character must be identical in all views. Clean white background.
Professional animation studio reference quality.
Must be absolutely adorable, toyetic, merchandise-ready.
Small form: cat-sized, approximately 18 inches long, 12 inches tall.""",
    },
}


def generate_turnaround(client, character_id: str, character_info: dict) -> bool:
    """Generate a turnaround sheet for a single character."""
    print(f"\n{'='*60}")
    print(f"Generating turnaround for: {character_info['name']}")
    print(f"Role: {character_info['role']}")
    print(f"{'='*60}")

    output_path = OUTPUT_DIR / f"{character_id}_turnaround.png"

    try:
        print(f"  Using model: {MODEL}")
        print(f"  Generating image...")

        response = client.models.generate_images(
            model=MODEL,
            prompt=character_info["prompt"],
            config=types.GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio="16:9",  # Wide format for turnaround
                safety_filter_level="BLOCK_LOW_AND_ABOVE",
                person_generation="ALLOW_ADULT",
            ),
        )

        if response.generated_images:
            image = response.generated_images[0]

            # Save the image
            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

            # The image data is in image.image.image_bytes
            if hasattr(image, 'image') and hasattr(image.image, 'image_bytes'):
                with open(output_path, 'wb') as f:
                    f.write(image.image.image_bytes)
                print(f"  SUCCESS: Saved to {output_path}")
                return True
            else:
                print(f"  ERROR: Unexpected image format: {type(image)}")
                return False
        else:
            print(f"  ERROR: No images generated")
            return False

    except Exception as e:
        print(f"  ERROR: {e}")
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
    print("Character Turnaround Sheet Generator")
    print("="*60)
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"Characters to generate: {len(TURNAROUND_PROMPTS)}")

    # Generate for each character
    results = {}
    for character_id, character_info in TURNAROUND_PROMPTS.items():
        results[character_id] = generate_turnaround(client, character_id, character_info)

        # Rate limiting - wait between requests
        time.sleep(3)

    # Print summary
    print("\n" + "="*60)
    print("GENERATION SUMMARY")
    print("="*60)

    success = sum(1 for v in results.values() if v)
    failed = sum(1 for v in results.values() if not v)

    for character_id, success_status in results.items():
        status = "SUCCESS" if success_status else "FAILED"
        print(f"  {character_id}: {status}")

    print("-"*60)
    print(f"  TOTAL: {success} succeeded, {failed} failed")

    # List generated files
    if OUTPUT_DIR.exists():
        print("\nGenerated files:")
        for f in sorted(OUTPUT_DIR.glob("*.png")):
            print(f"  - {f.name}")

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
