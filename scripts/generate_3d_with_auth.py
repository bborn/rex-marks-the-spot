#!/usr/bin/env python3
"""Generate 3D character models with HuggingFace authentication for higher quota.

Tries multiple spaces in order:
1. Hunyuan3D-2 (with auth)
2. TRELLIS (with auth)
3. TripoSR (StabilityAI)
4. InstantMesh

Usage:
    python3 scripts/generate_3d_with_auth.py <character_name>
"""

import sys
import os
import time
import shutil
from pathlib import Path

from gradio_client import Client, handle_file
from PIL import Image

OUTPUT_DIR = Path(__file__).parent.parent / "output" / "3d-models"
R2_BASE = "r2:rex-assets/3d-models/characters"
R2_PUBLIC = "https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/3d-models/characters"

HF_TOKEN = os.environ.get("HF_TOKEN", "")

CHARACTERS = {
    "ruben": {
        "turnaround": OUTPUT_DIR / "ruben" / "ruben_turnaround.png",
        "caption": "A stylized Pixar-like character: a washed-up 49-year-old fairy godfather wearing a rumpled janitor uniform, with droopy wilted fairy wings, tired weathered face",
    },
    "jenny": {
        "turnaround": OUTPUT_DIR / "jenny" / "jenny_turnaround.png",
        "caption": "A stylized Pixar-like character: a 15-year-old Latina teenager with dark wavy hair, wearing a coral pink hoodie, casual modern clothing",
    },
    "jetplane": {
        "turnaround": OUTPUT_DIR / "jetplane" / "jetplane_turnaround.png",
        "caption": "A stylized Pixar-like character: a cute chunky teal-green dinosaur with an orange crest, big expressive eyes, small lovable proportions",
    },
}


def extract_front_view(turnaround_path: str, output_path: str) -> str:
    """Extract front view from turnaround sheet."""
    img = Image.open(turnaround_path)
    w, h = img.size
    if w > h * 3:
        view_w = w // 4
    elif w > h * 2:
        view_w = w // 3
    else:
        view_w = w // 2
    front = img.crop((0, 0, view_w, h))
    max_dim = max(front.size)
    square = Image.new("RGBA", (max_dim, max_dim), (255, 255, 255, 255))
    offset_x = (max_dim - front.size[0]) // 2
    offset_y = (max_dim - front.size[1]) // 2
    square.paste(front, (offset_x, offset_y))
    square = square.convert("RGB").resize((512, 512), Image.LANCZOS)
    square.save(output_path)
    return output_path


def try_hunyuan(name, image_path, caption):
    """Try Hunyuan3D-2 with authentication."""
    print(f"\n[1] Trying Hunyuan3D-2 (with auth)...")
    output_glb = OUTPUT_DIR / name / f"{name}.glb"

    client = Client("Tencent/Hunyuan3D-2", token=HF_TOKEN)
    print("  Connected!")

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
    print(f"  Generated in {elapsed:.1f}s")

    shape_file = result[0]
    mesh_stats = result[2] if len(result) > 2 else {}
    path = shape_file.get("value", shape_file) if isinstance(shape_file, dict) else shape_file

    if os.path.exists(str(path)):
        shutil.copy2(str(path), str(output_glb))
        size_mb = os.path.getsize(str(output_glb)) / (1024 * 1024)
        print(f"  Saved: {output_glb} ({size_mb:.1f} MB)")
        if isinstance(mesh_stats, dict):
            print(f"  Verts: {mesh_stats.get('number_of_vertices', '?')}, Faces: {mesh_stats.get('number_of_faces', '?')}")
        return str(output_glb)
    return ""


