"""
Inspect Mia's rigged model to understand bone hierarchy, positions, and constraints.
Run with: xvfb-run blender --background --python scripts/inspect_mia_rig.py
"""
import bpy
import json
import math
import sys

# Clear default scene
bpy.ops.wm.read_factory_settings(use_empty=True)

# Import the rigged GLB
glb_path = "tmp/mia_rigged.glb"
bpy.ops.import_scene.gltf(filepath=glb_path)

print("\n" + "=" * 80)
print("MIA RIG INSPECTION REPORT")
print("=" * 80)

# Find armature
armature = None
meshes = []
for obj in bpy.data.objects:
    print(f"Object: {obj.name} (type: {obj.type})")
    if obj.type == 'ARMATURE':
        armature = obj
    elif obj.type == 'MESH':
        meshes.append(obj)

if not armature:
    print("ERROR: No armature found!")
    sys.exit(1)

print(f"\nArmature: {armature.name}")
print(f"Location: {list(armature.location)}")
print(f"Scale: {list(armature.scale)}")

# Bone hierarchy and details
print("\n" + "-" * 60)
print("BONE HIERARCHY")
print("-" * 60)

def print_bone_tree(bone, depth=0):
    indent = "  " * depth
    head = [round(x, 4) for x in bone.head_local]
    tail = [round(x, 4) for x in bone.tail_local]
    length = round(bone.length, 4)
    print(f"{indent}├─ {bone.name}")
    print(f"{indent}│  head={head} tail={tail} length={length}")
    print(f"{indent}│  connected={bone.use_connect} inherit_rotation={bone.use_inherit_rotation}")
    for child in bone.children:
        print_bone_tree(child, depth + 1)

# Print from root bones
for bone in armature.data.bones:
    if bone.parent is None:
        print_bone_tree(bone)

# Check existing constraints
print("\n" + "-" * 60)
print("EXISTING CONSTRAINTS (Pose Bones)")
print("-" * 60)

bpy.context.view_layer.objects.active = armature
bpy.ops.object.mode_set(mode='POSE')

for pbone in armature.pose.bones:
    if pbone.constraints:
        print(f"\n{pbone.name}:")
        for c in pbone.constraints:
            print(f"  - {c.type}: {c.name}")
    # Also check rotation limits
    if pbone.lock_rotation[0] or pbone.lock_rotation[1] or pbone.lock_rotation[2]:
        print(f"\n{pbone.name} has locked rotations: {list(pbone.lock_rotation)}")

bpy.ops.object.mode_set(mode='OBJECT')

# Mesh info
print("\n" + "-" * 60)
print("MESH DETAILS")
print("-" * 60)

for mesh in meshes:
    print(f"\nMesh: {mesh.name}")
    print(f"  Vertices: {len(mesh.data.vertices)}")
    print(f"  Polygons: {len(mesh.data.polygons)}")
    print(f"  Materials: {len(mesh.data.materials)}")
    for i, mat in enumerate(mesh.data.materials):
        if mat:
            print(f"    [{i}] {mat.name}")

    # Vertex groups
    print(f"  Vertex Groups: {len(mesh.vertex_groups)}")
    for vg in mesh.vertex_groups:
        print(f"    - {vg.name}")

    # Modifiers
    print(f"  Modifiers: {len(mesh.modifiers)}")
    for mod in mesh.modifiers:
        print(f"    - {mod.type}: {mod.name}")

    # Check for armature modifier
    has_armature_mod = any(m.type == 'ARMATURE' for m in mesh.modifiers)
    print(f"  Has Armature Modifier: {has_armature_mod}")

# Analyze arm clipping potential
print("\n" + "-" * 60)
print("ARM CLIPPING ANALYSIS")
print("-" * 60)

bones = armature.data.bones

# Get key bone positions for analysis
left_arm = bones.get("LeftArm")
left_upleg = bones.get("LeftUpLeg")
right_arm = bones.get("RightArm")
right_upleg = bones.get("RightUpLeg")
hips = bones.get("Hips")

if left_arm and left_upleg:
    arm_head = left_arm.head_local
    leg_head = left_upleg.head_local
    dist = math.sqrt(sum((a - b) ** 2 for a, b in zip(arm_head, leg_head)))
    print(f"Left Arm to Left UpLeg distance: {dist:.4f}")
    print(f"  Arm head: {[round(x, 4) for x in arm_head]}")
    print(f"  UpLeg head: {[round(x, 4) for x in leg_head]}")

if right_arm and right_upleg:
    arm_head = right_arm.head_local
    leg_head = right_upleg.head_local
    dist = math.sqrt(sum((a - b) ** 2 for a, b in zip(arm_head, leg_head)))
    print(f"Right Arm to Right UpLeg distance: {dist:.4f}")

# Check spine chain
print("\n" + "-" * 60)
print("SPINE CHAIN ANALYSIS")
print("-" * 60)

spine_bones = ["Hips", "Spine", "Spine01", "Spine02"]
for name in spine_bones:
    bone = bones.get(name)
    if bone:
        parent_name = bone.parent.name if bone.parent else "None"
        children = [c.name for c in bone.children]
        print(f"{name}: parent={parent_name}, children={children}")
        print(f"  head={[round(x, 4) for x in bone.head_local]}")
        print(f"  tail={[round(x, 4) for x in bone.tail_local]}")
    else:
        print(f"{name}: NOT FOUND")

# Check head/neck for ponytail attachment point
print("\n" + "-" * 60)
print("HEAD/NECK ANALYSIS (for ponytail)")
print("-" * 60)

head_bones = ["neck", "Head", "head_end", "headfront"]
for name in head_bones:
    bone = bones.get(name)
    if bone:
        parent_name = bone.parent.name if bone.parent else "None"
        children = [c.name for c in bone.children]
        print(f"{name}: parent={parent_name}, children={children}")
        print(f"  head={[round(x, 4) for x in bone.head_local]}")
        print(f"  tail={[round(x, 4) for x in bone.tail_local]}")

# Check for any hair-related vertex groups or mesh parts
print("\n" + "-" * 60)
print("HAIR/PONYTAIL MESH SEARCH")
print("-" * 60)

for mesh in meshes:
    for vg in mesh.vertex_groups:
        if any(kw in vg.name.lower() for kw in ['hair', 'pony', 'tail', 'head']):
            print(f"  Found vertex group: {vg.name} in {mesh.name}")

# Get bounding box of entire character
print("\n" + "-" * 60)
print("BOUNDING BOX")
print("-" * 60)

for mesh in meshes:
    bbox = [mesh.matrix_world @ bpy.mathutils.Vector(corner) for corner in mesh.bound_box]
    min_x = min(v.x for v in bbox)
    max_x = max(v.x for v in bbox)
    min_y = min(v.y for v in bbox)
    max_y = max(v.y for v in bbox)
    min_z = min(v.z for v in bbox)
    max_z = max(v.z for v in bbox)
    print(f"{mesh.name}: X[{min_x:.3f}, {max_x:.3f}] Y[{min_y:.3f}, {max_y:.3f}] Z[{min_z:.3f}, {max_z:.3f}]")

print("\n" + "=" * 80)
print("INSPECTION COMPLETE")
print("=" * 80)
