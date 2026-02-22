#!/usr/bin/env python3
"""
Render Mia Walking Animation - Cleaned Rig Verification
=========================================================
Renders a 120-frame (5s @ 24fps) walking animation using the cleaned rig
(mia_cleaned.glb) to verify that all fixes work in motion:
- No arm-leg clipping during back-swing
- Spine counter-rotation working
- Ponytail secondary motion
- Rotation limits preventing impossible poses

Usage:
    blender --background --python scripts/render_mia_walking_cleaned.py
"""

import bpy
import sys
import os
import math
from mathutils import Vector

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)

CLEANED_MODEL = os.path.join(PROJECT_DIR, "output", "mia_cleanup", "mia_cleaned.glb")
WALKING_ANIM = os.path.join(PROJECT_DIR, "output", "mia_cleanup", "mia_walking_anim.glb")
OUTPUT_DIR = os.path.join(PROJECT_DIR, "output", "mia_cleanup", "walking_test")
FRAME_PREFIX = os.path.join(OUTPUT_DIR, "frame_")
VIDEO_OUTPUT = os.path.join(OUTPUT_DIR, "mia_walking_cleaned.mp4")

FPS = 24
DURATION = 5  # seconds
TOTAL_FRAMES = FPS * DURATION  # 120
RESOLUTION = (1280, 720)
SAMPLES = 8


def clear_scene():
    """Remove all objects from the scene."""
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


def import_cleaned_model():
    """Import Mia's cleaned rigged model."""
    print(f"  Importing cleaned model: {CLEANED_MODEL}")

    if not os.path.exists(CLEANED_MODEL):
        print(f"  ERROR: File not found: {CLEANED_MODEL}")
        return None, None

    bpy.ops.import_scene.gltf(filepath=CLEANED_MODEL)

    armature = None
    mesh = None
    for obj in bpy.data.objects:
        if obj.type == 'ARMATURE':
            armature = obj
        elif obj.type == 'MESH' and obj.vertex_groups:
            mesh = obj

    if armature:
        bone_count = len(armature.data.bones)
        print(f"  Armature: {armature.name} ({bone_count} bones)")

        # Check for ponytail bones
        ponytail_count = sum(1 for b in armature.data.bones if 'Ponytail' in b.name)
        print(f"  Ponytail bones: {ponytail_count}")

    if mesh:
        print(f"  Mesh: {mesh.name} ({len(mesh.data.vertices)} verts, {len(mesh.data.polygons)} faces)")

        # Decimate for faster rendering (640K verts is very high)
        face_count = len(mesh.data.polygons)
        if face_count > 200000:
            bpy.context.view_layer.objects.active = mesh
            orig_faces = face_count

            # Remember armature modifier
            arm_mod = mesh.modifiers.get("Armature")
            arm_target = arm_mod.object if arm_mod else None
            if arm_mod:
                bpy.ops.object.modifier_remove(modifier="Armature")

            # Decimate to 30% for render speed
            decimate = mesh.modifiers.new(name="Decimate", type='DECIMATE')
            decimate.ratio = 0.3
            bpy.ops.object.modifier_apply(modifier="Decimate")
            new_faces = len(mesh.data.polygons)
            print(f"  Decimated: {orig_faces} -> {new_faces} faces ({new_faces/orig_faces*100:.0f}%)")

            # Re-add armature modifier
            if arm_target:
                arm_mod = mesh.modifiers.new(name="Armature", type='ARMATURE')
                arm_mod.object = arm_target
                print(f"  Re-added armature modifier: {arm_target.name}")

    return armature, mesh


