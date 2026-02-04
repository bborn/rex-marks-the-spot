#!/usr/bin/env python3
"""
Render Scene Assembly Test
==========================

Quick test to verify the scene assembly workflow produces valid renders.

Usage:
    blender -b -P scripts/render_scene_assembly_test.py

This will:
1. Clear the scene
2. Create placeholder characters
3. Set up lighting and camera
4. Render a single test frame
"""

import bpy
import sys
import os

# Add scripts directory to path
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

# Import the scene assembly module
import scene_assembly as sa

def main():
    print("\n" + "=" * 60)
    print("SCENE ASSEMBLY RENDER TEST")
    print("=" * 60)

    # Assemble the test scene
    sa.assemble_test_scene()

    # Configure for quick preview
    scene = bpy.context.scene
    render = scene.render

    # Very low quality for quick test
    render.resolution_x = 1280
    render.resolution_y = 720
    render.resolution_percentage = 100

    # Output path
    output_dir = os.path.join(os.path.dirname(script_dir), 'renders', 'test')
    os.makedirs(output_dir, exist_ok=True)
    render.filepath = os.path.join(output_dir, 'scene_assembly_test.png')
    render.image_settings.file_format = 'PNG'

    # Use EEVEE for speed (engine name varies by Blender version)
    try:
        scene.render.engine = 'BLENDER_EEVEE_NEXT'  # Blender 4.2+
    except TypeError:
        scene.render.engine = 'BLENDER_EEVEE'  # Blender 4.0-4.1
    scene.eevee.taa_render_samples = 16

    print(f"\nRendering to: {render.filepath}")
    print(f"Resolution: {render.resolution_x}x{render.resolution_y}")
    print(f"Engine: EEVEE")

    # Render
    bpy.ops.render.render(write_still=True)

    print("\n" + "=" * 60)
    print("RENDER COMPLETE!")
    print("=" * 60)
    print(f"\nOutput: {render.filepath}")

    # Verify output exists
    if os.path.exists(render.filepath):
        file_size = os.path.getsize(render.filepath)
        print(f"File size: {file_size / 1024:.1f} KB")
        print("SUCCESS: Scene assembly workflow verified!")
    else:
        print("ERROR: Render output not found!")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
