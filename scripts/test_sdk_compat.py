#!/usr/bin/env python3
"""Offline guard rails for the google-genai SDK version.

The existing suites (video/test_omni_flash.py, pipeline/test_orchestrator.py)
mock the SDK client itself, so they pass on both 1.61.0 and 2.20.0 and cannot
see the wire-format split that made every Omni call fail.  These tests go one
layer lower: they stub httpx and assert on the bytes the SDK actually puts on
the wire.

No network, no API key, no spend - httpx.Client.send is replaced with a canned
responder for the whole module.

Run:  cd scripts && python -m pytest test_sdk_compat.py -v
"""

import base64
import json
import os
import sys
from pathlib import Path

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).parent))

os.environ.setdefault("GEMINI_API_KEY", "not-a-real-key")

FAKE_PNG = b"\x89PNG\r\n\x1a\nfake-image-bytes"
FAKE_MP4 = b"\x00\x00\x00\x18ftypmp42" + b"x" * 512


# ---------------------------------------------------------------------------
# Canned transport
# ---------------------------------------------------------------------------

def _canned(request: httpx.Request) -> httpx.Response:
    url = str(request.url)
    if "/interactions" in url:
        body = {
            "id": "interactions/offline-test",
            "status": "completed",
            "output_video": {
                "type": "video",
                "mime_type": "video/mp4",
                "data": base64.b64encode(FAKE_MP4).decode(),
            },
            "usage": {
                "total_input_tokens": 1161,
                "total_output_tokens": 10331,
                "output_tokens_by_modality": [{"modality": "video", "tokens": 9655}],
            },
        }
    elif ":predictLongRunning" in url:
        body = {"name": "models/veo/operations/offline-test"}
    else:
        body = {
            "candidates": [{
                "content": {"role": "model", "parts": [
                    {"inlineData": {"mimeType": "image/png",
                                    "data": base64.b64encode(FAKE_PNG).decode()}},
                ]},
                "finishReason": "STOP",
            }],
            "usageMetadata": {"promptTokenCount": 1, "candidatesTokenCount": 2,
                              "totalTokenCount": 3},
        }
    return httpx.Response(200, json=body, request=request)


@pytest.fixture
def captured(monkeypatch):
    """Stub httpx so no request leaves the machine; yields the request list."""
    seen: list[httpx.Request] = []

    def _send(self, request, **kwargs):
        seen.append(request)
        return _canned(request)

    monkeypatch.setattr(httpx.Client, "send", _send)
    return seen


def _body(request: httpx.Request) -> dict:
    return json.loads(request.content.decode())


def _client():
    from google import genai
    return genai.Client(api_key="not-a-real-key")


# ---------------------------------------------------------------------------
# Version floor
# ---------------------------------------------------------------------------

def test_sdk_is_2x():
    """Omni is impossible on 1.x - fail loudly rather than at generation time."""
    from google import genai

    major = int(genai.__version__.split(".")[0])
    assert major >= 2, (
        f"google-genai {genai.__version__} is installed; the Interactions API "
        "(Gemini Omni) requires >= 2.0.0. Run ./scripts/setup_python_env.sh"
    )


def test_interaction_model_carries_video_output():
    """1.x's Interaction has no output_video field and silently drops the clip."""
    from google.genai.interactions import Interaction

    assert "output_video" in Interaction.model_fields


# ---------------------------------------------------------------------------
# Omni: the wire format that 1.x got wrong
# ---------------------------------------------------------------------------

def test_omni_request_uses_user_input_envelope(captured, tmp_path):
    """SDK 2.x wraps each input entry in a ``user_input`` envelope.

    1.61.0 emitted the flat legacy form ``{"text": ..., "type": "text"}``, which
    the server has rejected since May 2026.
    """
    from video.omni_flash import OmniFlashGenerator

    gen = OmniFlashGenerator()
    gen.generate("A dinosaur walks.", str(tmp_path / "out.mp4"),
                 duration_seconds=5, resolution="360p")

    body = _body(captured[-1])
    assert str(captured[-1].url).endswith("/interactions")
    assert body["input"] == [{
        "type": "user_input",
        "content": [{"type": "text", "text": "A dinosaur walks."}],
    }]
    # Duration is a string on response_format, not an int under video_config.
    assert body["response_format"]["duration"] == "5s"
    assert body["generation_config"]["video_config"]["task"] == "text_to_video"


