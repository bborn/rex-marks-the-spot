#!/usr/bin/env python3
"""Tests for the video generation abstraction layer.

Run:  cd scripts && python -m pytest video/test_video_generators.py -v
"""

import os
import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Ensure fake keys so constructors don't fail
os.environ.setdefault("GEMINI_API_KEY", "test-key")
os.environ.setdefault("REPLICATE_API_TOKEN", "test-token")

from video.base import VideoGenerator, VideoResult, create_generator, _REGISTRY, _ensure_registry
from video.veo_generator import VeoGenerator
from video.pvideo_generator import PVideoGenerator


# ---------------------------------------------------------------------------
# VideoResult dataclass
# ---------------------------------------------------------------------------

class TestVideoResult:
    def test_basic_fields(self):
        r = VideoResult(
            file_path="out.mp4",
            duration_seconds=5,
            model_used="test",
            estimated_cost=0.10,
            generation_time_seconds=30.0,
        )
        assert r.file_path == "out.mp4"
        assert r.duration_seconds == 5
        assert r.metadata == {}

    def test_metadata_default(self):
        r = VideoResult("a.mp4", 1, "m", 0, 0)
        assert isinstance(r.metadata, dict)

    def test_metadata_populated(self):
        r = VideoResult("a.mp4", 1, "m", 0, 0, metadata={"key": "val"})
        assert r.metadata["key"] == "val"


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

class TestFactory:
    def test_known_models(self):
        _ensure_registry()
        for name in ["veo-2", "veo-3", "veo-3.1", "p-video", "p-video-draft"]:
            assert name in _REGISTRY

    def test_create_veo(self):
        gen = create_generator("veo-3.1", api_key="fake")
        assert isinstance(gen, VeoGenerator)

    def test_create_pvideo(self):
        gen = create_generator("p-video", api_token="fake")
        assert isinstance(gen, PVideoGenerator)

    def test_create_pvideo_draft(self):
        gen = create_generator("p-video-draft", api_token="fake")
        assert isinstance(gen, PVideoGenerator)

    def test_unknown_model_raises(self):
        with pytest.raises(ValueError, match="Unknown model"):
            create_generator("nonexistent")

    def test_case_insensitive(self):
        gen = create_generator("VEO-3.1", api_key="fake")
        assert isinstance(gen, VeoGenerator)


# ---------------------------------------------------------------------------
# VeoGenerator
# ---------------------------------------------------------------------------

