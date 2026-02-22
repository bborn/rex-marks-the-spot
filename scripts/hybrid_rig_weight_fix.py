#!/usr/bin/env python3
"""
Hybrid Rig Weight Fix
=====================
Fixes weight painting on Meshy auto-rigged characters by replacing
the default (broken) vertex weights with zone-based distance weights.

The Meshy auto-rigger produces terrible weights where the Head bone
controls 92%+ of all vertices, causing extreme stretching on any pose.
This script replaces those weights with anatomically-correct zone-based
weights that restrict each bone's influence to its local body region.

Usage:
  xvfb-run -a blender --background --python scripts/hybrid_rig_weight_fix.py -- \
      --input /tmp/mia_rigged.fbx \
      --output /tmp/mia_hybrid_rig.blend \
      --textures /tmp/mia_textures/ \
      --render-tests /tmp/hybrid_rig_tests/

Input: FBX with Meshy auto-rig (armature + skinned mesh)
Output: Blend file with fixed weights + optional stress test renders

Approach:
  1. Import FBX, fix cm/m scale mismatch
  2. Clear all vertex weights
  3. Assign weights using strict anatomical zones:
     - Head zone: only Head/neck bones can influence
     - Torso zone: only Spine/Shoulder/Arm bones
     - Hip zone: only Hips/UpLeg bones
     - Leg zones: only Leg/Foot bones
  4. Within each zone, use Gaussian distance-to-bone falloff
  5. Optionally render stress test poses
"""

import bpy
import mathutils
import os
import math
import time
import sys
from math import exp


def dist_to_bone_segment(point, head, tail, length):
    """Distance from point to nearest point on bone segment."""
    if length < 0.0001:
        return (point - head).length
    d = (tail - head) / length
    t = max(0, min(1, (point - head).dot(d) / length))
    return (point - (head + t * (tail - head))).length


def get_allowed_bones(z, x, neck_z, shoulder_z, hips_z, knee_z, ankle_z):
    """Return dict of {bone_name: max_weight} based on vertex position.

    Strict zone enforcement prevents long-range bone influence.
    """
    allowed = {}

    if z > neck_z + 0.02:
        # Head/hair region
        allowed['Head'] = 1.0
        allowed['neck'] = 0.3
        return allowed

    if z > shoulder_z + 0.01:
        # Neck transition
        t = (z - shoulder_z - 0.01) / (neck_z + 0.02 - shoulder_z - 0.01)
        t = max(0, min(1, t))
        allowed['Head'] = t * 0.8
        allowed['neck'] = 1.0
        allowed['Spine'] = 1.0 - t * 0.5
        allowed['Spine01'] = (1.0 - t) * 0.3
        if abs(x) > 0.05:
            side = 'Left' if x > 0 else 'Right'
            allowed[f'{side}Shoulder'] = 0.5
        return allowed

    if z > hips_z + 0.03:
        # Upper torso
        allowed['Spine'] = 1.0
        allowed['Spine01'] = 1.0
        allowed['Spine02'] = 0.5
        if abs(x) > 0.03:
            side = 'Left' if x > 0 else 'Right'
            allowed[f'{side}Shoulder'] = 1.0
            allowed[f'{side}Arm'] = 1.0
            allowed[f'{side}ForeArm'] = 1.0
            allowed[f'{side}Hand'] = 1.0
        else:
            allowed['LeftShoulder'] = 0.3
            allowed['RightShoulder'] = 0.3
        return allowed

    if z > hips_z - 0.05:
        # Hip/waist region
        allowed['Hips'] = 1.0
        allowed['Spine02'] = 1.0
        allowed['Spine01'] = 0.3
        if x > 0.01:
            allowed['LeftUpLeg'] = 0.5
        elif x < -0.01:
            allowed['RightUpLeg'] = 0.5
        else:
            allowed['LeftUpLeg'] = 0.3
            allowed['RightUpLeg'] = 0.3
        return allowed

    if z > knee_z:
        # Upper leg
        if x > 0:
            allowed['LeftUpLeg'] = 1.0
            allowed['LeftLeg'] = 0.3
        elif x < 0:
            allowed['RightUpLeg'] = 1.0
            allowed['RightLeg'] = 0.3
        else:
            allowed['LeftUpLeg'] = 0.5
            allowed['RightUpLeg'] = 0.5
        allowed['Hips'] = 0.3
        return allowed

    if z > ankle_z:
        # Lower leg
        if x > 0:
            allowed['LeftLeg'] = 1.0
            allowed['LeftUpLeg'] = 0.2
            allowed['LeftFoot'] = 0.3
        elif x < 0:
            allowed['RightLeg'] = 1.0
            allowed['RightUpLeg'] = 0.2
            allowed['RightFoot'] = 0.3
        else:
            allowed['LeftLeg'] = 0.5
            allowed['RightLeg'] = 0.5
        return allowed

    # Foot region
    if x > 0:
        allowed['LeftFoot'] = 1.0
        allowed['LeftToeBase'] = 1.0
        allowed['LeftLeg'] = 0.2
    elif x < 0:
        allowed['RightFoot'] = 1.0
        allowed['RightToeBase'] = 1.0
        allowed['RightLeg'] = 0.2
    else:
        allowed['LeftFoot'] = 0.5
        allowed['RightFoot'] = 0.5
        allowed['LeftToeBase'] = 0.5
        allowed['RightToeBase'] = 0.5
    return allowed


