"""
Inspect the Meshy GLB model to understand its rig structure.
Run: blender --background --python scripts/blender/inspect_meshy_rig.py
"""
import bpy
import sys
import json

# Clear scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Import the GLB
model_path = "models/characters/mia/mia_rigged.glb"
bpy.ops.import_scene.gltf(filepath=model_path)

print("\n" + "=" * 70)
print("  MESHY MODEL INSPECTION")
print("=" * 70)

# List all objects
print("\n--- ALL OBJECTS ---")
for obj in bpy.context.scene.objects:
    print(f"  {obj.name} (type={obj.type}, parent={obj.parent.name if obj.parent else 'None'})")
    if obj.type == 'MESH':
        print(f"    Vertices: {len(obj.data.vertices)}")
        print(f"    Faces: {len(obj.data.polygons)}")
        print(f"    Vertex groups: {len(obj.vertex_groups)}")
        if obj.vertex_groups:
            print(f"    Groups: {[vg.name for vg in obj.vertex_groups]}")
        # Check modifiers
        print(f"    Modifiers: {[m.name + '(' + m.type + ')' for m in obj.modifiers]}")
        # Check materials
        print(f"    Materials: {[m.name for m in obj.data.materials if m]}")

# Inspect armature
print("\n--- ARMATURE DETAILS ---")
armatures = [obj for obj in bpy.context.scene.objects if obj.type == 'ARMATURE']
if armatures:
    arm = armatures[0]
    print(f"Armature: {arm.name}")
    print(f"Total bones: {len(arm.data.bones)}")

    # Print bone hierarchy
    print("\n--- BONE HIERARCHY ---")
    def print_bone_tree(bone, indent=0):
        connected = " [connected]" if bone.use_connect else ""
        print(f"{'  ' * indent}{bone.name} (head={[round(x, 3) for x in bone.head_local]}, tail={[round(x, 3) for x in bone.tail_local]}){connected}")
        for child in bone.children:
            print_bone_tree(child, indent + 1)

    for bone in arm.data.bones:
        if bone.parent is None:
            print_bone_tree(bone)

    # Check which bones are deform bones
    print("\n--- DEFORM BONES ---")
    deform_bones = [b for b in arm.data.bones if b.use_deform]
    non_deform = [b for b in arm.data.bones if not b.use_deform]
    print(f"Deform bones ({len(deform_bones)}): {[b.name for b in deform_bones]}")
    print(f"Non-deform bones ({len(non_deform)}): {[b.name for b in non_deform]}")

    # Check pose bone constraints
    print("\n--- POSE BONE CONSTRAINTS ---")
    for pbone in arm.pose.bones:
        if pbone.constraints:
            print(f"  {pbone.name}: {[(c.name, c.type) for c in pbone.constraints]}")
else:
    print("NO ARMATURE FOUND!")

# Check vertex group coverage
print("\n--- VERTEX GROUP ANALYSIS ---")
meshes = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']
for mesh_obj in meshes:
    if not mesh_obj.vertex_groups:
        continue
    total_verts = len(mesh_obj.data.vertices)
    unweighted = 0
    max_influences = 0
    for v in mesh_obj.data.vertices:
        if len(v.groups) == 0:
            unweighted += 1
        max_influences = max(max_influences, len(v.groups))

    print(f"\n  Mesh: {mesh_obj.name}")
    print(f"  Total vertices: {total_verts}")
    print(f"  Unweighted vertices: {unweighted} ({100*unweighted/total_verts:.1f}%)")
    print(f"  Max influences per vertex: {max_influences}")

    # Check weight distribution per group
    print(f"\n  Weight distribution per bone:")
    for vg in mesh_obj.vertex_groups:
        verts_in_group = 0
        max_weight = 0
        for v in mesh_obj.data.vertices:
            for g in v.groups:
                if g.group == vg.index:
                    verts_in_group += 1
                    max_weight = max(max_weight, g.weight)
        if verts_in_group > 0:
            print(f"    {vg.name}: {verts_in_group} verts, max_weight={max_weight:.3f}")

print("\n" + "=" * 70)
print("  INSPECTION COMPLETE")
print("=" * 70)
