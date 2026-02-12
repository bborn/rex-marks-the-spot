#!/usr/bin/env python3
"""
Render Mia full-body preview with proper framing (head to feet visible).

Usage:
    blender --background --python scripts/render_mia_full_body.py -- <glb_path> [output_path]
"""

import bpy
import sys
import math
from mathutils import Vector
from pathlib import Path


def clear_scene():
    """Remove all objects from scene."""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)


def import_glb(filepath):
    """Import a GLB/GLTF file and return imported objects."""
    bpy.ops.import_scene.gltf(filepath=filepath)
    imported = list(bpy.context.selected_objects)
    return imported


def get_model_bounds(objects):
    """Get bounding box of all mesh objects."""
    min_co = Vector((float('inf'),) * 3)
    max_co = Vector((float('-inf'),) * 3)
    for obj in objects:
        if obj.type not in ('MESH', 'ARMATURE'):
            continue
        if obj.type == 'ARMATURE':
            # Check children of armature
            for child in obj.children:
                if child.type == 'MESH':
                    for corner in child.bound_box:
                        world_co = child.matrix_world @ Vector(corner)
                        for i in range(3):
                            min_co[i] = min(min_co[i], world_co[i])
                            max_co[i] = max(max_co[i], world_co[i])
        elif obj.type == 'MESH':
            for corner in obj.bound_box:
                world_co = obj.matrix_world @ Vector(corner)
                for i in range(3):
                    min_co[i] = min(min_co[i], world_co[i])
                    max_co[i] = max(max_co[i], world_co[i])

    # Also check all mesh objects in scene (in case hierarchy is different)
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            for corner in obj.bound_box:
                world_co = obj.matrix_world @ Vector(corner)
                for i in range(3):
                    min_co[i] = min(min_co[i], world_co[i])
                    max_co[i] = max(max_co[i], world_co[i])

    if min_co[0] == float('inf'):
        return Vector((0, 0, 0)), Vector((1, 1, 1))

    center = (min_co + max_co) / 2
    size = max_co - min_co
    return center, size, min_co, max_co


def setup_lighting(center, size):
    """Set up three-point lighting for character preview."""
    max_dim = max(size.x, size.y, size.z)
    distance = max_dim * 3

    # Key light - front-right-top
    key_data = bpy.data.lights.new(name='KeyLight', type='AREA')
    key_data.energy = 500
    key_data.size = max_dim * 2
    key = bpy.data.objects.new('KeyLight', key_data)
    bpy.context.scene.collection.objects.link(key)
    key.location = (
        center.x + distance * 0.7,
        center.y - distance * 0.5,
        center.z + distance * 0.8
    )
    direction = center - key.location
    rot_quat = direction.to_track_quat('-Z', 'Y')
    key.rotation_euler = rot_quat.to_euler()

    # Fill light - front-left, softer
    fill_data = bpy.data.lights.new(name='FillLight', type='AREA')
    fill_data.energy = 200
    fill_data.size = max_dim * 2
    fill = bpy.data.objects.new('FillLight', fill_data)
    bpy.context.scene.collection.objects.link(fill)
    fill.location = (
        center.x - distance * 0.5,
        center.y - distance * 0.3,
        center.z + distance * 0.3
    )
    direction = center - fill.location
    rot_quat = direction.to_track_quat('-Z', 'Y')
    fill.rotation_euler = rot_quat.to_euler()

    # Rim light - back for separation
    rim_data = bpy.data.lights.new(name='RimLight', type='AREA')
    rim_data.energy = 300
    rim_data.size = max_dim
    rim = bpy.data.objects.new('RimLight', rim_data)
    bpy.context.scene.collection.objects.link(rim)
    rim.location = (
        center.x - distance * 0.3,
        center.y + distance * 0.8,
        center.z + distance * 0.5
    )
    direction = center - rim.location
    rot_quat = direction.to_track_quat('-Z', 'Y')
    rim.rotation_euler = rot_quat.to_euler()


def setup_world_background():
    """Set up dark blue-gray background."""
    world = bpy.context.scene.world
    if world is None:
        world = bpy.data.worlds.new("RenderWorld")
        bpy.context.scene.world = world

    world.use_nodes = True
    nodes = world.node_tree.nodes
    links = world.node_tree.links

    nodes.clear()

    output = nodes.new('ShaderNodeOutputWorld')
    output.location = (300, 0)

    background = nodes.new('ShaderNodeBackground')
    background.location = (100, 0)
    background.inputs['Color'].default_value = (0.15, 0.18, 0.22, 1.0)
    background.inputs['Strength'].default_value = 1.0

    links.new(background.outputs['Background'], output.inputs['Surface'])


