#!/usr/bin/env python3
"""
Rigging Pipeline for Fairy Dinosaur Date Night
===============================================
Automates the character rigging workflow:
  1. Take AI-generated 3D model (from Tripo/Meshy/Rodin)
  2. Auto-rig via AccuRIG or Mixamo API
  3. Import into Blender
  4. Run quality checks
  5. Apply cleanup fixes
  6. Export production-ready FBX/GLB

Usage:
  # Inside Blender (for import + cleanup):
  blender --background --python scripts/rigging_pipeline.py -- \\
      --model character.glb \\
      --method accurig \\
      --character-type hero \\
      --output character_rigged.fbx

  # Standalone (for pipeline overview):
  python scripts/rigging_pipeline.py --help

Dependencies:
  - Blender 4.0+ (for bone collections)
  - AccuRIG 2 (free) or Mixamo account
  - rig_quality_checker.py (in same directory)
"""

import argparse
import os
import sys
import json
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class CharacterType(Enum):
    HERO = "hero"           # Mia, Leo, Ruben, Jetplane - full rig + cleanup
    SUPPORTING = "supporting"  # Gabe, Nina - auto-rig + basic cleanup
    BACKGROUND = "background"  # Extras - auto-rig only
    QUADRUPED = "quadruped"    # Jetplane - special quadruped pipeline


class RiggingMethod(Enum):
    ACCURIG = "accurig"       # Best for stylized characters
    MIXAMO = "mixamo"         # Best for quick + animation library
    RIGIFY = "rigify"         # Best for full custom control
    AUTO_RIG_PRO = "arp"      # Best for game export
    TRIPO = "tripo"           # Use if model came from Tripo
    MESHY = "meshy"           # Use if model came from Meshy
    CASCADEUR = "cascadeur"   # Use for physics-based animation


@dataclass
class RiggingConfig:
    """Configuration for the rigging pipeline."""
    model_path: str
    output_path: str
    character_name: str = ""
    character_type: CharacterType = CharacterType.SUPPORTING
    rigging_method: RiggingMethod = RiggingMethod.ACCURIG
    add_ik: bool = True
    add_facial: bool = False
    fix_weights: bool = True
    add_rotation_limits: bool = True
    target_bone_count: int = 75  # Game-optimized default
    export_format: str = "fbx"   # fbx or glb

    @classmethod
    def for_character(cls, name: str, model_path: str, output_path: str):
        """Create config preset based on character name."""
        presets = {
            "mia": cls(
                model_path=model_path,
                output_path=output_path,
                character_name="Mia",
                character_type=CharacterType.HERO,
                rigging_method=RiggingMethod.ACCURIG,
                add_ik=True,
                add_facial=True,
                fix_weights=True,
                add_rotation_limits=True,
                target_bone_count=120,
            ),
            "leo": cls(
                model_path=model_path,
                output_path=output_path,
                character_name="Leo",
                character_type=CharacterType.HERO,
                rigging_method=RiggingMethod.ACCURIG,
                add_ik=True,
                add_facial=True,
                fix_weights=True,
                add_rotation_limits=True,
                target_bone_count=120,
            ),
            "ruben": cls(
                model_path=model_path,
                output_path=output_path,
                character_name="Ruben",
                character_type=CharacterType.HERO,
                rigging_method=RiggingMethod.ACCURIG,
                add_ik=True,
                add_facial=True,
                fix_weights=True,
                add_rotation_limits=True,
                target_bone_count=150,  # More complex due to fairy wings
            ),
            "jetplane": cls(
                model_path=model_path,
                output_path=output_path,
                character_name="Jetplane",
                character_type=CharacterType.QUADRUPED,
                rigging_method=RiggingMethod.ACCURIG,
                add_ik=True,
                add_facial=True,  # Jaw for expressions
                fix_weights=True,
                add_rotation_limits=True,
                target_bone_count=100,
            ),
            "gabe": cls(
                model_path=model_path,
                output_path=output_path,
                character_name="Gabe",
                character_type=CharacterType.SUPPORTING,
                rigging_method=RiggingMethod.MIXAMO,
                add_ik=False,
                add_facial=False,
                fix_weights=True,
                add_rotation_limits=False,
                target_bone_count=65,
            ),
            "nina": cls(
                model_path=model_path,
                output_path=output_path,
                character_name="Nina",
                character_type=CharacterType.SUPPORTING,
                rigging_method=RiggingMethod.MIXAMO,
                add_ik=False,
                add_facial=False,
                fix_weights=True,
                add_rotation_limits=False,
                target_bone_count=65,
            ),
        }
        key = name.lower()
        if key in presets:
            return presets[key]
        return cls(
            model_path=model_path,
            output_path=output_path,
            character_name=name,
        )


