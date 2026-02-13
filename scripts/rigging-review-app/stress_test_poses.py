"""
Stress Test Poses for Rigging Validation

Run in Blender:
    blender model.blend --background --python stress_test_poses.py -- --output ./renders/ --upload http://rex:3090

This script:
1. Detects the armature in the scene
2. Poses it into 8 stress positions that expose common rigging issues
3. Renders each pose from front + 3/4 view
4. Optionally uploads renders to the Rigging Review app

Requires: Blender 3.6+ with a rigged character (armature + mesh)
"""

import argparse
import math
import os
import sys
from pathlib import Path

# Must be run inside Blender
try:
    import bpy
    import mathutils
    IN_BLENDER = True
except ImportError:
    IN_BLENDER = False
    print("WARNING: Not running in Blender. Printing pose definitions only.")


# ---------------------------------------------------------------------------
# Stress Test Pose Definitions
# ---------------------------------------------------------------------------
# Each pose targets specific rigging problem areas.
# Bone rotations are in degrees (converted to radians in apply_pose).
# Names use common Mixamo / Auto-Rig Pro bone naming conventions.
# The script tries multiple naming conventions to find the right bones.

BONE_NAME_VARIANTS = {
    "hips": ["hips", "Hips", "mixamorig:Hips", "DEF-spine", "root", "Root"],
    "spine": ["spine", "Spine", "mixamorig:Spine", "DEF-spine.001"],
    "spine1": ["spine1", "Spine1", "mixamorig:Spine1", "DEF-spine.002"],
    "spine2": ["spine2", "Spine2", "mixamorig:Spine2", "DEF-spine.003"],
    "neck": ["neck", "Neck", "mixamorig:Neck", "DEF-spine.004"],
    "head": ["head", "Head", "mixamorig:Head", "DEF-spine.005"],
    "left_upper_arm": ["leftshoulder", "LeftArm", "mixamorig:LeftArm", "DEF-upper_arm.L", "Left arm", "LeftUpperArm", "upper_arm.L"],
    "right_upper_arm": ["rightshoulder", "RightArm", "mixamorig:RightArm", "DEF-upper_arm.R", "Right arm", "RightUpperArm", "upper_arm.R"],
    "left_forearm": ["leftforearm", "LeftForeArm", "mixamorig:LeftForeArm", "DEF-forearm.L", "Left forearm", "forearm.L"],
    "right_forearm": ["rightforearm", "RightForeArm", "mixamorig:RightForeArm", "DEF-forearm.R", "Right forearm", "forearm.R"],
    "left_upper_leg": ["leftupleg", "LeftUpLeg", "mixamorig:LeftUpLeg", "DEF-thigh.L", "Left thigh", "thigh.L"],
    "right_upper_leg": ["rightupleg", "RightUpLeg", "mixamorig:RightUpLeg", "DEF-thigh.R", "Right thigh", "thigh.R"],
    "left_lower_leg": ["leftleg", "LeftLeg", "mixamorig:LeftLeg", "DEF-shin.L", "Left shin", "shin.L"],
    "right_lower_leg": ["rightleg", "RightLeg", "mixamorig:RightLeg", "DEF-shin.R", "Right shin", "shin.R"],
}