# Bone influence radii (Gaussian falloff)
BONE_RADII = {
    'Head': 0.20, 'neck': 0.05,
    'Spine': 0.08, 'Spine01': 0.10, 'Spine02': 0.10, 'Hips': 0.10,
    'LeftShoulder': 0.05, 'LeftArm': 0.07, 'LeftForeArm': 0.06, 'LeftHand': 0.06,
    'RightShoulder': 0.05, 'RightArm': 0.07, 'RightForeArm': 0.06, 'RightHand': 0.06,
    'LeftUpLeg': 0.08, 'LeftLeg': 0.06, 'LeftFoot': 0.06, 'LeftToeBase': 0.05,
    'RightUpLeg': 0.08, 'RightLeg': 0.06, 'RightFoot': 0.06, 'RightToeBase': 0.05,
}


def fix_weights(input_fbx, output_blend, texture_dir=None, render_dir=None):
    """Main pipeline: import, fix weights, optionally render tests."""

    print("=" * 60)
    print("HYBRID RIG WEIGHT FIX")
    print("=" * 60)

    # Import
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=input_fbx)

    arm_obj = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    mesh_obj = next(o for o in bpy.data.objects if o.type == 'MESH')
    print(f"Armature: {arm_obj.name} ({len(arm_obj.data.bones)} bones)")
    print(f"Mesh: {mesh_obj.name} ({len(mesh_obj.data.vertices)} verts)")

    # Fix transforms (FBX cm/m mismatch)
    bpy.context.view_layer.objects.active = mesh_obj
    mesh_obj.select_set(True)
    bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
    mesh_obj.vertex_groups.clear()
    for mod in list(mesh_obj.modifiers):
        mesh_obj.modifiers.remove(mod)

    for obj in [mesh_obj, arm_obj]:
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    # Set non-deforming bones
    for bname in ['head_end', 'headfront']:
        if bname in arm_obj.data.bones:
            arm_obj.data.bones[bname].use_deform = False

    # Collect bone data
    bone_info = {}
    for bone in arm_obj.data.bones:
        if not bone.use_deform:
            continue
        h = mathutils.Vector(bone.head_local)
        t = mathutils.Vector(bone.tail_local)
        bone_info[bone.name] = {'head': h, 'tail': t, 'length': (t - h).length}

    # Zone boundaries from bone positions
    neck_z = bone_info['neck']['head'].z
    shoulder_z = bone_info['Spine']['head'].z
    hips_z = bone_info['Hips']['head'].z
    knee_z = 0.25
    ankle_z = 0.07
    print(f"Zones: ankle={ankle_z}, knee={knee_z}, hips={hips_z:.3f}, "
          f"shoulder={shoulder_z:.3f}, neck={neck_z:.3f}")

    # Create vertex groups
    bpy.context.view_layer.objects.active = mesh_obj
    for name in bone_info:
        mesh_obj.vertex_groups.new(name=name)

    # Paint weights
    total = len(mesh_obj.data.vertices)
    start = time.time()
    print(f"\nPainting {total} vertices...")

    for vi, v in enumerate(mesh_obj.data.vertices):
        vc = mathutils.Vector(v.co)
        allowed = get_allowed_bones(vc.z, vc.x, neck_z, shoulder_z, hips_z, knee_z, ankle_z)

        bone_weights = []
        for bname, max_w in allowed.items():
            if bname not in bone_info:
                continue
            info = bone_info[bname]
            dist = dist_to_bone_segment(vc, info['head'], info['tail'], info['length'])
            r = BONE_RADII.get(bname, 0.08)
            w = exp(-(dist / r) ** 2) * max_w
            if w > 0.001:
                bone_weights.append((bname, w))

        if not bone_weights:
            min_d, nearest = float('inf'), list(allowed.keys())[0] if allowed else 'Hips'
            for bname in allowed:
                if bname in bone_info:
                    d = dist_to_bone_segment(vc, bone_info[bname]['head'],
                                             bone_info[bname]['tail'], bone_info[bname]['length'])
                    if d < min_d:
                        min_d, nearest = d, bname
            bone_weights = [(nearest, 1.0)]

        bone_weights.sort(key=lambda x: x[1], reverse=True)
        bone_weights = bone_weights[:4]
        tw = sum(w for _, w in bone_weights)
        for name, w in bone_weights:
            mesh_obj.vertex_groups[name].add([vi], w / tw, 'REPLACE')

        if (vi + 1) % 100000 == 0:
            print(f"  {vi + 1}/{total} ({(vi + 1) / total * 100:.0f}%)")

    print(f"  Done in {time.time() - start:.1f}s")

    # Armature modifier (no parenting to avoid scale inheritance)
    arm_mod = mesh_obj.modifiers.new("Armature", 'ARMATURE')
    arm_mod.object = arm_obj

    # Apply PBR textures if provided
    if texture_dir and os.path.isdir(texture_dir):
        _apply_pbr_textures(mesh_obj, texture_dir)

    # Save
    bpy.ops.wm.save_as_mainfile(filepath=output_blend)
    print(f"\nSaved: {output_blend}")

    # Render stress tests if requested
    if render_dir:
        _render_stress_tests(arm_obj, mesh_obj, render_dir)

    return output_blend


