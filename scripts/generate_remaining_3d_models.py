#!/usr/bin/env python3
"""Generate 3D character models for Ruben, Jenny, and Jetplane.

Uses TRELLIS (Microsoft) via HuggingFace Spaces for textured 3D models,
with Hunyuan3D-2 (Tencent) as a fallback.

Usage:
    python scripts/generate_remaining_3d_models.py [character_name]

    # Generate all 3 characters:
    python scripts/generate_remaining_3d_models.py

    # Generate one character:
    python scripts/generate_remaining_3d_models.py ruben
"""

import sys
import os
import time
import shutil
import subprocess
from pathlib import Path

from gradio_client import Client, handle_file
from PIL import Image


SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
OUTPUT_DIR = PROJECT_DIR / "output" / "3d-models"
R2_BASE = "r2:rex-assets/3d-models/characters"
R2_PUBLIC = "https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/3d-models/characters"

CHARACTERS = {
    "ruben": {
        "turnaround": OUTPUT_DIR / "ruben" / "ruben_turnaround.png",
        "caption": "A stylized Pixar-like 3D character: a washed-up 49-year-old fairy godfather wearing a rumpled janitor uniform, with droopy wilted fairy wings, tired weathered face, balding with stubble",
    },
    "jenny": {
        "turnaround": OUTPUT_DIR / "jenny" / "jenny_turnaround.png",
        "caption": "A stylized Pixar-like 3D character: a 15-year-old Latina teenager with dark wavy hair, wearing a coral pink hoodie, casual modern clothing, expressive face",
    },
    "jetplane": {
        "turnaround": OUTPUT_DIR / "jetplane" / "jetplane_turnaround.png",
        "caption": "A stylized Pixar-like 3D character: a cute chunky teal-green dinosaur with an orange crest on its head, big expressive eyes, small lovable proportions, cartoon dinosaur",
    },
}


def extract_front_view(turnaround_path: str, output_path: str) -> str:
    """Extract the front view from a turnaround sheet."""
    img = Image.open(turnaround_path)
    w, h = img.size

    # Front view is typically the leftmost panel
    # Detect number of views from aspect ratio
    if w > h * 3:
        # 4-view turnaround: front is leftmost quarter
        view_w = w // 4
    elif w > h * 2:
        # 3-view turnaround: front is leftmost third
        view_w = w // 3
    else:
        # 2-view or single: use left half
        view_w = w // 2

    front = img.crop((0, 0, view_w, h))

    # Make square with white background for best AI model input
    max_dim = max(front.size)
    square = Image.new("RGBA", (max_dim, max_dim), (255, 255, 255, 255))
    offset_x = (max_dim - front.size[0]) // 2
    offset_y = (max_dim - front.size[1]) // 2
    square.paste(front, (offset_x, offset_y))
    square = square.convert("RGB").resize((512, 512), Image.LANCZOS)
    square.save(output_path)
    print(f"  Extracted front view: {output_path}")
    return output_path


def generate_with_trellis(character_name: str, image_path: str) -> str:
    """Generate a 3D GLB model using TRELLIS via HuggingFace Spaces."""
    print(f"\n--- Generating {character_name} with TRELLIS ---")
    output_glb = OUTPUT_DIR / character_name / f"{character_name}.glb"

    print("Connecting to TRELLIS Space...")
    client = Client("JeffreyXiang/TRELLIS")
    print("Connected!")

    # Step 1: Start session
    print("[1/5] Starting session...")
    client.predict(api_name="/start_session")

    # Step 2: Preprocess image
    print("[2/5] Preprocessing image...")
    client.predict(
        image=handle_file(image_path),
        api_name="/preprocess_image",
    )

    # Step 3: Get seed
    print("[3/5] Getting seed...")
    seed = client.predict(
        randomize_seed=False,
        seed=42,
        api_name="/get_seed",
    )
    print(f"  Seed: {seed}")

    # Step 4: Image to 3D
    print("[4/5] Generating 3D model (30-120 seconds)...")
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
        api_name="/image_to_3d",
    )
    elapsed = time.time() - t0
    print(f"  3D generated in {elapsed:.1f}s")

    # Step 5: Extract GLB
    print("[5/5] Extracting GLB model...")
    t0 = time.time()
    glb_result = client.predict(
        mesh_simplify=0.95,
        texture_size=1024,
        api_name="/extract_glb",
    )
    elapsed = time.time() - t0
    print(f"  GLB extracted in {elapsed:.1f}s")

    # Copy GLB file
    glb_file = glb_result
    if isinstance(glb_result, (list, tuple)):
        glb_file = glb_result[0]
    if isinstance(glb_file, dict):
        glb_file = glb_file.get("value", glb_file)

    glb_path = str(glb_file)
    if os.path.exists(glb_path):
        shutil.copy2(glb_path, str(output_glb))
        size_mb = os.path.getsize(str(output_glb)) / (1024 * 1024)
        print(f"  Model saved: {output_glb} ({size_mb:.1f} MB)")
        return str(output_glb)
    else:
        print(f"  WARNING: GLB file not found at {glb_path}")
        return ""


