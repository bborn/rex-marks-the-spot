#!/usr/bin/env python3
"""
Scene 01: INT. HOME - EVENING
First animated scene for Fairy Dinosaur Date Night

Creates a 45-second animated scene showing the family home with:
- Mia & Leo watching TV
- Parents (Gabe & Nina) getting ready to leave
- Warm, cozy evening lighting

Usage:
    blender -b -P scripts/render_scene01_home_evening.py -- [options]

Options:
    --preview       Low quality preview (540p, 16 samples)
    --output DIR    Output directory (default: renders/scene01)
    --frames N      Number of frames to render (default: all)
"""

import bpy
import bmesh
import sys
import os
import math
from pathlib import Path
from mathutils import Vector, Euler

# Parse arguments
def parse_args():
    args = {
        'preview': False,
        'output': 'renders/scene01_home_evening',
        'frames': None,  # None = all frames
    }

    if '--' in sys.argv:
        argv = sys.argv[sys.argv.index('--') + 1:]
        i = 0
        while i < len(argv):
            if argv[i] == '--preview':
                args['preview'] = True
                i += 1
            elif argv[i] == '--output' and i + 1 < len(argv):
                args['output'] = argv[i + 1]
                i += 2
            elif argv[i] == '--frames' and i + 1 < len(argv):
                args['frames'] = int(argv[i + 1])
                i += 2
            else:
                i += 1

    return args


def clear_scene():
    """Remove all objects from scene"""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

    # Clean orphan data
    for block in bpy.data.meshes:
        if block.users == 0:
            bpy.data.meshes.remove(block)
    for block in bpy.data.materials:
        if block.users == 0:
            bpy.data.materials.remove(block)


def create_material(name, color, roughness=0.5, metallic=0.0, emission=0.0):
    """Create a principled BSDF material"""
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


def create_living_room():
    """Create a cozy living room interior"""
    room_objects = []

    # Floor
    bpy.ops.mesh.primitive_plane_add(size=8, location=(0, 0, 0))
    floor = bpy.context.active_object
    floor.name = "Floor"
    floor_mat = create_material("FloorMat", (0.35, 0.25, 0.15, 1.0), roughness=0.7)
    floor.data.materials.append(floor_mat)
    room_objects.append(floor)

    # Back wall
    bpy.ops.mesh.primitive_plane_add(size=8, location=(0, 4, 2))
    back_wall = bpy.context.active_object
    back_wall.name = "BackWall"
    back_wall.rotation_euler = (math.radians(90), 0, 0)
    wall_mat = create_material("WallMat", (0.9, 0.85, 0.75, 1.0), roughness=0.9)
    back_wall.data.materials.append(wall_mat)
    room_objects.append(back_wall)

    # Left wall
    bpy.ops.mesh.primitive_plane_add(size=8, location=(-4, 0, 2))
    left_wall = bpy.context.active_object
    left_wall.name = "LeftWall"
    left_wall.rotation_euler = (math.radians(90), 0, math.radians(90))
    left_wall.data.materials.append(wall_mat)
    room_objects.append(left_wall)

    # Right wall
    bpy.ops.mesh.primitive_plane_add(size=8, location=(4, 0, 2))
    right_wall = bpy.context.active_object
    right_wall.name = "RightWall"
    right_wall.rotation_euler = (math.radians(90), 0, math.radians(-90))
    right_wall.data.materials.append(wall_mat)
    room_objects.append(right_wall)

    return room_objects


