#!/usr/bin/env python3
"""
Mia Turnaround V4 Generator

Uses the approved Mia turnaround as input image for Gemini image-to-image.
Only changes the hair: makes curls chunkier and more sculpted (solid volumes like clay)
to prevent mesh artifacts when converting to 3D in Meshy.

Usage:
    python3 scripts/generate_mia_turnaround_v4.py
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
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
INPUT_IMAGE = PROJECT_DIR / "tmp" / "mia_turnaround_APPROVED.png"
OUTPUT_DIR = PROJECT_DIR / "tmp" / "mia_v4"
R2_DEST = "r2:rex-assets/characters/mia/turnaround-v4/"
R2_PUBLIC_BASE = "https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/characters/mia/turnaround-v4"

MODEL = "gemini-2.5-flash-image"

# Prompt variations - all keep the character identical, only change hair geometry
PROMPTS = [
    # Variation 1: Direct and specific
    """Redraw this exact character turnaround sheet keeping everything identical - same face with freckles, same skin tone, same pink star shirt, same blue jeans, same red sneakers, same pink hair scrunchie, same poses and views, same white background.

The ONLY change: make the curly hair into chunky sculpted solid volumes like Pixar clay animation. The curls should be thick rounded masses, not individual wispy strands. Hair silhouette should be smooth solid shapes with no flyaways or thin strands sticking out. Keep the half-up ponytail style with pink scrunchie. The hair should look like it was sculpted from clay - big rounded chunky curls grouped together into solid forms.""",

    # Variation 2: Emphasize 3D-ready
    """Redraw this exact character turnaround sheet. Keep EVERYTHING identical: same girl character, same face with brown eyes and freckles, same medium-brown skin tone, same pink t-shirt with white star pattern, same blue jeans, same red sneakers, same pink scrunchie holding half-ponytail, same four poses (front, side, side, back), same white background.

ONLY CHANGE THE HAIR GEOMETRY: Replace the thin individual curly strands with CHUNKY SOLID VOLUMES. Think of how Pixar or Disney would sculpt hair for a 3D character - big bold curved shapes, thick ribbon-like curls, solid masses that read as curly hair from a distance. No thin wisps, no individual strand detail, no flyaway hairs. The hair should have a smooth outer silhouette made of large rounded curl shapes. Keep the half-up ponytail with scrunchie.""",

    # Variation 3: Clay/sculptural focus
    """Reproduce this character turnaround sheet exactly as shown - identical character, face, outfit (pink star shirt, jeans, red sneakers), freckles, skin tone, poses, and white background.

THE ONLY MODIFICATION: Restyle the hair to look like sculpted clay or polymer clay. The curly hair should become THICK CHUNKY ROUNDED VOLUMES - imagine each curl is a fat ribbon of clay, not thin strands. Group the curls into 5-8 large solid masses instead of many individual thin curls. The overall hair shape and half-ponytail with pink scrunchie stays the same, but the internal detail becomes bold sculptural chunks rather than fine curly strands. Smooth outer silhouette with no wispy edges.""",

    # Variation 4: Simplified for 3D
    """Keep this character turnaround sheet exactly the same - same girl, same face, freckles, skin, pink shirt with stars, blue jeans, red sneakers, pink scrunchie, all four views, white background. Do not change anything about the character except the hair.

HAIR CHANGE ONLY: Simplify the curly hair into large smooth volumetric shapes. Instead of many thin individual curly strands, make the hair consist of BIG CHUNKY CURLS - thick solid rounded shapes like a Pixar character's hair. The curls should be bold and simplified, with clean smooth edges. No thin strands, no flyaways, no wispy bits. The ponytail and scrunchie stay, but all curls become fat solid tubes/ribbons of hair grouped into clear volumetric masses.""",

    # Variation 5: Minimal change emphasis
    """This is a perfect character turnaround. Recreate it identically with one tiny adjustment to the hair only.

Keep 100% the same: the girl's face with freckles, her brown eyes, her medium-brown skin, her pink t-shirt with white stars, her blue jeans, her red sneakers, her pink hair scrunchie, her half-up ponytail hairstyle, all four character views (front, three-quarter, side, back), and the clean white background.

Hair adjustment: Make each curl THICKER and more SOLID. Convert the thin curly strands into chunky rounded shapes - like how a sculptor would carve curly hair from a block of clay. Big bold curves instead of thin spirals. The overall hair silhouette stays the same shape but the surface becomes smoother with larger, chunkier curl definitions. This is for 3D model conversion so the hair needs clean solid forms."""
]


