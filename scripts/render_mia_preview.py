#!/usr/bin/env python3
"""
Render preview images of Mia's 3D model using Blender headless mode.

Usage:
    blender -b -P scripts/render_mia_preview.py
"""

import bpy
import math
import os
import sys
from pathlib import Path

MODEL_PATH = "output/mia_meshy/mia_rigged.glb"
OUTPUT_DIR = Path("output/mia_meshy/previews")


def setup_scene():
    """Clear default scene and set up rendering."""
    # Delete all default objects
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()

    # Set render engine
    bpy.context.scene.render.engine = "BLENDER_EEVEE"
    bpy.context.scene.render.resolution_x = 1024
    bpy.context.scene.render.resolution_y = 1024
    bpy.context.scene.render.film_transparent = True

    # Set world background to neutral gray
    world = bpy.data.worlds.get("World")
    if world is None:
        world = bpy.data.worlds.new("World")
    bpy.context.scene.world = world
    world.use_nodes = True
    bg_node = world.node_tree.nodes.get("Background")
    if bg_node:
        bg_node.inputs["Color"].default_value = (0.15, 0.15, 0.18, 1.0)
        bg_node.inputs["Strength"].default_value = 0.5


def import_model():
    """Import the GLB model."""
    model_path = Path(MODEL_PATH).resolve()
    if not model_path.exists():
        # Try fallback to unrigged model
        model_path = Path("output/mia_meshy/mia_meshy.glb").resolve()
        if not model_path.exists():
            print(f"ERROR: Model not found at {MODEL_PATH}")
            sys.exit(1)
        print(f"Using unrigged model: {model_path}")

    print(f"Importing: {model_path}")
    bpy.ops.import_scene.gltf(filepath=str(model_path))

    # Find imported mesh objects
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    armatures = [obj for obj in bpy.context.scene.objects if obj.type == "ARMATURE"]

    print(f"Imported {len(meshes)} mesh(es) and {len(armatures)} armature(s)")

    return meshes, armatures


def center_model(meshes):
    """Center the model at origin and scale to fit."""
    if not meshes:
        return

    # Select all mesh objects
    bpy.ops.object.select_all(action="DESELECT")
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]

    # Get bounding box of all meshes
    min_x = min_y = min_z = float("inf")
    max_x = max_y = max_z = float("-inf")

    for obj in meshes:
        for corner in obj.bound_box:
            world_corner = obj.matrix_world @ bpy.app.driver_namespace.get("Vector", __import__("mathutils").Vector)(corner)
            min_x = min(min_x, world_corner.x)
            min_y = min(min_y, world_corner.y)
            min_z = min(min_z, world_corner.z)
            max_x = max(max_x, world_corner.x)
            max_y = max(max_y, world_corner.y)
            max_z = max(max_z, world_corner.z)

    # Calculate center and size
    center_x = (min_x + max_x) / 2
    center_y = (min_y + max_y) / 2
    center_z = (min_z + max_z) / 2
    height = max_z - min_z

    print(f"Model bounds: ({min_x:.2f}, {min_y:.2f}, {min_z:.2f}) to ({max_x:.2f}, {max_y:.2f}, {max_z:.2f})")
    print(f"Model center: ({center_x:.2f}, {center_y:.2f}, {center_z:.2f})")
    print(f"Model height: {height:.2f}")

    return center_x, center_y, center_z, height


def setup_lighting():
    """Set up three-point lighting."""
    # Key light
    bpy.ops.object.light_add(type="AREA", location=(2, -2, 3))
    key_light = bpy.context.active_object
    key_light.name = "KeyLight"
    key_light.data.energy = 200
    key_light.data.size = 2

    # Fill light
    bpy.ops.object.light_add(type="AREA", location=(-2, -1, 2))
    fill_light = bpy.context.active_object
    fill_light.name = "FillLight"
    fill_light.data.energy = 80
    fill_light.data.size = 3

    # Rim light
    bpy.ops.object.light_add(type="AREA", location=(0, 2, 3))
    rim_light = bpy.context.active_object
    rim_light.name = "RimLight"
    rim_light.data.energy = 120
    rim_light.data.size = 1.5


def setup_camera(center, height, angle_deg=30, elevation_deg=15):
    """Position camera to frame the character."""
    # Camera distance based on model height
    distance = height * 2.5

    angle_rad = math.radians(angle_deg)
    elev_rad = math.radians(elevation_deg)

    cam_x = center[0] + distance * math.sin(angle_rad) * math.cos(elev_rad)
    cam_y = center[1] - distance * math.cos(angle_rad) * math.cos(elev_rad)
    cam_z = center[2] + distance * math.sin(elev_rad)

    bpy.ops.object.camera_add(location=(cam_x, cam_y, cam_z))
    camera = bpy.context.active_object
    camera.name = "PreviewCamera"

    # Point at model center (slightly above base for character)
    look_at_z = center[2] + height * 0.4
    direction = bpy.app.driver_namespace.get("Vector", __import__("mathutils").Vector)(
        (center[0] - cam_x, center[1] - cam_y, look_at_z - cam_z)
    )
    rot_quat = direction.to_track_quat("-Z", "Y")
    camera.rotation_euler = rot_quat.to_euler()

    bpy.context.scene.camera = camera
    return camera


def render_view(output_path, angle_deg=30, elevation_deg=15, center=(0, 0, 0), height=2.0):
    """Render a single view."""
    # Remove existing camera
    for obj in bpy.data.objects:
        if obj.type == "CAMERA":
            bpy.data.objects.remove(obj, do_unlink=True)

    camera = setup_camera(center, height, angle_deg, elevation_deg)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    bpy.context.scene.render.filepath = str(output_path)
    bpy.context.scene.render.image_settings.file_format = "PNG"
    bpy.ops.render.render(write_still=True)
    print(f"Rendered: {output_path}")


def main():
    setup_scene()
    meshes, armatures = import_model()

    if not meshes:
        print("ERROR: No meshes found in model")
        sys.exit(1)

    result = center_model(meshes)
    if result is None:
        center = (0, 0, 0)
        height = 2.0
    else:
        center = (result[0], result[1], result[2])
        height = result[3]

    setup_lighting()

    # Render multiple views
    views = {
        "front_three_quarter": (30, 10),
        "front": (0, 10),
        "side": (90, 10),
        "back": (180, 10),
    }

    for view_name, (angle, elevation) in views.items():
        output_path = OUTPUT_DIR / f"mia_{view_name}.png"
        render_view(str(output_path), angle, elevation, center, height)

    print(f"\nAll previews saved to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
