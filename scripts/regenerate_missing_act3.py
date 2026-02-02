#!/usr/bin/env python3
"""Regenerate missing Act 3 storyboard panels."""

import os
import time
from pathlib import Path

from google import genai
from google.genai import types

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
OUTPUT_DIR = Path(__file__).parent.parent / "storyboards" / "act3" / "panels"

STYLE_PREFIX = """Rough storyboard sketch, simple black and white pencil drawing,
loose gestural lines, basic shapes for characters, professional animation thumbnail style,
focus on composition and camera angle, NOT detailed or polished,
quick sketch like Pixar story artist thumbnails, grayscale only, 16:9 aspect ratio."""

MISSING_PANELS = [
    {"filename": "scene-27-panel-15.png", "prompt": "Close-up of Mia. She imitates Leo in mocking tone, nose pinched. Classic sibling mockery expression."},
    {"filename": "scene-27-panel-16.png", "prompt": "Medium shot of Ruben. He stares up at dissipating plume, gears turning in head. Thoughtful realization dawning."},
    {"filename": "scene-27-panel-39.png", "prompt": "Medium shot. Leo gets another candy from bag, offers to Jetplane the chicken-lizard creature."},
    {"filename": "scene-36-panel-23.png", "prompt": "Medium shot of Gabe (man with glasses in torn tuxedo). He steps between police guns and giant Jetplane creature, hands raised. Desperate to defuse situation."},
]

def generate_image(prompt: str, filename: str) -> bool:
    output_path = OUTPUT_DIR / filename
    full_prompt = f"{STYLE_PREFIX}\n\nScene: {prompt}"

    print(f"Generating: {filename}")
    print(f"  Prompt: {prompt[:60]}...")

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp-image-generation",
            contents=f"Generate an image: {full_prompt}",
            config=types.GenerateContentConfig(response_modalities=["IMAGE", "TEXT"]),
        )

        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                with open(output_path, "wb") as f:
                    f.write(part.inline_data.data)
                print(f"  ✓ Saved to {output_path}")
                return True
        print(f"  ✗ No image in response")
        return False
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

def main():
    print("Regenerating missing Act 3 panels...")
    success = 0
    for panel in MISSING_PANELS:
        if generate_image(panel["prompt"], panel["filename"]):
            success += 1
        time.sleep(2)
    print(f"\nComplete: {success}/{len(MISSING_PANELS)} regenerated")

if __name__ == "__main__":
    main()
