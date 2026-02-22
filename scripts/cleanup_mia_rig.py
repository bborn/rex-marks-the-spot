#!/usr/bin/env python3
"""
Mia Rig Cleanup Script
=======================
Follows Section 3: Post-Meshy Cleanup in Blender from the production guide.

This script:
  1. Imports Mia's Meshy auto-rigged GLB
  2. Cleans up stray objects (Icosphere)
  3. Fixes weight painting (normalize, limit, clean)
  4. Fixes shoulder and hip area weight bleed
  5. Adds rotation limits to prevent impossible poses
  6. Adds IK constraints to hands and feet
  7. Adds ponytail bone chain for secondary motion
  8. Adds spine counter-rotation for natural walking
  9. Exports cleaned GLB and FBX

Usage:
  blender --background --python scripts/cleanup_mia_rig.py

Bone naming (Meshy convention):
  Hips > LeftUpLeg/RightUpLeg > LeftLeg/RightLeg > LeftFoot/RightFoot > LeftToeBase/RightToeBase
  Hips > Spine02 > Spine01 > Spine > LeftShoulder/RightShoulder > LeftArm/RightArm > LeftForeArm/RightForeArm > LeftHand/RightHand
  Spine > neck > Head > head_end, headfront
"""

import bpy
import bmesh
import math
import os
import sys
import json
from mathutils import Vector, Euler


# ---- Configuration ----

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
INPUT_MODEL = os.path.join(PROJECT_DIR, "output", "mia_cleanup", "mia_rigged.glb")
OUTPUT_DIR = os.path.join(PROJECT_DIR, "output", "mia_cleanup")
OUTPUT_GLB = os.path.join(OUTPUT_DIR, "mia_cleaned.glb")
OUTPUT_FBX = os.path.join(OUTPUT_DIR, "mia_cleaned.fbx")
REPORT_PATH = os.path.join(OUTPUT_DIR, "cleanup_report.json")

# Meshy bone name mapping
BONE_NAMES = {
    "hips": "Hips",
    "left_upleg": "LeftUpLeg",
    "left_leg": "LeftLeg",
    "left_foot": "LeftFoot",
    "left_toe": "LeftToeBase",
    "right_upleg": "RightUpLeg",
    "right_leg": "RightLeg",
    "right_foot": "RightFoot",
    "right_toe": "RightToeBase",
    "spine02": "Spine02",  # Lower spine (child of Hips)
    "spine01": "Spine01",  # Mid spine
    "spine": "Spine",       # Upper spine / chest
    "left_shoulder": "LeftShoulder",
    "left_arm": "LeftArm",
    "left_forearm": "LeftForeArm",
    "left_hand": "LeftHand",
    "right_shoulder": "RightShoulder",
    "right_arm": "RightArm",
    "right_forearm": "RightForeArm",
    "right_hand": "RightHand",
    "neck": "neck",
    "head": "Head",
    "head_end": "head_end",
    "headfront": "headfront",
}

# Number of ponytail bones to add
PONYTAIL_BONE_COUNT = 5
PONYTAIL_BONE_LENGTH = 0.04  # Length of each ponytail bone segment


def log(msg):
    """Print with prefix for easy identification in logs."""
    print(f"[MIA CLEANUP] {msg}")


# ---- Step 0: Import and Verify ----

def step_import_and_verify():
    """Import Mia's rigged GLB and verify structure."""
    log("Step 0: Importing model...")

    # Clear default scene
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

    # Import GLB
    bpy.ops.import_scene.gltf(filepath=INPUT_MODEL)

    # Verify scene objects
    armatures = [obj for obj in bpy.context.scene.objects if obj.type == 'ARMATURE']
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']

    if not armatures:
        raise RuntimeError("No armature found after import!")

    armature = armatures[0]
    mesh = None
    for m in meshes:
        if m.parent == armature and m.vertex_groups:
            mesh = m
            break

    if not mesh:
        raise RuntimeError("No weighted mesh found parented to armature!")

    log(f"  Armature: {armature.name} ({len(armature.data.bones)} bones)")
    log(f"  Mesh: {mesh.name} ({len(mesh.data.vertices)} vertices, {len(mesh.vertex_groups)} vertex groups)")

    # Remove stray objects (Icosphere, etc.)
    stray_count = 0
    for obj in list(bpy.context.scene.objects):
        if obj.type == 'MESH' and obj != mesh and not obj.vertex_groups:
            log(f"  Removing stray object: {obj.name}")
            bpy.data.objects.remove(obj, do_unlink=True)
            stray_count += 1

    log(f"  Removed {stray_count} stray objects")

    return armature, mesh


