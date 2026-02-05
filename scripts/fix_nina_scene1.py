#!/usr/bin/env python3
"""Fix Nina's appearance in Scene 1 storyboards.

Nina was looking too glamorous - she should look like a NORMAL MOM going
on a casual date night, not a celebrity going to the Oscars.

Regenerates panels 2, 3, and 4 where Nina appears.
"""

import os
import sys
import time
from pathlib import Path

from google import genai
from google.genai import types

# Initialize client
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# Local output directory for generation
OUTPUT_DIR = Path(__file__).parent / "output" / "scene01-nina-fix"

# R2 destination path
R2_DEST = "r2:rex-assets/storyboards/sketchy/scene-01/"

# Sketch style - rough pencil sketch storyboard look
SKETCH_STYLE = """Rough pencil sketch storyboard panel, black and white with minimal shading,
loose gestural pencil lines, animation production thumbnail style,
hand-drawn look with visible sketch construction lines,
professional storyboard artist style like Pixar pre-production thumbnails,
grayscale with cross-hatching for shadows, 16:9 aspect ratio"""

# NINA CHARACTER DESCRIPTION - NORMAL MOM, NOT GLAMOROUS
NINA_DESCRIPTION = """Nina is a NORMAL MOM in her late 30s, NOT a glamorous model:
- Average/normal mom body, warm and approachable
- Shoulder-length brown hair, simple and natural
- Wearing a nice blouse and pants (casual-nice date night outfit, NOT a cocktail dress)
- Kind, warm face with slight tiredness around eyes
- She's going to a nice restaurant, NOT a red carpet event
- Relatable, down-to-earth parent look"""

# GABE CHARACTER DESCRIPTION
GABE_DESCRIPTION = """Gabe is a tired dad in his early 40s:
- Soft around the middle (NOT muscular)
- Wearing a nice button-up shirt and slacks (NOT a tuxedo)
- Glasses
- Slightly rumpled look, tired but trying"""

# Panels to regenerate where Nina appears
NINA_PANELS = [
    {
        "filename": "panel-02-parents-ready.png",
        "prompt": f"""{SKETCH_STYLE},
TRACKING SHOT - mom figure (Nina) walking through house getting ready for date night,
{NINA_DESCRIPTION}
Nina putting on simple earrings while walking, casual nice blouse visible,
motion lines showing she's rushing through the living room,
warm domestic interior with furniture shapes in background,
kids visible on couch in background watching TV,
multitasking mom energy - not glamorous, just a busy parent"""
    },
    {
        "filename": "panel-03-goodbye.png",
        "prompt": f"""{SKETCH_STYLE},
TWO-SHOT MEDIUM - parents saying goodbye to kids before date night,
{NINA_DESCRIPTION}
{GABE_DESCRIPTION}
Nina (mom in casual-nice blouse and pants) leaning toward children on couch,
Gabe (dad in button-up shirt) checking his watch impatiently,
Teen babysitter Jenny in background looking at phone,
Two children on couch - Mia (8yo girl) and Leo (5yo boy in dinosaur pajamas),
Warm domestic scene, parents look like normal exhausted parents going out,
NOT a glamorous couple - just regular tired parents excited for date night"""
    },
    {
        "filename": "panel-04-promise.png",
        "prompt": f"""{SKETCH_STYLE},
CLOSE-UP emotional moment - Gabe hesitating while Nina gives him "the look",
{NINA_DESCRIPTION}
{GABE_DESCRIPTION}
Gabe's face showing conflict/hesitation on making a promise to the kids,
Nina entering frame from left with stern but loving expression,
She's giving him "the look" - don't you dare break this promise to the kids,
Wedding rings visible on their hands emphasizing their partnership,
Intimate family moment, raw emotion, these are REAL PARENTS not movie stars,
Nina looks like a normal mom who means business when it comes to her kids"""
    },
]


def generate_image(prompt: str, filename: str, retry_count: int = 3) -> bool:
    """Generate a single image using Gemini API."""
    output_path = OUTPUT_DIR / filename

    print(f"Generating: {filename}")
    print(f"  Prompt preview: {prompt[:150]}...")

    for attempt in range(retry_count):
        try:
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

            print(f"  ✗ No image in response (attempt {attempt + 1}/{retry_count})")
            if attempt < retry_count - 1:
                time.sleep(10)

        except Exception as e:
            print(f"  ✗ Error (attempt {attempt + 1}/{retry_count}): {e}")
            if attempt < retry_count - 1:
                time.sleep(10)

    return False


def upload_to_r2():
    """Upload generated images to R2."""
    import subprocess

    print("\nUploading to R2...")
    for panel in NINA_PANELS:
        local_path = OUTPUT_DIR / panel["filename"]
        if local_path.exists():
            cmd = f"rclone copy {local_path} {R2_DEST}"
            print(f"  Uploading {panel['filename']}...")
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"    ✓ Uploaded")
            else:
                print(f"    ✗ Failed: {result.stderr}")
        else:
            print(f"  ⊘ Skipping {panel['filename']} (not found)")


def main():
    """Regenerate Scene 1 panels with fixed Nina appearance."""
    print("=" * 70)
    print("Fixing Nina's Appearance in Scene 1 Storyboards")
    print("=" * 70)
    print()
    print("ISSUE: Nina looked like a glamorous model")
    print("FIX: Nina should look like a NORMAL MOM going on a casual date night")
    print()
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"R2 destination: {R2_DEST}")
    print()

    # Check for API key
    if not os.environ.get("GEMINI_API_KEY"):
        print("ERROR: GEMINI_API_KEY environment variable not set")
        return 1

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    success_count = 0
    total = len(NINA_PANELS)

    for i, panel in enumerate(NINA_PANELS, 1):
        print(f"\n[{i}/{total}] ", end="")
        if generate_image(panel["prompt"], panel["filename"]):
            success_count += 1

        # Delay between requests to avoid rate limiting (8+ seconds per CLAUDE.md)
        if i < total:
            print("  Waiting 10 seconds before next request...")
            time.sleep(10)

    print("\n" + "=" * 70)
    print(f"Generation complete: {success_count}/{total} images generated")
    print("=" * 70)

    if success_count == total:
        upload_to_r2()
        print("\n" + "=" * 70)
        print("All panels regenerated and uploaded!")
        print("=" * 70)
        print("\nR2 URLs:")
        base_url = "https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/storyboards/sketchy/scene-01"
        for panel in NINA_PANELS:
            print(f"  {base_url}/{panel['filename']}")
        return 0
    else:
        print("\nSome panels failed to generate. Not uploading to R2.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