def reapply_constraints(armature):
    """Re-apply bone constraints since GLB export strips them.

    The cleaned model has all constraints set up, but GLB format doesn't
    preserve Blender bone constraints. We need to re-add them.
    """
    print("\n  Re-applying constraints (lost during GLB export)...")

    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='POSE')

    constraints_added = 0

    # Rotation limits for all joints (from cleanup_mia_rig.py)
    joint_limits = {
        "LeftForeArm": {"x": (-5, 150), "y": (-90, 90), "z": (-10, 10)},
        "RightForeArm": {"x": (-5, 150), "y": (-90, 90), "z": (-10, 10)},
        "LeftLeg": {"x": (-5, 150), "y": (-10, 10), "z": (-10, 10)},
        "RightLeg": {"x": (-5, 150), "y": (-10, 10), "z": (-10, 10)},
        "Head": {"x": (-45, 45), "y": (-80, 80), "z": (-45, 45)},
        "neck": {"x": (-30, 30), "y": (-60, 60), "z": (-30, 30)},
        "LeftArm": {"x": (-120, 120), "y": (-90, 90), "z": (-170, 40)},
        "RightArm": {"x": (-120, 120), "y": (-90, 90), "z": (-40, 170)},
        "LeftShoulder": {"x": (-15, 15), "y": (-15, 15), "z": (-30, 30)},
        "RightShoulder": {"x": (-15, 15), "y": (-15, 15), "z": (-30, 30)},
        "Spine": {"x": (-30, 30), "y": (-45, 45), "z": (-20, 20)},
        "Spine01": {"x": (-20, 20), "y": (-30, 30), "z": (-15, 15)},
        "Spine02": {"x": (-20, 20), "y": (-30, 30), "z": (-15, 15)},
        "LeftHand": {"x": (-75, 75), "y": (-30, 30), "z": (-90, 90)},
        "RightHand": {"x": (-75, 75), "y": (-30, 30), "z": (-90, 90)},
        "LeftFoot": {"x": (-40, 50), "y": (-30, 30), "z": (-25, 25)},
        "RightFoot": {"x": (-40, 50), "y": (-30, 30), "z": (-25, 25)},
        "LeftUpLeg": {"x": (-120, 30), "y": (-45, 45), "z": (-60, 30)},
        "RightUpLeg": {"x": (-120, 30), "y": (-45, 45), "z": (-30, 60)},
        "LeftToeBase": {"x": (-30, 60), "y": (-10, 10), "z": (-10, 10)},
        "RightToeBase": {"x": (-30, 60), "y": (-10, 10), "z": (-10, 10)},
    }

    for bone_name, limits in joint_limits.items():
        pbone = armature.pose.bones.get(bone_name)
        if not pbone:
            continue

        limit = pbone.constraints.new('LIMIT_ROTATION')
        limit.name = f"Limit_{bone_name}"
        limit.owner_space = 'LOCAL'
        limit.use_limit_x = True
        limit.min_x = math.radians(limits["x"][0])
        limit.max_x = math.radians(limits["x"][1])
        limit.use_limit_y = True
        limit.min_y = math.radians(limits["y"][0])
        limit.max_y = math.radians(limits["y"][1])
        limit.use_limit_z = True
        limit.min_z = math.radians(limits["z"][0])
        limit.max_z = math.radians(limits["z"][1])
        constraints_added += 1

    # Spine counter-rotation
    spine_bone = armature.pose.bones.get("Spine")
    if spine_bone:
        cr = spine_bone.constraints.new('COPY_ROTATION')
        cr.name = "CounterRotation_Hips"
        cr.target = armature
        cr.subtarget = "Hips"
        cr.use_x = False
        cr.use_y = True
        cr.use_z = True
        cr.invert_y = True
        cr.invert_z = True
        cr.target_space = 'LOCAL'
        cr.owner_space = 'LOCAL'
        cr.influence = 0.3
        cr.mix_mode = 'ADD'
        constraints_added += 1

    spine01_bone = armature.pose.bones.get("Spine01")
    if spine01_bone:
        cr = spine01_bone.constraints.new('COPY_ROTATION')
        cr.name = "CounterRotation_Hips01"
        cr.target = armature
        cr.subtarget = "Hips"
        cr.use_x = False
        cr.use_y = True
        cr.use_z = True
        cr.invert_y = True
        cr.invert_z = True
        cr.target_space = 'LOCAL'
        cr.owner_space = 'LOCAL'
        cr.influence = 0.15
        cr.mix_mode = 'ADD'
        constraints_added += 1

    # Ponytail constraints
    for i in range(5):
        bone_name = f"Ponytail_{i+1:02d}"
        pbone = armature.pose.bones.get(bone_name)
        if not pbone:
            continue

        # Copy rotation from Head with decreasing influence
        cr = pbone.constraints.new('COPY_ROTATION')
        cr.name = "Ponytail_Follow"
        cr.target = armature
        cr.subtarget = "Head"
        cr.target_space = 'LOCAL'
        cr.owner_space = 'LOCAL'
        cr.mix_mode = 'ADD'
        cr.influence = max(0.05, 0.4 - (i * 0.08))

        # Limit rotation
        lr = pbone.constraints.new('LIMIT_ROTATION')
        lr.name = "Ponytail_Limit"
        lr.owner_space = 'LOCAL'
        lr.use_limit_x = True
        lr.min_x = math.radians(-60)
        lr.max_x = math.radians(60)
        lr.use_limit_y = True
        lr.min_y = math.radians(-45)
        lr.max_y = math.radians(45)
        lr.use_limit_z = True
        lr.min_z = math.radians(-60)
        lr.max_z = math.radians(60)

        constraints_added += 2

    bpy.ops.object.mode_set(mode='OBJECT')
    print(f"  Applied {constraints_added} constraints")
    return constraints_added


