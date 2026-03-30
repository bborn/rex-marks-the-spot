#!/usr/bin/env python3
"""Generate start frames for video-first pipeline using Gemini image generation."""

import os
import time
import base64
from pathlib import Path
from google import genai
from google.genai import types

OUTDIR = Path(__file__).parent
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

# Try models in order of preference
MODELS = [
    "gemini-2.5-flash-preview-image-generation",
    "gemini-2.5-flash-image",
    "gemini-2.0-flash-exp-image-generation",
]

def load_image(path):
    """Load image as PIL for Gemini."""
    with open(path, "rb") as f:
        return types.Part.from_bytes(data=f.read(), mime_type="image/png")

def generate_image(prompt, reference_images=None, output_path=None, model_idx=0):
    """Generate an image with Gemini, trying models in order."""
    if model_idx >= len(MODELS):
        raise RuntimeError("All models failed")

    model = MODELS[model_idx]
    print(f"Using model: {model}")

    contents = []
    if reference_images:
        for img_path, label in reference_images:
            contents.append(f"Reference image ({label}):")
            contents.append(load_image(img_path))
    contents.append(prompt)

    try:
        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
            ),
        )

        # Extract image from response
        for part in response.candidates[0].content.parts:
            if part.inline_data and part.inline_data.mime_type.startswith("image/"):
                with open(output_path, "wb") as f:
                    f.write(part.inline_data.data)
                print(f"Saved: {output_path} ({os.path.getsize(output_path)} bytes)")
                return True

        print(f"No image in response. Text: {response.text if hasattr(response, 'text') else 'none'}")
        return False

    except Exception as e:
        print(f"Model {model} failed: {e}")
        if "not found" in str(e).lower() or "not supported" in str(e).lower() or "invalid" in str(e).lower():
            print(f"Trying next model...")
            time.sleep(2)
            return generate_image(prompt, reference_images, output_path, model_idx + 1)
        raise

mia_path = OUTDIR / "mia_turnaround.png"
leo_path = OUTDIR / "leo_turnaround.png"

# STEP 2: Hero establishing shot
print("=" * 60)
print("STEP 2: Generating HERO establishing shot")
print("=" * 60)

hero_prompt = (
    "Pixar 3D animation style, wide establishing shot of a cozy suburban living room, evening. "
    "Warm amber interior lighting. TV on left side flickering showing colorful cartoon. "
    "Large couch center-left. Two children on couch: an 8-year-old girl with dark hair in a ponytail "
    "wearing pajamas (Mia, use reference image) and a 5-year-old boy in green dinosaur pajamas "
    "(Leo, use reference image). Teenage babysitter with dark brown curly hair and coral hoodie in "
    "armchair on right, looking at phone. Dinosaur toys scattered on floor. Storm clouds visible "
    "through windows. No text in the image. 16:9 aspect ratio."
)

success = generate_image(
    hero_prompt,
    reference_images=[(str(mia_path), "Mia"), (str(leo_path), "Leo")],
    output_path=str(OUTDIR / "hero_establishing.png"),
)

if not success:
    print("FAILED to generate hero shot")
    exit(1)

# STEP 3: Copy hero as 1A start
import shutil
shutil.copy(OUTDIR / "hero_establishing.png", OUTDIR / "panel-1A-start.png")
print(f"\nSTEP 3: Copied hero as panel-1A-start.png")

# Wait for rate limit
print("\nWaiting 10s for rate limit...")
time.sleep(10)

# STEP 4: Panel 1B START
print("=" * 60)
print("STEP 4: Generating Panel 1B START")
print("=" * 60)

panel_1b_prompt = (
    "Pixar 3D animation style, medium shot of Leo (5-year-old boy in green dinosaur pajamas, "
    "use reference) sitting cross-legged on the SAME couch from the reference image. He is hugging "
    "a plush T-Rex toy. Multiple plastic dinosaur toys around him on the couch. Mia partially "
    "visible at frame edge. TV glow on his face, content expression. SAME living room as the "
    "reference image - same walls, same furniture, same lighting. No text. 16:9 aspect ratio."
)

success = generate_image(
    panel_1b_prompt,
    reference_images=[
        (str(OUTDIR / "hero_establishing.png"), "the hero establishing shot - match this room"),
        (str(leo_path), "Leo character reference"),
    ],
    output_path=str(OUTDIR / "panel-1B-start.png"),
)

if not success:
    print("FAILED to generate 1B start")
    exit(1)

# Wait for rate limit
print("\nWaiting 10s for rate limit...")
time.sleep(10)

# STEP 5: Panel 1G START
print("=" * 60)
print("STEP 5: Generating Panel 1G START")
print("=" * 60)

panel_1g_prompt = (
    "Pixar 3D animation style, over-the-shoulder shot from behind the two children sitting on the "
    "SAME couch from the reference image. We see backs of their heads - Mia with dark ponytail on "
    "left, Leo in green dino pajamas on right. They look at the TV. Parents visible in background "
    "preparing to leave. SAME living room as reference - same walls, same furniture, same lighting. "
    "No text. 16:9 aspect ratio."
)

success = generate_image(
    panel_1g_prompt,
    reference_images=[
        (str(OUTDIR / "hero_establishing.png"), "the hero establishing shot - match this room"),
        (str(mia_path), "Mia character reference"),
        (str(leo_path), "Leo character reference"),
    ],
    output_path=str(OUTDIR / "panel-1G-start.png"),
)

if not success:
    print("FAILED to generate 1G start")
    exit(1)

print("\n" + "=" * 60)
print("All start frames generated successfully!")
print("=" * 60)
