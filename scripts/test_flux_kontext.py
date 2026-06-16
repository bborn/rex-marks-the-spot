#!/usr/bin/env python3
"""Test Flux Kontext for character consistency with Mia turnaround."""

import os
import replicate
import urllib.request
import time

# REPLICATE_API_TOKEN must be set in the environment (e.g. via ~/.bashrc)

INPUT_IMAGE = "/tmp/flux-kontext-test/mia_turnaround.png"
OUTPUT_DIR = "/tmp/flux-kontext-test/output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

PANELS = [
    (
        "panel_a",
        "Using the character shown in the input image as reference for Mia's appearance: "
        "Mia sitting on a cozy living room couch playing with toy dinosaurs, warm evening lighting, "
        "Pixar 3D animation style, cinematic composition, 16:9 aspect ratio",
    ),
    (
        "panel_b",
        "Using the character shown in the input image as reference for Mia's appearance: "
        "Mia standing up excitedly from the couch with arms raised in joy, same cozy living room, "
        "warm evening lighting, Pixar 3D animation style, cinematic composition, 16:9 aspect ratio",
    ),
    (
        "panel_c",
        "Using the character shown in the input image as reference for Mia's appearance: "
        "Close-up of Mia looking up at someone with a hopeful expression, warm lamp light on her face, "
        "soft bokeh background, Pixar 3D animation style, cinematic composition, 16:9 aspect ratio",
    ),
    (
        "panel_d",
        "Using the character shown in the input image as reference for Mia's appearance: "
        "Mia and a younger boy named Leo (blonde hair, green dinosaur pajamas) sitting together on the couch "
        "watching TV, blue TV glow illuminating their faces, cozy living room, Pixar 3D animation style, "
        "cinematic composition, 16:9 aspect ratio",
    ),
    (
        "panel_e",
        "Using the character shown in the input image as reference for Mia's appearance: "
        "Mia hugging her dad (tall man in dark suit, glasses, soft around middle) goodbye near the front door, "
        "warm hallway lighting, emotional moment, Pixar 3D animation style, cinematic composition, 16:9 aspect ratio",
    ),
]

MODEL = "black-forest-labs/flux-kontext-dev"


def generate_panel(name: str, prompt: str) -> str:
    """Generate a single panel and save it."""
    print(f"\n{'='*60}")
    print(f"Generating {name}...")
    print(f"Prompt: {prompt[:80]}...")

    with open(INPUT_IMAGE, "rb") as f:
        output = replicate.run(
            MODEL,
            input={
                "prompt": prompt,
                "input_image": f,
                "aspect_ratio": "16:9",
                "num_inference_steps": 28,
                "guidance_scale": 3.5,
            },
        )

    # Output could be a URL string or FileOutput
    if hasattr(output, "url"):
        url = output.url
    elif isinstance(output, str):
        url = output
    else:
        url = str(output)

    out_path = os.path.join(OUTPUT_DIR, f"{name}.png")
    print(f"Downloading result from: {url}")
    urllib.request.urlretrieve(url, out_path)
    size = os.path.getsize(out_path)
    print(f"Saved {out_path} ({size} bytes)")
    return out_path


def main():
    print("Flux Kontext Character Consistency Test")
    print(f"Model: {MODEL}")
    print(f"Input image: {INPUT_IMAGE}")
    print(f"Output dir: {OUTPUT_DIR}")

    results = []
    for name, prompt in PANELS:
        path = generate_panel(name, prompt)
        results.append(path)
        time.sleep(2)  # small delay between requests

    print(f"\n{'='*60}")
    print("All panels generated:")
    for p in results:
        print(f"  {p}")
    print("\nReady for upload to R2.")


if __name__ == "__main__":
    main()