# ---- Blender Pipeline Steps ----

def step_import_model(config: RiggingConfig):
    """Step 1: Import the 3D model into Blender."""
    import bpy

    # Clear scene
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

    ext = os.path.splitext(config.model_path)[1].lower()
    if ext == ".fbx":
        bpy.ops.import_scene.fbx(filepath=config.model_path)
    elif ext in (".glb", ".gltf"):
        bpy.ops.import_scene.gltf(filepath=config.model_path)
    elif ext == ".obj":
        bpy.ops.wm.obj_import(filepath=config.model_path)
    else:
        raise ValueError(f"Unsupported format: {ext}")

    print(f"Imported: {config.model_path}")
    print(f"Objects in scene: {len(bpy.context.scene.objects)}")


def step_check_existing_rig(config: RiggingConfig):
    """Step 2: Check if model already has a rig."""
    import bpy

    armatures = [obj for obj in bpy.context.scene.objects if obj.type == 'ARMATURE']
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']

    if armatures:
        arm = armatures[0]
        print(f"Existing rig found: {arm.name} ({len(arm.data.bones)} bones)")
        return True
    else:
        print("No existing rig found. Model needs rigging.")
        return False


def step_apply_rigify(config: RiggingConfig):
    """Step 3a: Apply Rigify metarig to the character."""
    import bpy

    # Get the mesh
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']
    if not meshes:
        raise RuntimeError("No mesh found in scene")

    mesh = meshes[0]

    # Add human metarig
    bpy.ops.object.armature_human_metarig_add()
    metarig = bpy.context.active_object

    # Scale metarig to match mesh dimensions
    mesh_dims = mesh.dimensions
    meta_dims = metarig.dimensions

    if meta_dims.z > 0:
        scale_factor = mesh_dims.z / meta_dims.z
        metarig.scale = (scale_factor, scale_factor, scale_factor)
        bpy.ops.object.transform_apply(scale=True)

    print(f"Rigify metarig added and scaled (factor: {scale_factor:.2f})")
    print("NOTE: Manual adjustment of metarig bones is recommended")
    print("      before generating the final rig.")

    return metarig


def step_fix_weights(config: RiggingConfig):
    """Step 4: Fix common weight painting issues."""
    import bpy

    meshes = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']
    if not meshes:
        return

    for mesh in meshes:
        if not mesh.vertex_groups:
            continue

        # Normalize all weights
        bpy.context.view_layer.objects.active = mesh
        bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
        bpy.ops.object.vertex_group_normalize_all()
        bpy.ops.object.mode_set(mode='OBJECT')

        # Limit total influences to 4 (game engine compatibility)
        bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
        bpy.ops.object.vertex_group_limit_total(limit=4)
        bpy.ops.object.mode_set(mode='OBJECT')

        # Clean up zero-weight groups
        bpy.ops.object.vertex_group_clean(group_select_mode='ALL', limit=0.01)

        print(f"Weight fixes applied to: {mesh.name}")
        print("  - Normalized all weights")
        print("  - Limited to 4 influences per vertex")
        print("  - Cleaned zero-weight groups")


def step_add_ik_constraints(config: RiggingConfig):
    """Step 5: Add IK constraints to arms and legs."""
    import bpy

    armatures = [obj for obj in bpy.context.scene.objects if obj.type == 'ARMATURE']
    if not armatures:
        return

    armature = armatures[0]
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='POSE')

    # Common IK target bones
    ik_targets = {
        "hand": ["hand.L", "hand.R", "Hand_L", "Hand_R",
                 "mixamorig:LeftHand", "mixamorig:RightHand"],
        "foot": ["foot.L", "foot.R", "Foot_L", "Foot_R",
                 "mixamorig:LeftFoot", "mixamorig:RightFoot"],
    }

    ik_added = 0
    for bone_type, names in ik_targets.items():
        for name in names:
            if name in armature.pose.bones:
                pbone = armature.pose.bones[name]
                # Check if IK already exists
                has_ik = any(c.type == 'IK' for c in pbone.constraints)
                if not has_ik:
                    ik = pbone.constraints.new('IK')
                    ik.chain_count = 2  # 2-bone chain (upper + lower limb)
                    ik_added += 1
                    print(f"  Added IK constraint to: {name}")

    bpy.ops.object.mode_set(mode='OBJECT')
    print(f"IK constraints added: {ik_added}")


