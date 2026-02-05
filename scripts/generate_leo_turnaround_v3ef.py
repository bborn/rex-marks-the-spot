#!/usr/bin/env python3
"""
Generate Leo turnaround sheet iterations V3e and V3f.

Based on V3d feedback:
- REMOVE the dinosaur tail on the back of the shorts
- Keep everything else from V3d (which was the best version)

Character specs:
- Fair skin (Caucasian)
- Sandy blonde/golden hair with slight wave
- Blue eyes, tooth gap when smiling
- 5 years old boy
- Chubby cheeks, cheerful expression
- Green dinosaur t-shirt (dino on FRONT only)
- PLAIN khaki cargo shorts (NO tail, NO dino details on back)
- Red sneakers
- 4 views (front, 3/4, side, back)
- Can hold a toy dino in side view

Style: Pixar 3D animation, character turnaround sheet
"""

import os
import sys
import time
import subprocess
from pathlib import Path

from google import genai
from google.genai import types

# Initialize client
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# Output directory
OUTPUT_DIR = Path(__file__).parent.parent / "output" / "leo_turnaround"

# R2 destination
R2_PATH = "characters/leo"

# The turnaround prompt - emphasizing NO TAIL on shorts
LEO_TURNAROUND_PROMPT = """3D animated character turnaround reference sheet in Pixar animation style.

CHARACTER: Leo, 5-year-old Caucasian boy
- Fair/light skin tone
- Sandy blonde/golden hair with slight wave, messy and tousled
- Big bright BLUE eyes with childlike sparkle
- Chubby cheeks, round face
- Big cheerful smile showing a cute tooth gap
- Small button nose

OUTFIT (CRITICAL - read carefully):
- GREEN T-SHIRT with a cute cartoon dinosaur printed on the FRONT of the shirt ONLY
- PLAIN KHAKI CARGO SHORTS - absolutely NO tail, NO dinosaur details, NO decorations on the back. The shorts are completely plain on the back side.
- RED SNEAKERS with white soles

TURNAROUND VIEWS - Show the SAME character in 4 views arranged left to right:
1. FRONT VIEW - Facing camera, arms slightly out, happy expression
2. THREE-QUARTER VIEW - Turned 45 degrees, can hold a small toy dinosaur plush
3. SIDE PROFILE VIEW - Full side view, holding toy dinosaur
4. BACK VIEW - Facing completely away, showing the PLAIN back of his shorts (NO TAIL), back of his head showing blonde hair

CRITICAL: The BACK VIEW must show completely PLAIN khaki shorts with NO tail, NO dinosaur elements. Just normal cargo shorts from behind.

Style: Pixar/Disney 3D animation, professional character model sheet
Background: Clean white/light gray
Quality: High detail, consistent character across all 4 views
Proportions: Stylized cartoon with slightly oversized head typical of Pixar kid characters"""


def generate_image(prompt: str, filename: str, variation_note: str = "") -> bool:
    """Generate a single turnaround image using Gemini 2.5 Flash Image."""
    output_path = OUTPUT_DIR / filename

    full_prompt = prompt
    if variation_note:
        full_prompt = f"{prompt}\n\n{variation_note}"

    print(f"Generating: {filename}")
    print(f"  Variation: {variation_note if variation_note else 'base'}")

    try:
        # Use Gemini 2.5 Flash Image Generation (per CLAUDE.md recommendation)
        response = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=f"Generate an image: {full_prompt}",
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
                print(f"  ✓ Saved to {output_path}")
                return True

        print(f"  ✗ No image in response")
        if response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'text') and part.text:
                    print(f"  Response text: {part.text[:200]}")
        return False

    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def upload_to_r2(local_path: Path, r2_path: str) -> bool:
    """Upload file to R2 using rclone."""
    print(f"Uploading {local_path.name} to r2:rex-assets/{r2_path}/")
    try:
        result = subprocess.run(
            ["rclone", "copy", str(local_path), f"r2:rex-assets/{r2_path}/"],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"  ✓ Uploaded to https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/{r2_path}/{local_path.name}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  ✗ Upload failed: {e.stderr}")
        return False


def main():
    """Generate Leo turnaround sheets V3e and V3f."""
    print("=" * 70)
    print("Leo Turnaround Sheet Generator - V3e and V3f")
    print("=" * 70)
    print("Fixes from V3d: Removing dinosaur tail from back of shorts")
    print()

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Define variations
    variations = [
        {
            "filename": "leo_turnaround_v3e.png",
            "note": "Variation E: Emphasize the playful, energetic pose. In the side view, Leo holds his toy dinosaur up proudly."
        },
        {
            "filename": "leo_turnaround_v3f.png",
            "note": "Variation F: Slightly calmer poses. In the side view, Leo hugs his toy dinosaur close to his chest."
        },
    ]

    results = []

    for i, var in enumerate(variations, 1):
        print(f"\n[{i}/{len(variations)}]")

        success = generate_image(
            LEO_TURNAROUND_PROMPT,
            var["filename"],
            var["note"]
        )
        results.append((var["filename"], success))

        # Delay between generations (rate limiting)
        if i < len(variations):
            print("  Waiting 10 seconds for rate limiting...")
            time.sleep(10)

    print("\n" + "=" * 70)
    print("GENERATION RESULTS")
    print("=" * 70)

    # Upload successful generations to R2
    for filename, success in results:
        if success:
            local_path = OUTPUT_DIR / filename
            upload_to_r2(local_path, R2_PATH)
        else:
            print(f"  ✗ {filename} - Generation failed, skipping upload")

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    success_count = sum(1 for _, s in results if s)
    print(f"Generated: {success_count}/{len(variations)}")

    print("\nR2 URLs (if successful):")
    for filename, success in results:
        if success:
            url = f"https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/{R2_PATH}/{filename}"
            print(f"  {url}")

    return 0 if success_count == len(variations) else 1


if __name__ == "__main__":
    sys.exit(main())
