"""
Rig Mia using Blender's Rigify system.

Usage:
    blender models/characters/mia.blend --background --python scripts/blender/rig_mia_rigify.py

This script:
1. Prepares the mesh (subdivide body parts, join deformable meshes)
2. Creates a Rigify human metarig positioned to fit Mia
3. Generates the full rig
4. Parents body mesh with automatic weights
5. Rigidly parents hair/accessories to appropriate bones
6. Saves the result
"""

import bpy
import math
import mathutils
import sys

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Body parts to join into one deformable mesh
BODY_PARTS = [
    "Mia_Head",
    "Mia_Torso",
    "Mia_UpperArm_L", "Mia_LowerArm_L", "Mia_Hand_L",
    "Mia_UpperArm_R", "Mia_LowerArm_R", "Mia_Hand_R",
    "Mia_Shorts",
    "Mia_UpperLeg_L", "Mia_LowerLeg_L",
    "Mia_UpperLeg_R", "Mia_LowerLeg_R",
    "Mia_Nose", "Mia_Mouth",
]

# Parts to rigidly parent to the head bone
HEAD_RIGID_PARTS = [
    "Mia_Hair_Base", "Mia_Ponytail", "Mia_Ponytail_End", "Mia_Scrunchie",
    "Mia_Eye_L", "Mia_Iris_L", "Mia_Pupil_L",
    "Mia_Eye_R", "Mia_Iris_R", "Mia_Pupil_R",
]

# Parts to rigidly parent to the chest/spine bone
CHEST_RIGID_PARTS = [
    "Mia_Shirt_Star",
]

# Shoes - rigidly parent to foot bones
LEFT_FOOT_PARTS = ["Mia_Shoe_L", "Mia_Shoe_Sole_L"]
RIGHT_FOOT_PARTS = ["Mia_Shoe_R", "Mia_Shoe_Sole_R"]

# Spine chain joints - must be continuous (each head = previous tail)
# Measured from model bounding boxes
SPINE_JOINTS = [
    (0, 0.02, 0.57),   # spine head (hips)
    (0, 0.01, 0.67),   # spine.001 head (lower back)
    (0, 0.00, 0.78),   # spine.002 head (mid back)
    (0, -0.01, 0.88),  # spine.003 head (upper back)
    (0, -0.01, 0.94),  # spine.004 head (neck base) = spine.003 tail
    (0, -0.01, 1.02),  # spine.005 head (neck top) = spine.004 tail
    (0, -0.01, 1.10),  # spine.006 head (head) = spine.005 tail
    (0, -0.01, 1.27),  # spine.006 tail (head top)
]

# Non-chain bone positions
LIMB_POSITIONS = {
    # Left arm (slight -Y offset at elbow for IK pole vector)
    "shoulder.L": {"head": (-0.04, -0.01, 0.94), "tail": (-0.10, -0.01, 0.94)},
    "upper_arm.L": {"head": (-0.10, 0, 0.94), "tail": (-0.114, 0.02, 0.80)},
    "forearm.L": {"head": (-0.114, 0.02, 0.80), "tail": (-0.114, 0, 0.71)},
    "hand.L": {"head": (-0.114, 0, 0.71), "tail": (-0.114, 0, 0.64)},

    # Right arm (slight -Y offset at elbow for IK pole vector)
    "shoulder.R": {"head": (0.04, -0.01, 0.94), "tail": (0.10, -0.01, 0.94)},
    "upper_arm.R": {"head": (0.10, 0, 0.94), "tail": (0.114, 0.02, 0.80)},
    "forearm.R": {"head": (0.114, 0.02, 0.80), "tail": (0.114, 0, 0.71)},
    "hand.R": {"head": (0.114, 0, 0.71), "tail": (0.114, 0, 0.64)},

    # Left leg (slight +Y offset at knee for IK pole vector)
    "thigh.L": {"head": (-0.051, 0, 0.57), "tail": (-0.051, -0.02, 0.39)},
    "shin.L": {"head": (-0.051, -0.02, 0.39), "tail": (-0.051, 0, 0.11)},
    "foot.L": {"head": (-0.051, 0, 0.11), "tail": (-0.051, 0.04, 0.07)},
    "toe.L": {"head": (-0.051, 0.04, 0.07), "tail": (-0.051, 0.065, 0.065)},

    # Right leg (slight +Y offset at knee for IK pole vector)
    "thigh.R": {"head": (0.051, 0, 0.57), "tail": (0.051, -0.02, 0.39)},
    "shin.R": {"head": (0.051, -0.02, 0.39), "tail": (0.051, 0, 0.11)},
    "foot.R": {"head": (0.051, 0, 0.11), "tail": (0.051, 0.04, 0.07)},
    "toe.R": {"head": (0.051, 0.04, 0.07), "tail": (0.051, 0.065, 0.065)},
}