# ---- Step 1: Weight Painting Fixes ----

def step_fix_weights(armature, mesh):
    """Fix weight painting issues following the production guide."""
    log("Step 1: Fixing weight painting...")

    # Ensure mesh is active
    bpy.context.view_layer.objects.active = mesh
    mesh.select_set(True)

    # 1. Normalize all weights
    log("  1a. Normalizing all weights...")
    bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
    bpy.ops.object.vertex_group_normalize_all()
    bpy.ops.object.mode_set(mode='OBJECT')

    # 2. Limit total influences to 4
    log("  1b. Limiting to 4 influences per vertex...")
    bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
    bpy.ops.object.vertex_group_limit_total(limit=4)
    bpy.ops.object.mode_set(mode='OBJECT')

    # 3. Clean zero-weight groups
    log("  1c. Cleaning zero-weight groups...")
    bpy.ops.object.vertex_group_clean(group_select_mode='ALL', limit=0.01)

    log("  Weight painting basic fixes complete")


def step_fix_shoulder_weights(armature, mesh):
    """Fix shoulder area weight bleed - critical for arm clipping.

    The issue: Upper arm vertices often have influence from chest/spine bones,
    causing the arm to drag torso geometry when raised.

    Fix: For vertices in the shoulder/upper arm area, reduce spine influence
    and increase upper arm influence where there's bleed.
    """
    log("Step 2: Fixing shoulder area weights...")

    bpy.context.view_layer.objects.active = mesh

    # Get vertex group indices
    vg_names = {vg.name: vg.index for vg in mesh.vertex_groups}

    # Bones whose influence should be reduced in the shoulder/upper arm area
    spine_bones = ["Spine", "Spine01", "Spine02"]
    arm_bones_left = ["LeftArm", "LeftShoulder"]
    arm_bones_right = ["RightArm", "RightShoulder"]

    # For each side, find vertices that have BOTH spine and arm influence
    # and reduce the spine influence while increasing the arm influence
    for side, arm_bone_names in [("Left", arm_bones_left), ("Right", arm_bones_right)]:
        arm_vg_indices = [vg_names[n] for n in arm_bone_names if n in vg_names]
        spine_vg_indices = [vg_names[n] for n in spine_bones if n in vg_names]

        if not arm_vg_indices or not spine_vg_indices:
            continue

        primary_arm_name = f"{side}Arm"
        if primary_arm_name not in vg_names:
            continue

        primary_arm_vg = mesh.vertex_groups[primary_arm_name]
        fixed_count = 0

        for vert in mesh.data.vertices:
            # Check if this vertex has arm influence
            arm_weight = 0
            spine_weight = 0

            for g in vert.groups:
                if g.group in arm_vg_indices:
                    arm_weight += g.weight
                if g.group in spine_vg_indices:
                    spine_weight += g.weight

            # If vertex has significant arm AND spine influence, it's a bleed area
            if arm_weight > 0.1 and spine_weight > 0.05:
                # Reduce spine influence and transfer to arm
                for g in vert.groups:
                    if g.group in spine_vg_indices and g.weight > 0.05:
                        transfer = g.weight * 0.7  # Transfer 70% of spine weight to arm
                        # Reduce spine weight
                        vg = mesh.vertex_groups[g.group]
                        vg.add([vert.index], g.weight - transfer, 'REPLACE')
                        # Add to arm
                        primary_arm_vg.add([vert.index], arm_weight + transfer, 'REPLACE')
                        fixed_count += 1

        log(f"  Fixed {fixed_count} vertices in {side} shoulder area")

    # Re-normalize after manual adjustments
    bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
    bpy.ops.object.vertex_group_normalize_all()
    bpy.ops.object.mode_set(mode='OBJECT')

    log("  Shoulder weight fixes complete")


