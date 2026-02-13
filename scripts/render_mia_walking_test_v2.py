#!/usr/bin/env python3
"""
Render Mia Walking Animation Test V2 - Fixed Rig Verification

Uses mia_rigged_v2.glb (from task #257) which includes:
- 28 bones (24 original + 4 ponytail)
- Weight-painted ponytail vertices

Re-applies bone constraints at render time since GLB doesn't preserve them:
- Arm rotation limits to prevent leg clipping
- Spine counter-rotation for natural hip-shoulder movement
- Ponytail secondary motion constraints

Usage:
    DISPLAY=:100 blender -b -P scripts/render_mia_walking_test_v2.py
    DISPLAY=:100 blender -b -P scripts/render_mia_walking_test_v2.py -- --preview
"""

import bpy
import sys
import os
import math
from mathutils import Vector


# ============================================================
# RIG FIX CONFIGURATION (from task #257 fix_mia_rig.py)
# ============================================================

ARM_LIMITS = {
    "LeftArm": {
        "use_limit_x": True, "min_x": math.radians(-50), "max_x": math.radians(90),
        "use_limit_y": True, "min_y": math.radians(-45), "max_y": math.radians(45),
        "use_limit_z": True, "min_z": math.radians(-30), "max_z": math.radians(90),
    },
    "RightArm": {
        "use_limit_x": True, "min_x": math.radians(-50), "max_x": math.radians(90),
        "use_limit_y": True, "min_y": math.radians(-45), "max_y": math.radians(45),
        "use_limit_z": True, "min_z": math.radians(-90), "max_z": math.radians(30),
    },
    "LeftForeArm": {
        "use_limit_x": True, "min_x": math.radians(-5), "max_x": math.radians(150),
        "use_limit_y": True, "min_y": math.radians(-90), "max_y": math.radians(90),
        "use_limit_z": True, "min_z": math.radians(-10), "max_z": math.radians(10),
    },
    "RightForeArm": {
        "use_limit_x": True, "min_x": math.radians(-5), "max_x": math.radians(150),
        "use_limit_y": True, "min_y": math.radians(-90), "max_y": math.radians(90),
        "use_limit_z": True, "min_z": math.radians(-10), "max_z": math.radians(10),
    },
}

SPINE_COUNTER_ROTATION_INFLUENCE = 0.35


