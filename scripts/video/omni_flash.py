#!/usr/bin/env python3
"""Gemini Omni Flash video generation via the google-genai Interactions API.

Requires **google-genai >= 2.0.0**.  The May 2026 breaking change retired the
legacy Interactions schema; SDK 1.x sends the old wire format and the server
rejects every call with:

    The legacy Interactions API schema is no longer supported.
    Please upgrade your google-genai Python SDK to version >= 2.0.0

See https://ai.google.dev/gemini-api/docs/interactions-breaking-changes-may-2026

Reference: https://ai.google.dev/gemini-api/docs/omni

Behaviour confirmed against the live API (Phase 0 smoke test, Aug 2026):

* Duration is set with ``response_format["duration"]``, a duration STRING such
  as ``"5s"``.  Allowed range is **3s-10s**; omitting it defaults to 10s.
  It is NOT ``generation_config.video_config.duration_seconds`` - unknown keys
  under ``video_config`` are silently accepted and ignored, so that spelling
  bills you for a full 10s clip while looking like it worked.
* Every clip carries an **AAC audio stream** and there is no parameter to
  disable it.  A "Silent." instruction in the prompt is NOT a reliable control:
  empty/static shots do come back as near-silent room tone (~-48 dB), but shots
  containing people ignore it and return loud audio (measured -8 dB peaks).
  Strip it unconditionally on ingest: ``ffmpeg -i in.mp4 -c:v copy -an out.mp4``.
* Billing is by **output token**, not per second: a 10s 360p clip is 19,310
  video output tokens.

The Omni video API is a single ``client.interactions.create`` call whose mode is
selected by ``generation_config.video_config.task``.  This wrapper exposes each
of the five task modes as a method while keeping the generic
:class:`~video.base.VideoGenerator` interface, so it drops into the same
comparison harness as ``VeoGenerator`` and ``PVideoGenerator``.
"""

import base64
import mimetypes
import os
import time
from pathlib import Path
from typing import Iterable, Optional, Sequence

from video.base import VideoGenerator, VideoResult


# Task modes accepted by generation_config.video_config.task.  Confirmed
# against the live API (an invalid value echoes back the supported list).
TASKS = ("text_to_video", "image_to_video", "reference_to_video", "edit", "extend")

# Confirmed against the live API by sending deliberately invalid values, which
# makes the server echo the supported set back in the 400 message.
SUPPORTED_RESOLUTIONS = ("360p", "720p", "1080p", "4k")
SUPPORTED_ASPECT_RATIOS = ("16:9", "9:16")

# Duration is a string on response_format ("5s"), NOT a video_config int.
MIN_DURATION_SECONDS = 3
MAX_DURATION_SECONDS = 10
DEFAULT_DURATION_SECONDS = 10  # what the API produces when duration is omitted

# Prompt tags used to bind an entry of the ``input`` array to a role.
TAG_FIRST_FRAME = "<FIRST_FRAME>"
TAG_LAST_FRAME = "<LAST_FRAME>"


# ---------------------------------------------------------------------------
# Pricing
# ---------------------------------------------------------------------------
# Omni bills by OUTPUT TOKEN, not per second.  Published rates (Aug 2026):
#   input  (text / image / video / audio): $1.50 per 1M tokens
#   output (video):                        $17.50 per 1M tokens
# Google quotes ~$0.10/s for 720p via "5,792 tokens per second of 720p video".
# Measured at 360p: a 10s clip is 19,310 video output tokens => 1,931 tokens/s,
# i.e. ~$0.0338/s.  Prefer `cost_from_usage()` on a real response over the
# per-second table below, which is only for pre-flight estimates.
USD_PER_1M_VIDEO_OUTPUT_TOKENS = 17.50
USD_PER_1M_INPUT_TOKENS = 1.50
USD_PER_1M_TEXT_OUTPUT_TOKENS = 17.50  # upper bound; text output is a rounding error here

# Measured video output tokens per second of generated video, by resolution.
# Only 360p is measured; the rest scale off Google's 720p figure.
_TOKENS_PER_SECOND = {
    "360p": 1931.0,
    "720p": 5792.0,
    "1080p": 5792.0 * 2.25,
    "4k": 5792.0 * 9.0,
}




