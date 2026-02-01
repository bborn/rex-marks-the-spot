"""
Headless Render Pipeline

This package provides utilities for running Blender renders headlessly
from the command line or from external Python scripts.

Modules:
    engine: Core render engine controller for headless execution
    batch: Batch rendering support for multiple scenes/frames

Usage (from outside Blender):
    from render import engine, batch

    # Render a single scene
    result = engine.render_script(
        script_path='scene_setup.py',
        output_path='render.png',
        samples=128
    )

    # Batch render multiple scenes
    results = batch.render_scenes([
        {'script': 'scene1.py', 'output': 'scene1.png'},
        {'script': 'scene2.py', 'output': 'scene2.png'},
    ])
"""

from . import engine
from . import batch

__all__ = ['engine', 'batch']
