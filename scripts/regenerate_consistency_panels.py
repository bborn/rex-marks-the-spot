#!/usr/bin/env python3
"""Regenerate off-model storyboard panels for Act 1 Scenes 2-4.

Uses approved character turnarounds as image references with Gemini
to ensure character consistency across panels.

Panels to regenerate (failed consistency audit):
- Scene 2 Panel 2: Parents rushing to car (was 3 people, off-model)
- Scene 3 Panel 1: Two-shot driving (both characters off-model)
- Scene 3 Panel 4: Close-up Nina (off-model)
- Scene 4 Panel 1: Living room wide (too many kids, all off-model)
- Scene 4 Panel 2: Jenny texting (off-model)
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

# Directories
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
OUTPUT_DIR = PROJECT_DIR / "tmp" / "regenerated"
TURNAROUND_DIR = PROJECT_DIR / "tmp" / "turnarounds"

# Model - prefer gemini-3-pro-image-preview per CLAUDE.md
MODEL = "gemini-2.0-flash-exp-image-generation"

# Pixar-style rendered panel prefix (NOT sketch - fully rendered for character lock)
RENDER_STYLE = """Pixar-style 3D animated movie storyboard panel, fully rendered,
cinematic lighting, rich color palette, professional animation quality,
16:9 widescreen aspect ratio, high quality CG animation look"""


def load_image_as_part(image_path: str) -> types.Part:
    """Load an image file and return as a Gemini Part."""
    with open(image_path, "rb") as f:
        image_data = f.read()
    return types.Part.from_bytes(data=image_data, mime_type="image/png")


def generate_panel_with_refs(
    prompt: str,
    filename: str,
    reference_images: list[tuple[str, str]],
    max_retries: int = 2,
) -> bool:
    """Generate a panel using character turnaround references.

    Args:
        prompt: The text prompt for the panel
        filename: Output filename
        reference_images: List of (image_path, description) tuples
        max_retries: Number of retries on failure
    """
    output_path = OUTPUT_DIR / filename
    print(f"\nGenerating: {filename}")
    print(f"  References: {', '.join(desc for _, desc in reference_images)}")
    print(f"  Prompt: {prompt[:100]}...")

    # Build the content parts: reference images first, then prompt
    contents = []

    for img_path, desc in reference_images:
        full_path = TURNAROUND_DIR / img_path
        if not full_path.exists():
            print(f"  WARNING: Reference image not found: {full_path}")
            continue
        contents.append(load_image_as_part(str(full_path)))
        contents.append(f"[CHARACTER REFERENCE: {desc}]")

    contents.append(
        f"Using the character reference images above for exact character appearance, "
        f"generate this storyboard panel:\n\n{prompt}"
    )

    for attempt in range(max_retries + 1):
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=contents,
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE", "TEXT"],
                ),
            )

            for part in response.candidates[0].content.parts:
                if part.inline_data is not None:
                    image_data = part.inline_data.data
                    with open(output_path, "wb") as f:
                        f.write(image_data)
                    print(f"  OK Saved to {output_path} ({len(image_data)} bytes)")
                    return True

            print(f"  No image in response (attempt {attempt + 1})")
            if attempt < max_retries:
                time.sleep(10)

        except Exception as e:
            print(f"  Error (attempt {attempt + 1}): {e}")
            if attempt < max_retries:
                time.sleep(15)

    print(f"  FAILED after {max_retries + 1} attempts")
    return False


# Panels to regenerate with character references and detailed prompts
PANELS_TO_REGENERATE = [
    {
        "filename": "scene-02-panel-02.png",
        "references": [
            ("gabe_turnaround_APPROVED.png", "Gabe - father, early 40s, glasses, brown hair, soft build. In this scene wearing BLACK TIE formal suit."),
            ("nina_turnaround_APPROVED.png", "Nina - mother, auburn/red wavy hair, green eyes. In this scene wearing elegant BLACK DRESS for formal event."),
        ],
        "prompt": f"""{RENDER_STYLE},
TRACKING SHOT - Gabe and Nina rushing from front door to car in heavy rain at night.
ONLY TWO PEOPLE in frame - Gabe (father with glasses, brown hair, wearing black formal suit)
and Nina (mother with auburn wavy hair, wearing elegant black dress).
Gabe leading the way, Nina holding her clutch purse over her head to shield from rain.
Rain soaking their formal attire, puddles splashing underfoot.
Car headlights illuminating them from right side of frame.
Dark stormy night, house door still open behind them with warm light spilling out.
Urgent rushing energy, cinematic rain effects, dramatic lighting from lightning and headlights."""
    },
    {
        "filename": "scene-03-panel-01.png",
        "references": [
            ("gabe_turnaround_APPROVED.png", "Gabe - father, early 40s, brown hair, GLASSES (important!), soft/slightly stocky build. Here in black formal suit driving."),
            ("nina_turnaround_APPROVED.png", "Nina - mother, auburn/red wavy shoulder-length hair, green eyes, fair skin with freckles. Here in elegant black dress, passenger seat."),
        ],
        "prompt": f"""{RENDER_STYLE},
