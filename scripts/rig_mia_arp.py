"""
Rig Mia character using Auto-Rig Pro with Voxelize skinning.

Usage:
    blender --background models/characters/mia.blend --python scripts/rig_mia_arp.py

The ARP Smart detection throws a non-fatal error in headless mode (space_data is
None) but the rig IS created before the error. We catch and continue.
"""

import bpy
import mathutils
import math
import addon_utils
import sys
import os

OUTPUT_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           "models", "characters", "mia_rigged.blend")

BODY_PARTS = [
    'Mia_Torso', 'Mia_Head', 'Mia_UpperArm_L', 'Mia_UpperArm_R',
    'Mia_LowerArm_L', 'Mia_LowerArm_R', 'Mia_Hand_L', 'Mia_Hand_R',
    'Mia_UpperLeg_L', 'Mia_UpperLeg_R', 'Mia_LowerLeg_L', 'Mia_LowerLeg_R',
    'Mia_Shoe_L', 'Mia_Shoe_R', 'Mia_Shoe_Sole_L', 'Mia_Shoe_Sole_R',
    'Mia_Shorts', 'Mia_Nose',
]

LEFT_ARM_PARTS = ['Mia_UpperArm_L', 'Mia_LowerArm_L', 'Mia_Hand_L']
RIGHT_ARM_PARTS = ['Mia_UpperArm_R', 'Mia_LowerArm_R', 'Mia_Hand_R']

SHOULDER_L = mathutils.Vector((-0.1016, 0, 0.9402))
SHOULDER_R = mathutils.Vector((0.1016, 0, 0.9402))


def log(msg):
    print(f"[RIG] {msg}")
    sys.stdout.flush()


def rotate_around_pivot(obj, pivot, axis, angle):
    """Rotate object around a world-space pivot."""
    rot = mathutils.Matrix.Rotation(angle, 4, axis)
    t = mathutils.Matrix.Translation(pivot)
    t_inv = mathutils.Matrix.Translation(-pivot)
    obj.matrix_world = t @ rot @ t_inv @ obj.matrix_world


def apply_transforms(obj):
    """Apply object transforms."""
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)


