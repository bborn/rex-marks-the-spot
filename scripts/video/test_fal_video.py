#!/usr/bin/env python3
"""Tests for the fal.ai (MiniMax H3) wrapper.

Offline: the httpx transport, ffmpeg and the R2 uploader are all injected, so
the suite locks in the request shape and the money-adjacent rules without
spending a cent.

Run:  cd scripts && python -m pytest video/test_fal_video.py -v
"""

import base64
import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

os.environ.setdefault("FAL_KEY", "test-key")

from video.base import (  # noqa: E402
    FIRST_LAST_FRAME,
    create_generator,
)
from video.fal_video import (  # noqa: E402
    CDN_URL_LIFETIME_DAYS,
    DEFAULT_MAX_CONCURRENCY,
    DEFAULT_RESOLUTION,
    ENDPOINT_H3_IMAGE_TO_VIDEO,
    ENDPOINT_H3_REFERENCE_TO_VIDEO,
    ENDPOINT_H3_TEXT_TO_VIDEO,
    MAX_DURATION_SECONDS,
    MIN_BILLABLE_SECONDS,
    QUEUE_BASE,
    USD_PER_SECOND,
    FalError,
    FalVideoGenerator,
)


FAKE_MP4 = b"\x00\x00\x00\x18ftypmp42" + b"v" * 4096
CDN_URL = "https://v3.fal.media/files/fake/clip.mp4"


class FakeResponse:
    def __init__(self, payload=None, *, status_code=200, content=b""):
        self.status_code = status_code
        self._payload = payload
        self.content = content
        self.text = json.dumps(payload) if payload is not None else ""

    def json(self):
        if self._payload is None:
            raise ValueError("no json")
        return self._payload


class FakeTransport:
    """Stands in for httpx.Client: one POST to submit, GETs to poll and fetch.

    ``statuses`` is the sequence of queue states the poller will see.
    """

    def __init__(self, statuses=("COMPLETED",), result=None, submit_status="IN_QUEUE"):
        self.statuses = list(statuses)
        self.submit_status = submit_status
        self.result = result if result is not None else {
            "video": {
                "url": CDN_URL,
                "content_type": "video/mp4",
                "file_name": "clip.mp4",
                "file_size": len(FAKE_MP4),
            },
            "expanded_prompt": "an expanded prompt",
        }
        self.posts = []
        self.gets = []

    def post(self, url, json=None, headers=None):
        self.posts.append({"url": url, "json": json, "headers": headers})
        return FakeResponse({
            "status": self.submit_status,
            "request_id": "req-123",
            "status_url": f"{url}/requests/req-123/status",
            "response_url": f"{url}/requests/req-123",
        })

    def get(self, url, headers=None):
        self.gets.append({"url": url, "headers": headers})
        if url == CDN_URL:
            return FakeResponse(content=FAKE_MP4)
        if url.endswith("/status"):
            status = self.statuses.pop(0) if self.statuses else "COMPLETED"
            return FakeResponse({"status": status, "request_id": "req-123"})
        return FakeResponse(self.result)


@pytest.fixture
def transport():
    return FakeTransport()


@pytest.fixture
def gen(transport):
    g = FalVideoGenerator(
        api_key="test-key",
        http=transport,
        poll_interval_seconds=0,
        uploader=lambda local, key: f"https://r2.example/{key}",
    )
    # Audio stripping shells out to ffmpeg; exercise it explicitly instead.
    g._run_ffmpeg_strip = lambda src, dest: dest.write_bytes(src.read_bytes())
    return g


@pytest.fixture
def png(tmp_path):
    p = tmp_path / "panel-1A.png"
    p.write_bytes(b"\x89PNG\r\n\x1a\n" + b"z" * 256)
    return str(p)


def _payload(gen):
    return gen._http.posts[-1]["json"]


# ---------------------------------------------------------------------------
# Request shape - read off the live endpoint schema
# ---------------------------------------------------------------------------


