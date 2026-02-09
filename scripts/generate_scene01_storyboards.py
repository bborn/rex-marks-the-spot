#!/usr/bin/env python3
"""
Generate Act 1, Scene 1 storyboard panels using Gemini image generation
with character reference images for consistency.

Uses gemini-3-pro-image-preview with image-to-image approach.
"""

import os
import sys
import time
import subprocess
from pathlib import Path

from google import genai
from google.genai import types
from PIL import Image
import io

# Configuration
MODEL = "gemini-3-pro-image-preview"
FALLBACK_MODEL = "gemini-2.5-flash-image"
DELAY_BETWEEN_REQUESTS = 12  # seconds

SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
CHAR_REF_DIR = PROJECT_DIR / "tmp" / "char-refs"
OUTPUT_DIR = PROJECT_DIR / "tmp" / "scene01-panels"
R2_DEST = "r2:rex-assets/storyboards/act1/scene-01/"
R2_PUBLIC = "https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/storyboards/act1/scene-01"

# Character reference image paths
CHAR_REFS = {
    "mia": CHAR_REF_DIR / "mia_turnaround_APPROVED.png",
    "leo": CHAR_REF_DIR / "leo_turnaround_APPROVED.png",
    "nina": CHAR_REF_DIR / "nina_turnaround_v5.png",
    "gabe": CHAR_REF_DIR / "gabe_turnaround_v4.png",
}

STYLE_SUFFIX = (
    "Professional animation storyboard, black and white pencil sketch, "
    "hand-drawn production board style, Pixar pre-production storyboard, "
    "rough pencil drawing with visible construction lines, "
    "sketchy gestural line work, grayscale on paper texture, "
    "16:9 widescreen aspect ratio"
)