def cost_from_usage(usage) -> float:
    """Exact USD cost for one interaction, from its reported token usage.

    This is the number to quote for real spend - the per-second table is an
    estimate, this is what was actually billed.
    """
    u = _as_dict(usage) or {}
    video_out = 0
    for entry in u.get("output_tokens_by_modality") or []:
        if entry.get("modality") == "video":
            video_out += entry.get("tokens", 0)
    total_out = u.get("total_output_tokens", 0) or 0
    other_out = max(total_out - video_out, 0)
    inp = u.get("total_input_tokens", 0) or 0
    return round(
        video_out * USD_PER_1M_VIDEO_OUTPUT_TOKENS / 1e6
        + other_out * USD_PER_1M_TEXT_OUTPUT_TOKENS / 1e6
        + inp * USD_PER_1M_INPUT_TOKENS / 1e6,
        6,
    )


class OmniFlashGenerator(VideoGenerator):
    """Video generation using Gemini Omni Flash.

    Requires the GEMINI_API_KEY environment variable (or an explicit api_key).

    Args:
        model_variant: Model id.  ``gemini-omni-1.1-flash`` is the id the API
            itself suggests; ``gemini-omni-flash-preview`` also resolves.
        api_key: API key; falls back to ``GEMINI_API_KEY``.
        cost_per_second: Optional ``{resolution: usd_per_second}`` override.
    """

    def __init__(
        self,
        model_variant: str = "gemini-omni-1.1-flash",
        api_key: Optional[str] = None,
        cost_per_second: Optional[dict] = None,
    ):
        self._variant = model_variant
        self._api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self._api_key:
            raise EnvironmentError(
                "GEMINI_API_KEY environment variable is required for OmniFlashGenerator"
            )
        self._costs = cost_per_second

        from google import genai

        self._client = genai.Client(api_key=self._api_key)

    # -- public interface --------------------------------------------------

    @property
    def model_name(self) -> str:
        return f"gemini-omni-flash ({self._variant})"

    def generate(
        self,
        prompt: str,
        output_path: str,
        duration_seconds: int = DEFAULT_DURATION_SECONDS,
        aspect_ratio: str = "16:9",
        resolution: str = "360p",
        image_path: Optional[str] = None,
        *,
        task: str = "text_to_video",
        reference_images: Optional[Sequence[str]] = None,
        first_frame: Optional[str] = None,
        last_frame: Optional[str] = None,
        video_path: Optional[str] = None,
        **kwargs,
    ) -> VideoResult:
        """Generate a video.

        ``image_path`` is accepted for interface compatibility with the other
        generators and is treated as the first frame when the task is
        ``image_to_video``.

        Args:
            prompt: Text prompt.  Any ``<IMAGE_REF_n>`` / ``<FIRST_FRAME>`` /
                ``<LAST_FRAME>`` tags already present are left alone; missing
                tags for supplied images are prepended automatically.
            output_path: Where to write the .mp4.
            duration_seconds: Output length in seconds, 3-10.  Sent as
                ``response_format["duration"] = f"{n}s"``.
            aspect_ratio: "16:9" or "9:16".
            resolution: "360p", "720p", "1080p" or "4k".
            image_path: Convenience alias for ``first_frame``.
            task: One of :data:`TASKS`.
            reference_images: Paths bound to ``<IMAGE_REF_0..n>``.
            first_frame / last_frame: Paths bound to the frame tags.
            video_path: Source video for ``edit`` / ``extend``.

        Returns:
            VideoResult.
        """
        if task not in TASKS:
            raise ValueError(f"task must be one of {TASKS}, got {task!r}")
        if resolution not in SUPPORTED_RESOLUTIONS:
            raise ValueError(
                f"resolution must be one of {SUPPORTED_RESOLUTIONS}, got {resolution!r}"
            )
        if aspect_ratio not in SUPPORTED_ASPECT_RATIOS:
            raise ValueError(
                f"aspect_ratio must be one of {SUPPORTED_ASPECT_RATIOS}, "
                f"got {aspect_ratio!r}"
            )
        if not MIN_DURATION_SECONDS <= duration_seconds <= MAX_DURATION_SECONDS:
            raise ValueError(
                f"duration_seconds must be between {MIN_DURATION_SECONDS} and "
                f"{MAX_DURATION_SECONDS}, got {duration_seconds!r}"
            )

        if image_path and not first_frame:
            first_frame = image_path

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        start = time.time()

        payload, prompt = self._build_input(
            prompt,
            reference_images=reference_images or [],
            first_frame=first_frame,
            last_frame=last_frame,
            video_path=video_path,
        )

        request = {
            "model": self._variant,
            "input": payload,
            "response_format": {
                "type": "video",
                "aspect_ratio": aspect_ratio,
                "resolution": resolution,
                "duration": f"{duration_seconds}s",
            },
            "generation_config": {"video_config": {"task": task}},
        }

        print(f"[OmniFlash] {task} -> {self._variant} @ {resolution} {aspect_ratio}")
        interaction = self._client.interactions.create(**request)

        elapsed = time.time() - start
        written = self._save_video(interaction, output_path)
        print(f"[OmniFlash] Saved {written} bytes to {output_path}")

        return VideoResult(
            file_path=output_path,
            duration_seconds=duration_seconds,
            model_used=self.model_name,
            estimated_cost=cost_from_usage(getattr(interaction, "usage", None)),
            generation_time_seconds=round(elapsed, 1),
            metadata={
                "variant": self._variant,
                "task": task,
                "aspect_ratio": aspect_ratio,
                "resolution": resolution,
                "duration_seconds": duration_seconds,
                "prompt": prompt,
                "reference_images": list(reference_images or []),
                "first_frame": first_frame,
                "last_frame": last_frame,
                "bytes": written,
                "usage": _as_dict(getattr(interaction, "usage", None)),
                "estimated_cost_preflight": self.estimate_cost(
                    duration_seconds, resolution
                ),
                "interaction_id": getattr(interaction, "id", None),
                **kwargs,
            },
        )

    # -- task-mode conveniences -------------------------------------------

    def text_to_video(self, prompt: str, output_path: str, **kw) -> VideoResult:
        return self.generate(prompt, output_path, task="text_to_video", **kw)

    def image_to_video(
        self, prompt: str, output_path: str, first_frame: str, **kw
    ) -> VideoResult:
        return self.generate(
            prompt, output_path, task="image_to_video", first_frame=first_frame, **kw
        )

    def reference_to_video(
        self, prompt: str, output_path: str, reference_images: Sequence[str], **kw
    ) -> VideoResult:
        return self.generate(
            prompt,
            output_path,
            task="reference_to_video",
            reference_images=reference_images,
            **kw,
        )

    def edit(self, prompt: str, output_path: str, video_path: str, **kw) -> VideoResult:
        return self.generate(prompt, output_path, task="edit", video_path=video_path, **kw)

    def extend(self, prompt: str, output_path: str, video_path: str, **kw) -> VideoResult:
        return self.generate(
            prompt, output_path, task="extend", video_path=video_path, **kw
        )

    def estimate_cost(
        self, duration_seconds: int = DEFAULT_DURATION_SECONDS,
        resolution: str = "360p", **kwargs
    ) -> float:
        """Pre-flight estimate.  For real spend use :func:`cost_from_usage`."""
        if self._costs:
            return round(self._costs.get(resolution, 0.0338) * duration_seconds, 4)
        tps = _TOKENS_PER_SECOND.get(resolution, _TOKENS_PER_SECOND["360p"])
        return round(tps * duration_seconds * USD_PER_1M_VIDEO_OUTPUT_TOKENS / 1e6, 4)

    # -- internals ---------------------------------------------------------

    def _build_input(
        self,
        prompt: str,
        reference_images: Sequence[str],
        first_frame: Optional[str],
        last_frame: Optional[str],
        video_path: Optional[str],
    ) -> tuple[list, str]:
        """Assemble the ``input`` array and auto-tag the prompt.

        The API binds each media entry to the prompt by tag, not by position, so
        an untagged prompt silently ignores its images.  Any tag the caller has
        already written is respected; only missing ones are prepended.
        """
        items: list = []
        prefix: list[str] = []

        if first_frame:
            items.append(_media_part(first_frame))
            if TAG_FIRST_FRAME not in prompt:
                prefix.append(TAG_FIRST_FRAME)
        if last_frame:
            items.append(_media_part(last_frame))
            if TAG_LAST_FRAME not in prompt:
                prefix.append(TAG_LAST_FRAME)
        if video_path:
            items.append(_media_part(video_path))
            if "<VIDEO_REF_0>" not in prompt:
                prefix.append("<VIDEO_REF_0>")

        for i, ref in enumerate(reference_images):
            items.append(_media_part(ref))
            tag = f"<IMAGE_REF_{i}>"
            if tag not in prompt:
                prefix.append(tag)

        if prefix:
            prompt = " ".join(prefix) + " " + prompt

        items.append({"type": "text", "text": prompt})
        return items, prompt

    def _save_video(self, interaction, output_path: str) -> int:
        """Pull the first video payload out of an Interaction and write it."""
        # Fast path: SDK 2.x exposes a flattened `output_video` convenience field.
        data = None
        ov = getattr(interaction, "output_video", None)
        raw = getattr(ov, "data", None) if ov is not None else None
        if isinstance(raw, bytes):
            data = raw
        elif isinstance(raw, str):
            data = base64.b64decode(raw)
        if data is None:
            data = _extract_video_bytes(interaction)
        if data is None:
            uri = _extract_video_uri(interaction)
            if uri:
                data = self._download(uri)
        if data is None:
            raise RuntimeError(
                "No video payload in the response. Raw interaction:\n"
                f"{_as_dict(interaction)}"
            )
        Path(output_path).write_bytes(data)
        return len(data)

    def _download(self, uri: str) -> bytes:
        import httpx

        headers = {"x-goog-api-key": self._api_key}
        resp = httpx.get(uri, headers=headers, follow_redirects=True, timeout=300)
        resp.raise_for_status()
        return resp.content


