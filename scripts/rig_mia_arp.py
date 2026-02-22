"""
Rig Mia character with Auto-Rig Pro.

Run with:
    xvfb-run -a -s "-screen 0 1920x1080x24" \
        blender models/characters/mia.blend --python scripts/rig_mia_arp.py

MUST be run with xvfb (not --background) because ARP operators require a viewport.
The mia.blend file is loaded as the initial file (not via open_mainfile) so the
timer callback can work with it.
"""

import bpy
import os
import sys
import math
from mathutils import Vector

# Paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
OUTPUT_FILE = os.path.join(PROJECT_DIR, "models", "characters", "mia_arp_rigged.blend")


def run_rigging():
    """Main rigging function, called via timer after GUI init."""
    print("\n" + "=" * 60)
    print("RIGGING MIA WITH AUTO-RIG PRO")
    print("=" * 60)

    # Verify meshes loaded
    mesh_objects = [o for o in bpy.data.objects if o.type == 'MESH']
    print(f"Found {len(mesh_objects)} mesh objects")
    for obj in mesh_objects:
        print(f"  {obj.name}")

    materials = [m for m in bpy.data.materials if m.name.startswith('Mia_')]
    print(f"Found {len(materials)} Mia materials")

    # Record original mesh names for verification later
    original_meshes = set(o.name for o in mesh_objects)

    # ── Step 1: Enable addons ───────────────────────────────────
    print("\n[1/6] Enabling Auto-Rig Pro addons")
    bpy.ops.preferences.addon_enable(module='auto_rig_pro')
    bpy.ops.preferences.addon_enable(module='rig_tools')
    print("  Done")

    # ── Step 2: Get VIEW_3D context ─────────────────────────────
    print("\n[2/6] Setting up viewport context")
    area = None
    for a in bpy.context.screen.areas:
        if a.type == 'VIEW_3D':
            area = a
            break

    if area is None:
        print("ERROR: No VIEW_3D area found!")
        bpy.ops.wm.quit_blender()
        return None

    with bpy.context.temp_override(area=area, region=area.regions[-1]):
        # ── Step 3: Add ARP humanoid armature ───────────────────
        print("\n[3/6] Adding ARP humanoid armature")
        bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.arp.append_arp(rig_preset='human')
        rig = bpy.context.active_object
        print(f"  Created armature: {rig.name}")

        # ── Position reference bones to match Mia ──────────────
        print("  Positioning reference bones for Mia (child, ~1.25m)")

        bpy.ops.object.mode_set(mode='EDIT')
        eb = rig.data.edit_bones

        # ── ROOT & SPINE ──
        eb["root_ref.x"].head = Vector((0.0, 0.0, 0.632))
        eb["root_ref.x"].tail = Vector((0.0, 0.0, 0.740))

        eb["spine_01_ref.x"].head = Vector((0.0, 0.0, 0.740))
        eb["spine_01_ref.x"].tail = Vector((0.0, 0.0, 0.850))

        eb["spine_02_ref.x"].head = Vector((0.0, 0.0, 0.850))
        eb["spine_02_ref.x"].tail = Vector((0.0, 0.0, 0.960))

        # ── NECK & HEAD ──
        eb["neck_ref.x"].head = Vector((0.0, 0.0, 0.960))
        eb["neck_ref.x"].tail = Vector((0.0, -0.005, 1.020))

        eb["head_ref.x"].head = Vector((0.0, -0.005, 1.020))
        eb["head_ref.x"].tail = Vector((0.0, -0.005, 1.270))

        # ── LEGS ──
        eb["thigh_ref.l"].head = Vector((0.051, 0.0, 0.569))
        eb["thigh_ref.l"].tail = Vector((0.051, 0.0, 0.391))

        eb["thigh_ref.r"].head = Vector((-0.051, 0.0, 0.569))
        eb["thigh_ref.r"].tail = Vector((-0.051, 0.0, 0.391))

        eb["leg_ref.l"].head = Vector((0.051, 0.0, 0.391))
        eb["leg_ref.l"].tail = Vector((0.051, 0.005, 0.108))

        eb["leg_ref.r"].head = Vector((-0.051, 0.0, 0.391))
        eb["leg_ref.r"].tail = Vector((-0.051, 0.005, 0.108))

        # Feet
        eb["foot_ref.l"].head = Vector((0.051, 0.005, 0.108))
        eb["foot_ref.l"].tail = Vector((0.051, -0.040, 0.058))

        eb["foot_ref.r"].head = Vector((-0.051, 0.005, 0.108))
        eb["foot_ref.r"].tail = Vector((-0.051, -0.040, 0.058))

        # Toes
        eb["toes_ref.l"].head = Vector((0.051, -0.040, 0.058))
        eb["toes_ref.l"].tail = Vector((0.051, -0.065, 0.058))

        eb["toes_ref.r"].head = Vector((-0.051, -0.040, 0.058))
        eb["toes_ref.r"].tail = Vector((-0.051, -0.065, 0.058))

        # Foot bank references
        eb["foot_bank_01_ref.l"].head = Vector((0.076, 0.005, 0.058))
        eb["foot_bank_01_ref.l"].tail = Vector((0.076, -0.015, 0.058))
        eb["foot_bank_01_ref.r"].head = Vector((-0.076, 0.005, 0.058))
        eb["foot_bank_01_ref.r"].tail = Vector((-0.076, -0.015, 0.058))
        eb["foot_bank_02_ref.l"].head = Vector((0.025, 0.005, 0.058))
        eb["foot_bank_02_ref.l"].tail = Vector((0.025, -0.015, 0.058))
        eb["foot_bank_02_ref.r"].head = Vector((-0.025, 0.005, 0.058))
        eb["foot_bank_02_ref.r"].tail = Vector((-0.025, -0.015, 0.058))

        # Foot heel
        eb["foot_heel_ref.l"].head = Vector((0.051, 0.035, 0.058))
        eb["foot_heel_ref.l"].tail = Vector((0.051, 0.015, 0.058))
        eb["foot_heel_ref.r"].head = Vector((-0.051, 0.035, 0.058))
        eb["foot_heel_ref.r"].tail = Vector((-0.051, 0.015, 0.058))

        # ── ARMS (A-pose) ──
        eb["shoulder_ref.l"].head = Vector((0.030, 0.0, 0.940))
        eb["shoulder_ref.l"].tail = Vector((0.090, 0.0, 0.940))
        eb["shoulder_ref.r"].head = Vector((-0.030, 0.0, 0.940))
        eb["shoulder_ref.r"].tail = Vector((-0.090, 0.0, 0.940))

        eb["arm_ref.l"].head = Vector((0.090, 0.0, 0.940))
        eb["arm_ref.l"].tail = Vector((0.114, 0.0, 0.800))
        eb["arm_ref.r"].head = Vector((-0.090, 0.0, 0.940))
        eb["arm_ref.r"].tail = Vector((-0.114, 0.0, 0.800))

        eb["forearm_ref.l"].head = Vector((0.114, 0.0, 0.800))
        eb["forearm_ref.l"].tail = Vector((0.114, 0.0, 0.680))
        eb["forearm_ref.r"].head = Vector((-0.114, 0.0, 0.800))
        eb["forearm_ref.r"].tail = Vector((-0.114, 0.0, 0.680))

        eb["hand_ref.l"].head = Vector((0.114, 0.0, 0.680))
        eb["hand_ref.l"].tail = Vector((0.114, 0.0, 0.640))
        eb["hand_ref.r"].head = Vector((-0.114, 0.0, 0.680))
        eb["hand_ref.r"].tail = Vector((-0.114, 0.0, 0.640))

        # ── FINGERS ──
        finger_len = 0.012
        hand_x_l = 0.114
        hand_x_r = -0.114

        finger_defs = {
            "thumb": {"y": -0.015, "x_off": 0.005, "z": 0.670,
                      "segs": ["1", "2", "3"]},
            "index": {"y": -0.005, "x_off": 0.018, "z": 0.648,
                      "segs": ["1_base", "1", "2", "3"]},
            "middle": {"y": 0.002, "x_off": 0.018, "z": 0.646,
                       "segs": ["1_base", "1", "2", "3"]},
            "ring": {"y": 0.010, "x_off": 0.016, "z": 0.648,
                     "segs": ["1_base", "1", "2", "3"]},
            "pinky": {"y": 0.018, "x_off": 0.013, "z": 0.651,
                      "segs": ["1_base", "1", "2", "3"]},
        }

        for finger, fd in finger_defs.items():
            for i, seg in enumerate(fd["segs"]):
                bn_l = f"{finger}{seg}_ref.l"
                bn_r = f"{finger}{seg}_ref.r"
                z_h = fd["z"] - i * finger_len
                z_t = fd["z"] - (i + 1) * finger_len

                if bn_l in eb:
                    eb[bn_l].head = Vector((hand_x_l + fd["x_off"], fd["y"], z_h))
                    eb[bn_l].tail = Vector((hand_x_l + fd["x_off"], fd["y"], z_t))
                if bn_r in eb:
                    eb[bn_r].head = Vector((hand_x_r - fd["x_off"], fd["y"], z_h))
                    eb[bn_r].tail = Vector((hand_x_r - fd["x_off"], fd["y"], z_t))

        bpy.ops.object.mode_set(mode='OBJECT')
        print("  Reference bones positioned")

        # ── Step 4: Generate the rig ────────────────────────────
        print("\n[4/6] Generating rig (match_to_rig)")
        bpy.ops.arp.match_to_rig('EXEC_DEFAULT')
        print("  Rig generated successfully")

        # ── Step 5: Bind meshes to armature ─────────────────────
        print("\n[5/6] Binding meshes to armature")

        rig = None
        for obj in bpy.data.objects:
            if obj.type == 'ARMATURE':
                rig = obj
                break

        print(f"  Armature: {rig.name} ({len(rig.data.bones)} bones)")

        # Find head bone
        head_bone = None
        for name in ["c_head.x", "head.x", "head"]:
            if name in rig.data.bones:
                head_bone = name
                break
        print(f"  Head bone: {head_bone}")

        # Find spine bone for shirt star
        spine_bone = None
        for name in ["c_spine_02.x", "c_spine_01.x", "spine_02.x"]:
            if name in rig.data.bones:
                spine_bone = name
                break
        print(f"  Spine bone: {spine_bone}")

        # Find foot bones
        foot_bone_l = None
        foot_bone_r = None
        for name in ["c_foot_ik.l", "c_foot_fk.l", "foot.l"]:
            if name in rig.data.bones:
                foot_bone_l = name
                break
        for name in ["c_foot_ik.r", "c_foot_fk.r", "foot.r"]:
            if name in rig.data.bones:
                foot_bone_r = name
                break
        print(f"  Foot bones: {foot_bone_l}, {foot_bone_r}")

        # Categorize mesh parts
        deforming_parts = [
            "Mia_Head", "Mia_Torso",
            "Mia_UpperArm_L", "Mia_UpperArm_R",
            "Mia_LowerArm_L", "Mia_LowerArm_R",
            "Mia_Hand_L", "Mia_Hand_R",
            "Mia_UpperLeg_L", "Mia_UpperLeg_R",
            "Mia_LowerLeg_L", "Mia_LowerLeg_R",
            "Mia_Shorts",
        ]

        rigid_head_parts = [
            "Mia_Eye_L", "Mia_Eye_R",
            "Mia_Iris_L", "Mia_Iris_R",
            "Mia_Pupil_L", "Mia_Pupil_R",
            "Mia_Mouth", "Mia_Nose",
            "Mia_Hair_Base", "Mia_Ponytail",
            "Mia_Ponytail_End", "Mia_Scrunchie",
        ]

        rigid_bone_map = {
            "Mia_Shoe_L": foot_bone_l,
            "Mia_Shoe_R": foot_bone_r,
            "Mia_Shoe_Sole_L": foot_bone_l,
            "Mia_Shoe_Sole_R": foot_bone_r,
            "Mia_Shirt_Star": spine_bone,
        }

        # ── Bind deforming parts ──
        print("\n  Binding deforming parts...")
        bpy.ops.object.mode_set(mode='OBJECT')

        for part_name in deforming_parts:
            obj = bpy.data.objects.get(part_name)
            if obj is None:
                print(f"    SKIP: {part_name} not found")
                continue

            # Use standard Blender automatic weights (more reliable in headless)
            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(True)
            rig.select_set(True)
            bpy.context.view_layer.objects.active = rig

            try:
                bpy.ops.object.parent_set(type='ARMATURE_AUTO')
                print(f"    {part_name}: auto weights OK")
            except Exception as e:
                print(f"    {part_name}: auto weights failed ({e}), trying envelope")
                bpy.ops.object.select_all(action='DESELECT')
                obj.select_set(True)
                rig.select_set(True)
                bpy.context.view_layer.objects.active = rig
                try:
                    bpy.ops.object.parent_set(type='ARMATURE_ENVELOPE')
                    print(f"    {part_name}: envelope weights OK")
                except Exception as e2:
                    # Last resort: just parent with empty groups
                    bpy.ops.object.parent_set(type='ARMATURE_NAME')
                    print(f"    {part_name}: name groups (manual weight painting needed)")

        # ── Parent rigid head parts ──
        print("\n  Parenting head-attached parts...")
        for part_name in rigid_head_parts:
            obj = bpy.data.objects.get(part_name)
            if obj is None:
                print(f"    SKIP: {part_name} not found")
                continue

            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(True)
            rig.select_set(True)
            bpy.context.view_layer.objects.active = rig
            rig.data.bones.active = rig.data.bones[head_bone]
            bpy.ops.object.parent_set(type='BONE')
            print(f"    {part_name} -> {head_bone}")

        # ── Parent rigid body parts ──
        print("\n  Parenting body-attached rigid parts...")
        for part_name, bone_name in rigid_bone_map.items():
            obj = bpy.data.objects.get(part_name)
            if obj is None:
                print(f"    SKIP: {part_name} not found")
                continue
            if bone_name is None or bone_name not in rig.data.bones:
                print(f"    SKIP: {part_name} - bone {bone_name} not found")
                continue

            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(True)
            rig.select_set(True)
            bpy.context.view_layer.objects.active = rig
            rig.data.bones.active = rig.data.bones[bone_name]
            bpy.ops.object.parent_set(type='BONE')
            print(f"    {part_name} -> {bone_name}")

    # ── Step 6: Save ────────────────────────────────────────────
    print(f"\n[6/6] Saving to {OUTPUT_FILE}")

    remaining_meshes = set(o.name for o in bpy.data.objects if o.type == 'MESH')
    missing = original_meshes - remaining_meshes
    if missing:
        print(f"  WARNING: Missing meshes: {missing}")
    else:
        print(f"  All {len(original_meshes)} mesh parts preserved")

    mia_mats = [m for m in bpy.data.materials if m.name.startswith('Mia_')]
    print(f"  Materials preserved: {len(mia_mats)}")

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=OUTPUT_FILE)
    print(f"  Saved!")

    print("\n" + "=" * 60)
    print("RIGGING COMPLETE")
    print("=" * 60)

    bpy.ops.wm.quit_blender()
    return None


# Register timer to run after GUI initialization
bpy.app.timers.register(run_rigging, first_interval=1.5)