# Panel definitions with character refs needed
PANELS = [
    {
        "id": "01",
        "name": "Panel 1A: Wide Establishing Shot",
        "chars": ["mia", "leo"],
        "prompt": (
            "Wide establishing shot of a cozy family living room. "
            "A 5-year-old boy in green dinosaur pajamas clutching a plush T-Rex sits on the right side of a couch. "
            "An 8-year-old girl with her legs tucked under sits on the left of the couch. "
            "A teen babysitter sits in an armchair to the far right, looking at her phone. "
            "A TV glows on the left. Dinosaur toys scattered on the floor. "
            "Windows show a dark stormy sky with lightning. Warm amber interior lighting. "
            "Parents are visible in the background kitchen area getting ready to leave. "
        ),
    },
    {
        "id": "02",
        "name": "Panel 1B: Medium Shot Leo",
        "chars": ["leo"],
        "prompt": (
            "Medium shot of a 5-year-old boy sitting cross-legged on a couch, center frame. "
            "He wears green dinosaur pajamas and hugs a plush T-Rex toy lovingly. "
            "Several plastic dinosaur toys (T-Rex, Triceratops, pterodactyl) scattered around him. "
            "He watches TV contentedly with a small smile. "
            "Soft warm TV glow illuminates his face. His older sister is partially visible at frame edge. "
        ),
    },
    {
        "id": "03",
        "name": "Panel 1C: Tracking Nina",
        "chars": ["nina"],
        "prompt": (
            "Medium tracking shot of an elegant mother in a black dress, center frame, "
            "walking through the house while putting on earrings. She is multitasking - "
            "checking her purse and looking for her phone while walking gracefully. "
            "She moves from the living room toward the front door area. "
            "Camera motion arrows indicate tracking movement left to right. "
            "Earrings catch the light. Frantic but graceful movement. "
        ),
    },
    {
        "id": "04",
        "name": "Panel 1D: Two-Shot Gabe/Nina",
        "chars": ["gabe", "nina"],
        "prompt": (
            "Two-shot of parents in formal attire, medium shot from waist up. "
            "The father (screen right) wears a slightly rumpled tuxedo and checks his watch impatiently. "
            "He has glasses and is soft around the middle, early 40s. "
            "The mother (screen left) wears a black dress and is composed despite the chaos. "
            "In the background, kids are visible on the couch and a teen babysitter is oblivious on her phone. "
            "Comedy timing moment - the father is frustrated about running late. "
        ),
    },
    {
        "id": "05",
        "name": "Panel 1E: Close-up Jenny",
        "chars": [],
        "prompt": (
            "Close-up of a 15-year-old babysitter with a blonde ponytail, "
            "head tilted down looking at her phone screen. She is completely absorbed in texting. "
            "Phone glow illuminates her face. Cheerful but disconnected expression. "
            "Background is blurred with shallow depth of field. "
            "She is oblivious to the family chaos around her. "
        ),
    },
    {
        "id": "06",
        "name": "Panel 1F: Close-up TV",
        "chars": [],
        "prompt": (
            "Close-up of a TV screen filling most of the frame. "
            "A colorful cartoon is visible but distorted with static interference. "
            "Horizontal scan lines roll through the image. "
            "A brief flash of eerie blue light emanates from the screen - foreshadowing. "
            "Lightning flash is reflected in the screen glass. "
            "The TV flickers and jitters ominously. "
        ),
    },
    {
        "id": "07",
        "name": "Panel 1G: Over-shoulder Kids",
        "chars": ["mia", "leo"],
        "prompt": (
            "Over-the-shoulder shot from behind two children on a couch. "
            "Camera looks past the kids toward the TV and their parents in the background. "
            "On the left, the back of an 8-year-old girl's head is visible (she looks concerned). "
            "On the right, a 5-year-old boy in dinosaur pajamas. "
            "The parents are visible in the background still preparing to leave in formal attire. "
            "Kids' silhouettes against the TV glow. Contrast between children's calm and parents' rushed chaos. "
        ),
    },
    {
        "id": "08",
        "name": "Panel 1H: Close-up Mia",
        "chars": ["mia"],
        "prompt": (
            "Close-up of an 8-year-old girl's face, emotional and earnest. "
            "She looks up at her parents who are off-screen. Big expressive eyes full of concern. "
            "She is asking 'Promise?' - need for reassurance before her parents leave. "
            "The TV flickers in the reflection of her eyes. "
            "A flash of lightning briefly illuminates her face. "
            "Warm but vulnerable expression. Slow camera push indicated with arrow. "
            "This is the emotional anchor of the scene. "
        ),
    },
    {
        "id": "09",
        "name": "Panel 1I: Close-up Gabe Hesitates",
        "chars": ["gabe", "nina"],
        "prompt": (
            "Starting as close-up of a father's face showing internal conflict and hesitation. "
            "He wears glasses and has a soft face, early 40s. He is uncomfortable making a promise. "
            "The shot pulls back to reveal his wife glaring at him from the left side of frame - "
            "a 'don't you dare' expression. "
            "He finally relents and says 'Promise.' Tension then release. "
            "Camera pull-back arrows indicate widening from close-up to two-shot. "
        ),
    },
]


