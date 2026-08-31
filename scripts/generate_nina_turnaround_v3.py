#!/usr/bin/env python3
"""
Nina V3 Character Turnaround Generator

Generates Nina turnaround V3 combining:
- V2's burgundy sweater, dark jeans, white sneakers (cozy casual)
- V1's body proportions and build
- Reddish/auburn hair instead of plain brown

Model: gemini-2.5-flash-image-generation
Output: nina_turnaround_v3.png
"""

import os
import sys
import time
from pathlib import Path

from google import genai
from google.genai import types

sys.path.insert(0, str(Path(__file__).parent))
from genai_compat import generate_image  # noqa: E402

# Configuration
OUTPUT_DIR = Path(__file__).parent.parent / "assets" / "characters" / "nina"
MODEL = "gemini-2.5-flash-image"
OUTPUT_FILENAME = "nina_turnaround_v3.png"

NINA_V3_PROMPT = """Professional character turnaround sheet for 3D modeling reference.
Pixar/Dreamworks animation style, mother character age 37 named Nina.

HAIR: Shoulder-length reddish-auburn hair with natural soft waves, warm copper-red
highlights catching the light, rich auburn color (NOT plain brown, NOT bright red -
think natural warm reddish-brown auburn tone). Hair frames face with gentle movement.

FACE: Heart-shaped face with defined cheekbones, refined features.
Beautiful warm hazel-green eyes with kind, patient expression.
Medium/tan complexion with warm undertones. Full lips with natural rose color.

BODY: Average-height woman (5'7"), natural normal mom body proportions.
Not overly thin or overly curvy - realistic healthy proportions.
Slightly soft around the middle, approachable and relatable.
Natural posture, relaxed and confident.

OUTFIT (Cozy Casual):
- Soft burgundy/wine-colored oversized crew-neck sweater, slightly slouchy
- Dark blue/indigo skinny jeans, well-fitted
- Clean white canvas sneakers (like Converse low-tops)
- No jewelry except a simple wedding ring

Show FOUR views in a horizontal row on white background:
- FRONT view (facing camera, arms relaxed at sides)
- 3/4 view (turned 45 degrees, natural stance)
- SIDE view (full profile, showing body proportions)
- BACK view (facing away, hair and outfit details visible)

Character must be IDENTICAL in all four views - same person, same outfit, same hair.
Clean white background. Professional animation studio model sheet quality.
Warm, approachable mom character. NOT a fashion model - a real relatable parent.
Stylized Pixar 3D animation aesthetic with slightly exaggerated proportions."""


def generate_nina_v3():
    """Generate Nina V3 turnaround sheet."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY environment variable not set")
        sys.exit(1)

    client = genai.Client(api_key=api_key)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / OUTPUT_FILENAME

    print("=" * 60)
    print("Nina V3 Character Turnaround Generator")
    print("=" * 60)
    print(f"Model: {MODEL}")
    print(f"Output: {output_path}")
    print()

    # Try with Gemini flash image generation (text-to-image via generate_content)
    print("Generating Nina V3 turnaround...")
    print(f"Prompt preview: {NINA_V3_PROMPT[:120]}...")
    print()

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=f"Generate an image: {NINA_V3_PROMPT}",
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
            ),
        )

        # Extract image from response
        image_saved = False
        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                image_data = part.inline_data.data
                with open(output_path, "wb") as f:
                    f.write(image_data)
                print(f"SUCCESS: Saved to {output_path}")
                print(f"File size: {os.path.getsize(output_path) / 1024:.1f} KB")
                image_saved = True
                break
            elif part.text:
                print(f"Model text response: {part.text[:200]}")

        if not image_saved:
            print("ERROR: No image was generated in the response")
            print("Attempting with imagen model as fallback...")
            return try_imagen_fallback(client, output_path)

        return True

    except Exception as e:
        print(f"ERROR with {MODEL}: {e}")
        print("Attempting with imagen model as fallback...")
        return try_imagen_fallback(client, output_path)


FALLBACK_MODEL = "gemini-3-pro-image-preview"


def try_imagen_fallback(client, output_path):
    """Fallback to a second image model.

    Was Imagen 4 via client.models.generate_images(); google-genai 2.x removed
    that method from the Gemini Developer API surface, so this now retries on a
    different Gemini image model through generate_content().
    See docs/research/sdk-migration-decision.md.
    """
    try:
        print(f"\nUsing fallback model: {FALLBACK_MODEL}")

        image_bytes, text = generate_image(
            client, NINA_V3_PROMPT, model=FALLBACK_MODEL, aspect_ratio="16:9"
        )

        if image_bytes:
            with open(output_path, 'wb') as f:
                f.write(image_bytes)
            print(f"SUCCESS (fallback model): Saved to {output_path}")
            print(f"File size: {os.path.getsize(output_path) / 1024:.1f} KB")
            return True

        print("ERROR: No images generated with the fallback model either")
        if text:
            print(f"Model said: {text[:200]}")
        return False

    except Exception as e:
        print(f"ERROR with fallback model: {e}")
        return False


def main():
    success = generate_nina_v3()
    if success:
        print("\n" + "=" * 60)
        print("DONE: Nina V3 turnaround generated successfully!")
        print("=" * 60)
        print(f"\nNext step: Upload to R2")
        print(f"  rclone copy {OUTPUT_DIR / OUTPUT_FILENAME} r2:rex-assets/characters/nina/")
    else:
        print("\n" + "=" * 60)
        print("FAILED: Could not generate Nina V3 turnaround")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()