def import_walking_animation():
    """Import walking animation GLB and extract the action."""
    print(f"  Importing walking animation: {WALKING_ANIM}")

    if not os.path.exists(WALKING_ANIM):
        print(f"  ERROR: File not found: {WALKING_ANIM}")
        return None

    existing = set(obj.name for obj in bpy.data.objects)

    bpy.ops.import_scene.gltf(filepath=WALKING_ANIM)

    # Find the walking action
    walking_action = None
    for action in bpy.data.actions:
        if 'walking' in action.name.lower() or 'walk' in action.name.lower():
            walking_action = action
            break

    # Fallback: use the most recently added action
    if not walking_action:
        for action in bpy.data.actions:
            if action.name.startswith("Armature"):
                walking_action = action
                break

    if walking_action:
        print(f"  Walking action: {walking_action.name}")
        print(f"  Frame range: {walking_action.frame_range}")
    else:
        print("  WARNING: No walking action found!")
        print(f"  Available actions: {[a.name for a in bpy.data.actions]}")

    # Clean up imported objects (only need the action)
    for obj in list(bpy.data.objects):
        if obj.name not in existing:
            bpy.data.objects.remove(obj, do_unlink=True)

    return walking_action


def apply_walking_animation(armature, walking_action):
    """Apply walking animation via NLA strips for looping."""
    if not armature or not walking_action:
        print("  ERROR: Missing armature or action!")
        return

    if not armature.animation_data:
        armature.animation_data_create()

    # Clear existing animation data
    armature.animation_data.action = None
    for track in list(armature.animation_data.nla_tracks):
        armature.animation_data.nla_tracks.remove(track)

    # Create NLA track with looping
    track = armature.animation_data.nla_tracks.new()
    track.name = "WalkCycle"

    frame_start = walking_action.frame_range[0]
    frame_end = walking_action.frame_range[1]
    cycle_length = frame_end - frame_start

    num_repeats = math.ceil(TOTAL_FRAMES / cycle_length) + 1

    strip = track.strips.new(walking_action.name, int(1), walking_action)
    strip.action_frame_start = frame_start
    strip.action_frame_end = frame_end
    strip.repeat = num_repeats
    strip.use_animated_time = False
    strip.blend_type = 'REPLACE'

    print(f"  Walk cycle: {cycle_length:.1f} frames, {num_repeats} repeats")
    print(f"  Total coverage: {cycle_length * num_repeats:.0f} frames")


def setup_scene():
    """Set up ground, lighting, world background."""
    # Ground plane
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

    # Key light (sun)
    bpy.ops.object.light_add(type='SUN', location=(5, -5, 10))
    key = bpy.context.active_object
    key.name = "Key_Light"
    key.data.energy = 3.0
    key.data.color = (1.0, 0.97, 0.95)
    key.rotation_euler = (math.radians(50), math.radians(10), math.radians(30))

    # Fill light (area)
    bpy.ops.object.light_add(type='AREA', location=(-4, -6, 4))
    fill = bpy.context.active_object
    fill.name = "Fill_Light"
    fill.data.energy = 100.0
    fill.data.size = 5.0
    fill.rotation_euler = (math.radians(60), 0, math.radians(-30))

    # Rim light (area)
    bpy.ops.object.light_add(type='AREA', location=(0, 5, 5))
    rim = bpy.context.active_object
    rim.name = "Rim_Light"
    rim.data.energy = 80.0
    rim.data.size = 3.0
    rim.rotation_euler = (math.radians(-50), 0, 0)

    # World background
    world = bpy.context.scene.world
    if not world:
        world = bpy.data.worlds.new("World")
        bpy.context.scene.world = world
    world.use_nodes = True
    nodes = world.node_tree.nodes
    nodes.clear()
    bg = nodes.new('ShaderNodeBackground')
    bg.inputs["Color"].default_value = (0.85, 0.85, 0.87, 1.0)
    bg.inputs["Strength"].default_value = 0.5
    output = nodes.new('ShaderNodeOutputWorld')
    world.node_tree.links.new(bg.outputs["Background"], output.inputs["Surface"])