def step_add_rotation_limits(config: RiggingConfig):
    """Step 6: Add rotation limits to prevent impossible poses."""
    import bpy
    import math

    armatures = [obj for obj in bpy.context.scene.objects if obj.type == 'ARMATURE']
    if not armatures:
        return

    armature = armatures[0]
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='POSE')

    # Joint limits (in degrees) - based on human anatomy
    joint_limits = {
        "elbow": {
            "names": ["forearm.L", "forearm.R", "Forearm_L", "Forearm_R",
                      "mixamorig:LeftForeArm", "mixamorig:RightForeArm"],
            "min_x": -5, "max_x": 150,
            "min_y": -90, "max_y": 90,
            "min_z": -10, "max_z": 10,
        },
        "knee": {
            "names": ["shin.L", "shin.R", "Shin_L", "Shin_R",
                      "mixamorig:LeftLeg", "mixamorig:RightLeg"],
            "min_x": -5, "max_x": 150,
            "min_y": -10, "max_y": 10,
            "min_z": -10, "max_z": 10,
        },
        "head": {
            "names": ["head", "Head", "mixamorig:Head"],
            "min_x": -45, "max_x": 45,
            "min_y": -80, "max_y": 80,
            "min_z": -45, "max_z": 45,
        },
    }

    limits_added = 0
    for joint_type, data in joint_limits.items():
        for name in data["names"]:
            if name in armature.pose.bones:
                pbone = armature.pose.bones[name]
                # Check if limit already exists
                has_limit = any(c.type == 'LIMIT_ROTATION' for c in pbone.constraints)
                if not has_limit:
                    limit = pbone.constraints.new('LIMIT_ROTATION')
                    limit.use_limit_x = True
                    limit.min_x = math.radians(data["min_x"])
                    limit.max_x = math.radians(data["max_x"])
                    limit.use_limit_y = True
                    limit.min_y = math.radians(data["min_y"])
                    limit.max_y = math.radians(data["max_y"])
                    limit.use_limit_z = True
                    limit.min_z = math.radians(data["min_z"])
                    limit.max_z = math.radians(data["max_z"])
                    limit.owner_space = 'LOCAL'
                    limits_added += 1
                    print(f"  Added rotation limits to: {name}")

    bpy.ops.object.mode_set(mode='OBJECT')
    print(f"Rotation limits added: {limits_added}")


def step_export(config: RiggingConfig):
    """Step 7: Export the rigged character."""
    import bpy

    output = config.output_path
    ext = os.path.splitext(output)[1].lower()

    if ext == ".fbx":
        bpy.ops.export_scene.fbx(
            filepath=output,
            use_selection=False,
            add_leaf_bones=False,
            bake_anim=False,
            path_mode='COPY',
            embed_textures=True,
        )
    elif ext in (".glb", ".gltf"):
        bpy.ops.export_scene.gltf(
            filepath=output,
            export_format='GLB' if ext == ".glb" else 'GLTF_SEPARATE',
        )
    else:
        raise ValueError(f"Unsupported export format: {ext}")

    print(f"Exported: {output}")


