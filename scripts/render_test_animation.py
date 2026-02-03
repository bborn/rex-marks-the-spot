#!/usr/bin/env python3
"""
Test Animation Script - First Animated Scene for Pipeline Validation

Creates a 12-second (288 frames @ 24fps) test animation demonstrating:
- Character stand-in animation (walking, interacting)
- Camera dolly/orbit movement
- Basic lighting and environment

This proves the headless Blender pipeline works for animation production.

Usage:
    blender -b -P scripts/render_test_animation.py

With options:
    blender -b -P scripts/render_test_animation.py -- --output renders/test_anim/frame_ --samples 32 --preview
"""

import bpy
import sys
import os
import math
from mathutils import Vector, Euler


def parse_args():
    """Parse command line arguments after '--'"""
    args = {
        'output': 'renders/test_animation/frame_',
        'samples': 64,
        'preview': False,
        'resolution': (1920, 1080),
        'fps': 24,
        'duration': 12,  # seconds
    }

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
            elif argv[i] == '--preview':
                args['preview'] = True
                args['resolution'] = (960, 540)
                args['samples'] = 16
                i += 1
            elif argv[i] == '--duration' and i + 1 < len(argv):
                args['duration'] = int(argv[i + 1])
                i += 2
            else:
                i += 1

    return args


def clear_scene():
    """Remove all objects from the scene"""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

    # Clean up orphan data
    for block in bpy.data.meshes:
        if block.users == 0:
            bpy.data.meshes.remove(block)
    for block in bpy.data.materials:
        if block.users == 0:
            bpy.data.materials.remove(block)


def create_material(name, color, roughness=0.5, metallic=0.0):
    """Create a principled BSDF material"""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = color
        bsdf.inputs["Roughness"].default_value = roughness
        bsdf.inputs["Metallic"].default_value = metallic
    return mat


def create_ground():
    """Create ground plane with grass-like material"""
    bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, 0))
    ground = bpy.context.active_object
    ground.name = "Ground"

    mat = create_material("GroundMat", (0.15, 0.4, 0.1, 1.0), roughness=0.9)
    ground.data.materials.append(mat)
    return ground


def create_character_standin(name, color, location, height=1.8):
    """
    Create a simple character stand-in (body + head + arms indication).
    Returns the root empty that parents everything.
    """
    # Create root empty for animation
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=location)
    root = bpy.context.active_object
    root.name = f"{name}_Root"
    root.empty_display_size = 0.5

    # Body proportions
    body_height = height * 0.55
    body_radius = height * 0.18
    head_radius = height * 0.12

    # Body (cylinder)
    bpy.ops.mesh.primitive_cylinder_add(
        radius=body_radius,
        depth=body_height,
        location=(0, 0, body_height / 2 + 0.1)
    )
    body = bpy.context.active_object
    body.name = f"{name}_Body"
    body.parent = root

    # Head (sphere)
    bpy.ops.mesh.primitive_uv_sphere_add(
        radius=head_radius,
        location=(0, 0, body_height + head_radius + 0.15)
    )
    head = bpy.context.active_object
    head.name = f"{name}_Head"
    head.parent = root

    # Arms indication (small horizontal cylinder)
    bpy.ops.mesh.primitive_cylinder_add(
        radius=height * 0.06,
        depth=height * 0.5,
        rotation=(0, math.radians(90), 0),
        location=(0, 0, body_height * 0.8)
    )
    arms = bpy.context.active_object
    arms.name = f"{name}_Arms"
    arms.parent = root

    # Apply material
    mat = create_material(f"{name}Mat", color, roughness=0.6)
    body.data.materials.append(mat)
    head.data.materials.append(mat)
    arms.data.materials.append(mat)

    return root


def create_simple_house():
    """Create a simple house as background element"""
    # House body
    bpy.ops.mesh.primitive_cube_add(size=4, location=(-8, 8, 2))
    house = bpy.context.active_object
    house.name = "House_Body"
    house.scale = (1, 1.5, 1)

    mat = create_material("HouseMat", (0.85, 0.8, 0.7, 1.0), roughness=0.9)
    house.data.materials.append(mat)

    # Roof
    bpy.ops.mesh.primitive_cone_add(
        radius1=3.5,
        radius2=0,
        depth=2.5,
        location=(-8, 8, 5.25)
    )
    roof = bpy.context.active_object
    roof.name = "House_Roof"
    roof.scale = (1, 1.5, 1)

    roof_mat = create_material("RoofMat", (0.5, 0.25, 0.15, 1.0), roughness=0.85)
    roof.data.materials.append(roof_mat)

    return house


