"""
Fix Meshy Weight Painting for Mia - v4
========================================
Improves weight painting on the existing Meshy rig.
Keeps the mesh EXACTLY the same. Only modifies vertex group weights and adds constraints.

Core issues with Meshy's weights:
- Shoulder bones influence 83% of vertices (should be ~5%)
- Arm bones influence 45% of vertices (should be ~10%)
- Head influences 92% (should be ~15%)
- No hair weighting (head_end unused)
- Result: arm clipping, stiff torso, rigid hair

Fix strategy (working in armature local space, cm):
1. Define body zones by Z-height using bone HEAD positions
2. Remove cross-zone weight leaks (arms→legs, legs→head, etc.)
3. Fade weights at zone boundaries for smooth transitions
4. Boost spine weights in torso
5. Assign hair to head_end
6. Normalize and add constraints

Usage:
  xvfb-run blender --background --python scripts/blender/fix_meshy_weights.py
"""

import bpy
import math
import sys
import os
from mathutils import Vector

MODEL_PATH = "models/characters/mia/mia_rigged.glb"
OUTPUT_GLB = "models/characters/mia/mia_improved_rig.glb"
OUTPUT_BLEND = "models/characters/mia/mia_improved_rig.blend"
EXPECTED_VERTS = 640542
EXPECTED_FACES = 1075577


def log(msg):
    print(f"[FIX] {msg}")


def verify_mesh(mesh_obj):
    v = len(mesh_obj.data.vertices)
    f = len(mesh_obj.data.polygons)
    assert v == EXPECTED_VERTS and f == EXPECTED_FACES, f"Mesh changed! {v}v/{f}f"


def get_vg(mesh_obj, name):
    return mesh_obj.vertex_groups.get(name)


def get_weight(vg, vi):
    try:
        return vg.weight(vi)
    except RuntimeError:
        return 0.0


# ---------------------------------------------------------------
# Step 1: Import
# ---------------------------------------------------------------
def step_import():
    log("Step 1: Import")
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    bpy.ops.import_scene.gltf(filepath=MODEL_PATH)

    for obj in list(bpy.context.scene.objects):
        if obj.type == 'MESH' and not obj.vertex_groups:
            name = obj.name
            bpy.data.objects.remove(obj, do_unlink=True)
            log(f"  Removed: {name}")

    arm = mesh = None
    for obj in bpy.context.scene.objects:
        if obj.type == 'ARMATURE':
            arm = obj
        elif obj.type == 'MESH' and obj.vertex_groups:
            mesh = obj

    assert arm and mesh
    verify_mesh(mesh)

    # Print bone HEAD z-positions for reference
    log("  Bone HEAD z-positions (armature local, cm):")
    for bone in arm.data.bones:
        log(f"    {bone.name}: head_z={bone.head_local.z:.1f}")

    return arm, mesh