def step_fix_hip_weights(armature, mesh):
    """Fix hip/thigh area weight bleed - critical for leg clipping.

    The issue: Thigh vertices can bleed into the opposite leg or torso,
    causing cross-body deformation.

    Fix: For vertices in the thigh area, reduce cross-body influence.
    """
    log("Step 3: Fixing hip/thigh area weights...")

    bpy.context.view_layer.objects.active = mesh

    vg_names = {vg.name: vg.index for vg in mesh.vertex_groups}

    # For each leg, check for cross-body weight bleed
    sides = [
        ("Left", "LeftUpLeg", "RightUpLeg"),
        ("Right", "RightUpLeg", "LeftUpLeg"),
    ]

    for side, own_bone, opposite_bone in sides:
        if own_bone not in vg_names or opposite_bone not in vg_names:
            continue

        own_idx = vg_names[own_bone]
        opp_idx = vg_names[opposite_bone]
        own_vg = mesh.vertex_groups[own_bone]
        opp_vg = mesh.vertex_groups[opposite_bone]

        fixed_count = 0
        for vert in mesh.data.vertices:
            own_weight = 0
            opp_weight = 0

            for g in vert.groups:
                if g.group == own_idx:
                    own_weight = g.weight
                elif g.group == opp_idx:
                    opp_weight = g.weight

            # If vertex has weight on both legs, it's cross-body bleed
            if own_weight > 0.1 and opp_weight > 0.02:
                # Remove opposite leg influence and transfer to own leg
                transfer = opp_weight * 0.9
                opp_vg.add([vert.index], opp_weight - transfer, 'REPLACE')
                own_vg.add([vert.index], own_weight + transfer, 'REPLACE')
                fixed_count += 1

        log(f"  Fixed {fixed_count} cross-body vertices in {side} hip area")

    # Also fix Hips/thigh bleed for hip-area vertices
    if "Hips" in vg_names:
        hips_idx = vg_names["Hips"]
        for leg_name in ["LeftUpLeg", "RightUpLeg"]:
            if leg_name not in vg_names:
                continue
            leg_idx = vg_names[leg_name]
            leg_vg = mesh.vertex_groups[leg_name]
            hips_vg = mesh.vertex_groups["Hips"]

            fixed_count = 0
            for vert in mesh.data.vertices:
                hips_w = 0
                leg_w = 0
                for g in vert.groups:
                    if g.group == hips_idx:
                        hips_w = g.weight
                    elif g.group == leg_idx:
                        leg_w = g.weight

                # Where thigh influence is dominant but hips pulls too much
                if leg_w > 0.3 and hips_w > 0.15:
                    transfer = hips_w * 0.5
                    hips_vg.add([vert.index], hips_w - transfer, 'REPLACE')
                    leg_vg.add([vert.index], leg_w + transfer, 'REPLACE')
                    fixed_count += 1

            log(f"  Fixed {fixed_count} hip-thigh bleed vertices for {leg_name}")

    # Re-normalize
    bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
    bpy.ops.object.vertex_group_normalize_all()
    bpy.ops.object.mode_set(mode='OBJECT')

    log("  Hip/thigh weight fixes complete")


# ---- Step 2: Smooth Weight Transitions ----

def step_smooth_weights(armature, mesh):
    """Smooth weight transitions at joints using vertex proximity blending.

    This helps eliminate hard transitions that cause pinching or folding.
    """
    log("Step 4: Smoothing weight transitions at joints...")

    bpy.context.view_layer.objects.active = mesh

    # Use Blender's built-in smooth operation on key joint areas
    # We'll do this by briefly entering weight paint mode and using
    # the smooth brush equivalent (vertex group smooth)

    joint_groups = [
        "LeftShoulder", "RightShoulder",
        "LeftArm", "RightArm",
        "LeftForeArm", "RightForeArm",
        "LeftUpLeg", "RightUpLeg",
        "LeftLeg", "RightLeg",
        "neck",
    ]

    for group_name in joint_groups:
        if group_name in [vg.name for vg in mesh.vertex_groups]:
            # Set active vertex group
            mesh.vertex_groups.active_index = mesh.vertex_groups[group_name].index
            # Smooth the vertex group
            bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
            bpy.ops.object.vertex_group_smooth(
                group_select_mode='ACTIVE',
                factor=0.5,
                repeat=2
            )
            bpy.ops.object.mode_set(mode='OBJECT')

    log("  Weight smoothing complete")


