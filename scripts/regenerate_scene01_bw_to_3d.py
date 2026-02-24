#!/usr/bin/env python3
"""
Regenerate Scene 1 B&W sketch panels as 3D Pixar renders.

Panels 01, 03, 05, 06 were originally B&W sketches.
Bruno decided all Scene 1 panels should be consistent 3D Pixar renders.
This script regenerates those 4 panels to match the style of
existing rendered panels (02, 04, 07, 08, 09).

Uses character reference turnarounds for consistency.
"""

import os
import sys
import time
import subprocess
from pathlib import Path

from google import genai
from google.genai import types
from PIL import Image
import io

# Configuration
MODEL = "gemini-2.5-flash-image"
DELAY_BETWEEN_REQUESTS = 12  # seconds

SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
CHAR_REF_DIR = PROJECT_DIR / "tmp" / "char-refs"
OUTPUT_DIR = PROJECT_DIR / "tmp" / "scene01-panels-3d"
R2_DEST = "r2:rex-assets/storyboards/act1/panels/"
R2_PUBLIC = "https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/storyboards/act1/panels"

# Also upload to scene-01 path for backward compat
R2_DEST_SCENE = "r2:rex-assets/storyboards/act1/scene-01/"
R2_PUBLIC_SCENE = "https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/storyboards/act1/scene-01"

# Character reference image paths (APPROVED turnarounds)
CHAR_REFS = {
    "mia": CHAR_REF_DIR / "mia_turnaround_APPROVED.png",
    "leo": CHAR_REF_DIR / "leo_turnaround_APPROVED.png",
    "nina": CHAR_REF_DIR / "nina_turnaround_APPROVED.png",
    "gabe": CHAR_REF_DIR / "gabe_turnaround_APPROVED.png",
}

# 3D Pixar render style (NOT B&W sketch) - matches existing rendered panels
STYLE_SUFFIX = (
    "Pixar-style 3D animated render, rich warm cinematic lighting, "
    "detailed textures, soft ambient occlusion, subsurface scattering on skin, "
    "professional animation quality, movie production still, "
    "16:9 widescreen aspect ratio, photorealistic Pixar rendering"
)

# The 4 panels that need regeneration from B&W sketch to 3D render
PANELS = [
    {
        "id": "01",
        "name": "Panel 1A: Wide Establishing Shot",
        "chars": ["mia", "leo"],
        "prompt": (
            "Wide establishing shot of a cozy suburban family living room in the evening. "
            "A 5-year-old boy with blonde curly hair in green dinosaur pajamas clutches a plush T-Rex toy, "
            "sitting cross-legged on the right side of a large couch. "
            "An 8-year-old girl with dark curly hair in a high ponytail sits on the left side of the couch, "
            "legs tucked under, looking slightly concerned. "
            "A 15-year-old babysitter with a blonde ponytail sits in an armchair to the far right, "
            "head down, completely absorbed in her phone. "
            "A TV glows on the left side of the room. Dinosaur toys are scattered on the floor. "
            "Through the windows, a dark stormy sky with lightning is visible outside. "
            "In the background, a mother in a black cocktail dress and father in a tuxedo "
            "are visible in the kitchen area getting ready to leave. "
            "Warm amber interior lighting contrasts with cold blue storm outside. "
        ),
    },
    {
        "id": "03",
        "name": "Panel 1C: Tracking Shot Nina",
        "chars": ["nina"],
        "prompt": (
            "Match this character EXACTLY - same face shape, same auburn wavy hair, same features. "
            "Generate a NEW image: Medium tracking shot of this elegant mother in a black cocktail dress, "
            "walking through the house while putting on earrings. She is multitasking - "
            "one hand putting in an earring while her other hand checks her purse. "
            "She moves gracefully from the living room toward the front door area. "
            "Her auburn/reddish-brown shoulder-length wavy hair catches the warm light. "
            "Frantic but graceful energy. Earrings glint in the warm interior lighting. "
            "Warm domestic lighting with slight motion blur suggesting movement. "
        ),
    },
    {
        "id": "05",
        "name": "Panel 1E: Close-up Jenny",
        "chars": [],  # No Jenny turnaround available
        "prompt": (
            "Close-up insert shot of a 15-year-old babysitter with a blonde ponytail. "
            "She sits in an armchair, head tilted down, completely absorbed in her phone screen. "
            "The phone's glow illuminates her face with a soft blue-white light. "
            "She has a cheerful but totally disconnected expression - oblivious to everything around her. "
            "Shallow depth of field with the background heavily blurred. "
            "She is texting rapidly, completely in her own world. "
            "Warm ambient living room light mixed with cool phone glow on her face. "
        ),
    },
    {
        "id": "06",
        "name": "Panel 1F: Close-up TV Flickering",
        "chars": [],  # No characters needed
        "prompt": (
            "Close-up of a TV screen filling most of the frame. "
            "A colorful cartoon is playing but it's being disrupted by static interference. "
            "Horizontal scan lines roll through the image creating distortion. "
            "A brief flash of eerie blue-white light emanates from the screen - subtle foreshadowing. "
            "A lightning flash from outside is reflected in the TV screen glass. "
            "The TV flickers and jitters slightly - something is not right. "
            "The surrounding room is visible at the edges, out of focus, dimly lit. "
        ),
    },
]