def generate_variation(client, reference_image, prompt, output_path, variation_num):
    """Generate one variation of the Mia turnaround."""
    print(f"\n{'='*60}")
    print(f"Generating variation {variation_num}...")
    print(f"Output: {output_path}")
    print(f"{'='*60}")

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=[prompt, reference_image],
            config=types.GenerateContentConfig(
                response_modalities=["TEXT", "IMAGE"]
            ),
        )

        if hasattr(response, "candidates") and response.candidates:
            for part in response.candidates[0].content.parts:
                if part.inline_data is not None:
                    img_bytes = part.inline_data.data
                    with open(output_path, "wb") as f:
                        f.write(img_bytes)

                    # Check dimensions
                    img = Image.open(output_path)
                    print(f"  Generated: {img.size[0]}x{img.size[1]}, {len(img_bytes):,} bytes")

                    # Upscale if needed (Meshy requires 1040x1040 minimum)
                    if img.size[0] < 1040 or img.size[1] < 1040:
                        scale = max(1040 / img.size[0], 1040 / img.size[1])
                        new_w = int(img.size[0] * scale)
                        new_h = int(img.size[1] * scale)
                        print(f"  Upscaling to {new_w}x{new_h} (Meshy minimum: 1040x1040)")
                        img_upscaled = img.resize((new_w, new_h), Image.LANCZOS)
                        img_upscaled.save(output_path)
                        print(f"  Saved upscaled version")

                    return True

                # Check for text response
                if hasattr(part, "text") and part.text:
                    print(f"  Text response: {part.text[:200]}")

        print(f"  ERROR: No image data in response")
        return False

    except Exception as e:
        print(f"  ERROR: {e}")
        return False


def upload_to_r2(output_dir):
    """Upload all generated images to R2."""
    print(f"\nUploading to R2: {R2_DEST}")
    try:
        result = subprocess.run(
            ["rclone", "copy", str(output_dir), R2_DEST, "--include", "*.png"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0:
            print(f"SUCCESS: Uploaded to R2")
            return True
        else:
            print(f"ERROR uploading: {result.stderr}")
            return False
    except Exception as e:
        print(f"ERROR uploading: {e}")
        return False


def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY environment variable not set")
        sys.exit(1)

    if not INPUT_IMAGE.exists():
        print(f"ERROR: Input image not found: {INPUT_IMAGE}")
        print("Download it first: rclone copy r2:rex-assets/characters/mia/mia_turnaround_APPROVED.png tmp/")
        sys.exit(1)

    print("=" * 60)
    print("Mia Turnaround V4 Generator")
    print("Hair simplification: chunky sculpted volumes for 3D")
    print(f"Model: {MODEL}")
    print(f"Input: {INPUT_IMAGE}")
    print("=" * 60)

    # Load reference image
    reference_image = Image.open(INPUT_IMAGE)
    print(f"Reference image loaded: {reference_image.size}")

    # Configure client
    client = genai.Client(api_key=api_key)

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Generate variations
    successes = []
    for i, prompt in enumerate(PROMPTS, 1):
        output_path = OUTPUT_DIR / f"mia_turnaround_v4_var{i}.png"
        success = generate_variation(client, reference_image, prompt, output_path, i)
        if success:
            successes.append(output_path)

        # Rate limit delay between requests
        if i < len(PROMPTS):
            delay = 10
            print(f"\nWaiting {delay}s for rate limit...")
            time.sleep(delay)

    print(f"\n{'='*60}")
    print(f"Results: {len(successes)}/{len(PROMPTS)} variations generated")
    print(f"{'='*60}")

    if not successes:
        print("FAILED: No images were generated")
        sys.exit(1)

    # List generated files
    for path in successes:
        img = Image.open(path)
        size_kb = path.stat().st_size / 1024
        print(f"  {path.name}: {img.size[0]}x{img.size[1]}, {size_kb:.0f}KB")

    # Upload to R2
    if upload_to_r2(OUTPUT_DIR):
        print(f"\nGenerated images available at:")
        for path in successes:
            print(f"  {R2_PUBLIC_BASE}/{path.name}")
    else:
        print(f"\nImages saved locally in {OUTPUT_DIR} but R2 upload failed")

    print(f"\nDONE!")


if __name__ == "__main__":
    main()
