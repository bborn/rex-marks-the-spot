#!/usr/bin/env python3
"""
Render Mia Walking Animation Test

Imports Mia's rigged model and walking animation, sets up a simple scene,
and renders a 5-10 second animation test to verify the rig works.

Usage:
    blender -b -P scripts/render_mia_walking_test.py
    blender -b -P scripts/render_mia_walking_test.py -- --preview
    blender -b -P scripts/render_mia_walking_test.py -- --duration 5
"""

import bpy
import sys
import os
import math
from mathutils import Vector


def parse_args():
    """Parse command line arguments after '--'"""
    args = {
        'output': 'renders/mia_walking_test/frame_',
        'video_output': 'renders/mia_walking_test.mp4',
        'samples': 8,
        'preview': False,
        'resolution': (1280, 720),
        'fps': 24,
        'duration': 5,  # seconds
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
                args['resolution'] = (640, 360)
                args['samples'] = 4
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
    for block in bpy.data.meshes:
        if block.users == 0:
            bpy.data.meshes.remove(block)
    for block in bpy.data.materials:
        if block.users == 0:
            bpy.data.materials.remove(block)
    for block in bpy.data.armatures:
        if block.users == 0:
            bpy.data.armatures.remove(block)
    for block in bpy.data.actions:
        if block.users == 0:
            bpy.data.actions.remove(block)


def import_mia_rigged():
    """Import Mia's rigged model GLB"""
    rigged_path = os.path.abspath("assets/models/characters/mia/mia_rigged.glb")
    print(f"  Importing rigged model: {rigged_path}")
    bpy.ops.import_scene.gltf(filepath=rigged_path)

    # Find the armature and mesh
    armature = None
    mesh = None
    to_delete = []

    for obj in bpy.data.objects:
        if obj.type == 'ARMATURE':
            armature = obj
        elif obj.type == 'MESH' and obj.name.startswith('char'):
            mesh = obj
        elif obj.type == 'MESH' and 'Icosphere' in obj.name:
            to_delete.append(obj)

    # Remove extra icosphere
    for obj in to_delete:
        bpy.data.objects.remove(obj, do_unlink=True)

    print(f"  Found armature: {armature.name if armature else 'None'}")
    print(f"  Found mesh: {mesh.name if mesh else 'None'}")
    if armature:
        print(f"  Bones: {len(armature.data.bones)}")
    if mesh:
        print(f"  Vertices: {len(mesh.data.vertices)}, Faces: {len(mesh.data.polygons)}")
        # Apply decimation to reduce poly count for faster rendering
        if len(mesh.data.polygons) > 200000:
            orig_faces = len(mesh.data.polygons)
            bpy.context.view_layer.objects.active = mesh
            # Temporarily remove armature modifier, apply decimate, re-add armature
            arm_mod = mesh.modifiers.get("Armature")
            arm_target = arm_mod.object if arm_mod else None
            if arm_mod:
                bpy.ops.object.modifier_remove(modifier="Armature")
            # Add and apply decimate
            decimate = mesh.modifiers.new(name="Decimate", type='DECIMATE')
            decimate.ratio = 0.3
            bpy.ops.object.modifier_apply(modifier="Decimate")
            new_faces = len(mesh.data.polygons)
            print(f"  Applied decimate: {orig_faces} -> {new_faces} faces ({new_faces/orig_faces*100:.0f}%)")
            # Re-add armature modifier
            if arm_target:
                arm_mod = mesh.modifiers.new(name="Armature", type='ARMATURE')
                arm_mod.object = arm_target
                print(f"  Re-added armature modifier targeting: {arm_target.name}")

    return armature, mesh


def import_walking_animation():
    """Import walking animation GLB and extract the action"""
    walking_path = os.path.abspath("assets/models/characters/mia/animations/mia_walking.glb")
    print(f"  Importing walking animation: {walking_path}")

    # Remember existing objects
    existing = set(obj.name for obj in bpy.data.objects)

    bpy.ops.import_scene.gltf(filepath=walking_path)

    # Find the walking action
    walking_action = None
    for action in bpy.data.actions:
        if 'walking' in action.name.lower():
            walking_action = action
            break

    print(f"  Walking action: {walking_action.name if walking_action else 'None'}")
    if walking_action:
        print(f"  Frame range: {walking_action.frame_range}")

    # Delete the imported objects (we only need the action)
    for obj in list(bpy.data.objects):
        if obj.name not in existing:
            bpy.data.objects.remove(obj, do_unlink=True)

    return walking_action


def apply_walking_animation(armature, walking_action, total_frames):
    """Apply walking animation to the armature with looping via NLA"""
    if not armature or not walking_action:
        print("  ERROR: Missing armature or action!")
        return

    # Ensure the armature has animation data
    if not armature.animation_data:
        armature.animation_data_create()

    # Clear existing action
    armature.animation_data.action = None

    # Use NLA strips for looping
    nla_tracks = armature.animation_data.nla_tracks

    # Clear existing NLA tracks
    for track in list(nla_tracks):
        nla_tracks.remove(track)

    # Create a new NLA track
    track = nla_tracks.new()
    track.name = "WalkCycle"

    # Get the action frame range
    frame_start = walking_action.frame_range[0]
    frame_end = walking_action.frame_range[1]
    cycle_length = frame_end - frame_start

    # Calculate how many repetitions we need
    num_repeats = math.ceil(total_frames / cycle_length) + 1

    # Add the strip
    strip = track.strips.new(walking_action.name, int(1), walking_action)
    strip.action_frame_start = frame_start
    strip.action_frame_end = frame_end
    strip.repeat = num_repeats
    strip.use_animated_time = False
    strip.blend_type = 'REPLACE'

    print(f"  Applied walking animation via NLA")
    print(f"  Cycle length: {cycle_length:.1f} frames")
    print(f"  Repeats: {num_repeats}")
    print(f"  Total coverage: {cycle_length * num_repeats:.0f} frames")


def setup_ground():
    """Create a simple ground plane"""
    bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, 0))
    ground = bpy.context.active_object
    ground.name = "Ground"

    mat = bpy.data.materials.new(name="GroundMat")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.75, 0.75, 0.75, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.9
    ground.data.materials.append(mat)

    return ground


