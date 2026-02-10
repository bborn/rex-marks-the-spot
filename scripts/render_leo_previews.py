#!/usr/bin/env python3
"""
Render preview images of Leo 3D model from multiple angles.

Run headless:
    blender --background --python scripts/render_leo_previews.py -- output/leo_meshy/leo_meshy.glb
"""

import bpy
import sys
import math
from mathutils import Vector
from pathlib import Path


def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()


def import_glb(filepath):
    bpy.ops.import_scene.gltf(filepath=filepath)
    imported = list(bpy.context.selected_objects)
    return imported


def get_model_bounds(objects):
    min_co = Vector((float('inf'),) * 3)
    max_co = Vector((float('-inf'),) * 3)
    for obj in objects:
        if obj.type != 'MESH':
            continue
        for corner in obj.bound_box:
            world_co = obj.matrix_world @ Vector(corner)
            for i in range(3):
                min_co[i] = min(min_co[i], world_co[i])
                max_co[i] = max(max_co[i], world_co[i])
    center = (min_co + max_co) / 2
    size = max_co - min_co
    return center, size


def setup_lighting(center):
    bpy.ops.object.light_add(type='AREA', location=(center.x + 3, center.y - 3, center.z + 3))
    key = bpy.context.active_object
    key.name = "KeyLight"
    key.data.energy = 500
    key.data.size = 3

    bpy.ops.object.light_add(type='AREA', location=(center.x - 3, center.y - 2, center.z + 2))
    fill = bpy.context.active_object
    fill.name = "FillLight"
    fill.data.energy = 200
    fill.data.size = 2

    bpy.ops.object.light_add(type='AREA', location=(center.x, center.y + 3, center.z + 2))
    rim = bpy.context.active_object
    rim.name = "RimLight"
    rim.data.energy = 300
    rim.data.size = 2

    world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
    bpy.context.scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = (0.85, 0.85, 0.9, 1.0)
        bg.inputs[1].default_value = 0.8


def setup_camera_at(location, target, name="Camera"):
    cam = bpy.data.objects.get(name)
    if cam:
        bpy.data.objects.remove(cam, do_unlink=True)

    cam_data = bpy.data.cameras.new(name)
    cam_data.lens = 50
    cam = bpy.data.objects.new(name, cam_data)
    bpy.context.collection.objects.link(cam)

    cam.location = location

    # Use track-to constraint for reliable aiming
    track = cam.constraints.new(type='TRACK_TO')
    # Create empty at target for tracking
    empty = bpy.data.objects.get("CamTarget")
    if not empty:
        empty = bpy.data.objects.new("CamTarget", None)
        bpy.context.collection.objects.link(empty)
    empty.location = target
    track.target = empty
    track.track_axis = 'TRACK_NEGATIVE_Z'
    track.up_axis = 'UP_Y'

    bpy.context.scene.camera = cam
    return cam


def render_view(angle_name, center, size, output_dir):
    max_dim = max(size.x, size.y, size.z)
    distance = max_dim * 2.0

    angles = {
        "front": (0, -1, 0.3),
        "side": (1, 0, 0.3),
        "three_quarter": (0.7, -0.7, 0.4),
    }

    dx, dy, dz = angles.get(angle_name, (0, -1, 0.3))
    cam_loc = (
        center.x + dx * distance,
        center.y + dy * distance,
        center.z + dz * distance,
    )

    setup_camera_at(cam_loc, center)

    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE'
    scene.eevee.taa_render_samples = 64
    scene.render.resolution_x = 1024
    scene.render.resolution_y = 1024
    scene.render.film_transparent = True
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'

    output_path = str(Path(output_dir) / f"leo_meshy_{angle_name}.png")
    scene.render.filepath = output_path

    import sys
    sys.stderr.write(f"Rendering {angle_name} view...\n")
    bpy.ops.render.render(write_still=True)
    sys.stderr.write(f"  Saved: {output_path}\n")
    return output_path


def main():
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = []

    if not argv:
        import sys as s
        s.stderr.write("Usage: blender --background --python render_leo_previews.py -- <glb_path> [output_dir]\n")
        sys.exit(1)

    glb_path = argv[0]
    output_dir = argv[1] if len(argv) > 1 else "output/leo_meshy/previews"
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    clear_scene()
    objects = import_glb(glb_path)
    center, size = get_model_bounds(objects)

    import sys as s
    s.stderr.write(f"Model center: {center}, size: {size}\n")

    setup_lighting(center)

    rendered = []
    for angle in ["front", "side", "three_quarter"]:
        path = render_view(angle, center, size, output_dir)
        rendered.append(path)

    s.stderr.write(f"\nRendered {len(rendered)} preview images to {output_dir}\n")


if __name__ == "__main__":
    main()