def generate_with_hunyuan(character_name: str, image_path: str, caption: str = "") -> str:
    """Generate a 3D GLB model using Hunyuan3D-2 via HuggingFace Spaces."""
    print(f"\n--- Generating {character_name} with Hunyuan3D-2 ---")
    output_glb = OUTPUT_DIR / character_name / f"{character_name}.glb"

    print("Connecting to Hunyuan3D-2 Space...")
    client = Client("Tencent/Hunyuan3D-2")
    print("Connected!")

    print("Generating shape (30-120 seconds)...")
    t0 = time.time()
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
    elapsed = time.time() - t0
    print(f"  Shape generated in {elapsed:.1f}s")

    shape_file = result[0]
    mesh_stats = result[2] if len(result) > 2 else {}
    path = shape_file.get("value", shape_file) if isinstance(shape_file, dict) else shape_file

    if os.path.exists(str(path)):
        shutil.copy2(str(path), str(output_glb))
        size_mb = os.path.getsize(str(output_glb)) / (1024 * 1024)
        print(f"  Model saved: {output_glb} ({size_mb:.1f} MB)")
        if isinstance(mesh_stats, dict):
            print(f"  Vertices: {mesh_stats.get('number_of_vertices', '?')}")
            print(f"  Faces: {mesh_stats.get('number_of_faces', '?')}")
        return str(output_glb)
    else:
        print(f"  WARNING: GLB file not found at {path}")
        return ""


def decimate_model(input_glb: str, output_glb: str, ratio: float = 0.10):
    """Decimate a GLB model using Blender headless."""
    print(f"  Decimating model (ratio={ratio})...")
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
        timeout=120,
    )
    for line in result.stdout.split("\n"):
        if "Decimated" in line or "Export" in line:
            print(f"    {line.strip()}")

    if os.path.exists(output_glb):
        size_mb = os.path.getsize(output_glb) / (1024 * 1024)
        print(f"  Decimated model: {output_glb} ({size_mb:.1f} MB)")
        return True
    return False


def render_preview(glb_path: str, output_png: str, character_name: str):
    """Render a preview image of the model using Blender."""
    print(f"  Rendering preview...")
    script = f"""
import bpy
import math

# Clear scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Import model
bpy.ops.import_scene.gltf(filepath="{glb_path}")

# Select mesh objects and center
meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
if not meshes:
    print("ERROR: No mesh objects found")
else:
    # Center and normalize
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')

    # Find bounds
    min_co = [float('inf')] * 3
    max_co = [float('-inf')] * 3
    for obj in meshes:
        for v in obj.data.vertices:
            co = obj.matrix_world @ v.co
            for i in range(3):
                min_co[i] = min(min_co[i], co[i])
                max_co[i] = max(max_co[i], co[i])

    size = max(max_co[i] - min_co[i] for i in range(3))
    center = [(max_co[i] + min_co[i]) / 2 for i in range(3)]

    # Add camera
    cam_data = bpy.data.cameras.new("Camera")
    cam_obj = bpy.data.objects.new("Camera", cam_data)
    bpy.context.scene.collection.objects.link(cam_obj)
    bpy.context.scene.camera = cam_obj

    dist = size * 2.5
    cam_obj.location = (center[0] + dist * 0.7, center[1] - dist * 0.7, center[2] + dist * 0.5)
    direction = [center[i] - cam_obj.location[i] for i in range(3)]
    cam_obj.rotation_euler = (math.radians(70), 0, math.radians(45))

    # Point camera at center
    constraint = cam_obj.constraints.new(type='TRACK_TO')
    empty = bpy.data.objects.new("Target", None)
    bpy.context.scene.collection.objects.link(empty)
    empty.location = center
    constraint.target = empty
    constraint.track_axis = 'TRACK_NEGATIVE_Z'
    constraint.up_axis = 'UP_Y'

    # Add lights
    light1 = bpy.data.lights.new("Key", type='SUN')
    light1.energy = 3.0
    light1_obj = bpy.data.objects.new("Key", light1)
    bpy.context.scene.collection.objects.link(light1_obj)
    light1_obj.rotation_euler = (math.radians(45), math.radians(30), 0)

    light2 = bpy.data.lights.new("Fill", type='SUN')
    light2.energy = 1.5
    light2_obj = bpy.data.objects.new("Fill", light2)
    bpy.context.scene.collection.objects.link(light2_obj)
    light2_obj.rotation_euler = (math.radians(60), math.radians(-45), 0)

    # Set background
    bpy.context.scene.world = bpy.data.worlds.new("World")
    bpy.context.scene.world.color = (0.15, 0.15, 0.2)

    # Render settings
    bpy.context.scene.render.engine = 'BLENDER_EEVEE_NEXT'
    bpy.context.scene.render.resolution_x = 1024
    bpy.context.scene.render.resolution_y = 1024
    bpy.context.scene.render.film_transparent = False
    bpy.context.scene.render.filepath = "{output_png}"
    bpy.context.scene.render.image_settings.file_format = 'PNG'

    bpy.ops.render.render(write_still=True)
    print(f"Preview rendered: {output_png}")
"""
    script_path = "/tmp/render_preview.py"
    with open(script_path, "w") as f:
        f.write(script)

    result = subprocess.run(
        ["blender", "--background", "--python", script_path],
        capture_output=True,
        text=True,
        timeout=180,
    )
    for line in result.stdout.split("\n"):
        if "Preview" in line or "ERROR" in line:
            print(f"    {line.strip()}")

    return os.path.exists(output_png)


