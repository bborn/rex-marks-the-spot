#!/usr/bin/env python3
"""Fix Panel 02 end - match medium shot framing of panel 02 start."""

import os
import sys
import io
import subprocess
from pathlib import Path

from google import genai
from google.genai import types
from PIL import Image

MODEL = "gemini-2.5-flash-image"
CHAR_REF_DIR = Path("/tmp/char-refs")
OUTPUT_DIR = Path.home() / "rex-marks-the-spot" / "assets" / "storyboards" / "v2" / "scene-01"
ENV_REF = OUTPUT_DIR / "scene-01-panel-01-start.png"
START_REF = OUTPUT_DIR / "scene-01-panel-02-start.png"  # Use the start panel as composition ref

def image_to_part(img_path):
    img = Image.open(img_path)
    max_dim = 2048
    if max(img.size) > max_dim:
        ratio = max_dim / max(img.size)
        new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
        img = img.resize(new_size, Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return types.Part.from_bytes(data=buf.getvalue(), mime_type='image/png')

def crop_to_16_9(img_path):
    img = Image.open(img_path)
    w, h = img.size
    target = 16 / 9
    if abs(w/h - target) < 0.01:
        return
    if w/h > target:
        new_w = int(h * target)
        left = (w - new_w) // 2
        img = img.crop((left, 0, left + new_w, h))
    else:
        new_h = int(w / target)
        top = (h - new_h) // 2
        img = img.crop((0, top, w, top + new_h))
    img.save(img_path)
    print(f"  Cropped to 16:9: {img.size[0]}x{img.size[1]}")

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

env_part = image_to_part(ENV_REF)
start_part = image_to_part(START_REF)
leo_part = image_to_part(CHAR_REF_DIR / "leo_turnaround_APPROVED.png")

prompt = (
    "The SECOND reference image shows the EXACT composition, camera angle, and framing to match. "
    "Generate a new image with the SAME medium shot, SAME camera distance, SAME couch, SAME background. "
    "The boy (Leo) is in the SAME position on the couch but now glances DOWN at small dinosaur toys "
    "beside him with a slight smile. "
    "He has blonde curly hair and wears green dinosaur pajamas. He holds a plush T-Rex in one arm. "
    "CRITICAL: Match the EXACT same camera distance and framing as the second reference - "
    "medium shot showing the boy from waist up with couch and living room background visible. "
    "Do NOT zoom in closer. Do NOT make this a close-up. Keep the same wide-ish medium shot. "
    "Do NOT render any text, words, letters, or dialogue into the image. "
    "Do NOT add any UI elements or subtitles. "
    "Pixar-style 3D animated render, rich warm cinematic lighting, 16:9 widescreen."
)

content = [
    env_part,
    start_part,
    leo_part,
    types.Part.from_text(text=(
        "First image: environment reference (living room). "
        "Second image: COMPOSITION REFERENCE - match this exact framing and camera distance. "
        "Third image: character turnaround sheet for Leo. "
        "Generate the scene below:\n\n" + prompt
    )),
]

output_path = OUTPUT_DIR / "scene-01-panel-02-end.png"

for attempt in range(3):
    print(f"Attempt {attempt+1}/3...")
    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=content,
            config=types.GenerateContentConfig(response_modalities=["IMAGE", "TEXT"]),
        )
        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                with open(output_path, "wb") as f:
                    f.write(part.inline_data.data)
                print(f"  Saved: {output_path}")
                crop_to_16_9(output_path)
                # Upload
                subprocess.run(f"rclone copy {output_path} r2:rex-assets/storyboards/v2/scene-01/",
                             shell=True, check=True)
                print("  Uploaded to R2")
                sys.exit(0)
        print("  No image in response")
    except Exception as e:
        print(f"  Error: {e}")
    import time; time.sleep(10)

print("Failed after 3 attempts")
sys.exit(1)
