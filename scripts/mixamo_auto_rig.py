#!/usr/bin/env python3
"""
Mixamo-Style Auto-Rigging Script for Blender.

Creates a humanoid rig with Mixamo-compatible bone naming convention,
applies automatic weight painting, and exports for use in the animation pipeline.

This script handles the common issue with AI-generated meshes (Meshy, Tripo, etc.)
where Blender's heat diffusion auto-weighting fails due to non-manifold geometry.
It uses voxel remeshing to create clean topology, then falls back to distance-based
weight painting when heat diffusion still fails.

Usage:
    blender --background --python scripts/mixamo_auto_rig.py -- \\
        --input path/to/model.glb \\
        --output path/to/rigged_output.fbx \\
        --character mia

Requirements:
    Blender 4.0+

Bone Naming Convention:
    Uses Mixamo format (mixamorig:BoneName) for compatibility with:
    - Mixamo animation library (2,500+ animations)
    - Existing stress test framework
    - Standard game engine pipelines
"""
import argparse
import os
import sys

try:
    import bpy
    import bmesh
    from mathutils import Vector
except ImportError:
    print("ERROR: This script must be run inside Blender.")
    print("Usage: blender --background --python scripts/mixamo_auto_rig.py -- --input model.glb --output rigged.fbx")
    sys.exit(1)

# Character presets for bone placement (proportions relative to height)
CHARACTER_PRESETS = {
    "mia": {  # 8-year-old girl
        "description": "Mia - 8yo protagonist, bigger head, shorter limbs",
        "hips_height": 0.45,
        "spine_heights": [0.50, 0.57, 0.64],
        "neck_height": 0.72,
        "head_height": 0.77,
        "shoulder_width": 0.08,
        "arm_widths": [0.20, 0.32, 0.42],
        "arm_heights": [0.68, 0.55, 0.43],
        "shoulder_height": 0.70,
        "leg_width": 0.10,
        "leg_heights": [0.43, 0.24, 0.04],
    },
    "leo": {  # 5-year-old boy
        "description": "Leo - 5yo, even bigger head ratio",
        "hips_height": 0.42,
        "spine_heights": [0.47, 0.54, 0.61],
        "neck_height": 0.69,
        "head_height": 0.74,
        "shoulder_width": 0.07,
        "arm_widths": [0.18, 0.28, 0.38],
        "arm_heights": [0.65, 0.52, 0.40],
        "shoulder_height": 0.67,
        "leg_width": 0.10,
        "leg_heights": [0.40, 0.22, 0.04],
    },
    "default": {  # Generic adult proportions
        "description": "Default adult proportions",
        "hips_height": 0.50,
        "spine_heights": [0.55, 0.62, 0.69],
        "neck_height": 0.78,
        "head_height": 0.82,
        "shoulder_width": 0.10,
        "arm_widths": [0.22, 0.35, 0.45],
        "arm_heights": [0.74, 0.58, 0.45],
        "shoulder_height": 0.76,
        "leg_width": 0.10,
        "leg_heights": [0.48, 0.26, 0.05],
    },
}

# Also map Gabe, Nina, Ruben to default for now
for name in ["gabe", "nina", "ruben"]:
    CHARACTER_PRESETS[name] = CHARACTER_PRESETS["default"].copy()
    CHARACTER_PRESETS[name]["description"] = f"{name.title()} - adult character"

TARGET_FACES = 50000
VOXEL_SIZE = 1.2


def log(msg):
    print(msg)
    sys.stdout.flush()