def create_trees(positions):
    """Create simple trees at given positions"""
    trees = []
    for i, (x, y) in enumerate(positions):
        # Trunk
        bpy.ops.mesh.primitive_cylinder_add(
            radius=0.15,
            depth=1.5,
            location=(x, y, 0.75)
        )
        trunk = bpy.context.active_object
        trunk.name = f"Tree_{i}_Trunk"

        trunk_mat = create_material(f"TrunkMat_{i}", (0.35, 0.2, 0.1, 1.0), roughness=0.95)
        trunk.data.materials.append(trunk_mat)

        # Foliage (cone)
        bpy.ops.mesh.primitive_cone_add(
            radius1=1.0,
            depth=2.0,
            location=(x, y, 2.5)
        )
        foliage = bpy.context.active_object
        foliage.name = f"Tree_{i}_Foliage"

        foliage_mat = create_material(f"FoliageMat_{i}", (0.1, 0.5, 0.15, 1.0), roughness=0.8)
        foliage.data.materials.append(foliage_mat)

        trees.append((trunk, foliage))

    return trees


def setup_lighting():
    """Create lighting for the scene"""
    # Main sun light
    bpy.ops.object.light_add(type='SUN', location=(10, -10, 15))
    sun = bpy.context.active_object
    sun.name = "Sun"
    sun.data.energy = 4.0
    sun.data.color = (1.0, 0.95, 0.9)
    sun.rotation_euler = (math.radians(45), math.radians(15), math.radians(30))

    # Fill light (area)
    bpy.ops.object.light_add(type='AREA', location=(-5, -8, 6))
    fill = bpy.context.active_object
    fill.name = "Fill_Light"
    fill.data.energy = 150.0
    fill.data.size = 4.0
    fill.rotation_euler = (math.radians(60), 0, math.radians(-30))

    return sun, fill


def setup_world():
    """Setup sky/world background"""
    world = bpy.context.scene.world
    if world is None:
        world = bpy.data.worlds.new("World")
        bpy.context.scene.world = world

    world.use_nodes = True
    nodes = world.node_tree.nodes
    links = world.node_tree.links
    nodes.clear()

    # Create gradient sky
    coord = nodes.new('ShaderNodeTexCoord')
    mapping = nodes.new('ShaderNodeMapping')
    gradient = nodes.new('ShaderNodeTexGradient')
    ramp = nodes.new('ShaderNodeValToRGB')
    background = nodes.new('ShaderNodeBackground')
    output = nodes.new('ShaderNodeOutputWorld')

    # Sky colors
    ramp.color_ramp.elements[0].color = (0.6, 0.8, 1.0, 1.0)  # Horizon
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[1].color = (0.2, 0.4, 0.9, 1.0)  # Zenith
    ramp.color_ramp.elements[1].position = 1.0

    background.inputs["Strength"].default_value = 1.0

    # Link nodes
    links.new(coord.outputs["Generated"], mapping.inputs["Vector"])
    links.new(mapping.outputs["Vector"], gradient.inputs["Vector"])
    links.new(gradient.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], background.inputs["Color"])
    links.new(background.outputs["Background"], output.inputs["Surface"])


def setup_camera():
    """Create and position camera"""
    bpy.ops.object.camera_add(location=(8, -10, 3))
    camera = bpy.context.active_object
    camera.name = "MainCamera"
    camera.data.lens = 35  # Wide-ish lens for scene establishing

    bpy.context.scene.camera = camera
    return camera


