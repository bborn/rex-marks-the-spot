#!/usr/bin/env python3
"""Fix Scene 1 sketchy storyboards - correct the errors.

Issues being fixed:
1. Panel 1 showed 3 kids - should be only 2 (Mia age 8, Leo age 5)
2. Panel 2 showed muscular dad - Gabe should be soft/tired parent
3. Panel 4 showed Ruben - he doesn't appear until Scene 20!
"""

import os
import sys
import time
from pathlib import Path

from google import genai
from google.genai import types

# Initialize client
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# Output directory
OUTPUT_DIR = Path("/tmp/scene01-fixed")

# Character descriptions for consistency
CHARACTERS = {
    "gabe": "tired-looking dad in his early 40s with glasses, soft around the middle (NOT muscular), wearing a tuxedo, slightly rumpled, checking his watch anxiously",
    "nina": "elegant mom in her 30s wearing a black formal dress, putting on earrings, multitasking",
    "mia": "8-year-old girl with concerned expression, sitting on couch, big expressive eyes",
    "leo": "5-year-old boy in green dinosaur pajamas, clutching a plush T-Rex toy, sitting on couch",
    "jenny": "15-year-old babysitter with blonde ponytail, sitting in armchair absorbed in her phone",
}

# Fixed panels for Scene 1
FIXED_PANELS = [
    {
        "filename": "panel-01-establishing.png",
        "prompt": f"""Traditional animation storyboard sketch, rough pencil drawing style.
Wide establishing shot of cozy family living room.

EXACTLY TWO CHILDREN on the couch - no more, no less:
- {CHARACTERS['leo']}
- {CHARACTERS['mia']}

{CHARACTERS['jenny']} sits in armchair to the side.
{CHARACTERS['gabe']} and {CHARACTERS['nina']} visible moving in background kitchen area.

Setting: Warm domestic interior, TV on showing cartoons, dinosaur toys scattered on floor,
storm visible through window with lightning, cozy but cluttered family home.

Style: Pixar pre-production storyboard, loose gestural pencil sketch,
visible pencil strokes, grayscale with slight sepia tint, 16:9 aspect ratio.
NOT polished final art - rough working drawing."""
    },
    {
        "filename": "panel-02-parents-ready.png",
        "prompt": f"""Traditional animation storyboard sketch, rough pencil drawing style.
Two-shot of married couple preparing to leave for fancy event.

{CHARACTERS['gabe']} - IMPORTANT: he should have a normal "dad bod", NOT fit or muscular.
Average build, slightly soft/pudgy around middle. Tired posture. Checking watch impatiently.

{CHARACTERS['nina']} - putting on earrings while still talking, graceful despite chaos.

Background: Two children (ONLY TWO - boy 5 and girl 8) visible on couch, babysitter on phone.

Style: Pixar pre-production storyboard, loose pencil sketch with visible construction lines,
grayscale pencil on paper texture, 16:9 aspect ratio."""
    },
    {
        "filename": "panel-03-goodbye.png",
        "prompt": f"""Traditional animation storyboard sketch, rough pencil drawing style.
Emotional moment - kids saying goodbye to parents.

Foreground: {CHARACTERS['mia']} looking up with worried expression, asking parents to promise.
Next to her: {CHARACTERS['leo']} hugging his dinosaur toy.

ONLY these two children - no other kids.

Background: Parents in doorway about to leave, Nina looking back warmly,
Gabe (soft build, NOT muscular) already half out the door.

Style: Pixar pre-production storyboard, emotional close framing on kids,
loose pencil sketch, grayscale with slight warmth, 16:9 aspect ratio."""
    },
    {
        "filename": "panel-04-promise.png",
        "prompt": f"""Traditional animation storyboard sketch, rough pencil drawing style.
Close-up of Gabe's face - the "Promise?" moment.

{CHARACTERS['gabe']} - close-up showing internal conflict.
Tired eyes behind glasses, torn between leaving and staying.
Soft jawline, NOT chiseled or muscular face. Normal dad face, early 40s.
Wearing tuxedo with bowtie slightly askew.

In small insert panel or background: Nina's sharp look that says "don't you dare not promise".

NO FAIRIES, NO MAGIC, NO RUBEN - this is a simple domestic scene.
Just a dad being asked to promise he'll come home.

Style: Pixar pre-production storyboard, emotional acting sketch,
loose pencil lines, grayscale, 16:9 aspect ratio."""
    },
]


def generate_image(prompt: str, filename: str) -> bool:
    """Generate a single sketch image using Gemini 2.0 Flash."""
    output_path = OUTPUT_DIR / filename

    print(f"Generating: {filename}")
    print(f"  Prompt preview: {prompt[:100]}...")

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp-image-generation",
            contents=f"Generate an image: {prompt}",
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
            ),
        )

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
    """Generate fixed Scene 1 storyboard panels."""
    print("=" * 60)
    print("Fixing Scene 1 Sketchy Storyboards")
    print("=" * 60)
    print("\nIssues being fixed:")
    print("  1. Panel 1: Had 3 kids, should be 2 (Mia & Leo only)")
    print("  2. Panel 2: Gabe was too muscular, should be soft/tired dad")
    print("  3. Panel 4: Had Ruben - he's NOT in Scene 1!")
    print(f"\nOutput: {OUTPUT_DIR}")
    print()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    success_count = 0
    total = len(FIXED_PANELS)

    for i, panel in enumerate(FIXED_PANELS, 1):
        print(f"\n[{i}/{total}] ", end="")
        if generate_image(panel["prompt"], panel["filename"]):
            success_count += 1

        # Delay between requests (Gemini rate limits)
        if i < total:
            print("  Waiting 10s for rate limit...")
            time.sleep(10)

    print("\n" + "=" * 60)
    print(f"Complete: {success_count}/{total} images generated")
    print("=" * 60)

    if success_count == total:
        print("\nNext steps:")
        print(f"  1. Review images in {OUTPUT_DIR}")
        print("  2. Upload to R2: rclone copy /tmp/scene01-fixed/ r2:rex-assets/storyboards/sketchy/scene-01/")
        print("  3. Delete old panel-04-ruben-appears.png from R2")

    return 0 if success_count == total else 1


if __name__ == "__main__":
    sys.exit(main())