def setup_lighting():
    """Set up 3-point lighting"""
    # Key light (sun) - main illumination from front-right
    bpy.ops.object.light_add(type='SUN', location=(5, -5, 10))
    key = bpy.context.active_object
    key.name = "Key_Light"
    key.data.energy = 3.0
    key.data.color = (1.0, 0.97, 0.95)
    key.rotation_euler = (math.radians(50), math.radians(10), math.radians(30))

    # Fill light (area) - softer from front-left
    bpy.ops.object.light_add(type='AREA', location=(-4, -6, 4))
    fill = bpy.context.active_object
    fill.name = "Fill_Light"
    fill.data.energy = 100.0
    fill.data.size = 5.0
    fill.rotation_euler = (math.radians(60), 0, math.radians(-30))

    # Rim/back light - behind and above
    bpy.ops.object.light_add(type='AREA', location=(0, 5, 5))
    rim = bpy.context.active_object
    rim.name = "Rim_Light"
    rim.data.energy = 80.0
    rim.data.size = 3.0
    rim.rotation_euler = (math.radians(-50), 0, 0)

    return key, fill, rim


def setup_world():
    """Set up light gray background"""
    world = bpy.context.scene.world
    if world is None:
        world = bpy.data.worlds.new("World")
        bpy.context.scene.world = world

    world.use_nodes = True
    nodes = world.node_tree.nodes
    nodes.clear()

    background = nodes.new('ShaderNodeBackground')
    background.inputs["Color"].default_value = (0.85, 0.85, 0.87, 1.0)
    background.inputs["Strength"].default_value = 0.5

    output = nodes.new('ShaderNodeOutputWorld')
    world.node_tree.links.new(background.outputs["Background"], output.inputs["Surface"])


