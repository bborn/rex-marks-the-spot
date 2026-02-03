#!/usr/bin/env python3
"""
Quick Pipeline Test - Renders only 3 key frames to verify pipeline works

This is a fast test (renders frames 1, 144, 288) to verify:
1. Scene creation works
2. Animation keyframes work
3. Render pipeline works

Usage:
    blender -b -P scripts/quick_pipeline_test.py

With preview quality:
    blender -b -P scripts/quick_pipeline_test.py -- --preview
"""

import bpy
import sys
import os
import math
from mathutils import Vector


def parse_args():
    args = {
        'output': 'renders/pipeline_test/',
        'samples': 32,
        'preview': False,
        'resolution': (1280, 720),
    }

    if '--' in sys.argv:
        argv = sys.argv[sys.argv.index('--') + 1:]
        for i, arg in enumerate(argv):
            if arg == '--preview':
                args['preview'] = True
                args['resolution'] = (640, 360)
                args['samples'] = 8
            elif arg == '--output' and i + 1 < len(argv):
                args['output'] = argv[i + 1]

    return args


def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()


def create_material(name, color, roughness=0.5):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = color
        bsdf.inputs["Roughness"].default_value = roughness
    return mat


def create_test_scene():
    """Create a minimal test scene with animated elements"""

    # Ground
    bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, 0))
    ground = bpy.context.active_object
    ground.name = "Ground"
    mat = create_material("GroundMat", (0.2, 0.5, 0.2, 1.0), 0.9)
    ground.data.materials.append(mat)

    # Animated character stand-in
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(-4, 0, 0))
    char_root = bpy.context.active_object
    char_root.name = "Character_Root"

    # Body
    bpy.ops.mesh.primitive_cylinder_add(radius=0.4, depth=1.2, location=(0, 0, 0.7))
    body = bpy.context.active_object
    body.name = "Character_Body"
    body.parent = char_root

    # Head
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.25, location=(0, 0, 1.55))
    head = bpy.context.active_object
    head.name = "Character_Head"
    head.parent = char_root

    char_mat = create_material("CharMat", (0.8, 0.4, 0.2, 1.0), 0.6)
    body.data.materials.append(char_mat)
    head.data.materials.append(char_mat)

    # Animate character walking
    scene = bpy.context.scene

    # Frame 1: Start position
    scene.frame_set(1)
    char_root.location = (-4, 0, 0)
    char_root.keyframe_insert(data_path="location", frame=1)

    # Frame 144 (6s): Middle position
    scene.frame_set(144)
    char_root.location = (0, 0, 0)
    char_root.keyframe_insert(data_path="location", frame=144)

    # Frame 288 (12s): End position
    scene.frame_set(288)
    char_root.location = (4, 0, 0)
    char_root.keyframe_insert(data_path="location", frame=288)

    # Simple tree for reference
    bpy.ops.mesh.primitive_cylinder_add(radius=0.15, depth=1.5, location=(3, 4, 0.75))
    trunk = bpy.context.active_object
    trunk_mat = create_material("TrunkMat", (0.4, 0.25, 0.1, 1.0), 0.9)
    trunk.data.materials.append(trunk_mat)

    bpy.ops.mesh.primitive_cone_add(radius1=1, depth=2, location=(3, 4, 2.5))
    foliage = bpy.context.active_object
    foliage_mat = create_material("FoliageMat", (0.1, 0.5, 0.2, 1.0), 0.8)
    foliage.data.materials.append(foliage_mat)

    return char_root


def setup_lighting():
    # Sun
    bpy.ops.object.light_add(type='SUN', location=(5, -5, 10))
    sun = bpy.context.active_object
    sun.data.energy = 4.0
    sun.rotation_euler = (math.radians(45), 0, math.radians(30))

    # Fill
    bpy.ops.object.light_add(type='AREA', location=(-4, -6, 5))
    fill = bpy.context.active_object
    fill.data.energy = 100.0
    fill.data.size = 3.0


def setup_camera(char_root):
    bpy.ops.object.camera_add(location=(0, -8, 3))
    camera = bpy.context.active_object
    camera.name = "Camera"
    camera.data.lens = 35

    # Track character
    constraint = camera.constraints.new(type='TRACK_TO')
    constraint.target = char_root
    constraint.track_axis = 'TRACK_NEGATIVE_Z'
    constraint.up_axis = 'UP_Y'

    bpy.context.scene.camera = camera
    return camera


def setup_world():
    world = bpy.context.scene.world
    if not world:
        world = bpy.data.worlds.new("World")
        bpy.context.scene.world = world

    world.use_nodes = True
    nodes = world.node_tree.nodes
    nodes.clear()

    bg = nodes.new('ShaderNodeBackground')
    bg.inputs["Color"].default_value = (0.5, 0.7, 1.0, 1.0)
    bg.inputs["Strength"].default_value = 1.0

    output = nodes.new('ShaderNodeOutputWorld')
    world.node_tree.links.new(bg.outputs["Background"], output.inputs["Surface"])


def configure_render(args):
    scene = bpy.context.scene
    render = scene.render

    render.image_settings.file_format = 'PNG'
    render.resolution_x = args['resolution'][0]
    render.resolution_y = args['resolution'][1]
    render.resolution_percentage = 100

    scene.frame_start = 1
    scene.frame_end = 288
    scene.render.fps = 24

    scene.render.engine = 'CYCLES'
    scene.cycles.samples = args['samples']
    scene.cycles.use_denoising = False

    # Try GPU
    try:
        prefs = bpy.context.preferences.addons['cycles'].preferences
        for device_type in ['OPTIX', 'CUDA', 'HIP', 'NONE']:
            try:
                prefs.compute_device_type = device_type
                prefs.get_devices()
                if prefs.devices:
                    for device in prefs.devices:
                        device.use = True
                    if device_type != 'NONE':
                        scene.cycles.device = 'GPU'
                        break
            except:
                continue
        else:
            scene.cycles.device = 'CPU'
    except:
        scene.cycles.device = 'CPU'


def render_test_frames(args):
    """Render 3 key frames to test pipeline"""
    scene = bpy.context.scene

    output_dir = os.path.abspath(args['output'])
    os.makedirs(output_dir, exist_ok=True)

    test_frames = [1, 144, 288]  # Start, middle, end

    print(f"\nRendering {len(test_frames)} test frames...")

    for frame in test_frames:
        output_path = os.path.join(output_dir, f"frame_{frame:04d}.png")
        scene.render.filepath = output_path
        scene.frame_set(frame)

        print(f"  Rendering frame {frame}...")
        bpy.ops.render.render(write_still=True)
        print(f"    Saved: {output_path}")

    return test_frames


def main():
    args = parse_args()

    print("=" * 50)
    print("Quick Pipeline Test")
    print("=" * 50)

    print("\n[1/6] Clearing scene...")
    clear_scene()

    print("[2/6] Creating test scene...")
    char_root = create_test_scene()

    print("[3/6] Setting up lighting...")
    setup_lighting()
    setup_world()

    print("[4/6] Setting up camera...")
    setup_camera(char_root)

    print("[5/6] Configuring render...")
    configure_render(args)

    print("[6/6] Rendering test frames...")
    frames = render_test_frames(args)

    print("\n" + "=" * 50)
    print("PIPELINE TEST COMPLETE!")
    print("=" * 50)
    print(f"\nRendered frames: {frames}")
    print(f"Output directory: {os.path.abspath(args['output'])}")
    print("\nIf you see 3 PNG files showing the character at different positions,")
    print("the pipeline is working correctly!")


if __name__ == "__main__":
    main()
