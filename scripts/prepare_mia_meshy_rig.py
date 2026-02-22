"""
Prepare Mia's Meshy-rigged v2 model for stress testing.

This script:
1. Imports the Meshy-rigged v2 GLB (with proper weights + ponytail bones)
2. Removes stray objects (Icosphere)
3. Re-applies rotation constraints (GLTF doesn't preserve them)
4. Saves as a clean .blend file ready for stress testing

Run: xvfb-run blender --background --python scripts/prepare_mia_meshy_rig.py
"""
import bpy
import math

WORK_DIR = "/home/rex/rex-marks-the-spot/.task-worktrees/263-fix-rig-mia-with-accurigmixamo-proper-de"
GLB_PATH = f"{WORK_DIR}/tmp/mia_rigged_v2.glb"
OUTPUT_BLEND = f"{WORK_DIR}/models/characters/mia_meshy_rigged.blend"


def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    for collection in bpy.data.collections:
        bpy.data.collections.remove(collection)


def import_model():
    print("Importing Meshy-rigged v2 GLB...")
    bpy.ops.import_scene.gltf(filepath=GLB_PATH)
    print(f"  Objects: {[obj.name for obj in bpy.data.objects]}")


def cleanup():
    """Remove stray objects like Icosphere."""
    to_remove = []
    for obj in bpy.data.objects:
        if obj.type == 'MESH' and not any(m.type == 'ARMATURE' for m in obj.modifiers):
            if obj.name != "char1":
                to_remove.append(obj)
    removed_names = [obj.name for obj in to_remove]
    for obj in to_remove:
        bpy.data.objects.remove(obj, do_unlink=True)
    if removed_names:
        print(f"  Removed stray objects: {removed_names}")


def apply_constraints(armature):
    """Re-apply rotation constraints from the v2 rig report.

    These constraints prevent extreme poses and add secondary motion.
    GLTF format does not preserve Blender constraints, so we re-create them.
    """
    print("Applying rotation constraints...")

    def add_limit_rotation(bone_name, x_range=None, y_range=None, z_range=None):
        if bone_name not in armature.pose.bones:
            print(f"  WARNING: Bone '{bone_name}' not found, skipping constraint")
            return
        pbone = armature.pose.bones[bone_name]
        c = pbone.constraints.new('LIMIT_ROTATION')
        c.name = f"Limit_{bone_name}"
        c.owner_space = 'LOCAL'
        if x_range:
            c.use_limit_x = True
            c.min_x = math.radians(x_range[0])
            c.max_x = math.radians(x_range[1])
        if y_range:
            c.use_limit_y = True
            c.min_y = math.radians(y_range[0])
            c.max_y = math.radians(y_range[1])
        if z_range:
            c.use_limit_z = True
            c.min_z = math.radians(z_range[0])
            c.max_z = math.radians(z_range[1])

    def add_copy_rotation(bone_name, target_bone, influence, invert_y=False, invert_z=False):
        if bone_name not in armature.pose.bones:
            print(f"  WARNING: Bone '{bone_name}' not found, skipping constraint")
            return
        pbone = armature.pose.bones[bone_name]
        c = pbone.constraints.new('COPY_ROTATION')
        c.name = f"{bone_name}_CounterRotation"
        c.target = armature
        c.subtarget = target_bone
        c.influence = influence
        c.invert_y = invert_y
        c.invert_z = invert_z
        c.mix_mode = 'ADD'

    # Leg limits
    add_limit_rotation("LeftUpLeg", x_range=(-30, 120), y_range=(-45, 45), z_range=(-60, 30))
    add_limit_rotation("LeftLeg", x_range=(-5, 150), y_range=(-10, 10), z_range=(-10, 10))
    add_limit_rotation("RightUpLeg", x_range=(-30, 120), y_range=(-45, 45), z_range=(-30, 60))
    add_limit_rotation("RightLeg", x_range=(-5, 150), y_range=(-10, 10), z_range=(-10, 10))

    # Shoulder limits
    add_limit_rotation("LeftShoulder", x_range=(-20, 20), y_range=(-15, 15), z_range=(-15, 15))
    add_limit_rotation("RightShoulder", x_range=(-20, 20), y_range=(-15, 15), z_range=(-15, 15))

    # Arm limits
    add_limit_rotation("LeftArm", x_range=(-50, 90), y_range=(-45, 45), z_range=(-30, 90))
    add_limit_rotation("LeftForeArm", x_range=(-5, 150), y_range=(-90, 90), z_range=(-10, 10))
    add_limit_rotation("RightArm", x_range=(-50, 90), y_range=(-45, 45), z_range=(-90, 30))
    add_limit_rotation("RightForeArm", x_range=(-5, 150), y_range=(-90, 90), z_range=(-10, 10))

    # Spine counter-rotation for natural walk motion
    add_copy_rotation("Spine", "Hips", influence=0.35, invert_y=True, invert_z=True)
    add_copy_rotation("Spine01", "Hips", influence=0.175, invert_y=True, invert_z=True)

    # Ponytail secondary motion
    ponytail_bones = ["Ponytail_01", "Ponytail_02", "Ponytail_03", "Ponytail_04"]
    ponytail_influence = [0.4, 0.3, 0.2, 0.1]
    ponytail_limits = [
        ((-45, 45), (-30, 30), (-40, 40)),
        ((-55, 55), (-35, 35), (-48, 48)),
        ((-65, 65), (-40, 40), (-56, 56)),
        ((-75, 75), (-45, 45), (-64, 64)),
    ]

    for bone_name, influence, (x_lim, y_lim, z_lim) in zip(
        ponytail_bones, ponytail_influence, ponytail_limits
    ):
        if bone_name not in armature.pose.bones:
            continue
        # Follow head rotation
        pbone = armature.pose.bones[bone_name]
        c = pbone.constraints.new('COPY_ROTATION')
        c.name = "Ponytail_Follow"
        c.target = armature
        c.subtarget = "Head"
        c.influence = influence
        c.mix_mode = 'ADD'
        # Limit rotation range
        add_limit_rotation(bone_name, x_range=x_lim, y_range=y_lim, z_range=z_lim)

    # Count constraints
    total = sum(len(pb.constraints) for pb in armature.pose.bones)
    print(f"  Applied {total} constraints to armature")