def animate_character_walk(char_root, start_frame, end_frame, start_pos, end_pos):
    """Animate a character walking from start to end position"""
    scene = bpy.context.scene

    # Calculate walk parameters
    total_frames = end_frame - start_frame
    distance = Vector(end_pos) - Vector(start_pos)

    # Keyframe start position
    scene.frame_set(start_frame)
    char_root.location = start_pos
    char_root.keyframe_insert(data_path="location", frame=start_frame)

    # Add bobbing motion during walk
    steps = int(total_frames / 12)  # One "step" every 12 frames (0.5 sec at 24fps)
    for step in range(steps + 1):
        frame = start_frame + step * 12
        if frame > end_frame:
            frame = end_frame

        progress = step / max(steps, 1)
        pos = Vector(start_pos) + distance * progress

        # Add slight bob
        bob = 0.05 * math.sin(step * math.pi)
        pos.z += bob

        scene.frame_set(frame)
        char_root.location = pos
        char_root.keyframe_insert(data_path="location", frame=frame)

    # Ensure end position is exact
    scene.frame_set(end_frame)
    char_root.location = end_pos
    char_root.keyframe_insert(data_path="location", frame=end_frame)

    # Set interpolation to smooth
    if char_root.animation_data and char_root.animation_data.action:
        for fc in char_root.animation_data.action.fcurves:
            for kf in fc.keyframe_points:
                kf.interpolation = 'BEZIER'


def animate_character_turn(char_root, frame, target_angle_deg):
    """Animate character turning to face a direction"""
    scene = bpy.context.scene
    scene.frame_set(frame)
    char_root.rotation_euler = (0, 0, math.radians(target_angle_deg))
    char_root.keyframe_insert(data_path="rotation_euler", frame=frame)


def animate_camera_dolly(camera, start_frame, end_frame, start_pos, end_pos, look_at_target):
    """Animate camera dolly movement while tracking a target"""
    scene = bpy.context.scene

    # Create look-at target empty
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=look_at_target)
    target = bpy.context.active_object
    target.name = "Camera_Target"

    # Add Track To constraint
    constraint = camera.constraints.new(type='TRACK_TO')
    constraint.target = target
    constraint.track_axis = 'TRACK_NEGATIVE_Z'
    constraint.up_axis = 'UP_Y'

    # Keyframe camera positions
    total_frames = end_frame - start_frame

    for i in range(total_frames + 1):
        frame = start_frame + i
        progress = i / total_frames

        # Smooth ease in/out
        smooth_progress = 0.5 - 0.5 * math.cos(progress * math.pi)

        pos = Vector(start_pos).lerp(Vector(end_pos), smooth_progress)

        scene.frame_set(frame)
        camera.location = pos
        camera.keyframe_insert(data_path="location", frame=frame)


def configure_render(args):
    """Configure render settings"""
    scene = bpy.context.scene
    render = scene.render

    # Ensure output directory exists
    output_dir = os.path.dirname(os.path.abspath(args['output']))
    os.makedirs(output_dir, exist_ok=True)

    render.filepath = os.path.abspath(args['output'])
    render.image_settings.file_format = 'PNG'
    render.resolution_x = args['resolution'][0]
    render.resolution_y = args['resolution'][1]
    render.resolution_percentage = 100

    # Frame range
    total_frames = args['fps'] * args['duration']
    scene.frame_start = 1
    scene.frame_end = total_frames
    scene.render.fps = args['fps']

    # Cycles settings
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = args['samples']

    # Disable denoising for compatibility (some builds don't have OIDN)
    scene.cycles.use_denoising = False

    # Try GPU rendering
    try:
        prefs = bpy.context.preferences.addons['cycles'].preferences
        for device_type in ['OPTIX', 'CUDA', 'HIP', 'METAL', 'NONE']:
            try:
                prefs.compute_device_type = device_type
                prefs.get_devices()
                if prefs.devices:
                    for device in prefs.devices:
                        device.use = True
                    if device_type != 'NONE':
                        scene.cycles.device = 'GPU'
                        print(f"Using GPU: {device_type}")
                        break
            except:
                continue
        else:
            scene.cycles.device = 'CPU'
            print("Using CPU rendering")
    except Exception as e:
        scene.cycles.device = 'CPU'
        print(f"GPU setup failed: {e}")

    return total_frames


