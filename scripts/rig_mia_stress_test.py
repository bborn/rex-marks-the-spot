"""
Stress test Mia's ARP rig with various poses and render images.

Usage:
    blender --background models/characters/mia_rigged.blend --python scripts/rig_mia_stress_test.py
"""

import bpy
import mathutils
import math
import addon_utils
import sys
import os

OUTPUT_DIR = "/tmp/mia_stress_tests"


def log(msg):
    print(f"[TEST] {msg}")
    sys.stdout.flush()


def setup_render():
    """Configure render settings for stress test images."""
    scn = bpy.context.scene
    scn.render.engine = 'BLENDER_EEVEE'
    scn.render.resolution_x = 800
    scn.render.resolution_y = 1000
    scn.render.resolution_percentage = 100
    scn.render.film_transparent = True
    scn.render.image_settings.file_format = 'PNG'

    # Use the existing camera or create one
    cam = bpy.data.objects.get('Character_Camera')
    if not cam:
        cam_data = bpy.data.cameras.new('StressTestCam')
        cam = bpy.data.objects.new('StressTestCam', cam_data)
        bpy.context.scene.collection.objects.link(cam)
        cam.location = (0, -3, 0.7)
        cam.rotation_euler = (math.radians(90), 0, 0)
    scn.camera = cam

    # Set up camera at eye level of the character, front-side view
    # Character is ~1.2m tall, centered around z=0.65
    cam.location = (0.5, -2.0, 0.65)
    # Point camera at the character center
    direction = mathutils.Vector((0, 0, 0.65)) - cam.location
    rot = direction.to_track_quat('-Z', 'Y').to_euler()
    cam.rotation_euler = rot
    cam_data = cam.data
    cam_data.lens = 35  # Wide enough to capture full body with margin

    # Ensure lights
    if not bpy.data.objects.get('Sun_Light'):
        light_data = bpy.data.lights.new('Sun_Light', 'SUN')
        light = bpy.data.objects.new('Sun_Light', light_data)
        bpy.context.scene.collection.objects.link(light)
        light.location = (2, -2, 3)


def switch_to_fk(rig):
    """Switch all limbs to FK mode for direct bone rotation control."""
    bpy.ops.object.select_all(action='DESELECT')
    rig.select_set(True)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode='POSE')

    # Set FK mode on all IK/FK switches (1.0 = FK in ARP)
    for pb in rig.pose.bones:
        if 'ik_fk_switch' in pb.keys():
            pb['ik_fk_switch'] = 1.0

    bpy.ops.object.mode_set(mode='OBJECT')


def reset_pose(rig):
    """Reset all bones to rest pose."""
    bpy.ops.object.select_all(action='DESELECT')
    rig.select_set(True)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode='POSE')

    for pbone in rig.pose.bones:
        pbone.location = (0, 0, 0)
        pbone.rotation_quaternion = (1, 0, 0, 0)
        pbone.rotation_euler = (0, 0, 0)
        pbone.scale = (1, 1, 1)

    bpy.ops.object.mode_set(mode='OBJECT')


def set_bone_rotation(rig, bone_name, euler_xyz_deg):
    """Set a pose bone's rotation in degrees (XYZ euler)."""
    bpy.ops.object.select_all(action='DESELECT')
    rig.select_set(True)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode='POSE')

    pbone = rig.pose.bones.get(bone_name)
    if pbone:
        pbone.rotation_mode = 'XYZ'
        pbone.rotation_euler = (
            math.radians(euler_xyz_deg[0]),
            math.radians(euler_xyz_deg[1]),
            math.radians(euler_xyz_deg[2])
        )
    else:
        log(f"  WARNING: bone {bone_name} not found")

    bpy.ops.object.mode_set(mode='OBJECT')


def render_pose(name, filepath):
    """Render the current pose to a file."""
    # Force depsgraph update before rendering
    bpy.context.view_layer.update()
    bpy.context.scene.render.filepath = filepath
    bpy.ops.render.render(write_still=True)
    log(f"  Rendered: {filepath}")


def pose_tpose(rig):
    """T-pose (rest pose) - baseline reference."""
    reset_pose(rig)


def pose_arms_overhead(rig):
    """Arms raised overhead - tests shoulder deformation."""
    reset_pose(rig)
    # Arms in T-pose go sideways. To raise overhead, rotate around local Z (roll axis)
    # In ARP convention, arm.l Z rotation raises the arm
    set_bone_rotation(rig, 'c_arm_fk.l', (0, -160, 0))   # Rotate up
    set_bone_rotation(rig, 'c_arm_fk.r', (0, 160, 0))    # Mirror