STRESS_POSES = [
    {
        "name": "t_pose",
        "description": "T-Pose (baseline) - default rest position, arms straight out",
        "tests": "Baseline mesh quality, overall proportions",
        "bones": {},  # Reset to rest pose
    },
    {
        "name": "deep_squat",
        "description": "Deep squat - knees bent 120deg, hips dropped",
        "tests": "Hip/thigh weight painting, knee deformation, groin area",
        "bones": {
            "left_upper_leg": {"x": 100},
            "right_upper_leg": {"x": 100},
            "left_lower_leg": {"x": -120},
            "right_lower_leg": {"x": -120},
        },
    },
    {
        "name": "arms_overhead",
        "description": "Both arms raised overhead",
        "tests": "Shoulder weight painting, armpit deformation, torso stretch",
        "bones": {
            "left_upper_arm": {"z": 170},
            "right_upper_arm": {"z": -170},
        },
    },
    {
        "name": "arms_behind_back",
        "description": "Arms pulled behind the back",
        "tests": "Shoulder/chest clipping, back deformation",
        "bones": {
            "left_upper_arm": {"z": -45, "x": -30},
            "right_upper_arm": {"z": 45, "x": -30},
        },
    },
    {
        "name": "spine_twist",
        "description": "Torso twisted 90 degrees",
        "tests": "Spine weight distribution, torso deformation, waist twisting",
        "bones": {
            "spine": {"y": 30},
            "spine1": {"y": 30},
            "spine2": {"y": 30},
        },
    },
    {
        "name": "extreme_head_turn",
        "description": "Head turned 90 degrees to the side",
        "tests": "Neck weights, jaw/chin area, hair deformation",
        "bones": {
            "neck": {"y": 30},
            "head": {"y": 60},
        },
    },
    {
        "name": "walk_extreme",
        "description": "Extreme walk pose - one leg forward, one back, arms swinging",
        "tests": "Overall deformation during locomotion, hip rotation",
        "bones": {
            "left_upper_leg": {"x": 60},
            "right_upper_leg": {"x": -40},
            "left_lower_leg": {"x": -30},
            "right_lower_leg": {"x": -60},
            "left_upper_arm": {"x": -30},
            "right_upper_arm": {"x": 30},
            "left_forearm": {"x": -20},
            "right_forearm": {"x": -40},
        },
    },
    {
        "name": "full_bend_forward",
        "description": "Bending forward at the waist, touching toes",
        "tests": "Spine chain, belly/waist area, back stretching",
        "bones": {
            "spine": {"x": 30},
            "spine1": {"x": 30},
            "spine2": {"x": 30},
        },
    },
]


def print_pose_definitions():
    """Print pose definitions for documentation."""
    print("\n=== STRESS TEST POSES ===\n")
    for i, pose in enumerate(STRESS_POSES, 1):
        print(f"{i}. {pose['name']}")
        print(f"   {pose['description']}")
        print(f"   Tests: {pose['tests']}")
        if pose['bones']:
            print(f"   Bones modified: {', '.join(pose['bones'].keys())}")
        print()


if not IN_BLENDER:
    print_pose_definitions()
    sys.exit(0)


# ---------------------------------------------------------------------------
# Blender Functions
# ---------------------------------------------------------------------------

def find_armature():
    """Find the first armature in the scene."""
    for obj in bpy.context.scene.objects:
        if obj.type == 'ARMATURE':
            return obj
    return None


def find_bone(armature, canonical_name):
    """Find a bone by trying multiple naming conventions."""
    variants = BONE_NAME_VARIANTS.get(canonical_name, [canonical_name])
    for name in variants:
        if name in armature.pose.bones:
            return armature.pose.bones[name]
    # Also try case-insensitive
    lower_variants = [v.lower() for v in variants]
    for bone in armature.pose.bones:
        if bone.name.lower() in lower_variants:
            return bone
    return None


def reset_pose(armature):
    """Reset all bones to rest pose."""
    for bone in armature.pose.bones:
        bone.rotation_mode = 'XYZ'
        bone.rotation_euler = (0, 0, 0)
        bone.location = (0, 0, 0)
        bone.scale = (1, 1, 1)


def apply_pose(armature, bone_rotations):
    """Apply rotations (in degrees) to named bones."""
    reset_pose(armature)
    missing_bones = []
    for canonical_name, rotations in bone_rotations.items():
        bone = find_bone(armature, canonical_name)
        if bone is None:
            missing_bones.append(canonical_name)
            continue
        bone.rotation_mode = 'XYZ'
        bone.rotation_euler = (
            math.radians(rotations.get("x", 0)),
            math.radians(rotations.get("y", 0)),
            math.radians(rotations.get("z", 0)),
        )
    if missing_bones:
        print(f"  WARNING: Could not find bones: {', '.join(missing_bones)}")
    bpy.context.view_layer.update()


def setup_camera(armature, angle_name="front"):
    """Position camera to view the character."""
    # Get armature bounds
    bbox = [armature.matrix_world @ mathutils.Vector(c) for c in armature.bound_box]
    center = sum(bbox, mathutils.Vector()) / 8
    size = max((max(v[i] for v in bbox) - min(v[i] for v in bbox)) for i in range(3))

    cam = bpy.context.scene.camera
    if cam is None:
        bpy.ops.object.camera_add()
        cam = bpy.context.object
        bpy.context.scene.camera = cam

    dist = size * 2.5
    if angle_name == "front":
        cam.location = (center.x, center.y - dist, center.z + size * 0.3)
    elif angle_name == "quarter":
        cam.location = (center.x + dist * 0.7, center.y - dist * 0.7, center.z + size * 0.3)

    # Point at center
    direction = center - cam.location
    rot = direction.to_track_quat('-Z', 'Y')
    cam.rotation_euler = rot.to_euler()


