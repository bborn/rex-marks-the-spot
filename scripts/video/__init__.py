"""Model-agnostic video generation abstraction layer.

Supports Google Veo, Replicate P-Video, Gemini Omni Flash and fal.ai (MiniMax
H3) behind one interface: a caller asks for image-to-video with these frames for
this duration, and picks a backend.

Usage:
    from video import create_generator

    gen = create_generator("veo-3.1")
    result = gen.generate(prompt="A dinosaur in a jungle", output_path="output.mp4")
    print(f"Cost: ${result.estimated_cost:.3f}, Duration: {result.duration_seconds}s")
"""

from video.base import (
    FIRST_FRAME,
    FIRST_LAST_FRAME,
    REFERENCE_IMAGES,
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
    "FIRST_FRAME",
    "FIRST_LAST_FRAME",
    "REFERENCE_IMAGES",
]


# FalVideoGenerator and OmniFlashGenerator are deliberately NOT imported here:
# each needs its own API key at construction time and importing them eagerly
# would make `import video` fail for anyone who only has the other key.  Reach
# them through create_generator("fal-h3") / create_generator("omni-flash"), or
# import video.fal_video / video.omni_flash directly.
