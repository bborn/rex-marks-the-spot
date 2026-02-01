#!/usr/bin/env python3
"""
Proof of Concept: Blender Scene Creation Script

This script demonstrates that Claude can generate Blender Python scripts
that create 3D scenes and render them headlessly.

Usage:
    blender -b -P scripts/poc_create_scene.py

Or with output path:
    blender -b -P scripts/poc_create_scene.py -- --output renders/test.png
"""

import bpy
import sys
import os
import math

def parse_args():
    """Parse command line arguments after '--'"""
    args = {'output': 'render_output.png', 'samples': 64}

    if '--' in sys.argv:
        argv = sys.argv[sys.argv.index('--') + 1:]
        i = 0
        while i < len(argv):
            if argv[i] == '--output' and i + 1 < len(argv):
                args['output'] = argv[i + 1]
                i += 2
            elif argv[i] == '--samples' and i + 1 < len(argv):
                args['samples'] = int(argv[i + 1])
                i += 2
            else:
                i += 1

    return args


def clear_scene():
    """Remove all objects from the scene"""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()


def create_ground_plane():
    """Create a ground plane with a material"""
    bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, 0))
    plane = bpy.context.active_object
    plane.name = "Ground"

    # Create material
    mat = bpy.data.materials.new(name="GroundMaterial")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    bsdf = nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.2, 0.5, 0.2, 1.0)  # Green
        bsdf.inputs["Roughness"].default_value = 0.8

    plane.data.materials.append(mat)
    return plane


def create_character_placeholder():
    """Create a simple character placeholder (capsule shape)"""
    # Body (cylinder)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.5, depth=1.5, location=(0, 0, 1.25))
    body = bpy.context.active_object
    body.name = "CharacterBody"

    # Head (sphere)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.4, location=(0, 0, 2.25))
    head = bpy.context.active_object
    head.name = "CharacterHead"

    # Create material
    mat = bpy.data.materials.new(name="CharacterMaterial")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    bsdf = nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.8, 0.4, 0.2, 1.0)  # Orange
        bsdf.inputs["Roughness"].default_value = 0.5

    body.data.materials.append(mat)
    head.data.materials.append(mat)

    return body, head


def create_simple_tree(location):
    """Create a simple tree (cone + cylinder)"""
    x, y = location

    # Trunk
    bpy.ops.mesh.primitive_cylinder_add(radius=0.15, depth=1.0, location=(x, y, 0.5))
    trunk = bpy.context.active_object
    trunk.name = f"TreeTrunk_{x}_{y}"

    trunk_mat = bpy.data.materials.new(name=f"TrunkMaterial_{x}_{y}")
    trunk_mat.use_nodes = True
    bsdf = trunk_mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.4, 0.25, 0.1, 1.0)  # Brown
    trunk.data.materials.append(trunk_mat)

    # Foliage
    bpy.ops.mesh.primitive_cone_add(radius1=0.8, depth=1.5, location=(x, y, 1.75))
    foliage = bpy.context.active_object
    foliage.name = f"TreeFoliage_{x}_{y}"

    foliage_mat = bpy.data.materials.new(name=f"FoliageMaterial_{x}_{y}")
    foliage_mat.use_nodes = True
    bsdf = foliage_mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.1, 0.6, 0.2, 1.0)  # Dark green
    foliage.data.materials.append(foliage_mat)

    return trunk, foliage


def setup_lighting():
    """Create a three-point lighting setup"""
    # Key light (sun)
    bpy.ops.object.light_add(type='SUN', location=(5, -5, 10))
    key_light = bpy.context.active_object
    key_light.name = "KeyLight"
    key_light.data.energy = 3.0
    key_light.rotation_euler = (math.radians(45), math.radians(15), math.radians(45))

    # Fill light
    bpy.ops.object.light_add(type='AREA', location=(-4, -3, 5))
    fill_light = bpy.context.active_object
    fill_light.name = "FillLight"
    fill_light.data.energy = 100.0
    fill_light.data.size = 3.0

    # Rim light
    bpy.ops.object.light_add(type='SPOT', location=(0, 5, 4))
    rim_light = bpy.context.active_object
    rim_light.name = "RimLight"
    rim_light.data.energy = 200.0
    rim_light.rotation_euler = (math.radians(-30), 0, math.radians(180))

    return key_light, fill_light, rim_light


def setup_camera():
    """Create and position the camera"""
    bpy.ops.object.camera_add(location=(6, -6, 4))
    camera = bpy.context.active_object
    camera.name = "MainCamera"

    # Point camera at origin
    bpy.ops.object.constraint_add(type='TRACK_TO')
    camera.constraints["Track To"].target = bpy.data.objects.get("CharacterBody")
    camera.constraints["Track To"].track_axis = 'TRACK_NEGATIVE_Z'
    camera.constraints["Track To"].up_axis = 'UP_Y'

    # Set as active camera
    bpy.context.scene.camera = camera

    return camera


