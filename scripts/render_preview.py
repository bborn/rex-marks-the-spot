#!/usr/bin/env python3
"""
Blender script to render preview images of textured GLB models.
Run with: blender --background --python render_preview.py -- <glb_path> <output_path> <name>
"""

import bpy
import sys
import math
import os
import mathutils


def clear_scene():
    """Remove all objects from scene."""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for block in bpy.data.meshes:
        if block.users == 0:
            bpy.data.meshes.remove(block)
    for block in bpy.data.materials:
        if block.users == 0:
            bpy.data.materials.remove(block)


def get_scene_bounds(objects):
    """Get bounding box of all objects in world space."""
    min_co = mathutils.Vector((float('inf'), float('inf'), float('inf')))
    max_co = mathutils.Vector((float('-inf'), float('-inf'), float('-inf')))

    for obj in objects:
        if obj.type != 'MESH':
            continue
        # Ensure transforms are applied
        depsgraph = bpy.context.evaluated_depsgraph_get()
        eval_obj = obj.evaluated_get(depsgraph)
        mesh = eval_obj.to_mesh()

        for v in mesh.vertices:
            world_co = obj.matrix_world @ v.co
            for i in range(3):
                min_co[i] = min(min_co[i], world_co[i])
                max_co[i] = max(max_co[i], world_co[i])

        eval_obj.to_mesh_clear()

    return min_co, max_co


def setup_scene(glb_path):
    """Import GLB and set up camera + lights."""

    # Import GLB
    bpy.ops.import_scene.gltf(filepath=glb_path)

    # Get all mesh objects
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']
    print(f"  Imported {len(meshes)} mesh objects")
    for m in meshes:
        print(f"    - {m.name}: loc={m.location}, scale={m.scale}")

    if not meshes:
        print("  ERROR: No mesh objects!")
        sys.exit(1)

    # Get bounds
    min_co, max_co = get_scene_bounds(meshes)
    center = (min_co + max_co) / 2
    size = (max_co - min_co).length
    max_dim = max(max_co[i] - min_co[i] for i in range(3))

    print(f"  Bounds: min={min_co}, max={max_co}")
    print(f"  Center: {center}, Size: {size}, MaxDim: {max_dim}")

    # RENDER SETTINGS
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x = 1024
    scene.render.resolution_y = 1024
    scene.render.film_transparent = False
    scene.render.image_settings.file_format = 'PNG'
    scene.eevee.taa_render_samples = 64

    # WORLD
    world = bpy.data.worlds.new("World")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.2, 0.2, 0.25, 1)
    bg.inputs["Strength"].default_value = 1.0

    # CAMERA
    cam_data = bpy.data.cameras.new("Camera")
    cam_data.lens = 50
    cam_data.clip_start = 0.01
    cam_data.clip_end = 1000
    cam_obj = bpy.data.objects.new("Camera", cam_data)
    bpy.context.scene.collection.objects.link(cam_obj)
    scene.camera = cam_obj

    # Position camera at a good distance
    dist = max_dim * 2.5
    cam_obj.location = (center.x + dist * 0.7, center.y - dist * 0.7, center.z + max_dim * 0.4)

    # Point camera at center
    direction = center - cam_obj.location
    rot_quat = direction.to_track_quat('-Z', 'Y')
    cam_obj.rotation_euler = rot_quat.to_euler()

    # KEY LIGHT
    key_data = bpy.data.lights.new("KeyLight", type='POINT')
    key_data.energy = max_dim * 500
    key_data.color = (1.0, 0.95, 0.9)
    key_data.shadow_soft_size = max_dim * 0.5
    key_obj = bpy.data.objects.new("KeyLight", key_data)
    key_obj.location = (center.x + dist, center.y - dist * 0.5, center.z + dist)
    bpy.context.scene.collection.objects.link(key_obj)

    # FILL LIGHT
    fill_data = bpy.data.lights.new("FillLight", type='POINT')
    fill_data.energy = max_dim * 200
    fill_data.color = (0.85, 0.9, 1.0)
    fill_obj = bpy.data.objects.new("FillLight", fill_data)
    fill_obj.location = (center.x - dist * 0.8, center.y - dist * 0.3, center.z + max_dim * 0.5)
    bpy.context.scene.collection.objects.link(fill_obj)

    # RIM LIGHT
    rim_data = bpy.data.lights.new("RimLight", type='POINT')
    rim_data.energy = max_dim * 300
    rim_data.color = (1.0, 1.0, 1.0)
    rim_obj = bpy.data.objects.new("RimLight", rim_data)
    rim_obj.location = (center.x, center.y + dist, center.z + max_dim * 0.3)
    bpy.context.scene.collection.objects.link(rim_obj)

    # GROUND
    bpy.ops.mesh.primitive_plane_add(size=max_dim * 10, location=(center.x, center.y, min_co.z))
    plane = bpy.context.active_object
    plane.name = "Ground"
    mat = bpy.data.materials.new("GroundMat")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0.15, 0.15, 0.18, 1)
    bsdf.inputs["Roughness"].default_value = 0.9
    plane.data.materials.append(mat)

    return meshes, cam_obj, center, max_dim


def render_angle(cam_obj, center, max_dim, angle_deg, output_path):
    """Render from a specific angle around the center."""
    dist = max_dim * 2.5
    angle_rad = math.radians(angle_deg)

    cam_obj.location = (
        center.x + dist * 0.7 * math.cos(angle_rad),
        center.y + dist * 0.7 * math.sin(angle_rad),
        center.z + max_dim * 0.4
    )

    direction = center - cam_obj.location
    rot_quat = direction.to_track_quat('-Z', 'Y')
    cam_obj.rotation_euler = rot_quat.to_euler()

    bpy.context.scene.render.filepath = output_path
    bpy.ops.render.render(write_still=True)
    print(f"  Saved: {output_path}")


def main():
    argv = sys.argv
    try:
        idx = argv.index("--")
        args = argv[idx + 1:]
    except ValueError:
        print("Usage: blender --background --python render_preview.py -- <glb_path> <output_dir> <name>")
        sys.exit(1)

    if len(args) < 3:
        print("Need: glb_path output_dir name")
        sys.exit(1)

    glb_path = os.path.abspath(args[0])
    output_dir = os.path.abspath(args[1])
    name = args[2]

    os.makedirs(output_dir, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"Rendering preview for: {name}")
    print(f"  GLB: {glb_path}")
    print(f"  Output: {output_dir}")
    print(f"{'='*60}")

    clear_scene()
    meshes, cam_obj, center, max_dim = setup_scene(glb_path)

    # Render front view (facing -Y direction, camera at -Y looking +Y)
    print("  Rendering front view...")
    render_angle(cam_obj, center, max_dim, -90, os.path.join(output_dir, f"{name}_front.png"))

    # Side view
    print("  Rendering side view...")
    render_angle(cam_obj, center, max_dim, 0, os.path.join(output_dir, f"{name}_side.png"))

    # 3/4 view
    print("  Rendering 3/4 view...")
    render_angle(cam_obj, center, max_dim, -55, os.path.join(output_dir, f"{name}_3quarter.png"))

    print(f"  Done! Renders saved to {output_dir}")


if __name__ == "__main__":
    main()
