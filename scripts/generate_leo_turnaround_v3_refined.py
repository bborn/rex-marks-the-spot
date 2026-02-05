#!/usr/bin/env python3
"""
Generate refined Leo turnaround variations V3a and V3b.

Based on V3 reference:
https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/characters/leo/leo_turnaround_v3.png

Core design from V3:
- Fair skin (Caucasian)
- Sandy blonde/golden hair with slight wave
- Blue eyes
- 5 years old boy
- Chubby cheeks, cheerful expression
- Green dinosaur t-shirt
- Khaki cargo shorts
- Red sneakers
"""

import os
import sys
import time
from pathlib import Path

from google import genai
from google.genai import types

# Import upload helper
sys.path.insert(0, str(Path(__file__).parent))
from r2_upload import upload_file

# Configuration
OUTPUT_DIR = Path(__file__).parent.parent / "output" / "leo_turnaround_refined"
MODEL = "gemini-2.0-flash-exp-image-generation"  # Use Gemini 2.0 Flash for child characters

# Base prompt for Leo V3 refinement
BASE_PROMPT = """Professional 3D character turnaround sheet for animated movie production, Pixar/Dreamworks quality.

CHARACTER: Leo, 5-year-old boy
- Fair Caucasian skin tone with rosy cheeks
- Sandy blonde/golden hair with slight natural wave, messy boyish style
- Bright blue eyes, large and expressive
- Round face with chubby cheeks
- Cheerful, happy expression with big smile
- Small button nose with light freckles

OUTFIT:
- Green t-shirt with cute dinosaur graphic print
- Khaki cargo shorts with pockets
- Red sneakers with white soles

LAYOUT: Four character views on clean white background:
1. FRONT VIEW - facing camera directly, arms relaxed at sides
2. THREE-QUARTER VIEW - turned 45 degrees, showing depth
3. SIDE PROFILE - full side view
4. BACK VIEW - facing away from camera

STYLE: Pixar 3D animation aesthetic, stylized cartoon proportions with oversized head, soft rounded shapes.
Professional model sheet quality. Same character in all four poses. Clean white background.
Adorable, appealing character design suitable for family animated film."""

# Variation prompts with slight refinements
PROMPTS = {
    "v3a": BASE_PROMPT + """

ADDITIONAL: Emphasize warmth and approachability. Slightly more golden tone to the hair.
Expression showing genuine childlike joy. Soft ambient lighting on the character.""",

    "v3b": BASE_PROMPT + """

ADDITIONAL: Crisp, clean lines and vibrant colors. Hair has a slightly tousled, playful look.
Eyes have extra sparkle and catchlights. Slightly more saturated greens and reds in costume.""",
}


def generate_turnaround(client, variant_id: str, prompt: str) -> Path:
    """Generate a single turnaround variation."""
    print(f"\n{'='*60}")
    print(f"Generating Leo Turnaround {variant_id.upper()}")
    print(f"{'='*60}")

    output_path = OUTPUT_DIR / f"leo_turnaround_{variant_id}.png"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    try:
        print(f"  Model: {MODEL}")
        print(f"  Generating image...")

        # Use generate_content with image response modality
        response = client.models.generate_content(
            model=MODEL,
            contents=f"Generate an image: {prompt}",
            config=types.GenerateContentConfig(response_modalities=["IMAGE", "TEXT"]),
        )

        # Extract and save the image from the response
        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                image_data = part.inline_data.data
                with open(output_path, 'wb') as f:
                    f.write(image_data)
                print(f"  SUCCESS: Saved to {output_path}")
                return output_path

        print(f"  ERROR: No image in response")
        return None

    except Exception as e:
        print(f"  ERROR: {e}")
        return None


def main():
    """Main entry point."""
    # Initialize client
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY environment variable not set")
        sys.exit(1)

    client = genai.Client(api_key=api_key)

    print("="*60)
    print("Leo Turnaround V3 Refinement Generator")
    print("="*60)
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"Variants to generate: v3a, v3b")

    # Generate each variant
    results = {}
    for variant_id, prompt in PROMPTS.items():
        output_path = generate_turnaround(client, variant_id, prompt)
        results[variant_id] = output_path

        # Rate limiting - wait 10 seconds between requests
        if variant_id != list(PROMPTS.keys())[-1]:
            print("  Waiting 10 seconds for rate limit...")
            time.sleep(10)

    # Upload to R2
    print("\n" + "="*60)
    print("UPLOADING TO R2")
    print("="*60)

    uploaded_urls = {}
    for variant_id, local_path in results.items():
        if local_path and local_path.exists():
            r2_path = f"characters/leo/leo_turnaround_{variant_id}.png"
            try:
                url = upload_file(str(local_path), r2_path)
                uploaded_urls[variant_id] = url
            except Exception as e:
                print(f"  ERROR uploading {variant_id}: {e}")

    # Print summary
    print("\n" + "="*60)
    print("GENERATION SUMMARY")
    print("="*60)

    for variant_id in PROMPTS.keys():
        if variant_id in uploaded_urls:
            print(f"  {variant_id}: {uploaded_urls[variant_id]}")
        elif results.get(variant_id):
            print(f"  {variant_id}: Generated locally at {results[variant_id]}")
        else:
            print(f"  {variant_id}: FAILED")

    success_count = len(uploaded_urls)
    print(f"\n  Total uploaded: {success_count}/{len(PROMPTS)}")

    sys.exit(0 if success_count == len(PROMPTS) else 1)


if __name__ == "__main__":
    main()
