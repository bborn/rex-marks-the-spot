#!/usr/bin/env python3
"""fal.ai video generation, primarily MiniMax H3.

Second provider behind :class:`~video.base.VideoGenerator`, alongside Omni.
It exists for two things Omni cannot do:

1. **First frame AND last frame in one call.**  ``image_url`` + ``end_image_url``
   on ``minimax/h3/image-to-video`` renders a clip that starts on panel A and
   lands on panel B.  Last-frame anchoring moved a failing shot from 0.231 to
   0.741 on the continuity gate, so this is the core workflow, not a nicety.
2. **Shots Google refuses.**  Scene 17 (two children alone in a police car) is
   unmakeable on Omni in any wording; it rendered on H3 first try with
   ``enable_safety_checker`` left at its default ``true``.

It is also about half the price: $0.06/s at 768P vs Omni's measured $0.104/s.

Everything below was read off the live endpoint schema
(``https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=minimax/h3/image-to-video``),
not inferred:

* ``duration`` is an INTEGER number of seconds, **minimum 5**, maximum 15.  There
  is no 3s option - a 3s shot is a 5s bill.  :meth:`FalVideoGenerator.generate`
  says so out loud and records both numbers in the sidecar rather than quietly
  rounding up your invoice.
* ``resolution`` is one of ``480P``, ``768P``, ``2K``, ``4K`` - and the API's own
  default is **2K at $0.13/s**, more than double 768P.  This wrapper therefore
  always sends an explicit resolution and defaults to 768P.
* Aspect ratio is not a parameter: the output follows the input image.  Send a
  9:16 panel, get a 9:16 clip.
* Audio cannot be disabled.  Strip it on ingest - ``strip_audio=True`` runs
  ``ffmpeg -i in.mp4 -c:v copy -an out.mp4`` before the file is kept.
* Output lands on fal's CDN and **those URLs expire in about 7 days**, so the
  wrapper downloads the file and pushes it to R2 as part of the call.  A clip we
  cannot fetch next week is a clip we do not have.
* New accounts are capped at **2 concurrent requests**; :meth:`generate_batch`
  defaults to that.

The transport is plain ``httpx`` against the queue API rather than the
``fal_client`` SDK: submit, poll, fetch.  That keeps the dependency list short
and makes the request shape testable without spending money.
"""

import base64
import json
import mimetypes
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable, Optional, Sequence

from video.base import (
    FIRST_FRAME,
    FIRST_LAST_FRAME,
    REFERENCE_IMAGES,
    VideoGenerator,
    VideoResult,
)


QUEUE_BASE = "https://queue.fal.run"

ENDPOINT_H3_IMAGE_TO_VIDEO = "minimax/h3/image-to-video"
ENDPOINT_H3_TEXT_TO_VIDEO = "minimax/h3/text-to-video"
ENDPOINT_H3_REFERENCE_TO_VIDEO = "minimax/h3/reference-to-video"

# fal's own default is 2K ($0.13/s).  Never inherit it.
DEFAULT_RESOLUTION = "768P"
SUPPORTED_RESOLUTIONS = ("480P", "768P", "2K", "4K")

# Schema minimum AND billing minimum: the endpoint rejects duration < 5, and a
# shorter shot is still a 5-second bill.  Trim in the edit, not in the request.
MIN_BILLABLE_SECONDS = 5
MAX_DURATION_SECONDS = 15
DEFAULT_DURATION_SECONDS = 5

# New fal accounts are capped at 2 concurrent requests.  Raising this on an
# uncapped account is a one-line change at the call site.
DEFAULT_MAX_CONCURRENCY = 2

# fal CDN output URLs stop resolving after roughly a week.
CDN_URL_LIFETIME_DAYS = 7

# image-to-video has no aspect_ratio parameter - the output follows the input
# image, which is why we are not locked to 16:9.  The text- and
# reference-to-video endpoints do take one, from this enum.
ENDPOINTS_WITHOUT_ASPECT_RATIO = frozenset({ENDPOINT_H3_IMAGE_TO_VIDEO})
SUPPORTED_ASPECT_RATIOS = (
    "adaptive", "21:9", "16:9", "4:3", "1:1", "3:4", "9:16",
)

_TERMINAL_OK = "COMPLETED"
_STATUS_POLLING = ("IN_QUEUE", "IN_PROGRESS")


