#!/usr/bin/env python3
"""
Unified Character Turnaround Generator

Generates character turnaround sheets using Gemini 3.0 Pro image generation.
Supports text-to-image or image-to-image (with reference).

Usage:
    # Text-to-image (new character)
    python scripts/generate_character_turnaround.py --character mia --version 2 --prompt "8-year-old girl..."

    # Image-to-image (fix existing)
    python scripts/generate_character_turnaround.py --character gabe --version 4 \
        --reference-url https://r2.dev/gabe_v3.png \
        --prompt "Fix 3/4 view only, keep everything else identical"

Outputs: {character}_turnaround_v{version}.png, uploaded to R2
"""

import argparse
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
MODEL = "gemini-3-pro-image-preview"
OUTPUT_BASE_DIR = Path(__file__).parent.parent / "assets" / "characters"
R2_BASE_PATH = "r2:rex-assets/characters"
R2_PUBLIC_BASE = "https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/characters"


def generate_turnaround(
    character: str,
    version: str,
    prompt: str,
    reference_url: Optional[str] = None,
    api_key: str = None
) -> Optional[Path]:
    """Generate character turnaround sheet."""
    print(f"Configuring Gemini with model: {MODEL}")
    genai.configure(api_key=api_key)

    model = genai.GenerativeModel(MODEL)

    # Setup output paths
    output_dir = OUTPUT_BASE_DIR / character
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = f"{character}_turnaround_v{version}.png"
    output_path = output_dir / output_file

    print(f"\nGenerating {character} V{version} turnaround...")
    print(f"Output: {output_path}")

    # Prepare content for generation
    if reference_url:
        # Check if it's a local file path or URL
        if reference_url.startswith('http://') or reference_url.startswith('https://'):
            print(f"Downloading reference image from: {reference_url}")
            with urlopen(reference_url) as response:
                reference_image = Image.open(BytesIO(response.read()))
        else:
            print(f"Loading reference image from: {reference_url}")
            reference_image = Image.open(reference_url)
        print(f"Reference image loaded: {reference_image.size}")
        content = [reference_image, prompt]
    else:
        content = f"Generate an image: {prompt}"

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
                    print(f"SUCCESS: Saved to {output_path}")
                    print(f"Size: {len(img_bytes):,} bytes")
                    return output_path

        print("ERROR: No image data in response")
        return None

    except Exception as e:
        print(f"ERROR generating image: {e}")
        return None


def upload_to_r2(local_path: Path, character: str) -> Optional[str]:
    """Upload generated image to R2."""
    r2_dest = f"{R2_BASE_PATH}/{character}/"
    print(f"\nUploading to R2: {r2_dest}")

    try:
        result = subprocess.run(
            ["rclone", "copy", str(local_path), r2_dest],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0:
            url = f"{R2_PUBLIC_BASE}/{character}/{local_path.name}"
            print(f"SUCCESS: Uploaded to {url}")
            return url
        else:
            print(f"ERROR uploading: {result.stderr}")
            return None
    except Exception as e:
        print(f"ERROR uploading: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description='Generate character turnaround sheets')
    parser.add_argument('--character', required=True, help='Character name (mia, leo, gabe, nina, etc)')
    parser.add_argument('--version', required=True, help='Version number/letter (2, 3, 4, v3a, etc)')
    parser.add_argument('--prompt', required=True, help='Generation prompt')
    parser.add_argument('--reference-url', help='Optional reference image URL for image-to-image')
    args = parser.parse_args()

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY environment variable not set")
        sys.exit(1)

    print("=" * 60)
    print(f"{args.character.upper()} Turnaround V{args.version} Generator")
    if args.reference_url:
        print("Mode: Image-to-image (with reference)")
    else:
        print("Mode: Text-to-image (from scratch)")
    print("=" * 60)

    # Generate the image
    output_path = generate_turnaround(
        character=args.character,
        version=args.version,
        prompt=args.prompt,
        reference_url=args.reference_url,
        api_key=api_key
    )

    if not output_path:
        print("\nFAILED: Could not generate image")
        sys.exit(1)

    # Upload to R2
    url = upload_to_r2(output_path, args.character)
    if url:
        print(f"\nDONE! View at: {url}")
    else:
        print(f"\nImage saved locally but R2 upload failed: {output_path}")
        sys.exit(1)


if __name__ == "__main__":
    main()
