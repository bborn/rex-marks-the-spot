#!/usr/bin/env python3
"""
Generate Mia turnaround iterations (V3 & V4) based on V1 style.

KEEP from V1:
- Overall Pixar style
- Yellow/mustard shirt
- Jeans and red sneakers
- Brown hair with ponytail
- 4-angle layout

REFINE:
- Make sure she looks 8 years old (not younger, not older)
- Adventurous/curious expression - she is the older sister who leads Leo into trouble
"""

import os
import sys
import time
from pathlib import Path
from google import genai
from google.genai import types

# Output directory
OUTPUT_DIR = Path("/tmp/mia_turnaround_output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Model for image generation
MODEL = "gemini-2.0-flash-exp-image-generation"

# Refined prompts emphasizing 4-angle layout very explicitly
PROMPTS = {
    "v3": """Create a CHARACTER TURNAROUND SHEET with EXACTLY 4 views of the SAME character arranged in a HORIZONTAL ROW.

The character is an 8-year-old adventurous girl for a Pixar-style animated movie.

CHARACTER DESIGN (must be IDENTICAL in all 4 views):
- Warm chestnut brown hair in a HIGH PONYTAIL with turquoise hair tie
- Big expressive brown eyes with adventurous sparkle
- Confident smile showing determination
- Age 8 - not a toddler, not a preteen
- Slim athletic build

OUTFIT (must be IDENTICAL in all 4 views):
- YELLOW/MUSTARD t-shirt (solid golden mustard color)
- BLUE DENIM JEANS (full length, not shorts)
- RED SNEAKERS with white soles

LAYOUT - 4 VIEWS IN A ROW, LEFT TO RIGHT:
VIEW 1 (leftmost): FRONT view - facing directly at camera, hands on hips
VIEW 2: THREE-QUARTER view - body rotated 45 degrees to the right
VIEW 3: BACK view - facing away from camera, ponytail visible
VIEW 4 (rightmost): SIDE PROFILE - facing right, full side view

Clean white background. Professional animation model sheet format.
3D Pixar cartoon style, NOT realistic.
All 4 views must show the EXACT SAME character design.""",

    "v4": """CHARACTER MODEL SHEET: 4 views of one 8-year-old girl in a horizontal row.

Pixar/Disney 3D animated style. Adventurous older sister character.

CRITICAL - EXACT HAIR STYLE:
- Long brown hair pulled back into a HIGH PONYTAIL (NOT a bun!)
- The ponytail hangs DOWN from the back of her head
- Turquoise/teal hair tie holding the ponytail
- Some loose strands frame her face

CHARACTER:
- 8 years old exactly - not younger, not older
- Big brown eyes with curious, adventurous expression
- Confident slight smile
- Athletic build for an active kid

OUTFIT:
- Golden MUSTARD YELLOW t-shirt
- Blue denim JEANS (full length)
- RED sneakers with white soles

4 VIEWS LEFT TO RIGHT:
1. FRONT - facing camera, confident stance
2. 3/4 VIEW - turned slightly, showing depth
3. BACK - showing the long ponytail hanging down
4. SIDE PROFILE - ponytail visible extending back

White background. Same character in all views.
3D Pixar cartoon style, NOT realistic."""
}


def generate_image(client, prompt: str, version: str, retry_count: int = 3) -> str | None:
    """Generate a single turnaround image using Gemini 2.0 Flash."""
    print(f"\n{'='*60}")
    print(f"Generating Mia turnaround {version}")
    print(f"{'='*60}")

    output_path = OUTPUT_DIR / f"mia_turnaround_{version}.png"

    for attempt in range(retry_count):
        try:
            print(f"  Using model: {MODEL}")
            print(f"  Attempt {attempt + 1}/{retry_count}...")

            # Use Gemini 2.0 Flash with native image generation
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
                    print(f"  SUCCESS: Saved to {output_path}")
                    return str(output_path)

            print(f"  WARNING: No image in response")
            if attempt < retry_count - 1:
                print(f"  Waiting 5 seconds before retry...")
                time.sleep(5)

        except Exception as e:
            print(f"  ERROR (attempt {attempt + 1}/{retry_count}): {e}")
            if attempt < retry_count - 1:
                print(f"  Waiting 5 seconds before retry...")
                time.sleep(5)

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
    print("Mia Turnaround V3/V4 Generator")
    print("(Iterating on V1 with refined age and expression)")
    print("="*60)
    print(f"Output directory: {OUTPUT_DIR}")

    results = {}

    # Generate V3
    results["v3"] = generate_image(client, PROMPTS["v3"], "v3")

    # Rate limiting - wait between requests (Gemini needs ~8 sec)
    print("\nWaiting 10 seconds before next generation...")
    time.sleep(10)

    # Generate V4
    results["v4"] = generate_image(client, PROMPTS["v4"], "v4")

    # Summary
    print("\n" + "="*60)
    print("GENERATION SUMMARY")
    print("="*60)

    for version, path in results.items():
        status = "SUCCESS" if path else "FAILED"
        print(f"  {version}: {status}")
        if path:
            print(f"         Path: {path}")

    # Return paths for upload
    return [p for p in results.values() if p]


if __name__ == "__main__":
    generated = main()
    if generated:
        print(f"\nGenerated {len(generated)} images successfully")
        sys.exit(0)
    else:
        print("\nNo images generated")
        sys.exit(1)
