"""
Tests for src/backend/services/scene_reasoning.py

All tests are fully deterministic and require no network access.
The ``GraniteSceneReasoningProvider`` is never instantiated here — a
``FakeProvider`` is injected instead, giving complete control over the
raw response string.

Coverage
--------
Domain models
  - CinematicPrompt: valid construction from all fields
  - CinematicPrompt: default characters list (empty)
  - CinematicPrompt: mood validation — all four valid moods accepted
  - CinematicPrompt: mood normalisation — lowercase coercion
  - CinematicPrompt: invalid mood rejected with ValueError
  - CinematicPrompt: empty visual_description rejected
  - CinematicPrompt: empty lighting rejected
  - CinematicPrompt: empty environment rejected
  - CinematicPrompt: empty negative_prompt rejected
  - CinematicPrompt: characters list with blank entries is stripped
  - CinematicPrompt: characters list with non-string entry rejected
  - ShotType enum: all five values present and lowercase-string-valued
  - CameraAngle enum: all four values present and lowercase-string-valued
  - SceneReasoningError: stores cause correctly

Provider abstraction
  - SceneReasoningProvider is abstract (cannot be instantiated)
  - FakeProvider satisfies the ABC contract

SceneReasoningService with English scene
  - returns CinematicPrompt when provider returns valid JSON
  - visual_description is non-empty string
  - shot_type is a ShotType instance
  - camera_angle is a CameraAngle instance
  - characters list contains scene characters
  - mood is "dark" (passed through from fixture)

SceneReasoningService with Arabic scene
  - returns CinematicPrompt from an Arabic-language scene
  - visual_description is in English (fixture-controlled)
  - language on the scene is "ar"

SceneReasoningService with style variants
  - "sketch" style: provider still returns valid CinematicPrompt
  - "anime" style: provider still returns valid CinematicPrompt

SceneReasoningService failure modes
  - non-JSON provider response → SceneReasoningError
  - JSON array (not object) → SceneReasoningError
  - JSON object missing required field → SceneReasoningError
  - JSON object with invalid shot_type → SceneReasoningError
  - JSON object with invalid mood → SceneReasoningError
  - JSON object with invalid camera_angle → SceneReasoningError
  - provider raises SceneReasoningError → propagated unchanged
  - provider raises unexpected Exception → re-raised (not swallowed)

Provider output handling
  - markdown code fence (```json ... ```) is stripped before JSON parse
  - markdown fence without language tag (``` ... ```) is stripped
  - leading/trailing whitespace in provider output is stripped

Prompt construction (black-box verification)
  - scene heading appears in user prompt
  - scene location appears in user prompt
  - Arabic scene language tag appears in user prompt
  - English scene language tag appears in user prompt
  - style preference appears in user prompt
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from src.backend.services.script_parser import Scene
from src.backend.services.scene_reasoning import (
    CameraAngle,
    CinematicPrompt,
    SceneReasoningError,
    SceneReasoningProvider,
    SceneReasoningService,
    ShotType,
    _build_user_prompt,
    _SYSTEM_PROMPT,
)


# ---------------------------------------------------------------------------
# Helpers — fake provider and scene fixtures
# ---------------------------------------------------------------------------


class FakeProvider(SceneReasoningProvider):
    """Deterministic provider for testing — returns a pre-configured string."""

    def __init__(self, response: str) -> None:
        self._response = response

    async def generate(self, system_prompt: str, user_prompt: str) -> str:  # noqa: ARG002
        return self._response


class FailingProvider(SceneReasoningProvider):
    """Provider that always raises SceneReasoningError."""

    def __init__(self, message: str = "provider failure") -> None:
        self._message = message

    async def generate(self, system_prompt: str, user_prompt: str) -> str:  # noqa: ARG002
        raise SceneReasoningError(self._message)


class ExplodingProvider(SceneReasoningProvider):
    """Provider that raises an unexpected non-SceneReasoningError exception."""

    async def generate(self, system_prompt: str, user_prompt: str) -> str:  # noqa: ARG002
        raise RuntimeError("unexpected SDK crash")


def _valid_json(**overrides: Any) -> str:
    """Return a JSON string for a valid CinematicPrompt, with optional field overrides."""
    base: dict[str, Any] = {
        "visual_description": (
            "Cinematic wide shot, INT. bakery at dawn, flour dust particles "
            "floating in golden sunbeam, BAKER behind counter, warm amber "
            "lighting, shallow depth of field, 35mm film look"
        ),
        "shot_type": "wide",
        "camera_angle": "eye_level",
        "lighting": "warm amber, soft diffused morning light",
        "mood": "neutral",
        "environment": "interior bakery, early morning",
        "characters": ["BAKER"],
        "negative_prompt": "text, watermarks, blurry, low quality, distorted",
    }
    base.update(overrides)
    return json.dumps(base)


def _make_en_scene(
    *,
    index: int = 0,
    heading: str = "INT. BAKERY - DAY",
    description: str = "The smell of fresh bread fills the air.",
    characters: list[str] | None = None,
    location: str = "BAKERY",
    time_of_day: str = "DAY",
    mood: str = "neutral",
) -> Scene:
    return Scene(
        index=index,
        heading=heading,
        description=description,
        characters=characters if characters is not None else ["BAKER"],
        location=location,
        time_of_day=time_of_day,
        mood=mood,
        dialogue=["Good morning."],
        language="en",
    )


def _make_ar_scene(
    *,
    index: int = 1,
    heading: str = "داخلي. المطبخ - صباح",
    description: str = "الأم تُعِدّ القهوة بهدوء.",
    characters: list[str] | None = None,
    location: str = "المطبخ",
    time_of_day: str = "صباح",
    mood: str = "neutral",
) -> Scene:
    return Scene(
        index=index,
        heading=heading,
        description=description,
        characters=characters if characters is not None else ["الأم"],
        location=location,
        time_of_day=time_of_day,
        mood=mood,
        dialogue=[],
        language="ar",
    )


# ---------------------------------------------------------------------------
# ShotType enum
# ---------------------------------------------------------------------------


def test_shot_type_values_are_lowercase_strings():
    """Every ShotType value must be a lowercase string usable in prompts."""
    for member in ShotType:
        assert isinstance(member.value, str)
        assert member.value == member.value.lower()


def test_shot_type_has_five_members():
    assert len(ShotType) == 5


def test_shot_type_covers_expected_shots():
    names = {m.value for m in ShotType}
    assert "wide" in names
    assert "medium" in names
    assert "close_up" in names
    assert "extreme_close_up" in names
    assert "aerial" in names


# ---------------------------------------------------------------------------
# CameraAngle enum
# ---------------------------------------------------------------------------


def test_camera_angle_values_are_lowercase_strings():
    for member in CameraAngle:
        assert isinstance(member.value, str)
        assert member.value == member.value.lower()


def test_camera_angle_has_four_members():
    assert len(CameraAngle) == 4


def test_camera_angle_covers_expected_angles():
    names = {m.value for m in CameraAngle}
    assert "eye_level" in names
    assert "low_angle" in names
    assert "high_angle" in names
    assert "dutch" in names


# ---------------------------------------------------------------------------
# SceneReasoningError
# ---------------------------------------------------------------------------


def test_scene_reasoning_error_is_exception():
    err = SceneReasoningError("something went wrong")
    assert isinstance(err, Exception)
    assert str(err) == "something went wrong"


def test_scene_reasoning_error_stores_cause():
    original = ValueError("root cause")
    err = SceneReasoningError("wrapped", cause=original)
    assert err.cause is original


def test_scene_reasoning_error_cause_defaults_to_none():
    err = SceneReasoningError("no cause")
    assert err.cause is None


# ---------------------------------------------------------------------------
# CinematicPrompt — valid construction
# ---------------------------------------------------------------------------


def test_cinematic_prompt_valid_all_fields():
    p = CinematicPrompt(
        visual_description="Wide shot of a desert at dusk, lone figure on horizon",
        shot_type=ShotType.WIDE,
        camera_angle=CameraAngle.LOW_ANGLE,
        lighting="golden hour backlit",
        mood="tense",
        environment="exterior desert, dusk",
        characters=["ALICE"],
        negative_prompt="text, watermarks, blurry",
    )
    assert p.visual_description.startswith("Wide shot")
    assert p.shot_type is ShotType.WIDE
    assert p.camera_angle is CameraAngle.LOW_ANGLE
    assert p.mood == "tense"
    assert "ALICE" in p.characters


def test_cinematic_prompt_string_shot_type_accepted():
    """String values for shot_type should be coerced into the enum."""
    p = CinematicPrompt(
        visual_description="test description",
        shot_type="medium",  # type: ignore[arg-type]
        camera_angle="eye_level",  # type: ignore[arg-type]
        lighting="soft",
        mood="neutral",
        environment="interior",
        negative_prompt="text",
    )
    assert p.shot_type is ShotType.MEDIUM
    assert p.camera_angle is CameraAngle.EYE_LEVEL


def test_cinematic_prompt_defaults_empty_characters():
    p = CinematicPrompt(
        visual_description="Empty scene",
        shot_type=ShotType.AERIAL,
        camera_angle=CameraAngle.HIGH_ANGLE,
        lighting="overcast",
        mood="dark",
        environment="exterior rooftop",
        negative_prompt="text, blurry",
    )
    assert p.characters == []


def test_cinematic_prompt_all_valid_moods():
    for mood in ("neutral", "romantic", "tense", "dark"):
        p = CinematicPrompt(
            visual_description="test",
            shot_type=ShotType.MEDIUM,
            camera_angle=CameraAngle.EYE_LEVEL,
            lighting="soft",
            mood=mood,
            environment="studio",
            negative_prompt="text",
        )
        assert p.mood == mood


def test_cinematic_prompt_mood_normalised_to_lowercase():
    p = CinematicPrompt(
        visual_description="test",
        shot_type=ShotType.MEDIUM,
        camera_angle=CameraAngle.EYE_LEVEL,
        lighting="soft",
        mood="  Tense  ",
        environment="studio",
        negative_prompt="text",
    )
    assert p.mood == "tense"


# ---------------------------------------------------------------------------
# CinematicPrompt — validation rejections
# ---------------------------------------------------------------------------


def test_cinematic_prompt_invalid_mood_rejected():
    with pytest.raises(Exception):  # Pydantic ValidationError
        CinematicPrompt(
            visual_description="test",
            shot_type=ShotType.WIDE,
            camera_angle=CameraAngle.EYE_LEVEL,
            lighting="soft",
            mood="melancholic",  # not in allowed set
            environment="studio",
            negative_prompt="text",
        )


def test_cinematic_prompt_empty_visual_description_rejected():
    with pytest.raises(Exception):
        CinematicPrompt(
            visual_description="",
            shot_type=ShotType.WIDE,
            camera_angle=CameraAngle.EYE_LEVEL,
            lighting="soft",
            mood="neutral",
            environment="studio",
            negative_prompt="text",
        )


def test_cinematic_prompt_empty_lighting_rejected():
    with pytest.raises(Exception):
        CinematicPrompt(
            visual_description="test",
            shot_type=ShotType.WIDE,
            camera_angle=CameraAngle.EYE_LEVEL,
            lighting="",
            mood="neutral",
            environment="studio",
            negative_prompt="text",
        )


def test_cinematic_prompt_empty_environment_rejected():
    with pytest.raises(Exception):
        CinematicPrompt(
            visual_description="test",
            shot_type=ShotType.WIDE,
            camera_angle=CameraAngle.EYE_LEVEL,
            lighting="soft",
            mood="neutral",
            environment="",
            negative_prompt="text",
        )


def test_cinematic_prompt_empty_negative_prompt_rejected():
    with pytest.raises(Exception):
        CinematicPrompt(
            visual_description="test",
            shot_type=ShotType.WIDE,
            camera_angle=CameraAngle.EYE_LEVEL,
            lighting="soft",
            mood="neutral",
            environment="studio",
            negative_prompt="",
        )


def test_cinematic_prompt_invalid_shot_type_rejected():
    with pytest.raises(Exception):
        CinematicPrompt(
            visual_description="test",
            shot_type="fisheye",  # type: ignore[arg-type]
            camera_angle=CameraAngle.EYE_LEVEL,
            lighting="soft",
            mood="neutral",
            environment="studio",
            negative_prompt="text",
        )


def test_cinematic_prompt_invalid_camera_angle_rejected():
    with pytest.raises(Exception):
        CinematicPrompt(
            visual_description="test",
            shot_type=ShotType.WIDE,
            camera_angle="bird_eye",  # type: ignore[arg-type]
            lighting="soft",
            mood="neutral",
            environment="studio",
            negative_prompt="text",
        )


def test_cinematic_prompt_characters_blank_entries_stripped():
    """Blank strings in the characters list should be removed silently."""
    p = CinematicPrompt(
        visual_description="test",
        shot_type=ShotType.MEDIUM,
        camera_angle=CameraAngle.EYE_LEVEL,
        lighting="soft",
        mood="neutral",
        environment="studio",
        characters=["ALICE", "  ", "BOB", ""],
        negative_prompt="text",
    )
    assert p.characters == ["ALICE", "BOB"]


def test_cinematic_prompt_characters_non_string_entry_rejected():
    with pytest.raises(Exception):
        CinematicPrompt(
            visual_description="test",
            shot_type=ShotType.MEDIUM,
            camera_angle=CameraAngle.EYE_LEVEL,
            lighting="soft",
            mood="neutral",
            environment="studio",
            characters=[42],  # type: ignore[list-item]
            negative_prompt="text",
        )


# ---------------------------------------------------------------------------
# Provider abstraction
# ---------------------------------------------------------------------------


def test_scene_reasoning_provider_is_abstract():
    """SceneReasoningProvider must not be directly instantiable."""
    with pytest.raises(TypeError):
        SceneReasoningProvider()  # type: ignore[abstract]


def test_fake_provider_satisfies_abc():
    """FakeProvider is a valid concrete implementation."""
    provider = FakeProvider(_valid_json())
    assert isinstance(provider, SceneReasoningProvider)


# ---------------------------------------------------------------------------
# SceneReasoningService — English scene happy path
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_service_returns_cinematic_prompt_for_english_scene():
    scene = _make_en_scene()
    service = SceneReasoningService(FakeProvider(_valid_json()))
    result = await service.reason(scene, style="cinematic")
    assert isinstance(result, CinematicPrompt)


@pytest.mark.asyncio
async def test_service_visual_description_non_empty():
    scene = _make_en_scene()
    service = SceneReasoningService(FakeProvider(_valid_json()))
    result = await service.reason(scene)
    assert len(result.visual_description) > 0


@pytest.mark.asyncio
async def test_service_shot_type_is_enum():
    scene = _make_en_scene()
    service = SceneReasoningService(FakeProvider(_valid_json(shot_type="medium")))
    result = await service.reason(scene)
    assert isinstance(result.shot_type, ShotType)
    assert result.shot_type is ShotType.MEDIUM


@pytest.mark.asyncio
async def test_service_camera_angle_is_enum():
    scene = _make_en_scene()
    service = SceneReasoningService(FakeProvider(_valid_json(camera_angle="low_angle")))
    result = await service.reason(scene)
    assert isinstance(result.camera_angle, CameraAngle)
    assert result.camera_angle is CameraAngle.LOW_ANGLE


@pytest.mark.asyncio
async def test_service_characters_from_provider_response():
    scene = _make_en_scene(characters=["ALICE", "BOB"])
    service = SceneReasoningService(
        FakeProvider(_valid_json(characters=["ALICE", "BOB"]))
    )
    result = await service.reason(scene)
    assert "ALICE" in result.characters
    assert "BOB" in result.characters


@pytest.mark.asyncio
async def test_service_mood_dark_forwarded():
    scene = _make_en_scene(mood="dark")
    service = SceneReasoningService(FakeProvider(_valid_json(mood="dark")))
    result = await service.reason(scene)
    assert result.mood == "dark"


@pytest.mark.asyncio
async def test_service_all_valid_shot_types_accepted():
    """Service accepts every valid ShotType from the provider."""
    scene = _make_en_scene()
    for shot in ShotType:
        service = SceneReasoningService(
            FakeProvider(_valid_json(shot_type=shot.value))
        )
        result = await service.reason(scene)
        assert result.shot_type is shot


@pytest.mark.asyncio
async def test_service_all_valid_camera_angles_accepted():
    scene = _make_en_scene()
    for angle in CameraAngle:
        service = SceneReasoningService(
            FakeProvider(_valid_json(camera_angle=angle.value))
        )
        result = await service.reason(scene)
        assert result.camera_angle is angle


# ---------------------------------------------------------------------------
# SceneReasoningService — Arabic scene
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_service_arabic_scene_returns_cinematic_prompt():
    """Provider returns valid JSON even for Arabic input (fixture controls output)."""
    scene = _make_ar_scene()
    ar_json = _valid_json(
        visual_description=(
            "Warm interior kitchen, Arabic mother preparing coffee in silence, "
            "soft morning light through latticed window, medium shot"
        ),
        environment="interior Arabic kitchen, morning",
        characters=["MOTHER"],
        mood="neutral",
    )
    service = SceneReasoningService(FakeProvider(ar_json))
    result = await service.reason(scene, style="cinematic")
    assert isinstance(result, CinematicPrompt)
    assert "kitchen" in result.visual_description.lower()


@pytest.mark.asyncio
async def test_service_arabic_scene_language_is_ar():
    """The scene passed to the service has language == 'ar'."""
    scene = _make_ar_scene()
    assert scene.language == "ar"
    service = SceneReasoningService(FakeProvider(_valid_json()))
    result = await service.reason(scene)
    # The CinematicPrompt output is always English; language tag lives on the Scene
    assert isinstance(result, CinematicPrompt)


@pytest.mark.asyncio
async def test_service_arabic_scene_visual_description_is_english():
    """Fixture enforces that visual_description is written in English."""
    scene = _make_ar_scene()
    ar_json = _valid_json(
        visual_description="Interior kitchen scene with warm sunlight, Arabic household"
    )
    service = SceneReasoningService(FakeProvider(ar_json))
    result = await service.reason(scene)
    # Simple heuristic: no Arabic Unicode in the visual description
    assert all(ord(c) < 0x0600 for c in result.visual_description)


# ---------------------------------------------------------------------------
# SceneReasoningService — style variants
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_service_sketch_style_returns_prompt():
    scene = _make_en_scene()
    service = SceneReasoningService(FakeProvider(_valid_json()))
    result = await service.reason(scene, style="sketch")
    assert isinstance(result, CinematicPrompt)


@pytest.mark.asyncio
async def test_service_anime_style_returns_prompt():
    scene = _make_en_scene()
    service = SceneReasoningService(FakeProvider(_valid_json()))
    result = await service.reason(scene, style="anime")
    assert isinstance(result, CinematicPrompt)


# ---------------------------------------------------------------------------
# SceneReasoningService — failure modes
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_service_non_json_response_raises_scene_reasoning_error():
    scene = _make_en_scene()
    service = SceneReasoningService(FakeProvider("This is not JSON at all."))
    with pytest.raises(SceneReasoningError) as exc_info:
        await service.reason(scene)
    assert "non-JSON" in str(exc_info.value)


@pytest.mark.asyncio
async def test_service_json_array_raises_scene_reasoning_error():
    """A JSON array is valid JSON but not a valid CinematicPrompt object."""
    scene = _make_en_scene()
    service = SceneReasoningService(FakeProvider(json.dumps([1, 2, 3])))
    with pytest.raises(SceneReasoningError) as exc_info:
        await service.reason(scene)
    assert "not an object" in str(exc_info.value)


@pytest.mark.asyncio
async def test_service_json_missing_required_field_raises():
    """JSON object that lacks a required field raises SceneReasoningError."""
    scene = _make_en_scene()
    incomplete = json.dumps({
        # visual_description is missing
        "shot_type": "wide",
        "camera_angle": "eye_level",
        "lighting": "soft",
        "mood": "neutral",
        "environment": "interior",
        "negative_prompt": "text",
    })
    service = SceneReasoningService(FakeProvider(incomplete))
    with pytest.raises(SceneReasoningError) as exc_info:
        await service.reason(scene)
    assert "Invalid structured output" in str(exc_info.value)


@pytest.mark.asyncio
async def test_service_invalid_shot_type_raises():
    scene = _make_en_scene()
    bad = _valid_json(shot_type="fisheye")
    service = SceneReasoningService(FakeProvider(bad))
    with pytest.raises(SceneReasoningError):
        await service.reason(scene)


@pytest.mark.asyncio
async def test_service_invalid_mood_raises():
    scene = _make_en_scene()
    bad = _valid_json(mood="melancholic")
    service = SceneReasoningService(FakeProvider(bad))
    with pytest.raises(SceneReasoningError):
        await service.reason(scene)


@pytest.mark.asyncio
async def test_service_invalid_camera_angle_raises():
    scene = _make_en_scene()
    bad = _valid_json(camera_angle="bird_eye")
    service = SceneReasoningService(FakeProvider(bad))
    with pytest.raises(SceneReasoningError):
        await service.reason(scene)


@pytest.mark.asyncio
async def test_service_provider_scene_reasoning_error_propagated():
    """SceneReasoningError raised by the provider reaches the caller unchanged."""
    scene = _make_en_scene()
    service = SceneReasoningService(FailingProvider("network timeout"))
    with pytest.raises(SceneReasoningError) as exc_info:
        await service.reason(scene)
    assert "network timeout" in str(exc_info.value)


@pytest.mark.asyncio
async def test_service_provider_unexpected_exception_propagated():
    """An unexpected RuntimeError from the provider is NOT swallowed."""
    scene = _make_en_scene()
    service = SceneReasoningService(ExplodingProvider())
    with pytest.raises(RuntimeError, match="unexpected SDK crash"):
        await service.reason(scene)


# ---------------------------------------------------------------------------
# SceneReasoningService — markdown fence stripping
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_service_strips_markdown_json_fence():
    """Provider wrapping JSON in ```json ... ``` is handled correctly."""
    scene = _make_en_scene()
    fenced = f"```json\n{_valid_json()}\n```"
    service = SceneReasoningService(FakeProvider(fenced))
    result = await service.reason(scene)
    assert isinstance(result, CinematicPrompt)


@pytest.mark.asyncio
async def test_service_strips_plain_markdown_fence():
    """Provider wrapping JSON in ``` ... ``` (no language) is handled."""
    scene = _make_en_scene()
    fenced = f"```\n{_valid_json()}\n```"
    service = SceneReasoningService(FakeProvider(fenced))
    result = await service.reason(scene)
    assert isinstance(result, CinematicPrompt)


@pytest.mark.asyncio
async def test_service_handles_leading_trailing_whitespace():
    scene = _make_en_scene()
    padded = f"\n\n  {_valid_json()}  \n\n"
    service = SceneReasoningService(FakeProvider(padded))
    result = await service.reason(scene)
    assert isinstance(result, CinematicPrompt)


# ---------------------------------------------------------------------------
# Prompt construction (_build_user_prompt)
# ---------------------------------------------------------------------------


def test_user_prompt_contains_scene_heading():
    scene = _make_en_scene(heading="EXT. DESERT - NIGHT")
    prompt = _build_user_prompt(scene, style="cinematic")
    assert "EXT. DESERT - NIGHT" in prompt


def test_user_prompt_contains_location():
    scene = _make_en_scene(location="ROOFTOP")
    prompt = _build_user_prompt(scene, style="cinematic")
    assert "ROOFTOP" in prompt


def test_user_prompt_contains_time_of_day():
    scene = _make_en_scene(time_of_day="NIGHT")
    prompt = _build_user_prompt(scene, style="cinematic")
    assert "NIGHT" in prompt


def test_user_prompt_contains_style():
    scene = _make_en_scene()
    prompt = _build_user_prompt(scene, style="anime")
    assert "anime" in prompt


def test_user_prompt_english_language_tag():
    scene = _make_en_scene()
    prompt = _build_user_prompt(scene, style="cinematic")
    assert "en" in prompt


def test_user_prompt_arabic_language_tag():
    scene = _make_ar_scene()
    prompt = _build_user_prompt(scene, style="cinematic")
    assert "ar" in prompt


def test_user_prompt_contains_characters():
    scene = _make_en_scene(characters=["ALICE", "BOB"])
    prompt = _build_user_prompt(scene, style="cinematic")
    assert "ALICE" in prompt
    assert "BOB" in prompt


def test_user_prompt_no_characters_shows_none():
    scene = _make_en_scene(characters=[])
    prompt = _build_user_prompt(scene, style="cinematic")
    assert "none" in prompt.lower()


def test_system_prompt_non_empty():
    """The module-level system prompt must be a non-empty string."""
    assert isinstance(_SYSTEM_PROMPT, str)
    assert len(_SYSTEM_PROMPT) > 50


def test_system_prompt_requires_json_response():
    """System prompt must instruct the model to respond with JSON."""
    assert "JSON" in _SYSTEM_PROMPT


def test_system_prompt_lists_all_shot_types():
    for shot in ShotType:
        assert shot.value in _SYSTEM_PROMPT


def test_system_prompt_lists_all_camera_angles():
    for angle in CameraAngle:
        assert angle.value in _SYSTEM_PROMPT


def test_system_prompt_mentions_arabic_handling():
    """System prompt must include instruction for Arabic input."""
    assert "Arabic" in _SYSTEM_PROMPT


# ---------------------------------------------------------------------------
# GraniteSceneReasoningProvider — configuration and non-blocking behaviour
# ---------------------------------------------------------------------------


def test_granite_provider_missing_granite_model_id_raises():
    """GraniteSceneReasoningProvider.__init__ must raise EnvironmentError
    when GRANITE_MODEL_ID is absent, enforcing that no default model ID
    is ever assumed."""
    import os
    from unittest.mock import patch
    from src.backend.services.scene_reasoning import GraniteSceneReasoningProvider

    with patch.dict(
        os.environ,
        {"WATSONX_API_KEY": "test-key", "WATSONX_PROJECT_ID": "test-project"},
        clear=True,
    ):
        with pytest.raises(EnvironmentError) as exc_info:
            GraniteSceneReasoningProvider()
    assert "GRANITE_MODEL_ID" in str(exc_info.value)


def test_granite_provider_missing_api_key_raises():
    """WATSONX_API_KEY is required — missing it raises EnvironmentError."""
    import os
    from unittest.mock import patch
    from src.backend.services.scene_reasoning import GraniteSceneReasoningProvider

    with patch.dict(
        os.environ,
        {"WATSONX_PROJECT_ID": "proj", "GRANITE_MODEL_ID": "ibm/granite-test"},
        clear=True,
    ):
        with pytest.raises(EnvironmentError):
            GraniteSceneReasoningProvider()


def test_granite_provider_missing_project_id_raises():
    """WATSONX_PROJECT_ID is required — missing it raises EnvironmentError."""
    import os
    from unittest.mock import patch
    from src.backend.services.scene_reasoning import GraniteSceneReasoningProvider

    with patch.dict(
        os.environ,
        {"WATSONX_API_KEY": "key", "GRANITE_MODEL_ID": "ibm/granite-test"},
        clear=True,
    ):
        with pytest.raises(EnvironmentError):
            GraniteSceneReasoningProvider()


@pytest.mark.asyncio
async def test_granite_provider_uses_asyncio_to_thread():
    """GraniteSceneReasoningProvider.generate() must call asyncio.to_thread()
    with the SDK client's synchronous generate method so that it never blocks
    the FastAPI event loop.

    Strategy: patch ``asyncio.to_thread`` inside the scene_reasoning module to
    an AsyncMock that returns the fake SDK response directly.  Assert that
    to_thread was called exactly once, that the first positional argument is the
    client's .generate method, and that the ``prompt`` keyword argument is
    present and non-empty.
    """
    import os
    from unittest.mock import AsyncMock, MagicMock, patch
    from src.backend.services.scene_reasoning import GraniteSceneReasoningProvider
    import src.backend.services.scene_reasoning as _sr_mod

    fake_sdk_response = {
        "results": [{"generated_text": "some text"}]
    }

    env = {
        "WATSONX_API_KEY": "test-key",
        "WATSONX_PROJECT_ID": "test-project",
        "GRANITE_MODEL_ID": "ibm/granite-test",
    }
    with patch.dict(os.environ, env, clear=True):
        provider = GraniteSceneReasoningProvider()

    # Replace the lazy client with a mock whose .generate() is synchronous
    mock_client = MagicMock()
    mock_client.generate.return_value = fake_sdk_response
    provider._client = mock_client

    # Patch asyncio.to_thread inside the module under test so we can assert
    # it is called with the right arguments, while still returning a value.
    mock_to_thread = AsyncMock(return_value=fake_sdk_response)
    with patch.object(_sr_mod, "asyncio") as mock_asyncio:
        mock_asyncio.to_thread = mock_to_thread

        # generate() will raise SceneReasoningError because fake_sdk_response
        # has only partial JSON — that is fine; we only care that to_thread
        # was called correctly before the response is further processed.
        try:
            await provider.generate("system prompt", "user prompt")
        except Exception:
            pass

    mock_to_thread.assert_awaited_once()
    call_args = mock_to_thread.call_args
    # First positional arg must be the client's .generate bound method
    assert call_args.args[0] is mock_client.generate
    # The prompt keyword argument must be the concatenated prompt string
    assert "prompt" in call_args.kwargs
    assert "system prompt" in call_args.kwargs["prompt"]
    assert "user prompt" in call_args.kwargs["prompt"]
