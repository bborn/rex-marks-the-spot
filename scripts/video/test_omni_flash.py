#!/usr/bin/env python3
"""Tests for the Gemini Omni Flash wrapper.

These are offline - the Interactions client is mocked - so they lock in the
request shape that Phase 0 established against the live API without spending
money to re-verify it.

Run:  cd scripts && python -m pytest video/test_omni_flash.py -v
"""

import base64
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

os.environ.setdefault("GEMINI_API_KEY", "test-key")

from video.base import create_generator  # noqa: E402
from video.omni_flash import (  # noqa: E402
    MAX_DURATION_SECONDS,
    MIN_DURATION_SECONDS,
    TASKS,
    OmniFlashGenerator,
    cost_from_usage,
)


FAKE_MP4 = b"\x00\x00\x00\x18ftypmp42" + b"x" * 4096


def _fake_interaction(video_bytes=FAKE_MP4, usage=None):
    """Mimic the SDK 2.x Interaction: flattened output_video + usage."""
    it = MagicMock()
    it.output_video.data = base64.b64encode(video_bytes).decode()
    it.usage = usage or {
        "output_tokens_by_modality": [{"modality": "video", "tokens": 9655}],
        "total_output_tokens": 10331,
        "total_input_tokens": 1161,
    }
    it.id = "v1_fake"
    return it


@pytest.fixture
def gen():
    with patch("google.genai.Client"):
        g = OmniFlashGenerator()
    g._client = MagicMock()
    g._client.interactions.create.return_value = _fake_interaction()
    return g


@pytest.fixture
def png(tmp_path):
    p = tmp_path / "ref.png"
    p.write_bytes(b"\x89PNG\r\n\x1a\n" + b"z" * 512)
    return str(p)


# ---------------------------------------------------------------------------
# Request shape - the part that cost real money to establish
# ---------------------------------------------------------------------------


class TestRequestShape:
    def test_duration_is_a_string_on_response_format(self, gen, tmp_path):
        gen.text_to_video("a room", str(tmp_path / "o.mp4"), duration_seconds=5)
        kw = gen._client.interactions.create.call_args.kwargs
        assert kw["response_format"]["duration"] == "5s"

    def test_video_config_carries_only_task(self, gen, tmp_path):
        """Unknown video_config keys are silently ignored by the API and bill
        for a full-length clip, so the wrapper must never invent any."""
        gen.text_to_video("a room", str(tmp_path / "o.mp4"), duration_seconds=4)
        kw = gen._client.interactions.create.call_args.kwargs
        assert kw["generation_config"] == {"video_config": {"task": "text_to_video"}}

    def test_response_format_fields(self, gen, tmp_path):
        gen.text_to_video(
            "a room", str(tmp_path / "o.mp4"),
            duration_seconds=3, aspect_ratio="9:16", resolution="720p",
        )
        rf = gen._client.interactions.create.call_args.kwargs["response_format"]
        assert rf == {
            "type": "video",
            "aspect_ratio": "9:16",
            "resolution": "720p",
            "duration": "3s",
        }

    def test_omits_nothing_when_duration_defaults(self, gen, tmp_path):
        gen.text_to_video("a room", str(tmp_path / "o.mp4"))
        rf = gen._client.interactions.create.call_args.kwargs["response_format"]
        assert rf["duration"] == "10s"


class TestValidation:
    @pytest.mark.parametrize("bad", [0, 2, 11, 999])
    def test_duration_out_of_range_rejected_locally(self, gen, tmp_path, bad):
        with pytest.raises(ValueError, match="duration_seconds"):
            gen.text_to_video("x", str(tmp_path / "o.mp4"), duration_seconds=bad)
        gen._client.interactions.create.assert_not_called()

    @pytest.mark.parametrize("n", [MIN_DURATION_SECONDS, 7, MAX_DURATION_SECONDS])
    def test_duration_in_range_accepted(self, gen, tmp_path, n):
        gen.text_to_video("x", str(tmp_path / "o.mp4"), duration_seconds=n)

    def test_bad_task_rejected(self, gen, tmp_path):
        with pytest.raises(ValueError, match="task must be one of"):
            gen.generate("x", str(tmp_path / "o.mp4"), task="dance")

    def test_bad_resolution_rejected(self, gen, tmp_path):
        with pytest.raises(ValueError, match="resolution"):
            gen.generate("x", str(tmp_path / "o.mp4"), resolution="480p")

    def test_bad_aspect_ratio_rejected(self, gen, tmp_path):
        with pytest.raises(ValueError, match="aspect_ratio"):
            gen.generate("x", str(tmp_path / "o.mp4"), aspect_ratio="4:3")

    def test_missing_media_file_raises(self, gen, tmp_path):
        with pytest.raises(FileNotFoundError):
            gen.image_to_video("x", str(tmp_path / "o.mp4"), first_frame="/nope.png")


