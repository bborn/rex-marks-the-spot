#!/usr/bin/env python3
"""
Mia Cleaned Rig Validation Renders
====================================
Renders test poses to validate the cleanup fixes:
1. Rest pose (T-pose) from multiple angles
2. Arms raised - tests shoulder deformation fix
3. Deep squat - tests hip/thigh weight fix
4. Arm back-swing pose - tests the clipping fix
5. Head turn - tests rotation limits
6. Walking pose (manual) - tests overall rig

Usage:
  blender --background --python scripts/render_mia_cleanup_validation.py
"""

import bpy
import math
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
INPUT_MODEL = os.path.join(PROJECT_DIR, "output", "mia_cleanup", "mia_cleaned.glb")
OUTPUT_DIR = os.path.join(PROJECT_DIR, "output", "mia_cleanup", "validation_renders")


def setup_scene():
    """Set up the scene for rendering."""
    # Clear default scene
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

    # Import model
    bpy.ops.import_scene.gltf(filepath=INPUT_MODEL)
    print(f"Imported: {INPUT_MODEL}")

    # Find armature and mesh
    armature = None
    mesh = None
    for obj in bpy.context.scene.objects:
        if obj.type == 'ARMATURE':
            armature = obj
        elif obj.type == 'MESH' and obj.vertex_groups:
            mesh = obj

    if not armature:
        raise RuntimeError("No armature found!")

    # Setup world background
    world = bpy.data.worlds.get('World')
    if not world:
        world = bpy.data.worlds.new('World')
    bpy.context.scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get('Background')
    if bg:
        bg.inputs[0].default_value = (0.15, 0.15, 0.18, 1.0)  # Dark blue-gray

    # Add camera
    cam_data = bpy.data.cameras.new('Camera')
    cam = bpy.data.objects.new('Camera', cam_data)
    bpy.context.scene.collection.objects.link(cam)
    bpy.context.scene.camera = cam

    # Add lighting
    # Key light
    key_data = bpy.data.lights.new('KeyLight', 'AREA')
    key_data.energy = 200
    key_data.size = 3
    key = bpy.data.objects.new('KeyLight', key_data)
    bpy.context.scene.collection.objects.link(key)
    key.location = (2, -3, 3)
    key.rotation_euler = (math.radians(50), 0, math.radians(30))

    # Fill light
    fill_data = bpy.data.lights.new('FillLight', 'AREA')
    fill_data.energy = 80
    fill_data.size = 4
    fill = bpy.data.objects.new('FillLight', fill_data)
    bpy.context.scene.collection.objects.link(fill)
    fill.location = (-2, -2, 2)
    fill.rotation_euler = (math.radians(50), 0, math.radians(-30))

    # Rim light
    rim_data = bpy.data.lights.new('RimLight', 'AREA')
    rim_data.energy = 100
    rim_data.size = 2
    rim = bpy.data.objects.new('RimLight', rim_data)
    bpy.context.scene.collection.objects.link(rim)
    rim.location = (0, 3, 3)
    rim.rotation_euler = (math.radians(130), 0, 0)

    # Add ground plane
    bpy.ops.mesh.primitive_plane_add(size=10, location=(0, 0, 0))
    ground = bpy.context.active_object
    ground.name = "Ground"
    mat = bpy.data.materials.new("Ground_Mat")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0.25, 0.25, 0.28, 1)
    bsdf.inputs["Roughness"].default_value = 0.8
    ground.data.materials.append(mat)

    # Render settings
    bpy.context.scene.render.engine = 'BLENDER_EEVEE'
    bpy.context.scene.render.resolution_x = 1280
    bpy.context.scene.render.resolution_y = 720
    bpy.context.scene.render.resolution_percentage = 100
    bpy.context.scene.render.film_transparent = False

    return armature, mesh, cam


def set_camera(cam, pos, look_at=(0, 0, 0.6)):
    """Position camera to look at a point."""
    cam.location = pos
    direction = (
        look_at[0] - pos[0],
        look_at[1] - pos[1],
        look_at[2] - pos[2],
    )
    # Calculate rotation to look at target
    import mathutils
    rot_quat = mathutils.Vector(direction).to_track_quat('-Z', 'Y')
    cam.rotation_euler = rot_quat.to_euler()


def reset_pose(armature):
    """Reset all bones to rest pose."""
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='POSE')
    bpy.ops.pose.select_all(action='SELECT')
    bpy.ops.pose.rot_clear()
    bpy.ops.pose.loc_clear()
    bpy.ops.object.mode_set(mode='OBJECT')


def pose_bone(armature, bone_name, rotation_degrees):
    """Rotate a bone by given Euler angles (degrees)."""
    if bone_name not in armature.pose.bones:
        print(f"  WARNING: Bone '{bone_name}' not found")
        return
    pbone = armature.pose.bones[bone_name]
    pbone.rotation_mode = 'XYZ'
    pbone.rotation_euler = (
        math.radians(rotation_degrees[0]),
        math.radians(rotation_degrees[1]),
        math.radians(rotation_degrees[2]),
    )


def render_pose(cam, output_name, description):
    """Render the current pose."""
    filepath = os.path.join(OUTPUT_DIR, f"{output_name}.png")
    bpy.context.scene.render.filepath = filepath
    bpy.ops.render.render(write_still=True)
    print(f"  Rendered: {output_name} ({description})")


