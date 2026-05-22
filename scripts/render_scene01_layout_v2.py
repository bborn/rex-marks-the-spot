#!/usr/bin/env python3
"""
Render all 8 camera angles from scene01_layout_v2.blend.

Usage:
    xvfb-run -a blender --background scene01_layout_v2.blend --python scripts/render_scene01_layout_v2.py
"""

import bpy
import os
import sys


def main():
    scene = bpy.context.scene

    # Render settings: EEVEE, 1376x768
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x = 1376
    scene.render.resolution_y = 768
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGB'

    # EEVEE quality settings
    if hasattr(scene.eevee, 'taa_render_samples'):
        scene.eevee.taa_render_samples = 64

    # Output directory: same directory as the .blend file
    blend_dir = os.path.dirname(bpy.data.filepath)
    if not blend_dir:
        blend_dir = os.getcwd()

    output_dir = blend_dir
    os.makedirs(output_dir, exist_ok=True)

    # Find all cameras
    cameras = [obj for obj in bpy.data.objects if obj.type == 'CAMERA']
    cameras.sort(key=lambda c: c.name)

    print(f"Found {len(cameras)} cameras")
    print(f"Output directory: {output_dir}")
    print(f"Resolution: {scene.render.resolution_x}x{scene.render.resolution_y}")
    print(f"Engine: {scene.render.engine}")
    print()

    # Render each camera
    for i, cam in enumerate(cameras):
        scene.camera = cam
        output_path = os.path.join(output_dir, cam.name + ".png")
        scene.render.filepath = output_path

        print(f"[{i+1}/{len(cameras)}] Rendering {cam.name}...")
        bpy.ops.render.render(write_still=True)
        print(f"  Saved: {output_path}")

    print(f"\nAll {len(cameras)} renders complete!")


if __name__ == "__main__":
    main()