def setup_camera(armature):
    """Set up camera at 3/4 front view showing full body"""
    # Calculate character approximate position and height
    # The armature origin is typically at the feet
    char_center = armature.location.copy()

    # Camera positioned at front 3/4 view
    cam_distance = 5.0
    cam_angle = math.radians(30)  # 30 degrees off center
    cam_height = 1.2  # Slightly above character center

    cam_x = char_center.x + cam_distance * math.sin(cam_angle)
    cam_y = char_center.y - cam_distance * math.cos(cam_angle)
    cam_z = char_center.z + cam_height

    bpy.ops.object.camera_add(location=(cam_x, cam_y, cam_z))
    camera = bpy.context.active_object
    camera.name = "MainCamera"
    camera.data.lens = 50  # Portrait-ish lens

    # Add Track To constraint to follow character
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(char_center.x, char_center.y, char_center.z + 0.8))
    target = bpy.context.active_object
    target.name = "Camera_Target"

    constraint = camera.constraints.new(type='TRACK_TO')
    constraint.target = target
    constraint.track_axis = 'TRACK_NEGATIVE_Z'
    constraint.up_axis = 'UP_Y'

    bpy.context.scene.camera = camera

    return camera, target


def configure_render(args):
    """Configure render settings optimized for animation test"""
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

    # Use EEVEE for speed (this is just a rig test)
    scene.render.engine = 'BLENDER_EEVEE'
    scene.eevee.taa_render_samples = args['samples']

    # EEVEE settings for decent quality
    scene.eevee.use_gtao = True  # Ambient occlusion
    scene.eevee.gtao_distance = 1.0
    scene.eevee.use_bloom = False
    scene.eevee.use_ssr = False  # No screen space reflections needed

    print(f"  Engine: EEVEE (fast for rig test)")
    print(f"  Resolution: {args['resolution'][0]}x{args['resolution'][1]}")
    print(f"  Samples: {args['samples']}")
    print(f"  Frames: {total_frames} ({args['duration']}s @ {args['fps']}fps)")

    return total_frames


def main():
    args = parse_args()

    print("=" * 60)
    print("Mia Walking Animation Test - Rig Verification")
    print("=" * 60)

    # Step 1: Clear scene
    print("\n[1/7] Clearing scene...")
    clear_scene()

    # Step 2: Import rigged model
    print("\n[2/7] Importing Mia's rigged model...")
    armature, mesh = import_mia_rigged()
    if not armature:
        print("ERROR: Could not find armature in rigged model!")
        return

    # Step 3: Import and apply walking animation
    print("\n[3/7] Importing walking animation...")
    walking_action = import_walking_animation()
    if not walking_action:
        print("ERROR: Could not find walking action!")
        return

    total_frames = args['fps'] * args['duration']
    print("\n[4/7] Applying walking animation...")
    apply_walking_animation(armature, walking_action, total_frames)

    # Step 5: Set up scene
    print("\n[5/7] Setting up scene...")
    setup_ground()
    setup_lighting()
    setup_world()
    camera, cam_target = setup_camera(armature)

    # Step 6: Configure render
    print("\n[6/7] Configuring render...")
    total_frames = configure_render(args)

    # Step 7: Render
    print(f"\n[7/7] Rendering {total_frames} frames...")
    print(f"Output: {os.path.abspath(args['output'])}")
    print("This will take a while. Progress:")

    bpy.ops.render.render(animation=True)

    print("\n" + "=" * 60)
    print("RENDER COMPLETE!")
    print("=" * 60)

    output_dir = os.path.dirname(os.path.abspath(args['output']))
    frame_count = len([f for f in os.listdir(output_dir) if f.endswith('.png')])
    print(f"Frames saved: {frame_count} in {output_dir}")

    # Convert to video
    video_output = os.path.abspath(args['video_output'])
    frame_pattern = os.path.abspath(args['output']) + '%04d.png'
    print(f"\nTo create video:\n  ffmpeg -framerate {args['fps']} -i \"{frame_pattern}\" -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p -movflags +faststart \"{video_output}\"")


if __name__ == "__main__":
    main()
