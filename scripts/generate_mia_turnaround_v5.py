#!/usr/bin/env python3
"""
Mia Turnaround V5 Generator - Simple wavy ponytail (not curly)

Uses image-to-image with the approved Mia turnaround as input.
Changes ONLY the hair to a simple wavy ponytail suitable for animation.

Usage:
    python scripts/generate_mia_turnaround_v5.py

Outputs 5 variations to output/turnaround-v5/, uploads to R2.
"""

import os
import sys
import time
import subprocess
from pathlib import Path

from google import genai
from google.genai import types
from PIL import Image

# Configuration
OUTPUT_DIR = Path(__file__).parent.parent / "output" / "turnaround-v5"
INPUT_IMAGE = Path(__file__).parent.parent / "output" / "mia_turnaround_APPROVED.png"
MODEL = "gemini-3-pro-image-preview"
R2_DEST = "r2:rex-assets/characters/mia/turnaround-v5/"
R2_BASE_URL = "https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/characters/mia/turnaround-v5"
MIN_SIZE = 1040

# 5 prompt variations - all targeting simple wavy ponytail
VARIATIONS = [
    {
        "name": "v5a",
        "prompt": (
            "Redraw this exact character turnaround sheet. Keep the same face, freckles, "
            "skin tone, pink star shirt, jeans, red sneakers, and all 4 poses exactly as shown. "
            "ONLY change the hair: replace the curly hair with a SIMPLE WAVY PONYTAIL. "
            "The hair should be smooth flowing waves pulled back into a single ponytail, NOT curls. "
            "Hair should be solid chunky shapes like Pixar/Disney animation hair — no individual strands "
            "or ringlets. Keep the pink hair tie/scrunchie. The hair silhouette should be smooth and simple, "
            "easy to animate as a solid mass. Two simple front framing pieces + one ponytail in back. "
            "White background."
        ),
    },
    {
        "name": "v5b",
        "prompt": (
            "Redraw this character turnaround sheet identically — same girl, same face with freckles, "
            "same pink star t-shirt, same blue jeans, same red sneakers, same 4 views (front, 3/4, side, back). "
            "The ONLY change: give her a SIMPLE WAVY PONYTAIL instead of curly hair. "
            "Think smooth, flowing, animation-friendly hair like Rapunzel or Anna from Frozen — "
            "gentle waves, NOT tight curls or ringlets. The ponytail should be one smooth solid shape. "
            "A few soft bangs/framing pieces in front, pulled back with a pink scrunchie. "
            "No flyaway strands, no spiral curls. Clean, smooth, chunky hair volumes. White background."
        ),
    },
    {
        "name": "v5c",
        "prompt": (
            "Reproduce this character turnaround sheet with one modification to the hair only. "
            "Keep everything else EXACTLY the same: face, freckles, expression, pink shirt with star, "
            "jeans, red sneakers, body proportions, all 4 poses on white background. "
            "HAIR CHANGE: Replace curly hair with a sleek wavy ponytail. The hair should have "
            "gentle S-curve waves, NOT spiral curls. It should look like smooth clay or sculpted shapes — "
            "two simple side-swept pieces framing the face, and one thick wavy ponytail gathered at the back "
            "with a pink hair tie. The ponytail hangs down as one unified shape with soft wave texture. "
            "Think 3D animation character hair that moves as one piece."
        ),
    },
    {
        "name": "v5d",
        "prompt": (
            "Recreate this exact character model sheet, changing ONLY the hairstyle. "
            "Same Pixar-style 8-year-old girl, same face with freckles, same pink star shirt, "
            "same jeans, same red sneakers, same 4 rotation views on white background. "
            "NEW HAIR: Simple wavy ponytail — imagine smooth dark brown hair with loose, gentle waves "
            "(like beach waves, NOT ringlet curls). Hair is pulled back into a low-to-mid ponytail "
            "secured with a pink scrunchie. Front pieces are smooth and swept to the sides. "
            "The overall hair shape is SIMPLE — maximum 2-3 large smooth shapes, no intricate curl details. "
            "This is hair designed for 3D animation — smooth, chunky, solid volumes."
        ),
    },
    {
        "name": "v5e",
        "prompt": (
            "Redraw this character turnaround keeping the identical character design: same young girl "
            "with freckles, same pink star top, same blue jeans, same red sneakers, same 4 angles. "
            "CHANGE ONLY THE HAIR to a simple wavy ponytail style. Requirements: "
            "1) Smooth wavy texture, absolutely NO tight curls or ringlets. "
            "2) Hair pulled into a single ponytail with a pink hair tie. "
            "3) Soft face-framing pieces on both sides, smooth and simple. "
            "4) The ponytail is one big smooth wavy shape, like a thick ribbon with gentle S-waves. "
            "5) Overall silhouette is clean and simple — think Moana or Elsa-style animated hair. "
            "6) Dark brown color. White background, professional model sheet quality."
        ),
    },
]