def run_pipeline(config: RiggingConfig):
    """Run the complete rigging pipeline inside Blender."""
    import bpy

    print(f"\n{'='*60}")
    print(f"  RIGGING PIPELINE: {config.character_name}")
    print(f"  Type: {config.character_type.value}")
    print(f"  Method: {config.rigging_method.value}")
    print(f"{'='*60}\n")

    # Step 1: Import
    print("\n--- Step 1: Import Model ---")
    step_import_model(config)

    # Step 2: Check existing rig
    print("\n--- Step 2: Check Existing Rig ---")
    has_rig = step_check_existing_rig(config)

    # Step 3: Apply rig if needed
    if not has_rig and config.rigging_method == RiggingMethod.RIGIFY:
        print("\n--- Step 3: Apply Rigify ---")
        step_apply_rigify(config)
    elif not has_rig:
        print("\n--- Step 3: No rig found ---")
        print(f"Model needs to be rigged externally with {config.rigging_method.value}")
        print("Recommended workflow:")
        if config.rigging_method == RiggingMethod.ACCURIG:
            print("  1. Open AccuRIG 2 (free download from reallusion.com)")
            print("  2. Import your model")
            print("  3. Place markers on joints (5 steps)")
            print("  4. Export as FBX")
            print("  5. Re-run this pipeline with the rigged FBX")
        elif config.rigging_method == RiggingMethod.MIXAMO:
            print("  1. Go to mixamo.com")
            print("  2. Upload your model")
            print("  3. Auto-rig (place markers)")
            print("  4. Optionally apply an animation")
            print("  5. Download as FBX")
            print("  6. Re-run this pipeline with the rigged FBX")
        return

    # Step 4: Fix weights
    if config.fix_weights and has_rig:
        print("\n--- Step 4: Fix Weight Painting ---")
        step_fix_weights(config)

    # Step 5: Add IK
    if config.add_ik and has_rig:
        print("\n--- Step 5: Add IK Constraints ---")
        step_add_ik_constraints(config)

    # Step 6: Add rotation limits
    if config.add_rotation_limits and has_rig:
        print("\n--- Step 6: Add Rotation Limits ---")
        step_add_rotation_limits(config)

    # Step 7: Run quality checks
    print("\n--- Step 7: Quality Check ---")
    try:
        # Import the quality checker from the same directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, script_dir)
        from rig_quality_checker import run_blender_checks

        armatures = [obj for obj in bpy.context.scene.objects if obj.type == 'ARMATURE']
        meshes = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']

        if armatures:
            arm = armatures[0]
            mesh = None
            for m in meshes:
                if m.parent == arm:
                    mesh = m
                    break
            if not mesh and meshes:
                mesh = meshes[0]

            report = run_blender_checks(arm, mesh)
            print(report.summary())
    except Exception as e:
        print(f"Quality check error: {e}")

    # Step 8: Export
    if config.output_path:
        print(f"\n--- Step 8: Export ({config.export_format}) ---")
        step_export(config)

    print(f"\n{'='*60}")
    print(f"  PIPELINE COMPLETE: {config.character_name}")
    print(f"{'='*60}\n")


# ---- CLI ----

def main():
    parser = argparse.ArgumentParser(
        description="Character Rigging Pipeline for Fairy Dinosaur Date Night"
    )
    parser.add_argument("--model", help="Path to 3D model file (FBX/GLB/OBJ)")
    parser.add_argument("--output", help="Output path for rigged model")
    parser.add_argument("--character", help="Character name (mia/leo/ruben/jetplane/gabe/nina)")
    parser.add_argument("--method", choices=[m.value for m in RiggingMethod],
                        default="accurig", help="Rigging method")
    parser.add_argument("--character-type", choices=[t.value for t in CharacterType],
                        default="supporting", help="Character importance level")
    parser.add_argument("--no-ik", action="store_true", help="Skip IK constraint setup")
    parser.add_argument("--no-weights", action="store_true", help="Skip weight fixing")
    parser.add_argument("--no-limits", action="store_true", help="Skip rotation limits")
    parser.add_argument("--facial", action="store_true", help="Add facial controls")
    parser.add_argument("--guide", action="store_true", help="Print rigging guide")

    # Handle Blender's argument passing
    argv = sys.argv
    if "--" in argv:
        args = parser.parse_args(argv[argv.index("--") + 1:])
    else:
        args = parser.parse_args()

    if args.guide:
        try:
            from rig_quality_checker import print_rigging_guide
            print_rigging_guide()
        except ImportError:
            print("Run inside the scripts directory or pass --guide from Blender")
        return

    if not args.model:
        parser.print_help()
        print("\nExample usage:")
        print("  blender --background --python scripts/rigging_pipeline.py -- \\")
        print("      --model characters/mia.glb --character mia --output mia_rigged.fbx")
        return

    # Build config
    if args.character:
        config = RiggingConfig.for_character(
            args.character, args.model,
            args.output or args.model.replace(".", "_rigged.")
        )
    else:
        config = RiggingConfig(
            model_path=args.model,
            output_path=args.output or args.model.replace(".", "_rigged."),
            character_type=CharacterType(args.character_type),
            rigging_method=RiggingMethod(args.method),
        )

    # Apply CLI overrides
    if args.no_ik:
        config.add_ik = False
    if args.no_weights:
        config.fix_weights = False
    if args.no_limits:
        config.add_rotation_limits = False
    if args.facial:
        config.add_facial = True

    try:
        import bpy
        run_pipeline(config)
    except ImportError:
        print("This script must be run inside Blender for the full pipeline.")
        print(f"Run: blender --background --python {__file__} -- --model {args.model}")


if __name__ == "__main__":
    main()