# ---------------------------------------------------------------
# Step 2: Zone-based weight cleanup
# ---------------------------------------------------------------
def step_zone_cleanup(armature, mesh_obj):
    """Remove weight leaks across body zones.

    Body zones (Z in armature local cm):
    - Feet:    z < 10
    - Legs:    10 <= z < 40
    - Hips:    40 <= z < 52
    - Torso:   52 <= z < 72
    - Neck:    72 <= z < 77
    - Head:    z >= 77

    Rules:
    - Arm/shoulder bones: weight = 0 below z=35 (hard), fade z=35-50
    - Leg bones: weight = 0 above z=72 (hard), fade z=60-72
    - Hand bones: weight = 0 outside arm region
    """
    log("Step 2: Zone-based weight cleanup")

    arm_inv = armature.matrix_world.inverted()
    mesh_mat = mesh_obj.matrix_world

    # Bone groups
    arm_shoulder_bones = {
        "LeftShoulder", "LeftArm", "LeftForeArm", "LeftHand",
        "RightShoulder", "RightArm", "RightForeArm", "RightHand",
    }
    leg_foot_bones = {
        "LeftUpLeg", "LeftLeg", "LeftFoot", "LeftToeBase",
        "RightUpLeg", "RightLeg", "RightFoot", "RightToeBase",
    }

    # Zone boundaries (armature local z, cm)
    ARM_HARD_CUTOFF = 35.0    # Arms have ZERO influence below this
    ARM_FADE_START = 50.0     # Arms start fading below this
    LEG_HARD_CUTOFF = 72.0    # Legs have ZERO influence above this
    LEG_FADE_START = 60.0     # Legs start fading above this

    log(f"  Arm zone: hard<{ARM_HARD_CUTOFF}, fade {ARM_HARD_CUTOFF}-{ARM_FADE_START}")
    log(f"  Leg zone: hard>{LEG_HARD_CUTOFF}, fade {LEG_FADE_START}-{LEG_HARD_CUTOFF}")

    removed = 0
    faded = 0
    report_every = EXPECTED_VERTS // 10

    for i, v in enumerate(mesh_obj.data.vertices):
        if i > 0 and i % report_every == 0:
            log(f"    {100*i//EXPECTED_VERTS}%")

        local_co = arm_inv @ (mesh_mat @ v.co)
        vz = local_co.z

        for g in list(v.groups):
            if g.weight < 0.001:
                continue

            vg = mesh_obj.vertex_groups[g.group]
            bone_name = vg.name

            # ARM/SHOULDER bones below their zone
            if bone_name in arm_shoulder_bones:
                if vz < ARM_HARD_CUTOFF:
                    vg.add([v.index], 0.0, 'REPLACE')
                    removed += 1
                elif vz < ARM_FADE_START:
                    # Fade: 0 at hard_cutoff, full at fade_start
                    t = (vz - ARM_HARD_CUTOFF) / (ARM_FADE_START - ARM_HARD_CUTOFF)
                    new_w = g.weight * t
                    if new_w < 0.005:
                        vg.add([v.index], 0.0, 'REPLACE')
                        removed += 1
                    else:
                        vg.add([v.index], new_w, 'REPLACE')
                        faded += 1

            # LEG/FOOT bones above their zone
            elif bone_name in leg_foot_bones:
                if vz > LEG_HARD_CUTOFF:
                    vg.add([v.index], 0.0, 'REPLACE')
                    removed += 1
                elif vz > LEG_FADE_START:
                    # Fade: full at fade_start, 0 at hard_cutoff
                    t = 1.0 - (vz - LEG_FADE_START) / (LEG_HARD_CUTOFF - LEG_FADE_START)
                    new_w = g.weight * t
                    if new_w < 0.005:
                        vg.add([v.index], 0.0, 'REPLACE')
                        removed += 1
                    else:
                        vg.add([v.index], new_w, 'REPLACE')
                        faded += 1

    log(f"  Removed {removed} cross-zone weights")
    log(f"  Faded {faded} transition weights")
    verify_mesh(mesh_obj)


# ---------------------------------------------------------------
# Step 3: Proximity cleanup within zones
# ---------------------------------------------------------------
def step_proximity_cleanup(armature, mesh_obj):
    """Within each zone, reduce weights from very distant bones.

    Uses distance from bone HEAD position (the reliable position in Meshy rigs)
    to reduce weight from bones that are clearly too far away.
    """
    log("Step 3: Proximity cleanup")

    arm_inv = armature.matrix_world.inverted()
    mesh_mat = mesh_obj.matrix_world

    # Bone HEAD positions in armature local space
    bone_heads = {}
    for bone in armature.data.bones:
        bone_heads[bone.name] = Vector(bone.head_local)

    # Max distance from bone head for weight influence (cm)
    # These are generous - just removing the extreme long-range leaks
    max_dist = {
        "Hips": 30, "Spine02": 25, "Spine01": 25, "Spine": 25,
        "neck": 20, "Head": 45, "head_end": 40, "headfront": 30,
        "LeftShoulder": 20, "LeftArm": 25, "LeftForeArm": 25, "LeftHand": 20,
        "RightShoulder": 20, "RightArm": 25, "RightForeArm": 25, "RightHand": 20,
        "LeftUpLeg": 30, "LeftLeg": 25, "LeftFoot": 20, "LeftToeBase": 15,
        "RightUpLeg": 30, "RightLeg": 25, "RightFoot": 20, "RightToeBase": 15,
    }

    removed = 0
    faded = 0
    report_every = EXPECTED_VERTS // 10

    for i, v in enumerate(mesh_obj.data.vertices):
        if i > 0 and i % report_every == 0:
            log(f"    {100*i//EXPECTED_VERTS}%")

        local_co = arm_inv @ (mesh_mat @ v.co)

        for g in list(v.groups):
            if g.weight < 0.001:
                continue

            vg = mesh_obj.vertex_groups[g.group]
            bone_name = vg.name
            bone_head = bone_heads.get(bone_name)
            if bone_head is None:
                continue

            dist = (local_co - bone_head).length
            mr = max_dist.get(bone_name, 25)
            fade_start = mr * 0.7

            if dist > mr:
                vg.add([v.index], 0.0, 'REPLACE')
                removed += 1
            elif dist > fade_start:
                t = (dist - fade_start) / (mr - fade_start)
                new_w = g.weight * (1.0 - t)
                if new_w < 0.005:
                    vg.add([v.index], 0.0, 'REPLACE')
                    removed += 1
                else:
                    vg.add([v.index], new_w, 'REPLACE')
                    faded += 1

    log(f"  Removed {removed} distant weights")
    log(f"  Faded {faded} transition weights")
    verify_mesh(mesh_obj)


