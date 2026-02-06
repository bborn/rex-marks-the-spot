#!/usr/bin/env python3
"""
Gabe Turnaround V4 Generator

Fixes V3's duplicate side views by generating proper 3/4 view (45-degree angle).

Usage:
    python scripts/generate_gabe_turnaround_v4.py

Outputs: gabe_turnaround_v4.png, uploaded to R2
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import Optional
from urllib.request import urlopen
from io import BytesIO

import google.generativeai as genai
from PIL import Image

# Configuration
OUTPUT_DIR = Path(__file__).parent.parent / "assets" / "characters" / "gabe"
OUTPUT_FILE = "gabe_turnaround_v4.png"
MODEL = "gemini-2.0-flash-exp-image-generation"
R2_DEST = "r2:rex-assets/characters/gabe/"
REFERENCE_IMAGE_URL = "https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/characters/gabe/gabe_turnaround_v3.png"

# Gabe V4 prompt - proper 3/4 view using reference image
GABE_V4_PROMPT = """Regenerate this EXACT character turnaround with ONE CRITICAL FIX:

The second view must be a proper THREE-QUARTER (3/4) view at EXACTLY 45 degrees - NOT a side profile.

Keep EVERYTHING else identical:
- Same character design, face, hair, body type, outfit
- Same plaid shirt pattern and colors
- Same khaki pants
- Same glasses style
- Same overall appearance

The four views must be:
1. FRONT - facing camera (keep as-is)
2. THREE-QUARTER (3/4) - Turn the character 45 degrees to show BOTH front and side at same time (FIX THIS - currently it's just another side view)
3. SIDE - full 90-degree profile (keep as-is)
4. BACK - facing away (keep as-is)

The 3/4 view should show the character rotated halfway between the front view and the side view - you should be able to see part of his face AND part of the side of his head simultaneously.

Professional character turnaround model sheet for 3D animation reference.
Pixar/Dreamworks style animated movie character design.

Character: Gabe, a father in his early 40s. Workaholic dad learning to be present with family.

FACE:
- Rectangular glasses with thin modern frames (NOT thick nerd glasses)
- Light stubble/five o'clock shadow
- Receding hairline at temples
- Dark brown hair with slight gray at temples
- Warm brown eyes, slightly tired

HAIR:
- Wavy, textured hair with body and movement (NOT flat or slicked down)
- Natural waves, stylish but not overly groomed
- Slightly messy in an authentic dad way

BODY:
- Normal dad bod - soft around middle but NOT overly chubby
- Trimmed down belly (still present, just not pronounced)
- Average height ~5'10", comfortable proportions
- NOT muscular, just regular dad physique

OUTFIT:
- Blue/teal plaid button-up shirt (casual pattern)
- Khaki/tan casual pants
- Brown casual shoes or loafers
- Rolled sleeves (casual, approachable)

CRITICAL - FOUR DISTINCT VIEWS in horizontal row on clean white background:
1. FRONT view - facing camera directly, neutral stance, arms relaxed at sides
2. THREE-QUARTER (3/4) view - body and face turned EXACTLY 45 degrees to the right, showing depth and dimension (THIS IS NOT A SIDE VIEW - it's a diagonal angle between front and side, you can see both the front of his face AND the side of his head)
3. SIDE PROFILE view - full 90-degree side view, showing complete profile from the side
4. BACK view - facing completely away from camera, showing back of head, shirt, and pants

The 3/4 view is CRUCIAL - it must show the character at a 45-degree angle, NOT straight-on and NOT a full side profile. Think of it as rotating the character halfway between front and side.

Character MUST be identical and consistent across all four views - same outfit, same hair, same proportions.
Clean white background. Professional animation studio model sheet quality.
Pixar/Dreamworks 3D animation aesthetic, NOT photorealistic.
Approachable dad energy."""


def generate_gabe_v4(api_key: str) -> Optional[Path]:
    """Generate Gabe V4 turnaround sheet."""
    print(f"Configuring Gemini with model: {MODEL}")
    genai.configure(api_key=api_key)

    model = genai.GenerativeModel(MODEL)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / OUTPUT_FILE

    print(f"Downloading reference image from: {REFERENCE_IMAGE_URL}")
    with urlopen(REFERENCE_IMAGE_URL) as response:
        reference_image = Image.open(BytesIO(response.read()))
    print(f"Reference image loaded: {reference_image.size}")

    print(f"Generating Gabe V4 turnaround with reference image...")
    print(f"Output: {output_path}")

    try:
        response = model.generate_content(
            [reference_image, GABE_V4_PROMPT],
            generation_config={
                "response_modalities": ["IMAGE", "TEXT"],
            },
        )

        if hasattr(response, "candidates") and response.candidates:
            for part in response.candidates[0].content.parts:
                if hasattr(part, "inline_data") and part.inline_data:
                    img_bytes = part.inline_data.data
                    with open(output_path, "wb") as f:
                        f.write(img_bytes)
                    print(f"SUCCESS: Saved to {output_path}")
                    print(f"Size: {len(img_bytes):,} bytes")
                    return output_path

        print("ERROR: No image data in response")
        return None

    except Exception as e:
        print(f"ERROR generating image: {e}")
        return None


def upload_to_r2(local_path: Path) -> Optional[str]:
    """Upload generated image to R2."""
    print(f"\nUploading to R2: {R2_DEST}")
    try:
        result = subprocess.run(
            ["rclone", "copy", str(local_path), R2_DEST],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0:
            url = f"https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/characters/gabe/{OUTPUT_FILE}"
            print(f"SUCCESS: Uploaded to {url}")
            return url
        else:
            print(f"ERROR uploading: {result.stderr}")
            return None
    except Exception as e:
        print(f"ERROR uploading: {e}")
        return None


def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY environment variable not set")
        sys.exit(1)

    print("=" * 60)
    print("Gabe Turnaround V4 Generator")
    print("Fixing 3/4 view - proper 45-degree angle")
    print("=" * 60)

    # Generate the image
    output_path = generate_gabe_v4(api_key)
    if not output_path:
        print("\nFAILED: Could not generate image")
        sys.exit(1)

    # Upload to R2
    url = upload_to_r2(output_path)
    if url:
        print(f"\nDONE! View at: {url}")
    else:
        print(f"\nImage saved locally but R2 upload failed: {output_path}")
        sys.exit(1)


if __name__ == "__main__":
    main()