def main():
    """Run all validation renders."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("\n=== MIA CLEANED RIG VALIDATION ===\n")

    armature, mesh, cam = setup_scene()

    # -- Pose 1: Rest pose (front view) --
    print("Pose 1: Rest pose...")
    reset_pose(armature)
    set_camera(cam, (0, -2.5, 0.8), (0, 0, 0.6))
    render_pose(cam, "01_rest_front", "Rest pose - front view")

    # -- Pose 1b: Rest pose (3/4 view) --
    set_camera(cam, (1.5, -2.0, 0.8), (0, 0, 0.6))
    render_pose(cam, "02_rest_3q", "Rest pose - 3/4 view")

    # -- Pose 2: Arms raised (shoulder test) --
    print("Pose 2: Arms raised...")
    reset_pose(armature)
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='POSE')
    pose_bone(armature, "LeftArm", (0, 0, -170))
    pose_bone(armature, "RightArm", (0, 0, 170))
    bpy.ops.object.mode_set(mode='OBJECT')

    set_camera(cam, (0, -2.5, 0.8), (0, 0, 0.7))
    render_pose(cam, "03_arms_up_front", "Arms raised - tests shoulder deformation")

    set_camera(cam, (1.5, -2.0, 0.8), (0, 0, 0.7))
    render_pose(cam, "04_arms_up_3q", "Arms raised - 3/4 view")

    # -- Pose 3: Deep squat (hip/thigh test) --
    print("Pose 3: Deep squat...")
    reset_pose(armature)
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='POSE')
    pose_bone(armature, "LeftUpLeg", (-90, 0, 0))
    pose_bone(armature, "RightUpLeg", (-90, 0, 0))
    pose_bone(armature, "LeftLeg", (90, 0, 0))
    pose_bone(armature, "RightLeg", (90, 0, 0))
    bpy.ops.object.mode_set(mode='OBJECT')

    set_camera(cam, (0, -2.5, 0.5), (0, 0, 0.3))
    render_pose(cam, "05_squat_front", "Deep squat - tests hip/thigh deformation")

    set_camera(cam, (2.0, -1.5, 0.5), (0, 0, 0.3))
    render_pose(cam, "06_squat_side", "Deep squat - side view")

    # -- Pose 4: Arm back-swing (clipping test) --
    print("Pose 4: Arm back-swing (the clipping pose)...")
    reset_pose(armature)
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='POSE')
    # Simulate walking arm back-swing
    pose_bone(armature, "LeftArm", (30, 0, 0))    # Left arm swings back
    pose_bone(armature, "RightArm", (-30, 0, 0))   # Right arm swings forward
    # Slight leg movement
    pose_bone(armature, "LeftUpLeg", (-30, 0, 0))
    pose_bone(armature, "RightUpLeg", (15, 0, 0))
    bpy.ops.object.mode_set(mode='OBJECT')

    set_camera(cam, (0, -2.5, 0.8), (0, 0, 0.6))
    render_pose(cam, "07_backswing_front", "Arm back-swing - tests clipping fix")

    set_camera(cam, (2.0, -1.0, 0.8), (0, 0, 0.6))
    render_pose(cam, "08_backswing_side", "Arm back-swing - side view")

    # -- Pose 5: Head turn (rotation limit test) --
    print("Pose 5: Head turn...")
    reset_pose(armature)
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='POSE')
    pose_bone(armature, "Head", (0, 0, 70))   # Turn head
    pose_bone(armature, "neck", (0, 0, 20))   # Slight neck
    bpy.ops.object.mode_set(mode='OBJECT')

    set_camera(cam, (0, -2.5, 0.8), (0, 0, 0.7))
    render_pose(cam, "09_head_turn_front", "Head turn - tests rotation limits")

    # -- Pose 6: Walking pose (overall test) --
    print("Pose 6: Walking pose...")
    reset_pose(armature)
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='POSE')
    # Walking mid-stride
    pose_bone(armature, "LeftUpLeg", (-25, 0, 0))   # Left leg forward
    pose_bone(armature, "LeftLeg", (30, 0, 0))
    pose_bone(armature, "RightUpLeg", (20, 0, 0))   # Right leg back
    pose_bone(armature, "RightLeg", (10, 0, 0))
    pose_bone(armature, "LeftArm", (20, 0, 0))       # Counter-swing arms
    pose_bone(armature, "RightArm", (-20, 0, 0))
    pose_bone(armature, "Spine", (0, 5, 0))          # Slight spine twist
    pose_bone(armature, "Spine01", (0, -3, 0))       # Counter-rotation
    bpy.ops.object.mode_set(mode='OBJECT')

    set_camera(cam, (0, -2.5, 0.8), (0, 0, 0.6))
    render_pose(cam, "10_walking_front", "Walking pose - overall rig test")

    set_camera(cam, (2.0, -1.5, 0.8), (0, 0, 0.6))
    render_pose(cam, "11_walking_3q", "Walking pose - 3/4 view")

    # -- Pose 7: Ponytail test (back view) --
    print("Pose 7: Ponytail visibility test...")
    reset_pose(armature)
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='POSE')
    # Pose ponytail bones to show they can move
    pose_bone(armature, "Ponytail_01", (10, 5, 0))
    pose_bone(armature, "Ponytail_02", (15, 8, 0))
    pose_bone(armature, "Ponytail_03", (20, 10, 0))
    pose_bone(armature, "Ponytail_04", (25, 12, 0))
    pose_bone(armature, "Ponytail_05", (30, 15, 0))
    bpy.ops.object.mode_set(mode='OBJECT')

    set_camera(cam, (0, 2.5, 0.8), (0, 0, 0.7))
    render_pose(cam, "12_ponytail_back", "Ponytail posed - back view")

    set_camera(cam, (1.5, 2.0, 0.8), (0, 0, 0.7))
    render_pose(cam, "13_ponytail_3q_back", "Ponytail posed - 3/4 back view")

    print(f"\n=== All validation renders saved to: {OUTPUT_DIR} ===")
    print(f"Total renders: 13")


if __name__ == "__main__":
    main()