def setup_camera(armature):
    """Set up 3/4 view camera showing full body."""
    char_center = armature.location.copy()

    cam_distance = 5.0
    cam_angle = math.radians(30)
    cam_height = 1.2

    cam_x = char_center.x + cam_distance * math.sin(cam_angle)
    cam_y = char_center.y - cam_distance * math.cos(cam_angle)
    cam_z = char_center.z + cam_height

    bpy.ops.object.camera_add(location=(cam_x, cam_y, cam_z))
    camera = bpy.context.active_object
    camera.name = "MainCamera"
    camera.data.lens = 50

    # Camera target at character center
    bpy.ops.object.empty_add(type='PLAIN_AXES',
                             location=(char_center.x, char_center.y, char_center.z + 0.8))
    target = bpy.context.active_object
    target.name = "Camera_Target"

    constraint = camera.constraints.new(type='TRACK_TO')
    constraint.target = target
    constraint.track_axis = 'TRACK_NEGATIVE_Z'
    constraint.up_axis = 'UP_Y'

    bpy.context.scene.camera = camera
    return camera


def configure_render():
    """Configure EEVEE render settings."""
    scene = bpy.context.scene
    render = scene.render

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    render.filepath = FRAME_PREFIX
    render.image_settings.file_format = 'PNG'
    render.resolution_x = RESOLUTION[0]
    render.resolution_y = RESOLUTION[1]
    render.resolution_percentage = 100

    scene.frame_start = 1
    scene.frame_end = TOTAL_FRAMES
    scene.render.fps = FPS

    scene.render.engine = 'BLENDER_EEVEE'
    scene.eevee.taa_render_samples = SAMPLES
    scene.eevee.use_gtao = True
    scene.eevee.gtao_distance = 1.0
    scene.eevee.use_bloom = False
    scene.eevee.use_ssr = False

    print(f"  Engine: EEVEE, Samples: {SAMPLES}")
    print(f"  Resolution: {RESOLUTION[0]}x{RESOLUTION[1]}")
    print(f"  Frames: {TOTAL_FRAMES} ({DURATION}s @ {FPS}fps)")


def main():
    print("=" * 60)
    print("  Mia Walking Animation - Cleaned Rig Test")
    print("=" * 60)

    # Step 1: Clear scene
    print("\n[1/7] Clearing scene...")
    clear_scene()

    # Step 2: Import cleaned model
    print("\n[2/7] Importing cleaned model...")
    armature, mesh = import_cleaned_model()
    if not armature:
        print("ERROR: Could not import model!")
        sys.exit(1)

    # Step 3: Re-apply constraints (lost in GLB export)
    print("\n[3/7] Re-applying constraints...")
    reapply_constraints(armature)

    # Step 4: Import and apply walking animation
    print("\n[4/7] Importing walking animation...")
    walking_action = import_walking_animation()
    if not walking_action:
        print("ERROR: Could not find walking action!")
        sys.exit(1)

    print("\n[5/7] Applying walking animation...")
    apply_walking_animation(armature, walking_action)

    # Step 5: Set up scene
    print("\n[6/7] Setting up scene...")
    setup_scene()
    setup_camera(armature)
    configure_render()

    # Step 6: Render
    print(f"\n[7/7] Rendering {TOTAL_FRAMES} frames...")
    print(f"  Output: {FRAME_PREFIX}*.png")
    bpy.ops.render.render(animation=True)

    # Count rendered frames
    frame_count = len([f for f in os.listdir(OUTPUT_DIR) if f.endswith('.png')])
    print(f"\n  Rendered {frame_count} frames")

    # Print ffmpeg command
    print(f"\nTo create video:")
    print(f'  ffmpeg -framerate {FPS} -i "{FRAME_PREFIX}%04d.png" -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p -movflags +faststart "{VIDEO_OUTPUT}"')

    print("\n" + "=" * 60)
    print("  RENDER COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