# ---------------------------------------------------------------------------
# Pricing - published USD per second of generated video, by endpoint.
#
# Source: the fal model catalogue (fal.ai/api/models), read Aug 2026.  These are
# list rates used for pre-flight estimates and the sidecar; fal does not return
# a billed amount on the response, so the sidecar records what the published
# rate says this clip cost.
# ---------------------------------------------------------------------------

_H3_RATES = {"480P": 0.05, "768P": 0.06, "2K": 0.13, "4K": 0.16}

USD_PER_SECOND: dict[str, dict[str, float]] = {
    ENDPOINT_H3_IMAGE_TO_VIDEO: dict(_H3_RATES),
    ENDPOINT_H3_TEXT_TO_VIDEO: dict(_H3_RATES),
    # Reference-to-video: first 5 reference images free, $0.08 each after that.
    ENDPOINT_H3_REFERENCE_TO_VIDEO: dict(_H3_RATES),
    # h3-max is a post-trained variant on a PROMOTIONAL rate that ends 1 Sept
    # 2026, after which 480P is $0.05/s and 768P is $0.08/s - i.e. more
    # expensive than plain h3 at 768P.  Rates below are the POST-promo ones so
    # an estimate can never come in under the real bill.
    "minimax/h3-max/image-to-video": {"480P": 0.05, "768P": 0.08},
    "minimax/h3-max/text-to-video": {"480P": 0.05, "768P": 0.08},
}

#: Endpoints whose advertised price is a launch promo that will rise.  Building
#: a pipeline on one of these buys a price increase, so the wrapper warns.
PROMOTIONAL_ENDPOINTS = frozenset(
    {"minimax/h3-max/image-to-video", "minimax/h3-max/text-to-video"}
)

# Free reference images per reference-to-video request, then $0.08 each.
FREE_REFERENCE_IMAGES = 5
USD_PER_EXTRA_REFERENCE_IMAGE = 0.08

# Resolutions callers may type that map cleanly onto the H3 enum.  "1080p" is
# deliberately absent: it sits between 768P and 2K, and guessing upward would
# silently double the rate.
_RESOLUTION_ALIASES = {
    "480p": "480P",
    "768p": "768P",
    "720p": "768P",  # nearest native mode; 2K/4K are upscales of a 768P base
    "2k": "2K",
    "4k": "4K",
}


class FalError(RuntimeError):
    """A fal request failed, was rejected, or came back without a video."""