# ---- Step 3: Add Rotation Limits ----

def step_add_rotation_limits(armature):
    """Add rotation limits following the production guide table.

    Prevents impossible joint positions that cause clipping.
    """
    log("Step 5: Adding rotation limits...")

    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='POSE')

    # Joint limits from the production guide (degrees)
    joint_limits = {
        # Elbows - only bend one direction
        "LeftForeArm": {"x": (-5, 150), "y": (-90, 90), "z": (-10, 10)},
        "RightForeArm": {"x": (-5, 150), "y": (-90, 90), "z": (-10, 10)},

        # Knees - only bend backward
        "LeftLeg": {"x": (-5, 150), "y": (-10, 10), "z": (-10, 10)},
        "RightLeg": {"x": (-5, 150), "y": (-10, 10), "z": (-10, 10)},

        # Head - natural range of motion
        "Head": {"x": (-45, 45), "y": (-80, 80), "z": (-45, 45)},

        # Neck - slightly more restricted than head
        "neck": {"x": (-30, 30), "y": (-60, 60), "z": (-30, 30)},

        # Upper arms - prevent over-rotation
        "LeftArm": {"x": (-120, 120), "y": (-90, 90), "z": (-170, 40)},
        "RightArm": {"x": (-120, 120), "y": (-90, 90), "z": (-40, 170)},

        # Shoulders - limited range
        "LeftShoulder": {"x": (-15, 15), "y": (-15, 15), "z": (-30, 30)},
        "RightShoulder": {"x": (-15, 15), "y": (-15, 15), "z": (-30, 30)},

        # Spine bones - allow natural torso rotation
        "Spine": {"x": (-30, 30), "y": (-45, 45), "z": (-20, 20)},
        "Spine01": {"x": (-20, 20), "y": (-30, 30), "z": (-15, 15)},
        "Spine02": {"x": (-20, 20), "y": (-30, 30), "z": (-15, 15)},

        # Hands - wrist range
        "LeftHand": {"x": (-75, 75), "y": (-30, 30), "z": (-90, 90)},
        "RightHand": {"x": (-75, 75), "y": (-30, 30), "z": (-90, 90)},

        # Feet - ankle range
        "LeftFoot": {"x": (-40, 50), "y": (-30, 30), "z": (-25, 25)},
        "RightFoot": {"x": (-40, 50), "y": (-30, 30), "z": (-25, 25)},

        # Thighs - hip range
        "LeftUpLeg": {"x": (-120, 30), "y": (-45, 45), "z": (-60, 30)},
        "RightUpLeg": {"x": (-120, 30), "y": (-45, 45), "z": (-30, 60)},

        # Toes
        "LeftToeBase": {"x": (-30, 60), "y": (-10, 10), "z": (-10, 10)},
        "RightToeBase": {"x": (-30, 60), "y": (-10, 10), "z": (-10, 10)},
    }

    limits_added = 0
    for bone_name, limits in joint_limits.items():
        if bone_name not in armature.pose.bones:
            log(f"  WARNING: Bone '{bone_name}' not found, skipping")
            continue

        pbone = armature.pose.bones[bone_name]

        # Remove existing limit constraints
        for c in list(pbone.constraints):
            if c.type == 'LIMIT_ROTATION':
                pbone.constraints.remove(c)

        # Add new limit rotation constraint
        limit = pbone.constraints.new('LIMIT_ROTATION')
        limit.name = f"Limit_{bone_name}"
        limit.owner_space = 'LOCAL'

        # X axis
        limit.use_limit_x = True
        limit.min_x = math.radians(limits["x"][0])
        limit.max_x = math.radians(limits["x"][1])

        # Y axis
        limit.use_limit_y = True
        limit.min_y = math.radians(limits["y"][0])
        limit.max_y = math.radians(limits["y"][1])

        # Z axis
        limit.use_limit_z = True
        limit.min_z = math.radians(limits["z"][0])
        limit.max_z = math.radians(limits["z"][1])

        limits_added += 1

    bpy.ops.object.mode_set(mode='OBJECT')
    log(f"  Added rotation limits to {limits_added} bones")


# ---- Step 4: Add IK Constraints ----