# ---------------------------------------------------------------
# Step 4: Boost spine for torso flexibility
# ---------------------------------------------------------------
def step_boost_spine(armature, mesh_obj):
    """Ensure spine bones have adequate weight in torso region."""
    log("Step 4: Boost spine weights")

    arm_inv = armature.matrix_world.inverted()
    mesh_mat = mesh_obj.matrix_world

    # Spine bone head positions
    spine_info = []
    for name in ["Spine02", "Spine01", "Spine"]:
        bone = armature.data.bones.get(name)
        if bone:
            spine_info.append((name, Vector(bone.head_local)))

    hips_z = armature.data.bones["Hips"].head_local.z  # ~47.7
    neck_z = armature.data.bones["neck"].head_local.z   # ~73.4

    boosted = 0
    for v in mesh_obj.data.vertices:
        local_co = arm_inv @ (mesh_mat @ v.co)
        vz = local_co.z

        if vz < hips_z or vz > neck_z:
            continue

        # Check total spine weight
        total_spine = 0
        for name, _ in spine_info:
            vg = get_vg(mesh_obj, name)
            if vg:
                total_spine += get_weight(vg, v.index)

        if total_spine < 0.1:
            # Find closest spine bone
            best = None
            best_d = float('inf')
            for name, pos in spine_info:
                d = (local_co - pos).length
                if d < best_d:
                    best_d = d
                    best = name

            if best:
                vg = get_vg(mesh_obj, best)
                if vg:
                    cur = get_weight(vg, v.index)
                    vg.add([v.index], max(cur, 0.15), 'REPLACE')
                    boosted += 1

    log(f"  Boosted {boosted} torso vertices")
    verify_mesh(mesh_obj)


# ---------------------------------------------------------------
# Step 5: Fix hair weights
# ---------------------------------------------------------------
def step_fix_hair(armature, mesh_obj):
    """Assign hair/ponytail vertices to head_end."""
    log("Step 5: Fix hair weights")

    arm_inv = armature.matrix_world.inverted()
    mesh_mat = mesh_obj.matrix_world

    head_bone = armature.data.bones.get("Head")
    head_end_bone = armature.data.bones.get("head_end")
    if not head_bone or not head_end_bone:
        log("  Missing bones, skip")
        return

    # All in armature local (cm)
    head_top_z = max(head_bone.head_local.z, head_bone.tail_local.z)
    head_start_z = head_bone.head_local.z  # ~78.5
    head_center_y = head_bone.head_local.y  # ~-6.6

    # head_end is at z=120, which is the top of the hair
    head_end_z = head_end_bone.head_local.z  # ~120.2

    log(f"  Head: start_z={head_start_z:.1f}, top_z={head_top_z:.1f}")
    log(f"  head_end: z={head_end_z:.1f}")

    # Hair region: above ~90% of head height
    # For this model, that's approximately z > 100 (above the skull dome)
    # Also: behind the head (y > head_center + 5) and above forehead
    hair_threshold_z = head_start_z + (head_end_z - head_start_z) * 0.3  # ~91
    log(f"  Hair threshold z > {hair_threshold_z:.1f} OR ponytail region")

    head_vg = get_vg(mesh_obj, "Head")
    head_end_vg = get_vg(mesh_obj, "head_end")
    if not head_end_vg:
        head_end_vg = mesh_obj.vertex_groups.new(name="head_end")

    hair_count = 0
    for v in mesh_obj.data.vertices:
        local_co = arm_inv @ (mesh_mat @ v.co)

        head_w = get_weight(head_vg, v.index) if head_vg else 0
        if head_w < 0.05:
            continue

        # Hair detection
        is_hair_top = local_co.z > hair_threshold_z
        is_ponytail = (local_co.y > head_center_y + 8.0 and
                       local_co.z > head_start_z + 5.0)

        if not (is_hair_top or is_ponytail):
            continue

        # Gradient: base of hair = mostly Head, tips = mostly head_end
        height_above_head = local_co.z - head_start_z
        max_hair_height = head_end_z - head_start_z  # ~42 cm
        t = min(1.0, max(0.0, height_above_head / max_hair_height))

        # Base: 85% Head / 15% head_end → Tips: 30% Head / 70% head_end
        he_ratio = 0.15 + 0.55 * t
        h_ratio = 1.0 - he_ratio

        head_end_vg.add([v.index], he_ratio * head_w, 'REPLACE')
        head_vg.add([v.index], h_ratio * head_w, 'REPLACE')
        hair_count += 1

    log(f"  {hair_count} hair vertices assigned to head_end")
    verify_mesh(mesh_obj)


