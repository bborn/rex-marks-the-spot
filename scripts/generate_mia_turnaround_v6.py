#!/usr/bin/env python3
"""
Generate Mia turnaround v6 - remove front hair wisps from v5b and v5e.

Uses Gemini image-to-image to redraw the turnaround sheets with hair wisps
removed from in front of the ears. All hair should be swept back cleanly
into the ponytail.
"""

import os
import sys
import time
from pathlib import Path

from google import genai
from google.genai import types
from PIL import Image

# Initialize client
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# Directories
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
INPUT_DIR = PROJECT_DIR / "output" / "v6"
OUTPUT_DIR = PROJECT_DIR / "output" / "v6"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# The edit prompt
EDIT_PROMPT = (
    "Redraw this character turnaround sheet exactly as-is, but remove the small "
    "hair pieces hanging in front of the ears. All hair should be swept back "
    "cleanly into the ponytail. No loose strands or wisps framing the face. "
    "The front hairline should be clean and smooth, hair pulled back from the "
    "forehead. Keep everything else identical — same face, freckles, skin tone, "
    "outfit, poses, ponytail style, background color, and layout."
)

# Source images and their output prefixes
SOURCES = [
    ("mia_turnaround_v5b.png", "mia_v6_from5b"),
    ("mia_turnaround_v5e.png", "mia_v6_from5e"),
]

NUM_VARIATIONS = 3
DELAY_BETWEEN_REQUESTS = 12  # seconds


def generate_variation(source_path: Path, output_prefix: str, var_num: int) -> Path | None:
    """Generate one variation from a source image."""
    output_path = OUTPUT_DIR / f"{output_prefix}_var{var_num}.png"

    if output_path.exists():
        print(f"  Already exists: {output_path.name}, skipping")
        return output_path

    print(f"  Generating {output_path.name}...")
    image = Image.open(source_path)

    try:
        response = client.models.generate_content(
            model="gemini-3-pro-image-preview",
            contents=[EDIT_PROMPT, image],
            config=types.GenerateContentConfig(response_modalities=["TEXT", "IMAGE"]),
        )

        # Extract image from response
        if response.candidates:
            for part in response.candidates[0].content.parts:
                if part.inline_data and part.inline_data.mime_type.startswith("image/"):
                    # Save the image
                    import io
                    img_data = part.inline_data.data
                    result_img = Image.open(io.BytesIO(img_data))

                    # Upscale if needed (target: at least 1040x1040)
                    min_dim = min(result_img.size)
                    if min_dim < 1040:
                        scale = 1040 / min_dim
                        new_w = int(result_img.width * scale)
                        new_h = int(result_img.height * scale)
                        result_img = result_img.resize(
                            (max(new_w, 1040), max(new_h, 1040)),
                            Image.LANCZOS,
                        )
                        print(f"    Upscaled to {result_img.size}")

                    result_img.save(output_path, "PNG")
                    print(f"    Saved: {output_path.name} ({result_img.size})")
                    return output_path

        print(f"    WARNING: No image in response for {output_path.name}")
        # Print text parts for debugging
        if response.candidates:
            for part in response.candidates[0].content.parts:
                if part.text:
                    print(f"    Response text: {part.text[:200]}")
        return None

    except Exception as e:
        print(f"    ERROR: {e}")
        return None


def main():
    print("=" * 60)
    print("Mia Turnaround V6 - Remove Front Hair Wisps")
    print("=" * 60)

    results = []

    for source_file, prefix in SOURCES:
        source_path = INPUT_DIR / source_file
        if not source_path.exists():
            print(f"ERROR: Source not found: {source_path}")
            sys.exit(1)

        print(f"\nSource: {source_file}")
        for var in range(1, NUM_VARIATIONS + 1):
            result = generate_variation(source_path, prefix, var)
            results.append((f"{prefix}_var{var}.png", result))

            if var < NUM_VARIATIONS or source_file != SOURCES[-1][0]:
                print(f"  Waiting {DELAY_BETWEEN_REQUESTS}s for rate limit...")
                time.sleep(DELAY_BETWEEN_REQUESTS)

    print("\n" + "=" * 60)
    print("Results:")
    print("=" * 60)
    success = 0
    for name, path in results:
        if path and path.exists():
            img = Image.open(path)
            print(f"  OK: {name} ({img.size})")
            success += 1
        else:
            print(f"  FAILED: {name}")

    print(f"\n{success}/{len(results)} variations generated successfully")
    return success > 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
