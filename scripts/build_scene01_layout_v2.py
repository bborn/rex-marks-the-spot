#!/usr/bin/env python3
"""
Scene 01 Layout V2: Humanoid stand-ins instead of cylinders.

Opens the existing scene01_layout.blend, replaces cylinder stand-ins
with head+torso humanoid shapes, improves room details, and saves.

Usage:
    xvfb-run -a blender --background <blend_file> --python scripts/build_scene01_layout_v2.py
"""

import bpy
import bmesh
import math
import os
import sys


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_material(name, color, roughness=0.5, metallic=0.0, emission=0.0):
    """Create or reuse a Principled BSDF material."""
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = color
        bsdf.inputs["Roughness"].default_value = roughness
        bsdf.inputs["Metallic"].default_value = metallic
        if emission > 0:
            bsdf.inputs["Emission Color"].default_value = color
            bsdf.inputs["Emission Strength"].default_value = emission
    return mat


def delete_objects_by_name(*names):
    """Delete objects whose name matches any of the given names."""
    for name in names:
        obj = bpy.data.objects.get(name)
        if obj:
            bpy.data.objects.remove(obj, do_unlink=True)


def link_obj(obj):
    """Ensure object is linked to the scene's active collection."""
    if obj.name not in bpy.context.scene.collection.all_objects:
        bpy.context.scene.collection.objects.link(obj)


# ---------------------------------------------------------------------------
# Humanoid stand-in builder
# ---------------------------------------------------------------------------

def create_humanoid_standin(
    name, body_color, head_color=None,
    location=(0, 0, 0), seated_height=0.6,
):
    """
    Create a simple head + torso humanoid stand-in.

    - Torso: slightly tapered cube (wider at shoulders, narrower at waist)
    - Head: UV sphere

    The figure is built so its base is at z=0 (relative to location),
    and the total height from base to top of head equals `seated_height`.
    """
    if head_color is None:
        head_color = body_color

    # Proportions
    head_radius = seated_height * 0.16
    torso_height = seated_height - head_radius * 2  # leave room for head
    torso_width = seated_height * 0.28
    torso_depth = seated_height * 0.22

    # Create an empty as parent
    empty = bpy.data.objects.new(f"{name}_Root", None)
    empty.empty_display_type = 'PLAIN_AXES'
    empty.empty_display_size = 0.1
    empty.location = location
    bpy.context.scene.collection.objects.link(empty)

    # --- Torso ---
    bm = bmesh.new()
    # Create a slightly tapered box: wider at top (shoulders), narrower at bottom
    # We'll just use a cube and scale it – simple enough for a layout mockup
    bmesh.ops.create_cube(bm, size=1.0)
    bm_mesh = bpy.data.meshes.new(f"{name}_Torso_Mesh")
    bm.to_mesh(bm_mesh)
    bm.free()

    torso = bpy.data.objects.new(f"{name}_Torso", bm_mesh)
    torso.scale = (torso_width, torso_depth, torso_height)
    torso.location = (0, 0, torso_height / 2)
    torso.parent = empty
    bpy.context.scene.collection.objects.link(torso)

    body_mat = make_material(f"{name}_Body", body_color, roughness=0.7)
    torso.data.materials.append(body_mat)

    # --- Head ---
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=12, radius=head_radius)
    head_mesh = bpy.data.meshes.new(f"{name}_Head_Mesh")
    bm.to_mesh(head_mesh)
    bm.free()

    head = bpy.data.objects.new(f"{name}_Head", head_mesh)
    head.location = (0, 0, torso_height + head_radius)
    head.parent = empty
    bpy.context.scene.collection.objects.link(head)

    head_mat = make_material(f"{name}_HeadMat", head_color, roughness=0.7)
    head.data.materials.append(head_mat)

    return empty


# ---------------------------------------------------------------------------
# Room improvements
# ---------------------------------------------------------------------------

