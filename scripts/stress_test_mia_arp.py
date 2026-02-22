"""
Stress test Mia's ARP rig with 5 poses and render each.

Run with:
    blender models/characters/mia_arp_rigged.blend --background \
        --python scripts/stress_test_mia_arp.py

Renders 800x600 images to /tmp/arp_stress_tests/
"""

import bpy
import os
import math
from mathutils import Vector, Euler

OUTPUT_DIR = "/tmp/arp_stress_tests"


def setup_render():
    """Configure render settings for stress test images."""
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE'  # Fast, good quality
    scene.render.resolution_x = 800
    scene.render.resolution_y = 600
    scene.render.film_transparent = False

    # EEVEE settings for good quality
    scene.eevee.taa_render_samples = 64
    scene.eevee.use_gtao = True
    scene.eevee.use_bloom = False
    scene.eevee.shadow_cube_size = '512'

    # World background - neutral studio gray
    world = bpy.data.worlds.get('World')
    if world is None:
        world = bpy.data.worlds.new('World')
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get('Background')
    if bg:
        bg.inputs['Color'].default_value = (0.25, 0.25, 0.28, 1.0)
        bg.inputs['Strength'].default_value = 0.8


def setup_lighting():
    """Set up three-point lighting for character renders."""
    # Remove existing lights
    for obj in list(bpy.data.objects):
        if obj.type == 'LIGHT':
            bpy.data.objects.remove(obj, do_unlink=True)

    # Key light - warm, from front-right-above
    key = bpy.data.lights.new(name="Key_Light", type='AREA')
    key.energy = 120
    key.color = (1.0, 0.95, 0.9)
    key.size = 1.5
    key_obj = bpy.data.objects.new("Key_Light", key)
    bpy.context.scene.collection.objects.link(key_obj)
    key_obj.location = (1.0, -1.5, 2.0)
    key_obj.rotation_euler = (math.radians(50), math.radians(10), math.radians(30))

    # Fill light - cooler, from front-left
    fill = bpy.data.lights.new(name="Fill_Light", type='AREA')
    fill.energy = 50
    fill.color = (0.85, 0.9, 1.0)
    fill.size = 2.0
    fill_obj = bpy.data.objects.new("Fill_Light", fill)
    bpy.context.scene.collection.objects.link(fill_obj)
    fill_obj.location = (-1.2, -1.0, 1.5)
    fill_obj.rotation_euler = (math.radians(45), math.radians(-15), math.radians(-20))

    # Rim light - from behind
    rim = bpy.data.lights.new(name="Rim_Light", type='AREA')
    rim.energy = 80
    rim.color = (0.9, 0.92, 1.0)
    rim.size = 1.0
    rim_obj = bpy.data.objects.new("Rim_Light", rim)
    bpy.context.scene.collection.objects.link(rim_obj)
    rim_obj.location = (0.0, 1.5, 2.0)
    rim_obj.rotation_euler = (math.radians(130), 0, math.radians(180))

    # Ground plane for shadows
    bpy.ops.mesh.primitive_plane_add(size=5, location=(0, 0, 0.057))
    ground = bpy.context.active_object
    ground.name = "Ground_Plane"
    mat = bpy.data.materials.new(name="Ground_Mat")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (0.35, 0.35, 0.38, 1.0)
        bsdf.inputs['Roughness'].default_value = 0.9
        bsdf.inputs['Specular IOR Level'].default_value = 0.1
    ground.data.materials.append(mat)


def setup_camera():
    """Set up camera framing for a ~1.25m child character."""
    # Remove existing cameras
    for obj in list(bpy.data.objects):
        if obj.type == 'CAMERA':
            bpy.data.objects.remove(obj, do_unlink=True)

    cam_data = bpy.data.cameras.new(name="Stress_Cam")
    cam_data.lens = 65  # Mild telephoto for flattering character render
    cam_data.clip_start = 0.1
    cam_data.clip_end = 100

    cam_obj = bpy.data.objects.new("Stress_Cam", cam_data)
    bpy.context.scene.collection.objects.link(cam_obj)

    # Position: front-center, slightly above mid-height, looking at character center
    # Character height ~1.25m, center at ~0.65m
    cam_obj.location = (0.0, -2.0, 0.65)
    cam_obj.rotation_euler = (math.radians(90), 0, 0)

    bpy.context.scene.camera = cam_obj
    return cam_obj