# ---------------------------------------------------------------------------
# Media binding is by TAG, not position - an untagged prompt drops its images
# ---------------------------------------------------------------------------


class TestMediaTagging:
    def test_first_frame_tag_auto_prepended(self, gen, tmp_path, png):
        gen.image_to_video("slow push in", str(tmp_path / "o.mp4"), first_frame=png)
        payload = gen._client.interactions.create.call_args.kwargs["input"]
        assert payload[0]["type"] == "image"
        assert payload[-1]["text"].startswith("<FIRST_FRAME> ")

    def test_existing_tag_not_duplicated(self, gen, tmp_path, png):
        gen.image_to_video("<FIRST_FRAME> hold it", str(tmp_path / "o.mp4"), first_frame=png)
        text = gen._client.interactions.create.call_args.kwargs["input"][-1]["text"]
        assert text.count("<FIRST_FRAME>") == 1

    def test_reference_images_numbered_from_zero(self, gen, tmp_path, png):
        gen.reference_to_video(
            "two characters", str(tmp_path / "o.mp4"), reference_images=[png, png, png]
        )
        payload = gen._client.interactions.create.call_args.kwargs["input"]
        text = payload[-1]["text"]
        assert len([p for p in payload if p["type"] == "image"]) == 3
        for i in range(3):
            assert f"<IMAGE_REF_{i}>" in text

    def test_image_is_base64_encoded(self, gen, tmp_path, png):
        gen.image_to_video("x", str(tmp_path / "o.mp4"), first_frame=png)
        part = gen._client.interactions.create.call_args.kwargs["input"][0]
        assert part["mime_type"] == "image/png"
        assert base64.b64decode(part["data"]) == Path(png).read_bytes()

    def test_image_path_aliases_first_frame(self, gen, tmp_path, png):
        gen.generate("x", str(tmp_path / "o.mp4"), image_path=png, task="image_to_video")
        text = gen._client.interactions.create.call_args.kwargs["input"][-1]["text"]
        assert "<FIRST_FRAME>" in text


class TestOutput:
    def test_writes_video_bytes(self, gen, tmp_path):
        out = tmp_path / "sub" / "o.mp4"
        res = gen.text_to_video("x", str(out), duration_seconds=5)
        assert out.read_bytes() == FAKE_MP4
        assert res.metadata["bytes"] == len(FAKE_MP4)

    def test_reports_billed_cost_from_usage(self, gen, tmp_path):
        res = gen.text_to_video("x", str(tmp_path / "o.mp4"), duration_seconds=5)
        # 9655 video + 676 other @ $17.50/1M + 1161 input @ $1.50/1M
        assert res.estimated_cost == pytest.approx(0.18249, abs=1e-4)

    def test_raises_when_no_video_in_response(self, gen, tmp_path):
        empty = MagicMock()
        empty.output_video = None
        empty.usage = {}
        empty.model_dump.return_value = {"steps": []}
        gen._client.interactions.create.return_value = empty
        with pytest.raises(RuntimeError, match="No video payload"):
            gen.text_to_video("x", str(tmp_path / "o.mp4"))


class TestCost:
    def test_cost_from_usage_splits_modalities(self):
        usage = {
            "output_tokens_by_modality": [{"modality": "video", "tokens": 19310}],
            "total_output_tokens": 20115,
            "total_input_tokens": 50,
        }
        assert cost_from_usage(usage) == pytest.approx(0.35209, abs=1e-4)

    def test_empty_usage_is_free(self):
        assert cost_from_usage({}) == 0.0

    def test_estimate_scales_with_duration(self, gen):
        assert gen.estimate_cost(10, "360p") == pytest.approx(
            2 * gen.estimate_cost(5, "360p"), abs=1e-3  # estimate_cost rounds to 4dp
        )

    def test_360p_estimate_matches_measured_rate(self, gen):
        # 1,931 video tokens/s at 360p x $17.50/1M ~= $0.0338/s
        assert gen.estimate_cost(10, "360p") == pytest.approx(0.338, abs=0.005)


class TestRegistry:
    def test_factory_knows_omni(self):
        with patch("google.genai.Client"):
            g = create_generator("omni-flash")
        assert isinstance(g, OmniFlashGenerator)
        assert "gemini-omni-1.1-flash" in g.model_name

    def test_factory_knows_preview_variant(self):
        with patch("google.genai.Client"):
            g = create_generator("omni-flash-preview")
        assert "gemini-omni-flash-preview" in g.model_name

    def test_all_five_task_modes_exposed(self, gen):
        for t in TASKS:
            assert callable(getattr(gen, t))