def ensure_object_mode():
    """Ensure we're in object mode."""
    if bpy.context.active_object and bpy.context.active_object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')


def deselect_all():
    bpy.ops.object.select_all(action='DESELECT')


def select_object(obj, active=True):
    obj.select_set(True)
    if active:
        bpy.context.view_layer.objects.active = obj


def subdivide_mesh(obj, levels=1):
    """Add subdivision to increase geometry for better deformation."""
    deselect_all()
    select_object(obj)
    mod = obj.modifiers.new(name="Subdivide", type='SUBSURF')
    mod.levels = levels
    mod.render_levels = levels
    bpy.ops.object.modifier_apply(modifier=mod.name)
    print(f"  Subdivided {obj.name}: now {len(obj.data.vertices)} verts")


def join_meshes(mesh_names, result_name="Mia_Body"):
    """Join named meshes into one object."""
    ensure_object_mode()
    deselect_all()

    objects_to_join = []
    for name in mesh_names:
        obj = bpy.data.objects.get(name)
        if obj and obj.type == 'MESH':
            objects_to_join.append(obj)
        else:
            print(f"  WARNING: {name} not found or not a mesh")

    if not objects_to_join:
        print("ERROR: No meshes to join!")
        return None

    # Unparent all objects first (keep transform)
    for obj in objects_to_join:
        deselect_all()
        select_object(obj)
        bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')

    # Select all and join
    deselect_all()
    for obj in objects_to_join:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects_to_join[0]
    bpy.ops.object.join()

    result = bpy.context.active_object
    result.name = result_name
    print(f"  Joined into {result_name}: {len(result.data.vertices)} verts, {len(result.data.polygons)} faces")
    return result


def fix_mesh(obj):
    """Clean up mesh - recalculate normals, remove doubles."""
    deselect_all()
    select_object(obj)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')

    # Remove doubles
    bpy.ops.mesh.remove_doubles(threshold=0.0001)

    # Recalculate normals
    bpy.ops.mesh.normals_make_consistent(inside=False)

    bpy.ops.object.mode_set(mode='OBJECT')
    print(f"  Fixed mesh {obj.name}: {len(obj.data.vertices)} verts")


