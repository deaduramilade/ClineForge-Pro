"""Tests for the storyboard generation application service."""

from unittest.mock import AsyncMock

import pytest

from src.backend.services.image_generation import GeneratedImage
from src.backend.services.scene_reasoning import CinematicPrompt
from src.backend.services.script_parser import Scene
from src.backend.services.storyboard_service import StoryboardGenerationService


def _scene() -> Scene:
    return Scene(
        index=0,
        heading="INT. ROOM - DAY",
        description="John walks into the room.",
        characters=[],
        location="ROOM",
        time_of_day="DAY",
        mood="neutral",
        dialogue=[],
        language="en",
    )


@pytest.mark.asyncio
async def test_generate_connects_reasoning_to_image_generation():
    scene = _scene()

    prompt = CinematicPrompt(
        visual_description="A cinematic interior room.",
        shot_type="medium",
        camera_angle="eye_level",
        lighting="natural daylight",
        mood="neutral",
        environment="interior room",
        negative_prompt="blurry, distorted",
    )

    image = GeneratedImage(
        image_bytes=b"\x89PNG\r\n\x1a\nimage-data",
        mime_type="image/png",
        provider_id="fake-provider",
        model_id="fake-model",
    )

    reasoning_service = AsyncMock()
    reasoning_service.reason.return_value = prompt

    image_service = AsyncMock()
    image_service.generate.return_value = image

    service = StoryboardGenerationService(
        reasoning_service=reasoning_service,
        image_service=image_service,
    )

    result = await service.generate(scene, style="cinematic")

    reasoning_service.reason.assert_awaited_once_with(
        scene,
        style="cinematic",
    )
    image_service.generate.assert_awaited_once_with(prompt)

    assert result.cinematic_prompt is prompt
    assert result.generated_image is image


@pytest.mark.asyncio
async def test_reasoning_failure_stops_pipeline():
    scene = _scene()
    error = RuntimeError("reasoning failed")

    reasoning_service = AsyncMock()
    reasoning_service.reason.side_effect = error

    image_service = AsyncMock()

    service = StoryboardGenerationService(
        reasoning_service=reasoning_service,
        image_service=image_service,
    )

    with pytest.raises(RuntimeError, match="reasoning failed"):
        await service.generate(scene)

    image_service.generate.assert_not_awaited()


@pytest.mark.asyncio
async def test_image_generation_failure_propagates():
    scene = _scene()

    prompt = CinematicPrompt(
        visual_description="A cinematic interior room.",
        shot_type="medium",
        camera_angle="eye_level",
        lighting="natural daylight",
        mood="neutral",
        environment="interior room",
        negative_prompt="blurry",
    )

    reasoning_service = AsyncMock()
    reasoning_service.reason.return_value = prompt

    image_service = AsyncMock()
    image_service.generate.side_effect = RuntimeError("image generation failed")

    service = StoryboardGenerationService(
        reasoning_service=reasoning_service,
        image_service=image_service,
    )

    with pytest.raises(RuntimeError, match="image generation failed"):
        await service.generate(scene)

    reasoning_service.reason.assert_awaited_once()
    image_service.generate.assert_awaited_once_with(prompt)
