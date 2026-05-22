#!/usr/bin/env python3
"""Fix remaining Scene 1 v2 storyboard panels.

Issues to fix:
- Panel 01 end: Lightning flash too extreme (white-out)
- Panel 02 start: Leo missing (empty room)
- Panel 02 end: Wrong composition (random close-up)
- Panel 03 end: Nina in wrong outfit (burgundy instead of black)
- Panel 04 end: Nina disappeared (only Gabe visible)
- Panel 05 start+end: Wrong room (fireplace room instead of living room)
- Panel 07 end: Three kids instead of two
"""

import os
import sys
import time
import subprocess
import io
from pathlib import Path

from google import genai
from google.genai import types
from PIL import Image

# Configuration
MODEL = "gemini-2.5-flash-image"
DELAY_BETWEEN_REQUESTS = 10

CHAR_REF_DIR = Path("/tmp/char-refs")
ENV_REF_PATH = Path.home() / "rex-marks-the-spot" / "assets" / "storyboards" / "v2" / "scene-01" / "scene-01-panel-01-start.png"
OUTPUT_DIR = Path.home() / "rex-marks-the-spot" / "assets" / "storyboards" / "v2" / "scene-01"
R2_DEST = "r2:rex-assets/storyboards/v2/scene-01/"
R2_PUBLIC = "https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/storyboards/v2/scene-01"

# Character references
CHAR_REFS = {
    "mia": CHAR_REF_DIR / "mia_turnaround_APPROVED_ALT.png",
    "leo": CHAR_REF_DIR / "leo_turnaround_APPROVED.png",
    "nina": CHAR_REF_DIR / "nina_turnaround_APPROVED.png",
    "gabe": CHAR_REF_DIR / "gabe_turnaround_APPROVED.png",
    "jenny": CHAR_REF_DIR / "jenny_turnaround_APPROVED.png",
}

NO_TEXT = "Do NOT render any text, words, letters, or dialogue into the image. Do NOT add any UI elements or subtitles."

STYLE = (
    "Pixar-style 3D animated render, rich warm cinematic lighting, "
    "detailed textures, soft ambient occlusion, subsurface scattering on skin, "
    "professional animation quality, movie production still, "
    "16:9 widescreen aspect ratio."
)

