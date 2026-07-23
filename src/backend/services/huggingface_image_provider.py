"""Hugging Face Inference Providers image-generation adapter."""

from __future__ import annotations

import asyncio
import io
import os
from typing import Any

from huggingface_hub import InferenceClient

from src.backend.services.image_generation import (
    GeneratedImage,
    ImageGenerationError,
    ImageGenerationProvider,
)


class HuggingFaceImageGenerationProvider(ImageGenerationProvider):
    """Generate images through Hugging Face Inference Providers."""

    provider_id = "huggingface"

    def __init__(
        self,
        *,
        api_token: str | None = None,
        model_id: str | None = None,
        inference_provider: str | None = None,
        timeout_seconds: float = 60.0,
        client: Any | None = None,
    ) -> None:
        self._api_token = api_token or os.getenv("HUGGINGFACE_API_TOKEN")
        self._model_id = model_id or os.getenv("IMAGE_GENERATION_MODEL_ID")
        self._inference_provider = (
            inference_provider
            or os.getenv("IMAGE_GENERATION_PROVIDER")
            or "auto"
        )

        if not self._api_token:
            raise EnvironmentError(
                "HUGGINGFACE_API_TOKEN must be configured."
            )

        if not self._model_id:
            raise EnvironmentError(
                "IMAGE_GENERATION_MODEL_ID must be configured."
            )

        self._client = client or InferenceClient(
            model=self._model_id,
            provider=self._inference_provider,
            token=self._api_token,
            timeout=timeout_seconds,
        )

    async def generate_image(
        self,
        prompt: str,
        negative_prompt: str,
        width: int = 512,
        height: int = 512,
    ) -> GeneratedImage:
        try:
            image = await asyncio.to_thread(
                self._client.text_to_image,
                prompt,
                negative_prompt=negative_prompt or None,
                width=width,
                height=height,
            )

            buffer = io.BytesIO()
            image.save(buffer, format="PNG")

            return GeneratedImage(
                image_bytes=buffer.getvalue(),
                mime_type="image/png",
                provider_id=self.provider_id,
                model_id=self._model_id,
            )

        except Exception as exc:
            raise ImageGenerationError(
                f"Hugging Face image generation failed: {exc}",
                cause=exc,
            ) from exc