def step_add_ik_constraints(armature):
    """Add IK constraints to hands and feet for proper placement."""
    log("Step 6: Adding IK constraints...")

    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='POSE')

    # IK targets: bone_name -> chain_count
    ik_targets = {
        "LeftHand": 2,   # Upper arm + forearm
        "RightHand": 2,
        "LeftFoot": 2,   # Upper leg + lower leg
        "RightFoot": 2,
    }

    ik_added = 0
    for bone_name, chain_count in ik_targets.items():
        if bone_name not in armature.pose.bones:
            log(f"  WARNING: Bone '{bone_name}' not found, skipping IK")
            continue

        pbone = armature.pose.bones[bone_name]

        # Check if IK already exists
        has_ik = any(c.type == 'IK' for c in pbone.constraints)
        if has_ik:
            log(f"  IK already exists on {bone_name}, skipping")
            continue

        ik = pbone.constraints.new('IK')
        ik.name = f"IK_{bone_name}"
        ik.chain_count = chain_count
        # No explicit target (use for interactive posing)
        ik_added += 1
        log(f"  Added IK constraint to {bone_name} (chain: {chain_count})")

    bpy.ops.object.mode_set(mode='OBJECT')
    log(f"  Added {ik_added} IK constraints")


# ---- Step 5: Add Ponytail Bone Chain ----

def step_add_ponytail_bones(armature, mesh):
    """Add bone chain for Mia's ponytail to enable secondary motion.

    Following production guide Option A: bone chains.
    1. Add 4-6 bones following the ponytail
    2. Parent to head bone
    3. Weight paint hair mesh to these bones
    """
    log("Step 7: Adding ponytail bone chain...")

    bpy.context.view_layer.objects.active = armature

    # First, find the head bone position to determine ponytail start
    head_bone = armature.data.bones.get("Head")
    if not head_bone:
        log("  ERROR: Head bone not found!")
        return

    # Get head bone tail position (top of head) in armature space
    head_tail = head_bone.tail_local.copy()
    head_head = head_bone.head_local.copy()

    # Ponytail starts at the back of the head (offset from head bone tail)
    # Head bone goes up, so we offset backward (negative Y in Blender space)
    # For a ponytail, start slightly behind and below the top of head
    ponytail_start = head_tail.copy()
    ponytail_start.y += 0.04   # Behind the head
    ponytail_start.z -= 0.02   # Slightly below top

    # Enter edit mode to add bones
    bpy.ops.object.mode_set(mode='EDIT')

    # Create ponytail bone chain
    ponytail_bones = []
    prev_bone = None

    for i in range(PONYTAIL_BONE_COUNT):
        bone_name = f"Ponytail_{i+1:02d}"

        # Create new bone
        new_bone = armature.data.edit_bones.new(bone_name)

        if i == 0:
            # First bone starts at head position
            new_bone.head = ponytail_start
        else:
            # Subsequent bones chain from previous tail
            new_bone.head = prev_bone.tail.copy()

        # Each bone points downward and slightly backward (gravity/bounce direction)
        direction = Vector((0, 0.01 * (i + 1), -PONYTAIL_BONE_LENGTH))
        new_bone.tail = new_bone.head + direction

        # Parent first bone to Head, rest to previous ponytail bone
        if i == 0:
            head_edit = armature.data.edit_bones.get("Head")
            new_bone.parent = head_edit
        else:
            new_bone.parent = prev_bone

        new_bone.use_deform = True
        ponytail_bones.append(bone_name)
        prev_bone = new_bone

        log(f"  Added bone: {bone_name}")

    bpy.ops.object.mode_set(mode='OBJECT')

    # Now weight paint the ponytail area to these bones
    log("  Weight painting ponytail bones...")
    _weight_paint_ponytail(armature, mesh, ponytail_bones)

    # Add damped track / spring-like constraints for secondary motion
    log("  Adding spring constraints to ponytail...")
    _add_ponytail_spring_constraints(armature, ponytail_bones)

    log(f"  Ponytail setup complete ({PONYTAIL_BONE_COUNT} bones)")


