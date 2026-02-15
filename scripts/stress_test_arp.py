"""
Stress test the ARP-rigged Mia character with various poses.

Usage:
    blender --background models/characters/mia_arp_rigged.blend \
        --python scripts/stress_test_arp.py

Renders 5 poses to /tmp/arp_stress_tests/ at 800x600:
    1. T-pose (rest)
    2. Arms overhead
    3. Deep squat
    4. Walking pose
    5. Spine twist
"""

import bpy
import sys
import os
import math
from mathutils import Vector, Euler

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
OUTPUT_DIR = "/tmp/arp_stress_tests"
RENDER_WIDTH = 800
RENDER_HEIGHT = 600

print("=" * 60)
print("  ARP Stress Test: Mia Poses")
print("=" * 60)
print(f"  Output: {OUTPUT_DIR}")
print()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def log(msg):
    print(f"  [STRESS] {msg}")


def force_update():
    """Force full depsgraph update including driver evaluation."""
    scn = bpy.context.scene
    cur = scn.frame_current
    scn.frame_set(cur + 1)
    scn.frame_set(cur)
    bpy.context.view_layer.update()


def reset_pose(rig):
    """Reset all pose bones to rest position."""
    for pb in rig.pose.bones:
        pb.location = (0, 0, 0)
        pb.rotation_quaternion = (1, 0, 0, 0)
        pb.rotation_euler = (0, 0, 0)
        pb.scale = (1, 1, 1)
    force_update()


def set_bone_rotation(rig, bone_name, euler_xyz_deg):
    """Set a pose bone's rotation in degrees (euler XYZ)."""
    pb = rig.pose.bones.get(bone_name)
    if pb is None:
        return False
    pb.rotation_mode = 'XYZ'
    pb.rotation_euler = (
        math.radians(euler_xyz_deg[0]),
        math.radians(euler_xyz_deg[1]),
        math.radians(euler_xyz_deg[2]),
    )
    return True


def set_bone_location(rig, bone_name, loc):
    """Set a pose bone's location."""
    pb = rig.pose.bones.get(bone_name)
    if pb is None:
        return False
    pb.location = loc
    return True


def find_bone(rig, *candidates):
    """Find the first matching bone from candidates."""
    for name in candidates:
        if rig.pose.bones.get(name):
            return name
    return None


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Find the body mesh first, then the rig it's bound to
body = None
for obj in bpy.data.objects:
    if obj.type == 'MESH' and 'mia' in obj.name.lower():
        body = obj
        break

# Find the rig that the body is actually bound to (via armature modifier or parent)
rig = None
if body:
    for mod in body.modifiers:
        if mod.type == 'ARMATURE' and mod.object:
            rig = mod.object
            break
    if rig is None and body.parent and body.parent.type == 'ARMATURE':
        rig = body.parent

# Fallback: just find any armature
if rig is None:
    for obj in bpy.data.objects:
        if obj.type == 'ARMATURE':
            rig = obj
            break

if rig is None:
    log("FATAL: No armature found in scene!")
    sys.exit(1)

log(f"Rig: {rig.name} ({len(rig.data.bones)} bones)")
if body:
    log(f"Body: {body.name}")

# Discover key control bones
BONE_ROOT = find_bone(rig, 'c_root_master.x', 'c_root.x', 'c_traj')
BONE_SPINE1 = find_bone(rig, 'c_spine_01.x')
BONE_SPINE2 = find_bone(rig, 'c_spine_02.x')
BONE_NECK = find_bone(rig, 'c_neck.x')
BONE_HEAD = find_bone(rig, 'c_head.x')
BONE_SHOULDER_L = find_bone(rig, 'c_shoulder.l')
BONE_SHOULDER_R = find_bone(rig, 'c_shoulder.r')
BONE_ARM_FK_L = find_bone(rig, 'c_arm_fk.l')
BONE_ARM_FK_R = find_bone(rig, 'c_arm_fk.r')
BONE_FOREARM_FK_L = find_bone(rig, 'c_forearm_fk.l')
BONE_FOREARM_FK_R = find_bone(rig, 'c_forearm_fk.r')
BONE_HAND_FK_L = find_bone(rig, 'c_hand_fk.l')
BONE_HAND_FK_R = find_bone(rig, 'c_hand_fk.r')
BONE_THIGH_FK_L = find_bone(rig, 'c_thigh_fk.l')
BONE_THIGH_FK_R = find_bone(rig, 'c_thigh_fk.r')
BONE_LEG_FK_L = find_bone(rig, 'c_leg_fk.l')
BONE_LEG_FK_R = find_bone(rig, 'c_leg_fk.r')
BONE_FOOT_FK_L = find_bone(rig, 'c_foot_fk.l')
BONE_FOOT_FK_R = find_bone(rig, 'c_foot_fk.r')
BONE_HAND_IK_L = find_bone(rig, 'c_hand_ik.l')
BONE_HAND_IK_R = find_bone(rig, 'c_hand_ik.r')
BONE_FOOT_IK_L = find_bone(rig, 'c_foot_ik.l')
BONE_FOOT_IK_R = find_bone(rig, 'c_foot_ik.r')

