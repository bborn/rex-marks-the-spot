#!/usr/bin/env python3
"""Render preview images for all character GLB models.

Run: blender --background --python scripts/render_all_previews.py
"""

import bpy
import math
import os
import sys

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                          "output", "3d-models")

CHARACTERS = {
    "ruben": os.path.join(OUTPUT_DIR, "ruben", "ruben.glb"),
    "jenny": os.path.join(OUTPUT_DIR, "jenny", "jenny.glb"),
    "jetplane": os.path.join(OUTPUT_DIR, "jetplane", "jetplane.glb"),
}


def render_character(name, glb_path):
    """Render a preview for a single character."""
    if not os.path.exists(glb_path):
        print(f"SKIP {name}: GLB not found at {glb_path}")
        return None

    print(f"\nRendering {name}...")

    # Clear scene
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

    # Remove orphan data
    for block in bpy.data.meshes:
        if block.users == 0:
            bpy.data.meshes.remove(block)
    for block in bpy.data.materials:
        if block.users == 0:
            bpy.data.materials.remove(block)

    # Import GLB
    bpy.ops.import_scene.gltf(filepath=glb_path)
    print(f"  Imported {glb_path}")

    # Find mesh bounds
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    if not meshes:
        print(f"  ERROR: No meshes found")
        return None

    min_co = [float('inf')] * 3
    max_co = [float('-inf')] * 3
    for obj in meshes:
        for v in obj.data.vertices:
            co = obj.matrix_world @ v.co
            for i in range(3):
                min_co[i] = min(min_co[i], co[i])
                max_co[i] = max(max_co[i], co[i])

    center = [(max_co[i] + min_co[i]) / 2 for i in range(3)]
    size = max(max_co[i] - min_co[i] for i in range(3))
    print(f"  Model size: {size:.2f}, center: {[f'{c:.2f}' for c in center]}")

    # Camera
    cam_data = bpy.data.cameras.new("Camera")
    cam_obj = bpy.data.objects.new("Camera", cam_data)
    bpy.context.scene.collection.objects.link(cam_obj)
    bpy.context.scene.camera = cam_obj

    dist = size * 2.5
    cam_obj.location = (
        center[0] + dist * 0.7,
        center[1] - dist * 0.7,
        center[2] + dist * 0.4,
    )

    # Track to center
    empty = bpy.data.objects.new("Target", None)
    bpy.context.scene.collection.objects.link(empty)
    empty.location = center
    constraint = cam_obj.constraints.new(type='TRACK_TO')
    constraint.target = empty
    constraint.track_axis = 'TRACK_NEGATIVE_Z'
    constraint.up_axis = 'UP_Y'

    # Lights
    light1 = bpy.data.lights.new("Key", type='SUN')
    light1.energy = 3.0
    light1_obj = bpy.data.objects.new("Key", light1)
    bpy.context.scene.collection.objects.link(light1_obj)
    light1_obj.rotation_euler = (math.radians(50), math.radians(30), 0)

    light2 = bpy.data.lights.new("Fill", type='SUN')
    light2.energy = 1.5
    light2_obj = bpy.data.objects.new("Fill", light2)
    bpy.context.scene.collection.objects.link(light2_obj)
    light2_obj.rotation_euler = (math.radians(60), math.radians(-45), 0)

    light3 = bpy.data.lights.new("Rim", type='SUN')
    light3.energy = 2.0
    light3_obj = bpy.data.objects.new("Rim", light3)
    bpy.context.scene.collection.objects.link(light3_obj)
    light3_obj.rotation_euler = (math.radians(30), math.radians(180), 0)

    # Background
    if bpy.context.scene.world is None:
        bpy.context.scene.world = bpy.data.worlds.new("World")
    bpy.context.scene.world.color = (0.15, 0.15, 0.2)

    # Render settings - use EEVEE (Blender 4.0 compatible)
    bpy.context.scene.render.engine = 'BLENDER_EEVEE'
    bpy.context.scene.render.resolution_x = 1024
    bpy.context.scene.render.resolution_y = 1024
    bpy.context.scene.render.film_transparent = False

    preview_path = os.path.join(OUTPUT_DIR, name, f"preview_{name}.png")
    bpy.context.scene.render.filepath = preview_path
    bpy.context.scene.render.image_settings.file_format = 'PNG'

    bpy.ops.render.render(write_still=True)

    if os.path.exists(preview_path):
        size_kb = os.path.getsize(preview_path) / 1024
        print(f"  Preview saved: {preview_path} ({size_kb:.0f} KB)")
        return preview_path
    else:
        print(f"  ERROR: Preview not saved")
        return None


def main():
    # Filter to specific character if provided
    target = None
    for arg in sys.argv:
        if arg in CHARACTERS:
            target = arg
            break

    chars = {target: CHARACTERS[target]} if target else CHARACTERS
    results = {}

    for name, glb_path in chars.items():
        result = render_character(name, glb_path)
        if result:
            results[name] = result

    print(f"\n{'='*50}")
    print("RENDER SUMMARY")
    print(f"{'='*50}")
    for name, path in results.items():
        print(f"  {name}: {path}")
    failed = [n for n in chars if n not in results]
    if failed:
        print(f"  FAILED: {', '.join(failed)}")


if __name__ == "__main__":
    main()