def _apply_pbr_textures(mesh_obj, tex_dir):
    """Load PBR texture maps into the material."""
    mat = mesh_obj.data.materials[0]
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    bsdf = next((n for n in nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if not bsdf:
        return

    for ttype, fname, inp in [
        ('b', 'mia_base_color.png', 'Base Color'),
        ('r', 'mia_roughness.png', 'Roughness'),
        ('m', 'mia_metallic.png', 'Metallic'),
    ]:
        fp = os.path.join(tex_dir, fname)
        if os.path.exists(fp):
            img = bpy.data.images.load(fp)
            tn = nodes.new('ShaderNodeTexImage')
            tn.image = img
            if ttype != 'b':
                img.colorspace_settings.name = 'Non-Color'
            links.new(tn.outputs['Color'], bsdf.inputs[inp])

    nfp = os.path.join(tex_dir, 'mia_normal.png')
    if os.path.exists(nfp):
        img = bpy.data.images.load(nfp)
        img.colorspace_settings.name = 'Non-Color'
        tn = nodes.new('ShaderNodeTexImage')
        tn.image = img
        nm = nodes.new('ShaderNodeNormalMap')
        links.new(tn.outputs['Color'], nm.inputs['Color'])
        links.new(nm.outputs['Normal'], bsdf.inputs['Normal'])

    print("  PBR textures loaded")


def _render_stress_tests(arm_obj, mesh_obj, output_dir):
    """Render 5 stress test poses at 800x600."""
    os.makedirs(output_dir, exist_ok=True)
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x = 800
    scene.render.resolution_y = 600
    scene.render.film_transparent = False
    scene.eevee.taa_render_samples = 32

    # Lighting
    bpy.ops.object.light_add(type='SUN', location=(2, -3, 5))
    bpy.context.active_object.data.energy = 3
    bpy.context.active_object.rotation_euler = (math.radians(45), math.radians(15), math.radians(30))
    bpy.ops.object.light_add(type='AREA', location=(-2, -2, 3))
    bpy.context.active_object.data.energy = 100
    bpy.context.active_object.data.size = 3
    bpy.ops.object.light_add(type='AREA', location=(0, 2, 2))
    bpy.context.active_object.data.energy = 50
    bpy.context.active_object.data.size = 2

    world = bpy.data.worlds.new("World")
    scene.world = world
    world.use_nodes = True
    world.node_tree.nodes['Background'].inputs[0].default_value = (0.25, 0.3, 0.35, 1)

    # Camera framing
    total = len(mesh_obj.data.vertices)
    sample = [mesh_obj.matrix_world @ mesh_obj.data.vertices[i].co
              for i in range(0, total, max(1, total // 1000))]
    cz = sum(v.z for v in sample) / len(sample)
    ch = max(v.z for v in sample) - min(v.z for v in sample)
    cd = ch * 2.0

    bpy.ops.object.camera_add(location=(0, -cd, cz))
    cam = bpy.context.active_object
    scene.camera = cam
    cam.data.lens = 65
    d = mathutils.Vector((0, 0, cz)) - cam.location
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()

    # Bone local axes for correct poses:
    # Head/neck (Y-up): euler Y = turn, X = nod
    # Arms (mostly Z-down): euler Z = raise/lower
    # Legs (Z-down): euler X = swing fwd/back
    poses = {
        "01_rest_pose": {},
        "02_head_turn": {"Head": (0, -30, 0), "neck": (0, -10, 0)},
        "03_arms_up": {"LeftArm": (0, 0, 120), "RightArm": (0, 0, -120),
                       "LeftForeArm": (30, 0, 0), "RightForeArm": (-30, 0, 0)},
        "04_walking": {"LeftUpLeg": (-30, 0, 0), "RightUpLeg": (30, 0, 0),
                       "LeftLeg": (40, 0, 0), "LeftArm": (20, 0, 0),
                       "RightArm": (-20, 0, 0), "Spine02": (0, 5, 0)},
        "05_deep_squat": {"LeftUpLeg": (-80, 0, 0), "RightUpLeg": (-80, 0, 0),
                          "LeftLeg": (80, 0, 0), "RightLeg": (80, 0, 0),
                          "Spine02": (10, 0, 0)},
    }

    for pn, pd in poses.items():
        # Reset
        bpy.context.view_layer.objects.active = arm_obj
        bpy.ops.object.mode_set(mode='POSE')
        bpy.ops.pose.select_all(action='SELECT')
        bpy.ops.pose.rot_clear()
        bpy.ops.pose.loc_clear()
        # Apply
        for bn, (rx, ry, rz) in pd.items():
            if bn in arm_obj.pose.bones:
                pb = arm_obj.pose.bones[bn]
                pb.rotation_mode = 'XYZ'
                pb.rotation_euler = (math.radians(rx), math.radians(ry), math.radians(rz))
        bpy.ops.object.mode_set(mode='OBJECT')

        fp = os.path.join(output_dir, f"{pn}.png")
        scene.render.filepath = fp
        bpy.ops.render.render(write_still=True)
        print(f"  {pn}: {os.path.getsize(fp) / 1024:.0f}KB")


if __name__ == '__main__':
    # Parse args after "--"
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = []

    import argparse
    parser = argparse.ArgumentParser(description="Fix Meshy auto-rig weight painting")
    parser.add_argument("--input", required=True, help="Input FBX with Meshy auto-rig")
    parser.add_argument("--output", required=True, help="Output .blend file path")
    parser.add_argument("--textures", help="Directory with PBR textures")
    parser.add_argument("--render-tests", help="Directory for stress test renders")
    args = parser.parse_args(argv)

    fix_weights(args.input, args.output, args.textures, args.render_tests)
