#!/usr/bin/env python3
"""Replicate P-Video generation via the replicate Python SDK."""

import os
import time
import urllib.request
from pathlib import Path
from typing import Optional

from video.base import VideoGenerator, VideoResult

# Pricing: USD per second of generated video
_PVIDEO_COST = {
    # (draft, resolution) -> cost per second
    (False, "720p"): 0.02,
    (False, "1080p"): 0.04,
    (True, "720p"): 0.005,
    (True, "1080p"): 0.01,
}

REPLICATE_MODEL = "prunaai/p-video"


class PVideoGenerator(VideoGenerator):
    """Video generation using Replicate P-Video (prunaai/p-video).

    Supports text-to-video, image-to-video, and audio-to-video.
    Requires the REPLICATE_API_TOKEN environment variable.
    """

    def __init__(
        self,
        draft: bool = False,
        api_token: Optional[str] = None,
    ):
        self._draft = draft
        self._api_token = api_token or os.environ.get("REPLICATE_API_TOKEN")
        if not self._api_token:
            raise EnvironmentError(
                "REPLICATE_API_TOKEN environment variable is required for PVideoGenerator"
            )
        os.environ["REPLICATE_API_TOKEN"] = self._api_token

        import replicate

        self._client = replicate.Client(api_token=self._api_token)

    # -- public interface --------------------------------------------------

    @property
    def model_name(self) -> str:
        mode = "draft" if self._draft else "standard"
        return f"replicate-p-video ({mode})"

    def generate(
        self,
        prompt: str,
        output_path: str,
        duration_seconds: int = 5,
        aspect_ratio: str = "16:9",
        resolution: str = "720p",
        image_path: Optional[str] = None,
        **kwargs,
    ) -> VideoResult:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        start = time.time()

        # Build input payload
        input_data: dict = {
            "prompt": prompt,
            "duration": min(max(duration_seconds, 1), 10),
            "aspect_ratio": aspect_ratio,
            "resolution": resolution,
            "fps": kwargs.get("fps", 24),
            "draft": self._draft,
            "prompt_upsampling": kwargs.get("prompt_upsampling", True),
        }

        if "seed" in kwargs:
            input_data["seed"] = kwargs["seed"]

        # Image input
        if image_path:
            input_data["image"] = open(image_path, "rb")

        # Audio input
        audio_path = kwargs.get("audio_path")
        if audio_path:
            input_data["audio"] = open(audio_path, "rb")

        print(f"[PVideoGenerator] Submitting to {REPLICATE_MODEL} (draft={self._draft})...")
        output = self._client.run(REPLICATE_MODEL, input=input_data)

        elapsed = time.time() - start

        # Close any file handles we opened
        if image_path and hasattr(input_data.get("image"), "close"):
            input_data["image"].close()
        if audio_path and hasattr(input_data.get("audio"), "close"):
            input_data["audio"].close()

        # Download output video
        video_url = self._extract_url(output)
        print(f"[PVideoGenerator] Downloading from {video_url[:80]}...")
        urllib.request.urlretrieve(video_url, output_path)
        print(f"[PVideoGenerator] Saved to {output_path}")

        actual_duration = input_data["duration"]
        cost = self.estimate_cost(actual_duration, resolution)

        return VideoResult(
            file_path=output_path,
            duration_seconds=actual_duration,
            model_used=self.model_name,
            estimated_cost=cost,
            generation_time_seconds=round(elapsed, 1),
            metadata={
                "replicate_model": REPLICATE_MODEL,
                "draft": self._draft,
                "fps": input_data["fps"],
                "aspect_ratio": aspect_ratio,
                "resolution": resolution,
                "prompt": prompt,
                "video_url": video_url,
            },
        )

    def estimate_cost(
        self,
        duration_seconds: int = 5,
        resolution: str = "720p",
        **kwargs,
    ) -> float:
        draft = kwargs.get("draft", self._draft)
        key = (draft, resolution)
        per_sec = _PVIDEO_COST.get(key, 0.02)
        return round(per_sec * duration_seconds, 4)

    # -- helpers -----------------------------------------------------------

    @staticmethod
    def _extract_url(output) -> str:
        """Extract video URL from replicate output (may be str, FileOutput, or list)."""
        if isinstance(output, str):
            return output
        if isinstance(output, list):
            return str(output[0])
        # replicate.helpers.FileOutput or similar
        return str(output)
