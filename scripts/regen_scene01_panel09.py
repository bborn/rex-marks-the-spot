#!/usr/bin/env python3
"""
Regenerate Scene 1 Panel 09 - Fix wardrobe issue.

Issue: Both parents wearing casual clothes instead of date night attire.
Fix: Gabe in black tuxedo, Nina in black cocktail dress.
Style: 3D Pixar render (consistent with panels 02, 04, 07, 08).
Aspect ratio: 16:9 widescreen.
"""

import os
import sys
import subprocess
from pathlib import Path

from google import genai
from google.genai import types
from PIL import Image
import io

MODEL = "gemini-2.0-flash-exp-image-generation"

SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
CHAR_REF_DIR = PROJECT_DIR / "tmp" / "char-refs"
OUTPUT_DIR = PROJECT_DIR / "tmp" / "scene01-panels"
R2_DEST = "r2:rex-assets/storyboards/act1/panels/"
R2_PUBLIC = "https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/storyboards/act1/panels"

CHAR_REFS = {
    "gabe": CHAR_REF_DIR / "gabe_turnaround_APPROVED.png",
    "nina": CHAR_REF_DIR / "nina_turnaround_APPROVED.png",
}

# 3D Pixar render style (matching panels 02, 04, 07, 08)
STYLE_SUFFIX = (
    "3D animated render, Pixar animation style, stylized 3D characters, "
    "cinematic lighting, warm interior ambient light, soft shadows, "
    "high quality 3D render, 16:9 widescreen aspect ratio"
)

# Panel 09 with explicit wardrobe correction
PANEL_PROMPT = (
    "Close-up two-shot of a married couple in a warmly lit living room. "
    "IMPORTANT WARDROBE: The father wears a BLACK TUXEDO with a bow tie - formal date night attire. "
    "The mother wears an ELEGANT BLACK COCKTAIL DRESS - formal date night attire. "
    "The father (screen right) has a round soft face, rectangular glasses, light stubble, "
    "dark brown slightly thinning hair, stocky build soft around the middle, early 40s. "
    "His expression shows internal conflict and hesitation - he is uncomfortable making a promise to his kids. "
    "He adjusts his glasses nervously. "
    "The mother (screen left) has brownish-auburn shoulder-length hair with natural waves, "
    "warm hazel-green eyes, mature features with smile lines, late 30s. "
    "She gives him a fierce 'don't you dare back out' glare with her arms crossed. "
    "The emotional beat: he hesitates, she glares, he finally says 'Promise.' "
    "Warm amber interior lighting from the living room. Close-up framing showing both faces. "
)


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


def generate_panel(client, model_name):
    """Generate panel 09."""
    filename = "scene-01-panel-09.png"
    output_path = OUTPUT_DIR / filename

    print(f"Generating Panel 09 with model: {model_name}")

    # Load character references
    ref_parts = []
    for name, path in CHAR_REFS.items():
        if path.exists():
            ref_parts.append(image_to_part(path))
            print(f"  Loaded ref: {name}")
        else:
            print(f"  WARNING: Missing ref for {name} at {path}")

    full_prompt = PANEL_PROMPT + STYLE_SUFFIX

    if ref_parts:
        ref_note = (
            "Use these character reference sheets to maintain consistent character designs. "
            "CRITICAL: The father must be wearing a BLACK TUXEDO (not casual clothes). "
            "The mother must be wearing a BLACK COCKTAIL DRESS (not casual clothes). "
            "They are dressed up for a formal date night. "
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

        print("  FAILED: No image data in response")
        return None

    except Exception as e:
        print(f"  ERROR: {e}")
        return None


def enforce_16_9(img_path):
    """Crop or pad the image to exact 16:9 aspect ratio."""
    img = Image.open(img_path)
    w, h = img.size
    target_ratio = 16 / 9
    current_ratio = w / h

    if abs(current_ratio - target_ratio) < 0.05:
        print(f"  Aspect ratio {current_ratio:.2f} is close enough to 16:9")
        return img_path

    if current_ratio < target_ratio:
        # Too tall - center crop height
        new_h = int(w / target_ratio)
        top = (h - new_h) // 2
        img = img.crop((0, top, w, top + new_h))
        print(f"  Cropped height: {w}x{h} -> {img.size[0]}x{img.size[1]}")
    else:
        # Too wide - pad top/bottom with edge color
        new_h = int(w / target_ratio)
        pad_total = new_h - h
        pad_top = pad_total // 2
        pad_bottom = pad_total - pad_top
        # Sample average color from top and bottom edges
        import numpy as np
        arr = np.array(img)
        top_color = tuple(arr[0].mean(axis=0).astype(int))
        bot_color = tuple(arr[-1].mean(axis=0).astype(int))
        new_img = Image.new('RGB', (w, new_h), top_color)
        new_img.paste(img, (0, pad_top))
        # Fill bottom strip with bottom color
        for y in range(pad_top + h, new_h):
            for x in range(w):
                new_img.putpixel((x, y), bot_color)
        img = new_img
        print(f"  Padded height: {w}x{h} -> {img.size[0]}x{img.size[1]}")

    img.save(img_path)
    ratio = img.size[0] / img.size[1]
    print(f"  Final aspect ratio: {ratio:.2f}")
    return img_path


def upload_to_r2(local_path):
    """Upload to R2."""
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

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    client = genai.Client(api_key=api_key)

    result_path = generate_panel(client, MODEL)

    if result_path is None:
        print("\nFAILED: Could not generate panel 09")
        sys.exit(1)

    # Enforce 16:9 aspect ratio
    print("\nEnforcing 16:9 aspect ratio...")
    enforce_16_9(result_path)

    # Upload to R2
    print("\nUploading to R2...")
    url = upload_to_r2(result_path)

    if url:
        print(f"\nSUCCESS: Panel 09 regenerated and uploaded")
        print(f"  URL: {url}")
    else:
        print(f"\nGenerated but upload failed. File at: {result_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