def create_metarig():
    """Create a Rigify human metarig and position bones to fit Mia."""
    print("\n=== Creating Rigify Metarig ===")

    # Enable Rigify addon
    bpy.ops.preferences.addon_enable(module="rigify")

    ensure_object_mode()
    deselect_all()

    # Add human metarig
    bpy.ops.object.armature_human_metarig_add()
    metarig = bpy.context.active_object
    metarig.name = "Mia_Metarig"
    print(f"  Created metarig with {len(metarig.data.bones)} bones")

    # Position the metarig bones
    bpy.ops.object.mode_set(mode='EDIT')

    positioned = 0

    # Position spine chain - must be continuous
    spine_names = ["spine", "spine.001", "spine.002", "spine.003",
                   "spine.004", "spine.005", "spine.006"]
    for i, bone_name in enumerate(spine_names):
        bone = metarig.data.edit_bones.get(bone_name)
        if bone:
            bone.head = mathutils.Vector(SPINE_JOINTS[i])
            bone.tail = mathutils.Vector(SPINE_JOINTS[i + 1])
            positioned += 1
        else:
            print(f"  WARNING: Spine bone '{bone_name}' not found")

    # Position limb bones
    for bone_name, positions in LIMB_POSITIONS.items():
        bone = metarig.data.edit_bones.get(bone_name)
        if bone:
            bone.head = mathutils.Vector(positions["head"])
            bone.tail = mathutils.Vector(positions["tail"])
            positioned += 1
        else:
            print(f"  WARNING: Limb bone '{bone_name}' not found")

    # Ensure arm/leg chains are connected
    for chain in [
        ["upper_arm.L", "forearm.L", "hand.L"],
        ["upper_arm.R", "forearm.R", "hand.R"],
        ["thigh.L", "shin.L", "foot.L", "toe.L"],
        ["thigh.R", "shin.R", "foot.R", "toe.R"],
    ]:
        for j in range(1, len(chain)):
            prev = metarig.data.edit_bones.get(chain[j-1])
            curr = metarig.data.edit_bones.get(chain[j])
            if prev and curr:
                curr.head = prev.tail.copy()

    print(f"  Positioned {positioned} bones")

    # Scale finger bones relative to hand position (they're tiny on this model)
    # Just scale them down to fit the hand size
    hand_bones_l = [b for b in metarig.data.edit_bones
                    if '.L' in b.name and ('f_' in b.name or 'thumb' in b.name or 'palm' in b.name)]
    hand_bones_r = [b for b in metarig.data.edit_bones
                    if '.R' in b.name and ('f_' in b.name or 'thumb' in b.name or 'palm' in b.name)]

    # Get hand bone for reference
    hand_l = metarig.data.edit_bones.get("hand.L")
    hand_r = metarig.data.edit_bones.get("hand.R")

    if hand_l:
        # Scale finger chain to fit our small hand
        for bone in hand_bones_l:
            # Move fingers to be within hand bounds
            offset = bone.head - hand_l.head
            scale = 0.3  # Fingers are small relative to default metarig
            bone.head = hand_l.head + offset * scale
            bone.tail = hand_l.head + (bone.tail - hand_l.head) * scale

    if hand_r:
        for bone in hand_bones_r:
            offset = bone.head - hand_r.head
            scale = 0.3
            bone.head = hand_r.head + offset * scale
            bone.tail = hand_r.head + (bone.tail - hand_r.head) * scale

    # Remove face bones to simplify initial rig (can add back later)
    # Face rig needs careful positioning for our stylized character
    face_bone = metarig.data.edit_bones.get("face")
    if face_bone:
        # Delete face bone and all its children recursively
        face_bones = [face_bone]
        # Collect all descendants
        def collect_children(bone):
            for child in bone.children:
                face_bones.append(child)
                collect_children(child)
        collect_children(face_bone)
        for fb in face_bones:
            metarig.data.edit_bones.remove(fb)
        print(f"  Removed {len(face_bones)} face bones (simplified rig)")

    bpy.ops.object.mode_set(mode='OBJECT')
    return metarig


def generate_rig(metarig):
    """Generate the Rigify rig from the metarig."""
    print("\n=== Generating Rigify Rig ===")

    ensure_object_mode()
    deselect_all()
    select_object(metarig)

    # Generate the rig
    bpy.ops.pose.rigify_generate()

    # Find the generated rig
    rig = bpy.data.objects.get("rig")
    if rig is None:
        # Sometimes named differently
        for obj in bpy.context.scene.objects:
            if obj.type == 'ARMATURE' and obj != metarig:
                rig = obj
                break

    if rig:
        rig.name = "Mia_Rig"
        print(f"  Generated rig: {rig.name} with {len(rig.data.bones)} bones")
    else:
        print("  ERROR: Could not find generated rig!")

    return rig


def parent_with_auto_weights(mesh_obj, armature_obj):
    """Parent mesh to armature with automatic weights."""
    print(f"\n=== Parenting {mesh_obj.name} to {armature_obj.name} with auto weights ===")

    ensure_object_mode()
    deselect_all()

    # Select mesh first, then armature (armature must be active)
    mesh_obj.select_set(True)
    armature_obj.select_set(True)
    bpy.context.view_layer.objects.active = armature_obj

    # Parent with automatic weights
    bpy.ops.object.parent_set(type='ARMATURE_AUTO')

    print(f"  Parented with auto weights. Vertex groups: {len(mesh_obj.vertex_groups)}")


def parent_rigid_to_bone(obj, armature, bone_name):
    """Rigidly parent an object to a specific bone."""
    ensure_object_mode()

    # Find the deform bone name - Rigify DEF- bones
    # Try variations
    bone_candidates = [
        f"DEF-{bone_name}",
        bone_name,
        f"DEF-{bone_name}.001",
    ]

    actual_bone = None
    for candidate in bone_candidates:
        if candidate in armature.data.bones:
            actual_bone = candidate
            break

    if actual_bone is None:
        print(f"  WARNING: Could not find bone '{bone_name}' (tried {bone_candidates}) for {obj.name}")
        # List available bones containing the key word
        key = bone_name.split('.')[0].split('-')[-1]
        matches = [b.name for b in armature.data.bones if key.lower() in b.name.lower()]
        if matches:
            print(f"    Possible matches: {matches[:5]}")
            actual_bone = matches[0]
        else:
            return

    # Clear existing parent
    deselect_all()
    select_object(obj)
    bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')

    # Parent to bone
    obj.parent = armature
    obj.parent_type = 'BONE'
    obj.parent_bone = actual_bone

    # Adjust the object's matrix to compensate for the bone parent
    # This keeps the object in its current visual position
    bone = armature.data.bones[actual_bone]
    bone_matrix = armature.matrix_world @ bone.matrix_local
    obj.matrix_parent_inverse = bone_matrix.inverted()

    print(f"  Rigidly parented {obj.name} to bone '{actual_bone}'")


