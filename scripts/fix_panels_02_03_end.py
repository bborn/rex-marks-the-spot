#!/usr/bin/env python3
"""Regenerate panel 02-end and 03-end to match their start frame compositions."""

import os
import subprocess
import time
from pathlib import Path

from google import genai
from google.genai import types
from PIL import Image

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

ASSET_DIR = Path.home() / "rex-marks-the-spot" / "assets" / "storyboards" / "v2" / "scene-01"
OUTPUT_DIR = Path(__file__).parent.parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

ENV_REF = ASSET_DIR / "scene-01-panel-01-start.png"
CHAR_DIR = Path("/tmp/char-refs")


def load_image(path: Path) -> types.Part:
    data = path.read_bytes()
    return types.Part.from_bytes(data=data, mime_type="image/png")


def crop_to_16_9(img_path: Path):
    img = Image.open(img_path)
    w, h = img.size
    target_ratio = 16 / 9
    current_ratio = w / h
    if current_ratio > target_ratio:
        new_w = int(h * target_ratio)
        left = (w - new_w) // 2
        img = img.crop((left, 0, left + new_w, h))
    elif current_ratio < target_ratio:
        new_h = int(w / target_ratio)
        top = (h - new_h) // 2
        img = img.crop((0, top, w, top + new_h))
    img.save(img_path)
    print(f"  Cropped to {img.size[0]}x{img.size[1]}")


def generate_panel(name: str, prompt: str, ref_images: list[Path], output_name: str):
    print(f"\n=== Generating {name} ===")
    parts = []
    for ref in ref_images:
        print(f"  Input ref: {ref.name}")
        parts.append(load_image(ref))
    parts.append(prompt)

    response = client.models.generate_content(
        model="gemini-2.5-flash-image",
        contents=parts,
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE", "TEXT"],
        ),
    )

    output_path = OUTPUT_DIR / output_name
    for part in response.candidates[0].content.parts:
        if part.inline_data is not None:
            output_path.write_bytes(part.inline_data.data)
            print(f"  Saved: {output_path}")
            crop_to_16_9(output_path)
            return output_path

    raise RuntimeError(f"No image in response for {name}")


def upload_to_r2(local_path: Path, r2_path: str):
    cmd = ["rclone", "copyto", str(local_path), f"r2:rex-assets/{r2_path}"]
    print(f"  Uploading to r2:rex-assets/{r2_path}")
    subprocess.run(cmd, check=True)
    print(f"  Done: https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/{r2_path}")


def main():
    # Panel 02 end - Leo on couch
    p02_start = ASSET_DIR / "scene-01-panel-02-start.png"
    leo_ref = CHAR_DIR / "leo_turnaround_APPROVED.png"
    p02_prompt = (
        "Generate an image matching this EXACT same composition, camera angle, and framing. "
        "Same boy, same couch, same room, same camera distance. "
        "The ONLY change is: the boy looks down at small toy dinosaurs beside him on the couch "
        "with a gentle smile, instead of looking forward. Everything else stays identical. "
        "Do NOT render any text, words, letters, or dialogue into the image."
    )
    p02_out = generate_panel(
        "Panel 02 end",
        p02_prompt,
        [leo_ref, ENV_REF, p02_start],
        "scene-01-panel-02-end.png",
    )
    upload_to_r2(p02_out, "storyboards/v2/scene-01/scene-01-panel-02-end.png")

    # Copy to assets dir too
    subprocess.run(["cp", str(p02_out), str(ASSET_DIR / "scene-01-panel-02-end.png")], check=True)

    print("\nWaiting 10s for rate limit...")
    time.sleep(10)

    # Panel 03 end - Nina in black dress
    p03_start = ASSET_DIR / "scene-01-panel-03-start.png"
    nina_ref = CHAR_DIR / "nina_turnaround_APPROVED.png"
    p03_prompt = (
        "Generate an image matching this same woman with the same BLACK dress, same DARK BROWN "
        "hair color, same appearance. The ONLY change is: she is now near the front door area "
        "of the living room, checking her purse with slight urgency. Same room, same lighting, "
        "same character appearance. "
        "Do NOT render any text, words, letters, or dialogue into the image."
    )
    p03_out = generate_panel(
        "Panel 03 end",
        p03_prompt,
        [nina_ref, ENV_REF, p03_start],
        "scene-01-panel-03-end.png",
    )
    upload_to_r2(p03_out, "storyboards/v2/scene-01/scene-01-panel-03-end.png")

    subprocess.run(["cp", str(p03_out), str(ASSET_DIR / "scene-01-panel-03-end.png")], check=True)

    print("\n=== All panels generated and uploaded! ===")


if __name__ == "__main__":
    main()