def main():
    """Main function - create scene, animate, and render"""
    args = parse_args()

    print("=" * 60)
    print("Fairy Dinosaur Date Night - Test Animation Pipeline")
    print("=" * 60)

    # Setup
    print("\n[1/8] Clearing scene...")
    clear_scene()

    print("[2/8] Creating environment...")
    create_ground()
    create_simple_house()
    create_trees([
        (-4, 5), (3, 7), (6, 4), (-6, -3), (5, -5), (-3, -6)
    ])

    print("[3/8] Creating characters...")
    # Character colors inspired by the movie characters
    # Mia (kid) - blue outfit
    mia = create_character_standin(
        "Mia",
        color=(0.2, 0.4, 0.8, 1.0),
        location=(-3, -2, 0),
        height=1.2
    )

    # Leo (kid) - green outfit
    leo = create_character_standin(
        "Leo",
        color=(0.2, 0.7, 0.3, 1.0),
        location=(-5, -2, 0),
        height=1.3
    )

    # Parent figure - warm orange
    parent = create_character_standin(
        "Parent",
        color=(0.9, 0.5, 0.2, 1.0),
        location=(-8, 0, 0),
        height=1.8
    )

    print("[4/8] Setting up lighting...")
    setup_lighting()
    setup_world()

    print("[5/8] Setting up camera...")
    camera = setup_camera()

    print("[6/8] Creating animations...")
    fps = args['fps']

    # Animation timeline (12 seconds = 288 frames at 24fps):
    # 0-3s (1-72): Camera establishes scene, parent walks toward kids
    # 3-7s (73-168): Kids notice parent, turn and wave
    # 7-12s (169-288): Family walks together toward house

    # Parent walks from far to near kids
    animate_character_walk(parent, 1, 72, (-8, 0, 0), (-4, -1, 0))
    animate_character_turn(parent, 1, -90)  # Facing toward kids initially

    # Kids react - turn to face parent
    animate_character_turn(mia, 60, 180)  # Turn to face parent
    animate_character_turn(leo, 65, 160)

    # Family walks together toward house
    animate_character_walk(mia, 169, 288, (-3, -2, 0), (-6, 4, 0))
    animate_character_walk(leo, 169, 288, (-5, -2, 0), (-7, 3, 0))
    animate_character_walk(parent, 169, 288, (-4, -1, 0), (-8, 5, 0))

    # Update turns for walking direction
    animate_character_turn(mia, 169, 45)
    animate_character_turn(leo, 169, 50)
    animate_character_turn(parent, 169, 45)

    # Camera movement - dolly from wide establishing to closer
    animate_camera_dolly(
        camera,
        start_frame=1,
        end_frame=288,
        start_pos=(10, -12, 4),
        end_pos=(2, -6, 2.5),
        look_at_target=(0, 0, 1.2)
    )

    print("[7/8] Configuring render settings...")
    total_frames = configure_render(args)

    print(f"\n[8/8] Rendering {total_frames} frames...")
    print(f"Output: {os.path.abspath(args['output'])}")
    print(f"Resolution: {args['resolution'][0]}x{args['resolution'][1]}")
    print(f"Samples: {args['samples']}")
    print(f"Duration: {args['duration']}s @ {args['fps']}fps")
    print("\nThis will take a while. Progress:")

    # Render animation
    bpy.ops.render.render(animation=True)

    print("\n" + "=" * 60)
    print("RENDER COMPLETE!")
    print("=" * 60)

    output_dir = os.path.dirname(os.path.abspath(args['output']))
    print(f"\nFrames saved to: {output_dir}")
    print(f"Total frames: {total_frames}")

    print("\nTo create video from frames, run:")
    print(f"  ffmpeg -framerate {args['fps']} -i {args['output']}%04d.png -c:v libx264 -pix_fmt yuv420p output.mp4")

    # Scene summary
    print("\n[Scene Summary]")
    print("- Environment: Grass ground, simple house, 6 trees")
    print("- Characters: 3 stand-ins (Mia-blue, Leo-green, Parent-orange)")
    print("- Animation: Parent approaches kids, family walks to house")
    print("- Camera: Dolly from wide shot to medium close-up")
    print("- Lighting: Sun + fill light, gradient sky")


if __name__ == "__main__":
    main()