def upload_to_r2(local_path: str, r2_dir: str):
    """Upload a file to R2."""
    filename = os.path.basename(local_path)
    print(f"  Uploading {filename} to R2...")
    subprocess.run(["rclone", "copy", local_path, r2_dir], check=True)
    r2_name = r2_dir.split("r2:rex-assets/")[-1]
    public_url = f"https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/{r2_name}/{filename}"
    print(f"    -> {public_url}")
    return public_url


def process_character(name: str, info: dict):
    """Process a single character: generate, decimate, render, upload."""
    print(f"\n{'='*60}")
    print(f" PROCESSING: {name.upper()}")
    print(f"{'='*60}")

    char_dir = OUTPUT_DIR / name
    os.makedirs(str(char_dir), exist_ok=True)

    turnaround_path = str(info["turnaround"])
    if not os.path.exists(turnaround_path):
        print(f"ERROR: Turnaround not found: {turnaround_path}")
        return None

    # Extract front view
    front_path = str(char_dir / f"{name}_front.png")
    extract_front_view(turnaround_path, front_path)

    # Try TRELLIS first (produces textured models)
    glb_path = ""
    try:
        glb_path = generate_with_trellis(name, front_path)
    except Exception as e:
        print(f"  TRELLIS failed: {e}")

    # Fallback to Hunyuan3D-2
    if not glb_path or not os.path.exists(glb_path):
        print("  Falling back to Hunyuan3D-2...")
        try:
            glb_path = generate_with_hunyuan(name, front_path, info.get("caption", ""))
        except Exception as e:
            print(f"  Hunyuan3D-2 also failed: {e}")
            return None

    if not glb_path or not os.path.exists(glb_path):
        print(f"  ERROR: No model generated for {name}")
        return None

    result = {"name": name, "glb": glb_path}

    # Decimate
    decimated_path = str(char_dir / f"{name}_decimated.glb")
    if decimate_model(glb_path, decimated_path, ratio=0.10):
        result["decimated"] = decimated_path

    # Render preview
    preview_path = str(char_dir / f"preview_{name}.png")
    if render_preview(glb_path, preview_path, name):
        result["preview"] = preview_path

    # Upload to R2
    r2_dir = f"{R2_BASE}/{name}"
    urls = {}
    urls["glb"] = upload_to_r2(glb_path, r2_dir)
    if "decimated" in result:
        urls["decimated"] = upload_to_r2(result["decimated"], r2_dir)
    if "preview" in result:
        urls["preview"] = upload_to_r2(result["preview"], r2_dir)
    # Also upload the front view used for generation
    urls["front_view"] = upload_to_r2(front_path, r2_dir)
    result["urls"] = urls

    print(f"\n  {name.upper()} complete!")
    for key, url in urls.items():
        print(f"    {key}: {url}")

    return result


def main():
    target = sys.argv[1].lower() if len(sys.argv) > 1 else None

    if target and target not in CHARACTERS:
        print(f"Unknown character: {target}")
        print(f"Available: {', '.join(CHARACTERS.keys())}")
        sys.exit(1)

    chars_to_process = {target: CHARACTERS[target]} if target else CHARACTERS
    results = {}

    for name, info in chars_to_process.items():
        result = process_character(name, info)
        if result:
            results[name] = result
        else:
            print(f"\n  FAILED: {name}")
        # Brief pause between characters to avoid rate limiting
        if len(chars_to_process) > 1:
            print("\nWaiting 10s before next character...")
            time.sleep(10)

    # Summary
    print(f"\n{'='*60}")
    print(" SUMMARY")
    print(f"{'='*60}")
    for name, result in results.items():
        print(f"\n{name.upper()}:")
        for key, url in result.get("urls", {}).items():
            print(f"  {key}: {url}")

    failed = [n for n in chars_to_process if n not in results]
    if failed:
        print(f"\nFAILED: {', '.join(failed)}")

    return len(results) == len(chars_to_process)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