def try_trellis(name, image_path):
    """Try TRELLIS with authentication."""
    print(f"\n[2] Trying TRELLIS (with auth)...")
    output_glb = OUTPUT_DIR / name / f"{name}.glb"

    client = Client("JeffreyXiang/TRELLIS", token=HF_TOKEN)
    print("  Connected!")

    client.predict(api_name="/start_session")
    client.predict(image=handle_file(image_path), api_name="/preprocess_image")
    seed = client.predict(randomize_seed=False, seed=42, api_name="/get_seed")

    t0 = time.time()
    client.predict(
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

    glb_result = client.predict(
        mesh_simplify=0.95,
        texture_size=1024,
        api_name="/extract_glb",
    )

    glb_file = glb_result
    if isinstance(glb_result, (list, tuple)):
        glb_file = glb_result[0]
    if isinstance(glb_file, dict):
        glb_file = glb_file.get("value", glb_file)

    if os.path.exists(str(glb_file)):
        shutil.copy2(str(glb_file), str(output_glb))
        size_mb = os.path.getsize(str(output_glb)) / (1024 * 1024)
        print(f"  Saved: {output_glb} ({size_mb:.1f} MB)")
        return str(output_glb)
    return ""


def try_triposr(name, image_path):
    """Try TripoSR (StabilityAI)."""
    print(f"\n[3] Trying TripoSR...")
    output_glb = OUTPUT_DIR / name / f"{name}.glb"

    client = Client("stabilityai/TripoSR", token=HF_TOKEN)
    print("  Connected!")

    t0 = time.time()
    result = client.predict(
        input_image=handle_file(image_path),
        do_remove_background=True,
        foreground_ratio=0.85,
        mc_resolution=256,
        api_name="/run",
    )
    elapsed = time.time() - t0
    print(f"  Generated in {elapsed:.1f}s")

    # TripoSR returns [preprocessed_image, output_model_obj]
    if isinstance(result, (list, tuple)) and len(result) >= 2:
        model_path = result[1]
        if isinstance(model_path, dict):
            model_path = model_path.get("value", "")
        if os.path.exists(str(model_path)):
            # TripoSR outputs OBJ, convert name
            output_obj = str(OUTPUT_DIR / name / f"{name}.obj")
            shutil.copy2(str(model_path), output_obj)
            size_mb = os.path.getsize(output_obj) / (1024 * 1024)
            print(f"  Saved: {output_obj} ({size_mb:.1f} MB)")
            return output_obj
    return ""


def try_instantmesh(name, image_path):
    """Try InstantMesh."""
    print(f"\n[4] Trying InstantMesh...")
    output_glb = OUTPUT_DIR / name / f"{name}.glb"

    client = Client("TencentARC/InstantMesh", token=HF_TOKEN)
    print("  Connected!")

    t0 = time.time()
    # InstantMesh has a multi-step API
    # Step 1: check input image
    result = client.predict(
        input_image=handle_file(image_path),
        do_remove_background=True,
        api_name="/check_input_image",
    )
    print(f"  Preprocessed in {time.time() - t0:.1f}s")

    preprocessed = result
    if isinstance(result, dict):
        preprocessed = result.get("value", result)

    # Step 2: generate multiview
    t0 = time.time()
    mv_result = client.predict(
        input_image=handle_file(str(preprocessed)) if os.path.exists(str(preprocessed)) else handle_file(image_path),
        sample_steps=75,
        sample_seed=42,
        api_name="/generate_mvs",
    )
    print(f"  Multiview generated in {time.time() - t0:.1f}s")

    # Step 3: generate 3D
    t0 = time.time()
    mesh_result = client.predict(api_name="/make3d")
    elapsed = time.time() - t0
    print(f"  3D generated in {elapsed:.1f}s")

    if isinstance(mesh_result, (list, tuple)):
        for item in mesh_result:
            path = str(item.get("value", item) if isinstance(item, dict) else item)
            if path.endswith(('.glb', '.obj')):
                shutil.copy2(path, str(output_glb if path.endswith('.glb') else OUTPUT_DIR / name / f"{name}.obj"))
                size_mb = os.path.getsize(str(output_glb if path.endswith('.glb') else OUTPUT_DIR / name / f"{name}.obj")) / (1024 * 1024)
                ext = Path(path).suffix
                print(f"  Saved: {name}{ext} ({size_mb:.1f} MB)")
                return str(output_glb if path.endswith('.glb') else OUTPUT_DIR / name / f"{name}.obj")
    elif isinstance(mesh_result, str) and os.path.exists(mesh_result):
        ext = Path(mesh_result).suffix
        dest = str(OUTPUT_DIR / name / f"{name}{ext}")
        shutil.copy2(mesh_result, dest)
        print(f"  Saved: {dest}")
        return dest
    return ""


def upload_to_r2(local_path, r2_dir):
    """Upload file to R2."""
    import subprocess
    filename = os.path.basename(local_path)
    print(f"  Uploading {filename}...")
    subprocess.run(["rclone", "copy", local_path, r2_dir], check=True)
    r2_name = r2_dir.split("r2:rex-assets/")[-1]
    url = f"https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/{r2_name}/{filename}"
    print(f"    -> {url}")
    return url


def process_character(name):
    """Process a single character through multiple generation backends."""
    info = CHARACTERS[name]
    char_dir = OUTPUT_DIR / name
    os.makedirs(str(char_dir), exist_ok=True)

    turnaround = str(info["turnaround"])
    front_path = str(char_dir / f"{name}_front.png")

    if not os.path.exists(front_path):
        extract_front_view(turnaround, front_path)

    caption = info.get("caption", "")
    glb_path = ""

    # Try each backend in order
    for attempt_fn in [
        lambda: try_hunyuan(name, front_path, caption),
        lambda: try_trellis(name, front_path),
        lambda: try_triposr(name, front_path),
        lambda: try_instantmesh(name, front_path),
    ]:
        try:
            glb_path = attempt_fn()
            if glb_path and os.path.exists(glb_path):
                print(f"\n  SUCCESS: Model generated at {glb_path}")
                break
        except Exception as e:
            print(f"  Failed: {e}")
            glb_path = ""

    if not glb_path:
        print(f"\n  ALL METHODS FAILED for {name}")
        return None

    # Upload to R2
    r2_dir = f"{R2_BASE}/{name}"
    urls = {}
    urls["model"] = upload_to_r2(glb_path, r2_dir)
    urls["front_view"] = upload_to_r2(front_path, r2_dir)

    # Decimate if GLB
    if glb_path.endswith('.glb'):
        import subprocess
        decimated = str(char_dir / f"{name}_decimated.glb")
        script = f"""
import bpy
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()
bpy.ops.import_scene.gltf(filepath="{glb_path}")
for obj in bpy.context.scene.objects:
    if obj.type == 'MESH':
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        d = obj.modifiers.new(name="Decimate", type='DECIMATE')
        d.ratio = 0.10
        bpy.ops.object.modifier_apply(modifier="Decimate")
        print(f"Decimated: {{len(obj.data.vertices)}} verts, {{len(obj.data.polygons)}} faces")
bpy.ops.export_scene.gltf(filepath="{decimated}", export_format='GLB')
print("Done")
"""
        with open("/tmp/dec.py", "w") as f:
            f.write(script)
        subprocess.run(["blender", "--background", "--python", "/tmp/dec.py"],
                      capture_output=True, text=True, timeout=120)
        if os.path.exists(decimated):
            urls["decimated"] = upload_to_r2(decimated, r2_dir)

    return urls


def main():
    name = sys.argv[1].lower() if len(sys.argv) > 1 else None
    if not name or name not in CHARACTERS:
        print(f"Usage: {sys.argv[0]} <character_name>")
        print(f"Available: {', '.join(CHARACTERS.keys())}")
        sys.exit(1)

    print(f"{'='*60}")
    print(f" GENERATING: {name.upper()}")
    print(f"{'='*60}")

    result = process_character(name)
    if result:
        print(f"\n{'='*60}")
        print(f" {name.upper()} COMPLETE!")
        for k, v in result.items():
            print(f"  {k}: {v}")
        print(f"{'='*60}")
    else:
        print(f"\nFAILED to generate {name}")
        sys.exit(1)


if __name__ == "__main__":
    main()