def parse_args():
    """Parse command line arguments after '--'"""
    args = {
        'output': 'renders/mia_walking_test_v2/frame_',
        'video_output': 'renders/mia_walking_test_v2.mp4',
        'samples': 8,
        'preview': False,
        'resolution': (1920, 1080),
        'fps': 24,
        'duration': 5,
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


def import_mia_rigged_v2():
    """Import Mia's fixed rigged model (v2) GLB"""
    rigged_path = os.path.abspath("assets/models/characters/mia/mia_rigged_v2.glb")
    print(f"  Importing fixed rig v2: {rigged_path}")

    if not os.path.exists(rigged_path):
        print(f"  ERROR: File not found: {rigged_path}")
        return None, None

    bpy.ops.import_scene.gltf(filepath=rigged_path)

    armature = None
    mesh = None

    for obj in bpy.data.objects:
        if obj.type == 'ARMATURE':
            armature = obj
        elif obj.type == 'MESH' and obj.name.startswith('char'):
            mesh = obj

    print(f"  Found armature: {armature.name if armature else 'None'}")
    print(f"  Found mesh: {mesh.name if mesh else 'None'}")

    if armature:
        bone_count = len(armature.data.bones)
        print(f"  Bones: {bone_count}")
        if bone_count >= 28:
            print(f"  V2 rig confirmed (ponytail bones present)")
        else:
            print(f"  WARNING: Expected 28+ bones for v2, got {bone_count}")

    if mesh:
        vert_count = len(mesh.data.vertices)
        face_count = len(mesh.data.polygons)
        print(f"  Vertices: {vert_count}, Faces: {face_count}")

        # Decimate for faster rendering
        if face_count > 200000:
            orig_faces = face_count
            bpy.context.view_layer.objects.active = mesh

            arm_mod = mesh.modifiers.get("Armature")
            arm_target = arm_mod.object if arm_mod else None
            if arm_mod:
                bpy.ops.object.modifier_remove(modifier="Armature")

            decimate = mesh.modifiers.new(name="Decimate", type='DECIMATE')
            decimate.ratio = 0.3
            bpy.ops.object.modifier_apply(modifier="Decimate")
            new_faces = len(mesh.data.polygons)
            print(f"  Applied decimate: {orig_faces} -> {new_faces} faces ({new_faces/orig_faces*100:.0f}%)")

            if arm_target:
                arm_mod = mesh.modifiers.new(name="Armature", type='ARMATURE')
                arm_mod.object = arm_target
                print(f"  Re-added armature modifier targeting: {arm_target.name}")

    return armature, mesh


def apply_rig_constraints(armature):
    """Re-apply bone constraints that were lost during GLB export"""
    print("\n  Re-applying rig constraints (lost during GLB export)...")

    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='POSE')

    constraints_added = 0

    # --- Arm rotation limits ---
    for bone_name, limits in ARM_LIMITS.items():
        pbone = armature.pose.bones.get(bone_name)
        if not pbone:
            print(f"    WARNING: Bone '{bone_name}' not found")
            continue

        constraint = pbone.constraints.new('LIMIT_ROTATION')
        constraint.name = f"Limit_{bone_name}"
        constraint.owner_space = 'LOCAL'
        constraint.use_limit_x = limits.get("use_limit_x", False)
        constraint.min_x = limits.get("min_x", 0)
        constraint.max_x = limits.get("max_x", 0)
        constraint.use_limit_y = limits.get("use_limit_y", False)
        constraint.min_y = limits.get("min_y", 0)
        constraint.max_y = limits.get("max_y", 0)
        constraint.use_limit_z = limits.get("use_limit_z", False)
        constraint.min_z = limits.get("min_z", 0)
        constraint.max_z = limits.get("max_z", 0)
        constraints_added += 1
        print(f"    Added LIMIT_ROTATION on {bone_name}")

    # Shoulder limits
    for side in ["Left", "Right"]:
        shoulder_name = f"{side}Shoulder"
        pbone = armature.pose.bones.get(shoulder_name)
        if pbone:
            constraint = pbone.constraints.new('LIMIT_ROTATION')
            constraint.name = f"Limit_{shoulder_name}"
            constraint.owner_space = 'LOCAL'
            constraint.use_limit_x = True
            constraint.min_x = math.radians(-20)
            constraint.max_x = math.radians(20)
            constraint.use_limit_y = True
            constraint.min_y = math.radians(-15)
            constraint.max_y = math.radians(15)
            constraint.use_limit_z = True
            constraint.min_z = math.radians(-15)
            constraint.max_z = math.radians(15)
            constraints_added += 1
            print(f"    Added LIMIT_ROTATION on {shoulder_name}")

    # Leg rotation limits
    leg_bones = {
        "LeftUpLeg": {"min_x": -90, "max_x": 60, "min_z": -30, "max_z": 45},
        "RightUpLeg": {"min_x": -90, "max_x": 60, "min_z": -45, "max_z": 30},
        "LeftLeg": {"min_x": 0, "max_x": 150, "min_z": -5, "max_z": 5},
        "RightLeg": {"min_x": 0, "max_x": 150, "min_z": -5, "max_z": 5},
    }
    for bone_name, limits in leg_bones.items():
        pbone = armature.pose.bones.get(bone_name)
        if pbone:
            constraint = pbone.constraints.new('LIMIT_ROTATION')
            constraint.name = f"Limit_{bone_name}"
            constraint.owner_space = 'LOCAL'
            constraint.use_limit_x = True
            constraint.min_x = math.radians(limits["min_x"])
            constraint.max_x = math.radians(limits["max_x"])
            constraint.use_limit_z = True
            constraint.min_z = math.radians(limits["min_z"])
            constraint.max_z = math.radians(limits["max_z"])
            constraints_added += 1
            print(f"    Added LIMIT_ROTATION on {bone_name}")

    # --- Spine counter-rotation ---
    spine_bone = armature.pose.bones.get("Spine")
    hips_bone = armature.pose.bones.get("Hips")

    if spine_bone and hips_bone:
        constraint = spine_bone.constraints.new('COPY_ROTATION')
        constraint.name = "Spine_CounterRotation"
        constraint.target = armature
        constraint.subtarget = "Hips"
        constraint.use_x = False
        constraint.use_y = True
        constraint.use_z = True
        constraint.invert_y = True
        constraint.invert_z = True
        constraint.target_space = 'LOCAL'
        constraint.owner_space = 'LOCAL'
        constraint.influence = SPINE_COUNTER_ROTATION_INFLUENCE
        constraint.mix_mode = 'ADD'
        constraints_added += 1
        print(f"    Added COPY_ROTATION (counter) on Spine (influence={SPINE_COUNTER_ROTATION_INFLUENCE})")

    spine01_bone = armature.pose.bones.get("Spine01")
    if spine01_bone:
        constraint = spine01_bone.constraints.new('COPY_ROTATION')
        constraint.name = "Spine01_CounterRotation"
        constraint.target = armature
        constraint.subtarget = "Hips"
        constraint.use_x = False
        constraint.use_y = True
        constraint.use_z = True
        constraint.invert_y = True
        constraint.invert_z = True
        constraint.target_space = 'LOCAL'
        constraint.owner_space = 'LOCAL'
        constraint.influence = SPINE_COUNTER_ROTATION_INFLUENCE * 0.5
        constraint.mix_mode = 'ADD'
        constraints_added += 1
        print(f"    Added COPY_ROTATION (counter) on Spine01 (influence={SPINE_COUNTER_ROTATION_INFLUENCE * 0.5:.2f})")

    # --- Ponytail secondary motion constraints ---
    ponytail_bones = [f"Ponytail_{i+1:02d}" for i in range(4)]
    for i, bone_name in enumerate(ponytail_bones):
        pbone = armature.pose.bones.get(bone_name)
        if not pbone:
            continue

        # Copy rotation from Head with decreasing influence (lag effect)
        cr = pbone.constraints.new('COPY_ROTATION')
        cr.name = "Ponytail_Follow"
        cr.target = armature
        cr.subtarget = "Head"
        cr.target_space = 'LOCAL'
        cr.owner_space = 'LOCAL'
        cr.mix_mode = 'ADD'
        cr.influence = max(0.05, 0.4 - (i * 0.1))
        cr.use_x = True
        cr.use_y = True
        cr.use_z = True

        # Limit rotation to prevent extreme deformation
        lr = pbone.constraints.new('LIMIT_ROTATION')
        lr.name = "Ponytail_Limit"
        lr.owner_space = 'LOCAL'
        lr.use_limit_x = True
        lr.min_x = math.radians(-45 - i * 10)
        lr.max_x = math.radians(45 + i * 10)
        lr.use_limit_y = True
        lr.min_y = math.radians(-30 - i * 5)
        lr.max_y = math.radians(30 + i * 5)
        lr.use_limit_z = True
        lr.min_z = math.radians(-40 - i * 8)
        lr.max_z = math.radians(40 + i * 8)

        constraints_added += 2
        print(f"    Added COPY_ROTATION + LIMIT_ROTATION on {bone_name} (follow={cr.influence:.2f})")

    bpy.ops.object.mode_set(mode='OBJECT')
    print(f"  Total constraints applied: {constraints_added}")
    return constraints_added


