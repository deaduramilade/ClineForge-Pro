"""Hugging Face scene-reasoning provider."""

from __future__ import annotations

import asyncio
import os
from typing import Any

from huggingface_hub import InferenceClient

from src.backend.services.scene_reasoning import (
    SceneReasoningError,
    SceneReasoningProvider,
)


class HuggingFaceSceneReasoningProvider(SceneReasoningProvider):
    """Scene reasoning through Hugging Face Inference Providers."""

    def __init__(
        self,
        *,
        api_token: str | None = None,
        model_id: str | None = None,
        inference_provider: str | None = None,
        client: Any | None = None,
    ) -> None:
        self._api_token = api_token or os.getenv("HUGGINGFACE_API_TOKEN")
        self._model_id = (
            model_id
            or os.getenv("SCENE_REASONING_MODEL_ID")
            or "Qwen/Qwen2.5-7B-Instruct"
        )
        self._inference_provider = (
            inference_provider
            or os.getenv("SCENE_REASONING_PROVIDER")
            or "auto"
        )

        if not self._api_token:
            raise EnvironmentError(
                "HUGGINGFACE_API_TOKEN must be configured."
            )

        self._client = client or InferenceClient(
            provider=self._inference_provider,
            token=self._api_token,
        )

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        try:
            response = await asyncio.to_thread(
                self._client.chat_completion,
                model=self._model_id,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": user_prompt,
                    },
                ],
                max_tokens=700,
                temperature=0.0,
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content

            if not content or not content.strip():
                raise SceneReasoningError(
                    "Hugging Face reasoning provider returned an empty response."
                )

            return content.strip()

        except SceneReasoningError:
            raise
        except Exception as exc:
            raise SceneReasoningError(
                f"Hugging Face scene reasoning failed: {exc}",
                cause=exc,
            ) from exc