def create_couch():
    """Create a cozy couch for the kids"""
    # Couch base
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 1.5, 0.35))
    couch_base = bpy.context.active_object
    couch_base.name = "Couch_Base"
    couch_base.scale = (1.5, 0.5, 0.35)
    couch_mat = create_material("CouchMat", (0.4, 0.25, 0.15, 1.0), roughness=0.8)
    couch_base.data.materials.append(couch_mat)

    # Couch back
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 1.9, 0.7))
    couch_back = bpy.context.active_object
    couch_back.name = "Couch_Back"
    couch_back.scale = (1.5, 0.15, 0.5)
    couch_back.data.materials.append(couch_mat)

    # Couch cushions
    cushion_mat = create_material("CushionMat", (0.5, 0.35, 0.2, 1.0), roughness=0.9)
    for i, x in enumerate([-0.6, 0.6]):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(x, 1.5, 0.55))
        cushion = bpy.context.active_object
        cushion.name = f"Couch_Cushion_{i}"
        cushion.scale = (0.5, 0.35, 0.15)
        cushion.data.materials.append(cushion_mat)

    return couch_base


def create_tv():
    """Create a TV on a stand"""
    # TV stand
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 3.2, 0.4))
    stand = bpy.context.active_object
    stand.name = "TV_Stand"
    stand.scale = (1.2, 0.3, 0.4)
    stand_mat = create_material("StandMat", (0.15, 0.1, 0.05, 1.0), roughness=0.5)
    stand.data.materials.append(stand_mat)

    # TV screen
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 3.1, 1.2))
    tv = bpy.context.active_object
    tv.name = "TV_Screen"
    tv.scale = (1.0, 0.05, 0.6)
    # TV screen with glow (shows cartoon playing)
    tv_mat = create_material("TVMat", (0.3, 0.5, 0.8, 1.0), roughness=0.1, emission=2.0)
    tv.data.materials.append(tv_mat)

    return tv


def create_window():
    """Create a window showing evening sky"""
    # Window frame
    bpy.ops.mesh.primitive_cube_add(size=1, location=(-3.9, 1, 1.5))
    frame = bpy.context.active_object
    frame.name = "Window_Frame"
    frame.scale = (0.1, 1.0, 0.8)
    frame_mat = create_material("FrameMat", (0.8, 0.75, 0.7, 1.0), roughness=0.7)
    frame.data.materials.append(frame_mat)

    # Window glass (shows evening orange/pink sky)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(-3.85, 1, 1.5))
    glass = bpy.context.active_object
    glass.name = "Window_Glass"
    glass.scale = (0.9, 0.75, 1.0)
    glass.rotation_euler = (0, math.radians(90), 0)
    glass_mat = create_material("GlassMat", (1.0, 0.7, 0.4, 1.0), roughness=0.1, emission=0.5)
    glass.data.materials.append(glass_mat)

    return glass


def create_lamp():
    """Create a warm floor lamp"""
    # Lamp base
    bpy.ops.mesh.primitive_cylinder_add(radius=0.15, depth=0.1, location=(2.5, 2, 0.05))
    base = bpy.context.active_object
    base.name = "Lamp_Base"
    lamp_mat = create_material("LampMat", (0.2, 0.15, 0.1, 1.0), roughness=0.3, metallic=0.5)
    base.data.materials.append(lamp_mat)

    # Lamp pole
    bpy.ops.mesh.primitive_cylinder_add(radius=0.03, depth=1.5, location=(2.5, 2, 0.8))
    pole = bpy.context.active_object
    pole.name = "Lamp_Pole"
    pole.data.materials.append(lamp_mat)

    # Lamp shade
    bpy.ops.mesh.primitive_cone_add(radius1=0.3, radius2=0.15, depth=0.3, location=(2.5, 2, 1.6))
    shade = bpy.context.active_object
    shade.name = "Lamp_Shade"
    shade.rotation_euler = (math.radians(180), 0, 0)
    shade_mat = create_material("ShadeMat", (1.0, 0.9, 0.7, 1.0), roughness=0.95, emission=1.0)
    shade.data.materials.append(shade_mat)

    # Add actual light
    bpy.ops.object.light_add(type='POINT', location=(2.5, 2, 1.5))
    light = bpy.context.active_object
    light.name = "Lamp_Light"
    light.data.energy = 100
    light.data.color = (1.0, 0.9, 0.7)

    return shade


