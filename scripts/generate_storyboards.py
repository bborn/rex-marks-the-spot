#!/usr/bin/env python3
"""Generate storyboard images using Gemini API."""

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
OUTPUT_DIR = Path(__file__).parent.parent / "storyboards" / "act1" / "panels"

# Scene 1 prompts (9 panels)
SCENE_1_PANELS = [
    {
        "filename": "scene-01-panel-01.png",
        "prompt": """Storyboard panel, wide establishing shot, warm suburban living room,
Pixar animation style, cozy domestic chaos,
TV on left side flickering, couch center-left with two children,
kitchen visible in background, windows showing storm clouds darkening,
warm amber interior lighting, lightning flash through window,
dinosaur toys scattered on floor, family home atmosphere,
cinematic composition 16:9"""
    },
    {
        "filename": "scene-01-panel-02.png",
        "prompt": """Storyboard panel, medium shot, cute 5-year-old boy on couch,
Pixar animation style, wearing green dinosaur pajamas,
sitting cross-legged hugging plush T-Rex toy,
multiple plastic dinosaur toys around him,
TV glow on face, content expression watching cartoons,
warm domestic lighting, 16:9 cinematic composition"""
    },
    {
        "filename": "scene-01-panel-03.png",
        "prompt": """Storyboard panel, medium tracking shot, elegant mother late 30s,
Pixar animation style, walking through house putting on earrings,
wearing elegant black cocktail dress, multitasking,
moving from living room toward front door,
checking purse while walking, frantic but graceful movement,
warm domestic lighting, motion blur indicating movement,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-01-panel-04.png",
        "prompt": """Storyboard panel, two-shot medium, married couple in formal wear,
Pixar animation style, husband in black tuxedo checking watch impatiently,
wife in black dress still putting together her look,
overlapping conversation energy, comedy timing,
children visible on couch in background, babysitter absorbed in phone,
warm interior lighting, 16:9 cinematic composition"""
    },
    {
        "filename": "scene-01-panel-05.png",
        "prompt": """Storyboard panel, close-up insert, teenage babysitter blonde ponytail,
Pixar animation style, head tilted down looking at phone screen,
texting completely absorbed, oblivious expression,
phone glow illuminating face, background soft focus,
cheerful but disconnected, 16:9 cinematic composition"""
    },
    {
        "filename": "scene-01-panel-06.png",
        "prompt": """Storyboard panel, close-up, TV screen filling frame,
Pixar animation style, cartoon interrupted by static lines,
horizontal scan lines rolling through, blue electrical flicker,
lightning flash reflected in screen, ominous foreshadowing,
static distortion effect, 16:9 cinematic composition"""
    },
    {
        "filename": "scene-01-panel-07.png",
        "prompt": """Storyboard panel, over-the-shoulder shot from behind children,
Pixar animation style, boy in dinosaur pajamas and girl in pajamas,
backs of heads visible, looking at TV and parents in background,
parents still preparing to leave in background,
contrast between children's calm and parents' chaos,
TV glow on silhouettes, 16:9 cinematic composition"""
    },
    {
        "filename": "scene-01-panel-08.png",
        "prompt": """Storyboard panel, close-up emotional, 8-year-old girl face,
Pixar animation style, big expressive brown eyes looking up,
earnest concerned expression, need for reassurance,
TV flickering reflected in eyes, slight worry,
lightning flash briefly illuminating, vulnerable moment,
slow push composition, 16:9 cinematic composition"""
    },
    {
        "filename": "scene-01-panel-09.png",
        "prompt": """Storyboard panel, close-up to two-shot, father with glasses showing conflict,
Pixar animation style, mother entering frame with sharp glare,
husband uncomfortable, wife's "don't you dare" expression,
tension then relief when he finally promises,
rectangular glasses, stubble, black tuxedo,
dramatic family moment, 16:9 cinematic composition"""
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
