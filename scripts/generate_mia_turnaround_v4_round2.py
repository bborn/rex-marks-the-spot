#!/usr/bin/env python3
"""
Mia Turnaround V4 - Round 2

Round 1 results: vars 1-3 too subtle (hair barely changed), vars 4-5 too extreme (back view
looks like grape clusters). This round targets the sweet spot.

Also tries gemini-3-pro-image-preview for potentially better quality.
"""

import os
import sys
import time
import subprocess
from pathlib import Path

from google import genai
from google.genai import types
from PIL import Image

SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
INPUT_IMAGE = PROJECT_DIR / "tmp" / "mia_turnaround_APPROVED.png"
OUTPUT_DIR = PROJECT_DIR / "tmp" / "mia_v4"
R2_DEST = "r2:rex-assets/characters/mia/turnaround-v4/"
R2_PUBLIC_BASE = "https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/characters/mia/turnaround-v4"

# Try both models
MODELS = ["gemini-2.5-flash-image", "gemini-3-pro-image-preview"]

PROMPTS = [
    # Var 6: Middle ground - moderate chunking with natural look
    ("""Edit this character turnaround sheet. Keep the character, face, outfit, poses, and white background exactly the same.

ONLY modify the hair: Make the curly hair MORE CHUNKY and SOLID while keeping it looking like natural curly hair. Currently the curls are thin individual strands - merge groups of 3-4 thin strands into single thick chunky curls. The hair should have about HALF as many individual curl shapes, each one TWICE as thick. Think of Brave's Merida hair but with the curl detail simplified - fat rounded tubes instead of thin wispy spirals. The overall silhouette and ponytail shape stays identical. No stray flyaway hairs - clean edges on the hair silhouette.""", "gemini-2.5-flash-image"),

    # Var 7: Stronger direction with gemini-3-pro
    ("""Redraw this character turnaround sheet identically - same girl, same face with freckles, same pink star shirt, same jeans, same red sneakers, same pink scrunchie, same 4 views, same white background. Change NOTHING except the hair.

HAIR MODIFICATION: Convert the thin wispy individual curly strands into THICK CHUNKY SCULPTED CURLS suitable for 3D modeling. Each curl should be a solid rounded tube/ribbon shape, not thin individual strands. Reduce the total number of visible curl shapes by grouping small curls into larger solid masses. The hair should look like it was modeled in a 3D program - smooth solid volumes with rounded edges. Keep the same overall hair silhouette and half-ponytail with scrunchie. ALL views (front, side, and back) should show this chunky sculpted treatment consistently.""", "gemini-3-pro-image-preview"),

    # Var 8: Reference Pixar/Encanto style directly
    ("""Redraw this character turnaround keeping everything identical except the hair. Same face, freckles, skin tone, pink star shirt, jeans, red sneakers, scrunchie, poses, white background.

For the hair ONLY: Style it like Mirabel from Encanto or Moana's hair - thick chunky defined curls that read as solid 3D shapes. Each curl should be a distinct rounded volume, like tubes of clay. NOT thin individual strands. The curls should be chunky enough that you could easily model each one as a separate 3D shape. Keep the half-ponytail with pink scrunchie. Hair silhouette should be smooth and clean - no thin strands poking out from the main mass.""", "gemini-2.5-flash-image"),

    # Var 9: Even more explicit about what we want for 3D
    ("""This character turnaround needs ONE modification for 3D model conversion. Keep everything identical: girl's face, freckles, brown skin, pink shirt with white stars, blue jeans, red sneakers, pink hair scrunchie ponytail, all four rotation views, white background.

HAIR ONLY: The current thin curly strands will cause mesh artifacts in 3D conversion. Simplify the hair into BOLD CHUNKY VOLUMES:
- Front hair: 4-6 large curved chunks framing the face
- Ponytail: one thick solid mass with 3-4 large curl shapes at the end
- Side/back hair: 5-8 large rounded curl volumes hanging down
- Each curl should be thick like a finger, not thin like a strand
- Smooth rounded edges, no thin wispy details
- Clean silhouette with no flyaway strands
Keep it looking like curly hair, just much chunkier and more simplified.""", "gemini-3-pro-image-preview"),
]


def generate_variation(client, reference_image, prompt, model, output_path, var_num):
    print(f"\n{'='*60}")
    print(f"Generating variation {var_num} with {model}...")
    print(f"{'='*60}")

    try:
        response = client.models.generate_content(
            model=model,
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

                    img = Image.open(output_path)
                    print(f"  Generated: {img.size[0]}x{img.size[1]}, {len(img_bytes):,} bytes")

                    if img.size[0] < 1040 or img.size[1] < 1040:
                        scale = max(1040 / img.size[0], 1040 / img.size[1])
                        new_w = int(img.size[0] * scale)
                        new_h = int(img.size[1] * scale)
                        print(f"  Upscaling to {new_w}x{new_h}")
                        img.resize((new_w, new_h), Image.LANCZOS).save(output_path)

                    return True

                if hasattr(part, "text") and part.text:
                    print(f"  Text: {part.text[:200]}")

        print(f"  ERROR: No image in response")
        return False

    except Exception as e:
        print(f"  ERROR: {e}")
        return False


def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY not set")
        sys.exit(1)

    reference_image = Image.open(INPUT_IMAGE)
    print(f"Reference: {reference_image.size}")

    client = genai.Client(api_key=api_key)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    successes = []
    for i, (prompt, model) in enumerate(PROMPTS, 6):  # Start at var6
        output_path = OUTPUT_DIR / f"mia_turnaround_v4_var{i}.png"
        success = generate_variation(client, reference_image, prompt, model, output_path, i)
        if success:
            successes.append(output_path)

        if i < len(PROMPTS) + 5:
            delay = 10
            print(f"\nWaiting {delay}s...")
            time.sleep(delay)

    print(f"\n{'='*60}")
    print(f"Round 2 results: {len(successes)}/{len(PROMPTS)} generated")
    print(f"{'='*60}")

    if not successes:
        print("FAILED")
        sys.exit(1)

    for path in successes:
        img = Image.open(path)
        print(f"  {path.name}: {img.size[0]}x{img.size[1]}, {path.stat().st_size/1024:.0f}KB")

    # Upload
    result = subprocess.run(
        ["rclone", "copy", str(OUTPUT_DIR), R2_DEST, "--include", "*.png"],
        capture_output=True, text=True, timeout=120,
    )
    if result.returncode == 0:
        print(f"\nUploaded to R2:")
        for path in successes:
            print(f"  {R2_PUBLIC_BASE}/{path.name}")
    else:
        print(f"R2 upload failed: {result.stderr}")


if __name__ == "__main__":
    main()