def generate_variation(client, input_image, variation):
    """Generate a single turnaround variation."""
    name = variation["name"]
    prompt = variation["prompt"]
    output_path = OUTPUT_DIR / f"mia_turnaround_{name}.png"

    print(f"\nGenerating: {name}")
    print(f"  Output: {output_path}")

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=[prompt, input_image],
            config=types.GenerateContentConfig(
                response_modalities=["TEXT", "IMAGE"],
            ),
        )

        # Extract image from response
        if response.candidates:
            for part in response.candidates[0].content.parts:
                if part.inline_data is not None:
                    img_bytes = part.inline_data.data
                    with open(output_path, "wb") as f:
                        f.write(img_bytes)
                    print(f"  Saved raw: {len(img_bytes):,} bytes")

                    # Check size and upscale if needed
                    img = Image.open(output_path)
                    print(f"  Dimensions: {img.size}")
                    if img.width < MIN_SIZE or img.height < MIN_SIZE:
                        scale = max(MIN_SIZE / img.width, MIN_SIZE / img.height)
                        new_w = int(img.width * scale)
                        new_h = int(img.height * scale)
                        img = img.resize((new_w, new_h), Image.LANCZOS)
                        img.save(output_path)
                        print(f"  Upscaled to: {img.size}")

                    return output_path

        # Check for text-only response (prompt issues)
        if response.candidates:
            for part in response.candidates[0].content.parts:
                if hasattr(part, "text") and part.text:
                    print(f"  Text response: {part.text[:200]}")

        print(f"  ERROR: No image in response")
        return None

    except Exception as e:
        print(f"  ERROR: {e}")
        return None


def upload_to_r2(local_path):
    """Upload a file to R2."""
    filename = local_path.name
    print(f"  Uploading {filename} to R2...")
    try:
        result = subprocess.run(
            ["rclone", "copy", str(local_path), R2_DEST],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0:
            url = f"{R2_BASE_URL}/{filename}"
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

    print("=" * 60)
    print("Mia Turnaround V5 - Simple Wavy Ponytail")
    print("=" * 60)
    print(f"Model: {MODEL}")
    print(f"Input: {INPUT_IMAGE}")
    print(f"Output: {OUTPUT_DIR}")
    print(f"Min size: {MIN_SIZE}x{MIN_SIZE}")

    # Verify input image exists
    if not INPUT_IMAGE.exists():
        print(f"\nERROR: Input image not found: {INPUT_IMAGE}")
        print("Download it first:")
        print("  curl -o output/mia_turnaround_APPROVED.png \\")
        print("    https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/characters/mia/mia_turnaround_APPROVED.png")
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load input image
    input_image = Image.open(INPUT_IMAGE)
    print(f"Input image loaded: {input_image.size}")

    # Initialize client
    client = genai.Client(api_key=api_key)

    # Generate all variations
    results = []
    urls = []
    for i, variation in enumerate(VARIATIONS):
        output_path = generate_variation(client, input_image, variation)
        success = output_path is not None
        results.append((variation["name"], success, output_path))

        if success:
            url = upload_to_r2(output_path)
            if url:
                urls.append((variation["name"], url))

        # Rate limiting between requests
        if i < len(VARIATIONS) - 1:
            delay = 10
            print(f"\n  Waiting {delay}s for rate limiting...")
            time.sleep(delay)

    # Summary
    print("\n" + "=" * 60)
    print("GENERATION SUMMARY")
    print("=" * 60)

    for name, success, path in results:
        status = "SUCCESS" if success else "FAILED"
        print(f"  mia_turnaround_{name}.png: {status}")

    successful = sum(1 for _, s, _ in results if s)
    print(f"\n  Total: {successful}/{len(results)} successful")

    if urls:
        print("\nR2 URLs:")
        for name, url in urls:
            print(f"  {name}: {url}")

    return 0 if successful > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
