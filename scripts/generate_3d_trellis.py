#!/usr/bin/env python3
"""Generate 3D models for Mia and Leo using TRELLIS via HuggingFace Spaces.
Full pipeline in a single session per character."""

import os
import sys
import time
import shutil
import glob
from pathlib import Path

from gradio_client import Client, handle_file

OUTPUT_DIR = Path(__file__).parent.parent / "output" / "3d-models"


def generate_character(image_path: str, character_name: str):
    """Generate a complete 3D GLB model for one character."""
    print(f"\n{'='*60}")
    print(f"GENERATING 3D MODEL: {character_name.upper()}")
    print(f"Image: {image_path}")
    print(f"{'='*60}")

    output_glb = OUTPUT_DIR / f"{character_name}.glb"

    # Connect fresh for each character
    print("Connecting to TRELLIS...")
    client = Client("JeffreyXiang/TRELLIS")
    print("Connected!")

    # Step 1: Start session
    print("[1/5] Starting session...")
    client.predict(api_name="/start_session")

    # Step 2: Preprocess image
    print("[2/5] Preprocessing image...")
    client.predict(
        image=handle_file(image_path),
        api_name="/preprocess_image"
    )

    # Step 3: Get seed
    print("[3/5] Getting seed...")
    seed = client.predict(
        randomize_seed=False,
        seed=42,
        api_name="/get_seed"
    )
    print(f"  Seed: {seed}")

    # Step 4: Image to 3D
    print("[4/5] Generating 3D model (takes 15-60 seconds)...")
    t0 = time.time()
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
    elapsed = time.time() - t0
    print(f"  3D generated in {elapsed:.1f}s")

    # Save the preview video if available
    if isinstance(result, dict) and "video" in result:
        video_path = result["video"]
        if os.path.exists(str(video_path)):
            preview_dest = OUTPUT_DIR / f"{character_name}_preview.mp4"
            shutil.copy2(str(video_path), preview_dest)
            print(f"  Preview video saved: {preview_dest}")

    # Step 5: Extract GLB
    print("[5/5] Extracting GLB model...")
    t0 = time.time()
    glb_result = client.predict(
        mesh_simplify=0.95,
        texture_size=1024,
        api_name="/extract_glb"
    )
    elapsed = time.time() - t0
    print(f"  GLB extracted in {elapsed:.1f}s")
    print(f"  Result: {str(glb_result)[:300]}")

    # Parse result to find the GLB file path
    glb_path = None
    if isinstance(glb_result, (list, tuple)):
        # Could be (filepath, download_path) tuple
        for item in glb_result:
            item_str = str(item)
            if item_str.endswith(".glb") or "/gradio/" in item_str:
                glb_path = item_str
                break
        if not glb_path and glb_result:
            glb_path = str(glb_result[0])
    elif isinstance(glb_result, dict):
        glb_path = glb_result.get("value", glb_result.get("path", ""))
        if isinstance(glb_path, dict):
            glb_path = glb_path.get("path", str(glb_path))
    else:
        glb_path = str(glb_result)

    # Try to copy the GLB file
    if glb_path and os.path.exists(str(glb_path)):
        shutil.copy2(str(glb_path), output_glb)
        size_kb = os.path.getsize(output_glb) / 1024
        print(f"  SAVED: {output_glb} ({size_kb:.1f} KB)")
        return str(output_glb)
    else:
        print(f"  GLB path not directly accessible: {glb_path}")
        # Search for recently created GLB files
        recent_glbs = sorted(
            glob.glob("/tmp/gradio*/**/*.glb", recursive=True),
            key=os.path.getmtime,
            reverse=True
        )
        if recent_glbs:
            latest = recent_glbs[0]
            shutil.copy2(latest, output_glb)
            size_kb = os.path.getsize(output_glb) / 1024
            print(f"  Found and saved GLB: {output_glb} ({size_kb:.1f} KB)")
            return str(output_glb)
        else:
            print("  ERROR: No GLB files found!")
            return None


def main():
    characters = [
        ("mia", str(OUTPUT_DIR / "mia_front.png")),
        ("leo", str(OUTPUT_DIR / "leo_front.png")),
    ]

    results = {}
    for name, img_path in characters:
        if not os.path.exists(img_path):
            print(f"ERROR: Image not found: {img_path}")
            continue

        try:
            glb_path = generate_character(img_path, name)
            results[name] = glb_path
        except Exception as e:
            print(f"ERROR generating {name}: {e}")
            import traceback
            traceback.print_exc()
            results[name] = None

        # Pause between characters
        if name != characters[-1][0]:
            print("\nWaiting 10s before next character...")
            time.sleep(10)

    # Summary
    print(f"\n{'='*60}")
    print("GENERATION SUMMARY")
    print(f"{'='*60}")
    for name, path in results.items():
        if path and os.path.exists(path):
            size = os.path.getsize(path) / 1024
            print(f"  {name}: OK ({size:.1f} KB) -> {path}")
        else:
            print(f"  {name}: FAILED")

    return results


if __name__ == "__main__":
    main()