def setup_camera_full_body(center, size, min_co, max_co):
    """Set up camera for full-body framing at 1920x1080.

    The character should take up ~70-80% of frame height with
    margin on all sides, and use a slight 3/4 angle.
    """
    height = size.z
    width = max(size.x, size.y)

    # Camera target: center of the character (not geometric center,
    # slightly biased toward the vertical center for full body)
    target = Vector((center.x, center.y, center.z))

    # For 1920x1080 (landscape), the character (tall) needs to fit in height.
    # We want the character to be ~75% of frame height.
    # With a 50mm lens on a 36mm sensor (full frame), the vertical FOV is:
    # vfov = 2 * atan(sensor_height / (2 * focal_length))
    # For 50mm lens, sensor_height = 36 * (1080/1920) = 20.25mm
    # vfov = 2 * atan(20.25 / 100) = ~22.8 degrees
    # But Blender uses sensor_width=36mm by default with AUTO fit.
    # For 1920x1080, it fits to width, so we need to calculate based on that.

    # Use a portrait lens
    focal_length = 65  # 65mm - good balance of portrait and framing

    # Force sensor fit to VERTICAL so we control vertical framing precisely
    # This is set on the camera data below

    # Sensor dimensions
    sensor_width = 36.0  # mm (Blender default)
    sensor_height = 36.0 * (1080.0 / 1920.0)  # ~20.25mm for 16:9

    # We want the character to take up ~75% of the vertical frame
    # With VERTICAL sensor fit, the vertical FOV is determined by sensor_height
    desired_height_in_frame = height / 0.75  # Total visible height
    half_vfov = math.atan(sensor_height / (2.0 * focal_length))
    distance = (desired_height_in_frame / 2.0) / math.tan(half_vfov)

    sys.stderr.write(f"DEBUG: height={height:.3f}, desired_height_in_frame={desired_height_in_frame:.3f}\n")
    sys.stderr.write(f"DEBUG: half_vfov={math.degrees(half_vfov):.2f} deg, distance={distance:.3f}\n")

    # Empirical adjustment: EEVEE with this setup renders character smaller
    # than the math predicts. Scale distance down to compensate.
    distance = distance * 0.62
    sys.stderr.write(f"DEBUG: adjusted distance={distance:.3f}\n")

    # 3/4 angle: ~30-35 degrees from front
    angle = math.radians(30)
    elevation = math.radians(8)  # Slight upward angle (camera slightly above center)

    cam_x = target.x + distance * math.sin(angle)
    cam_y = target.y - distance * math.cos(angle)
    cam_z = target.z + distance * math.sin(elevation)

    cam_loc = Vector((cam_x, cam_y, cam_z))

    # Create camera
    cam_data = bpy.data.cameras.new(name='FullBodyCamera')
    cam_data.lens = focal_length
    cam_data.sensor_width = 36.0
    cam_data.sensor_fit = 'VERTICAL'

    cam_obj = bpy.data.objects.new('FullBodyCamera', cam_data)
    bpy.context.scene.collection.objects.link(cam_obj)
    cam_obj.location = cam_loc

    # Point camera at target
    direction = target - cam_loc
    rot_quat = direction.to_track_quat('-Z', 'Y')
    cam_obj.rotation_euler = rot_quat.to_euler()

    bpy.context.scene.camera = cam_obj

    sys.stderr.write(f"Camera: focal={focal_length}mm, distance={distance:.2f}\n")
    sys.stderr.write(f"Model height={height:.3f}, width={width:.3f}\n")
    sys.stderr.write(f"Camera at: {cam_loc}\n")
    sys.stderr.write(f"Looking at: {target}\n")

    return cam_obj


def configure_render(output_path):
    """Configure render settings for 1920x1080 output."""
    scene = bpy.context.scene
    render = scene.render

    render.filepath = output_path
    render.resolution_x = 1920
    render.resolution_y = 1080
    render.resolution_percentage = 100

    render.image_settings.file_format = 'PNG'
    render.image_settings.color_mode = 'RGBA'
    render.image_settings.color_depth = '8'

    # Use EEVEE for faster rendering (still looks good for previews)
    render.engine = 'BLENDER_EEVEE'
    scene.eevee.taa_render_samples = 128

    # Transparent background (we'll composite over the world background)
    render.film_transparent = False  # Keep background visible

    # Try GPU
    try:
        prefs = bpy.context.preferences.addons.get('cycles')
        if prefs:
            prefs = prefs.preferences
            for device_type in ['OPTIX', 'CUDA', 'HIP', 'METAL']:
                try:
                    prefs.compute_device_type = device_type
                    prefs.get_devices()
                    if prefs.devices:
                        for device in prefs.devices:
                            device.use = True
                        scene.cycles.device = 'GPU'
                        sys.stderr.write(f"GPU available: {device_type}\n")
                        break
                except:
                    continue
    except Exception as e:
        sys.stderr.write(f"GPU setup: {e}\n")


def main():
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = []

    if not argv:
        sys.stderr.write(
            "Usage: blender --background --python render_mia_full_body.py "
            "-- <glb_path> [output_path]\n"
        )
        sys.exit(1)

    glb_path = argv[0]
    output_path = argv[1] if len(argv) > 1 else "output/mia_render/mia_blender_full_body.png"

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    sys.stderr.write(f"Input: {glb_path}\n")
    sys.stderr.write(f"Output: {output_path}\n")

    # Clear and import
    clear_scene()
    sys.stderr.write("Importing GLB...\n")
    objects = import_glb(glb_path)
    sys.stderr.write(f"Imported {len(objects)} objects\n")

    # List all objects in scene
    for obj in bpy.context.scene.objects:
        sys.stderr.write(f"  - {obj.name} ({obj.type})\n")

    # Get bounds
    center, size, min_co, max_co = get_model_bounds(objects)
    sys.stderr.write(f"Model bounds: min={min_co}, max={max_co}\n")
    sys.stderr.write(f"Model center: {center}, size: {size}\n")

    # Setup scene
    setup_lighting(center, size)
    setup_world_background()
    setup_camera_full_body(center, size, min_co, max_co)
    configure_render(output_path)

    # Render
    sys.stderr.write("Rendering...\n")
    bpy.ops.render.render(write_still=True)

    if Path(output_path).exists():
        file_size = Path(output_path).stat().st_size
        sys.stderr.write(f"Success! Saved: {output_path} ({file_size / 1024:.0f} KB)\n")
    else:
        sys.stderr.write(f"ERROR: Output file not created!\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
