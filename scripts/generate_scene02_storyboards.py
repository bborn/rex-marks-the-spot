#!/usr/bin/env python3
"""Generate Act 1 Scene 2 storyboard panels using Gemini with character references."""

import os
import sys
import time
import subprocess
from pathlib import Path

import google.generativeai as genai
from PIL import Image

# Configuration
MODEL = "gemini-3-pro-image-preview"
FALLBACK_MODEL = "gemini-2.5-flash-image"
CHAR_REF_DIR = Path(__file__).parent.parent / "tmp" / "char-refs"
OUTPUT_DIR = Path(__file__).parent.parent / "tmp" / "output"
R2_DEST = "r2:rex-assets/storyboards/act1/scene-02/"
R2_PUBLIC = "https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/storyboards/act1/scene-02"

# Panel definitions
PANELS = [
    {
        "filename": "scene-02-panel-01.png",
        "char_refs": [],  # No characters visible
        "prompt": (
            "Generate an image: Traditional animation storyboard panel, "
            "rough pencil sketch on paper, black and white with light gray shading, "
            "hand-drawn look with visible pencil strokes and construction lines. "
            "WIDE ESTABLISHING SHOT: Suburban two-story family house at night during a violent rainstorm. "
            "Heavy rain streaking down, dark stormy sky dominating the upper two-thirds of frame. "
            "Warm amber light spilling from the house windows contrasting with the cold dark exterior. "
            "A car sits in the driveway. Lightning bolt illuminating the scene. "
            "Trees bending in fierce wind, puddles forming on walkway. "
            "Ominous, foreboding atmosphere. Transition from safety to danger. "
            "Pixar pre-production storyboard style, loose gestural drawing, "
            "minimal cross-hatching for shadows, 16:9 widescreen composition. "
            "Camera direction notes: 'WIDE EST. - STATIC' written in margin."
        ),
    },
    {
        "filename": "scene-02-panel-02.png",
        "char_refs": ["gabe_turnaround_APPROVED.png", "nina_turnaround_APPROVED.png"],
        "prompt": (
            "Generate an image based on these character reference sheets. "
            "Draw these EXACT characters in a storyboard panel: "
            "Traditional animation storyboard panel, rough pencil sketch on paper, "
            "black and white with light gray shading, hand-drawn look with visible pencil strokes. "
            "MEDIUM TRACKING SHOT: The couple from the reference sheets rushing out of their front door "
            "into heavy rain at night. The husband (Gabe - glasses, soft build, early 40s from ref) "
            "is leading, running toward the driver side of the car with his jacket held over his head. "
            "The wife (Nina - elegant, dark hair from ref) follows just behind, holding a small clutch "
            "purse over her head. Both are in black-tie formal attire getting soaked by rain. "
            "Door just slammed behind them. Rain pouring down hard. "
            "Nina's heels splashing through puddles on the walkway. Car headlights flickering on. "
            "Urgent body language, handheld camera energy. "
            "Pixar pre-production storyboard style, loose gestural drawing, "
            "16:9 widescreen composition. "
            "Camera note: 'MED TRACK - following action' in margin."
        ),
    },
    {
        "filename": "scene-02-panel-03.png",
        "char_refs": [],  # No characters - sky shot
        "prompt": (
            "Generate an image: Traditional animation storyboard panel, "
            "rough pencil sketch on paper, black and white with light gray shading, "
            "hand-drawn look with visible pencil strokes and construction lines. "
            "LOW ANGLE WIDE SHOT looking UP at the stormy sky. "
            "House roofline and tree silhouettes at the very bottom of frame. "
            "A MASSIVE dramatic lightning bolt cracking across churning dark clouds, "
            "branching into multiple forks. Rain falling toward the camera. "
            "Intense, ominous energy. Foreshadowing danger. "
            "Car headlights visible as small glow at bottom edge of frame. "
            "Deep blacks with white lightning creating stark contrast. "
            "Pixar pre-production storyboard style, loose gestural drawing, "
            "heavy cross-hatching for the dark stormy sky, "
            "16:9 widescreen composition. "
            "Camera note: 'LOW ANGLE - STATIC - hold on sky' in margin."
        ),
    },
]


def generate_panel(panel: dict, model_name: str, api_key: str) -> bool:
    """Generate a single storyboard panel."""
    output_path = OUTPUT_DIR / panel["filename"]
    filename = panel["filename"]

    print(f"\nGenerating: {filename}")
    print(f"  Model: {model_name}")
    print(f"  Character refs: {panel['char_refs'] or 'None'}")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name)

    # Build content with optional character reference images
    content = []
    for ref_file in panel["char_refs"]:
        ref_path = CHAR_REF_DIR / ref_file
        if ref_path.exists():
            print(f"  Loading ref: {ref_file}")
            img = Image.open(ref_path)
            content.append(img)
        else:
            print(f"  WARNING: Reference not found: {ref_path}")

    content.append(panel["prompt"])

    for attempt in range(3):
        try:
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
                        print(f"  SUCCESS: {output_path} ({len(img_bytes):,} bytes)")
                        return True

            print(f"  No image in response (attempt {attempt + 1}/3)")
            if attempt < 2:
                time.sleep(10)

        except Exception as e:
            print(f"  Error (attempt {attempt + 1}/3): {e}")
            if attempt < 2:
                time.sleep(10)

    return False


def upload_to_r2(local_path: Path) -> str:
    """Upload file to R2 and return public URL."""
    print(f"  Uploading to R2: {R2_DEST}")
    try:
        result = subprocess.run(
            ["rclone", "copy", str(local_path), R2_DEST],
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode == 0:
            url = f"{R2_PUBLIC}/{local_path.name}"
            print(f"  Uploaded: {url}")
            return url
        else:
            print(f"  Upload error: {result.stderr}")
            return ""
    except Exception as e:
        print(f"  Upload error: {e}")
        return ""


def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY not set")
        return 1

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("Act 1, Scene 2: House Exterior - Storyboard Generation")
    print(f"Model: {MODEL}")
    print(f"Output: {OUTPUT_DIR}")
    print("=" * 60)

    urls = []
    for i, panel in enumerate(PANELS):
        print(f"\n[{i + 1}/{len(PANELS)}] ", end="")

        # Try primary model, fall back if needed
        success = generate_panel(panel, MODEL, api_key)
        if not success:
            print(f"  Trying fallback model: {FALLBACK_MODEL}")
            success = generate_panel(panel, FALLBACK_MODEL, api_key)

        if success:
            url = upload_to_r2(OUTPUT_DIR / panel["filename"])
            urls.append(url)
        else:
            print(f"  FAILED: Could not generate {panel['filename']}")
            urls.append("")

        # Rate limit delay between panels
        if i < len(PANELS) - 1:
            delay = 12
            print(f"  Waiting {delay}s for rate limiting...")
            time.sleep(delay)

    print("\n" + "=" * 60)
    print("RESULTS:")
    for i, url in enumerate(urls):
        status = "OK" if url else "FAILED"
        print(f"  Panel {i + 1}: [{status}] {url}")
    print("=" * 60)

    success_count = sum(1 for u in urls if u)
    return 0 if success_count == len(PANELS) else 1


if __name__ == "__main__":
    sys.exit(main())