def verify_model():
    """Print verification summary."""
    armature = None
    mesh = None
    for obj in bpy.data.objects:
        if obj.type == 'ARMATURE':
            armature = obj
        elif obj.type == 'MESH' and any(m.type == 'ARMATURE' for m in obj.modifiers):
            mesh = obj

    if not armature or not mesh:
        print("ERROR: Missing armature or mesh!")
        return False

    print("\n=== VERIFICATION ===")
    print(f"Armature: {armature.name} ({len(armature.data.bones)} bones)")
    print(f"Mesh: {mesh.name} ({len(mesh.data.vertices)} vertices, {len(mesh.data.polygons)} faces)")
    print(f"Vertex groups: {len(mesh.vertex_groups)}")

    # Weight coverage
    unweighted = sum(1 for v in mesh.data.vertices if len(v.groups) == 0)
    coverage = (1 - unweighted / max(len(mesh.data.vertices), 1)) * 100
    print(f"Weight coverage: {coverage:.1f}% ({unweighted} unweighted)")

    # Bone list
    print(f"Bones: {[b.name for b in armature.data.bones]}")

    # Constraint count per bone
    for pbone in armature.pose.bones:
        if pbone.constraints:
            print(f"  {pbone.name}: {len(pbone.constraints)} constraints")

    return True


def main():
    clear_scene()
    import_model()
    cleanup()

    armature = None
    for obj in bpy.data.objects:
        if obj.type == 'ARMATURE':
            armature = obj
            break

    if not armature:
        print("ERROR: No armature found after import!")
        return

    apply_constraints(armature)

    if verify_model():
        bpy.ops.wm.save_as_mainfile(filepath=OUTPUT_BLEND)
        print(f"\nSaved to: {OUTPUT_BLEND}")
    else:
        print("Verification failed, not saving.")


if __name__ == "__main__":
    main()