def import_walking_animation():
    """Import walking animation GLB and extract the action"""
    walking_path = os.path.abspath("assets/models/characters/mia/animations/mia_walking.glb")
    print(f"  Importing walking animation: {walking_path}")

    if not os.path.exists(walking_path):
        print(f"  ERROR: File not found: {walking_path}")
        return None

    existing = set(obj.name for obj in bpy.data.objects)

    bpy.ops.import_scene.gltf(filepath=walking_path)

    walking_action = None
    for action in bpy.data.actions:
        if 'walking' in action.name.lower():
            walking_action = action
            break

    print(f"  Walking action: {walking_action.name if walking_action else 'None'}")
    if walking_action:
        print(f"  Frame range: {walking_action.frame_range}")

    # Delete imported objects (we only need the action)
    for obj in list(bpy.data.objects):
        if obj.name not in existing:
            bpy.data.objects.remove(obj, do_unlink=True)

    return walking_action


def apply_walking_animation(armature, walking_action, total_frames):
    """Apply walking animation to the armature with looping via NLA"""
    if not armature or not walking_action:
        print("  ERROR: Missing armature or action!")
        return

    if not armature.animation_data:
        armature.animation_data_create()

    armature.animation_data.action = None

    nla_tracks = armature.animation_data.nla_tracks
    for track in list(nla_tracks):
        nla_tracks.remove(track)

    track = nla_tracks.new()
    track.name = "WalkCycle"

    frame_start = walking_action.frame_range[0]
    frame_end = walking_action.frame_range[1]
    cycle_length = frame_end - frame_start

    num_repeats = math.ceil(total_frames / cycle_length) + 1

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
    """Set up 3-point lighting (same as v1 for comparison)"""
    bpy.ops.object.light_add(type='SUN', location=(5, -5, 10))
    key = bpy.context.active_object
    key.name = "Key_Light"
    key.data.energy = 3.0
    key.data.color = (1.0, 0.97, 0.95)
    key.rotation_euler = (math.radians(50), math.radians(10), math.radians(30))

    bpy.ops.object.light_add(type='AREA', location=(-4, -6, 4))
    fill = bpy.context.active_object
    fill.name = "Fill_Light"
    fill.data.energy = 100.0
    fill.data.size = 5.0
    fill.rotation_euler = (math.radians(60), 0, math.radians(-30))

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
    """Configure render settings"""
    scene = bpy.context.scene
    render = scene.render

    output_dir = os.path.dirname(os.path.abspath(args['output']))
    os.makedirs(output_dir, exist_ok=True)

    render.filepath = os.path.abspath(args['output'])
    render.image_settings.file_format = 'PNG'
    render.resolution_x = args['resolution'][0]
    render.resolution_y = args['resolution'][1]
    render.resolution_percentage = 100

    total_frames = args['fps'] * args['duration']
    scene.frame_start = 1
    scene.frame_end = total_frames
    scene.render.fps = args['fps']

    scene.render.engine = 'BLENDER_EEVEE'
    scene.eevee.taa_render_samples = args['samples']
    scene.eevee.use_gtao = True
    scene.eevee.gtao_distance = 1.0
    scene.eevee.use_bloom = False
    scene.eevee.use_ssr = False

    print(f"  Engine: EEVEE")
    print(f"  Resolution: {args['resolution'][0]}x{args['resolution'][1]}")
    print(f"  Samples: {args['samples']}")
    print(f"  Frames: {total_frames} ({args['duration']}s @ {args['fps']}fps)")

    return total_frames