class TestRequestShape:
    def test_posts_to_the_queue_endpoint(self, gen, tmp_path):
        gen.text_to_video("a room", str(tmp_path / "o.mp4"))
        assert gen._http.posts[0]["url"] == f"{QUEUE_BASE}/{ENDPOINT_H3_IMAGE_TO_VIDEO}"

    def test_duration_is_an_integer_not_a_string(self, gen, tmp_path):
        gen.text_to_video("a room", str(tmp_path / "o.mp4"), duration_seconds=8)
        assert _payload(gen)["duration"] == 8

    def test_resolution_is_always_sent_explicitly(self, gen, tmp_path):
        """The API default is 2K at $0.13/s - more than double 768P."""
        gen.text_to_video("a room", str(tmp_path / "o.mp4"))
        assert _payload(gen)["resolution"] == DEFAULT_RESOLUTION == "768P"

    def test_first_and_last_frame_map_to_image_and_end_image_url(
        self, gen, tmp_path, png
    ):
        gen.image_to_video("1A to 1B", str(tmp_path / "o.mp4"), png, last_frame=png)
        body = _payload(gen)
        assert body["image_url"].startswith("data:image/png;base64,")
        assert body["end_image_url"].startswith("data:image/png;base64,")

    def test_public_urls_pass_through_untouched(self, gen, tmp_path):
        url = "https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/a/1A.png"
        gen.image_to_video("x", str(tmp_path / "o.mp4"), url)
        assert _payload(gen)["image_url"] == url

    def test_local_frame_is_base64_encoded(self, gen, tmp_path, png):
        gen.image_to_video("x", str(tmp_path / "o.mp4"), png)
        head, b64 = _payload(gen)["image_url"].split(",", 1)
        assert head == "data:image/png;base64"
        assert base64.b64decode(b64) == Path(png).read_bytes()

    def test_safety_checker_left_on_by_default(self, gen, tmp_path):
        """Scene 17 rendered with the checker on; there is no reason to touch it."""
        gen.text_to_video("x", str(tmp_path / "o.mp4"))
        assert _payload(gen)["enable_safety_checker"] is True

    def test_optional_params_omitted_when_unset(self, gen, tmp_path):
        gen.text_to_video("x", str(tmp_path / "o.mp4"))
        body = _payload(gen)
        for key in ("seed", "prompt_expansion_mode", "image_url",
                    "end_image_url", "aspect_ratio"):
            assert key not in body

    def test_seed_and_expansion_mode_passed_through(self, gen, tmp_path):
        gen.text_to_video(
            "x", str(tmp_path / "o.mp4"), seed=7, prompt_expansion_mode="quality"
        )
        body = _payload(gen)
        assert body["seed"] == 7
        assert body["prompt_expansion_mode"] == "quality"

    def test_reference_images_use_reference_image_urls(self, tmp_path, png, transport):
        g = FalVideoGenerator(
            endpoint=ENDPOINT_H3_REFERENCE_TO_VIDEO, api_key="k", http=transport,
            poll_interval_seconds=0, uploader=lambda a, b: "u",
        )
        g._run_ffmpeg_strip = lambda src, dest: dest.write_bytes(src.read_bytes())
        g.reference_to_video("two kids", str(tmp_path / "o.mp4"), [png, png])
        assert len(transport.posts[-1]["json"]["reference_image_urls"]) == 2

    def test_api_key_is_sent_as_a_key_header_and_never_in_the_payload(
        self, gen, tmp_path
    ):
        gen.text_to_video("x", str(tmp_path / "o.mp4"))
        post = gen._http.posts[-1]
        assert post["headers"]["Authorization"] == "Key test-key"
        assert "test-key" not in json.dumps(post["json"])


class TestAspectRatio:
    def test_image_to_video_ignores_aspect_ratio(self, gen, tmp_path, png):
        """Not a parameter on i2v - the output follows the input image."""
        gen.image_to_video("x", str(tmp_path / "o.mp4"), png, aspect_ratio="9:16")
        assert "aspect_ratio" not in _payload(gen)

    def test_text_to_video_sends_aspect_ratio(self, tmp_path, transport):
        g = FalVideoGenerator(
            endpoint=ENDPOINT_H3_TEXT_TO_VIDEO, api_key="k", http=transport,
            poll_interval_seconds=0, uploader=lambda a, b: "u",
        )
        g._run_ffmpeg_strip = lambda src, dest: dest.write_bytes(src.read_bytes())
        g.text_to_video("x", str(tmp_path / "o.mp4"), aspect_ratio="9:16")
        assert transport.posts[-1]["json"]["aspect_ratio"] == "9:16"

    def test_unknown_aspect_ratio_rejected(self, tmp_path, transport):
        g = FalVideoGenerator(
            endpoint=ENDPOINT_H3_TEXT_TO_VIDEO, api_key="k", http=transport,
            poll_interval_seconds=0,
        )
        with pytest.raises(ValueError, match="aspect_ratio"):
            g.text_to_video("x", str(tmp_path / "o.mp4"), aspect_ratio="5:4")
        assert transport.posts == []


