#!/usr/bin/env python3
"""
Generate Leo turnaround variations v3c and v3d.

Iterating on v3a with the addition of a small gap between front teeth
(cute kid detail).

Character specs:
- Fair skin (Caucasian)
- Sandy blonde/golden hair with slight wave
- Blue eyes
- 5 years old boy
- Chubby cheeks, cheerful expression
- Green dinosaur t-shirt
- Khaki cargo shorts
- Red sneakers
- GAP BETWEEN FRONT TEETH (new detail)
- 3+ views (front, 3/4, side, back)

Style: Pixar 3D animation, character turnaround sheet
"""

import os
import sys
import time
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from google import genai
from google.genai import types
from r2_upload import upload_file

# Configuration - using gemini-2.5-flash-image per CLAUDE.md
MODEL = "gemini-2.5-flash-image"
OUTPUT_DIR = Path(__file__).parent.parent / "assets" / "characters" / "leo"

# Base prompt for Leo turnaround with tooth gap
LEO_TURNAROUND_BASE = """Pixar 3D animation style character turnaround sheet.

5-year-old boy character named Leo:
- Fair skin (Caucasian)
- Sandy blonde/golden hair with slight natural wave, tousled and messy
- Bright blue eyes, large and expressive
- Round chubby cheeks, cute and cheerful expression
- BIG SMILE showing a SMALL CUTE GAP BETWEEN HIS TWO FRONT TEETH (adorable kid detail)
- Green t-shirt with cartoon dinosaur print on front
- Khaki cargo shorts with pockets
- Bright red sneakers with white soles

Character turnaround showing FOUR VIEWS in a horizontal row:
1. FRONT VIEW - facing camera, arms relaxed at sides, showing the tooth gap in his smile
2. 3/4 VIEW - turned 45 degrees, cheerful expression
3. SIDE VIEW - full profile, showing hair texture
4. BACK VIEW - facing away, showing outfit from behind

White background, clean professional character model sheet layout.
Same exact character design in all four poses, consistent proportions.
Cute stylized Pixar/Disney animation style with slightly oversized head.
Professional animation studio quality reference sheet."""


def generate_image(client, prompt: str, filename: str) -> bool:
    """Generate a single turnaround image."""
    output_path = OUTPUT_DIR / filename

    print(f"\nGenerating: {filename}")
    print(f"Using model: {MODEL}")

    try:
        response = client.models.generate_content(
            model=MODEL,
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
                print(f"✓ Saved to {output_path}")
                return True

        print("✗ No image in response")
        # Check for text response explaining why
        for part in response.candidates[0].content.parts:
            if hasattr(part, 'text') and part.text:
                print(f"  Response text: {part.text}")
        return False

    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def main():
    """Generate Leo turnaround variations v3c and v3d."""
    # Initialize client
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY environment variable not set")
        sys.exit(1)

    client = genai.Client(api_key=api_key)

    print("=" * 60)
    print("Leo Turnaround Generator - v3c and v3d")
    print("Adding: Gap between front teeth (cute kid detail)")
    print("=" * 60)

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    variations = [
        {
            "filename": "leo_turnaround_v3c.png",
            "prompt": LEO_TURNAROUND_BASE + "\n\nVariation notes: Big cheerful grin showing the adorable tooth gap prominently in the front view.",
        },
        {
            "filename": "leo_turnaround_v3d.png",
            "prompt": LEO_TURNAROUND_BASE + "\n\nVariation notes: Slightly different expression angle, joyful smile with visible tooth gap, playful energy.",
        },
    ]

    results = []

    for i, var in enumerate(variations, 1):
        print(f"\n[{i}/{len(variations)}]")
        success = generate_image(client, var["prompt"], var["filename"])
        results.append((var["filename"], success))

        # Rate limiting - wait between requests
        if i < len(variations):
            print("Waiting 10 seconds for rate limit...")
            time.sleep(10)

    # Upload successful images to R2
    print("\n" + "=" * 60)
    print("Uploading to R2...")
    print("=" * 60)

    uploaded_urls = []
    for filename, success in results:
        if success:
            local_path = OUTPUT_DIR / filename
            r2_path = f"characters/leo/{filename}"
            try:
                url = upload_file(str(local_path), r2_path)
                uploaded_urls.append(url)
            except Exception as e:
                print(f"✗ Upload failed for {filename}: {e}")

    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    success_count = sum(1 for _, s in results if s)
    print(f"Generated: {success_count}/{len(variations)} images")

    if uploaded_urls:
        print("\nUploaded URLs:")
        for url in uploaded_urls:
            print(f"  {url}")

    return 0 if success_count == len(variations) else 1


if __name__ == "__main__":
    sys.exit(main())
