#!/usr/bin/env python3
"""
Generate Ruben turnaround for Asset Bible.

Image-to-image from ruben_final_C.png on R2. Produces clean front/3-4/side/back
turnaround on plain white background. Saves 2 candidates to asset-bible/characters/ruben-alts/.
"""

import os
import sys
from pathlib import Path
from urllib.request import urlopen, Request
from io import BytesIO

import google.generativeai as genai
from PIL import Image

MODEL = "gemini-3-pro-image-preview"
REFERENCE_URL = (
    "https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/"
    "characters/ruben/final-iterations/ruben_final_C.png"
)
USER_AGENT = "Mozilla/5.0 (asset-bible-generator)"
OUT_DIR = Path(__file__).parent.parent / "asset-bible" / "characters" / "ruben-alts"

PROMPT = """Generate a clean Pixar-style character turnaround sheet of the SAME character shown in the reference image, on a plain pure-white background.

CRITICAL VIEWS REQUIRED (horizontal row, left to right):
1. FRONT view - facing camera directly, arms slightly out at sides (relaxed A-pose if possible without mop), full body visible
2. SIDE view - full 90-degree profile from the left side, full body
3. BACK view - facing completely away from camera, showing back of head, vest, wings, trousers

The character is RUBEN, a fairy godfather:
- Appears late 50s, lanky build, hunched/tired posture
- Silvery-gray wild unkempt hair (mostly bald on top with wisps around the sides)
- Large prominent bulbous nose
- Heavy brows, tired droopy eyes, world-weary expression
- 3-day stubble
- TRANSLUCENT FAIRY WINGS in muted purple/lavender, slightly drooping, visible in front (behind body), full from side, and prominent in back view
- Faded gray-blue button-down shirt, slightly wrinkled
- Olive-gray utility vest, slightly stained
- Dark gray trousers
- Brown worn shoes

The reference image shows him holding a mop - for THIS turnaround, OMIT THE MOP. Arms hang at sides in a neutral A-pose stance.

Style: Pixar 3D animation, stylized but rendered (matches the reference image's style).
Background: pure plain white, no shadows, no text, no labels.
Character proportions identical across all 3 views (same height, same age).
Professional character model sheet for 3D animation reference.
"""


def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Downloading reference from {REFERENCE_URL}")
    req = Request(REFERENCE_URL, headers={"User-Agent": USER_AGENT})
    with urlopen(req) as r:
        ref_bytes = r.read()
    ref_img = Image.open(BytesIO(ref_bytes))
    print(f"Reference loaded: {ref_img.size}")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(MODEL)

    candidate = sys.argv[1] if len(sys.argv) > 1 else "v1"
    out_path = OUT_DIR / f"ruben_turnaround_{candidate}.png"

    print(f"Generating ruben turnaround {candidate} -> {out_path}")
    response = model.generate_content(
        [ref_img, PROMPT],
        generation_config={"response_modalities": ["IMAGE", "TEXT"]},
    )

    if not (hasattr(response, "candidates") and response.candidates):
        print("ERROR: no candidates in response", file=sys.stderr)
        sys.exit(2)

    for part in response.candidates[0].content.parts:
        if hasattr(part, "inline_data") and part.inline_data:
            with open(out_path, "wb") as f:
                f.write(part.inline_data.data)
            print(f"SAVED {out_path} ({len(part.inline_data.data):,} bytes)")
            return

    print("ERROR: no image data in any part", file=sys.stderr)
    sys.exit(3)


if __name__ == "__main__":
    main()