def import_and_prepare_mesh(input_path):
    """Import model, strip old rig, decimate, fix topology."""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

    ext = os.path.splitext(input_path)[1].lower()
    if ext in ('.glb', '.gltf'):
        bpy.ops.import_scene.gltf(filepath=input_path)
    elif ext == '.fbx':
        bpy.ops.import_scene.fbx(filepath=input_path)
    elif ext == '.obj':
        bpy.ops.wm.obj_import(filepath=input_path)
    else:
        log(f"ERROR: Unsupported format: {ext}")
        sys.exit(1)

    # Remove armatures
    for obj in list(bpy.data.objects):
        if obj.type == 'ARMATURE':
            bpy.data.objects.remove(obj, do_unlink=True)

    # Find main mesh (largest by face count)
    meshes = [obj for obj in bpy.data.objects if obj.type == 'MESH']
    if not meshes:
        log("ERROR: No mesh objects found!")
        sys.exit(1)

    mesh_obj = max(meshes, key=lambda o: len(o.data.polygons))

    # Remove smaller meshes
    for obj in meshes:
        if obj != mesh_obj:
            bpy.data.objects.remove(obj, do_unlink=True)

    # Clean parent/modifier references
    mesh_obj.parent = None
    for mod in list(mesh_obj.modifiers):
        mesh_obj.modifiers.remove(mod)
    mesh_obj.vertex_groups.clear()

    # Apply transforms
    bpy.ops.object.select_all(action='DESELECT')
    mesh_obj.select_set(True)
    bpy.context.view_layer.objects.active = mesh_obj
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    orig_faces = len(mesh_obj.data.polygons)
    log(f"Original: {len(mesh_obj.data.vertices):,} verts, {orig_faces:,} faces")

    # Decimate if needed
    if orig_faces > TARGET_FACES:
        dec = mesh_obj.modifiers.new(name="Decimate", type='DECIMATE')
        dec.ratio = TARGET_FACES / orig_faces
        bpy.ops.object.modifier_apply(modifier="Decimate")
        log(f"Decimated: {len(mesh_obj.data.vertices):,} verts, {len(mesh_obj.data.polygons):,} faces")

    # Fix topology
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles(threshold=0.1)
    bpy.ops.mesh.delete_loose(use_verts=True, use_edges=True, use_faces=False)
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.mesh.select_non_manifold()
    try:
        bpy.ops.mesh.fill_holes(sides=0)
    except:
        pass
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode='OBJECT')

    # Voxel remesh for manifold mesh
    remesh = mesh_obj.modifiers.new(name="Remesh", type='REMESH')
    remesh.mode = 'VOXEL'
    remesh.voxel_size = VOXEL_SIZE
    remesh.use_smooth_shade = True
    bpy.ops.object.modifier_apply(modifier="Remesh")

    # Smooth
    smooth = mesh_obj.modifiers.new(name="Smooth", type='SMOOTH')
    smooth.factor = 0.5
    smooth.iterations = 5
    bpy.ops.object.modifier_apply(modifier="Smooth")

    log(f"Final mesh: {len(mesh_obj.data.vertices):,} verts, {len(mesh_obj.data.polygons):,} faces")
    return mesh_obj


def analyze_mesh(mesh_obj):
    """Get mesh bounding box."""
    verts = mesh_obj.data.vertices
    xs = [v.co.x for v in verts]
    ys = [v.co.y for v in verts]
    zs = [v.co.z for v in verts]
    return {
        'min_x': min(xs), 'max_x': max(xs),
        'min_y': min(ys), 'max_y': max(ys),
        'min_z': min(zs), 'max_z': max(zs),
        'center_x': (min(xs) + max(xs)) / 2,
        'center_y': (min(ys) + max(ys)) / 2,
        'height': max(zs) - min(zs),
        'width': max(xs) - min(xs),
        'depth': max(ys) - min(ys),
    }