def add_back_cushions():
    """Add back cushions to the couch (soft lumpy rectangles leaning against back)."""
    couch_back = bpy.data.objects.get("Couch_Back")
    if not couch_back:
        return

    cushion_mat = make_material(
        "BackCushion_Brown", (0.55, 0.38, 0.25, 1.0), roughness=0.9
    )

    # Two back cushions, one on each side
    for i, x_off in enumerate([-0.32, 0.32]):
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        mesh = bpy.data.meshes.new(f"BackCushion_{i}_Mesh")
        bm.to_mesh(mesh)
        bm.free()

        cush = bpy.data.objects.new(f"BackCushion_{i}", mesh)
        # Position: lean against couch back, sitting on the seat
        cush.location = (x_off, 0.82, 0.72)
        cush.scale = (0.30, 0.08, 0.20)
        cush.rotation_euler = (math.radians(-8), 0, 0)
        bpy.context.scene.collection.objects.link(cush)
        cush.data.materials.append(cushion_mat)


def add_curtains():
    """Add flat curtain planes beside the window."""
    curtain_mat = make_material(
        "Curtain_Cream", (0.92, 0.88, 0.80, 1.0), roughness=0.95
    )

    # Window is on the back wall around x=0, y ≈ 1.5 (back wall)
    # Window_Frame objects are at various positions; the window center is roughly (0, 1.5, 1.4)
    # Looking at the scene, the back wall is at y≈1.5
    # Let's place curtains to the left and right of the window
    for i, x_off in enumerate([-0.65, 0.65]):
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        mesh = bpy.data.meshes.new(f"Curtain_{i}_Mesh")
        bm.to_mesh(mesh)
        bm.free()

        curtain = bpy.data.objects.new(f"Curtain_{i}", mesh)
        curtain.location = (x_off, 1.48, 1.4)
        curtain.scale = (0.18, 0.02, 0.55)
        bpy.context.scene.collection.objects.link(curtain)
        curtain.data.materials.append(curtain_mat)


def improve_tv_screen():
    """Add a bright colorful plane on the TV to represent the cartoon playing."""
    tv_screen = bpy.data.objects.get("TV_Screen")
    if not tv_screen:
        return

    # Create a colorful emissive plane slightly in front of the TV screen
    cartoon_mat = make_material(
        "TV_Cartoon", (0.3, 0.7, 0.9, 1.0),
        roughness=0.1, emission=3.0
    )

    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    mesh = bpy.data.meshes.new("TV_Cartoon_Mesh")
    bm.to_mesh(mesh)
    bm.free()

    cartoon = bpy.data.objects.new("TV_Cartoon", mesh)
    # TV_Screen is at roughly (0, 1.48, 1.15) with scale (0.55, 0.02, 0.33)
    # Place the cartoon plane slightly in front
    cartoon.location = (0, 1.46, 1.15)
    cartoon.scale = (0.50, 0.005, 0.28)
    bpy.context.scene.collection.objects.link(cartoon)
    cartoon.data.materials.append(cartoon_mat)


