#!/usr/bin/env python3
"""
Generate individual character views of Mia from the approved alt turnaround.

Uses Gemini 3.0 Pro image-to-image to extract/generate 4 separate views
(front, 3/4, side, rear) with 2 variations each = 8 images total.
"""

import io
import os
import subprocess
import sys
import time
from pathlib import Path

from google import genai
from google.genai import types
from PIL import Image

# Initialize client
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# Directories
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
OUTPUT_DIR = PROJECT_DIR / "output" / "individual-views"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Reference image
TURNAROUND_PATH = OUTPUT_DIR / "mia_turnaround_APPROVED_ALT.png"

# View definitions
VIEWS = [
    {
        "name": "front",
        "view_desc": "straight-on front",
        "detail": (
            "facing directly toward the camera. Both arms visible, symmetrical pose."
        ),
    },
    {
        "name": "threequarter",
        "view_desc": "three-quarter (turned about 45 degrees to her left)",
        "detail": (
            "turned about 45 degrees so we see her front and one side. "
            "The ponytail should be partially visible behind her head."
        ),
    },
    {
        "name": "side",
        "view_desc": "full side profile (facing left)",
        "detail": (
            "in a complete side profile view facing left. The ponytail with pink "
            "scrunchie should be clearly visible hanging behind her head."
        ),
    },
    {
        "name": "rear",
        "view_desc": "rear/back",
        "detail": (
            "from directly behind, showing her back. The ponytail with pink "
            "scrunchie should be prominently visible. We see the back of her "
            "outfit and shoes."
        ),
    },
]

NUM_VARIATIONS = 2
DELAY_BETWEEN_REQUESTS = 12  # seconds


def make_prompt(view: dict) -> str:
    """Build the generation prompt for a specific view."""
    return (
        f"Using this character turnaround sheet as reference, generate a single "
        f"high-quality image showing ONLY the {view['view_desc']} view of this "
        f"character, {view['detail']} "
        f"\n\n"
        f"She should be in A-pose (arms slightly away from body, fingers relaxed) "
        f"on a plain white background. Center the character in the frame. Show the "
        f"full body from head to feet with some padding around her.\n\n"
        f"Match the character EXACTLY from the turnaround sheet:\n"
        f"- Young girl, about 8 years old\n"
        f"- Brown skin with freckles on cheeks\n"
        f"- Dark brown/black hair in a simple wavy ponytail with pink scrunchie\n"
        f"- Hair swept back cleanly, no loose strands framing the face\n"
        f"- Pink t-shirt with a star design on the front\n"
        f"- Blue jeans\n"
        f"- Red sneakers\n"
        f"- Bright, friendly expression\n"
        f"- 3D animated Pixar-style cartoon character\n\n"
        f"IMPORTANT: Generate ONLY ONE view of the character. Do NOT create a "
        f"turnaround sheet or multiple views. Just this single {view['view_desc']} "
        f"view as one standalone image."
    )


def generate_view(turnaround: Image.Image, view: dict, var_num: int) -> Path | None:
    """Generate one variation of a specific view."""
    output_path = OUTPUT_DIR / f"mia_{view['name']}_var{var_num}.png"

    if output_path.exists():
        print(f"  Already exists: {output_path.name}, skipping")
        return output_path

    prompt = make_prompt(view)
    print(f"  Generating {output_path.name}...")

    try:
        response = client.models.generate_content(
            model="gemini-3-pro-image-preview",
            contents=[prompt, turnaround],
            config=types.GenerateContentConfig(
                response_modalities=["TEXT", "IMAGE"],
            ),
        )

        # Extract image from response
        if response.candidates:
            for part in response.candidates[0].content.parts:
                if part.inline_data and part.inline_data.mime_type.startswith("image/"):
                    img_data = part.inline_data.data
                    result_img = Image.open(io.BytesIO(img_data))

                    # Upscale if needed (target: at least 1040x1040)
                    min_dim = min(result_img.size)
                    if min_dim < 1040:
                        scale = 1040 / min_dim
                        new_w = int(result_img.width * scale)
                        new_h = int(result_img.height * scale)
                        result_img = result_img.resize(
                            (max(new_w, 1040), max(new_h, 1040)),
                            Image.LANCZOS,
                        )
                        print(f"    Upscaled to {result_img.size}")

                    result_img.save(output_path, "PNG")
                    print(f"    Saved: {output_path.name} ({result_img.size})")
                    return output_path

        print(f"    WARNING: No image in response for {output_path.name}")
        if response.candidates:
            for part in response.candidates[0].content.parts:
                if part.text:
                    print(f"    Response text: {part.text[:300]}")
        return None

    except Exception as e:
        print(f"    ERROR: {e}")
        return None


def upload_to_r2(local_path: Path, r2_prefix: str) -> str | None:
    """Upload a file to R2 and return public URL."""
    r2_dest = f"r2:rex-assets/{r2_prefix}"
    try:
        result = subprocess.run(
            ["rclone", "copy", str(local_path), r2_dest],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0:
            url = f"https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/{r2_prefix}{local_path.name}"
            return url
        else:
            print(f"    R2 upload error: {result.stderr}")
            return None
    except Exception as e:
        print(f"    R2 upload exception: {e}")
        return None


def main():
    print("=" * 60)
    print("Mia Individual Views - From Approved Alt Turnaround")
    print("=" * 60)

    if not TURNAROUND_PATH.exists():
        print(f"ERROR: Turnaround not found: {TURNAROUND_PATH}")
        print("Download it first from R2")
        sys.exit(1)

    turnaround = Image.open(TURNAROUND_PATH)
    print(f"Reference image: {turnaround.size}")

    results = []
    total_requests = len(VIEWS) * NUM_VARIATIONS
    current = 0

    for view in VIEWS:
        print(f"\n--- {view['name'].upper()} VIEW ---")
        for var in range(1, NUM_VARIATIONS + 1):
            current += 1
            print(f"[{current}/{total_requests}]")
            result = generate_view(turnaround, view, var)
            results.append((f"mia_{view['name']}_var{var}.png", result))

            if current < total_requests:
                print(f"  Waiting {DELAY_BETWEEN_REQUESTS}s for rate limit...")
                time.sleep(DELAY_BETWEEN_REQUESTS)

    # Summary
    print("\n" + "=" * 60)
    print("RESULTS:")
    print("=" * 60)

    success_paths = []
    for name, path in results:
        if path and path.exists():
            img = Image.open(path)
            print(f"  OK: {name} ({img.size})")
            success_paths.append(path)
        else:
            print(f"  FAILED: {name}")

    print(f"\n{len(success_paths)}/{len(results)} images generated successfully")

    # Upload to R2
    if success_paths:
        print("\n--- Uploading to R2 ---")
        r2_prefix = "characters/mia/individual-views/"
        urls = []
        for path in success_paths:
            print(f"  Uploading {path.name}...")
            url = upload_to_r2(path, r2_prefix)
            if url:
                urls.append(url)
                print(f"    -> {url}")
            else:
                print(f"    FAILED to upload {path.name}")

        print(f"\n{len(urls)}/{len(success_paths)} files uploaded to R2")
        print("\nPublic URLs:")
        for url in urls:
            print(f"  {url}")

    return len(success_paths) > 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