def create_armature(bbox, preset_name="default"):
    """Create humanoid armature with Mixamo bone names."""
    p = CHARACTER_PRESETS.get(preset_name, CHARACTER_PRESETS["default"])
    h = bbox['height']
    cx = bbox['center_x']
    cy = bbox['center_y']
    bz = bbox['min_z']
    w = bbox['width']
    d = bbox['depth']

    positions = {
        'Hips':       (cx, cy, bz + h * p['hips_height']),
        'Spine':      (cx, cy, bz + h * p['spine_heights'][0]),
        'Spine1':     (cx, cy, bz + h * p['spine_heights'][1]),
        'Spine2':     (cx, cy, bz + h * p['spine_heights'][2]),
        'Neck':       (cx, cy, bz + h * p['neck_height']),
        'Head':       (cx, cy, bz + h * p['head_height']),
        'HeadTop':    (cx, cy, bz + h * 1.00),

        'LeftShoulder':  (cx + w * p['shoulder_width'], cy, bz + h * p['shoulder_height']),
        'LeftArm':       (cx + w * p['arm_widths'][0], cy, bz + h * p['arm_heights'][0]),
        'LeftForeArm':   (cx + w * p['arm_widths'][1], cy, bz + h * p['arm_heights'][1]),
        'LeftHand':      (cx + w * p['arm_widths'][2], cy, bz + h * p['arm_heights'][2]),

        'RightShoulder': (cx - w * p['shoulder_width'], cy, bz + h * p['shoulder_height']),
        'RightArm':      (cx - w * p['arm_widths'][0], cy, bz + h * p['arm_heights'][0]),
        'RightForeArm':  (cx - w * p['arm_widths'][1], cy, bz + h * p['arm_heights'][1]),
        'RightHand':     (cx - w * p['arm_widths'][2], cy, bz + h * p['arm_heights'][2]),

        'LeftUpLeg':     (cx + w * p['leg_width'], cy, bz + h * p['leg_heights'][0]),
        'LeftLeg':       (cx + w * p['leg_width'], cy + 0.5, bz + h * p['leg_heights'][1]),
        'LeftFoot':      (cx + w * p['leg_width'], cy, bz + h * p['leg_heights'][2]),
        'LeftToeBase':   (cx + w * p['leg_width'], cy - d * 0.25, bz),

        'RightUpLeg':    (cx - w * p['leg_width'], cy, bz + h * p['leg_heights'][0]),
        'RightLeg':      (cx - w * p['leg_width'], cy + 0.5, bz + h * p['leg_heights'][1]),
        'RightFoot':     (cx - w * p['leg_width'], cy, bz + h * p['leg_heights'][2]),
        'RightToeBase':  (cx - w * p['leg_width'], cy - d * 0.25, bz),
    }

    bpy.ops.object.armature_add(enter_editmode=True, location=(0, 0, 0))
    arm_obj = bpy.context.object
    arm_obj.name = "Armature"
    arm_obj.data.name = "Armature"

    bpy.ops.armature.select_all(action='SELECT')
    bpy.ops.armature.delete()

    bone_hierarchy = [
        ('mixamorig:Hips',   None,                   'Hips',       'Spine'),
        ('mixamorig:Spine',  'mixamorig:Hips',       'Spine',      'Spine1'),
        ('mixamorig:Spine1', 'mixamorig:Spine',      'Spine1',     'Spine2'),
        ('mixamorig:Spine2', 'mixamorig:Spine1',     'Spine2',     'Neck'),
        ('mixamorig:Neck',   'mixamorig:Spine2',     'Neck',       'Head'),
        ('mixamorig:Head',   'mixamorig:Neck',       'Head',       'HeadTop'),
        ('mixamorig:LeftShoulder',  'mixamorig:Spine2',         'LeftShoulder',  'LeftArm'),
        ('mixamorig:LeftArm',       'mixamorig:LeftShoulder',   'LeftArm',       'LeftForeArm'),
        ('mixamorig:LeftForeArm',   'mixamorig:LeftArm',        'LeftForeArm',   'LeftHand'),
        ('mixamorig:LeftHand',      'mixamorig:LeftForeArm',    'LeftHand',      None),
        ('mixamorig:RightShoulder', 'mixamorig:Spine2',         'RightShoulder', 'RightArm'),
        ('mixamorig:RightArm',      'mixamorig:RightShoulder',  'RightArm',      'RightForeArm'),
        ('mixamorig:RightForeArm',  'mixamorig:RightArm',       'RightForeArm',  'RightHand'),
        ('mixamorig:RightHand',     'mixamorig:RightForeArm',   'RightHand',     None),
        ('mixamorig:LeftUpLeg',   'mixamorig:Hips',        'LeftUpLeg',   'LeftLeg'),
        ('mixamorig:LeftLeg',     'mixamorig:LeftUpLeg',   'LeftLeg',     'LeftFoot'),
        ('mixamorig:LeftFoot',    'mixamorig:LeftLeg',     'LeftFoot',    'LeftToeBase'),
        ('mixamorig:LeftToeBase', 'mixamorig:LeftFoot',    'LeftToeBase', None),
        ('mixamorig:RightUpLeg',   'mixamorig:Hips',        'RightUpLeg',   'RightLeg'),
        ('mixamorig:RightLeg',     'mixamorig:RightUpLeg',  'RightLeg',     'RightFoot'),
        ('mixamorig:RightFoot',    'mixamorig:RightLeg',    'RightFoot',    'RightToeBase'),
        ('mixamorig:RightToeBase', 'mixamorig:RightFoot',   'RightToeBase', None),
    ]

    bones = {}
    arm = arm_obj.data
    for name, parent, head_k, tail_k in bone_hierarchy:
        b = arm.edit_bones.new(name)
        b.head = Vector(positions[head_k])
        if tail_k and tail_k in positions:
            b.tail = Vector(positions[tail_k])
        else:
            if parent and parent in bones:
                d_vec = b.head - bones[parent].head
                b.tail = b.head + d_vec.normalized() * (d_vec.length * 0.5)
            else:
                b.tail = b.head + Vector((0, 0, h * 0.05))
        if parent and parent in bones:
            b.parent = bones[parent]
            b.use_connect = False
        bones[name] = b

    bpy.ops.object.mode_set(mode='OBJECT')
    log(f"Created armature: {len(bones)} bones ({p['description']})")
    return arm_obj