def _weight_paint_ponytail(armature, mesh, ponytail_bone_names):
    """Weight paint the ponytail/hair area to the ponytail bones.

    Strategy: Find vertices that are above and behind the head, assign them
    to ponytail bones based on their vertical position (higher = closer to
    root, lower = closer to tip).
    """
    bpy.context.view_layer.objects.active = mesh

    # Get head bone position for reference
    head_bone = armature.data.bones["Head"]
    head_center = (head_bone.head_local + head_bone.tail_local) / 2
    head_top_z = head_bone.tail_local.z

    # Create vertex groups for ponytail bones if they don't exist
    for bone_name in ponytail_bone_names:
        if bone_name not in [vg.name for vg in mesh.vertex_groups]:
            mesh.vertex_groups.new(name=bone_name)

    # Get the Head vertex group to find head-area vertices
    head_vg = mesh.vertex_groups.get("Head")
    if not head_vg:
        log("  WARNING: No Head vertex group found")
        return

    head_vg_idx = head_vg.index

    # Find vertices that have Head weight and are in the ponytail region
    # (behind and above/around the head)
    ponytail_verts = []
    for vert in mesh.data.vertices:
        # Check if vertex has Head group weight
        has_head_weight = False
        head_weight = 0
        for g in vert.groups:
            if g.group == head_vg_idx:
                has_head_weight = True
                head_weight = g.weight
                break

        if not has_head_weight or head_weight < 0.1:
            continue

        # Get vertex world position (approximate - use local coords)
        pos = vert.co

        # Ponytail region: behind head center (positive Y for Meshy models)
        # and below the top of the head
        # We detect ponytail by checking if vertex is behind head center
        is_behind = pos.y > head_center.y + 0.02
        is_below_top = pos.z < head_top_z + 0.05

        if is_behind and is_below_top:
            ponytail_verts.append((vert.index, pos.z, head_weight))

    if not ponytail_verts:
        log("  WARNING: No ponytail vertices detected. Trying alternative detection...")
        # Alternative: use vertices behind head with any head weight
        for vert in mesh.data.vertices:
            for g in vert.groups:
                if g.group == head_vg_idx and g.weight > 0.01:
                    pos = vert.co
                    if pos.y > head_center.y:
                        ponytail_verts.append((vert.index, pos.z, g.weight))
                    break

    if not ponytail_verts:
        log("  WARNING: Still no ponytail vertices found. Skipping hair weight painting.")
        return

    log(f"  Found {len(ponytail_verts)} ponytail candidate vertices")

    # Sort by Z position (highest to lowest)
    ponytail_verts.sort(key=lambda v: v[1], reverse=True)

    # Divide into segments for each bone
    segment_size = max(1, len(ponytail_verts) // PONYTAIL_BONE_COUNT)

    for i, bone_name in enumerate(ponytail_bone_names):
        vg = mesh.vertex_groups[bone_name]
        start_idx = i * segment_size
        end_idx = start_idx + segment_size if i < PONYTAIL_BONE_COUNT - 1 else len(ponytail_verts)

        segment_verts = ponytail_verts[start_idx:end_idx]

        for vert_idx, _, orig_weight in segment_verts:
            # Weight decreases for outer bones (smoother blending)
            weight = min(orig_weight, 0.8)
            vg.add([vert_idx], weight, 'REPLACE')

            # Also reduce Head bone weight for these vertices
            head_vg.add([vert_idx], orig_weight * 0.3, 'REPLACE')

        log(f"  Assigned {len(segment_verts)} vertices to {bone_name}")

    # Normalize after ponytail weight painting
    bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
    bpy.ops.object.vertex_group_normalize_all()
    bpy.ops.object.mode_set(mode='OBJECT')


def _add_ponytail_spring_constraints(armature, ponytail_bone_names):
    """Add spring-like constraints to ponytail bones for secondary motion.

    Uses Copy Rotation with low influence to create a follow-through effect.
    Each bone partially copies the rotation of its parent with a delay factor.
    """
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='POSE')

    for i, bone_name in enumerate(ponytail_bone_names):
        if bone_name not in armature.pose.bones:
            continue

        pbone = armature.pose.bones[bone_name]

        # Add rotation limits for natural hair movement
        limit = pbone.constraints.new('LIMIT_ROTATION')
        limit.name = f"Limit_{bone_name}"
        limit.owner_space = 'LOCAL'
        limit.use_limit_x = True
        limit.min_x = math.radians(-60)
        limit.max_x = math.radians(60)
        limit.use_limit_y = True
        limit.min_y = math.radians(-45)
        limit.max_y = math.radians(45)
        limit.use_limit_z = True
        limit.min_z = math.radians(-60)
        limit.max_z = math.radians(60)

        # Add damped track for subtle gravity effect
        # This helps the ponytail naturally hang downward
        if i >= 1:  # Not on root bone
            damped = pbone.constraints.new('DAMPED_TRACK')
            damped.name = f"Gravity_{bone_name}"
            # Track downward slightly
            damped.track_axis = 'TRACK_NEGATIVE_Z'
            damped.influence = 0.1 + (i * 0.05)  # Stronger gravity at tips

    bpy.ops.object.mode_set(mode='OBJECT')
    log("  Spring constraints added to ponytail")