def pose_deep_squat(rig):
    """Deep squat - tests hip and knee deformation."""
    reset_pose(rig)
    # Bend thighs forward (squat)
    set_bone_rotation(rig, 'c_thigh_fk.l', (-80, 0, 0))
    set_bone_rotation(rig, 'c_thigh_fk.r', (-80, 0, 0))
    # Bend knees (c_leg_fk only has Z unlocked, so use Z for knee bend)
    set_bone_rotation(rig, 'c_leg_fk.l', (0, 0, 90))
    set_bone_rotation(rig, 'c_leg_fk.r', (0, 0, 90))
    # Lower the root
    bpy.ops.object.select_all(action='DESELECT')
    rig.select_set(True)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode='POSE')
    root = rig.pose.bones.get('c_root_master.x')
    if root:
        root.location = (0, 0, -0.3)
    bpy.ops.object.mode_set(mode='OBJECT')


def pose_walking(rig):
    """Walking pose - tests all limb deformation."""
    reset_pose(rig)
    # Left leg forward, right leg back
    set_bone_rotation(rig, 'c_thigh_fk.l', (-30, 0, 0))
    set_bone_rotation(rig, 'c_leg_fk.l', (0, 0, 20))  # Z only
    set_bone_rotation(rig, 'c_thigh_fk.r', (20, 0, 0))
    set_bone_rotation(rig, 'c_leg_fk.r', (0, 0, 10))  # Z only
    # Arms swing (opposite to legs)
    set_bone_rotation(rig, 'c_arm_fk.l', (20, -45, 0))
    set_bone_rotation(rig, 'c_forearm_fk.l', (0, 0, -30))  # Z only
    set_bone_rotation(rig, 'c_arm_fk.r', (-20, 45, 0))
    set_bone_rotation(rig, 'c_forearm_fk.r', (0, 0, -30))  # Z only
    # Slight spine twist
    set_bone_rotation(rig, 'c_spine_01.x', (0, 0, 5))


def pose_spine_twist(rig):
    """Spine twist - tests torso deformation."""
    reset_pose(rig)
    # Dramatic spine twist
    set_bone_rotation(rig, 'c_spine_01.x', (15, 45, 0))
    set_bone_rotation(rig, 'c_spine_02.x', (0, -30, 0))
    set_bone_rotation(rig, 'c_head.x', (-10, -20, 0))
    # Arms in a gesture pose
    set_bone_rotation(rig, 'c_arm_fk.l', (0, -80, 0))
    set_bone_rotation(rig, 'c_forearm_fk.l', (0, 0, -60))
    set_bone_rotation(rig, 'c_arm_fk.r', (30, 45, 0))


def pose_head_turn(rig):
    """Head turn with tilt - tests neck/head deformation."""
    reset_pose(rig)
    # Dramatic head turn and tilt
    set_bone_rotation(rig, 'c_neck.x', (15, 30, 0))
    set_bone_rotation(rig, 'c_head.x', (-20, 45, 0))
    # Slight body lean
    set_bone_rotation(rig, 'c_spine_01.x', (5, 15, 0))


def main():
    log("=" * 60)
    log("Stress Testing Mia Rig")
    log("=" * 60)

    # Enable ARP for rig tools
    addon_utils.enable('auto_rig_pro', default_set=True)
    addon_utils.enable('rig_tools', default_set=True)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Find the rig
    rig = bpy.data.objects.get('rig')
    if not rig:
        raise RuntimeError("No rig found in scene!")
    log(f"Found rig: {rig.name} with {len(rig.data.bones)} bones")

    # Switch to FK mode for direct bone rotation control
    switch_to_fk(rig)
    log("Switched to FK mode")

    setup_render()

    # Define stress test poses
    poses = [
        ("01_tpose", "T-Pose (rest)", pose_tpose),
        ("02_arms_overhead", "Arms Overhead", pose_arms_overhead),
        ("03_deep_squat", "Deep Squat", pose_deep_squat),
        ("04_walking", "Walking", pose_walking),
        ("05_spine_twist", "Spine Twist", pose_spine_twist),
        ("06_head_turn", "Head Turn", pose_head_turn),
    ]

    rendered = []
    for filename, label, pose_fn in poses:
        log(f"\nPose: {label}")
        try:
            pose_fn(rig)
            filepath = os.path.join(OUTPUT_DIR, f"{filename}.png")
            render_pose(label, filepath)
            rendered.append(filepath)
        except Exception as e:
            log(f"  FAILED: {e}")
            import traceback
            traceback.print_exc()

    log(f"\n{'=' * 60}")
    log(f"Rendered {len(rendered)} stress test images to {OUTPUT_DIR}")
    log(f"{'=' * 60}")


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        log(f"FATAL: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