def apply_weights(mesh_obj, arm_obj):
    """Apply automatic weights, fall back to distance-based if needed."""
    log("Applying automatic weights...")

    bpy.ops.object.select_all(action='DESELECT')
    mesh_obj.select_set(True)
    arm_obj.select_set(True)
    bpy.context.view_layer.objects.active = arm_obj

    try:
        bpy.ops.object.parent_set(type='ARMATURE_AUTO')
    except RuntimeError as e:
        log(f"  Heat diffusion failed: {e}")

    total = len(mesh_obj.data.vertices)
    weighted = sum(1 for v in mesh_obj.data.vertices if len(v.groups) > 0)
    pct = weighted / total * 100 if total > 0 else 0
    log(f"  Heat diffusion coverage: {weighted}/{total} ({pct:.1f}%)")

    if pct < 50:
        log("  Falling back to distance-based weights...")
        _apply_distance_weights(mesh_obj, arm_obj)
        weighted = sum(1 for v in mesh_obj.data.vertices if len(v.groups) > 0)
        pct = weighted / total * 100 if total > 0 else 0
        log(f"  Distance weights coverage: {weighted}/{total} ({pct:.1f}%)")

    # Clean weights
    bpy.ops.object.select_all(action='DESELECT')
    mesh_obj.select_set(True)
    bpy.context.view_layer.objects.active = mesh_obj
    bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
    bpy.ops.object.vertex_group_normalize_all(lock_active=False)
    bpy.ops.object.vertex_group_clean(group_select_mode='ALL', limit=0.01)
    bpy.ops.object.vertex_group_limit_total(group_select_mode='ALL', limit=4)
    bpy.ops.object.mode_set(mode='OBJECT')

    return pct


def _apply_distance_weights(mesh_obj, arm_obj):
    """Distance-based weight assignment fallback."""
    mesh_obj.parent = arm_obj
    if not any(m.type == 'ARMATURE' for m in mesh_obj.modifiers):
        mod = mesh_obj.modifiers.new(name="Armature", type='ARMATURE')
        mod.object = arm_obj

    mesh_obj.vertex_groups.clear()
    for bone in arm_obj.data.bones:
        mesh_obj.vertex_groups.new(name=bone.name)

    bone_data = []
    for bone in arm_obj.data.bones:
        head = arm_obj.matrix_world @ bone.head_local
        tail = arm_obj.matrix_world @ bone.tail_local
        length = (tail - head).length
        bone_data.append((bone.name, head, tail, length))

    total = len(mesh_obj.data.vertices)
    for i, v in enumerate(mesh_obj.data.vertices):
        if i % 5000 == 0 and i > 0:
            log(f"    {i}/{total}...")

        v_pos = mesh_obj.matrix_world @ v.co
        weights = {}
        for bname, bhead, btail, blength in bone_data:
            ab = btail - bhead
            ap = v_pos - bhead
            t = max(0, min(1, ap.dot(ab) / max(ab.dot(ab), 1e-10)))
            closest = bhead + ab * t
            dist = (v_pos - closest).length
            radius = max(blength * 2.5, 8.0)
            if dist < radius:
                w = (1.0 - dist / radius) ** 2
                if w > 0.01:
                    weights[bname] = w

        if weights:
            top = sorted(weights.items(), key=lambda x: -x[1])[:4]
            total_w = sum(w for _, w in top)
            for bname, w in top:
                mesh_obj.vertex_groups[bname].add([i], w / total_w, 'REPLACE')