class FalVideoGenerator(VideoGenerator):
    """Video generation on fal.ai, defaulting to MiniMax H3 image-to-video.

    Requires ``FAL_KEY`` in the environment (or an explicit ``api_key``).  The
    key is never printed, logged, or written to a sidecar.

    Args:
        endpoint: fal endpoint id, e.g. ``minimax/h3/image-to-video``.
        api_key: fal key; falls back to ``FAL_KEY``.
        poll_interval_seconds: Gap between queue status polls.
        timeout_seconds: Give up on a queued request after this long.
        http: Optional transport with ``.post`` / ``.get`` (an ``httpx.Client``).
            Injected by the tests so they never touch the network.
        uploader: Optional ``(local_path, r2_path) -> url`` callable, defaulting
            to :func:`r2_upload.upload_file`.
    """

    capabilities = frozenset({FIRST_FRAME, FIRST_LAST_FRAME, REFERENCE_IMAGES})

    def __init__(
        self,
        endpoint: str = ENDPOINT_H3_IMAGE_TO_VIDEO,
        api_key: Optional[str] = None,
        *,
        poll_interval_seconds: float = 5.0,
        timeout_seconds: float = 1800.0,
        http=None,
        uploader: Optional[Callable[[str, str], str]] = None,
    ):
        self._endpoint = endpoint.strip("/")
        self._api_key = api_key or os.environ.get("FAL_KEY")
        if not self._api_key:
            raise EnvironmentError(
                "FAL_KEY environment variable is required for FalVideoGenerator"
            )
        self._poll_interval = poll_interval_seconds
        self._timeout = timeout_seconds
        self._http = http
        self._uploader = uploader

        if self._endpoint in PROMOTIONAL_ENDPOINTS:
            print(
                f"[fal] WARNING: {self._endpoint} is on a promotional launch rate "
                "that expires 1 Sept 2026 (768P goes $0.04 -> $0.08/s, dearer "
                f"than {ENDPOINT_H3_IMAGE_TO_VIDEO} at $0.06/s). Do not build on it."
            )

    # -- public interface --------------------------------------------------

    @property
    def model_name(self) -> str:
        return f"fal ({self._endpoint})"

    @property
    def endpoint(self) -> str:
        return self._endpoint

    def generate(
        self,
        prompt: str,
        output_path: str,
        duration_seconds: int = DEFAULT_DURATION_SECONDS,
        aspect_ratio: Optional[str] = None,
        resolution: str = DEFAULT_RESOLUTION,
        image_path: Optional[str] = None,
        *,
        first_frame: Optional[str] = None,
        last_frame: Optional[str] = None,
        reference_images: Optional[Sequence[str]] = None,
        seed: Optional[int] = None,
        enable_safety_checker: bool = True,
        prompt_expansion_mode: Optional[str] = None,
        strip_audio: bool = True,
        upload_to_r2: bool = True,
        r2_path: Optional[str] = None,
        sidecar: bool = True,
        **kwargs,
    ) -> VideoResult:
        """Render one clip, fetch it off the CDN, strip audio, park it on R2.

        Args:
            prompt: Text prompt (required by the endpoint even for i2v).
            output_path: Where the .mp4 lands locally.
            duration_seconds: 5-15.  Anything under 5 is raised to 5 with a
                warning - the endpoint rejects it and it bills as 5 anyway.
            aspect_ratio: Not a parameter on H3; the output follows the input
                image.  Accepted for interface compatibility and recorded in the
                sidecar, but a value that cannot be honoured is called out.
            resolution: "480P", "768P", "2K" or "4K" (aliases: 480p/720p/768p/2k/4k).
            image_path: Alias for ``first_frame``.
            first_frame / last_frame: Local paths or public URLs.  ``last_frame``
                is the whole point of this provider.
            reference_images: For ``minimax/h3/reference-to-video``.
            seed: Fixed seed for reproducible retries.
            enable_safety_checker: Left at the endpoint default (True).  Scene 17
                rendered with it on; there is no reason to touch it.
            prompt_expansion_mode: "fast", "balanced" (default) or "quality".
            strip_audio: Run ffmpeg to drop the audio track H3 always adds.
            upload_to_r2: Push the clip to R2.  The fal CDN URL dies in ~7 days.
            r2_path: R2 key; defaults to ``video/fal/<YYYYMMDD>/<stem>.mp4``.
            sidecar: Write ``<output_path>.json`` with cost and provenance.

        Returns:
            VideoResult whose ``estimated_cost`` is the published rate for the
            BILLED duration, not the requested one.
        """
        resolution = self._normalise_resolution(resolution)
        billed_seconds = self._billable_duration(duration_seconds)

        if image_path and not first_frame:
            first_frame = image_path
        if last_frame and not first_frame:
            raise ValueError(
                "last_frame requires first_frame - H3 interpolates between the "
                "two, it cannot anchor only the end of a clip."
            )
        send_aspect_ratio = None
        if aspect_ratio:
            if self._endpoint in ENDPOINTS_WITHOUT_ASPECT_RATIO:
                print(
                    f"[fal] NOTE: aspect_ratio={aspect_ratio!r} is not a parameter "
                    f"on {self._endpoint}; the output follows the input image."
                )
            elif aspect_ratio not in SUPPORTED_ASPECT_RATIOS:
                raise ValueError(
                    f"aspect_ratio must be one of {SUPPORTED_ASPECT_RATIOS}, "
                    f"got {aspect_ratio!r}"
                )
            else:
                send_aspect_ratio = aspect_ratio

        payload: dict = {
            "prompt": prompt,
            "duration": billed_seconds,
            "resolution": resolution,
            "enable_safety_checker": enable_safety_checker,
        }
        if first_frame:
            payload["image_url"] = self._as_url(first_frame)
        if last_frame:
            payload["end_image_url"] = self._as_url(last_frame)
        if reference_images:
            payload["reference_image_urls"] = [
                self._as_url(r) for r in reference_images
            ]
        if seed is not None:
            payload["seed"] = seed
        if prompt_expansion_mode:
            payload["prompt_expansion_mode"] = prompt_expansion_mode
        if send_aspect_ratio:
            payload["aspect_ratio"] = send_aspect_ratio

        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)

        anchors = "first+last frame" if last_frame else (
            "first frame" if first_frame else "text only"
        )
        cost = self.estimate_cost(
            billed_seconds,
            resolution,
            reference_images=len(reference_images or []),
        )
        print(
            f"[fal] {self._endpoint} @ {resolution} {billed_seconds}s ({anchors}) "
            f"~${cost:.4f}"
        )

        start = time.time()
        submission = self._submit(payload)
        request_id = submission.get("request_id")
        result = self._await_result(submission)
        elapsed = time.time() - start

        video = (result or {}).get("video") or {}
        cdn_url = video.get("url")
        if not cdn_url:
            raise FalError(
                f"No video in the response for request {request_id}: "
                f"{json.dumps(result)[:800]}"
            )

        raw_bytes = self._download(cdn_url)
        written = self._write_video(raw_bytes, out, strip_audio=strip_audio)
        print(f"[fal] Saved {written} bytes to {out}")

        fetched_at = datetime.now(timezone.utc)
        r2_url = None
        if upload_to_r2:
            key = r2_path or self._default_r2_path(out, fetched_at)
            r2_url = self._upload(str(out), key)

        metadata = {
            "provider": "fal",
            "endpoint": self._endpoint,
            "request_id": request_id,
            "prompt": prompt,
            "expanded_prompt": (result or {}).get("expanded_prompt"),
            "resolution": resolution,
            "requested_duration_seconds": int(duration_seconds),
            "billed_duration_seconds": billed_seconds,
            "min_billable_seconds": MIN_BILLABLE_SECONDS,
            "usd_per_second": self._rate(resolution),
            "estimated_cost_usd": cost,
            "first_frame": first_frame,
            "last_frame": last_frame,
            "reference_images": list(reference_images or []),
            "seed": seed,
            "enable_safety_checker": enable_safety_checker,
            "prompt_expansion_mode": prompt_expansion_mode,
            "aspect_ratio": send_aspect_ratio or "follows input image",
            "requested_aspect_ratio": aspect_ratio,
            "audio_stripped": bool(strip_audio),
            "bytes": written,
            "fal_cdn_url": cdn_url,
            "fal_cdn_fetched_at": fetched_at.isoformat(),
            "fal_cdn_expires_after": (
                fetched_at + timedelta(days=CDN_URL_LIFETIME_DAYS)
            ).isoformat(),
            "r2_url": r2_url,
            "generation_time_seconds": round(elapsed, 1),
            **kwargs,
        }

        if sidecar:
            self._write_sidecar(out, metadata)

        return VideoResult(
            file_path=str(out),
            duration_seconds=billed_seconds,
            model_used=self.model_name,
            estimated_cost=cost,
            generation_time_seconds=round(elapsed, 1),
            metadata=metadata,
        )

    def image_to_video(
        self,
        prompt: str,
        output_path: str,
        first_frame: str,
        last_frame: Optional[str] = None,
        **kwargs,
    ) -> VideoResult:
        """First (and optionally last) frame conditioning - the core workflow."""
        return self.generate(
            prompt,
            output_path,
            first_frame=first_frame,
            last_frame=last_frame,
            **kwargs,
        )

    def text_to_video(self, prompt: str, output_path: str, **kwargs) -> VideoResult:
        return self.generate(prompt, output_path, **kwargs)

    def reference_to_video(
        self,
        prompt: str,
        output_path: str,
        reference_images: Sequence[str],
        **kwargs,
    ) -> VideoResult:
        return self.generate(
            prompt, output_path, reference_images=reference_images, **kwargs
        )

    def generate_batch(
        self,
        jobs: Sequence[dict],
        max_concurrency: int = DEFAULT_MAX_CONCURRENCY,
    ) -> list:
        """Render several clips, never exceeding ``max_concurrency`` in flight.

        New fal accounts are capped at 2 concurrent requests and the cap is
        enforced server-side, so a wider fan-out just collects rejections.

        Args:
            jobs: One kwargs dict per clip, as passed to :meth:`generate`.
            max_concurrency: In-flight requests.  Defaults to the account cap.

        Returns:
            A list positionally matching ``jobs``; each entry is a VideoResult
            or, if that clip failed, the Exception.  One bad shot does not throw
            away the clips that rendered.
        """
        if max_concurrency < 1:
            raise ValueError("max_concurrency must be >= 1")
        if max_concurrency > DEFAULT_MAX_CONCURRENCY:
            print(
                f"[fal] NOTE: max_concurrency={max_concurrency} exceeds the "
                f"{DEFAULT_MAX_CONCURRENCY}-request cap on new fal accounts; "
                "the extra requests will be rejected unless the cap was raised."
            )

        def _run(job: dict):
            try:
                return self.generate(**job)
            except Exception as exc:  # a failed shot is data, not a crash
                return exc

        with ThreadPoolExecutor(max_workers=max_concurrency) as pool:
            return list(pool.map(_run, jobs))

    def estimate_cost(
        self,
        duration_seconds: int = DEFAULT_DURATION_SECONDS,
        resolution: str = DEFAULT_RESOLUTION,
        **kwargs,
    ) -> float:
        """Published-rate cost for a clip, charged on the BILLED duration."""
        resolution = self._normalise_resolution(resolution)
        billed = self._billable_duration(duration_seconds, quiet=True)
        total = self._rate(resolution) * billed
        extra_refs = max(int(kwargs.get("reference_images", 0)) - FREE_REFERENCE_IMAGES, 0)
        total += extra_refs * USD_PER_EXTRA_REFERENCE_IMAGE
        return round(total, 4)

    # -- transport ---------------------------------------------------------

    @property
    def _client(self):
        if self._http is None:
            import httpx

            self._http = httpx.Client(timeout=120.0, follow_redirects=True)
        return self._http

    def _headers(self) -> dict:
        return {
            "Authorization": f"Key {self._api_key}",
            "Content-Type": "application/json",
        }

    def _submit(self, payload: dict) -> dict:
        url = f"{QUEUE_BASE}/{self._endpoint}"
        resp = self._client.post(url, json=payload, headers=self._headers())
        return self._json_or_raise(resp, f"submit {self._endpoint}")

    def _await_result(self, submission: dict) -> dict:
        """Poll the queue until COMPLETED, then fetch the response body."""
        request_id = submission.get("request_id")
        if not request_id:
            raise FalError(f"No request_id in submission: {submission}")

        base = f"{QUEUE_BASE}/{self._endpoint}/requests/{request_id}"
        status_url = submission.get("status_url") or f"{base}/status"
        response_url = submission.get("response_url") or base

        deadline = time.time() + self._timeout
        status = submission.get("status")
        while status in _STATUS_POLLING:
            if time.time() > deadline:
                raise FalError(
                    f"Timed out after {self._timeout:.0f}s waiting on request "
                    f"{request_id} (last status {status}). It may still be "
                    f"running: GET {status_url}"
                )
            time.sleep(self._poll_interval)
            body = self._json_or_raise(
                self._client.get(status_url, headers=self._headers()),
                f"status {request_id}",
            )
            status = body.get("status")

        if status != _TERMINAL_OK:
            raise FalError(f"Request {request_id} ended in status {status!r}")

        return self._json_or_raise(
            self._client.get(response_url, headers=self._headers()),
            f"result {request_id}",
        )

    def _json_or_raise(self, resp, what: str) -> dict:
        """Decode a fal response, turning an error status into a FalError.

        5xx and cold starts are not billed and fal retries server-side, so a
        surfaced error here is a real rejection worth reading - a moderation
        block, a bad parameter, or an exhausted balance.
        """
        status = getattr(resp, "status_code", None)
        try:
            body = resp.json()
        except Exception:
            body = {"raw": getattr(resp, "text", "")[:800]}
        if status is not None and status >= 400:
            raise FalError(f"fal {what} failed with HTTP {status}: {json.dumps(body)[:800]}")
        return body

    def _download(self, url: str) -> bytes:
        resp = self._client.get(url)
        status = getattr(resp, "status_code", 200)
        if status >= 400:
            raise FalError(f"Downloading the clip failed with HTTP {status}: {url}")
        return resp.content

    # -- local file handling ----------------------------------------------

    def _write_video(self, data: bytes, out: Path, *, strip_audio: bool) -> int:
        """Write the clip, dropping H3's inescapable audio track on the way in."""
        if not strip_audio:
            out.write_bytes(data)
            return len(data)

        tmp = out.with_suffix(out.suffix + ".withaudio")
        tmp.write_bytes(data)
        try:
            self._run_ffmpeg_strip(tmp, out)
        finally:
            tmp.unlink(missing_ok=True)
        return out.stat().st_size

    def _run_ffmpeg_strip(self, src: Path, dest: Path) -> None:
        """``ffmpeg -i in.mp4 -c:v copy -an out.mp4`` - remux, no re-encode."""
        proc = subprocess.run(
            [
                "ffmpeg", "-y", "-loglevel", "error",
                "-i", str(src), "-c:v", "copy", "-an", str(dest),
            ],
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0 or not dest.exists():
            raise FalError(f"ffmpeg failed to strip audio: {proc.stderr.strip()[:500]}")

    def _upload(self, local_path: str, r2_path: str) -> Optional[str]:
        """Park the clip on R2.  fal's CDN URL is gone in about a week."""
        uploader = self._uploader
        if uploader is None:
            sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
            from r2_upload import upload_file

            uploader = upload_file
        try:
            return uploader(local_path, r2_path)
        except Exception as exc:
            # The clip is on disk either way; losing the upload should not lose
            # the render, but it must be loud - the CDN copy expires.
            print(f"[fal] WARNING: R2 upload failed ({exc}). Local copy: {local_path}")
            return None

    def _write_sidecar(self, out: Path, metadata: dict) -> Path:
        path = out.with_suffix(out.suffix + ".json")
        path.write_text(json.dumps(metadata, indent=2, default=str))
        return path

    @staticmethod
    def _default_r2_path(out: Path, when: datetime) -> str:
        return f"video/fal/{when.strftime('%Y%m%d')}/{out.name}"

    def _as_url(self, path_or_url: str) -> str:
        """Public URL passthrough; a local file becomes a data URI.

        H3 takes ``image_url`` only - it has no multipart upload - so a local
        panel has to be inlined (or pushed somewhere public first).
        """
        if str(path_or_url).startswith(("http://", "https://", "data:")):
            return str(path_or_url)
        p = Path(path_or_url)
        if not p.is_file():
            raise FileNotFoundError(f"frame not found: {path_or_url}")
        mime = mimetypes.guess_type(p.name)[0] or "image/png"
        return f"data:{mime};base64,{base64.b64encode(p.read_bytes()).decode()}"

    # -- validation --------------------------------------------------------

    @staticmethod
    def _normalise_resolution(resolution: str) -> str:
        if resolution in SUPPORTED_RESOLUTIONS:
            return resolution
        key = str(resolution).strip().lower()
        if key in _RESOLUTION_ALIASES:
            return _RESOLUTION_ALIASES[key]
        raise ValueError(
            f"resolution must be one of {SUPPORTED_RESOLUTIONS} (or an alias "
            f"{sorted(_RESOLUTION_ALIASES)}), got {resolution!r}. Note 1080p is "
            "not an H3 mode: pick 768P ($0.06/s) or 2K ($0.13/s) deliberately."
        )

    @staticmethod
    def _billable_duration(duration_seconds: int, *, quiet: bool = False) -> int:
        n = int(duration_seconds)
        if n > MAX_DURATION_SECONDS:
            raise ValueError(
                f"duration_seconds must be <= {MAX_DURATION_SECONDS}, got {n}"
            )
        if n < 1:
            raise ValueError(f"duration_seconds must be positive, got {n}")
        if n < MIN_BILLABLE_SECONDS:
            if not quiet:
                print(
                    f"[fal] NOTE: {n}s was requested but H3's minimum is "
                    f"{MIN_BILLABLE_SECONDS}s and a shorter clip bills as "
                    f"{MIN_BILLABLE_SECONDS}s anyway. Rendering "
                    f"{MIN_BILLABLE_SECONDS}s and charging for "
                    f"{MIN_BILLABLE_SECONDS}s - trim it in the edit."
                )
            return MIN_BILLABLE_SECONDS
        return n

    def _rate(self, resolution: str) -> float:
        rates = USD_PER_SECOND.get(self._endpoint)
        if rates is None:
            raise ValueError(
                f"No published rate on file for endpoint {self._endpoint!r}. Add "
                "it to USD_PER_SECOND before rendering, so spend stays auditable."
            )
        if resolution not in rates:
            raise ValueError(
                f"{self._endpoint} has no published rate for {resolution}; "
                f"known: {sorted(rates)}"
            )
        return rates[resolution]