def main():
    args = parse_args()

    print("=" * 60)
    print("Mia Walking Animation Test V2 - Fixed Rig Verification")
    print("=" * 60)
    print("Changes from V1:")
    print("  - Using mia_rigged_v2.glb (28 bones with ponytail chain)")
    print("  - Re-applying bone constraints (arm limits, spine counter-rotation, ponytail)")
    print(f"  - Resolution: {args['resolution'][0]}x{args['resolution'][1]} (was 1280x720)")
    print("")

    # Step 1: Clear scene
    print("[1/8] Clearing scene...")
    clear_scene()

    # Step 2: Import fixed rigged model
    print("\n[2/8] Importing Mia's fixed rig v2...")
    armature, mesh = import_mia_rigged_v2()
    if not armature:
        print("ERROR: Could not find armature in rigged model!")
        sys.exit(1)

    # Step 3: Re-apply bone constraints (lost during GLB export)
    print("\n[3/8] Re-applying bone constraints...")
    constraints_count = apply_rig_constraints(armature)

    # Step 4: Import walking animation
    print("\n[4/8] Importing walking animation...")
    walking_action = import_walking_animation()
    if not walking_action:
        print("ERROR: Could not find walking action!")
        sys.exit(1)

    # Step 5: Apply walking animation
    total_frames = args['fps'] * args['duration']
    print("\n[5/8] Applying walking animation...")
    apply_walking_animation(armature, walking_action, total_frames)

    # Step 6: Set up scene
    print("\n[6/8] Setting up scene...")
    setup_ground()
    setup_lighting()
    setup_world()
    camera, cam_target = setup_camera(armature)

    # Step 7: Configure render
    print("\n[7/8] Configuring render...")
    total_frames = configure_render(args)

    # Step 8: Render
    print(f"\n[8/8] Rendering {total_frames} frames...")
    print(f"Output: {os.path.abspath(args['output'])}")

    bpy.ops.render.render(animation=True)

    print("\n" + "=" * 60)
    print("RENDER COMPLETE!")
    print("=" * 60)

    output_dir = os.path.dirname(os.path.abspath(args['output']))
    frame_count = len([f for f in os.listdir(output_dir) if f.endswith('.png')])
    print(f"Frames saved: {frame_count} in {output_dir}")

    video_output = os.path.abspath(args['video_output'])
    frame_pattern = os.path.abspath(args['output']) + '%04d.png'
    print(f"\nTo create video:")
    print(f'  ffmpeg -framerate {args["fps"]} -i "{frame_pattern}" -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p -movflags +faststart "{video_output}"')


if __name__ == "__main__":
    main()