def export_result(mesh_obj, arm_obj, output_path):
    """Export rigged model."""
    bpy.ops.object.select_all(action='DESELECT')
    mesh_obj.select_set(True)
    arm_obj.select_set(True)
    bpy.context.view_layer.objects.active = arm_obj

    ext = os.path.splitext(output_path)[1].lower()
    if ext == '.fbx':
        bpy.ops.export_scene.fbx(
            filepath=output_path,
            use_selection=True,
            object_types={'ARMATURE', 'MESH'},
            use_mesh_modifiers=True,
            add_leaf_bones=False,
            bake_anim=False,
            path_mode='COPY',
            embed_textures=True,
            axis_forward='-Z',
            axis_up='Y',
        )
    elif ext in ('.glb', '.gltf'):
        bpy.ops.export_scene.gltf(
            filepath=output_path,
            use_selection=True,
            export_format='GLB' if ext == '.glb' else 'GLTF_SEPARATE',
            export_apply=True,
        )
    else:
        log(f"Unsupported export format: {ext}, defaulting to FBX")
        output_path = output_path.rsplit('.', 1)[0] + '.fbx'
        bpy.ops.export_scene.fbx(
            filepath=output_path,
            use_selection=True,
            object_types={'ARMATURE', 'MESH'},
            use_mesh_modifiers=True,
            add_leaf_bones=False,
            bake_anim=False,
        )

    log(f"Exported: {output_path} ({os.path.getsize(output_path):,} bytes)")

    # Also save .blend
    blend_path = output_path.rsplit('.', 1)[0] + '.blend'
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    log(f"Saved: {blend_path}")

    return output_path


def main():
    argv = sys.argv
    if '--' in argv:
        argv = argv[argv.index('--') + 1:]
    else:
        argv = []

    parser = argparse.ArgumentParser(description="Mixamo-style auto-rigging")
    parser.add_argument("--input", required=True, help="Input model (GLB/FBX/OBJ)")
    parser.add_argument("--output", required=True, help="Output rigged model (FBX/GLB)")
    parser.add_argument("--character", default="default", help="Character preset name")
    args = parser.parse_args(argv)

    log("=" * 60)
    log(f"Mixamo-Style Auto-Rig: {args.character}")
    log("=" * 60)

    mesh_obj = import_and_prepare_mesh(args.input)
    bbox = analyze_mesh(mesh_obj)
    arm_obj = create_armature(bbox, args.character)
    coverage = apply_weights(mesh_obj, arm_obj)
    export_result(mesh_obj, arm_obj, args.output)

    # Summary
    total = len(mesh_obj.data.vertices)
    weighted = sum(1 for v in mesh_obj.data.vertices if len(v.groups) > 0)
    max_inf = max((len(v.groups) for v in mesh_obj.data.vertices), default=0)

    log("\n" + "=" * 60)
    log("RIG SUMMARY")
    log("=" * 60)
    log(f"Character: {args.character}")
    log(f"Bones: {len(arm_obj.data.bones)}")
    log(f"Vertices: {total:,}")
    log(f"Weight coverage: {weighted}/{total} ({coverage:.1f}%)")
    log(f"Max influences: {max_inf}")
    log(f"Output: {args.output}")
    log("=" * 60)


if __name__ == "__main__":
    main()
