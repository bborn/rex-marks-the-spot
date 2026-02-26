#!/usr/bin/env python3
"""Google Veo video generation via the google-genai SDK."""

import os
import time
from pathlib import Path
from typing import Optional

from video.base import VideoGenerator, VideoResult


# Cost estimates per second of video (USD).  Google doesn't publish exact
# per-second pricing for all tiers, so these are approximate based on
# publicly available information as of early 2025.
_VEO_COST_PER_SECOND = {
    "veo-2": {
        "720p": 0.02,
        "1080p": 0.04,
        "4k": 0.08,
    },
    "veo-3-generate-preview": {
        "720p": 0.03,
        "1080p": 0.06,
        "4k": 0.12,
    },
    "veo-3.1-generate-preview": {
        "720p": 0.035,
        "1080p": 0.07,
        "4k": 0.14,
    },
}

# Default durations produced by each model variant
_DEFAULT_DURATION = {
    "veo-2": 8,
    "veo-3-generate-preview": 8,
    "veo-3.1-generate-preview": 8,
}


class VeoGenerator(VideoGenerator):
    """Video generation using Google Veo (veo-2, veo-3, veo-3.1).

    Requires the GEMINI_API_KEY environment variable.
    """

    def __init__(
        self,
        model_variant: str = "veo-3.1-generate-preview",
        api_key: Optional[str] = None,
        poll_interval: int = 10,
    ):
        self._variant = model_variant
        self._api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self._api_key:
            raise EnvironmentError(
                "GEMINI_API_KEY environment variable is required for VeoGenerator"
            )
        self._poll_interval = poll_interval

        from google import genai

        self._client = genai.Client(api_key=self._api_key)

    # -- public interface --------------------------------------------------

    @property
    def model_name(self) -> str:
        return f"google-veo ({self._variant})"

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
        from google.genai import types

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        start = time.time()

        # Build config
        config = types.GenerateVideosConfig(
            aspect_ratio=aspect_ratio,
            resolution=resolution,
        )

        # Optional: negative prompt
        if "negative_prompt" in kwargs:
            config.negative_prompt = kwargs["negative_prompt"]

        # Optional: person generation flag
        if "person_generation" in kwargs:
            config.person_generation = kwargs["person_generation"]

        # Build generation call kwargs
        gen_kwargs: dict = {
            "model": self._variant,
            "prompt": prompt,
            "config": config,
        }

        # Image-to-video: load image
        if image_path:
            gen_kwargs["image"] = types.Image.from_file(location=image_path)

        # Submit generation request
        print(f"[VeoGenerator] Submitting to {self._variant}...")
        operation = self._client.models.generate_videos(**gen_kwargs)

        # Poll until done
        while not operation.done:
            print(f"[VeoGenerator] Waiting ({self._poll_interval}s)...")
            time.sleep(self._poll_interval)
            operation = self._client.operations.get(operation)

        elapsed = time.time() - start

        # Download and save
        video = operation.response.generated_videos[0]
        self._client.files.download(file=video.video)
        video.video.save(output_path)
        print(f"[VeoGenerator] Saved to {output_path}")

        actual_duration = _DEFAULT_DURATION.get(self._variant, duration_seconds)
        cost = self.estimate_cost(actual_duration, resolution)

        return VideoResult(
            file_path=output_path,
            duration_seconds=actual_duration,
            model_used=self.model_name,
            estimated_cost=cost,
            generation_time_seconds=round(elapsed, 1),
            metadata={
                "variant": self._variant,
                "aspect_ratio": aspect_ratio,
                "resolution": resolution,
                "prompt": prompt,
                **{k: v for k, v in kwargs.items()},
            },
        )

    def estimate_cost(
        self,
        duration_seconds: int = 8,
        resolution: str = "720p",
        **kwargs,
    ) -> float:
        costs = _VEO_COST_PER_SECOND.get(self._variant, {})
        per_sec = costs.get(resolution, 0.035)
        return round(per_sec * duration_seconds, 4)
