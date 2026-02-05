#!/usr/bin/env python3
"""Generate pencil sketch style storyboard images for comparison."""

import os
import sys
import time
from pathlib import Path

from google import genai
from google.genai import types

# Initialize client
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# Output directory for sketch versions
OUTPUT_DIR = Path(__file__).parent.parent / "storyboards" / "sketches"

# Pencil sketch versions of key panels for social media comparison
SKETCH_PANELS = [
    {
        "filename": "scene-01-panel-01-sketch.png",
        "prompt": """Traditional animation storyboard sketch, rough pencil drawing style,
hand-drawn look with visible pencil strokes and construction lines,
wide shot of cozy living room scene, family watching TV,
two children on couch, warm domestic setting,
sketchy line work like Pixar pre-production storyboards,
loose gestural drawing, minimal shading with cross-hatching,
annotation arrows and camera direction notes in margins,
professional storyboard artist style, not polished final art,
grayscale pencil on paper texture, 16:9 aspect ratio"""
    },
    {
        "filename": "scene-20-panel-01-sketch.png",
        "prompt": """Traditional animation storyboard sketch, rough pencil drawing style,
hand-drawn look with visible pencil strokes and construction lines,
medium shot of children in dimly lit shelter or hideout,
one girl sitting up alertly while others sleep around her,
sketchy line work like Pixar pre-production storyboards,
loose gestural drawing, minimal shading with cross-hatching,
annotation arrows and notes in margins,
professional storyboard artist style, not polished final art,
grayscale pencil on paper texture, 16:9 aspect ratio"""
    },
    {
        "filename": "scene-01-panel-04-sketch.png",
        "prompt": """Traditional animation storyboard sketch, rough pencil drawing style,
hand-drawn look with visible pencil strokes and construction lines,
two-shot of married couple in formal wear preparing to leave,
husband checking watch, wife putting on earrings, comedic timing,
children visible in background on couch,
sketchy line work like Pixar pre-production storyboards,
loose gestural drawing, minimal shading with cross-hatching,
professional storyboard artist style, not polished final art,
grayscale pencil on paper texture, 16:9 aspect ratio"""
    },
]


def generate_image(prompt: str, filename: str) -> bool:
    """Generate a single sketch image using Gemini 2.0 Flash."""
    output_path = OUTPUT_DIR / filename

    print(f"Generating: {filename}")
    print(f"  Prompt: {prompt[:80]}...")

    try:
        # Use Gemini 2.0 Flash with native image generation
        response = client.models.generate_content(
            model="gemini-2.5-flash-image",
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
                print(f"  ✓ Saved to {output_path}")
                return True

        print(f"  ✗ No image in response")
        return False

    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def main():
    """Generate pencil sketch storyboard panels."""
    print("=" * 60)
    print("Generating Pencil Sketch Storyboard Panels")
    print("=" * 60)
    print(f"Output directory: {OUTPUT_DIR}")
    print()

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    success_count = 0
    total = len(SKETCH_PANELS)

    for i, panel in enumerate(SKETCH_PANELS, 1):
        print(f"\n[{i}/{total}] ", end="")
        if generate_image(panel["prompt"], panel["filename"]):
            success_count += 1

        # Small delay between requests to avoid rate limiting
        if i < total:
            time.sleep(2)

    print("\n" + "=" * 60)
    print(f"Complete: {success_count}/{total} images generated")
    print("=" * 60)

    return 0 if success_count == total else 1


if __name__ == "__main__":
    sys.exit(main())
