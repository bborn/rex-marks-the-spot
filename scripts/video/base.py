#!/usr/bin/env python3
"""Base abstraction for video generation models."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Capabilities
#
# Backends differ in what conditioning they accept, and the difference is not
# cosmetic: asking a backend for a last frame it cannot honour produces a clip
# that silently ignores the anchor.  Declaring capabilities lets a caller pick
# a backend for a shot instead of hard-coding one.
# ---------------------------------------------------------------------------

#: Accepts a first frame (image-to-video conditioning).
FIRST_FRAME = "first_frame"
#: Accepts a first AND a last frame in one call (keyframe interpolation).
FIRST_LAST_FRAME = "first_last_frame"
#: Accepts free-floating reference images (character/style conditioning).
REFERENCE_IMAGES = "reference_images"


@dataclass
class VideoResult:
    """Result from a video generation request."""

    file_path: str
    duration_seconds: float
    model_used: str
    estimated_cost: float
    generation_time_seconds: float
    metadata: dict = field(default_factory=dict)


class VideoGenerator(ABC):
    """Abstract base class for video generation models."""

    #: What conditioning this backend accepts.  See the module constants.
    capabilities: frozenset = frozenset()

    def supports(self, capability: str) -> bool:
        """Return True if this backend accepts ``capability``."""
        return capability in self.capabilities

    def image_to_video(
        self,
        prompt: str,
        output_path: str,
        first_frame: str,
        last_frame: Optional[str] = None,
        **kwargs,
    ) -> "VideoResult":
        """Generate a clip conditioned on a first (and optionally last) frame.

        This is the model-agnostic entry point: a caller asks for
        "image-to-video, these frames, this duration" and the backend it picked
        does the rest.  A backend that cannot honour a last frame raises rather
        than quietly dropping it - a dropped anchor looks like a successful
        render right up until the continuity gate fails it.
        """
        if last_frame is not None and not self.supports(FIRST_LAST_FRAME):
            raise NotImplementedError(
                f"{self.model_name} does not support last-frame conditioning. "
                f"Use a backend whose capabilities include {FIRST_LAST_FRAME!r} "
                f"(e.g. create_generator('fal-h3'))."
            )
        if last_frame is not None:
            kwargs["last_frame"] = last_frame
        return self.generate(prompt, output_path, image_path=first_frame, **kwargs)

    @abstractmethod
    def generate(
        self,
        prompt: str,
        output_path: str,
        duration_seconds: int = 8,
        aspect_ratio: str = "16:9",
        resolution: str = "720p",
        image_path: Optional[str] = None,
        **kwargs,
    ) -> VideoResult:
        """Generate a video from a text prompt and optional image.

        Args:
            prompt: Text description of the video to generate.
            output_path: Local path to save the generated video.
            duration_seconds: Desired video length in seconds.
            aspect_ratio: Aspect ratio (e.g. "16:9", "9:16").
            resolution: Resolution (e.g. "720p", "1080p", "4k").
            image_path: Optional path to an input image for image-to-video.
            **kwargs: Model-specific parameters.

        Returns:
            VideoResult with file path, cost, and metadata.
        """
        ...

    @abstractmethod
    def estimate_cost(
        self,
        duration_seconds: int = 8,
        resolution: str = "720p",
        **kwargs,
    ) -> float:
        """Estimate the cost of generating a video without running it.

        Args:
            duration_seconds: Desired video length.
            resolution: Resolution.
            **kwargs: Model-specific parameters.

        Returns:
            Estimated cost in USD.
        """
        ...

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return a human-readable model identifier."""
        ...


# Registry of model name -> (class, kwargs) for the factory
_REGISTRY: dict[str, tuple[type, dict]] = {}


def _register(name: str, cls: type, **default_kwargs):
    """Register a generator class under one or more model names."""
    _REGISTRY[name] = (cls, default_kwargs)


def create_generator(model: str, **kwargs) -> VideoGenerator:
    """Factory: create a VideoGenerator by model name.

    Supported model names:
        - "veo-2", "veo-3", "veo-3.1" -> VeoGenerator
        - "p-video", "p-video-draft"   -> PVideoGenerator
        - "omni-flash", "omni-flash-preview" -> OmniFlashGenerator
        - "fal-h3", "fal-h3-t2v", "fal-h3-ref" -> FalVideoGenerator

    Args:
        model: Model identifier string.
        **kwargs: Passed through to the generator constructor.

    Returns:
        An initialised VideoGenerator instance.

    Raises:
        ValueError: If the model name is not recognised.
    """
    # Lazy-import so the registry is populated
    _ensure_registry()

    key = model.lower().strip()
    if key not in _REGISTRY:
        available = ", ".join(sorted(_REGISTRY.keys()))
        raise ValueError(
            f"Unknown model '{model}'. Available: {available}"
        )

    cls, defaults = _REGISTRY[key]
    merged = {**defaults, **kwargs}
    return cls(**merged)


def _ensure_registry():
    """Populate the registry on first call."""
    if _REGISTRY:
        return

    from video.veo_generator import VeoGenerator
    from video.pvideo_generator import PVideoGenerator
    from video.omni_flash import OmniFlashGenerator
    from video.fal_video import (
        ENDPOINT_H3_IMAGE_TO_VIDEO,
        ENDPOINT_H3_REFERENCE_TO_VIDEO,
        ENDPOINT_H3_TEXT_TO_VIDEO,
        FalVideoGenerator,
    )

    _register("veo-2", VeoGenerator, model_variant="veo-2")
    _register("veo-3", VeoGenerator, model_variant="veo-3-generate-preview")
    _register("veo-3.1", VeoGenerator, model_variant="veo-3.1-generate-preview")
    _register("p-video", PVideoGenerator, draft=False)
    _register("p-video-draft", PVideoGenerator, draft=True)
    _register("omni-flash", OmniFlashGenerator, model_variant="gemini-omni-1.1-flash")
    _register(
        "omni-flash-preview", OmniFlashGenerator,
        model_variant="gemini-omni-flash-preview",
    )
    _register("fal-h3", FalVideoGenerator, endpoint=ENDPOINT_H3_IMAGE_TO_VIDEO)
    _register("fal-h3-i2v", FalVideoGenerator, endpoint=ENDPOINT_H3_IMAGE_TO_VIDEO)
    _register("fal-h3-t2v", FalVideoGenerator, endpoint=ENDPOINT_H3_TEXT_TO_VIDEO)
    _register("fal-h3-ref", FalVideoGenerator, endpoint=ENDPOINT_H3_REFERENCE_TO_VIDEO)
