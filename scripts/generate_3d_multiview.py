#!/usr/bin/env python3
"""Generate 3D models using TRELLIS multi-view pipeline."""

import os
import sys
import time
import shutil
import glob
from pathlib import Path
from gradio_client import Client, handle_file

OUTPUT_DIR = Path(__file__).parent.parent / "output" / "3d-models"


def generate_multiview(character_name: str, front_image: str, extra_images: list):
    """Generate 3D model using multi-view inputs."""
    print(f"\n{'='*60}")
    print(f"MULTI-VIEW 3D GENERATION: {character_name.upper()}")
    print(f"Front: {front_image}")
    print(f"Extra views: {len(extra_images)}")
    print(f"{'='*60}")

    output_glb = OUTPUT_DIR / f"{character_name}_multiview.glb"

    client = Client("JeffreyXiang/TRELLIS")
    print("Connected to TRELLIS")

    # Step 1: Start session
    print("[1/5] Starting session...")
    client.predict(api_name="/start_session")

    # Step 2: Preprocess multiple images
    print("[2/5] Preprocessing images...")
    multi_files = [handle_file(p) for p in extra_images]
    client.predict(
        images=multi_files,
        api_name="/preprocess_images"
    )

    # Step 3: Seed
    print("[3/5] Getting seed...")
    seed = client.predict(randomize_seed=False, seed=42, api_name="/get_seed")

    # Step 4: Generate 3D with multi-view
    print("[4/5] Generating 3D model with multi-view...")
    t0 = time.time()
    result = client.predict(
        image=handle_file(front_image),
        multiimages=multi_files,
        seed=seed if isinstance(seed, int) else 42,
        ss_guidance_strength=7.5,
        ss_sampling_steps=12,
        slat_guidance_strength=3.0,
        slat_sampling_steps=12,
        multiimage_algo="stochastic",
        api_name="/image_to_3d"
    )
    elapsed = time.time() - t0
    print(f"  Generated in {elapsed:.1f}s")

    # Save preview
    if isinstance(result, dict) and "video" in result:
        video_path = result["video"]
        if os.path.exists(str(video_path)):
            shutil.copy2(str(video_path), OUTPUT_DIR / f"{character_name}_multiview_preview.mp4")

    # Step 5: Extract GLB
    print("[5/5] Extracting GLB...")
    t0 = time.time()
    glb_result = client.predict(
        mesh_simplify=0.95,
        texture_size=1024,
        api_name="/extract_glb"
    )
    elapsed = time.time() - t0
    print(f"  Extracted in {elapsed:.1f}s")
    print(f"  Result: {str(glb_result)[:300]}")

    # Save GLB
    glb_path = None
    if isinstance(glb_result, (list, tuple)):
        for item in glb_result:
            s = str(item)
            if s.endswith(".glb") or "/gradio/" in s:
                glb_path = s
                break
        if not glb_path and glb_result:
            glb_path = str(glb_result[0])
    elif isinstance(glb_result, dict):
        glb_path = str(glb_result.get("value", glb_result.get("path", "")))
    else:
        glb_path = str(glb_result)

    if glb_path and os.path.exists(glb_path):
        shutil.copy2(glb_path, output_glb)
        print(f"  SAVED: {output_glb} ({os.path.getsize(output_glb)/1024:.1f} KB)")
        return str(output_glb)
    else:
        recent = sorted(glob.glob("/tmp/gradio*/**/*.glb", recursive=True),
                       key=os.path.getmtime, reverse=True)
        if recent:
            shutil.copy2(recent[0], output_glb)
            print(f"  SAVED (found): {output_glb} ({os.path.getsize(output_glb)/1024:.1f} KB)")
            return str(output_glb)

    print("  ERROR: No GLB found!")
    return None


def main():
    characters = {
        "mia": {
            "front": str(OUTPUT_DIR / "mia_view_0.png"),
            "views": [str(OUTPUT_DIR / f"mia_view_{i}.png") for i in range(4)],
        },
        "leo": {
            "front": str(OUTPUT_DIR / "leo_view_0.png"),
            "views": [str(OUTPUT_DIR / f"leo_view_{i}.png") for i in range(4)],
        },
    }

    results = {}
    for name, info in characters.items():
        try:
            glb = generate_multiview(name, info["front"], info["views"])
            results[name] = glb
        except Exception as e:
            print(f"ERROR: {name}: {e}")
            import traceback
            traceback.print_exc()
            results[name] = None

        if name != list(characters.keys())[-1]:
            print("\nWaiting 10s...")
            time.sleep(10)

    print(f"\n{'='*60}")
    print("RESULTS")
    for name, path in results.items():
        if path and os.path.exists(path):
            print(f"  {name}: {os.path.getsize(path)/1024:.1f} KB -> {path}")
        else:
            print(f"  {name}: FAILED")


if __name__ == "__main__":
    main()