def create_dino_toys():
    """Create scattered dinosaur toys"""
    toys = []
    positions = [
        (-1.5, 0.5, 0.1),
        (1.2, 0.8, 0.1),
        (-0.5, 2.5, 0.1),
        (0.8, 2.2, 0.15),
    ]
    colors = [
        (0.2, 0.7, 0.3, 1.0),  # Green
        (0.8, 0.3, 0.2, 1.0),  # Red
        (0.3, 0.4, 0.8, 1.0),  # Blue
        (0.9, 0.7, 0.2, 1.0),  # Yellow
    ]

    for i, (pos, color) in enumerate(zip(positions, colors)):
        # Simple dino toy (cone body + sphere head)
        bpy.ops.mesh.primitive_cone_add(radius1=0.12, radius2=0.05, depth=0.2, location=pos)
        body = bpy.context.active_object
        body.name = f"DinoToy_{i}_Body"
        body.rotation_euler = (math.radians(-20), 0, math.radians(45 * i))
        dino_mat = create_material(f"DinoMat_{i}", color, roughness=0.7)
        body.data.materials.append(dino_mat)

        # Head
        head_pos = (pos[0] + 0.08, pos[1], pos[2] + 0.15)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.06, location=head_pos)
        head = bpy.context.active_object
        head.name = f"DinoToy_{i}_Head"
        head.data.materials.append(dino_mat)
        toys.append(body)

    return toys


def create_character_standin(name, color, location, height=1.8, pose='standing'):
    """Create a simple character stand-in"""
    # Root empty
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=location)
    root = bpy.context.active_object
    root.name = f"{name}_Root"
    root.empty_display_size = 0.3

    # Body proportions
    body_height = height * 0.55
    body_radius = height * 0.15
    head_radius = height * 0.12

    # Create material
    mat = create_material(f"{name}Mat", color, roughness=0.6)

    # Body
    body_z = body_height / 2 + 0.1
    if pose == 'sitting':
        body_z = 0.5

    bpy.ops.mesh.primitive_cylinder_add(
        radius=body_radius,
        depth=body_height,
        location=(0, 0, body_z)
    )
    body = bpy.context.active_object
    body.name = f"{name}_Body"
    body.parent = root
    body.data.materials.append(mat)

    # Head
    head_z = body_z + body_height/2 + head_radius + 0.05
    if pose == 'sitting':
        head_z = body_z + body_height/2 + head_radius + 0.05

    bpy.ops.mesh.primitive_uv_sphere_add(radius=head_radius, location=(0, 0, head_z))
    head = bpy.context.active_object
    head.name = f"{name}_Head"
    head.parent = root
    head.data.materials.append(mat)

    # Arms
    arm_z = body_z + body_height * 0.3
    bpy.ops.mesh.primitive_cylinder_add(
        radius=height * 0.05,
        depth=height * 0.35,
        rotation=(0, math.radians(90), 0),
        location=(0, 0, arm_z)
    )
    arms = bpy.context.active_object
    arms.name = f"{name}_Arms"
    arms.parent = root
    arms.data.materials.append(mat)

    # Legs (if standing)
    if pose == 'standing':
        for side, x_offset in [('L', -0.1), ('R', 0.1)]:
            bpy.ops.mesh.primitive_cylinder_add(
                radius=height * 0.06,
                depth=height * 0.4,
                location=(x_offset, 0, height * 0.2)
            )
            leg = bpy.context.active_object
            leg.name = f"{name}_Leg_{side}"
            leg.parent = root
            leg.data.materials.append(mat)

    return root