# ---------------------------------------------------------------------------
# The 5-second minimum: say so, do not silently overcharge
# ---------------------------------------------------------------------------


class TestBillableDuration:
    def test_short_request_is_raised_to_the_five_second_minimum(self, gen, tmp_path):
        res = gen.text_to_video("x", str(tmp_path / "o.mp4"), duration_seconds=3)
        assert _payload(gen)["duration"] == MIN_BILLABLE_SECONDS
        assert res.duration_seconds == MIN_BILLABLE_SECONDS

    def test_short_request_says_so_out_loud(self, gen, tmp_path, capsys):
        gen.text_to_video("x", str(tmp_path / "o.mp4"), duration_seconds=3)
        out = capsys.readouterr().out
        assert "minimum" in out and "bills as" in out

    def test_sidecar_records_requested_and_billed_duration(self, gen, tmp_path):
        res = gen.text_to_video("x", str(tmp_path / "o.mp4"), duration_seconds=3)
        assert res.metadata["requested_duration_seconds"] == 3
        assert res.metadata["billed_duration_seconds"] == 5

    def test_three_second_clip_costs_the_same_as_five(self, gen):
        assert gen.estimate_cost(3, "768P") == gen.estimate_cost(5, "768P")

    def test_duration_over_the_maximum_rejected(self, gen, tmp_path):
        with pytest.raises(ValueError, match="duration_seconds"):
            gen.text_to_video("x", str(tmp_path / "o.mp4"), duration_seconds=16)
        assert gen._http.posts == []

    @pytest.mark.parametrize("n", [MIN_BILLABLE_SECONDS, 10, MAX_DURATION_SECONDS])
    def test_durations_in_range_pass_through(self, gen, tmp_path, n):
        gen.text_to_video("x", str(tmp_path / "o.mp4"), duration_seconds=n)
        assert _payload(gen)["duration"] == n


class TestResolution:
    @pytest.mark.parametrize(
        "given,sent",
        [("480P", "480P"), ("480p", "480P"), ("768p", "768P"),
         ("720p", "768P"), ("2k", "2K"), ("4K", "4K")],
    )
    def test_aliases_normalise_onto_the_enum(self, gen, tmp_path, given, sent):
        gen.text_to_video("x", str(tmp_path / "o.mp4"), resolution=given)
        assert _payload(gen)["resolution"] == sent

    def test_1080p_is_rejected_rather_than_guessed_upward(self, gen, tmp_path):
        """Guessing 1080p -> 2K would silently double the rate."""
        with pytest.raises(ValueError, match="1080p"):
            gen.text_to_video("x", str(tmp_path / "o.mp4"), resolution="1080p")
        assert gen._http.posts == []

    def test_unknown_resolution_rejected(self, gen, tmp_path):
        with pytest.raises(ValueError, match="resolution"):
            gen.text_to_video("x", str(tmp_path / "o.mp4"), resolution="8K")


# ---------------------------------------------------------------------------
# Cost, from published rates
# ---------------------------------------------------------------------------


