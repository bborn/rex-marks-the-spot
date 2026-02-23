#!/usr/bin/env python3
"""Fix Scene 1 Panel 07 - Gabe beard and wardrobe wrong.

Director feedback:
- Gabe has a beard in panel (should be clean-shaven)
- Parents should be in date-night formal wear
  - Gabe: black suit/tux
  - Nina: black cocktail dress
- Nina appears in casual clothes instead

Regenerate the over-the-shoulder kids watching TV panel with correct
parent wardrobe and Gabe clean-shaven.
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
MODEL = "gemini-3-pro-image-preview"
MAX_ATTEMPTS = 3
DELAY_BETWEEN_ATTEMPTS = 12

SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
CHAR_REF_DIR = PROJECT_DIR / "tmp" / "char-refs"
OUTPUT_DIR = PROJECT_DIR / "tmp" / "scene01-panels"
OUTPUT_FILE = OUTPUT_DIR / "scene-01-panel-07.png"

# R2 upload destinations (upload to both locations for consistency)
R2_PANELS = "r2:rex-assets/storyboards/act1/panels/"
R2_SCENE01 = "r2:rex-assets/storyboards/act1/scene-01/"
R2_PUBLIC_PANELS = "https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/storyboards/act1/panels"
R2_PUBLIC_SCENE01 = "https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/storyboards/act1/scene-01"


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


def upload_to_r2(local_path, r2_dest):
    """Upload a file to R2."""
    try:
        result = subprocess.run(
            ["rclone", "copy", str(local_path), r2_dest],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode == 0:
            print(f"  Uploaded to: {r2_dest}")
            return True
        else:
            print(f"  Upload error: {result.stderr}")
            return False
    except Exception as e:
        print(f"  Upload error: {e}")
        return False


def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY not set")
        sys.exit(1)

    # Verify character refs
    refs = {
        "gabe": CHAR_REF_DIR / "gabe_turnaround_APPROVED.png",
        "nina": CHAR_REF_DIR / "nina_turnaround_APPROVED.png",
        "mia": CHAR_REF_DIR / "mia_turnaround_APPROVED.png",
        "leo": CHAR_REF_DIR / "leo_turnaround_APPROVED.png",
    }

    print("Checking character references...")
    for name, path in refs.items():
        if path.exists():
            print(f"  {name}: OK")
        else:
            print(f"  {name}: MISSING - {path}")
            sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load character reference images
    print("\nLoading character references...")
    ref_parts = []
    for name in ["gabe", "nina", "mia", "leo"]:
        ref_parts.append(image_to_part(refs[name]))
        print(f"  Loaded: {name}")

    # Build prompt with strong emphasis on wardrobe and no-beard
    prompt = """Use these 4 character reference sheets to maintain consistent character designs.
The characters shown are (in order): Gabe (father), Nina (mother), Mia (8-year-old daughter), Leo (5-year-old son).

IMPORTANT WARDROBE CHANGES FROM REFERENCE SHEETS:
- Gabe is wearing a BLACK SUIT / TUXEDO for date night (NOT his everyday plaid shirt)
- Nina is wearing an elegant BLACK COCKTAIL DRESS for date night (NOT her everyday burgundy sweater)
- Gabe is CLEAN-SHAVEN - absolutely NO BEARD, NO FACIAL HAIR, NO STUBBLE

Generate a cinematic Pixar-style 3D animated storyboard panel:

SCENE: Panel 1G - Over-the-shoulder shot, kids watching TV, parents leaving in background

COMPOSITION:
- Camera positioned behind/between TWO children sitting on a couch
- Looking past the kids toward a TV screen showing a colorful dinosaur cartoon
- Parents (Gabe and Nina) visible in the background near a doorway/hallway, preparing to leave

FOREGROUND (kids from behind):
- LEFT: Mia (8-year-old girl) - dark brown/black curly hair in a high ponytail, pink star-pattern pajama top, seen from behind
- RIGHT: Leo (5-year-old boy) - blonde curly hair, green dinosaur-pattern pajamas, seen from behind
- EXACTLY 2 children only

BACKGROUND (parents):
- Gabe: CLEAN-SHAVEN face (NO BEARD AT ALL), glasses, wearing a BLACK SUIT/TUXEDO, dark brown hair, soft build
- Nina: Auburn/reddish-brown wavy hair, wearing an elegant BLACK COCKTAIL DRESS, small earrings catching light
- They are getting ready to leave, near the hallway/door area

LIGHTING:
- Warm TV glow illuminating kids from front
- Warm amber interior home lighting
- Cozy living room atmosphere

STYLE: Pixar/Dreamworks 3D animated movie quality, cinematic lighting
ASPECT RATIO: Must be 16:9 WIDESCREEN (wider than tall, like a movie frame). Width should be roughly 1.78x the height. This is a WIDE horizontal image, NOT square.
"""

    client = genai.Client(api_key=api_key)

    content_parts = ref_parts + [types.Part.from_text(text=prompt)]

    for attempt in range(1, MAX_ATTEMPTS + 1):
        print(f"\nAttempt {attempt}/{MAX_ATTEMPTS} using {MODEL}...")
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
                        with open(OUTPUT_FILE, "wb") as f:
                            f.write(img_bytes)
                        size_kb = len(img_bytes) / 1024
                        print(f"  SUCCESS: Saved {OUTPUT_FILE} ({size_kb:.0f} KB)")

                        # Upload to R2 (both locations)
                        print("\nUploading to R2...")
                        upload_to_r2(OUTPUT_FILE, R2_PANELS)
                        upload_to_r2(OUTPUT_FILE, R2_SCENE01)

                        print(f"\nPanel URLs:")
                        print(f"  {R2_PUBLIC_PANELS}/scene-01-panel-07.png")
                        print(f"  {R2_PUBLIC_SCENE01}/scene-01-panel-07.png")
                        return 0

                    elif hasattr(part, 'text') and part.text:
                        print(f"  Text response: {part.text[:200]}")

            print(f"  No image data in response")

        except Exception as e:
            print(f"  Error: {e}")

        if attempt < MAX_ATTEMPTS:
            print(f"  Waiting {DELAY_BETWEEN_ATTEMPTS}s before retry...")
            time.sleep(DELAY_BETWEEN_ATTEMPTS)

    print("\nFailed to generate image after all attempts")
    return 1


if __name__ == "__main__":
    sys.exit(main())
