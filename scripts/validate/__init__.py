"""
Vision Validation Module

Integrates with Claude Vision API to analyze rendered images
and provide feedback for the iterative render loop.

Modules:
    vision: Claude Vision API integration for render validation

Usage:
    from validate import vision

    # Validate a single render
    result = vision.validate_render(
        image_path='render.png',
        scene_description='A forest scene with trees and a character'
    )

    if result.needs_changes:
        print(result.suggestions)
"""

from . import vision

__all__ = ['vision']