def image_to_part(img_path):
    """Convert an image file to a genai Part."""
    img = Image.open(img_path)
    # Resize if too large (max 4MP for Gemini)
    max_dim = 2048
    if max(img.size) > max_dim:
        ratio = max_dim / max(img.size)
        new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
        img = img.resize(new_size, Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    data = buf.getvalue()
    return types.Part.from_bytes(data=data, mime_type='image/png')


def generate_panel(panel, client, model_name):
    """Generate a single storyboard panel as a 3D Pixar render."""
    panel_id = panel["id"]
    panel_name = panel["name"]
    filename = f"scene-01-panel-{panel_id}.png"
    output_path = OUTPUT_DIR / filename

    print(f"\n{'='*60}")
    print(f"Generating {panel_name}")
    print(f"  File: {filename}")
    print(f"  Characters: {panel['chars'] or ['none']}")

    # Load character reference image parts
    ref_parts = []
    for name in panel["chars"]:
        path = CHAR_REFS.get(name)
        if path and path.exists():
            ref_parts.append(image_to_part(path))
            print(f"  Loaded ref: {name}")
        else:
            print(f"  WARNING: Missing ref for {name}")

    # Build the prompt with 3D Pixar style
    full_prompt = panel["prompt"] + STYLE_SUFFIX

    # Build content: reference images first, then prompt
    if ref_parts:
        ref_note = (
            "Use these character reference turnaround sheets to maintain consistent character designs. "
            "Match these exact characters - same face shapes, same features, same proportions. "
            "Render them in the scene described below as a 3D Pixar-style animation:\n\n"
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
                image_config=types.ImageConfig(
                    aspect_ratio="16:9",
                ),
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

        print(f"  FAILED: No image data in response")
        return None

    except Exception as e:
        print(f"  ERROR: {e}")
        return None


def upload_to_r2(local_path):
    """Upload a single file to both R2 destinations."""
    urls = []
    for dest, public_url in [(R2_DEST, R2_PUBLIC), (R2_DEST_SCENE, R2_PUBLIC_SCENE)]:
        try:
            result = subprocess.run(
                ["rclone", "copy", str(local_path), dest],
                capture_output=True, text=True, timeout=60
            )
            if result.returncode == 0:
                url = f"{public_url}/{local_path.name}"
                print(f"  Uploaded: {url}")
                urls.append(url)
            else:
                print(f"  Upload error to {dest}: {result.stderr}")
        except Exception as e:
            print(f"  Upload error: {e}")
    return urls


def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY not set")
        sys.exit(1)

    # Verify character refs exist
    print("Checking character references...")
    for name, path in CHAR_REFS.items():
        if path.exists():
            print(f"  {name}: OK ({path.name})")
        else:
            print(f"  {name}: MISSING ({path})")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Initialize client
    client = genai.Client(api_key=api_key)
    print(f"\nUsing model: {MODEL}")
    print(f"Style: 3D Pixar render (replacing B&W sketches)")
    print(f"Panels to regenerate: {', '.join(p['id'] for p in PANELS)}")

    # Generate panels
    results = {}
    total = len(PANELS)

    for i, panel in enumerate(PANELS):
        panel_id = panel["id"]
        result_path = generate_panel(panel, client, MODEL)
        results[panel_id] = result_path

        # Rate limiting
        if i < total - 1:
            print(f"\n  Waiting {DELAY_BETWEEN_REQUESTS}s for rate limit...")
            time.sleep(DELAY_BETWEEN_REQUESTS)

    # Upload successful panels
    print(f"\n{'='*60}")
    print("Uploading to R2...")
    all_urls = {}
    for panel_id, path in results.items():
        if path and path.exists():
            urls = upload_to_r2(path)
            if urls:
                all_urls[panel_id] = urls

    # Summary
    print(f"\n{'='*60}")
    print(f"SUMMARY: {len(all_urls)}/{total} panels generated and uploaded")
    print(f"{'='*60}")
    for panel_id, urls in sorted(all_urls.items()):
        print(f"  Panel {panel_id}:")
        for url in urls:
            print(f"    {url}")

    failed = [p["id"] for p in PANELS if p["id"] not in all_urls]
    if failed:
        print(f"\n  FAILED panels: {', '.join(failed)}")

    return 0 if len(all_urls) == total else 1


if __name__ == "__main__":
    sys.exit(main())
