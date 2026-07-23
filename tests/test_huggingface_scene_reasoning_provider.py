"""Tests for the Hugging Face scene-reasoning provider."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest

from src.backend.services.huggingface_scene_reasoning_provider import (
    HuggingFaceSceneReasoningProvider,
)
from src.backend.services.scene_reasoning import SceneReasoningError


def _response(content: str):
    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content=content)
            )
        ]
    )


def test_requires_api_token(monkeypatch):
    monkeypatch.delenv("HUGGINGFACE_API_TOKEN", raising=False)

    with pytest.raises(
        EnvironmentError,
        match="HUGGINGFACE_API_TOKEN",
    ):
        HuggingFaceSceneReasoningProvider()


def test_constructor_accepts_explicit_token():
    client = Mock()

    provider = HuggingFaceSceneReasoningProvider(
        api_token="test-token",
        client=client,
    )

    assert provider._api_token == "test-token"


@pytest.mark.asyncio
async def test_generate_returns_model_content():
    client = Mock()
    client.chat_completion.return_value = _response(
        '{"mood":"neutral"}'
    )

    provider = HuggingFaceSceneReasoningProvider(
        api_token="test-token",
        model_id="test-model",
        client=client,
    )

    result = await provider.generate(
        "system prompt",
        "user prompt",
    )

    assert result == '{"mood":"neutral"}'

    client.chat_completion.assert_called_once_with(
        model="test-model",
        messages=[
            {
                "role": "system",
                "content": "system prompt",
            },
            {
                "role": "user",
                "content": "user prompt",
            },
        ],
        max_tokens=700,
        temperature=0.0,
        response_format={"type": "json_object"},
    )


@pytest.mark.asyncio
async def test_empty_response_raises_domain_error():
    client = Mock()
    client.chat_completion.return_value = _response("   ")

    provider = HuggingFaceSceneReasoningProvider(
        api_token="test-token",
        client=client,
    )

    with pytest.raises(
        SceneReasoningError,
        match="empty response",
    ):
        await provider.generate(
            "system prompt",
            "user prompt",
        )


@pytest.mark.asyncio
async def test_provider_failure_is_wrapped():
    client = Mock()
    client.chat_completion.side_effect = RuntimeError(
        "provider unavailable"
    )

    provider = HuggingFaceSceneReasoningProvider(
        api_token="test-token",
        client=client,
    )

    with pytest.raises(
        SceneReasoningError,
        match="Hugging Face scene reasoning failed",
    ) as exc_info:
        await provider.generate(
            "system prompt",
            "user prompt",
        )

    assert isinstance(exc_info.value.cause, RuntimeError)