STANDARD TWO-SHOT - Car interior at night, shot from behind dashboard looking at both front seats.
Gabe DRIVING on LEFT - he MUST have glasses, brown hair, slightly stocky build, wearing black suit.
Nina in PASSENGER SEAT on RIGHT - she has auburn/red wavy hair, green eyes, wearing black dress.
Gabe's hands on steering wheel, tense focused expression, looking at road.
Nina in passenger seat, looking through purse, slightly frustrated expression.
Windshield showing heavy rain, occasional lightning flash through glass.
Dashboard glow casting warm light on their faces. Dark exterior through windows.
Wipers visible on windshield. Intimate but tense couple in enclosed car space."""
    },
    {
        "filename": "scene-03-panel-04.png",
        "references": [
            ("nina_turnaround_APPROVED.png", "Nina - mother, auburn/red wavy shoulder-length hair, green eyes, fair skin with light freckles. Here wearing elegant black dress."),
        ],
        "prompt": f"""{RENDER_STYLE},
CLOSE-UP PROFILE SHOT - Nina's face in the car passenger seat at night.
Nina has AUBURN/RED WAVY SHOULDER-LENGTH HAIR, green eyes, fair skin with light freckles.
She is wearing an elegant black dress (formal event attire).
Shot in profile or 3/4 view, looking slightly concerned/thoughtful.
Warm dashboard glow illuminating her face from below.
Occasional lightning flash creating dramatic light through rain-streaked window behind her.
Rain shadow patterns playing across her face.
Emotional moment - she's talking about her daughter, concern visible in her expression.
Dark car interior, moody cinematic lighting, intimate character moment."""
    },
    {
        "filename": "scene-04-panel-01.png",
        "references": [
            ("jenny_turnaround_APPROVED.png", "Jenny - teenage babysitter, 15 years old, dark brown hair in ponytail, darker skin, coral/salmon zip hoodie, dark leggings, white sneakers, always on phone."),
            ("mia_turnaround_APPROVED.png", "Mia - 8-year-old daughter, dark curly hair with pink hair tie/ponytail, darker skin, pink polka-dot top, jeans, red sneakers."),
            ("leo_turnaround_APPROVED.png", "Leo - 5-year-old son, blonde curly hair, blue eyes, green t-shirt, khaki shorts, red sneakers, carries green dinosaur toy."),
        ],
        "prompt": f"""{RENDER_STYLE},
WIDE SHOT - Cozy living room at night, warm amber lighting.
EXACTLY THREE young people in the room - no more, no less:
1. Leo (5yo boy, blonde curly hair, green shirt, khaki shorts) sprawled on couch with toy dinosaur
2. Mia (8yo girl, dark curly hair with ponytail, pink top) sitting properly on couch watching TV
3. Jenny (15yo teen, dark hair in ponytail, coral hoodie, dark leggings) sitting in armchair absorbed in phone

TV on left side glowing, cozy blankets on couch, toys scattered on floor.
Storm visible but muted through curtained windows in background.
Warm domestic scene, peaceful and calm. No adults present.
The kids are comfortable and safe while parents are out.
Amber table lamp glow, TV screen light, overall cozy family home feeling."""
    },
    {
        "filename": "scene-04-panel-02.png",
        "references": [
            ("jenny_turnaround_APPROVED.png", "Jenny - teenage babysitter, 15 years old, dark brown hair in ponytail, DARKER SKIN, coral/salmon zip-up hoodie, holding phone."),
        ],
        "prompt": f"""{RENDER_STYLE},
CLOSE-UP INSERT SHOT - Jenny's hands and phone, with her face partially visible above (chin/mouth area).
Jenny has DARK BROWN HAIR, DARKER SKIN, wearing CORAL/SALMON ZIP HOODIE.
She is completely absorbed in texting on her phone.
Phone screen showing text message conversation (generic chat bubbles).
Her expression (visible lower face) shows she's smiling/engaged with texts, oblivious to surroundings.
Background softly blurred - warm living room colors out of focus.
Comedic moment - she's supposed to be babysitting but is totally on her phone.
Warm ambient lighting, phone screen glow on her face."""
    },
]


def main():
    """Regenerate off-model panels with character references."""
    print("=" * 60)
    print("Act 1 Scenes 2-4 Consistency Regeneration")
    print("=" * 60)
    print(f"Model: {MODEL}")
    print(f"Output: {OUTPUT_DIR}")
    print(f"Turnarounds: {TURNAROUND_DIR}")
    print(f"Panels to regenerate: {len(PANELS_TO_REGENERATE)}")
    print()

    # Verify turnarounds exist
    for panel in PANELS_TO_REGENERATE:
        for img_path, _ in panel["references"]:
            full_path = TURNAROUND_DIR / img_path
            if not full_path.exists():
                print(f"ERROR: Missing turnaround: {full_path}")
                return 1

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    success_count = 0
    total = len(PANELS_TO_REGENERATE)

    for i, panel in enumerate(PANELS_TO_REGENERATE, 1):
        print(f"\n{'='*40}")
        print(f"[{i}/{total}] {panel['filename']}")
        print(f"{'='*40}")

        if generate_panel_with_refs(
            panel["prompt"],
            panel["filename"],
            panel["references"],
        ):
            success_count += 1

        # Delay between requests for rate limiting
        if i < total:
            delay = 10
            print(f"  Waiting {delay}s for rate limit...")
            time.sleep(delay)

    print(f"\n{'='*60}")
    print(f"Complete: {success_count}/{total} panels regenerated")
    print(f"{'='*60}")

    return 0 if success_count == total else 1


if __name__ == "__main__":
    sys.exit(main())
