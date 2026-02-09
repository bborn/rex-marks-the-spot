#!/usr/bin/env python3
"""Generate 3D models for Mia and Leo using TRELLIS (Microsoft) via HuggingFace Spaces."""

import os
import sys
import time
import shutil
from pathlib import Path
from PIL import Image
from gradio_client import Client, handle_file

OUTPUT_DIR = Path(__file__).parent.parent / "output" / "3d-models"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def extract_front_view(turnaround_path: str, output_path: str):
    """Extract the front-facing view from a turnaround sheet.

    Turnaround sheets typically have 4 views arranged left to right:
    front, side, back, 3/4 view (or similar).
    We take the leftmost (front) view.
    """
    img = Image.open(turnaround_path)
    w, h = img.size

    # The turnaround has 4 views side by side
    # Front view is the first quarter
    quarter_w = w // 4

    # Crop the front view (first quarter, with some padding)
    front = img.crop((0, 0, quarter_w, h))

    # Also create a slightly wider crop in case the front view needs more context
    front_wide = img.crop((0, 0, int(quarter_w * 1.1), h))

    front.save(output_path)
    print(f"Extracted front view: {output_path} ({front.size[0]}x{front.size[1]})")
    return output_path


def generate_3d_with_trellis(image_path: str, character_name: str):
    """Generate a 3D model using TRELLIS via HuggingFace Spaces."""
    print(f"\n{'='*60}")
    print(f"Generating 3D model for {character_name}")
    print(f"Input image: {image_path}")
    print(f"{'='*60}")

    client = Client("JeffreyXiang/TRELLIS")

    # Step 1: Start session
    print("Starting session...")
    session_result = client.predict(api_name="/start_session")
    print(f"Session started")

    # Step 2: Preprocess image
    print("Preprocessing image...")
    preprocess_result = client.predict(
        image=handle_file(image_path),
        api_name="/preprocess_image"
    )
    print(f"Image preprocessed")

    # Step 3: Get seed
    print("Getting seed...")
    seed = client.predict(
        randomize_seed=True,
        seed=42,
        api_name="/get_seed"
    )
    print(f"Seed: {seed}")

    # Step 4: Generate 3D from image
    print("Generating 3D model (this may take a while)...")
    start_time = time.time()

    result = client.predict(
        image=handle_file(image_path),
        multiimages=[],
        seed=seed if isinstance(seed, int) else 42,
        ss_guidance_strength=7.5,
        ss_sampling_steps=12,
        slat_guidance_strength=3.0,
        slat_sampling_steps=12,
        multiimage_algo="stochastic",
        api_name="/image_to_3d"
    )

    elapsed = time.time() - start_time
    print(f"3D generation completed in {elapsed:.1f}s")
    print(f"Result: {result}")

    # Step 5: Extract GLB
    print("Extracting GLB model...")
    glb_result = client.predict(
        mesh_simplify=0.95,
        texture_size=1024,
        api_name="/extract_glb"
    )
    print(f"GLB extraction result: {glb_result}")

    # Copy the GLB file to our output directory
    output_glb = OUTPUT_DIR / f"{character_name}.glb"
    if isinstance(glb_result, (list, tuple)):
        glb_path = glb_result[0] if len(glb_result) > 0 else glb_result
    else:
        glb_path = glb_result

    # Handle dict result (gradio sometimes returns dict with 'value' key)
    if isinstance(glb_path, dict):
        glb_path = glb_path.get('value', glb_path.get('path', str(glb_path)))

    glb_path = str(glb_path)

    if os.path.exists(glb_path):
        shutil.copy2(glb_path, output_glb)
        file_size = os.path.getsize(output_glb)
        print(f"Saved GLB: {output_glb} ({file_size / 1024:.1f} KB)")
    else:
        print(f"Warning: GLB file not found at {glb_path}")
        # Try to find it in temp directories
        import glob
        for pattern in ['/tmp/gradio*/**/*.glb', '/tmp/**/*.glb']:
            found = glob.glob(pattern, recursive=True)
            if found:
                latest = max(found, key=os.path.getmtime)
                shutil.copy2(latest, output_glb)
                print(f"Found and saved GLB: {output_glb}")
                break

    return str(output_glb)


def main():
    characters = {
        "mia": {
            "turnaround": OUTPUT_DIR / "mia_turnaround.png",
            "description": "Mia, 8-year-old girl, curly dark hair with ponytail, pink polka-dot shirt, blue jeans, red sneakers",
        },
        "leo": {
            "turnaround": OUTPUT_DIR / "leo_turnaround.png",
            "description": "Leo, 5-year-old boy, curly blonde hair, green t-shirt, cargo pants, red sneakers, holding toy dinosaur",
        },
    }

    results = {}

    for name, info in characters.items():
        turnaround_path = str(info["turnaround"])

        if not os.path.exists(turnaround_path):
            print(f"Error: Turnaround not found: {turnaround_path}")
            continue

        # Extract front view
        front_view_path = str(OUTPUT_DIR / f"{name}_front.png")
        extract_front_view(turnaround_path, front_view_path)

        # Generate 3D model
        try:
            glb_path = generate_3d_with_trellis(front_view_path, name)
            results[name] = glb_path
            print(f"\nSuccess: {name} -> {glb_path}")
        except Exception as e:
            print(f"\nError generating {name}: {e}")
            import traceback
            traceback.print_exc()

        # Brief pause between generations
        if len(characters) > 1:
            print("\nWaiting 5 seconds before next generation...")
            time.sleep(5)

    print(f"\n{'='*60}")
    print("Generation Summary:")
    print(f"{'='*60}")
    for name, path in results.items():
        exists = os.path.exists(path)
        size = os.path.getsize(path) if exists else 0
        print(f"  {name}: {path} ({'OK' if exists else 'MISSING'}, {size/1024:.1f} KB)")

    return results


if __name__ == "__main__":
    main()
