#!/usr/bin/env python3
"""
Render preview images for all character models.

This script is executed INSIDE Blender and handles:
1. Opening each character .blend file
2. Setting up camera and lighting
3. Rendering to PNG

Usage:
    blender -b -P scripts/render_character_previews.py -- --output-dir docs/images/characters
"""

import bpy
import os
import sys
import math
from pathlib import Path


def clear_scene():
    """Remove all objects from scene."""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)


def get_scene_bounds():
    """Get the bounding box of all mesh objects in scene."""
    from mathutils import Vector

    min_coords = [float('inf')] * 3
    max_coords = [float('-inf')] * 3

    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            for corner in obj.bound_box:
                world_corner = obj.matrix_world @ Vector(corner)
                for i in range(3):
                    min_coords[i] = min(min_coords[i], world_corner[i])
                    max_coords[i] = max(max_coords[i], world_corner[i])

    if min_coords[0] == float('inf'):
        return (0, 0, 0), (1, 1, 1)

    return tuple(min_coords), tuple(max_coords)


def setup_camera_for_character():
    """Set up camera to frame the character nicely."""
    from mathutils import Vector

    # Get bounds of all mesh objects
    min_coords, max_coords = get_scene_bounds()

    # Calculate center and size
    center = Vector([
        (min_coords[i] + max_coords[i]) / 2 for i in range(3)
    ])
    size = Vector([
        max_coords[i] - min_coords[i] for i in range(3)
    ])

    # Calculate camera distance based on object size
    max_dimension = max(size.x, size.y, size.z)
    distance = max_dimension * 2.5

    # Position camera at 45 degrees from front-right
    angle = math.radians(45)
    elevation = math.radians(20)

    cam_x = center.x + distance * math.cos(angle) * math.cos(elevation)
    cam_y = center.y - distance * math.sin(angle) * math.cos(elevation)
    cam_z = center.z + distance * math.sin(elevation) + size.z * 0.3

    # Create or get camera
    cam_data = bpy.data.cameras.new(name='PreviewCamera')
    cam_obj = bpy.data.objects.new('PreviewCamera', cam_data)
    bpy.context.scene.collection.objects.link(cam_obj)

    # Position camera
    cam_obj.location = (cam_x, cam_y, cam_z)

    # Point camera at center of character
    direction = center - cam_obj.location
    rot_quat = direction.to_track_quat('-Z', 'Y')
    cam_obj.rotation_euler = rot_quat.to_euler()

    # Set as active camera
    bpy.context.scene.camera = cam_obj

    # Adjust focal length for nice framing
    cam_data.lens = 50

    return cam_obj


def setup_lighting():
    """Set up three-point lighting for character preview."""
    from mathutils import Vector

    # Get scene center
    min_coords, max_coords = get_scene_bounds()
    center = Vector([
        (min_coords[i] + max_coords[i]) / 2 for i in range(3)
    ])
    size = max(max_coords[i] - min_coords[i] for i in range(3))
    distance = size * 3

    # Key light - main light from front-right-top
    key_light_data = bpy.data.lights.new(name='KeyLight', type='AREA')
    key_light_data.energy = 500
    key_light_data.size = size * 2
    key_light = bpy.data.objects.new('KeyLight', key_light_data)
    bpy.context.scene.collection.objects.link(key_light)
    key_light.location = (center.x + distance * 0.7, center.y - distance * 0.5, center.z + distance * 0.8)

    # Point at center
    direction = center - key_light.location
    rot_quat = direction.to_track_quat('-Z', 'Y')
    key_light.rotation_euler = rot_quat.to_euler()

    # Fill light - softer light from front-left
    fill_light_data = bpy.data.lights.new(name='FillLight', type='AREA')
    fill_light_data.energy = 200
    fill_light_data.size = size * 2
    fill_light = bpy.data.objects.new('FillLight', fill_light_data)
    bpy.context.scene.collection.objects.link(fill_light)
    fill_light.location = (center.x - distance * 0.5, center.y - distance * 0.3, center.z + distance * 0.3)

    direction = center - fill_light.location
    rot_quat = direction.to_track_quat('-Z', 'Y')
    fill_light.rotation_euler = rot_quat.to_euler()

    # Rim light - back light for separation
    rim_light_data = bpy.data.lights.new(name='RimLight', type='AREA')
    rim_light_data.energy = 300
    rim_light_data.size = size
    rim_light = bpy.data.objects.new('RimLight', rim_light_data)
    bpy.context.scene.collection.objects.link(rim_light)
    rim_light.location = (center.x - distance * 0.3, center.y + distance * 0.8, center.z + distance * 0.5)

    direction = center - rim_light.location
    rot_quat = direction.to_track_quat('-Z', 'Y')
    rim_light.rotation_euler = rot_quat.to_euler()


def setup_world_background():
    """Set up a nice gradient background."""
    world = bpy.context.scene.world
    if world is None:
        world = bpy.data.worlds.new("PreviewWorld")
        bpy.context.scene.world = world

    world.use_nodes = True
    nodes = world.node_tree.nodes
    links = world.node_tree.links

    # Clear existing nodes
    nodes.clear()

    # Create gradient background
    output = nodes.new('ShaderNodeOutputWorld')
    output.location = (300, 0)

    background = nodes.new('ShaderNodeBackground')
    background.location = (100, 0)
    background.inputs['Color'].default_value = (0.15, 0.18, 0.22, 1.0)  # Dark blue-gray
    background.inputs['Strength'].default_value = 1.0

    links.new(background.outputs['Background'], output.inputs['Surface'])