class TestCost:
    def test_768p_is_six_cents_a_second(self, gen):
        assert gen.estimate_cost(5, "768P") == pytest.approx(0.30)

    def test_480p_is_five_cents_a_second(self, gen):
        assert gen.estimate_cost(5, "480P") == pytest.approx(0.25)

    def test_2k_is_more_than_double_768p(self, gen):
        assert gen.estimate_cost(5, "2K") > 2 * gen.estimate_cost(5, "768P")

    def test_result_cost_is_charged_on_billed_seconds(self, gen, tmp_path):
        res = gen.text_to_video(
            "x", str(tmp_path / "o.mp4"), duration_seconds=3, resolution="480P"
        )
        assert res.estimated_cost == pytest.approx(0.25)

    def test_extra_reference_images_cost_eight_cents_each(self, transport):
        g = FalVideoGenerator(
            endpoint=ENDPOINT_H3_REFERENCE_TO_VIDEO, api_key="k", http=transport,
        )
        base = g.estimate_cost(5, "768P", reference_images=5)
        assert g.estimate_cost(5, "768P", reference_images=7) == pytest.approx(
            base + 0.16
        )

    def test_h3_max_priced_at_its_post_promo_rate(self):
        """The $0.04 launch rate expires 1 Sept 2026 and becomes $0.08."""
        assert USD_PER_SECOND["minimax/h3-max/image-to-video"]["768P"] == 0.08

    def test_endpoint_without_a_published_rate_refuses_to_render(self, transport):
        g = FalVideoGenerator(endpoint="some/new/endpoint", api_key="k", http=transport)
        with pytest.raises(ValueError, match="No published rate"):
            g.estimate_cost(5, "768P")

    def test_h3_max_warns_that_it_is_promotional(self, transport, capsys):
        FalVideoGenerator(
            endpoint="minimax/h3-max/image-to-video", api_key="k", http=transport
        )
        assert "promotional" in capsys.readouterr().out.lower()


# ---------------------------------------------------------------------------
# Queue polling
# ---------------------------------------------------------------------------


class TestQueue:
    def test_polls_until_completed(self, tmp_path):
        t = FakeTransport(statuses=["IN_QUEUE", "IN_PROGRESS", "COMPLETED"])
        g = FalVideoGenerator(api_key="k", http=t, poll_interval_seconds=0,
                              uploader=lambda a, b: "u")
        g._run_ffmpeg_strip = lambda src, dest: dest.write_bytes(src.read_bytes())
        g.text_to_video("x", str(tmp_path / "o.mp4"))
        assert len([g for g in t.gets if g["url"].endswith("/status")]) == 3

    def test_no_polling_when_submission_is_already_complete(self, tmp_path):
        t = FakeTransport(submit_status="COMPLETED")
        g = FalVideoGenerator(api_key="k", http=t, poll_interval_seconds=0,
                              uploader=lambda a, b: "u")
        g._run_ffmpeg_strip = lambda src, dest: dest.write_bytes(src.read_bytes())
        g.text_to_video("x", str(tmp_path / "o.mp4"))
        assert [x for x in t.gets if x["url"].endswith("/status")] == []

    def test_error_status_raises(self, tmp_path):
        t = FakeTransport(statuses=["IN_PROGRESS", "ERROR"])
        g = FalVideoGenerator(api_key="k", http=t, poll_interval_seconds=0)
        with pytest.raises(FalError, match="ERROR"):
            g.text_to_video("x", str(tmp_path / "o.mp4"))

    def test_http_error_on_submit_raises_with_the_body(self, tmp_path):
        t = FakeTransport()
        t.post = lambda url, json=None, headers=None: FakeResponse(
            {"detail": "Unprocessable"}, status_code=422
        )
        g = FalVideoGenerator(api_key="k", http=t, poll_interval_seconds=0)
        with pytest.raises(FalError, match="422"):
            g.text_to_video("x", str(tmp_path / "o.mp4"))

    def test_missing_video_in_result_raises(self, tmp_path):
        t = FakeTransport(result={"expanded_prompt": "x"})
        g = FalVideoGenerator(api_key="k", http=t, poll_interval_seconds=0)
        with pytest.raises(FalError, match="No video"):
            g.text_to_video("x", str(tmp_path / "o.mp4"))

    def test_timeout_names_the_status_url(self, tmp_path):
        t = FakeTransport(statuses=["IN_QUEUE"] * 50)
        g = FalVideoGenerator(
            api_key="k", http=t, poll_interval_seconds=0, timeout_seconds=-1
        )
        with pytest.raises(FalError, match="Timed out"):
            g.text_to_video("x", str(tmp_path / "o.mp4"))


# ---------------------------------------------------------------------------
# Ingest: download, strip audio, park on R2
# ---------------------------------------------------------------------------