# ---------------------------------------------------------------
# Step 6: Normalize
# ---------------------------------------------------------------
def step_normalize(mesh_obj):
    log("Step 6: Normalize")

    fixed = 0
    fallback = 0

    for v in mesh_obj.data.vertices:
        # Remove near-zero weights
        for g in list(v.groups):
            if g.weight < 0.005:
                mesh_obj.vertex_groups[g.group].remove([v.index])

        total = sum(g.weight for g in v.groups)
        if total > 0 and abs(total - 1.0) > 0.001:
            for g in v.groups:
                mesh_obj.vertex_groups[g.group].add(
                    [v.index], g.weight / total, 'REPLACE')
            fixed += 1
        elif total == 0:
            hips_vg = get_vg(mesh_obj, "Hips")
            if hips_vg:
                hips_vg.add([v.index], 1.0, 'REPLACE')
            fallback += 1

    log(f"  Renormalized {fixed}, fallback to Hips {fallback}")

    # Limit influences
    bpy.context.view_layer.objects.active = mesh_obj
    bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
    try:
        bpy.ops.object.vertex_group_limit_total(limit=4)
    except Exception:
        pass
    bpy.ops.object.mode_set(mode='OBJECT')
    verify_mesh(mesh_obj)


# ---------------------------------------------------------------
# Step 7: Add constraints
# ---------------------------------------------------------------
def step_add_constraints(armature):
    log("Step 7: Add constraints")
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='POSE')

    limits = {
        "LeftForeArm":  (-5, 150, -90, 90, -10, 10),
        "RightForeArm": (-5, 150, -90, 90, -10, 10),
        "LeftLeg":      (-5, 150, -10, 10, -10, 10),
        "RightLeg":     (-5, 150, -10, 10, -10, 10),
        "Head":         (-45, 45, -80, 80, -45, 45),
        "neck":         (-30, 30, -60, 60, -30, 30),
    }
    for bone_name, (xn, xx, yn, yx, zn, zx) in limits.items():
        pbone = armature.pose.bones.get(bone_name)
        if not pbone:
            continue
        for c in list(pbone.constraints):
            if c.type == 'LIMIT_ROTATION':
                pbone.constraints.remove(c)
        lim = pbone.constraints.new('LIMIT_ROTATION')
        lim.use_limit_x, lim.min_x, lim.max_x = True, math.radians(xn), math.radians(xx)
        lim.use_limit_y, lim.min_y, lim.max_y = True, math.radians(yn), math.radians(yx)
        lim.use_limit_z, lim.min_z, lim.max_z = True, math.radians(zn), math.radians(zx)
        lim.owner_space = 'LOCAL'
        log(f"  {bone_name}: limits added")
    bpy.ops.object.mode_set(mode='OBJECT')


# ---------------------------------------------------------------
# Step 8: Report
# ---------------------------------------------------------------
def step_report(mesh_obj):
    log("Final weight distribution:")
    total = len(mesh_obj.data.vertices)
    for vg in mesh_obj.vertex_groups:
        count = sum(1 for v in mesh_obj.data.vertices
                    for g in v.groups
                    if g.group == vg.index and g.weight > 0.005)
        if count > 0:
            log(f"  {vg.name}: {count} ({100*count/total:.1f}%)")


# ---------------------------------------------------------------
# Step 9: Export
# ---------------------------------------------------------------
def step_export():
    log("Step 9: Export")
    os.makedirs(os.path.dirname(os.path.abspath(OUTPUT_BLEND)), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(OUTPUT_BLEND))
    log(f"  Saved: {OUTPUT_BLEND}")

    try:
        bpy.ops.export_scene.gltf(
            filepath=os.path.abspath(OUTPUT_GLB),
            export_format='GLB',
            export_apply=False,
        )
        log(f"  Exported: {OUTPUT_GLB}")
    except Exception as e:
        log(f"  GLB failed: {e}, trying FBX...")
        try:
            bpy.ops.export_scene.fbx(
                filepath=os.path.abspath(OUTPUT_GLB.replace('.glb', '.fbx')),
                use_selection=False, add_leaf_bones=False,
                bake_anim=False, path_mode='COPY', embed_textures=True,
            )
            log(f"  Exported FBX")
        except Exception as e2:
            log(f"  FBX also failed: {e2}")


# ---------------------------------------------------------------
# Main
# ---------------------------------------------------------------
def main():
    log("=" * 60)
    log("  FIX MESHY WEIGHTS v4 - Zone + Proximity")
    log("=" * 60)

    armature, mesh = step_import()
    step_zone_cleanup(armature, mesh)
    step_proximity_cleanup(armature, mesh)
    step_boost_spine(armature, mesh)
    step_fix_hair(armature, mesh)
    step_normalize(mesh)
    step_add_constraints(armature)
    step_report(mesh)
    step_export()

    log("COMPLETE!")


if __name__ == "__main__":
    main()