# ---------------------------------------------------------------------------
# Response walking
#
# The Interactions response is a `steps` array of structured, type-discriminated
# steps whose exact nesting varies by task.  Rather than hard-code one path, walk
# the whole structure for the first video-ish payload.
# ---------------------------------------------------------------------------


def _as_dict(obj):
    """Best-effort conversion of an SDK model to plain dict/list/scalars."""
    if obj is None or isinstance(obj, (str, int, float, bool, bytes)):
        return obj
    for attr in ("model_dump", "dict", "to_json_dict"):
        fn = getattr(obj, attr, None)
        if callable(fn):
            try:
                return fn()
            except Exception:
                pass
    if isinstance(obj, dict):
        return {k: _as_dict(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_as_dict(v) for v in obj]
    return obj


def _walk(node) -> Iterable[dict]:
    """Yield every dict in a nested dict/list structure."""
    if isinstance(node, dict):
        yield node
        for v in node.values():
            yield from _walk(v)
    elif isinstance(node, (list, tuple)):
        for v in node:
            yield from _walk(v)


def _extract_video_bytes(interaction) -> Optional[bytes]:
    for node in _walk(_as_dict(interaction)):
        mime = str(node.get("mime_type") or node.get("mimeType") or "")
        kind = str(node.get("type") or "")
        if "video" not in mime and kind != "video":
            continue
        for key in ("data", "bytes", "inline_data", "inlineData", "video_bytes"):
            val = node.get(key)
            if isinstance(val, bytes):
                return val
            if isinstance(val, str) and len(val) > 1024:
                try:
                    return base64.b64decode(val)
                except Exception:
                    continue
    return None


def _extract_video_uri(interaction) -> Optional[str]:
    for node in _walk(_as_dict(interaction)):
        mime = str(node.get("mime_type") or node.get("mimeType") or "")
        kind = str(node.get("type") or "")
        if "video" not in mime and kind != "video":
            continue
        for key in ("uri", "url", "file_uri", "fileUri", "download_uri"):
            val = node.get(key)
            if isinstance(val, str) and val.startswith("http"):
                return val
    return None


def _media_part(path: str) -> dict:
    """Base64-encode a local image/video into an ``input`` array entry."""
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"media not found: {path}")
    mime = mimetypes.guess_type(p.name)[0] or "application/octet-stream"
    kind = "video" if mime.startswith("video/") else "image"
    return {
        "type": kind,
        "data": base64.b64encode(p.read_bytes()).decode(),
        "mime_type": mime,
    }