def setup_lighting():
    """Create warm evening lighting"""
    # Main area light (simulating ceiling light)
    bpy.ops.object.light_add(type='AREA', location=(0, 1, 3.5))
    main_light = bpy.context.active_object
    main_light.name = "Main_Light"
    main_light.data.energy = 200
    main_light.data.size = 2.0
    main_light.data.color = (1.0, 0.9, 0.75)

    # Window light (evening sun)
    bpy.ops.object.light_add(type='AREA', location=(-3.5, 1, 1.5))
    window_light = bpy.context.active_object
    window_light.name = "Window_Light"
    window_light.data.energy = 150
    window_light.data.size = 1.5
    window_light.data.color = (1.0, 0.6, 0.3)  # Warm sunset
    window_light.rotation_euler = (0, math.radians(-90), 0)

    # Fill light
    bpy.ops.object.light_add(type='AREA', location=(3, -1, 2))
    fill_light = bpy.context.active_object
    fill_light.name = "Fill_Light"
    fill_light.data.energy = 80
    fill_light.data.size = 2.0
    fill_light.rotation_euler = (math.radians(45), 0, math.radians(-45))


def setup_world():
    """Setup world background"""
    world = bpy.context.scene.world
    if world is None:
        world = bpy.data.worlds.new("World")
        bpy.context.scene.world = world

    world.use_nodes = True
    nodes = world.node_tree.nodes
    links = world.node_tree.links
    nodes.clear()

    # Warm ambient background
    bg = nodes.new('ShaderNodeBackground')
    bg.inputs['Color'].default_value = (0.15, 0.1, 0.08, 1.0)  # Dark warm
    bg.inputs['Strength'].default_value = 0.5

    output = nodes.new('ShaderNodeOutputWorld')
    links.new(bg.outputs['Background'], output.inputs['Surface'])


def setup_camera():
    """Create camera with animation for the scene"""
    bpy.ops.object.camera_add(location=(0, -4, 1.5))
    camera = bpy.context.active_object
    camera.name = "Scene_Camera"
    camera.data.lens = 35

    bpy.context.scene.camera = camera
    return camera


