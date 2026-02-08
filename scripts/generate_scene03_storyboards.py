#!/usr/bin/env python3
"""Generate Act 1, Scene 3 storyboard panels using Gemini with character reference images."""

import os
import sys
import time
import subprocess
from pathlib import Path

from google import genai
from google.genai import types
from PIL import Image

# Initialize client
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# Models
PRIMARY_MODEL = "gemini-3-pro-image-preview"
FALLBACK_MODEL = "gemini-2.5-flash-image"

# Paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
CHAR_REFS_DIR = PROJECT_DIR / "tmp" / "char-refs"
OUTPUT_DIR = PROJECT_DIR / "tmp" / "scene-03-panels"
R2_DEST = "r2:rex-assets/storyboards/act1/scene-03/"
R2_PUBLIC_BASE = "https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/storyboards/act1/scene-03"

# Character reference images
GABE_REF = CHAR_REFS_DIR / "gabe_turnaround_APPROVED.png"
NINA_REF = CHAR_REFS_DIR / "nina_turnaround_APPROVED.png"

# Style preamble for all panels
STYLE_PREFIX = """Black and white pencil sketch storyboard panel. Hand-drawn production board quality
with visible pencil strokes and light cross-hatching shading. Pixar pre-production storyboard style.
Rough gestural drawing, NOT polished final art. 16:9 cinematic aspect ratio.
The characters must match the reference images provided - use them for face, hair, body proportions, and overall look."""

# Panel definitions based on scene-03-car-night.md
PANELS = [
    {
        "filename": "scene-03-panel-01.png",
        "label": "Panel 3A: Two-Shot - Driving",
        "char_refs": ["gabe", "nina"],
        "prompt": f"""{STYLE_PREFIX}

SCENE: Interior of a car at night during heavy rain. Two-shot from dashboard perspective.

COMPOSITION: Gabe (the husband from reference image 1) is driving on the left side of frame,
hands on steering wheel, eyes focused on road, tense body language. Nina (the wife from reference image 2)
is in the passenger seat on the right, searching through her purse and the car console, frustrated.

DETAILS:
- Rain streaking across the windshield between them
- Windshield wipers visible, clearing view rhythmically
- Dashboard instruments casting warm glow on their faces
- Occasional lightning flash illuminating the car interior
- Dark stormy night visible through windows
- Gabe wearing formal suit/jacket (date night attire)
- Nina in elegant black dress

DIALOGUE NOTE: Nina says "Ugh. It's not in here."

MOOD: Tense, intimate enclosed space, rain creating visual texture on glass."""
    },
    {
        "filename": "scene-03-panel-02.png",
        "label": "Panel 3B: Insert - Phone Screen",
        "char_refs": ["nina"],
        "prompt": f"""{STYLE_PREFIX}

SCENE: Close-up insert shot of a smartphone screen in a dark car interior.

COMPOSITION: A smartphone held in Nina's hand (the woman from the reference image),
screen showing an outgoing call to "Nina Cell". The phone is bright against the dark car interior.

DETAILS:
- Phone screen is the brightest element, glowing in dark car
- "Calling Nina Cell" text visible on screen
- Ringing/calling indicator animation shown
- Nina's fingers (elegant, with a ring visible) holding the phone
- Dark car interior surrounds the bright screen
- Subtle rain shadows on her hand from the window

MOOD: Tension building, the search continues, intimate technology moment."""
    },
    {
        "filename": "scene-03-panel-03.png",
        "label": "Panel 3C: POV - Windshield View",
        "char_refs": [],
        "prompt": f"""{STYLE_PREFIX}

SCENE: POV (point of view) shot through the car windshield. Driver's perspective of the road ahead.

COMPOSITION: Looking through the rain-soaked windshield. The road ahead is barely visible
through the heavy downpour. No characters visible - this is a pure POV shot.

DETAILS:
- Heavy rain obscuring nearly all visibility
- Windshield wipers mid-sweep, struggling to keep up
- Headlight beams catching the rain, creating streaks of light
- Lightning flash revealing an empty, dark road ahead
- Silhouettes of trees on either side of the road
- Ominous darkness beyond the headlights
- The feeling that something could appear at any moment
- Road lines barely visible through the deluge

MOOD: Building dread, isolation, the storm as metaphor, tension before something happens."""
    },
    {
        "filename": "scene-03-panel-04.png",
        "label": "Panel 3D: Close-up - Nina",
        "char_refs": ["nina"],
        "prompt": f"""{STYLE_PREFIX}

SCENE: Close-up of Nina (the woman from the reference image) in the car passenger seat.
Profile or three-quarter view, emotional character moment.

COMPOSITION: Nina's face fills most of the frame. She is looking toward Gabe (off-screen left),
delivering an important line. Phone partially visible in her hand at the bottom of frame.

DETAILS:
- Concern and seriousness on her face - this is an important conversation
- Warm dashboard glow illuminating her features from below
- Rain shadows moving across her face from the window
- Lightning briefly illuminating her face with a flash
- Dark brown wavy hair (matching reference), slightly dressed up for date night
- Elegant earrings visible
- Her expression shows she cares deeply about what she's saying

DIALOGUE: Nina says "You need to be nicer to her." (referring to their daughter Mia)

MOOD: Emotional intimacy, parental concern, planting the seed for Gabe's character arc.
This is the key emotional beat of the scene."""
    },
]