log(f"Root: {BONE_ROOT}, Spine1: {BONE_SPINE1}, Spine2: {BONE_SPINE2}")
log(f"Arm FK L: {BONE_ARM_FK_L}, R: {BONE_ARM_FK_R}")
log(f"Thigh FK L: {BONE_THIGH_FK_L}, R: {BONE_THIGH_FK_R}")

# Enter pose mode
bpy.ops.object.select_all(action='DESELECT')
rig.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='POSE')

# Switch ALL limbs to FK mode (ik_fk_switch: 0=IK, 1=FK)
log("Switching to FK mode...")
fk_switches = [BONE_HAND_IK_L, BONE_HAND_IK_R, BONE_FOOT_IK_L, BONE_FOOT_IK_R]
for bone_name in fk_switches:
    if bone_name:
        pb = rig.pose.bones.get(bone_name)
        if pb and 'ik_fk_switch' in pb.keys():
            pb['ik_fk_switch'] = 1.0
            log(f"  {bone_name}: ik_fk_switch = 1.0 (FK)")

# Critical: force depsgraph to evaluate drivers after FK switch
force_update()

# Verify FK switch took effect
for bone_name in fk_switches:
    if bone_name:
        pb = rig.pose.bones.get(bone_name)
        if pb:
            log(f"  Verified {bone_name}: ik_fk_switch = {pb.get('ik_fk_switch', 'N/A')}")


# ---------------------------------------------------------------------------
# Render setup
# ---------------------------------------------------------------------------
log("Setting up render...")

bpy.context.scene.render.engine = 'BLENDER_EEVEE'
bpy.context.scene.render.resolution_x = RENDER_WIDTH
bpy.context.scene.render.resolution_y = RENDER_HEIGHT
bpy.context.scene.render.resolution_percentage = 100
bpy.context.scene.render.image_settings.file_format = 'PNG'

# Camera setup - position to see the full character
cam = None
for obj in bpy.data.objects:
    if obj.type == 'CAMERA':
        cam = obj
        break

if cam is None:
    cam_data = bpy.data.cameras.new('StressTestCam')
    cam = bpy.data.objects.new('StressTestCam', cam_data)
    bpy.context.scene.collection.objects.link(cam)

bpy.context.scene.camera = cam

# Position camera: front-right, pulled back to frame full character with margin
# Character is ~1.26m tall centered at origin, so aim at mid-height
cam.location = (1.2, -3.5, 0.75)
cam.rotation_euler = (math.radians(82), 0, math.radians(18))
# Use a wider lens to capture more
if hasattr(cam.data, 'lens'):
    cam.data.lens = 35  # mm, wider than default 50mm

# Ensure lighting exists
lights = [obj for obj in bpy.data.objects if obj.type == 'LIGHT']
if not lights:
    light_data = bpy.data.lights.new('KeyLight', type='SUN')
    light_data.energy = 3.0
    light_obj = bpy.data.objects.new('KeyLight', light_data)
    light_obj.rotation_euler = (math.radians(50), math.radians(20), math.radians(-30))
    bpy.context.scene.collection.objects.link(light_obj)

# Set world background
world = bpy.context.scene.world
if world is None:
    world = bpy.data.worlds.new("StressTestWorld")
    bpy.context.scene.world = world
if world.use_nodes:
    bg = world.node_tree.nodes.get('Background')
    if bg:
        bg.inputs[0].default_value = (0.3, 0.3, 0.35, 1.0)
        bg.inputs[1].default_value = 1.0


# ---------------------------------------------------------------------------
# Pose definitions
# ---------------------------------------------------------------------------
def make_pose_tpose():
    """T-pose / rest pose."""
    return {}


def make_pose_arms_overhead():
    """Arms raised above head."""
    pose = {}
    # ARP FK arm bones: +X rotation swings forward, so ~170 deg goes overhead
    if BONE_ARM_FK_L:
        pose[BONE_ARM_FK_L] = (170, 0, 0)
    if BONE_ARM_FK_R:
        pose[BONE_ARM_FK_R] = (170, 0, 0)
    if BONE_FOREARM_FK_L:
        pose[BONE_FOREARM_FK_L] = (15, 0, 0)
    if BONE_FOREARM_FK_R:
        pose[BONE_FOREARM_FK_R] = (15, 0, 0)
    return pose


def make_pose_deep_squat():
    """Deep squat position."""
    pose = {}
    if BONE_THIGH_FK_L:
        pose[BONE_THIGH_FK_L] = (90, 0, 10)
    if BONE_THIGH_FK_R:
        pose[BONE_THIGH_FK_R] = (90, 0, -10)
    if BONE_LEG_FK_L:
        pose[BONE_LEG_FK_L] = (-120, 0, 0)
    if BONE_LEG_FK_R:
        pose[BONE_LEG_FK_R] = (-120, 0, 0)
    if BONE_SPINE1:
        pose[BONE_SPINE1] = (-15, 0, 0)  # Lean forward
    return pose


