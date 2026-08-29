#!/usr/bin/env python3
"""Version-independent image generation on top of ``google-genai``.

Why this exists
---------------
``client.models.generate_images()`` (the Imagen ``:predict`` path) was removed
from the Gemini Developer API surface in google-genai 2.x.  On 2.20.0 it does
not even reach the network:

    ValueError: This method is only supported in Gemini Enterprise Agent
    Platform mode, not in Gemini Developer API mode.

``client.models.generate_content()`` with an image model is the supported
replacement, and it emits a byte-identical request on 1.61.0 and 2.20.0 - so
call sites routed through here work on both SDK versions.  See
``docs/research/sdk-migration-decision.md``.

The default model matches the project standard in CLAUDE.md
(``gemini-2.5-flash-image`` minimum, ``gemini-3-pro-image-preview`` preferred).
"""

from __future__ import annotations

from typing import Optional

DEFAULT_IMAGE_MODEL = "gemini-2.5-flash-image"


def generate_image_bytes(
    client,
    prompt,
    *,
    model: str = DEFAULT_IMAGE_MODEL,
    aspect_ratio: Optional[str] = None,
) -> Optional[bytes]:
    """Generate one image and return its raw bytes, or None if the model
    returned no image part.

    Args:
        client: a ``google.genai.Client``.
        prompt: a text prompt, or a list of parts for image-to-image.
        model: image-capable Gemini model id.
        aspect_ratio: e.g. "16:9".  Omitted from the request when None.

    Callers that also want the model's text (refusals, explanations) should
    use :func:`generate_image` instead.
    """
    image_bytes, _ = generate_image(
        client, prompt, model=model, aspect_ratio=aspect_ratio
    )
    return image_bytes


def generate_image(
    client,
    prompt,
    *,
    model: str = DEFAULT_IMAGE_MODEL,
    aspect_ratio: Optional[str] = None,
) -> tuple[Optional[bytes], str]:
    """Same as :func:`generate_image_bytes` but also returns the model's text.

    Returns:
        ``(image_bytes_or_None, text)``.
    """
    from google.genai import types

    config_kwargs: dict = {"response_modalities": ["Text", "Image"]}
    if aspect_ratio:
        config_kwargs["image_config"] = types.ImageConfig(aspect_ratio=aspect_ratio)

    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(**config_kwargs),
    )

    texts: list[str] = []
    for candidate in response.candidates or []:
        content = getattr(candidate, "content", None)
        for part in (getattr(content, "parts", None) or []):
            inline = getattr(part, "inline_data", None)
            if inline is not None and getattr(inline, "data", None):
                return inline.data, "".join(texts)
            if getattr(part, "text", None):
                texts.append(part.text)

    return None, "".join(texts)
