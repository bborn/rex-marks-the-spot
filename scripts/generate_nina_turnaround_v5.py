#!/usr/bin/env python3
"""
Nina Turnaround V5 Generator

Fixes V4's duplicate side views by generating proper 3/4 view (45-degree angle).
Keeps all V4 features: late 30s maturity, brownish-auburn hair, burgundy sweater.

Usage:
    python scripts/generate_nina_turnaround_v5.py

Outputs: nina_turnaround_v5.png, uploaded to R2
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
OUTPUT_DIR = Path(__file__).parent.parent / "assets" / "characters" / "nina"
OUTPUT_FILE = "nina_turnaround_v5.png"
MODEL = "gemini-2.0-flash-exp-image-generation"
R2_DEST = "r2:rex-assets/characters/nina/"
REFERENCE_IMAGE_URL = "https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/characters/nina/nina_turnaround_APPROVED.png"

# Nina V5 prompt - proper 3/4 view using reference image
NINA_V5_PROMPT = """Regenerate this EXACT character turnaround with ONE CRITICAL FIX:

The second view must be a proper THREE-QUARTER (3/4) view at EXACTLY 45 degrees - NOT a side profile.

Keep EVERYTHING else identical:
- Same character design, face, hair color (brownish-auburn), hair style
- Same mature late-30s mom features (smile lines, crow's feet)
- Same burgundy sweater
- Same dark jeans and white sneakers
- Same body type and proportions
- Same overall appearance

The four views must be:
1. FRONT - facing camera (keep as-is)
2. THREE-QUARTER (3/4) - Turn the character 45 degrees to show BOTH front and side at same time (FIX THIS - currently it's just another side view)
3. SIDE - full 90-degree profile (keep as-is)
4. BACK - facing away (keep as-is)

The 3/4 view should show the character rotated halfway between the front view and the side view - you should be able to see part of her face AND part of the side of her head simultaneously.

Professional character turnaround model sheet for 3D animation reference.
Pixar/Dreamworks style animated movie character design.

Character: Nina, a mother in her LATE 30s (age 37-38). She looks like a real mom who has been through years of parenting - NOT a young woman in her 20s.

FACE AND AGE (CRITICAL - she must clearly look late 30s, NOT early 20s):
- Heart-shaped face with DEFINED cheekbones, showing subtle age and maturity
- VISIBLE smile lines and crow's feet around her eyes - she has LAUGHED and CRIED for 37 years
- Clear nasolabial fold lines (laugh lines running from nose to mouth corners)
- Slightly less taut skin under chin and jawline - subtle but present
- Small forehead expression lines from years of raising kids
- Warm, wise, slightly tired hazel-green eyes with depth of experience
- Natural eyebrows with slight thinning at the tails (a late-30s detail)
- She is BEAUTIFUL but in a MATURE, lived-in, real-mom way
- Think Amy Adams or Bryce Dallas Howard at age 37-38, not a college student
- Fuller, softer facial features of a woman who has had two children
- Very slight under-eye shadows from years of interrupted sleep as a mom

HAIR (IMPORTANT - brownish-auburn, NOT bright red):
- Shoulder-length hair with natural body and soft waves
- Color: BROWNISH-AUBURN - primarily brown with warm auburn/chestnut undertones
- Think dark brown hair that catches reddish-auburn highlights in the light
- NOT bright red, NOT orange, NOT copper - BROWN with subtle auburn warmth
- Natural-looking, like she colors it herself, slight root shadow visible

BODY:
- Height 5'7", natural mom body - not model-thin, not heavy
- Soft midsection from having had two children
- Natural proportions, she takes care of herself but isn't fitness-obsessed
- Comfortable in her own skin

OUTFIT (casual at-home look):
- Cozy burgundy/wine-colored oversized sweater (slightly slouchy, comfortable)
- Dark wash skinny jeans (flattering but practical)
- Clean white canvas sneakers
- Simple gold stud earrings, thin gold bracelet

CRITICAL - FOUR DISTINCT VIEWS in horizontal row on clean white background:
1. FRONT view - facing camera directly, relaxed natural stance, arms at sides
2. THREE-QUARTER (3/4) view - body and face turned EXACTLY 45 degrees to the right, showing depth and dimension (THIS IS NOT A SIDE VIEW - it's a diagonal angle between front and side, you can see both the front of her face AND the side of her head)
3. SIDE PROFILE view - full 90-degree side view, showing complete profile from the side
4. BACK view - facing completely away from camera, showing back of head, hair, sweater, and jeans

The 3/4 view is CRUCIAL - it must show the character at a 45-degree angle, NOT straight-on and NOT a full side profile. Think of it as rotating the character halfway between front and side.

Character MUST be identical and consistent across all four views - same outfit, same hair, same age markers.
Clean white background. Professional animation studio model sheet quality.
Warm, approachable mom energy - the kind of mom who holds everything together.
Stylized Pixar 3D animation aesthetic, NOT photorealistic."""


def generate_nina_v5(api_key: str) -> Optional[Path]:
    """Generate Nina V5 turnaround sheet."""
    print(f"Configuring Gemini with model: {MODEL}")
    genai.configure(api_key=api_key)

    model = genai.GenerativeModel(MODEL)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / OUTPUT_FILE

    print(f"Downloading reference image from: {REFERENCE_IMAGE_URL}")
    with urlopen(REFERENCE_IMAGE_URL) as response:
        reference_image = Image.open(BytesIO(response.read()))
    print(f"Reference image loaded: {reference_image.size}")

    print(f"Generating Nina V5 turnaround with reference image...")
    print(f"Output: {output_path}")

    try:
        response = model.generate_content(
            [reference_image, NINA_V5_PROMPT],
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
            url = f"https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/characters/nina/{OUTPUT_FILE}"
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
    print("Nina Turnaround V5 Generator")
    print("Fixing 3/4 view - proper 45-degree angle")
    print("=" * 60)

    # Generate the image
    output_path = generate_nina_v5(api_key)
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