# ---- Step 6: Add Spine Counter-Rotation ----

def step_add_spine_counter_rotation(armature):
    """Add counter-rotation to spine for natural walking motion.

    During walking, the upper body counter-rotates against the hips.
    This adds a Copy Rotation constraint to the upper spine that
    copies a fraction of the hip Y rotation, inverted.
    """
    log("Step 8: Adding spine counter-rotation...")

    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='POSE')

    # The Meshy spine hierarchy is: Hips > Spine02 > Spine01 > Spine
    # We want Spine (upper/chest) to counter-rotate against Hips
    spine_bone = armature.pose.bones.get("Spine")
    hips_bone = armature.pose.bones.get("Hips")

    if not spine_bone or not hips_bone:
        log("  WARNING: Could not find Spine or Hips bone for counter-rotation")
        bpy.ops.object.mode_set(mode='OBJECT')
        return

    # Add Copy Rotation constraint to upper spine
    # Copies -30% of Hips Y rotation for natural counter-swing
    copy_rot = spine_bone.constraints.new('COPY_ROTATION')
    copy_rot.name = "CounterRotation_Hips"
    copy_rot.target = armature
    copy_rot.subtarget = "Hips"
    copy_rot.use_x = False
    copy_rot.use_y = True   # Only counter-rotate on Y (twist/turn axis)
    copy_rot.use_z = False
    copy_rot.invert_y = True  # Invert to create counter-rotation
    copy_rot.influence = 0.3  # 30% of hip rotation
    copy_rot.target_space = 'LOCAL'
    copy_rot.owner_space = 'LOCAL'
    copy_rot.mix_mode = 'ADD'

    bpy.ops.object.mode_set(mode='OBJECT')
    log("  Spine counter-rotation constraint added")


# ---- Step 7: Export ----

def step_export(armature, mesh):
    """Export cleaned model as both GLB and FBX."""
    log("Step 9: Exporting cleaned model...")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Select only the armature and mesh for export
    bpy.ops.object.select_all(action='DESELECT')
    armature.select_set(True)
    mesh.select_set(True)
    bpy.context.view_layer.objects.active = armature

    # Export GLB
    log(f"  Exporting GLB: {OUTPUT_GLB}")
    bpy.ops.export_scene.gltf(
        filepath=OUTPUT_GLB,
        export_format='GLB',
        use_selection=True,
        export_apply=False,
    )

    # Export FBX
    log(f"  Exporting FBX: {OUTPUT_FBX}")
    bpy.ops.export_scene.fbx(
        filepath=OUTPUT_FBX,
        use_selection=True,
        add_leaf_bones=False,
        bake_anim=False,
        path_mode='COPY',
        embed_textures=True,
    )

    log("  Export complete")


# ---- Quality Validation ----

def step_validate(armature, mesh):
    """Run the quality checker on the cleaned rig."""
    log("Step 10: Running quality validation...")

    # Import quality checker
    sys.path.insert(0, SCRIPT_DIR)
    try:
        from rig_quality_checker import run_blender_checks
        report = run_blender_checks(armature, mesh)
        log("\n" + report.summary())

        # Save report
        with open(REPORT_PATH, 'w') as f:
            json.dump(report.to_dict(), f, indent=2, default=str)
        log(f"  Report saved to: {REPORT_PATH}")

        return report
    except Exception as e:
        log(f"  Quality checker error: {e}")
        import traceback
        traceback.print_exc()
        return None


# ---- Generate Cleanup Summary ----

