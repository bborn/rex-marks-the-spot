"""
Blender Automation Modules

This package provides reusable utilities for Blender scene creation,
manipulation, and rendering via the bpy API.

Modules:
    scene: Scene setup and management
    objects: Object creation and manipulation
    materials: Material and shader utilities
    lighting: Lighting setup helpers
    camera: Camera positioning and configuration
    render: Render settings and output configuration

Usage:
    These modules are designed to be imported within Blender's Python
    environment, either through the GUI or via headless execution:

        blender -b -P your_script.py

    Example:
        from blender import scene, objects, lighting, camera, render

        scene.clear()
        objects.create_ground(size=20)
        lighting.three_point_setup()
        camera.setup_main((6, -6, 4), target=(0, 0, 1))
        render.configure(output_path='render.png')
        render.execute()
"""

# When running inside Blender, these imports will work
# When running outside (for type checking), they'll fail gracefully
try:
    from . import scene
    from . import objects
    from . import materials
    from . import lighting
    from . import camera
    from . import render

    __all__ = ['scene', 'objects', 'materials', 'lighting', 'camera', 'render']
except ImportError:
    # Running outside Blender environment
    pass
