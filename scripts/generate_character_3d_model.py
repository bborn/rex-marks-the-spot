#!/usr/bin/env python3
"""Generate 3D character models from turnaround sheets using Hunyuan3D-2.

Uses the Tencent/Hunyuan3D-2 HuggingFace Space to generate 3D mesh models
from character concept art/turnaround sheets.

Usage:
    python scripts/generate_character_3d_model.py <character_name> <image_path> [output_dir]

Example:
    python scripts/generate_character_3d_model.py gabe output/gabe_front.png output/3d-models/
"""

import sys
import os
import time
import shutil
import subprocess
from pathlib import Path

try:
    from gradio_client import Client, handle_file
except ImportError:
    print("Installing gradio_client...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "gradio_client"])
    from gradio_client import Client, handle_file

try:
    from PIL import Image
except ImportError:
    print("Installing Pillow...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
    from PIL import Image


R2_BASE = "r2:rex-assets/3d-models/characters"
R2_PUBLIC = "https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/3d-models/characters"


def extract_front_view(turnaround_path: str, output_path: str) -> str:
    """Extract the front view from a 4-view turnaround sheet."""
    img = Image.open(turnaround_path)
    w, h = img.size

    # Front view is the leftmost quarter
    view_w = w // 4
    front = img.crop((0, 0, view_w, h))

    # Make square with white background
    max_dim = max(front.size)
    square = Image.new("RGB", (max_dim, max_dim), (255, 255, 255))
    offset_x = (max_dim - front.size[0]) // 2
    offset_y = (max_dim - front.size[1]) // 2
    square.paste(front, (offset_x, offset_y))
    square = square.resize((512, 512), Image.LANCZOS)
    square.save(output_path)
    return output_path


def generate_shape(client, character_name: str, image_path: str, caption: str = ""):
    """Generate a 3D shape model from a character image."""
    print(f"Generating shape for {character_name}...")
    start = time.time()

    result = client.predict(
        caption=caption,
        image=handle_file(image_path),
        mv_image_front=None,
        mv_image_back=None,
        mv_image_left=None,
        mv_image_right=None,
        steps=30,
        guidance_scale=5.0,
        seed=42,
        octree_resolution=256,
        check_box_rembg=True,
        num_chunks=8000,
        randomize_seed=False,
        api_name="/shape_generation",
    )

    elapsed = time.time() - start
    print(f"Shape generation complete in {elapsed:.1f}s")

    shape_file = result[0]
    mesh_stats = result[2] if len(result) > 2 else {}
    path = shape_file.get("value", shape_file) if isinstance(shape_file, dict) else shape_file

    return str(path), mesh_stats


def decimate_model(input_glb: str, output_glb: str, ratio: float = 0.10):
    """Decimate a GLB model using Blender headless."""
    script = f"""
import bpy, os
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()
bpy.ops.import_scene.gltf(filepath="{input_glb}")
for obj in bpy.context.scene.objects:
    if obj.type == 'MESH':
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        decimate = obj.modifiers.new(name="Decimate", type='DECIMATE')
        decimate.ratio = {ratio}
        bpy.ops.object.modifier_apply(modifier="Decimate")
        print(f"Decimated: {{len(obj.data.vertices)}} verts, {{len(obj.data.polygons)}} faces")
bpy.ops.export_scene.gltf(filepath="{output_glb}", export_format='GLB')
print("Export complete")
"""
    script_path = "/tmp/decimate_script.py"
    with open(script_path, "w") as f:
        f.write(script)

    result = subprocess.run(
        ["blender", "--background", "--python", script_path],
        capture_output=True,
        text=True,
    )
    for line in result.stdout.split("\n"):
        if "Decimated" in line or "Export" in line:
            print(f"  {line.strip()}")


def upload_to_r2(local_path: str, r2_path: str):
    """Upload a file to R2."""
    print(f"Uploading {os.path.basename(local_path)} to R2...")
    subprocess.run(["rclone", "copy", local_path, r2_path], check=True)
    return f"{R2_PUBLIC}/{os.path.basename(r2_path)}/{os.path.basename(local_path)}"


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    character_name = sys.argv[1]
    image_path = sys.argv[2]
    output_dir = sys.argv[3] if len(sys.argv) > 3 else "."
    caption = sys.argv[4] if len(sys.argv) > 4 else ""

    os.makedirs(output_dir, exist_ok=True)

    # Check if image is a turnaround sheet (wide aspect ratio)
    img = Image.open(image_path)
    if img.size[0] > img.size[1] * 1.5:
        print("Detected turnaround sheet, extracting front view...")
        front_path = os.path.join(output_dir, f"{character_name}_front.png")
        image_path = extract_front_view(image_path, front_path)

    # Connect to Hunyuan3D-2
    print("Connecting to Hunyuan3D-2...")
    client = Client("Tencent/Hunyuan3D-2")

    # Generate shape
    glb_path, stats = generate_shape(client, character_name, image_path, caption)

    # Copy to output
    full_res = os.path.join(output_dir, f"{character_name}.glb")
    shutil.copy2(glb_path, full_res)
    size_mb = os.path.getsize(full_res) / (1024 * 1024)
    print(f"Full-res model: {full_res} ({size_mb:.1f} MB)")
    if isinstance(stats, dict):
        print(f"  Faces: {stats.get('number_of_faces', '?')}")
        print(f"  Vertices: {stats.get('number_of_vertices', '?')}")

    # Decimate for animation
    decimated = os.path.join(output_dir, f"{character_name}_decimated.glb")
    print("\nDecimating for animation...")
    decimate_model(full_res, decimated, ratio=0.10)
    if os.path.exists(decimated):
        size_mb = os.path.getsize(decimated) / (1024 * 1024)
        print(f"Decimated model: {decimated} ({size_mb:.1f} MB)")

    # Upload to R2
    r2_dest = f"{R2_BASE}/{character_name}"
    upload_to_r2(full_res, r2_dest)
    upload_to_r2(decimated, r2_dest)

    print(f"\nDone! Models available at:")
    print(f"  Full-res: {R2_PUBLIC}/{character_name}/{character_name}.glb")
    print(f"  Decimated: {R2_PUBLIC}/{character_name}/{character_name}_decimated.glb")


if __name__ == "__main__":
    main()