def setup_rigid_parents(armature):
    """Set up rigid parenting for all accessories."""
    print("\n=== Setting Up Rigid Parents ===")

    # Head accessories (hair, eyes, etc.)
    for name in HEAD_RIGID_PARTS:
        obj = bpy.data.objects.get(name)
        if obj:
            parent_rigid_to_bone(obj, armature, "spine.006")  # Head bone

    # Chest accessories
    for name in CHEST_RIGID_PARTS:
        obj = bpy.data.objects.get(name)
        if obj:
            parent_rigid_to_bone(obj, armature, "spine.003")  # Upper spine/chest

    # Shoes
    for name in LEFT_FOOT_PARTS:
        obj = bpy.data.objects.get(name)
        if obj:
            parent_rigid_to_bone(obj, armature, "foot.L")

    for name in RIGHT_FOOT_PARTS:
        obj = bpy.data.objects.get(name)
        if obj:
            parent_rigid_to_bone(obj, armature, "foot.R")


def hide_metarig(metarig):
    """Hide the metarig to reduce clutter."""
    metarig.hide_viewport = True
    metarig.hide_render = True


def main():
    print("=" * 60)
    print("RIGGING MIA WITH RIGIFY")
    print("=" * 60)

    # Phase 1: Mesh Preparation
    print("\n=== Phase 1: Mesh Preparation ===")

    ensure_object_mode()

    # Subdivide body parts for better deformation
    print("\nSubdividing body parts...")
    for name in BODY_PARTS:
        obj = bpy.data.objects.get(name)
        if obj and obj.type == 'MESH':
            if len(obj.data.vertices) < 200:  # Only subdivide low-poly parts
                subdivide_mesh(obj, levels=1)

    # Join body parts into single mesh
    print("\nJoining body parts...")
    body = join_meshes(BODY_PARTS, "Mia_Body")
    if body is None:
        print("FATAL: Failed to join body meshes")
        sys.exit(1)

    # Fix mesh
    print("\nFixing mesh...")
    fix_mesh(body)

    # Phase 2: Create and position Rigify metarig
    metarig = create_metarig()
    if metarig is None:
        print("FATAL: Failed to create metarig")
        sys.exit(1)

    # Phase 3: Generate rig
    rig = generate_rig(metarig)
    if rig is None:
        print("FATAL: Failed to generate rig")
        sys.exit(1)

    # Phase 4: Parent body mesh to rig
    parent_with_auto_weights(body, rig)

    # Phase 5: Rigid parent accessories
    setup_rigid_parents(rig)

    # Phase 6: Clean up
    hide_metarig(metarig)

    # Remove the old empty parent if it exists
    old_parent = bpy.data.objects.get("Mia_Character")
    if old_parent:
        bpy.data.objects.remove(old_parent, do_unlink=True)

    # Save
    output_path = bpy.data.filepath.replace(".blend", "_rigged.blend")
    if not output_path or output_path == "_rigged.blend":
        output_path = "//mia_rigged.blend"
    bpy.ops.wm.save_as_mainfile(filepath=output_path)
    print(f"\n=== SAVED: {output_path} ===")

    # Print summary
    print("\n" + "=" * 60)
    print("RIGGING COMPLETE")
    print("=" * 60)
    print(f"Body mesh: {len(body.data.vertices)} vertices, {len(body.data.polygons)} faces")
    print(f"Vertex groups: {len(body.vertex_groups)}")
    print(f"Rig bones: {len(rig.data.bones)}")
    print(f"Rigid accessories: {len(HEAD_RIGID_PARTS)} head, {len(CHEST_RIGID_PARTS)} chest, "
          f"{len(LEFT_FOOT_PARTS)} L foot, {len(RIGHT_FOOT_PARTS)} R foot")


if __name__ == "__main__":
    main()