PANELS = [
    {
        "filename": "scene-01-panel-01-end.png",
        "chars": ["mia", "leo"],
        "prompt": (
            "Same cozy family living room as the reference image. "
            "A flash of lightning visible OUTSIDE the window illuminating the storm clouds. "
            "The room is slightly brighter from the flash but the room itself is NOT washed out or overexposed. "
            "The living room interior is still clearly visible with all furniture and details. "
            "TV shows minor static flicker. "
            "Two children on the couch - an 8-year-old girl with dark wavy hair (Mia) and "
            "a 5-year-old boy in green dinosaur pajamas clutching a plush T-Rex (Leo). "
            "A teenage babysitter with blonde ponytail in an armchair looking at her phone. "
            "The lightning is SUBTLE - just a bright flash through the window, not an explosion of white light. "
            f"{NO_TEXT} {STYLE}"
        ),
    },
    {
        "filename": "scene-01-panel-02-start.png",
        "chars": ["leo"],
        "prompt": (
            "Medium shot of a 5-year-old boy sitting on a cozy living room couch. "
            "Medium shot, the boy fills the center of the frame from waist up. "
            "He is the main subject and is PROMINENT in the frame. "
            "He has blonde curly hair and wears green dinosaur pajamas. "
            "He hugs a plush T-Rex toy against his chest. "
            "TV glow illuminates his face from the side with a warm blue-white light. "
            "He has a content, relaxed expression watching TV. "
            "The couch and some living room background visible behind him, "
            "matching the reference environment image. "
            "Small dinosaur toys scattered on the couch cushions beside him. "
            f"{NO_TEXT} {STYLE}"
        ),
    },
    {
        "filename": "scene-01-panel-02-end.png",
        "chars": ["leo"],
        "prompt": (
            "Medium shot of a 5-year-old boy sitting on a cozy living room couch. "
            "Same composition and camera distance as a medium shot - the boy fills the center of the frame from waist up. "
            "He has blonde curly hair and wears green dinosaur pajamas. "
            "He holds a plush T-Rex in one arm. "
            "He glances down at small dinosaur toys beside him on the couch with a slight smile. "
            "Same living room background as the reference environment image. "
            "Warm TV glow on his face. "
            f"{NO_TEXT} {STYLE}"
        ),
    },
    {
        "filename": "scene-01-panel-03-end.png",
        "chars": ["nina"],
        "prompt": (
            "Medium shot of an elegant woman (Nina) near the front door of the living room, checking her purse. "
            "Nina wears an ELEGANT BLACK COCKTAIL DRESS. The dress is BLACK. NOT burgundy, NOT maroon, NOT red. "
            "She has auburn/reddish-brown shoulder-length wavy hair. "
            "She is multitasking - checking items in her purse before leaving for a date night. "
            "The living room from the reference image is visible in the background. "
            "Warm interior lighting. She looks graceful but slightly hurried. "
            f"{NO_TEXT} {STYLE}"
        ),
    },
    {
        "filename": "scene-01-panel-04-end.png",
        "chars": ["gabe", "nina"],
        "prompt": (
            "Two-shot showing BOTH Gabe and Nina together in the same frame. "
            "Both characters must be clearly visible in the image. "
            "Gabe (man with glasses, soft build, wearing a tuxedo) is gesturing urgently, checking his watch. "
            "Nina (elegant woman with auburn wavy hair, wearing an ELEGANT BLACK COCKTAIL DRESS) "
            "stands beside him looking calm and composed. "
            "They are in the same living room as the reference image. "
            "Warm evening lighting. Comedy staging - his urgency contrasts with her calm. "
            f"{NO_TEXT} {STYLE}"
        ),
    },
    {
        "filename": "scene-01-panel-05-start.png",
        "chars": ["jenny"],
        "prompt": (
            "Jenny is in THIS living room (from reference image). Same room, same furniture, same lighting. "
            "She sits in an armchair in this living room. There is NO fireplace. "
            "Jenny is a 15-year-old babysitter with dark brown curly hair wearing a coral hoodie. "
            "She sits in an armchair, completely absorbed in her phone, oblivious to everything. "
            "Phone screen glow on her face. She has a cheerful but disconnected expression. "
            "The living room background matches the reference environment exactly. "
            "No other children visible in the background. "
            f"{NO_TEXT} {STYLE}"
        ),
    },
    {
        "filename": "scene-01-panel-05-end.png",
        "chars": ["jenny"],
        "prompt": (
            "Jenny is in THIS living room (from reference image). Same room, same furniture, same lighting. "
            "She sits in an armchair in this living room. There is NO fireplace. "
            "Jenny is a 15-year-old babysitter with dark brown curly hair wearing a coral hoodie. "
            "She is texting on her phone rapidly, still completely absorbed. "
            "Slight change from start - she has shifted position slightly, maybe leaning forward. "
            "Phone glow illuminates her face. Living room background matches reference exactly. "
            "No other children visible in the background. "
            f"{NO_TEXT} {STYLE}"
        ),
    },
    {
        "filename": "scene-01-panel-07-end.png",
        "chars": ["mia", "leo"],
        "prompt": (
            "Over-the-shoulder shot from behind the couch showing exactly TWO children. "
            "Exactly TWO children on the couch, no more. Only Mia and Leo. "
            "Mia (8-year-old girl with dark wavy hair) sits on the left side of the couch. "
            "She turns her head slightly to look back toward the parents (off-screen behind camera). "
            "Leo (5-year-old boy with blonde curly hair in green dinosaur pajamas) sits on the right, "
            "still holding his plush T-Rex, watching TV. "
            "TV glow visible in front of them. Same living room as reference image. "
            "Parents are NOT visible - this is from behind the kids looking forward. "
            f"{NO_TEXT} {STYLE}"
        ),
    },
]