def main():
    log("=" * 60)
    log("Rigging Mia with Auto-Rig Pro")
    log("=" * 60)

    # ── Enable ARP first ──────────────────────────────────────
    log("Enabling Auto-Rig Pro...")
    addon_utils.enable('auto_rig_pro', default_set=True)
    addon_utils.enable('rig_tools', default_set=True)
    log("  ARP loaded OK")

    # ── T-pose arms ───────────────────────────────────────────
    log("T-posing arms...")
    for name in LEFT_ARM_PARTS + RIGHT_ARM_PARTS:
        obj = bpy.data.objects.get(name)
        if obj and obj.parent:
            mat = obj.matrix_world.copy()
            obj.parent = None
            obj.matrix_world = mat

    for name in LEFT_ARM_PARTS:
        obj = bpy.data.objects.get(name)
        if obj:
            rotate_around_pivot(obj, SHOULDER_L, 'Y', math.radians(90))

    for name in RIGHT_ARM_PARTS:
        obj = bpy.data.objects.get(name)
        if obj:
            rotate_around_pivot(obj, SHOULDER_R, 'Y', math.radians(-90))

    log("  Arms T-posed")

    # ── Apply transforms + join body ──────────────────────────
    log("Joining body meshes...")
    for name in BODY_PARTS:
        obj = bpy.data.objects.get(name)
        if obj:
            if obj.parent:
                mat = obj.matrix_world.copy()
                obj.parent = None
                obj.matrix_world = mat
            apply_transforms(obj)

    bpy.ops.object.select_all(action='DESELECT')
    count = 0
    for name in BODY_PARTS:
        obj = bpy.data.objects.get(name)
        if obj:
            obj.select_set(True)
            count += 1

    torso = bpy.data.objects.get('Mia_Torso')
    bpy.context.view_layer.objects.active = torso
    bpy.ops.object.join()

    body = bpy.context.active_object
    body.name = 'Mia_Body'
    body.data.name = 'Mia_Body'
    log(f"  Joined {count} parts: {len(body.data.vertices)} verts, {len(body.data.polygons)} faces")
    log(f"  Dimensions: {body.dimensions}")

    # ── Configure Smart detection ─────────────────────────────
    log("Configuring Smart detection...")
    scn = bpy.context.scene
    scn.arp_body_name = 'Mia_Body'
    scn.arp_smart_type = 'BODY'
    scn.arp_smart_preset_settings = 'DEFAULT'
    scn.arp_smart_overwrite = True
    scn.arp_smart_spine_count = 3
    scn.arp_smart_neck_count = 1
    scn.arp_smart_twist_count = 1
    scn.arp_smart_sym = True
    scn.arp_smart_depth = False
    scn.arp_fingers_enable = False
    scn.arp_smart_root_vertical = True
    scn.arp_smart_spine_shape = 'STRAIGHT'

    # Select body mesh
    bpy.ops.object.select_all(action='DESELECT')
    body.select_set(True)
    bpy.context.view_layer.objects.active = body

    # ── Run Smart detection ───────────────────────────────────
    log("Running Smart detection...")
    try:
        bpy.ops.id.go_detect()
        log("  Detection completed cleanly")
    except RuntimeError as e:
        if 'overlay' in str(e) or 'space_data' in str(e):
            log("  Detection completed with non-fatal UI error (expected in headless)")
        else:
            raise

    # Verify rig was created
    rig = bpy.data.objects.get('rig')
    if not rig or rig.type != 'ARMATURE':
        raise RuntimeError("No rig was created by Smart detection!")

    log(f"  Rig created: {len(rig.data.bones)} bones")

    # Print key bone positions
    key_bones = ['c_root_master.x', 'c_head.x', 'c_hand_fk.l', 'c_hand_fk.r',
                 'c_foot_fk.l', 'c_foot_fk.r', 'c_arm_fk.l', 'c_arm_fk.r',
                 'c_thigh_fk.l', 'c_thigh_fk.r', 'c_shoulder.l']
    for bname in key_bones:
        b = rig.data.bones.get(bname)
        if b:
            head = rig.matrix_world @ b.head_local
            log(f"    {bname}: ({head.x:.4f}, {head.y:.4f}, {head.z:.4f})")

    # ── Bind with Voxelize ────────────────────────────────────
    log("Binding with Voxelize mode...")
    scn.arp_bind_engine = 'PSEUDO_VOXELS'
    scn.arp_pseudo_voxels_resolution = 8
    scn.arp_pseudo_voxels_type = '1'
    scn.arp_bind_improve_twists = True
    scn.arp_bind_improve_hips = True
    scn.arp_bind_improve_heels = True
    scn.arp_bind_split = True

    # Ensure object mode
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')

    bpy.ops.object.select_all(action='DESELECT')
    body = bpy.data.objects['Mia_Body']
    body.select_set(True)
    bpy.context.view_layer.objects.active = rig
    rig.select_set(True)

    try:
        result = bpy.ops.arp.bind_to_rig()
        log(f"  Bind result: {result}")
    except RuntimeError as e:
        if 'overlay' in str(e) or 'space_data' in str(e):
            log(f"  Bind completed with non-fatal UI error")
        else:
            log(f"  Voxelize bind failed: {e}")
            log("  Trying heat map fallback...")
            scn.arp_bind_engine = 'HEAT_MAP'
            try:
                result = bpy.ops.arp.bind_to_rig()
                log(f"  Heat map result: {result}")
            except RuntimeError as e2:
                if 'overlay' in str(e2) or 'space_data' in str(e2):
                    log(f"  Heat map completed with non-fatal UI error")
                else:
                    raise

    # Check binding results
    vg_count = len(body.vertex_groups)
    log(f"  Vertex groups: {vg_count}")
    if body.parent == rig:
        log("  Body mesh parented to rig")
    else:
        # Try to check if Armature modifier was added
        arm_mod = None
        for mod in body.modifiers:
            if mod.type == 'ARMATURE':
                arm_mod = mod
                break
        if arm_mod:
            log(f"  Armature modifier found: {arm_mod.name}")
        else:
            log("  WARNING: No parenting or armature modifier found")

    # ── Parent accessories to head bone ───────────────────────
    log("Parenting accessories...")
    bone_map = {
        'Mia_Hair_Base': 'c_head.x',
        'Mia_Ponytail': 'c_head.x',
        'Mia_Ponytail_End': 'c_head.x',
        'Mia_Scrunchie': 'c_head.x',
        'Mia_Eye_L': 'c_head.x',
        'Mia_Eye_R': 'c_head.x',
        'Mia_Iris_L': 'c_head.x',
        'Mia_Iris_R': 'c_head.x',
        'Mia_Pupil_L': 'c_head.x',
        'Mia_Pupil_R': 'c_head.x',
        'Mia_Mouth': 'c_head.x',
        'Mia_Shirt_Star': 'c_spine_02.x',
    }

    # Ensure object mode
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')

    for obj_name, bone_name in bone_map.items():
        obj = bpy.data.objects.get(obj_name)
        if not obj:
            continue

        bone = rig.data.bones.get(bone_name)
        if not bone:
            # Try alternatives
            for alt in ['c_spine_01.x', 'c_root.x']:
                bone = rig.data.bones.get(alt)
                if bone:
                    bone_name = alt
                    break
        if not bone:
            log(f"  SKIP: no bone for {obj_name}")
            continue

        # Unparent first
        if obj.parent:
            mat = obj.matrix_world.copy()
            obj.parent = None
            obj.matrix_world = mat

        # Parent to bone
        obj.parent = rig
        obj.parent_type = 'BONE'
        obj.parent_bone = bone_name
        bone_mat = rig.matrix_world @ bone.matrix_local
        obj.matrix_parent_inverse = bone_mat.inverted()
        log(f"  {obj_name} -> {bone_name}")

    # ── Save ──────────────────────────────────────────────────
    log(f"Saving to {OUTPUT_PATH}...")
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=OUTPUT_PATH)
    log("  Saved!")

    log("=" * 60)
    log("RIGGING COMPLETE!")
    log("=" * 60)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        log(f"FATAL: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
