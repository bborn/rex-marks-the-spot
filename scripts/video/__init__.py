"""Model-agnostic video generation abstraction layer.

Supports Google Veo and Replicate P-Video with a unified interface.

Usage:
    from video import create_generator

    gen = create_generator("veo-3.1")
    result = gen.generate(prompt="A dinosaur in a jungle", output_path="output.mp4")
    print(f"Cost: ${result.estimated_cost:.3f}, Duration: {result.duration_seconds}s")
"""

from video.base import (
    VideoGenerator,
    VideoResult,
    create_generator,
)
from video.veo_generator import VeoGenerator
from video.pvideo_generator import PVideoGenerator

__all__ = [
    "VideoGenerator",
    "VideoResult",
    "VeoGenerator",
    "PVideoGenerator",
    "create_generator",
]