def setup_lighting():
    """Ensure basic lighting exists."""
    has_light = any(obj.type == 'LIGHT' for obj in bpy.context.scene.objects)
    if not has_light:
        bpy.ops.object.light_add(type='SUN', location=(5, -5, 10))
        bpy.context.object.data.energy = 3


def render_pose(output_path, resolution=(1280, 960)):
    """Render the current viewport to a file."""
    scene = bpy.context.scene
    scene.render.resolution_x = resolution[0]
    scene.render.resolution_y = resolution[1]
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.filepath = str(output_path)

    # Use EEVEE for speed
    scene.render.engine = 'BLENDER_EEVEE_NEXT' if bpy.app.version >= (4, 0, 0) else 'BLENDER_EEVEE'

    bpy.ops.render.render(write_still=True)
    print(f"  Rendered: {output_path}")


def upload_to_review_app(output_dir, character_name, rigging_tool, notes, server_url):
    """Upload all renders to the review app via bulk-upload API."""
    import subprocess

    renders = sorted(Path(output_dir).glob("*.png"))
    if not renders:
        print("No renders to upload")
        return

    cmd = [
        "curl", "-s", "-X", "POST", f"{server_url}/api/bulk-upload",
        "-F", f"character_name={character_name}",
        "-F", f"rigging_tool={rigging_tool}",
        "-F", f"notes={notes}",
        "-F", f"pose_names={','.join(r.stem for r in renders)}",
    ]
    for r in renders:
        cmd.extend(["-F", f"images=@{r}"])

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"Uploaded {len(renders)} renders to {server_url}")
        print(result.stdout)
    else:
        print(f"Upload failed: {result.stderr}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    # Parse args after '--'
    argv = sys.argv
    if '--' in argv:
        argv = argv[argv.index('--') + 1:]
    else:
        argv = []

    parser = argparse.ArgumentParser(description="Stress test rigging poses")
    parser.add_argument("--output", default="./stress_test_renders/", help="Output directory")
    parser.add_argument("--upload", default="", help="Review app URL (e.g. http://rex:3090)")
    parser.add_argument("--character", default="", help="Character name for upload")
    parser.add_argument("--tool", default="", help="Rigging tool used")
    parser.add_argument("--notes", default="", help="Notes for this iteration")
    parser.add_argument("--poses", default="all", help="Comma-separated pose names, or 'all'")
    args = parser.parse_args(argv)

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    armature = find_armature()
    if armature is None:
        print("ERROR: No armature found in scene!")
        sys.exit(1)

    print(f"Found armature: {armature.name}")
    print(f"Bones: {len(armature.pose.bones)}")
    print(f"Output: {output_dir}")

    # List available bones for debugging
    print(f"Available bones: {[b.name for b in armature.pose.bones[:20]]}...")

    setup_lighting()

    # Select which poses to render
    if args.poses == "all":
        poses = STRESS_POSES
    else:
        names = [n.strip() for n in args.poses.split(",")]
        poses = [p for p in STRESS_POSES if p["name"] in names]

    # Select armature
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='POSE')

    for pose in poses:
        print(f"\nPose: {pose['name']} - {pose['description']}")
        apply_pose(armature, pose["bones"])

        for angle in ["front", "quarter"]:
            setup_camera(armature, angle)
            out_path = output_dir / f"{pose['name']}_{angle}"
            render_pose(str(out_path))

    # Reset to rest pose
    reset_pose(armature)
    bpy.ops.object.mode_set(mode='OBJECT')

    print(f"\nDone! Rendered {len(poses) * 2} images to {output_dir}")

    # Upload if requested
    if args.upload:
        char_name = args.character or armature.name
        upload_to_review_app(
            output_dir, char_name, args.tool, args.notes, args.upload
        )


if __name__ == "__main__":
    main()