class TestIngest:
    def test_downloads_the_clip_off_the_cdn(self, gen, tmp_path):
        out = tmp_path / "sub" / "o.mp4"
        res = gen.text_to_video("x", str(out))
        assert out.read_bytes() == FAKE_MP4
        assert res.metadata["bytes"] == len(FAKE_MP4)

    def test_audio_is_stripped_with_a_stream_copy(self, tmp_path, transport):
        g = FalVideoGenerator(api_key="k", http=transport, poll_interval_seconds=0,
                              uploader=lambda a, b: "u")
        with patch("subprocess.run") as run:
            run.return_value = MagicMock(returncode=0, stderr="")
            (tmp_path / "o.mp4").write_bytes(FAKE_MP4)  # stand in for ffmpeg's output
            g.text_to_video("x", str(tmp_path / "o.mp4"))
        cmd = run.call_args.args[0]
        assert cmd[0] == "ffmpeg"
        assert "-an" in cmd and "copy" in cmd

    def test_ffmpeg_failure_raises(self, tmp_path, transport):
        g = FalVideoGenerator(api_key="k", http=transport, poll_interval_seconds=0)
        with patch("subprocess.run") as run:
            run.return_value = MagicMock(returncode=1, stderr="boom")
            with pytest.raises(FalError, match="ffmpeg"):
                g.text_to_video("x", str(tmp_path / "o.mp4"))

    def test_strip_audio_can_be_turned_off(self, tmp_path, transport):
        g = FalVideoGenerator(api_key="k", http=transport, poll_interval_seconds=0,
                              uploader=lambda a, b: "u")
        with patch("subprocess.run") as run:
            res = g.text_to_video("x", str(tmp_path / "o.mp4"), strip_audio=False)
        run.assert_not_called()
        assert res.metadata["audio_stripped"] is False

    def test_temp_file_is_cleaned_up(self, gen, tmp_path):
        out = tmp_path / "o.mp4"
        gen.text_to_video("x", str(out))
        assert list(tmp_path.glob("*.withaudio")) == []

    def test_clip_is_uploaded_to_r2(self, gen, tmp_path):
        res = gen.text_to_video("x", str(tmp_path / "o.mp4"))
        assert res.metadata["r2_url"].startswith("https://r2.example/video/fal/")

    def test_explicit_r2_path_is_honoured(self, gen, tmp_path):
        res = gen.text_to_video(
            "x", str(tmp_path / "o.mp4"), r2_path="video/scene-01/shot-1A.mp4"
        )
        assert res.metadata["r2_url"].endswith("video/scene-01/shot-1A.mp4")

    def test_failed_upload_keeps_the_render(self, tmp_path, transport, capsys):
        def boom(local, key):
            raise RuntimeError("rclone exploded")

        g = FalVideoGenerator(api_key="k", http=transport, poll_interval_seconds=0,
                              uploader=boom)
        g._run_ffmpeg_strip = lambda src, dest: dest.write_bytes(src.read_bytes())
        res = g.text_to_video("x", str(tmp_path / "o.mp4"))
        assert res.metadata["r2_url"] is None
        assert Path(res.file_path).exists()
        assert "WARNING" in capsys.readouterr().out

    def test_cdn_expiry_is_recorded_not_just_the_url(self, gen, tmp_path):
        """A CDN URL we cannot date is a clip we cannot tell is gone."""
        res = gen.text_to_video("x", str(tmp_path / "o.mp4"))
        assert res.metadata["fal_cdn_url"] == CDN_URL
        assert res.metadata["fal_cdn_expires_after"] > res.metadata["fal_cdn_fetched_at"]
        assert CDN_URL_LIFETIME_DAYS == 7


class TestSidecar:
    def test_sidecar_is_written_next_to_the_clip(self, gen, tmp_path):
        gen.image_to_video(
            "1A to 1B", str(tmp_path / "o.mp4"), "https://x/1A.png",
            last_frame="https://x/1B.png", duration_seconds=5, resolution="480P",
        )
        data = json.loads((tmp_path / "o.mp4.json").read_text())
        assert data["endpoint"] == ENDPOINT_H3_IMAGE_TO_VIDEO
        assert data["request_id"] == "req-123"
        assert data["usd_per_second"] == 0.05
        assert data["estimated_cost_usd"] == pytest.approx(0.25)
        assert data["last_frame"] == "https://x/1B.png"

    def test_sidecar_never_contains_the_api_key(self, gen, tmp_path):
        gen.text_to_video("x", str(tmp_path / "o.mp4"))
        assert "test-key" not in (tmp_path / "o.mp4.json").read_text()

    def test_sidecar_can_be_turned_off(self, gen, tmp_path):
        gen.text_to_video("x", str(tmp_path / "o.mp4"), sidecar=False)
        assert not (tmp_path / "o.mp4.json").exists()


