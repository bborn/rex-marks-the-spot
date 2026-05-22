"""
Render orthographic 4-view turnaround of Jetplane on plain white background.

Outputs a single composited 4-view PNG to asset-bible/characters/jetplane_turnaround.png
plus individual view PNGs to asset-bible/characters/jetplane-alts/.

Invoke with:
  xvfb-run -a blender --background assets/models/characters/jetplane.blend \
      --python scripts/render_jetplane_turnaround.py
"""
import math
import os
import sys
from pathlib import Path

import bpy

# ---- Paths ----
PROJECT_ROOT = Path(bpy.data.filepath).resolve().parents[2] if bpy.data.filepath else Path.cwd()
# When invoked from repo root, bpy.data.filepath = .../assets/models/characters/jetplane.blend
# so parents[2] = .../  (repo root). But this script writes via env override too:
PROJECT_ROOT = Path(os.environ.get("PROJECT_ROOT", PROJECT_ROOT))
OUT_DIR = PROJECT_ROOT / "asset-bible" / "characters"
ALT_DIR = OUT_DIR / "jetplane-alts"
OUT_DIR.mkdir(parents=True, exist_ok=True)
ALT_DIR.mkdir(parents=True, exist_ok=True)

print(f"PROJECT_ROOT: {PROJECT_ROOT}")
print(f"OUT_DIR: {OUT_DIR}")

# ---- World background: pure white ----
world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
bpy.context.scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (1.0, 1.0, 1.0, 1.0)
    bg.inputs["Strength"].default_value = 1.0

# Film transparency off so we get solid white from world
scene = bpy.context.scene
scene.render.film_transparent = False

# ---- Render settings ----
scene.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in {e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items} else "BLENDER_EEVEE"
scene.render.resolution_x = 800
scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGBA"
scene.view_settings.view_transform = "Standard"

# ---- Determine bounding box of the Jetplane mesh hierarchy ----
def world_bbox(objs):
    import mathutils as _mu
    xs, ys, zs = [], [], []
    for obj in objs:
        if obj.type != "MESH":
            continue
        for v in obj.bound_box:
            wv = obj.matrix_world @ _mu.Vector((v[0], v[1], v[2]))
            xs.append(wv.x); ys.append(wv.y); zs.append(wv.z)
    return (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs))

jet_objs = [o for o in bpy.data.objects if o.name.startswith("Jetplane_") and o.type == "MESH"]
if not jet_objs:
    print("ERROR: no Jetplane meshes found", file=sys.stderr)
    sys.exit(1)
(mn, mx) = world_bbox(jet_objs)
cx, cy, cz = (mn[0]+mx[0])/2, (mn[1]+mx[1])/2, (mn[2]+mx[2])/2
sx, sy, sz = mx[0]-mn[0], mx[1]-mn[1], mx[2]-mn[2]
print(f"Bounds: ({mn}, {mx})")
print(f"Center: ({cx}, {cy}, {cz})   Size: ({sx}, {sy}, {sz})")

# ---- Create orthographic camera ----
cam_data = bpy.data.cameras.get("TurnaroundCam") or bpy.data.cameras.new("TurnaroundCam")
cam_data.type = "ORTHO"
# Scale ortho so the larger of (height, width) fits with a small margin.
ortho_scale = max(sx, sz, sy) * 1.15
cam_data.ortho_scale = ortho_scale
cam_data.clip_start = 0.01
cam_data.clip_end = 1000.0

cam_obj = bpy.data.objects.get("TurnaroundCam") or bpy.data.objects.new("TurnaroundCam", cam_data)
if cam_obj.name not in bpy.context.scene.collection.objects:
    bpy.context.scene.collection.objects.link(cam_obj)
scene.camera = cam_obj

# ---- Lighting: brighten existing lights or add a soft front/key/fill ----
# Existing Sun.005 + Area.005 should be enough but let's bump strength.
for light in [obj for obj in bpy.data.objects if obj.type == "LIGHT"]:
    light.data.energy = max(light.data.energy, 5.0)

# Add a fill light to ensure even illumination for "model sheet" look
fill = bpy.data.lights.new("TurnaroundFill", type="SUN")
fill.energy = 2.0
fill_obj = bpy.data.objects.new("TurnaroundFill", fill)
fill_obj.rotation_euler = (math.radians(60), 0, math.radians(45))
bpy.context.scene.collection.objects.link(fill_obj)

# ---- Camera placement helper ----
import mathutils

def aim_camera(view: str):
    """
    Position cam so character is centered. view in {front, side, back, three_quarter}.
    Front = +Y looking down -Y; Side = +X looking down -X; Back = -Y; 3/4 = NE.
    """
    distance = max(sx, sy, sz) * 5.0  # ortho - distance only matters for clipping
    if view == "front":
        loc = (cx, cy - distance, cz)
        look_dir = mathutils.Vector((0, 1, 0))
    elif view == "back":
        loc = (cx, cy + distance, cz)
        look_dir = mathutils.Vector((0, -1, 0))
    elif view == "side":
        loc = (cx + distance, cy, cz)
        look_dir = mathutils.Vector((-1, 0, 0))
    elif view == "three_quarter":
        ang = math.radians(45)
        loc = (cx + distance * math.sin(ang), cy - distance * math.cos(ang), cz)
        look_dir = mathutils.Vector((-math.sin(ang), math.cos(ang), 0))
    else:
        raise ValueError(view)
    cam_obj.location = loc
    # Aim the camera at the center.
    target = mathutils.Vector((cx, cy, cz))
    direction = target - mathutils.Vector(loc)
    rot_quat = direction.to_track_quat('-Z', 'Y')
    cam_obj.rotation_euler = rot_quat.to_euler()

# ---- Render each view (skip if already exists, for restart safety) ----
views = ["front", "three_quarter", "side", "back"]
view_paths = {}
for v in views:
    out_path = ALT_DIR / f"jetplane_view_{v}.png"
    if out_path.exists() and out_path.stat().st_size > 10_000:
        print(f"Skipping {v} (already rendered: {out_path.stat().st_size:,} bytes)")
        view_paths[v] = out_path
        continue
    aim_camera(v)
    scene.render.filepath = str(out_path)
    print(f"Rendering {v} -> {out_path}")
    bpy.ops.render.render(write_still=True)
    view_paths[v] = out_path

print("Individual renders complete:")
for v, p in view_paths.items():
    print(f"  {v}: {p} ({p.stat().st_size:,} bytes)")
print("DONE rendering views")