def image_to_part(img_path):
    """Convert an image file to a genai Part."""
    img = Image.open(img_path)
    max_dim = 2048
    if max(img.size) > max_dim:
        ratio = max_dim / max(img.size)
        new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
        img = img.resize(new_size, Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    data = buf.getvalue()
    return types.Part.from_bytes(data=data, mime_type='image/png')


def crop_to_16_9(img_path):
    """Center-crop an image to 16:9 aspect ratio."""
    img = Image.open(img_path)
    w, h = img.size
    target_ratio = 16 / 9
    current_ratio = w / h

    if abs(current_ratio - target_ratio) < 0.01:
        return  # Already 16:9

    if current_ratio > target_ratio:
        # Too wide, crop width
        new_w = int(h * target_ratio)
        left = (w - new_w) // 2
        img = img.crop((left, 0, left + new_w, h))
    else:
        # Too tall, crop height
        new_h = int(w / target_ratio)
        top = (h - new_h) // 2
        img = img.crop((0, top, w, top + new_h))

    img.save(img_path)
    print(f"    Cropped to 16:9: {img.size[0]}x{img.size[1]}")


def generate_panel(panel, client, env_ref_part):
    """Generate a single panel."""
    filename = panel["filename"]
    output_path = OUTPUT_DIR / filename

    print(f"\n{'='*60}")
    print(f"Generating: {filename}")

    # Load character reference parts
    ref_parts = []
    for name in panel["chars"]:
        path = CHAR_REFS.get(name)
        if path and path.exists():
            ref_parts.append(image_to_part(path))
            print(f"  Loaded char ref: {name}")
        else:
            print(f"  WARNING: Missing ref for {name}")

    # Build content: env ref + char refs + prompt
    ref_note = (
        "Use these reference images to maintain consistency. "
        "The first reference image shows the ENVIRONMENT (living room) - match this room exactly. "
    )
    if ref_parts:
        ref_note += (
            "The remaining reference images are CHARACTER TURNAROUND SHEETS - "
            "match these exact characters (same face, same features, same proportions). "
        )

    ref_note += "Generate the scene described below:\n\n"

    all_ref_parts = [env_ref_part] + ref_parts
    content_parts = all_ref_parts + [types.Part.from_text(text=ref_note + panel["prompt"])]

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=MODEL,
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
                        crop_to_16_9(output_path)
                        return output_path
                    elif hasattr(part, 'text') and part.text:
                        print(f"  Text: {part.text[:200]}")

            print(f"  No image data (attempt {attempt + 1}/3)")

        except Exception as e:
            print(f"  Error (attempt {attempt + 1}/3): {e}")

        if attempt < 2:
            print(f"  Retrying in {DELAY_BETWEEN_REQUESTS}s...")
            time.sleep(DELAY_BETWEEN_REQUESTS)

    print(f"  FAILED: Could not generate {filename}")
    return None


def upload_to_r2(files):
    """Upload generated files to R2."""
    print(f"\n{'='*60}")
    print("Uploading to R2...")
    for f in files:
        if f and f.exists():
            cmd = f"rclone copy {f} {R2_DEST}"
            print(f"  Uploading {f.name}...")
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"    OK: {R2_PUBLIC}/{f.name}")
            else:
                print(f"    FAILED: {result.stderr}")


def main():
    print("=" * 60)
    print("Fix Scene 1 v2 Storyboard Panels")
    print("=" * 60)

    if not os.environ.get("GEMINI_API_KEY"):
        print("ERROR: GEMINI_API_KEY not set")
        return 1

    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load environment reference
    print(f"Loading environment reference: {ENV_REF_PATH}")
    if not ENV_REF_PATH.exists():
        print(f"ERROR: Environment reference not found: {ENV_REF_PATH}")
        return 1
    env_ref_part = image_to_part(ENV_REF_PATH)
    print("  OK")

    generated = []
    total = len(PANELS)

    for i, panel in enumerate(PANELS, 1):
        print(f"\n[{i}/{total}]", end="")
        result = generate_panel(panel, client, env_ref_part)
        generated.append(result)

        if i < total:
            print(f"  Waiting {DELAY_BETWEEN_REQUESTS}s...")
            time.sleep(DELAY_BETWEEN_REQUESTS)

    # Summary
    success = sum(1 for g in generated if g is not None)
    print(f"\n{'='*60}")
    print(f"Generated: {success}/{total}")

    if success > 0:
        upload_to_r2([g for g in generated if g is not None])

    print(f"\n{'='*60}")
    print("Done!")
    for g in generated:
        if g:
            print(f"  {R2_PUBLIC}/{g.name}")

    return 0 if success == total else 1


if __name__ == "__main__":
    sys.exit(main())