def animate_scene(camera, characters, duration_frames, fps):
    """Create animation keyframes for camera and characters"""
    scene = bpy.context.scene

    # Camera animation - starts wide, slowly moves in
    # Frame 1: Wide establishing shot
    scene.frame_set(1)
    camera.location = (0, -5, 2.0)
    camera.rotation_euler = (math.radians(75), 0, 0)
    camera.keyframe_insert(data_path="location", frame=1)
    camera.keyframe_insert(data_path="rotation_euler", frame=1)

    # Frame ~3s (72 frames): Move slightly closer
    frame_2 = int(3 * fps)
    scene.frame_set(frame_2)
    camera.location = (0.5, -4, 1.8)
    camera.rotation_euler = (math.radians(70), 0, math.radians(5))
    camera.keyframe_insert(data_path="location", frame=frame_2)
    camera.keyframe_insert(data_path="rotation_euler", frame=frame_2)

    # Frame ~8s: Pan to show kids
    frame_3 = int(8 * fps)
    scene.frame_set(frame_3)
    camera.location = (-0.5, -3.5, 1.5)
    camera.rotation_euler = (math.radians(72), 0, math.radians(-5))
    camera.keyframe_insert(data_path="location", frame=frame_3)
    camera.keyframe_insert(data_path="rotation_euler", frame=frame_3)

    # Frame ~15s: Back to wide
    frame_4 = int(15 * fps)
    scene.frame_set(frame_4)
    camera.location = (1.0, -4.5, 1.8)
    camera.rotation_euler = (math.radians(72), 0, math.radians(8))
    camera.keyframe_insert(data_path="location", frame=frame_4)
    camera.keyframe_insert(data_path="rotation_euler", frame=frame_4)

    # Frame ~25s: Closer to parents
    frame_5 = int(25 * fps)
    scene.frame_set(frame_5)
    camera.location = (1.5, -3.5, 1.6)
    camera.rotation_euler = (math.radians(70), 0, math.radians(15))
    camera.keyframe_insert(data_path="location", frame=frame_5)
    camera.keyframe_insert(data_path="rotation_euler", frame=frame_5)

    # Frame ~35s: Focus on kids asking "Promise?"
    frame_6 = int(35 * fps)
    scene.frame_set(frame_6)
    camera.location = (-0.3, -3.0, 1.3)
    camera.rotation_euler = (math.radians(68), 0, math.radians(-5))
    camera.keyframe_insert(data_path="location", frame=frame_6)
    camera.keyframe_insert(data_path="rotation_euler", frame=frame_6)

    # Final frame: End position
    scene.frame_set(duration_frames)
    camera.location = (0, -3.5, 1.5)
    camera.rotation_euler = (math.radians(70), 0, 0)
    camera.keyframe_insert(data_path="location", frame=duration_frames)
    camera.keyframe_insert(data_path="rotation_euler", frame=duration_frames)

    # Smooth camera interpolation
    if camera.animation_data and camera.animation_data.action:
        for fc in camera.animation_data.action.fcurves:
            for kf in fc.keyframe_points:
                kf.interpolation = 'BEZIER'
                kf.easing = 'AUTO'

    # Animate Gabe (parent) walking across room
    gabe = characters.get('Gabe')
    if gabe:
        # Start position (far side of room)
        scene.frame_set(1)
        gabe.location = (2.5, 2.5, 0)
        gabe.rotation_euler = (0, 0, math.radians(-120))
        gabe.keyframe_insert(data_path="location", frame=1)
        gabe.keyframe_insert(data_path="rotation_euler", frame=1)

        # Move toward door
        scene.frame_set(int(10 * fps))
        gabe.location = (1.5, 1.0, 0)
        gabe.rotation_euler = (0, 0, math.radians(-90))
        gabe.keyframe_insert(data_path="location", frame=int(10 * fps))
        gabe.keyframe_insert(data_path="rotation_euler", frame=int(10 * fps))

        # Back to kids
        scene.frame_set(int(25 * fps))
        gabe.location = (0.5, 0.5, 0)
        gabe.rotation_euler = (0, 0, math.radians(45))
        gabe.keyframe_insert(data_path="location", frame=int(25 * fps))
        gabe.keyframe_insert(data_path="rotation_euler", frame=int(25 * fps))

        # End
        scene.frame_set(duration_frames)
        gabe.location = (0.3, 0.3, 0)
        gabe.keyframe_insert(data_path="location", frame=duration_frames)

    # Animate Nina
    nina = characters.get('Nina')
    if nina:
        # Start near entrance
        scene.frame_set(1)
        nina.location = (1.5, 0.5, 0)
        nina.rotation_euler = (0, 0, math.radians(-45))
        nina.keyframe_insert(data_path="location", frame=1)
        nina.keyframe_insert(data_path="rotation_euler", frame=1)

        # Move to kids
        scene.frame_set(int(20 * fps))
        nina.location = (-0.5, 0.8, 0)
        nina.rotation_euler = (0, 0, math.radians(90))
        nina.keyframe_insert(data_path="location", frame=int(20 * fps))
        nina.keyframe_insert(data_path="rotation_euler", frame=int(20 * fps))

        # Final position
        scene.frame_set(duration_frames)
        nina.location = (-0.3, 0.6, 0)
        nina.keyframe_insert(data_path="location", frame=duration_frames)