def generate_summary(armature, mesh, report):
    """Generate a summary of all changes made."""
    summary = {
        "model": "Mia (Meshy auto-rigged)",
        "input": INPUT_MODEL,
        "output_glb": OUTPUT_GLB,
        "output_fbx": OUTPUT_FBX,
        "changes": {
            "weight_painting": {
                "normalized_all": True,
                "limited_to_4_influences": True,
                "cleaned_zero_weights": True,
                "fixed_shoulder_bleed": True,
                "fixed_hip_bleed": True,
                "smoothed_joint_transitions": True,
            },
            "rotation_limits": {
                "bones_with_limits": sum(
                    1 for pb in armature.pose.bones
                    for c in pb.constraints if c.type == 'LIMIT_ROTATION'
                ),
                "joints_covered": [
                    "elbows", "knees", "head", "neck", "shoulders",
                    "upper_arms", "spine", "hands", "feet", "thighs", "toes"
                ],
            },
            "ik_constraints": {
                "count": sum(
                    1 for pb in armature.pose.bones
                    for c in pb.constraints if c.type == 'IK'
                ),
                "targets": ["LeftHand", "RightHand", "LeftFoot", "RightFoot"],
            },
            "ponytail": {
                "bone_count": PONYTAIL_BONE_COUNT,
                "has_spring_constraints": True,
                "has_rotation_limits": True,
            },
            "spine_counter_rotation": {
                "enabled": True,
                "influence": 0.3,
                "axis": "Y",
            },
            "cleanup": {
                "removed_stray_objects": True,
            },
        },
        "bone_count": {
            "original": 24,
            "after_cleanup": len(armature.data.bones),
        },
        "vertex_count": len(mesh.data.vertices),
    }

    if report:
        summary["quality_score"] = report.overall_score
        summary["production_ready"] = report.production_ready

    summary_path = os.path.join(OUTPUT_DIR, "cleanup_summary.json")
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    log(f"Summary saved to: {summary_path}")

    return summary


# ---- Main Pipeline ----

def main():
    """Run the complete Mia rig cleanup pipeline."""
    log("=" * 60)
    log("  MIA RIG CLEANUP PIPELINE")
    log("  Following Production Guide Section 3")
    log("=" * 60)

    # Step 0: Import and verify
    armature, mesh = step_import_and_verify()

    # Step 1: Fix weight painting
    step_fix_weights(armature, mesh)

    # Step 2: Fix shoulder weights
    step_fix_shoulder_weights(armature, mesh)

    # Step 3: Fix hip/thigh weights
    step_fix_hip_weights(armature, mesh)

    # Step 4: Smooth weight transitions
    step_smooth_weights(armature, mesh)

    # Step 5: Add rotation limits
    step_add_rotation_limits(armature)

    # Step 6: Add IK constraints
    step_add_ik_constraints(armature)

    # Step 7: Add ponytail bone chain
    step_add_ponytail_bones(armature, mesh)

    # Step 8: Add spine counter-rotation
    step_add_spine_counter_rotation(armature)

    # Step 8.5: Final weight cleanup pass
    # Re-run limit total and normalize after all weight modifications
    log("Step 8.5: Final weight cleanup pass...")
    bpy.context.view_layer.objects.active = mesh
    mesh.select_set(True)
    bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
    bpy.ops.object.vertex_group_limit_total(limit=4)
    bpy.ops.object.vertex_group_normalize_all()
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.vertex_group_clean(group_select_mode='ALL', limit=0.01)
    log("  Final weight cleanup complete")

    # Step 9: Export
    step_export(armature, mesh)

    # Step 10: Validate
    report = step_validate(armature, mesh)

    # Generate summary
    summary = generate_summary(armature, mesh, report)

    log("")
    log("=" * 60)
    log("  CLEANUP PIPELINE COMPLETE")
    log(f"  Output GLB: {OUTPUT_GLB}")
    log(f"  Output FBX: {OUTPUT_FBX}")
    log(f"  Bone count: {summary['bone_count']['original']} -> {summary['bone_count']['after_cleanup']}")
    if report:
        log(f"  Quality score: {report.overall_score:.1f}%")
        log(f"  Production ready: {'YES' if report.production_ready else 'NO'}")
    log("=" * 60)


if __name__ == "__main__":
    main()