def setup_world():
    """Configure world/environment settings"""
    world = bpy.context.scene.world
    if world is None:
        world = bpy.data.worlds.new("World")
        bpy.context.scene.world = world

    world.use_nodes = True
    nodes = world.node_tree.nodes
    links = world.node_tree.links

    # Clear existing nodes
    nodes.clear()

    # Create gradient sky
    node_background = nodes.new(type='ShaderNodeBackground')
    node_output = nodes.new(type='ShaderNodeOutputWorld')
    node_gradient = nodes.new(type='ShaderNodeTexGradient')
    node_mapping = nodes.new(type='ShaderNodeMapping')
    node_coord = nodes.new(type='ShaderNodeTexCoord')
    node_colorramp = nodes.new(type='ShaderNodeValToRGB')

    # Configure color ramp for sky gradient
    node_colorramp.color_ramp.elements[0].color = (0.5, 0.7, 1.0, 1.0)  # Light blue
    node_colorramp.color_ramp.elements[1].color = (0.1, 0.3, 0.8, 1.0)  # Deep blue
    node_colorramp.color_ramp.elements[0].position = 0.0
    node_colorramp.color_ramp.elements[1].position = 1.0

    # Link nodes
    links.new(node_coord.outputs["Generated"], node_mapping.inputs["Vector"])
    links.new(node_mapping.outputs["Vector"], node_gradient.inputs["Vector"])
    links.new(node_gradient.outputs["Fac"], node_colorramp.inputs["Fac"])
    links.new(node_colorramp.outputs["Color"], node_background.inputs["Color"])
    links.new(node_background.outputs["Background"], node_output.inputs["Surface"])

    node_background.inputs["Strength"].default_value = 1.0


def configure_render_settings(output_path, samples=64):
    """Configure render settings for output"""
    scene = bpy.context.scene
    render = scene.render

    # Output settings
    render.filepath = output_path
    render.image_settings.file_format = 'PNG'
    render.resolution_x = 1920
    render.resolution_y = 1080
    render.resolution_percentage = 100

    # Use Cycles for quality
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = samples

    # Disable denoising if not available
    scene.cycles.use_denoising = False

    # Try to use GPU if available
    try:
        prefs = bpy.context.preferences.addons['cycles'].preferences
        # Try CUDA first, then OptiX, then HIP, finally CPU
        for device_type in ['CUDA', 'OPTIX', 'HIP', 'NONE']:
            try:
                prefs.compute_device_type = device_type
                prefs.get_devices()
                if prefs.devices:
                    for device in prefs.devices:
                        device.use = True
                    if device_type != 'NONE':
                        scene.cycles.device = 'GPU'
                        print(f"Using GPU rendering with {device_type}")
                    break
            except:
                continue
        else:
            scene.cycles.device = 'CPU'
            print("Using CPU rendering")
    except Exception as e:
        scene.cycles.device = 'CPU'
        print(f"GPU setup failed, using CPU: {e}")

    print(f"Render settings configured: {render.resolution_x}x{render.resolution_y}, {samples} samples")


def main():
    """Main function to create scene and render"""
    args = parse_args()

    print("=" * 50)
    print("Blender + LLM Integration Proof of Concept")
    print("=" * 50)

    # Step 1: Clear existing scene
    print("\n[1/7] Clearing scene...")
    clear_scene()

    # Step 2: Create ground
    print("[2/7] Creating ground plane...")
    create_ground_plane()

    # Step 3: Create character placeholder
    print("[3/7] Creating character placeholder...")
    create_character_placeholder()

    # Step 4: Create environment (trees)
    print("[4/7] Creating environment...")
    tree_positions = [(-3, 3), (4, 2), (-2, -4), (3, -3)]
    for pos in tree_positions:
        create_simple_tree(pos)

    # Step 5: Setup lighting
    print("[5/7] Setting up lighting...")
    setup_lighting()

    # Step 6: Setup camera
    print("[6/7] Setting up camera...")
    setup_camera()

    # Step 7: Configure world
    print("[7/7] Configuring world/sky...")
    setup_world()

    # Configure render settings
    output_path = os.path.abspath(args['output'])
    configure_render_settings(output_path, args['samples'])

    # Render
    print(f"\nRendering to: {output_path}")
    print("This may take a moment...")
    bpy.ops.render.render(write_still=True)

    print(f"\n{'=' * 50}")
    print(f"Render complete: {output_path}")
    print(f"{'=' * 50}")

    # Scene summary for vision validation
    print("\n[Scene Summary for Vision Validation]")
    print("- Ground: Green plane (20x20 units)")
    print("- Character: Orange capsule shape (body + head) at center")
    print("- Trees: 4 simple trees (brown trunk, green cone foliage)")
    print("- Lighting: Three-point setup (sun + area + spot)")
    print("- Camera: Positioned at (6, -6, 4) looking at character")
    print("- Sky: Blue gradient background")


if __name__ == "__main__":
    main()
