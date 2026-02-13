"""
Fix Mia's character rig:
1. Add arm rotation limits to prevent leg clipping
2. Set up spine counter-rotation for natural walk motion
3. Add ponytail bone chain with secondary motion constraints
4. Clean up stray objects

Run with: xvfb-run blender --background --python scripts/fix_mia_rig.py
"""
import bpy
import bmesh
import math
import mathutils
import json
import os
import sys

# ============================================================
# CONFIGURATION
# ============================================================

INPUT_GLB = "tmp/mia_rigged.glb"
OUTPUT_GLB = "tmp/mia_rigged_v2.glb"

# Arm rotation limits (in degrees) - prevents arm-leg clipping
# These are in bone-local space
ARM_LIMITS = {
    # Upper arm: limit backward swing to prevent thigh clipping
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
    # Forearm: limit to natural elbow bend range
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

# Ponytail configuration
PONYTAIL_SEGMENTS = 4
PONYTAIL_SEGMENT_LENGTH = 6.0  # in armature space units (character is ~120 units tall)

# Spine counter-rotation influence (how much upper spine opposes hip twist)
SPINE_COUNTER_ROTATION_INFLUENCE = 0.35


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def log(msg):
    print(f"[FIX_RIG] {msg}")


def find_armature():
    for obj in bpy.data.objects:
        if obj.type == 'ARMATURE':
            return obj
    return None


def find_main_mesh():
    for obj in bpy.data.objects:
        if obj.type == 'MESH' and len(obj.data.vertices) > 100:
            return obj
    return None


def ensure_mode(obj, mode):
    bpy.context.view_layer.objects.active = obj
    if obj.mode != mode:
        bpy.ops.object.mode_set(mode=mode)


# ============================================================
# STEP 1: IMPORT AND CLEAN UP
# ============================================================

def import_and_cleanup():
    log("Step 1: Importing GLB and cleaning up...")

    # Clear default scene
    bpy.ops.wm.read_factory_settings(use_empty=True)

    # Import GLB
    bpy.ops.import_scene.gltf(filepath=INPUT_GLB)
    log(f"  Imported {INPUT_GLB}")

    # Remove stray objects (like the Icosphere)
    removed = []
    for obj in list(bpy.data.objects):
        if obj.type == 'MESH' and len(obj.data.vertices) < 100 and not obj.vertex_groups:
            name = obj.name
            bpy.data.objects.remove(obj, do_unlink=True)
            removed.append(name)

    if removed:
        log(f"  Removed stray objects: {removed}")

    armature = find_armature()
    mesh = find_main_mesh()

    if not armature:
        log("ERROR: No armature found after import!")
        sys.exit(1)
    if not mesh:
        log("ERROR: No mesh found after import!")
        sys.exit(1)

    log(f"  Armature: {armature.name}")
    log(f"  Mesh: {mesh.name} ({len(mesh.data.vertices)} verts)")

    return armature, mesh


# ============================================================
# STEP 2: ARM ROTATION LIMITS (Anti-Clipping)
# ============================================================

def add_arm_rotation_limits(armature):
    log("Step 2: Adding arm rotation limits...")

    ensure_mode(armature, 'POSE')

    for bone_name, limits in ARM_LIMITS.items():
        pbone = armature.pose.bones.get(bone_name)
        if not pbone:
            log(f"  WARNING: Bone '{bone_name}' not found, skipping")
            continue

        # Remove existing limit rotation constraints if any
        for c in list(pbone.constraints):
            if c.type == 'LIMIT_ROTATION':
                pbone.constraints.remove(c)

        # Add LIMIT_ROTATION constraint
        constraint = pbone.constraints.new('LIMIT_ROTATION')
        constraint.name = f"Limit_{bone_name}"
        constraint.owner_space = 'LOCAL'

        # Apply limits
        constraint.use_limit_x = limits.get("use_limit_x", False)
        constraint.min_x = limits.get("min_x", 0)
        constraint.max_x = limits.get("max_x", 0)

        constraint.use_limit_y = limits.get("use_limit_y", False)
        constraint.min_y = limits.get("min_y", 0)
        constraint.max_y = limits.get("max_y", 0)

        constraint.use_limit_z = limits.get("use_limit_z", False)
        constraint.min_z = limits.get("min_z", 0)
        constraint.max_z = limits.get("max_z", 0)

        log(f"  Added rotation limits on {bone_name}")
        log(f"    X: [{math.degrees(limits.get('min_x', 0)):.0f}°, {math.degrees(limits.get('max_x', 0)):.0f}°]")
        log(f"    Y: [{math.degrees(limits.get('min_y', 0)):.0f}°, {math.degrees(limits.get('max_y', 0)):.0f}°]")
        log(f"    Z: [{math.degrees(limits.get('min_z', 0)):.0f}°, {math.degrees(limits.get('max_z', 0)):.0f}°]")

    # Also add limits to shoulder bones to prevent extreme poses
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
            log(f"  Added rotation limits on {shoulder_name}")

    ensure_mode(armature, 'OBJECT')
    log("  Arm rotation limits complete.")


# ============================================================
# STEP 3: SPINE COUNTER-ROTATION
# ============================================================

def setup_spine_counter_rotation(armature):
    log("Step 3: Setting up spine counter-rotation...")

    ensure_mode(armature, 'POSE')

    # The spine chain is: Hips -> Spine02 -> Spine01 -> Spine
    # For natural walking, the upper spine (Spine) should counter-rotate
    # against the hips on the Z axis (twist/yaw)

    spine_bone = armature.pose.bones.get("Spine")
    hips_bone = armature.pose.bones.get("Hips")

    if not spine_bone or not hips_bone:
        log("  WARNING: Spine or Hips bone not found!")
        ensure_mode(armature, 'OBJECT')
        return

    # Add COPY_ROTATION constraint on upper Spine targeting Hips
    # with inverted Y axis (the twist axis in this rig's orientation)
    # and reduced influence for subtle counter-rotation
    constraint = spine_bone.constraints.new('COPY_ROTATION')
    constraint.name = "Spine_CounterRotation"
    constraint.target = armature
    constraint.subtarget = "Hips"

    # Only copy Z rotation (twist axis) with inversion
    constraint.use_x = False
    constraint.use_y = True
    constraint.use_z = True
    constraint.invert_y = True
    constraint.invert_z = True

    constraint.target_space = 'LOCAL'
    constraint.owner_space = 'LOCAL'
    constraint.influence = SPINE_COUNTER_ROTATION_INFLUENCE
    constraint.mix_mode = 'ADD'

    log(f"  Added counter-rotation on Spine (influence={SPINE_COUNTER_ROTATION_INFLUENCE})")

    # Also add slight counter-rotation to Spine01 for smoother transition
    spine01_bone = armature.pose.bones.get("Spine01")
    if spine01_bone:
        constraint2 = spine01_bone.constraints.new('COPY_ROTATION')
        constraint2.name = "Spine01_CounterRotation"
        constraint2.target = armature
        constraint2.subtarget = "Hips"
        constraint2.use_x = False
        constraint2.use_y = True
        constraint2.use_z = True
        constraint2.invert_y = True
        constraint2.invert_z = True
        constraint2.target_space = 'LOCAL'
        constraint2.owner_space = 'LOCAL'
        constraint2.influence = SPINE_COUNTER_ROTATION_INFLUENCE * 0.5
        constraint2.mix_mode = 'ADD'
        log(f"  Added counter-rotation on Spine01 (influence={SPINE_COUNTER_ROTATION_INFLUENCE * 0.5:.2f})")

    ensure_mode(armature, 'OBJECT')
    log("  Spine counter-rotation complete.")


# ============================================================
# STEP 4: PONYTAIL BONE CHAIN WITH SECONDARY MOTION
# ============================================================

def add_ponytail_bones(armature, mesh):
    log("Step 4: Adding ponytail bone chain...")

    ensure_mode(armature, 'EDIT')

    edit_bones = armature.data.edit_bones

    # Find the Head bone to parent the ponytail chain to
    head_bone = edit_bones.get("Head")
    if not head_bone:
        log("  WARNING: Head bone not found!")
        ensure_mode(armature, 'OBJECT')
        return

    # The ponytail starts at the back-top of the head and goes backward/downward
    # Head bone head position gives us the base of the skull area
    # head_end bone position gives us the top of the head
    head_end_bone = edit_bones.get("head_end")

    # Calculate ponytail start position:
    # Slightly behind and above the head bone head position
    # The head bone head is at approximately [0, -6.6, 78.5] in armature space
    # We want the ponytail to start at the back of the head, going backward (+Y) and slightly down (-Z)
    head_pos = head_bone.head.copy()

    # Ponytail base: behind the head (positive Y direction in this rig), at skull height
    ponytail_start = mathutils.Vector((
        head_pos.x,                    # centered
        head_pos.y + 10.0,             # behind the head
        head_pos.z + 35.0              # above the center, near top of skull
    ))

    # Direction: backward and downward
    ponytail_dir = mathutils.Vector((0.0, 1.0, -0.8)).normalized()

    log(f"  Ponytail start: [{ponytail_start.x:.1f}, {ponytail_start.y:.1f}, {ponytail_start.z:.1f}]")
    log(f"  Direction: [{ponytail_dir.x:.2f}, {ponytail_dir.y:.2f}, {ponytail_dir.z:.2f}]")

    # Create ponytail bone chain
    prev_bone = None
    ponytail_bone_names = []

    for i in range(PONYTAIL_SEGMENTS):
        bone_name = f"Ponytail_{i+1:02d}"
        ponytail_bone_names.append(bone_name)

        # Remove if exists (for re-running)
        if bone_name in edit_bones:
            edit_bones.remove(edit_bones[bone_name])

        new_bone = edit_bones.new(bone_name)

        # Calculate positions along the chain
        # Each segment gets slightly longer (hair spreads out)
        seg_length = PONYTAIL_SEGMENT_LENGTH * (1.0 + i * 0.15)
        seg_start = ponytail_start + ponytail_dir * (sum(PONYTAIL_SEGMENT_LENGTH * (1.0 + j * 0.15) for j in range(i)))
        seg_end = seg_start + ponytail_dir * seg_length

        # Gravity effect: each subsequent bone droops more
        gravity_offset = mathutils.Vector((0, 0, -1.5 * (i + 1)))
        seg_end = seg_end + gravity_offset

        new_bone.head = seg_start
        new_bone.tail = seg_end

        # Parent chain
        if prev_bone:
            new_bone.parent = prev_bone
            new_bone.use_connect = True
        else:
            # First segment parents to Head bone
            new_bone.parent = head_bone
            new_bone.use_connect = False

        prev_bone = new_bone
        log(f"  Created bone {bone_name}: head={[round(x, 1) for x in seg_start]} tail={[round(x, 1) for x in seg_end]}")

    ensure_mode(armature, 'OBJECT')

    # --- Add secondary motion constraints (spring-like behavior) ---
    log("  Adding secondary motion constraints to ponytail...")

    ensure_mode(armature, 'POSE')

    for i, bone_name in enumerate(ponytail_bone_names):
        pbone = armature.pose.bones.get(bone_name)
        if not pbone:
            log(f"  WARNING: Pose bone '{bone_name}' not found!")
            continue

        # Add COPY_ROTATION constraint from Head bone with lag
        # This makes the ponytail follow head movement with delay
        cr = pbone.constraints.new('COPY_ROTATION')
        cr.name = "Ponytail_Follow"
        cr.target = armature
        cr.subtarget = "Head"
        cr.target_space = 'LOCAL'
        cr.owner_space = 'LOCAL'
        cr.mix_mode = 'ADD'
        # Decreasing influence along the chain creates a lag/wave effect
        cr.influence = max(0.05, 0.4 - (i * 0.1))
        cr.use_x = True
        cr.use_y = True
        cr.use_z = True

        # Add LIMIT_ROTATION to prevent extreme deformation
        lr = pbone.constraints.new('LIMIT_ROTATION')
        lr.name = "Ponytail_Limit"
        lr.owner_space = 'LOCAL'
        lr.use_limit_x = True
        lr.min_x = math.radians(-45 - i * 10)  # More freedom further down
        lr.max_x = math.radians(45 + i * 10)
        lr.use_limit_y = True
        lr.min_y = math.radians(-30 - i * 5)
        lr.max_y = math.radians(30 + i * 5)
        lr.use_limit_z = True
        lr.min_z = math.radians(-40 - i * 8)
        lr.max_z = math.radians(40 + i * 8)

        log(f"  {bone_name}: follow influence={cr.influence:.2f}, rotation limits added")

    ensure_mode(armature, 'OBJECT')

    # --- Weight paint ponytail vertices ---
    log("  Weight painting ponytail vertices...")
    weight_paint_ponytail(armature, mesh, ponytail_bone_names)

    log("  Ponytail setup complete.")
    return ponytail_bone_names


def weight_paint_ponytail(armature, mesh, ponytail_bone_names):
    """
    Assign vertices in the ponytail region to the new ponytail bones.
    Strategy: Find vertices behind and above the head center that are currently
    weighted to Head or head_end, and redistribute them to ponytail bones.
    """
    ensure_mode(mesh, 'OBJECT')

    # Get bone world positions for the ponytail chain
    ensure_mode(armature, 'POSE')
    ponytail_bone_heads = []
    ponytail_bone_tails = []
    for name in ponytail_bone_names:
        pbone = armature.pose.bones.get(name)
        if pbone:
            # Get bone head/tail in armature space
            head_world = pbone.head.copy()
            tail_world = pbone.tail.copy()
            ponytail_bone_heads.append(head_world)
            ponytail_bone_tails.append(tail_world)

    ensure_mode(armature, 'OBJECT')
    ensure_mode(mesh, 'OBJECT')

    # Create vertex groups for ponytail bones if they don't exist
    for name in ponytail_bone_names:
        if name not in mesh.vertex_groups:
            mesh.vertex_groups.new(name=name)

    # Get existing Head and head_end vertex groups
    head_vg = mesh.vertex_groups.get("Head")
    head_end_vg = mesh.vertex_groups.get("head_end")

    if not head_vg and not head_end_vg:
        log("  WARNING: No Head/head_end vertex groups found for weight transfer")
        return

    # Get armature space transform
    arm_mat_inv = armature.matrix_world.inverted()
    mesh_mat = mesh.matrix_world

    # Find vertices in the ponytail region
    # Ponytail region: behind the head (Y > head center Y) and above mid-skull
    head_bone = armature.data.bones.get("Head")
    if not head_bone:
        return

    head_center_y = head_bone.head_local.y
    head_center_z = head_bone.head_local.z
    # Ponytail region starts behind head center and above neck
    ponytail_min_y = head_center_y + 5.0  # Behind head center
    ponytail_min_z = head_center_z + 20.0  # Above mid-head

    log(f"  Ponytail region: Y > {ponytail_min_y:.1f}, Z > {ponytail_min_z:.1f}")

    # Identify ponytail vertices
    ponytail_verts = []
    for v in mesh.data.vertices:
        # Transform vertex to armature space
        v_world = mesh_mat @ v.co
        v_arm = arm_mat_inv @ v_world

        # Check if vertex is in ponytail region
        if v_arm.y > ponytail_min_y and v_arm.z > ponytail_min_z:
            # Check if it's weighted to Head or head_end
            is_head_weighted = False
            for g in v.groups:
                vg = mesh.vertex_groups[g.group]
                if vg.name in ("Head", "head_end") and g.weight > 0.1:
                    is_head_weighted = True
                    break

            if is_head_weighted:
                ponytail_verts.append((v.index, v_arm.copy()))

    log(f"  Found {len(ponytail_verts)} potential ponytail vertices")

    if len(ponytail_verts) == 0:
        # Try with more relaxed criteria
        log("  Trying relaxed ponytail detection...")
        for v in mesh.data.vertices:
            v_world = mesh_mat @ v.co
            v_arm = arm_mat_inv @ v_world
            # More relaxed: just behind head and high up
            if v_arm.y > head_center_y and v_arm.z > head_center_z + 30.0:
                ponytail_verts.append((v.index, v_arm.copy()))

        log(f"  Found {len(ponytail_verts)} ponytail vertices with relaxed criteria")

    if len(ponytail_verts) == 0:
        log("  WARNING: Could not identify ponytail vertices. Manual weight painting needed.")
        return

    # Sort vertices by distance along the ponytail direction (Y + down)
    ponytail_dir = mathutils.Vector((0.0, 1.0, -0.8)).normalized()

    # Project each vertex onto the ponytail direction to get its position along the chain
    projections = []
    for vi, v_pos in ponytail_verts:
        # Vector from ponytail start to vertex
        start_pos = mathutils.Vector((
            head_bone.head_local.x,
            head_bone.head_local.y + 10.0,
            head_bone.head_local.z + 35.0
        ))
        offset = v_pos - start_pos
        projection = offset.dot(ponytail_dir)
        projections.append((vi, v_pos, projection))

    # Get range of projections
    min_proj = min(p[2] for p in projections)
    max_proj = max(p[2] for p in projections)
    proj_range = max_proj - min_proj

    if proj_range < 0.01:
        log("  WARNING: Ponytail vertices all at same position, cannot distribute weights")
        # Assign all to first ponytail bone
        vg = mesh.vertex_groups.get(ponytail_bone_names[0])
        for vi, _, _ in projections:
            vg.add([vi], 1.0, 'REPLACE')
        return

    log(f"  Projection range: [{min_proj:.1f}, {max_proj:.1f}]")

    # Assign vertices to ponytail segments based on their position along the chain
    segment_size = proj_range / PONYTAIL_SEGMENTS

    for vi, v_pos, proj in projections:
        # Normalized position along the chain (0 = base, 1 = tip)
        t = (proj - min_proj) / proj_range
        t = max(0.0, min(1.0, t))

        # Determine which segment(s) this vertex belongs to
        seg_float = t * PONYTAIL_SEGMENTS
        seg_idx = min(int(seg_float), PONYTAIL_SEGMENTS - 1)

        # Blend between adjacent segments for smooth deformation
        seg_frac = seg_float - seg_idx

        # Primary weight
        primary_vg = mesh.vertex_groups.get(ponytail_bone_names[seg_idx])
        primary_weight = 1.0 - seg_frac * 0.5

        if primary_vg:
            primary_vg.add([vi], primary_weight, 'REPLACE')

        # Secondary weight (next segment) for smooth transition
        if seg_idx + 1 < PONYTAIL_SEGMENTS and seg_frac > 0.1:
            secondary_vg = mesh.vertex_groups.get(ponytail_bone_names[seg_idx + 1])
            secondary_weight = seg_frac * 0.5
            if secondary_vg:
                secondary_vg.add([vi], secondary_weight, 'REPLACE')

        # Reduce Head/head_end weight for these vertices
        # (keep some weight for smooth blending at the base)
        head_retain = max(0.0, 0.3 * (1.0 - t))  # More head weight at base
        for g in mesh.data.vertices[vi].groups:
            vg = mesh.vertex_groups[g.group]
            if vg.name in ("Head", "head_end"):
                if t > 0.3:  # Keep full head weight near the base
                    g.weight = head_retain

    log(f"  Weight painted {len(ponytail_verts)} vertices across {PONYTAIL_SEGMENTS} ponytail segments")


# ============================================================
# STEP 5: LEG ROTATION LIMITS (Additional Protection)
# ============================================================

def add_leg_rotation_limits(armature):
    """Add rotation limits on upper legs to prevent unnatural poses."""
    log("Step 5: Adding leg rotation limits...")

    ensure_mode(armature, 'POSE')

    leg_limits = {
        "LeftUpLeg": {
            "use_limit_x": True, "min_x": math.radians(-30), "max_x": math.radians(120),
            "use_limit_y": True, "min_y": math.radians(-45), "max_y": math.radians(45),
            "use_limit_z": True, "min_z": math.radians(-60), "max_z": math.radians(30),
        },
        "RightUpLeg": {
            "use_limit_x": True, "min_x": math.radians(-30), "max_x": math.radians(120),
            "use_limit_y": True, "min_y": math.radians(-45), "max_y": math.radians(45),
            "use_limit_z": True, "min_z": math.radians(-30), "max_z": math.radians(60),
        },
        # Lower legs: knees only bend one way
        "LeftLeg": {
            "use_limit_x": True, "min_x": math.radians(-5), "max_x": math.radians(150),
            "use_limit_y": True, "min_y": math.radians(-10), "max_y": math.radians(10),
            "use_limit_z": True, "min_z": math.radians(-10), "max_z": math.radians(10),
        },
        "RightLeg": {
            "use_limit_x": True, "min_x": math.radians(-5), "max_x": math.radians(150),
            "use_limit_y": True, "min_y": math.radians(-10), "max_y": math.radians(10),
            "use_limit_z": True, "min_z": math.radians(-10), "max_z": math.radians(10),
        },
    }

    for bone_name, limits in leg_limits.items():
        pbone = armature.pose.bones.get(bone_name)
        if not pbone:
            log(f"  WARNING: Bone '{bone_name}' not found")
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

        log(f"  Added rotation limits on {bone_name}")

    ensure_mode(armature, 'OBJECT')
    log("  Leg rotation limits complete.")


# ============================================================
# STEP 6: EXPORT
# ============================================================

def export_model(armature, mesh):
    log("Step 6: Exporting fixed model...")

    # Ensure we're in object mode
    ensure_mode(armature, 'OBJECT')

    # Select armature and mesh for export
    bpy.ops.object.select_all(action='DESELECT')
    armature.select_set(True)
    mesh.select_set(True)
    bpy.context.view_layer.objects.active = armature

    # Export as GLB
    bpy.ops.export_scene.gltf(
        filepath=OUTPUT_GLB,
        export_format='GLB',
        use_selection=True,
        export_apply=False,
        export_animations=True,
        export_skins=True,
        export_morph=True,
        export_materials='EXPORT',
        export_colors=True,
        export_extras=True,
    )

    log(f"  Exported to {OUTPUT_GLB}")

    # Verify file size
    if os.path.exists(OUTPUT_GLB):
        size_mb = os.path.getsize(OUTPUT_GLB) / (1024 * 1024)
        log(f"  File size: {size_mb:.1f} MB")
    else:
        log("  ERROR: Export file not found!")


# ============================================================
# STEP 7: GENERATE REPORT
# ============================================================

def generate_report(armature, mesh, ponytail_bones):
    log("Step 7: Generating rig report...")

    ensure_mode(armature, 'POSE')

    report = {
        "version": "v2",
        "fixes_applied": [],
        "bone_count": len(armature.data.bones),
        "new_bones": ponytail_bones if ponytail_bones else [],
        "constraints": {},
        "vertex_count": len(mesh.data.vertices),
        "face_count": len(mesh.data.polygons),
        "character_height": 1.2,
    }

    # Document all constraints
    for pbone in armature.pose.bones:
        if pbone.constraints:
            bone_constraints = []
            for c in pbone.constraints:
                cdata = {"type": c.type, "name": c.name}
                if c.type == 'LIMIT_ROTATION':
                    cdata["limits"] = {
                        "x": [math.degrees(c.min_x), math.degrees(c.max_x)] if c.use_limit_x else None,
                        "y": [math.degrees(c.min_y), math.degrees(c.max_y)] if c.use_limit_y else None,
                        "z": [math.degrees(c.min_z), math.degrees(c.max_z)] if c.use_limit_z else None,
                    }
                elif c.type == 'COPY_ROTATION':
                    cdata["target"] = c.subtarget
                    cdata["influence"] = c.influence
                    cdata["invert_y"] = c.invert_y
                    cdata["invert_z"] = c.invert_z
                bone_constraints.append(cdata)
            report["constraints"][pbone.name] = bone_constraints

    # List fixes
    report["fixes_applied"] = [
        "Arm rotation limits (LeftArm, RightArm, LeftForeArm, RightForeArm) - prevents leg clipping",
        "Shoulder rotation limits (LeftShoulder, RightShoulder) - prevents extreme poses",
        "Spine counter-rotation (Spine, Spine01 vs Hips) - natural walk motion",
        "Ponytail bone chain (4 segments) with secondary motion constraints",
        "Ponytail vertex weight painting",
        "Leg rotation limits (LeftUpLeg, RightUpLeg, LeftLeg, RightLeg) - natural range",
        "Removed stray Icosphere object",
    ]

    report["recommendations"] = [
        "Use same rig fix approach for Leo, Gabe, Nina characters",
        "Ponytail weights may need manual refinement in Blender GUI",
        "Test with Meshy walking/running animations to verify constraint values",
        "Consider Mixamo re-targeting for more animation variety",
        "Arm limits tuned for walk cycle - may need adjustment for other animations",
    ]

    ensure_mode(armature, 'OBJECT')

    # Save report
    report_path = "tmp/mia_rig_v2_report.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)

    log(f"  Report saved to {report_path}")
    return report


# ============================================================
# MAIN
# ============================================================

def main():
    log("=" * 60)
    log("FIXING MIA CHARACTER RIG")
    log("=" * 60)

    # Step 1: Import and cleanup
    armature, mesh = import_and_cleanup()

    # Step 2: Arm rotation limits
    add_arm_rotation_limits(armature)

    # Step 3: Spine counter-rotation
    setup_spine_counter_rotation(armature)

    # Step 4: Ponytail bones
    ponytail_bones = add_ponytail_bones(armature, mesh)

    # Step 5: Leg rotation limits
    add_leg_rotation_limits(armature)

    # Step 6: Export
    export_model(armature, mesh)

    # Step 7: Report
    report = generate_report(armature, mesh, ponytail_bones)

    log("")
    log("=" * 60)
    log("RIG FIX COMPLETE")
    log("=" * 60)
    log(f"  Input:  {INPUT_GLB}")
    log(f"  Output: {OUTPUT_GLB}")
    log(f"  Bones:  {report['bone_count']} (was 24, added {len(report.get('new_bones', []))})")
    log(f"  Fixes:  {len(report['fixes_applied'])}")
    log("")


if __name__ == "__main__":
    main()