def image_to_part(img_path):
    """Convert an image file to a genai Part."""
    img = Image.open(img_path)
    # Resize if too large (max 4MP for Gemini)
    max_dim = 2048
    if max(img.size) > max_dim:
        ratio = max_dim / max(img.size)
        new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
        img = img.resize(new_size, Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    data = buf.getvalue()
    return types.Part.from_bytes(data=data, mime_type='image/png')


def generate_panel(panel, client, model_name):
    """Generate a single storyboard panel."""
    panel_id = panel["id"]
    panel_name = panel["name"]
    filename = f"scene-01-panel-{panel_id}.png"
    output_path = OUTPUT_DIR / filename

    print(f"\n{'='*60}")
    print(f"Generating {panel_name}")
    print(f"  File: {filename}")
    print(f"  Characters: {panel['chars'] or ['none']}")

    # Load character reference image parts
    ref_parts = []
    for name in panel["chars"]:
        path = CHAR_REFS.get(name)
        if path and path.exists():
            ref_parts.append(image_to_part(path))
            print(f"  Loaded ref: {name}")
        else:
            print(f"  WARNING: Missing ref for {name}")

    # Build the prompt
    full_prompt = panel["prompt"] + STYLE_SUFFIX

    # Build content: reference images first, then prompt
    if ref_parts:
        ref_note = (
            "Use these character reference sheets to maintain consistent character designs. "
            "Draw these exact characters in the scene described below:\n\n"
        )
        content_parts = ref_parts + [types.Part.from_text(text=ref_note + full_prompt)]
    else:
        content_parts = [types.Part.from_text(text=f"Generate an image: {full_prompt}")]

    try:
        response = client.models.generate_content(
            model=model_name,
            contents=content_parts,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
            ),
        )

        if hasattr(response, "candidates") and response.candidates:
            for part in response.candidates[0].content.parts:
                if part.inline_data is not None:
                    img_bytes = part.inline_data.data
                    with open(output_path, "wb") as f:
                        f.write(img_bytes)
                    size_kb = len(img_bytes) / 1024
                    print(f"  SUCCESS: Saved {filename} ({size_kb:.0f} KB)")
                    return output_path
                elif part.text:
                    print(f"  Text response: {part.text[:200]}")

        print(f"  FAILED: No image data in response")
        return None

    except Exception as e:
        print(f"  ERROR: {e}")
        return None


def upload_to_r2(local_path):
    """Upload a single file to R2."""
    try:
        result = subprocess.run(
            ["rclone", "copy", str(local_path), R2_DEST],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode == 0:
            url = f"{R2_PUBLIC}/{local_path.name}"
            print(f"  Uploaded: {url}")
            return url
        else:
            print(f"  Upload error: {result.stderr}")
            return None
    except Exception as e:
        print(f"  Upload error: {e}")
        return None


def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY not set")
        sys.exit(1)

    # Verify character refs exist
    print("Checking character references...")
    for name, path in CHAR_REFS.items():
        if path.exists():
            print(f"  {name}: OK ({path.name})")
        else:
            print(f"  {name}: MISSING ({path})")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Initialize client
    client = genai.Client(api_key=api_key)
    model_name = MODEL
    print(f"\nUsing model: {model_name}")

    # Generate panels
    results = {}
    total = len(PANELS)

    for i, panel in enumerate(PANELS):
        panel_id = panel["id"]

        result_path = generate_panel(panel, client, model_name)

        if result_path is None and model_name == MODEL:
            # Try fallback model
            print(f"  Retrying with fallback model: {FALLBACK_MODEL}")
            fallback_path = generate_panel(panel, client, FALLBACK_MODEL)
            if fallback_path:
                result_path = fallback_path
                # Switch to fallback for remaining panels
                model_name = FALLBACK_MODEL
                print(f"  Switched to fallback model for remaining panels")

        results[panel_id] = result_path

        # Rate limiting
        if i < total - 1:
            print(f"\n  Waiting {DELAY_BETWEEN_REQUESTS}s for rate limit...")
            time.sleep(DELAY_BETWEEN_REQUESTS)

    # Upload successful panels
    print(f"\n{'='*60}")
    print("Uploading to R2...")
    urls = {}
    for panel_id, path in results.items():
        if path and path.exists():
            url = upload_to_r2(path)
            if url:
                urls[panel_id] = url

    # Summary
    print(f"\n{'='*60}")
    print(f"SUMMARY: {len(urls)}/{total} panels generated and uploaded")
    print(f"{'='*60}")
    for panel_id, url in sorted(urls.items()):
        print(f"  Panel {panel_id}: {url}")

    failed = [p["id"] for p in PANELS if p["id"] not in urls]
    if failed:
        print(f"\n  FAILED panels: {', '.join(failed)}")

    return 0 if len(urls) == total else 1


if __name__ == "__main__":
    sys.exit(main())