class TestVeoGenerator:
    def test_model_name(self):
        gen = VeoGenerator(api_key="fake")
        assert "veo" in gen.model_name.lower()

    def test_cost_720p(self):
        gen = VeoGenerator(model_variant="veo-3.1-generate-preview", api_key="fake")
        cost = gen.estimate_cost(8, "720p")
        assert cost == 0.28

    def test_cost_1080p(self):
        gen = VeoGenerator(model_variant="veo-3.1-generate-preview", api_key="fake")
        cost = gen.estimate_cost(8, "1080p")
        assert cost == 0.56

    def test_cost_veo2(self):
        gen = VeoGenerator(model_variant="veo-2", api_key="fake")
        assert gen.estimate_cost(8, "720p") == 0.16

    def test_missing_api_key(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("GEMINI_API_KEY", None)
            with pytest.raises(EnvironmentError, match="GEMINI_API_KEY"):
                VeoGenerator(api_key=None)
            os.environ["GEMINI_API_KEY"] = "test-key"

    @patch("video.veo_generator.genai", create=True)
    def test_generate_calls_api(self, _mock_genai):
        """Test that generate() invokes the Veo API and saves output."""
        gen = VeoGenerator(api_key="fake")

        # Mock the client pipeline
        mock_video_file = MagicMock()
        mock_video_file.save = MagicMock()

        mock_generated = MagicMock()
        mock_generated.video = mock_video_file

        mock_response = MagicMock()
        mock_response.generated_videos = [mock_generated]

        mock_op = MagicMock()
        mock_op.done = True
        mock_op.response = mock_response

        gen._client.models.generate_videos = MagicMock(return_value=mock_op)
        gen._client.files.download = MagicMock()

        with tempfile.TemporaryDirectory() as tmpdir:
            out = os.path.join(tmpdir, "test.mp4")
            result = gen.generate("test prompt", out)

        assert isinstance(result, VideoResult)
        assert result.model_used == gen.model_name
        assert result.estimated_cost > 0
        gen._client.models.generate_videos.assert_called_once()
        gen._client.files.download.assert_called_once()
        mock_video_file.save.assert_called_once()


# ---------------------------------------------------------------------------
# PVideoGenerator
# ---------------------------------------------------------------------------

class TestPVideoGenerator:
    def test_model_name_standard(self):
        gen = PVideoGenerator(draft=False, api_token="fake")
        assert "standard" in gen.model_name

    def test_model_name_draft(self):
        gen = PVideoGenerator(draft=True, api_token="fake")
        assert "draft" in gen.model_name

    def test_cost_standard_720p(self):
        gen = PVideoGenerator(draft=False, api_token="fake")
        assert gen.estimate_cost(5, "720p") == 0.10

    def test_cost_draft_720p(self):
        gen = PVideoGenerator(draft=True, api_token="fake")
        assert gen.estimate_cost(5, "720p") == 0.025

    def test_cost_standard_1080p(self):
        gen = PVideoGenerator(draft=False, api_token="fake")
        assert gen.estimate_cost(5, "1080p") == 0.20

    def test_cost_draft_1080p(self):
        gen = PVideoGenerator(draft=True, api_token="fake")
        assert gen.estimate_cost(5, "1080p") == 0.05

    def test_missing_api_token(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("REPLICATE_API_TOKEN", None)
            with pytest.raises(EnvironmentError, match="REPLICATE_API_TOKEN"):
                PVideoGenerator(api_token=None)
            os.environ["REPLICATE_API_TOKEN"] = "test-token"

    def test_extract_url_string(self):
        assert PVideoGenerator._extract_url("https://example.com/v.mp4") == "https://example.com/v.mp4"

    def test_extract_url_list(self):
        assert PVideoGenerator._extract_url(["https://example.com/v.mp4"]) == "https://example.com/v.mp4"

    @patch("video.pvideo_generator.urllib.request.urlretrieve")
    def test_generate_calls_api(self, mock_urlretrieve):
        """Test that generate() invokes the Replicate API and downloads output."""
        gen = PVideoGenerator(draft=True, api_token="fake")
        gen._client.run = MagicMock(return_value="https://example.com/video.mp4")

        with tempfile.TemporaryDirectory() as tmpdir:
            out = os.path.join(tmpdir, "test.mp4")
            result = gen.generate("test prompt", out, duration_seconds=3)

        assert isinstance(result, VideoResult)
        assert result.duration_seconds == 3
        assert result.estimated_cost == 0.015  # draft 720p: $0.005/s * 3s
        gen._client.run.assert_called_once()
        mock_urlretrieve.assert_called_once()


# ---------------------------------------------------------------------------
# Compare
# ---------------------------------------------------------------------------

class TestCompare:
    @patch("video.pvideo_generator.urllib.request.urlretrieve")
    def test_run_comparison(self, mock_urlretrieve):
        """Test comparison with a single mock model."""
        gen = PVideoGenerator(draft=True, api_token="fake")
        gen._client.run = MagicMock(return_value="https://example.com/video.mp4")

        with tempfile.TemporaryDirectory() as tmpdir:
            # Patch create_generator to return our mock
            with patch("video.compare.create_generator", return_value=gen):
                from video.compare import run_comparison

                summary = run_comparison(
                    prompt="test",
                    models=["p-video-draft"],
                    output_dir=tmpdir,
                    duration_seconds=2,
                )

        assert summary["total_estimated_cost"] > 0
        assert len(summary["results"]) == 1
        assert summary["results"][0]["status"] == "success"

    def test_run_comparison_skip_missing_key(self):
        """Models with missing API keys are skipped, not crashed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("video.compare.create_generator", side_effect=EnvironmentError("no key")):
                from video.compare import run_comparison

                summary = run_comparison(
                    prompt="test",
                    models=["veo-3.1"],
                    output_dir=tmpdir,
                )

        assert summary["results"][0]["status"] == "skipped"