# ---------------------------------------------------------------------------
# Batching against the 2-concurrent-request account cap
# ---------------------------------------------------------------------------


class TestBatch:
    def test_default_concurrency_matches_the_account_cap(self):
        assert DEFAULT_MAX_CONCURRENCY == 2

    def test_never_exceeds_the_concurrency_limit(self, gen, tmp_path):
        import threading

        live = 0
        peak = 0
        lock = threading.Lock()
        real = gen.generate

        def counting(**kw):
            nonlocal live, peak
            with lock:
                live += 1
                peak = max(peak, live)
            try:
                return real(**kw)
            finally:
                with lock:
                    live -= 1

        gen.generate = counting
        jobs = [
            {"prompt": f"shot {i}", "output_path": str(tmp_path / f"{i}.mp4")}
            for i in range(6)
        ]
        results = gen.generate_batch(jobs)
        assert len(results) == 6
        assert peak <= DEFAULT_MAX_CONCURRENCY

    def test_a_failing_shot_does_not_lose_the_others(self, gen, tmp_path):
        real = gen.generate

        def flaky(**kw):
            if kw["prompt"] == "bad":
                raise FalError("moderation block")
            return real(**kw)

        gen.generate = flaky
        results = gen.generate_batch([
            {"prompt": "good", "output_path": str(tmp_path / "a.mp4")},
            {"prompt": "bad", "output_path": str(tmp_path / "b.mp4")},
        ])
        assert results[0].file_path.endswith("a.mp4")
        assert isinstance(results[1], FalError)

    def test_zero_concurrency_rejected(self, gen):
        with pytest.raises(ValueError, match="max_concurrency"):
            gen.generate_batch([], max_concurrency=0)

    def test_raising_the_limit_warns_about_the_cap(self, gen, capsys):
        gen.generate_batch([], max_concurrency=8)
        assert "cap on new fal accounts" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# The shared interface
# ---------------------------------------------------------------------------


class TestSharedInterface:
    def test_factory_knows_fal(self):
        g = create_generator("fal-h3", api_key="k")
        assert isinstance(g, FalVideoGenerator)
        assert g.endpoint == ENDPOINT_H3_IMAGE_TO_VIDEO

    def test_factory_knows_the_other_h3_endpoints(self):
        assert create_generator("fal-h3-t2v", api_key="k").endpoint == (
            ENDPOINT_H3_TEXT_TO_VIDEO
        )
        assert create_generator("fal-h3-ref", api_key="k").endpoint == (
            ENDPOINT_H3_REFERENCE_TO_VIDEO
        )

    def test_declares_first_last_frame_support(self, gen):
        assert gen.supports(FIRST_LAST_FRAME)

    def test_a_backend_without_last_frame_support_raises_rather_than_dropping_it(
        self, tmp_path
    ):
        """A silently dropped anchor looks fine until the continuity gate fails."""
        from video.pvideo_generator import PVideoGenerator

        with patch("replicate.Client"):
            p = PVideoGenerator(api_token="t")
        assert not p.supports(FIRST_LAST_FRAME)
        with pytest.raises(NotImplementedError, match="last-frame"):
            p.image_to_video("x", str(tmp_path / "o.mp4"), "a.png", last_frame="b.png")

    def test_missing_key_is_an_environment_error(self, monkeypatch):
        monkeypatch.delenv("FAL_KEY", raising=False)
        with pytest.raises(EnvironmentError, match="FAL_KEY"):
            FalVideoGenerator()

    def test_missing_frame_file_raises(self, gen, tmp_path):
        with pytest.raises(FileNotFoundError):
            gen.image_to_video("x", str(tmp_path / "o.mp4"), "/nope/1A.png")

    def test_last_frame_without_a_first_frame_is_rejected(self, gen, tmp_path):
        with pytest.raises(ValueError, match="last_frame requires first_frame"):
            gen.generate("x", str(tmp_path / "o.mp4"), last_frame="https://x/1B.png")
