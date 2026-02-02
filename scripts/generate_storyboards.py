#!/usr/bin/env python3
"""Generate storyboard images using Gemini API.

STYLE: Rough sketch storyboards - like Pixar thumbnail boards.
Simple, loose pencil sketches focusing on composition and staging.
Black and white or grayscale. NOT detailed final renders.
"""

import base64
import os
import sys
import time
from pathlib import Path

from google import genai
from google.genai import types

# Initialize client
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# Output directory
OUTPUT_DIR = Path(__file__).parent.parent / "docs" / "storyboards" / "act1" / "panels"

# Rough sketch style prefix - applied to all prompts
SKETCH_STYLE = """Rough pencil sketch storyboard panel, black and white,
loose gestural lines, animation production thumbnail style,
simple shapes for characters, focus on composition and staging,
hand-drawn look with visible sketch lines, NOT rendered or polished,
professional storyboard artist style like Pixar pre-production thumbnails,
grayscale with hatching for shadows, 16:9 aspect ratio"""

# Scene 1 prompts (9 panels) - ROUGH SKETCH STYLE
SCENE_1_PANELS = [
    {
        "filename": "scene-01-panel-01.png",
        "prompt": f"""{SKETCH_STYLE},
WIDE ESTABLISHING SHOT - living room interior,
TV screen left (simple rectangle), couch center with two small child figures,
kitchen area sketched in background right, window showing storm clouds,
dinosaur toy shapes scattered on floor, cozy family home feel,
arrow indicating lightning flash through window"""
    },
    {
        "filename": "scene-01-panel-02.png",
        "prompt": f"""{SKETCH_STYLE},
MEDIUM SHOT - small boy figure on couch,
simple child shape wearing pajamas with dinosaur pattern indicated,
sitting cross-legged hugging round plush toy shape,
smaller toy shapes around him, TV glow indicated with light hatching,
content relaxed posture, watching off-screen"""
    },
    {
        "filename": "scene-01-panel-03.png",
        "prompt": f"""{SKETCH_STYLE},
TRACKING SHOT - woman figure walking through house,
elegant dress shape indicated, hands at ears (putting on earrings),
motion lines showing movement left to right,
purse in hand, rushing body language,
interior doorway and furniture shapes in background"""
    },
    {
        "filename": "scene-01-panel-04.png",
        "prompt": f"""{SKETCH_STYLE},
TWO-SHOT MEDIUM - couple in formal wear,
man figure right checking watch (impatient gesture),
woman figure left still getting ready,
children on couch in background (simple shapes),
teen figure in chair looking at phone rectangle,
comedy staging, overlapping conversation energy"""
    },
    {
        "filename": "scene-01-panel-05.png",
        "prompt": f"""{SKETCH_STYLE},
CLOSE-UP INSERT - teenage girl looking at phone,
ponytail hairstyle indicated, head tilted down,
phone rectangle glowing in hands,
completely absorbed expression, oblivious posture,
background indicated with minimal lines"""
    },
    {
        "filename": "scene-01-panel-06.png",
        "prompt": f"""{SKETCH_STYLE},
CLOSE-UP - TV screen filling frame,
static lines drawn across screen rectangle,
zigzag lines indicating electrical interference,
ominous mood, foreshadowing element,
simple TV frame edges visible"""
    },
    {
        "filename": "scene-01-panel-07.png",
        "prompt": f"""{SKETCH_STYLE},
OVER-SHOULDER SHOT - behind two children on couch,
backs of heads in foreground (boy and girl shapes),
TV rectangle visible ahead, parents figures in background,
parents still rushing around, children calm watching,
contrast in energy levels indicated through pose"""
    },
    {
        "filename": "scene-01-panel-08.png",
        "prompt": f"""{SKETCH_STYLE},
CLOSE-UP - young girl's face,
big expressive eyes looking up (off-screen to parents),
worried/concerned expression, eyebrows raised,
simple face with emotional read clear,
vulnerability shown in posture and expression"""
    },
    {
        "filename": "scene-01-panel-09.png",
        "prompt": f"""{SKETCH_STYLE},
CLOSE-UP TO TWO-SHOT - father with glasses,
man figure showing hesitation/conflict in expression,
woman figure entering frame with stern look,
tension between them visible in body language,
dramatic family moment, glasses indicated on father"""
    },
]


def generate_image(prompt: str, filename: str) -> bool:
    """Generate a single image using Gemini 2.0 Flash."""
    output_path = OUTPUT_DIR / filename

    print(f"Generating: {filename}")
    print(f"  Prompt: {prompt[:80]}...")

    try:
        # Use Gemini 2.0 Flash with native image generation
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp-image-generation",
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
    """Generate all Scene 1 storyboard panels."""
    print("=" * 60)
    print("Generating Act 1, Scene 1 Storyboard Panels")
    print("=" * 60)
    print(f"Output directory: {OUTPUT_DIR}")
    print()

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    success_count = 0
    total = len(SCENE_1_PANELS)

    for i, panel in enumerate(SCENE_1_PANELS, 1):
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