def configure_render(output_path, resolution=(1024, 1024)):
    """Configure render settings."""
    scene = bpy.context.scene
    render = scene.render

    # Output settings
    render.filepath = output_path
    render.resolution_x = resolution[0]
    render.resolution_y = resolution[1]
    render.resolution_percentage = 100

    # File format
    render.image_settings.file_format = 'PNG'
    render.image_settings.color_mode = 'RGBA'
    render.image_settings.color_depth = '8'

    # Use Cycles for quality
    render.engine = 'CYCLES'
    scene.cycles.samples = 128
    scene.cycles.use_denoising = False  # Denoiser not available in this build

    # Try to use GPU
    try:
        prefs = bpy.context.preferences.addons['cycles'].preferences
        for device_type in ['OPTIX', 'CUDA', 'HIP', 'METAL']:
            try:
                prefs.compute_device_type = device_type
                prefs.get_devices()
                if prefs.devices:
                    for device in prefs.devices:
                        device.use = True
                    scene.cycles.device = 'GPU'
                    print(f"Using GPU: {device_type}")
                    break
            except:
                continue
    except Exception as e:
        print(f"GPU setup failed, using CPU: {e}")
        scene.cycles.device = 'CPU'

    # Transparent background for flexibility
    render.film_transparent = True


def has_existing_camera():
    """Check if scene already has a camera set up."""
    return bpy.context.scene.camera is not None


def has_existing_lights():
    """Check if scene has light objects."""
    for obj in bpy.context.scene.objects:
        if obj.type == 'LIGHT':
            return True
    return False


def render_character(blend_file, output_path):
    """Render a single character model."""
    print(f"\n{'='*60}")
    print(f"Rendering: {blend_file}")
    print(f"Output: {output_path}")
    print(f"{'='*60}")

    # Open the blend file
    bpy.ops.wm.open_mainfile(filepath=blend_file)

    # Check what's already in the scene
    has_camera = has_existing_camera()
    has_lights = has_existing_lights()

    print(f"Scene has camera: {has_camera}")
    print(f"Scene has lights: {has_lights}")

    # Set up camera if needed
    if not has_camera:
        print("Setting up camera...")
        setup_camera_for_character()

    # Set up lighting if needed
    if not has_lights:
        print("Setting up lighting...")
        setup_lighting()

    # Set up background
    setup_world_background()

    # Configure render
    configure_render(output_path)

    # Render
    print("Rendering...")
    try:
        result = bpy.ops.render.render(write_still=True)
        print(f"Render result: {result}")
    except Exception as e:
        # Some warnings may be raised as exceptions, check if file was written
        print(f"Render exception (may be warning): {e}")

    # Check if file was written
    if os.path.exists(output_path):
        print(f"Saved: {output_path}")
        return True
    else:
        print(f"ERROR: Output file not created: {output_path}")
        return False


def main():
    """Main entry point."""
    # Parse arguments
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = []

    # Parse output directory
    output_dir = "docs/images/characters"
    for i, arg in enumerate(argv):
        if arg == "--output-dir" and i + 1 < len(argv):
            output_dir = argv[i + 1]

    # Get project root (this script is in scripts/)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    # Character model paths
    characters = {
        'mia': project_root / 'models' / 'characters' / 'mia.blend',
        'leo': project_root / 'models' / 'characters' / 'leo.blend',
        'gabe': project_root / 'models' / 'characters' / 'gabe.blend',
        'nina': project_root / 'models' / 'characters' / 'nina.blend',
        'ruben': project_root / 'assets' / 'models' / 'characters' / 'ruben.blend',
        'jetplane': project_root / 'assets' / 'models' / 'characters' / 'jetplane.blend',
    }

    # Output directory
    output_path = project_root / output_dir
    output_path.mkdir(parents=True, exist_ok=True)

    print(f"Project root: {project_root}")
    print(f"Output directory: {output_path}")

    # Render each character
    results = {}
    for name, blend_file in characters.items():
        if not blend_file.exists():
            print(f"WARNING: {blend_file} not found, skipping")
            results[name] = {'success': False, 'error': 'File not found'}
            continue

        output_file = output_path / f"{name}-preview.png"
        try:
            render_character(str(blend_file), str(output_file))
            results[name] = {'success': True, 'output': str(output_file)}
        except Exception as e:
            print(f"ERROR rendering {name}: {e}")
            results[name] = {'success': False, 'error': str(e)}

    # Summary
    print(f"\n{'='*60}")
    print("RENDERING SUMMARY")
    print(f"{'='*60}")
    for name, result in results.items():
        status = "✓" if result.get('success') else "✗"
        print(f"{status} {name}: {result.get('output', result.get('error'))}")

    success_count = sum(1 for r in results.values() if r.get('success'))
    print(f"\nCompleted: {success_count}/{len(characters)} characters")


if __name__ == "__main__":
    main()