def make_pose_walking():
    """Mid-stride walking pose."""
    pose = {}
    # Left leg forward
    if BONE_THIGH_FK_L:
        pose[BONE_THIGH_FK_L] = (40, 0, 0)
    if BONE_LEG_FK_L:
        pose[BONE_LEG_FK_L] = (-20, 0, 0)
    # Right leg back
    if BONE_THIGH_FK_R:
        pose[BONE_THIGH_FK_R] = (-25, 0, 0)
    if BONE_LEG_FK_R:
        pose[BONE_LEG_FK_R] = (-40, 0, 0)
    # Arms swing opposite to legs
    if BONE_ARM_FK_L:
        pose[BONE_ARM_FK_L] = (-30, 0, 0)
    if BONE_ARM_FK_R:
        pose[BONE_ARM_FK_R] = (35, 0, 0)
    if BONE_FOREARM_FK_L:
        pose[BONE_FOREARM_FK_L] = (-25, 0, 0)
    if BONE_FOREARM_FK_R:
        pose[BONE_FOREARM_FK_R] = (-35, 0, 0)
    # Slight torso twist
    if BONE_SPINE2:
        pose[BONE_SPINE2] = (0, 0, 8)
    return pose


def make_pose_spine_twist():
    """Extreme spine twist to test deformation."""
    pose = {}
    if BONE_SPINE1:
        pose[BONE_SPINE1] = (15, 0, 45)  # Lean + twist
    if BONE_SPINE2:
        pose[BONE_SPINE2] = (10, 0, 50)  # More twist
    if BONE_NECK:
        pose[BONE_NECK] = (-10, 0, -30)  # Counter-twist
    if BONE_HEAD:
        pose[BONE_HEAD] = (25, 0, -20)  # Look to side
    # Arms in expressive asymmetric pose
    if BONE_ARM_FK_L:
        pose[BONE_ARM_FK_L] = (80, 0, 0)  # Arm raised forward
    if BONE_ARM_FK_R:
        pose[BONE_ARM_FK_R] = (-40, 0, 0)  # Arm back
    return pose


POSES = [
    ("01_t_pose", "T-Pose (Rest)", make_pose_tpose),
    ("02_arms_overhead", "Arms Overhead", make_pose_arms_overhead),
    ("03_deep_squat", "Deep Squat", make_pose_deep_squat),
    ("04_walking", "Walking Stride", make_pose_walking),
    ("05_spine_twist", "Spine Twist", make_pose_spine_twist),
]


# ---------------------------------------------------------------------------
# Render each pose
# ---------------------------------------------------------------------------
rendered = 0
for filename, label, pose_fn in POSES:
    log(f"Posing: {label}...")

    # Reset to rest
    reset_pose(rig)

    # Apply pose rotations
    pose = pose_fn()
    bones_set = 0
    for bone_name, rotation in pose.items():
        if bone_name and set_bone_rotation(rig, bone_name, rotation):
            bones_set += 1

    # For deep squat, also move root down
    if 'squat' in filename and BONE_ROOT:
        set_bone_location(rig, BONE_ROOT, (0, 0, -0.2))

    log(f"  Set {bones_set} bone rotations")

    # Force full depsgraph evaluation before rendering
    force_update()

    # Debug: check mesh deformation
    if body:
        dg = bpy.context.evaluated_depsgraph_get()
        eval_obj = body.evaluated_get(dg)
        eval_mesh = eval_obj.to_mesh()
        verts = [eval_obj.matrix_world @ v.co for v in eval_mesh.vertices]
        xmin = min(v.x for v in verts)
        xmax = max(v.x for v in verts)
        zmin = min(v.z for v in verts)
        zmax = max(v.z for v in verts)
        log(f"  Mesh bounds: x=[{xmin:.3f},{xmax:.3f}] z=[{zmin:.3f},{zmax:.3f}]")
        eval_obj.to_mesh_clear()

    # Render
    output_path = os.path.join(OUTPUT_DIR, f"{filename}.png")
    bpy.context.scene.render.filepath = output_path

    try:
        bpy.ops.render.render(write_still=True)
        log(f"  Rendered: {output_path}")
        rendered += 1
    except Exception as e:
        log(f"  Render error: {e}")
        try:
            bpy.ops.render.render()
            bpy.data.images['Render Result'].save_render(filepath=output_path)
            log(f"  Saved via save_render: {output_path}")
            rendered += 1
        except Exception as e2:
            log(f"  FAILED: {e2}")

# Back to object mode
try:
    bpy.ops.object.mode_set(mode='OBJECT')
except:
    pass

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
print()
print("=" * 60)
print("  Stress Test Complete!")
print("=" * 60)
print(f"  Rendered: {rendered}/{len(POSES)} poses")
print(f"  Output:   {OUTPUT_DIR}/")

if os.path.exists(OUTPUT_DIR):
    for f in sorted(os.listdir(OUTPUT_DIR)):
        fpath = os.path.join(OUTPUT_DIR, f)
        size = os.path.getsize(fpath)
        print(f"    {f} ({size:,} bytes)")

print("=" * 60)