def get_rig():
    """Find the ARP armature."""
    for obj in bpy.data.objects:
        if obj.type == 'ARMATURE':
            return obj
    return None


def reset_pose(rig):
    """Reset all pose bones to rest position."""
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode='POSE')
    bpy.ops.pose.select_all(action='SELECT')
    bpy.ops.pose.rot_clear()
    bpy.ops.pose.loc_clear()
    bpy.ops.pose.scale_clear()

    # Reset IK/FK switches to IK mode
    for bone_name in ['c_hand_ik.l', 'c_hand_ik.r', 'c_foot_ik.l', 'c_foot_ik.r']:
        pb = rig.pose.bones.get(bone_name)
        if pb and 'ik_fk_switch' in pb:
            pb['ik_fk_switch'] = 0.0  # IK mode

    bpy.ops.object.mode_set(mode='OBJECT')


def set_fk_arms(rig):
    """Switch arms to FK mode."""
    for bone_name in ['c_hand_ik.l', 'c_hand_ik.r']:
        pb = rig.pose.bones.get(bone_name)
        if pb and 'ik_fk_switch' in pb:
            pb['ik_fk_switch'] = 1.0  # FK mode


def set_ik_arms(rig):
    """Switch arms to IK mode."""
    for bone_name in ['c_hand_ik.l', 'c_hand_ik.r']:
        pb = rig.pose.bones.get(bone_name)
        if pb and 'ik_fk_switch' in pb:
            pb['ik_fk_switch'] = 0.0  # IK mode


def pose_bone_rotation(rig, bone_name, rx=0, ry=0, rz=0):
    """Set rotation on a pose bone (euler degrees)."""
    pb = rig.pose.bones.get(bone_name)
    if pb:
        pb.rotation_mode = 'XYZ'
        pb.rotation_euler = (math.radians(rx), math.radians(ry), math.radians(rz))
    else:
        print(f"  Warning: bone {bone_name} not found")


def pose_bone_location(rig, bone_name, x=0, y=0, z=0):
    """Set location on a pose bone."""
    pb = rig.pose.bones.get(bone_name)
    if pb:
        pb.location = (x, y, z)
    else:
        print(f"  Warning: bone {bone_name} not found")


def apply_pose_tpose(rig):
    """T-Pose: arms straight out to sides."""
    reset_pose(rig)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode='POSE')

    set_fk_arms(rig)

    # Arms straight out - rotate shoulders up and arms out
    # In A-pose the arms are down; for T-pose, rotate them up
    pose_bone_rotation(rig, 'c_arm_fk.l', rx=0, ry=0, rz=60)
    pose_bone_rotation(rig, 'c_arm_fk.r', rx=0, ry=0, rz=-60)

    bpy.ops.object.mode_set(mode='OBJECT')


def apply_pose_arms_overhead(rig):
    """Arms reaching overhead."""
    reset_pose(rig)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode='POSE')

    set_fk_arms(rig)

    # Arms overhead
    pose_bone_rotation(rig, 'c_arm_fk.l', rx=-30, ry=0, rz=140)
    pose_bone_rotation(rig, 'c_arm_fk.r', rx=-30, ry=0, rz=-140)
    pose_bone_rotation(rig, 'c_forearm_fk.l', rx=0, ry=0, rz=20)
    pose_bone_rotation(rig, 'c_forearm_fk.r', rx=0, ry=0, rz=-20)

    # Slight head tilt up
    pose_bone_rotation(rig, 'c_head.x', rx=-10)

    bpy.ops.object.mode_set(mode='OBJECT')


def apply_pose_deep_squat(rig):
    """Deep squat position."""
    reset_pose(rig)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode='POSE')

    set_fk_arms(rig)

    # Move root down for squat
    pose_bone_location(rig, 'c_root_master.x', z=-0.25)

    # Bend spine forward slightly
    pose_bone_rotation(rig, 'c_spine_01.x', rx=15)
    pose_bone_rotation(rig, 'c_spine_02.x', rx=10)

    # Arms forward for balance
    pose_bone_rotation(rig, 'c_arm_fk.l', rx=-45, ry=0, rz=20)
    pose_bone_rotation(rig, 'c_arm_fk.r', rx=-45, ry=0, rz=-20)

    bpy.ops.object.mode_set(mode='OBJECT')


