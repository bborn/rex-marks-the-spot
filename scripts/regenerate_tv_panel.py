#!/usr/bin/env python3
"""Regenerate the TV static panel (scene-01-panel-06) with improved prompt.

This fixes the QA-flagged panel that showed pure TV static instead of a proper
storyboard showing a TV with cartoon content being disrupted by interference.
"""

import os
import sys
from pathlib import Path

from google import genai
from google.genai import types

# Initialize client
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# Output paths - update both locations
STORYBOARD_DIR = Path(__file__).parent.parent / "storyboards" / "act1" / "panels"
DOCS_DIR = Path(__file__).parent.parent / "docs" / "storyboards" / "act1" / "panels"
FILENAME = "scene-01-panel-06.png"

# Improved prompt - clearly shows a TV with interference, not pure static
SKETCH_STYLE = """Rough pencil sketch storyboard panel, black and white,
loose gestural lines, animation production thumbnail style,
simple shapes for characters, focus on composition and staging,
hand-drawn look with visible sketch lines, NOT rendered or polished,
professional storyboard artist style like Pixar pre-production thumbnails,
grayscale with hatching for shadows, 16:9 aspect ratio"""

IMPROVED_PROMPT = f"""{SKETCH_STYLE},
CLOSE-UP shot of a vintage TV set in a living room,
TV screen showing a cartoon dinosaur that is being disrupted,
diagonal interference lines and zigzag electrical distortion overlaying the cartoon image,
the TV frame is clearly visible around the screen,
blue electrical flicker effect indicated with sketch lines emanating from screen,
lightning flash from outside window reflected in TV glass,
ominous foreshadowing mood, supernatural interference beginning,
NOT pure static - cartoon content still visible behind the distortion"""


def generate_image(prompt: str, output_path: Path) -> bool:
    """Generate an image using Gemini 2.0 Flash."""
    print(f"Generating panel to: {output_path}")
    print(f"  Prompt preview: {prompt[:100]}...")

    try:
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

        print("  ✗ No image in response")
        return False

    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def main():
    """Regenerate the TV panel."""
    print("=" * 60)
    print("Regenerating Scene 1, Panel 6 - TV Flickering")
    print("=" * 60)
    print()
    print("Issue: Previous panel showed pure TV static")
    print("Fix: Generate proper storyboard showing TV with interference")
    print()

    # Ensure output directories exist
    STORYBOARD_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    # Generate to the storyboards directory (main panel location)
    success = generate_image(IMPROVED_PROMPT, STORYBOARD_DIR / FILENAME)

    if success:
        # Copy to docs directory as well for website
        import shutil
        src = STORYBOARD_DIR / FILENAME
        dst = DOCS_DIR / FILENAME
        shutil.copy(src, dst)
        print(f"  ✓ Also copied to {dst}")

    print()
    print("=" * 60)
    print("Done!" if success else "Failed!")
    print("=" * 60)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
