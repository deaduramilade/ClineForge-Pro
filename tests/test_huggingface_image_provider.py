"""Tests for the Hugging Face image-generation provider."""

from unittest.mock import MagicMock

import pytest

from src.backend.services.huggingface_image_provider import (
    HuggingFaceImageGenerationProvider,
)
from src.backend.services.image_generation import ImageGenerationError


class FakeImage:
    """Minimal Pillow-like image object returned by InferenceClient."""

    def save(self, buffer, format):
        assert format == "PNG"
        buffer.write(b"\x89PNG\r\n\x1a\nfake-image-data")


@pytest.mark.asyncio
async def test_generate_image_returns_png_result():
    client = MagicMock()
    client.text_to_image.return_value = FakeImage()

    provider = HuggingFaceImageGenerationProvider(
        api_token="test-token",
        model_id="test/model",
        inference_provider="auto",
        client=client,
    )

    result = await provider.generate_image(
        "A cinematic room",
        "blurry, distorted",
        width=768,
        height=512,
    )

    client.text_to_image.assert_called_once_with(
        "A cinematic room",
        negative_prompt="blurry, distorted",
        width=768,
        height=512,
    )

    assert result.image_bytes.startswith(b"\x89PNG\r\n\x1a\n")
    assert result.mime_type == "image/png"
    assert result.provider_id == "huggingface"
    assert result.model_id == "test/model"


@pytest.mark.asyncio
async def test_empty_negative_prompt_becomes_none():
    client = MagicMock()
    client.text_to_image.return_value = FakeImage()

    provider = HuggingFaceImageGenerationProvider(
        api_token="test-token",
        model_id="test/model",
        client=client,
    )

    await provider.generate_image("A cinematic room", "")

    client.text_to_image.assert_called_once_with(
        "A cinematic room",
        negative_prompt=None,
        width=512,
        height=512,
    )


@pytest.mark.asyncio
async def test_provider_failure_is_wrapped():
    client = MagicMock()
    error = RuntimeError("provider unavailable")
    client.text_to_image.side_effect = error

    provider = HuggingFaceImageGenerationProvider(
        api_token="test-token",
        model_id="test/model",
        client=client,
    )

    with pytest.raises(
        ImageGenerationError,
        match="Hugging Face image generation failed",
    ) as exc_info:
        await provider.generate_image("A room", "blurry")

    assert exc_info.value.cause is error


def test_missing_token_fails_configuration(monkeypatch):
    monkeypatch.delenv("HUGGINGFACE_API_TOKEN", raising=False)

    with pytest.raises(
        EnvironmentError,
        match="HUGGINGFACE_API_TOKEN",
    ):
        HuggingFaceImageGenerationProvider(
            api_token=None,
            model_id="test/model",
        )


def test_missing_model_fails_configuration(monkeypatch):
    monkeypatch.delenv("IMAGE_GENERATION_MODEL_ID", raising=False)

    with pytest.raises(
        EnvironmentError,
        match="IMAGE_GENERATION_MODEL_ID",
    ):
        HuggingFaceImageGenerationProvider(
            api_token="test-token",
            model_id=None,
        )