def configure_render(args, fps=24, duration_seconds=45):
    """Configure render settings"""
    scene = bpy.context.scene
    render = scene.render

    # Ensure output directory
    output_dir = os.path.abspath(args['output'])
    os.makedirs(output_dir, exist_ok=True)

    render.filepath = os.path.join(output_dir, "frame_")
    render.image_settings.file_format = 'PNG'

    if args['preview']:
        render.resolution_x = 960
        render.resolution_y = 540
        scene.cycles.samples = 16
    else:
        render.resolution_x = 1920
        render.resolution_y = 1080
        scene.cycles.samples = 64

    render.resolution_percentage = 100

    # Frame range
    total_frames = fps * duration_seconds
    if args['frames']:
        total_frames = args['frames']

    scene.frame_start = 1
    scene.frame_end = total_frames
    scene.render.fps = fps

    # Cycles settings
    scene.render.engine = 'CYCLES'

    # Disable denoising (causes issues on some builds)
    scene.cycles.use_denoising = False

    # Try GPU
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
    args = parse_args()

    print("=" * 60)
    print("SCENE 01: INT. HOME - EVENING")
    print("Fairy Dinosaur Date Night")
    print("=" * 60)

    print("\n[1/7] Clearing scene...")
    clear_scene()

    print("[2/7] Creating living room...")
    create_living_room()
    create_couch()
    create_tv()
    create_window()
    create_lamp()
    create_dino_toys()

    print("[3/7] Creating characters...")
    characters = {}

    # Mia (8 years old, sitting on couch) - blue outfit
    mia = create_character_standin(
        "Mia",
        color=(0.2, 0.4, 0.8, 1.0),
        location=(-0.5, 1.5, 0.45),
        height=1.2,
        pose='sitting'
    )
    characters['Mia'] = mia

    # Leo (5 years old, sitting on couch) - green dino pajamas
    leo = create_character_standin(
        "Leo",
        color=(0.2, 0.7, 0.3, 1.0),
        location=(0.5, 1.5, 0.45),
        height=1.0,
        pose='sitting'
    )
    characters['Leo'] = leo

    # Gabe (dad, standing, in formal attire) - dark suit
    gabe = create_character_standin(
        "Gabe",
        color=(0.15, 0.15, 0.2, 1.0),
        location=(2.0, 2.0, 0),
        height=1.85,
        pose='standing'
    )
    characters['Gabe'] = gabe

    # Nina (mom, standing, in formal dress) - elegant red/maroon
    nina = create_character_standin(
        "Nina",
        color=(0.6, 0.15, 0.15, 1.0),
        location=(1.5, 0.5, 0),
        height=1.7,
        pose='standing'
    )
    characters['Nina'] = nina

    # Jenny (babysitter, sitting) - casual pink
    jenny = create_character_standin(
        "Jenny",
        color=(0.9, 0.6, 0.7, 1.0),
        location=(-2.0, 1.0, 0.2),
        height=1.6,
        pose='sitting'
    )
    characters['Jenny'] = jenny

    print("[4/7] Setting up lighting...")
    setup_lighting()
    setup_world()

    print("[5/7] Setting up camera...")
    camera = setup_camera()

    fps = 24
    duration = 45  # 45 seconds

    print("[6/7] Creating animations...")
    animate_scene(camera, characters, fps * duration, fps)

    print("[7/7] Configuring render...")
    total_frames = configure_render(args, fps, duration)

    output_dir = os.path.abspath(args['output'])

    print(f"\n{'=' * 60}")
    print("RENDERING SCENE")
    print(f"{'=' * 60}")
    print(f"Output: {output_dir}")
    print(f"Frames: {total_frames}")
    print(f"Resolution: {bpy.context.scene.render.resolution_x}x{bpy.context.scene.render.resolution_y}")
    print(f"Samples: {bpy.context.scene.cycles.samples}")
    print(f"Duration: {duration}s @ {fps}fps")

    # Render animation
    bpy.ops.render.render(animation=True)

    print(f"\n{'=' * 60}")
    print("RENDER COMPLETE!")
    print(f"{'=' * 60}")
    print(f"\nFrames saved to: {output_dir}")

    # FFmpeg command for combining frames
    print("\nTo create video with audio, run:")
    print(f"  ffmpeg -framerate {fps} -i {output_dir}/frame_%04d.png \\")
    print(f"    -i assets/audio/music/main_theme.wav \\")
    print(f"    -c:v libx264 -pix_fmt yuv420p -c:a aac \\")
    print(f"    -shortest {output_dir}/scene01_home_evening.mp4")


if __name__ == "__main__":
    main()