def add_floor_dino_toys():
    """Add a few small cubes on the floor near the couch as dinosaur toys."""
    positions = [
        (-0.7, 0.1, 0.04),
        (-0.4, -0.1, 0.04),
        (0.6, 0.05, 0.04),
        (-0.1, -0.3, 0.04),
    ]
    colors = [
        (0.2, 0.65, 0.25, 1.0),   # green
        (0.45, 0.3, 0.15, 1.0),   # brown
        (0.2, 0.6, 0.3, 1.0),     # green
        (0.5, 0.35, 0.2, 1.0),    # brown
    ]

    for i, (pos, col) in enumerate(zip(positions, colors)):
        mat = make_material(f"FloorToy_{i}", col, roughness=0.8)

        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        mesh = bpy.data.meshes.new(f"FloorToy_{i}_Mesh")
        bm.to_mesh(mesh)
        bm.free()

        toy = bpy.data.objects.new(f"FloorToy_{i}", mesh)
        toy.location = pos
        toy.scale = (0.06, 0.04, 0.05)
        toy.rotation_euler = (0, 0, math.radians(30 * i))
        bpy.context.scene.collection.objects.link(toy)
        toy.data.materials.append(mat)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("Scene 01 Layout V2: Humanoid Stand-ins")
    print("=" * 60)

    # ---- 1. Remove old cylinder stand-ins ----
    print("[1/6] Removing old stand-ins...")
    delete_objects_by_name("Leo_Standin", "Mia_Standin", "Jenny_Standin")

    # ---- 2. Create humanoid stand-ins ----
    print("[2/6] Creating humanoid stand-ins...")

    # Leo: left side of couch, age ~5, GREEN, 0.5m seated
    # Couch seat is at ~y=0.7, seat height ~0.55
    leo = create_humanoid_standin(
        "Leo",
        body_color=(0.2, 0.65, 0.25, 1.0),      # green (dino onesie)
        location=(-0.45, 0.7, 0.55),               # on couch seat
        seated_height=0.50,
    )

    # Leo's plush dino toy: small green sphere beside him
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=0.06)
    plush_mesh = bpy.data.meshes.new("Plush_Dino_Mesh")
    bm.to_mesh(plush_mesh)
    bm.free()
    plush = bpy.data.objects.new("Plush_DinoToy", plush_mesh)
    plush.location = (-0.65, 0.55, 0.58)
    bpy.context.scene.collection.objects.link(plush)
    plush_mat = make_material("PlushDino_Green", (0.15, 0.55, 0.2, 1.0), roughness=0.9)
    plush.data.materials.append(plush_mat)

    # Mia: right side of couch, age ~8, PINK, 0.6m seated
    mia = create_humanoid_standin(
        "Mia",
        body_color=(0.9, 0.45, 0.6, 1.0),         # pink (star pajamas)
        head_color=(0.25, 0.15, 0.1, 1.0),         # dark brown (hair)
        location=(0.45, 0.7, 0.55),
        seated_height=0.60,
    )

    # Jenny: in armchair, age ~15, CORAL/SALMON, 0.7m seated
    # Armchair seat is at roughly (1.8, -1.2, 0.5) based on old standin position
    jenny = create_humanoid_standin(
        "Jenny",
        body_color=(0.9, 0.5, 0.45, 1.0),          # coral/salmon (hoodie)
        head_color=(0.25, 0.15, 0.1, 1.0),          # dark brown (hair)
        location=(1.8, -1.2, 0.5),
        seated_height=0.70,
    )

    # Jenny's phone: small light-emitting rectangle in front of her
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    phone_mesh = bpy.data.meshes.new("Phone_Mesh")
    bm.to_mesh(phone_mesh)
    bm.free()
    phone = bpy.data.objects.new("Jenny_Phone", phone_mesh)
    phone.location = (1.65, -1.35, 0.85)
    phone.scale = (0.04, 0.005, 0.07)
    phone.rotation_euler = (math.radians(-60), 0, math.radians(10))
    bpy.context.scene.collection.objects.link(phone)
    phone_mat = make_material("Phone_Screen", (0.8, 0.9, 1.0, 1.0), emission=5.0)
    phone.data.materials.append(phone_mat)

    # ---- 3. Improve room details ----
    print("[3/6] Adding back cushions...")
    add_back_cushions()

    print("[4/6] Adding curtains...")
    add_curtains()

    print("[5/6] Improving TV and adding floor toys...")
    improve_tv_screen()
    add_floor_dino_toys()

    # ---- 6. Save ----
    print("[6/6] Saving .blend file...")
    # Output to a fixed location in the main repo
    output_dir = "/home/rex/rex-marks-the-spot/assets/storyboards/v3/scene-01-layout-v2"
    os.makedirs(output_dir, exist_ok=True)
    blend_path = os.path.join(output_dir, "scene01_layout_v2.blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    print(f"Saved: {blend_path}")

    print("\nDone! Now run the render script on the saved .blend file.")


if __name__ == "__main__":
    main()