def test_omni_writes_the_returned_video(captured, tmp_path):
    from video.omni_flash import OmniFlashGenerator

    out = tmp_path / "out.mp4"
    result = OmniFlashGenerator().generate(
        "A dinosaur walks.", str(out), duration_seconds=5, resolution="360p"
    )
    assert out.read_bytes() == FAKE_MP4
    assert result.estimated_cost > 0


# ---------------------------------------------------------------------------
# Image generation: the path every storyboard script depends on
# ---------------------------------------------------------------------------

def test_generate_content_image_request_shape(captured):
    """Byte-for-byte the same request 1.61.0 sent - this must not drift."""
    from google.genai import types

    _client().models.generate_content(
        model="gemini-3-pro-image-preview",
        contents=[
            types.Part.from_bytes(data=FAKE_PNG, mime_type="image/png"),
            types.Part.from_text(text="Match the reference character."),
        ],
        config=types.GenerateContentConfig(response_modalities=["Text", "Image"]),
    )

    assert _body(captured[-1]) == {
        "contents": [{
            "role": "user",
            "parts": [
                {"inlineData": {"mimeType": "image/png",
                                "data": base64.b64encode(FAKE_PNG).decode()}},
                {"text": "Match the reference character."},
            ],
        }],
        "generationConfig": {"responseModalities": ["Text", "Image"]},
    }


def test_genai_compat_returns_image_bytes(captured):
    """The Imagen replacement helper parses a real response shape."""
    from genai_compat import generate_image

    image_bytes, text = generate_image(
        _client(), "A cozy living room.", aspect_ratio="16:9"
    )
    assert image_bytes == FAKE_PNG
    assert text == ""
    assert _body(captured[-1])["generationConfig"]["imageConfig"] == {"aspectRatio": "16:9"}


def test_imagen_generate_images_is_gone_on_2x(captured):
    """Documents the one regression: don't reintroduce generate_images().

    On 2.x this raises before any HTTP request is built, so the four scripts
    that used to call it now go through genai_compat.generate_image instead.
    The ``captured`` fixture is taken purely so that on an older SDK this test
    fails offline instead of dialling out.
    """
    from google.genai import types

    with pytest.raises(ValueError, match="Gemini Enterprise Agent Platform mode"):
        _client().models.generate_images(
            model="imagen-4.0-generate-001",
            prompt="anything",
            config=types.GenerateImagesConfig(number_of_images=1),
        )


def test_no_script_calls_generate_images():
    """Guard the migration: nothing under scripts/ may call generate_images().

    Parsed with ast so prose about the migration doesn't trip it.
    """
    import ast

    root = Path(__file__).parent
    offenders = []
    for path in sorted(root.rglob("*.py")):
        if path.name == Path(__file__).name:
            continue
        try:
            tree = ast.parse(path.read_text())
        except SyntaxError:
            continue  # Blender-only scripts may target another interpreter
        for node in ast.walk(tree):
            if (isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "generate_images"):
                offenders.append(f"{path.relative_to(root)}:{node.lineno}")
    assert not offenders, (
        "client.models.generate_images() is unsupported on google-genai 2.x; "
        f"use genai_compat.generate_image instead. Found at: {offenders}"
    )


# ---------------------------------------------------------------------------
# Veo
# ---------------------------------------------------------------------------

def test_veo_request_shape_unchanged(captured):
    from google.genai import types

    _client().models.generate_videos(
        model="veo-3.0-generate-001",
        prompt="A living room at dusk.",
        image=types.Image(image_bytes=FAKE_PNG, mime_type="image/png"),
        config=types.GenerateVideosConfig(
            aspect_ratio="16:9", number_of_videos=1, duration_seconds=8
        ),
    )

    body = _body(captured[-1])
    assert body["instances"][0]["prompt"] == "A living room at dusk."
    assert body["parameters"] == {
        "aspectRatio": "16:9", "durationSeconds": 8, "sampleCount": 1
    }