def generate_panel(panel: dict, model_name: str, retry_count: int = 2) -> bool:
    """Generate a single storyboard panel with character reference images."""
    output_path = OUTPUT_DIR / panel["filename"]
    label = panel["label"]

    print(f"\n{'='*60}")
    print(f"Generating: {label}")
    print(f"  File: {panel['filename']}")
    print(f"  Model: {model_name}")
    print(f"  Character refs: {panel['char_refs'] or 'none'}")

    # Build contents list: reference images + prompt
    contents = []

    for char in panel["char_refs"]:
        ref_path = GABE_REF if char == "gabe" else NINA_REF
        if ref_path.exists():
            img = Image.open(ref_path)
            contents.append(img)
            print(f"  Added ref: {ref_path.name} ({img.size})")
        else:
            print(f"  WARNING: Reference not found: {ref_path}")

    contents.append(panel["prompt"])

    for attempt in range(retry_count):
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=contents,
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE", "TEXT"],
                ),
            )

            # Extract image from response
            if response.candidates:
                for part in response.candidates[0].content.parts:
                    if part.inline_data is not None:
                        image_data = part.inline_data.data
                        with open(output_path, "wb") as f:
                            f.write(image_data)
                        size_kb = len(image_data) / 1024
                        print(f"  SUCCESS: Saved {output_path.name} ({size_kb:.0f} KB)")
                        return True

            print(f"  No image in response (attempt {attempt + 1}/{retry_count})")
            if attempt < retry_count - 1:
                time.sleep(10)

        except Exception as e:
            error_msg = str(e)
            print(f"  Error (attempt {attempt + 1}/{retry_count}): {error_msg}")
            if attempt < retry_count - 1:
                time.sleep(10)

    return False


def upload_to_r2(output_dir: Path) -> list[str]:
    """Upload all generated panels to R2."""
    print(f"\n{'='*60}")
    print(f"Uploading to R2: {R2_DEST}")

    urls = []
    for png in sorted(output_dir.glob("scene-03-panel-*.png")):
        try:
            result = subprocess.run(
                ["rclone", "copy", str(png), R2_DEST],
                capture_output=True,
                text=True,
                timeout=60,
            )
            if result.returncode == 0:
                url = f"{R2_PUBLIC_BASE}/{png.name}"
                urls.append(url)
                print(f"  Uploaded: {url}")
            else:
                print(f"  FAILED: {png.name} - {result.stderr}")
        except Exception as e:
            print(f"  ERROR: {png.name} - {e}")

    return urls


def main():
    """Generate Scene 3 storyboard panels."""
    print("=" * 60)
    print("Act 1, Scene 3: INT. CAR - NIGHT")
    print("Generating 4 Storyboard Panels")
    print("=" * 60)

    # Check prerequisites
    if not os.environ.get("GEMINI_API_KEY"):
        print("ERROR: GEMINI_API_KEY not set")
        return 1

    if not GABE_REF.exists() or not NINA_REF.exists():
        print("ERROR: Character reference images not found in tmp/char-refs/")
        print(f"  Gabe: {GABE_REF} {'EXISTS' if GABE_REF.exists() else 'MISSING'}")
        print(f"  Nina: {NINA_REF} {'EXISTS' if NINA_REF.exists() else 'MISSING'}")
        return 1

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Generate panels
    model = PRIMARY_MODEL
    success_count = 0
    total = len(PANELS)

    for i, panel in enumerate(PANELS):
        success = generate_panel(panel, model)

        if not success and model == PRIMARY_MODEL:
            print(f"\n  Retrying with fallback model: {FALLBACK_MODEL}")
            model = FALLBACK_MODEL
            success = generate_panel(panel, model)

        if success:
            success_count += 1
        else:
            print(f"  FAILED: Could not generate {panel['filename']}")

        # Rate limiting delay between generations
        if i < total - 1:
            delay = 12
            print(f"\n  Waiting {delay}s for rate limiting...")
            time.sleep(delay)

    print(f"\n{'='*60}")
    print(f"Generation complete: {success_count}/{total} panels")

    if success_count == 0:
        print("No panels generated. Exiting.")
        return 1

    # Upload to R2
    urls = upload_to_r2(OUTPUT_DIR)

    print(f"\n{'='*60}")
    print(f"RESULTS: {len(urls)}/{total} panels uploaded to R2")
    for url in urls:
        print(f"  {url}")
    print("=" * 60)

    return 0 if success_count == total else 1


if __name__ == "__main__":
    sys.exit(main())
