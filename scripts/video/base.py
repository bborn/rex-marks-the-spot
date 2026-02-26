#!/usr/bin/env python3
"""Base abstraction for video generation models."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


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

    _register("veo-2", VeoGenerator, model_variant="veo-2")
    _register("veo-3", VeoGenerator, model_variant="veo-3-generate-preview")
    _register("veo-3.1", VeoGenerator, model_variant="veo-3.1-generate-preview")
    _register("p-video", PVideoGenerator, draft=False)
    _register("p-video-draft", PVideoGenerator, draft=True)