def apply_pose_walking(rig):
    """Walking stride - one leg forward, one back."""
    reset_pose(rig)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode='POSE')

    set_fk_arms(rig)

    # Move feet apart using IK (default mode for legs)
    pose_bone_location(rig, 'c_foot_ik.l', y=-0.15, z=0.02)
    pose_bone_location(rig, 'c_foot_ik.r', y=0.15)

    # Arms swing opposite to legs
    pose_bone_rotation(rig, 'c_arm_fk.l', rx=30, rz=10)
    pose_bone_rotation(rig, 'c_arm_fk.r', rx=-25, rz=-10)
    pose_bone_rotation(rig, 'c_forearm_fk.l', rx=-15)
    pose_bone_rotation(rig, 'c_forearm_fk.r', rx=-30)

    # Slight torso twist
    pose_bone_rotation(rig, 'c_spine_01.x', ry=5)
    pose_bone_rotation(rig, 'c_spine_02.x', ry=-5)

    bpy.ops.object.mode_set(mode='OBJECT')


def apply_pose_spine_twist(rig):
    """Spine twist - torso rotated with head turn."""
    reset_pose(rig)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode='POSE')

    set_fk_arms(rig)

    # Spine twist
    pose_bone_rotation(rig, 'c_spine_01.x', ry=20, rx=5)
    pose_bone_rotation(rig, 'c_spine_02.x', ry=25, rx=-5)

    # Head turns opposite
    pose_bone_rotation(rig, 'c_neck.x', ry=-15)
    pose_bone_rotation(rig, 'c_head.x', ry=-20, rx=-5)

    # Arms follow body rotation
    pose_bone_rotation(rig, 'c_arm_fk.l', rx=-20, ry=15, rz=30)
    pose_bone_rotation(rig, 'c_arm_fk.r', rx=10, ry=-10, rz=-40)
    pose_bone_rotation(rig, 'c_forearm_fk.l', rx=-20)
    pose_bone_rotation(rig, 'c_forearm_fk.r', rx=-35)

    bpy.ops.object.mode_set(mode='OBJECT')


def render_pose(cam_obj, pose_name, output_dir):
    """Render the current pose."""
    filepath = os.path.join(output_dir, f"{pose_name}.png")
    bpy.context.scene.render.filepath = filepath
    bpy.ops.render.render(write_still=True)
    print(f"  Rendered: {filepath}")
    return filepath


def main():
    print("\n" + "=" * 60)
    print("STRESS TEST: MIA ARP RIG")
    print("=" * 60)

    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Find the rig
    rig = get_rig()
    if rig is None:
        print("ERROR: No armature found!")
        return

    print(f"Rig: {rig.name} ({len(rig.data.bones)} bones)")

    # Ensure rig and meshes are visible
    rig.hide_render = False
    rig.hide_viewport = False

    # Setup
    setup_render()
    setup_lighting()
    cam_obj = setup_camera()

    # Define poses
    poses = [
        ("01_tpose", apply_pose_tpose),
        ("02_arms_overhead", apply_pose_arms_overhead),
        ("03_deep_squat", apply_pose_deep_squat),
        ("04_walking_stride", apply_pose_walking),
        ("05_spine_twist", apply_pose_spine_twist),
    ]

    rendered_files = []
    for pose_name, pose_func in poses:
        print(f"\nApplying pose: {pose_name}")
        pose_func(rig)

        # Update scene
        bpy.context.view_layer.update()

        filepath = render_pose(cam_obj, pose_name, OUTPUT_DIR)
        rendered_files.append(filepath)

    # Reset to rest pose
    reset_pose(rig)

    print("\n" + "=" * 60)
    print(f"STRESS TEST COMPLETE - {len(rendered_files)} renders saved to {OUTPUT_DIR}")
    print("=" * 60)

    for f in rendered_files:
        print(f"  {f}")


main()
