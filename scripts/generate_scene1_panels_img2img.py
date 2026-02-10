#!/usr/bin/env python3
"""Generate Scene 1 panels using image-to-image with approved character turnarounds.

Uses character reference turnaround sheets as visual input to ensure
consistency with approved designs.
"""

import os
import sys
import time
from pathlib import Path
from typing import Optional

import google.generativeai as genai
from PIL import Image

# Configuration
MODEL = "gemini-2.5-flash-image"
CHAR_REF_DIR = Path(__file__).parent.parent / "tmp" / "char-refs"
OUTPUT_DIR = Path(__file__).parent.parent / "assets" / "storyboards" / "act1" / "scene-01"
R2_DEST = "r2:rex-assets/storyboards/act1/scene-01/"
R2_PUBLIC = "https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/storyboards/act1/scene-01"
DELAY_SECONDS = 12

# Load character reference images
def load_ref(name: str) -> Image.Image:
    path = CHAR_REF_DIR / f"{name}_turnaround_APPROVED.png"
    if not path.exists():
        print(f"ERROR: Missing reference image: {path}")
        sys.exit(1)
    img = Image.open(path)
    print(f"  Loaded {name} ref: {img.size}")
    return img


# Panel definitions - each has ref images and prompt
PANELS = [
    {
        "filename": "scene-01-panel-08.png",
        "panel": "Panel 08 - Mia close-up 'Promise?'",
        "refs": ["mia"],
        "prompt": (
            "Match this character EXACTLY - same face shape, same dark curly hair, same skin tone, same eye shape. "
            "Generate a NEW image: Close-up of this girl's face, she is looking up at her parents (off-screen above), "
            "saying 'Promise?' with an emotional, worried expression. Her big eyes reflect TV glow. "
            "A lightning flash illuminates the scene from a window behind her. "
            "Pixar-style cinematic storyboard, warm indoor lighting with cool lightning contrast, 16:9 aspect ratio."
        ),
    },
    {
        "filename": "scene-01-panel-02.png",
        "panel": "Panel 02 - Leo medium shot",
        "refs": ["leo"],
        "prompt": (
            "Match this character EXACTLY - same face, same blonde hair color, same round features. "
            "Generate a NEW image: Medium shot of this boy sitting on a cozy living room couch. "
            "He wears green dinosaur pajamas and hugs a plush T-Rex toy. Other small dino toys are scattered around him. "
            "TV glow lights his face from the left. He looks content and relaxed watching something off-screen. "
            "Pixar-style cinematic storyboard, warm cozy evening lighting, 16:9 aspect ratio."
        ),
    },
    {
        "filename": "scene-01-panel-04.png",
        "panel": "Panel 04 - Gabe & Nina two-shot",
        "refs": ["gabe", "nina"],
        "prompt": (
            "Match BOTH these characters EXACTLY - the man has glasses, soft build, and the woman is elegant. "
            "Generate a NEW image: Two-shot, waist up. The man (right) wears a tuxedo and checks his watch impatiently. "
            "The woman (left) wears a black dress with earrings, still getting ready. "
            "Children visible on couch in background. Living room setting, warm evening lighting. "
            "Pixar-style cinematic storyboard, comedy staging, 16:9 aspect ratio."
        ),
    },
    {
        "filename": "scene-01-panel-09.png",
        "panel": "Panel 09 - Gabe hesitates",
        "refs": ["gabe", "nina"],
        "prompt": (
            "Match BOTH these characters EXACTLY - the man with glasses and soft build, the woman elegant. "
            "Generate a NEW image: Close-up on the man's face showing hesitation and inner conflict. "
            "He just heard his daughter ask 'Promise?' and doesn't want to make a promise he might break. "
            "The woman is visible behind him, giving him a stern/encouraging glare. TWO figures only. "
            "Dramatic lighting, emotional family moment. "
            "Pixar-style cinematic storyboard, 16:9 aspect ratio."
        ),
    },
    {
        "filename": "scene-01-panel-07.png",
        "panel": "Panel 07 - Kids over-the-shoulder",
        "refs": ["mia", "leo"],
        "prompt": (
            "Match BOTH these characters EXACTLY - the girl with dark curly hair and the boy with blonde hair. "
            "Generate a NEW image: Over-the-shoulder shot from behind two children sitting on a couch watching TV. "
            "Girl (left) has dark curly hair in a ponytail visible from behind. "
            "Boy (right) has blonde hair and wears green dino pajamas visible from behind. "
            "TV screen ahead shows a dinosaur documentary. Parents are blurred figures rushing around in the background. "
            "Hair colors MUST be clearly distinct - dark vs blonde. "
            "Pixar-style cinematic storyboard, warm evening lighting, 16:9 aspect ratio."
        ),
    },
]


def generate_panel(refs: list[Image.Image], prompt: str, output_path: Path) -> bool:
    """Generate a single panel using image-to-image with character references."""
    try:
        model = genai.GenerativeModel(MODEL)

        # Build content: reference images first, then prompt
        content = refs + [prompt]

        response = model.generate_content(
            content,
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
                    print(f"  SUCCESS: Saved {len(img_bytes):,} bytes to {output_path}")
                    return True

        print("  ERROR: No image data in response")
        if hasattr(response, "candidates") and response.candidates:
            for part in response.candidates[0].content.parts:
                if hasattr(part, "text"):
                    print(f"  Response text: {part.text[:200]}")
        return False

    except Exception as e:
        print(f"  ERROR: {e}")
        return False


def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY not set")
        sys.exit(1)

    genai.configure(api_key=api_key)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("Scene 1 Panel Generation - Image-to-Image")
    print(f"Model: {MODEL}")
    print(f"Output: {OUTPUT_DIR}")
    print("=" * 60)

    # Pre-load all character references
    print("\nLoading character references...")
    char_refs = {}
    for name in ["mia", "leo", "gabe", "nina"]:
        char_refs[name] = load_ref(name)

    results = []
    total = len(PANELS)

    for i, panel in enumerate(PANELS):
        print(f"\n[{i+1}/{total}] {panel['panel']}")
        print(f"  Refs: {', '.join(panel['refs'])}")

        # Get reference images for this panel
        ref_images = [char_refs[name] for name in panel["refs"]]
        output_path = OUTPUT_DIR / panel["filename"]

        success = generate_panel(ref_images, panel["prompt"], output_path)
        results.append((panel["filename"], success))

        if i < total - 1:
            print(f"  Waiting {DELAY_SECONDS}s for rate limit...")
            time.sleep(DELAY_SECONDS)

    print("\n" + "=" * 60)
    print("Results:")
    for filename, success in results:
        status = "OK" if success else "FAILED"
        print(f"  [{status}] {filename}")

    success_count = sum(1 for _, s in results if s)
    print(f"\n{success_count}/{total} panels generated successfully")
    print("=" * 60)

    return 0 if success_count == total else 1


if __name__ == "__main__":
    sys.exit(main())
