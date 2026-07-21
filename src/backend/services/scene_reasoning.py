"""
Scene Reasoning Service — Granite-powered cinematic prompt generation.

Architecture
------------
This module defines three layers with strict separation of concerns:

1. **Domain models** (``CinematicPrompt``, ``ShotType``, ``CameraAngle``,
   ``SceneReasoningError``) — pure Python, no AI SDK imports.

2. **Provider abstraction** (``SceneReasoningProvider`` ABC) — defines the
   contract that any reasoning backend must satisfy.  The router and service
   layer depend only on this interface, never on a concrete SDK.

3. **Concrete provider** (``GraniteSceneReasoningProvider``) — the only
   module that imports IBM SDK code.  Isolated here so tests can substitute
   a lightweight fake without loading watsonx credentials.

4. **Service** (``SceneReasoningService``) — orchestrates the provider call,
   builds the Granite prompt, validates the structured JSON response, and
   propagates failures explicitly.

Data flow
---------
``Scene`` (from ``script_parser``)
  → ``SceneReasoningService.reason(scene, style)``
    → ``SceneReasoningProvider.generate(system_prompt, user_prompt)`` → raw str
      → JSON parse → Pydantic validation
  → ``CinematicPrompt``

Supported scene languages: ``"en"`` and ``"ar"``.
All output (including ``visual_description``) is always in English so that a
downstream image-generation model never needs to handle bilingual input.

Environment variables
---------------------
``WATSONX_API_KEY``       — IBM watsonx.ai API key (required for Granite provider)
``WATSONX_PROJECT_ID``    — watsonx.ai project ID (required)
``WATSONX_URL``           — watsonx.ai endpoint URL (defaults to us-south)
``GRANITE_MODEL_ID``      — Granite model to use for reasoning (required; must be
                            a model ID verified as available in the target
                            watsonx.ai environment — do not invent model IDs)
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from abc import ABC, abstractmethod
from enum import Enum

from pydantic import BaseModel, Field, field_validator

from src.backend.services.script_parser import Scene

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Domain enumerations
# ---------------------------------------------------------------------------


class ShotType(str, Enum):
    """Standard cinematographic shot sizes.

    Values are lowercase strings so they can be embedded directly into
    image-generation prompts (e.g. ``f"{shot_type.value} shot"``).
    """

    WIDE = "wide"
    MEDIUM = "medium"
    CLOSE_UP = "close_up"
    EXTREME_CLOSE_UP = "extreme_close_up"
    AERIAL = "aerial"


class CameraAngle(str, Enum):
    """Standard cinematographic camera angle positions."""

    EYE_LEVEL = "eye_level"
    LOW_ANGLE = "low_angle"
    HIGH_ANGLE = "high_angle"
    DUTCH = "dutch"


# ---------------------------------------------------------------------------
# Domain error
# ---------------------------------------------------------------------------


class SceneReasoningError(Exception):
    """Raised when the reasoning provider fails to produce a valid response.

    Never raised for programming errors (those propagate as-is).
    Raised for:
    - SDK / network failures
    - Non-JSON provider output
    - JSON that does not match the ``CinematicPrompt`` schema
    """

    def __init__(self, message: str, *, cause: BaseException | None = None) -> None:
        super().__init__(message)
        self.cause = cause


# ---------------------------------------------------------------------------
# Domain model — CinematicPrompt
# ---------------------------------------------------------------------------


class CinematicPrompt(BaseModel):
    """Structured cinematic prompt produced by scene reasoning.

    This is the contract between the Granite reasoning layer and the
    downstream image-generation service.  Every field is validated by
    Pydantic before the object is returned to the caller.

    Fields
    ------
    visual_description
        Full English-language image-generation prompt capturing the scene's
        visual essence.  Suitable for passing directly to a text-to-image
        model.  Must be non-empty.

    shot_type
        Cinematographic shot size (wide, medium, close_up, etc.).

    camera_angle
        Camera position relative to the subject.

    lighting
        Lighting description (e.g. "golden hour backlit", "harsh neon",
        "soft diffused daylight").  Must be non-empty.

    mood
        Emotional tone of the scene, forwarded from the parsed scene or
        refined by reasoning.  Must be one of: neutral, romantic, tense,
        dark — matching the parser's mood vocabulary.

    environment
        Brief environment description (e.g. "interior bakery, dawn").
        Derived from the scene's heading and description.  Must be non-empty.

    characters
        List of character names visible in the frame.  May be empty if the
        scene has no characters.  Each entry must be non-empty when present.

    negative_prompt
        Elements to exclude from image generation (e.g. "text, watermarks,
        blurry, low quality").  Must be non-empty; a sensible default is
        always generated.
    """

    visual_description: str = Field(
        ...,
        min_length=1,
        description="Full English image-generation prompt for the scene.",
    )
    shot_type: ShotType = Field(
        ...,
        description="Cinematographic shot size.",
    )
    camera_angle: CameraAngle = Field(
        ...,
        description="Camera position relative to the subject.",
    )
    lighting: str = Field(
        ...,
        min_length=1,
        description="Lighting style description.",
    )
    mood: str = Field(
        ...,
        description="Emotional tone: neutral | romantic | tense | dark.",
    )
    environment: str = Field(
        ...,
        min_length=1,
        description="Brief environment description.",
    )
    characters: list[str] = Field(
        default_factory=list,
        description="Character names visible in the frame.",
    )
    negative_prompt: str = Field(
        ...,
        min_length=1,
        description="Elements to exclude from image generation.",
    )

    @field_validator("mood")
    @classmethod
    def mood_must_be_known(cls, v: str) -> str:
        allowed = {"neutral", "romantic", "tense", "dark"}
        normalised = v.strip().lower()
        if normalised not in allowed:
            raise ValueError(
                f"mood must be one of {sorted(allowed)!r}, got {v!r}."
            )
        return normalised

    @field_validator("characters", mode="before")
    @classmethod
    def characters_no_blank_entries(cls, v: object) -> list[str]:
        if not isinstance(v, list):
            raise ValueError("characters must be a list.")
        cleaned: list[str] = []
        for item in v:
            if not isinstance(item, str):
                raise ValueError("Each character entry must be a string.")
            stripped = item.strip()
            if stripped:
                cleaned.append(stripped)
        return cleaned


# ---------------------------------------------------------------------------
# Provider abstraction
# ---------------------------------------------------------------------------


class SceneReasoningProvider(ABC):
    """Abstract interface for scene-reasoning backends.

    Concrete implementations may call IBM Granite, a local model, or any
    other text-generation service.  The service layer and all tests interact
    only with this interface.

    Implementers must:
    - Accept a ``system_prompt`` (str) and ``user_prompt`` (str).
    - Return the model's raw text response as a ``str``.
    - Raise ``SceneReasoningError`` for any non-programming failure
      (network error, authentication failure, rate limit, etc.).
    - Never return an empty string; raise ``SceneReasoningError`` instead.
    """

    @abstractmethod
    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Call the backing text-generation model and return the raw response.

        Args:
            system_prompt: Role/task instruction for the model.
            user_prompt: The scene content to reason about.

        Returns:
            Raw text response from the model (expected to be JSON).

        Raises:
            SceneReasoningError: on any provider-level failure.
        """


# ---------------------------------------------------------------------------
# Granite provider (only module that imports ibm_watsonx_ai)
# ---------------------------------------------------------------------------


class GraniteSceneReasoningProvider(SceneReasoningProvider):
    """Scene-reasoning provider backed by IBM Granite via watsonx.ai.

    Reads configuration from environment variables at construction time.
    The SDK client is created lazily on the first ``generate()`` call so
    that importing this module never requires network access.

    The synchronous ``ModelInference.generate()`` SDK call is offloaded to a
    thread pool via ``asyncio.to_thread()`` so it never blocks the FastAPI
    event loop.

    Environment variables
    ---------------------
    WATSONX_API_KEY       Required.
    WATSONX_PROJECT_ID    Required.
    WATSONX_URL           Optional; defaults to us-south endpoint.
    GRANITE_MODEL_ID      Required; must be a verified model ID available in
                          the target watsonx.ai project (do not invent IDs).
    """

    def __init__(self) -> None:
        self._api_key: str = os.getenv("WATSONX_API_KEY", "")
        self._project_id: str = os.getenv("WATSONX_PROJECT_ID", "")
        self._url: str = os.getenv(
            "WATSONX_URL", "https://us-south.ml.cloud.ibm.com"
        )
        self._model_id: str = os.getenv("GRANITE_MODEL_ID", "")
        self._client: object | None = None  # initialised lazily

        if not self._api_key or not self._project_id or not self._model_id:
            raise EnvironmentError(
                "WATSONX_API_KEY, WATSONX_PROJECT_ID, and GRANITE_MODEL_ID "
                "must all be set in the environment. "
                "GRANITE_MODEL_ID must be a model ID verified as available in "
                "your watsonx.ai project. See .env.example for guidance."
            )

    def _get_client(self) -> object:
        """Lazily initialise the watsonx.ai model client."""
        if self._client is None:
            # Import deferred to isolate SDK dependency from module load
            from ibm_watsonx_ai import Credentials  # type: ignore[import-untyped]
            from ibm_watsonx_ai.foundation_models import ModelInference  # type: ignore[import-untyped]

            credentials = Credentials(
                api_key=self._api_key,
                url=self._url,
            )
            self._client = ModelInference(
                model_id=self._model_id,
                credentials=credentials,
                project_id=self._project_id,
                params={
                    "decoding_method": "greedy",
                    "max_new_tokens": 600,
                    "temperature": 0.0,
                },
            )
        return self._client

    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Call Granite via the watsonx.ai SDK and return the raw text.

        ``ModelInference.generate()`` is a synchronous blocking call in
        ``ibm-watsonx-ai`` 1.x.  It is offloaded to a thread pool via
        ``asyncio.to_thread()`` so the FastAPI event loop is never blocked.

        Raises:
            SceneReasoningError: if the SDK raises, or if the response is empty.
        """
        combined_prompt = f"{system_prompt}\n\n{user_prompt}"
        logger.debug(
            "GraniteSceneReasoningProvider: calling model_id=%s", self._model_id
        )
        try:
            client = self._get_client()
            # Offload the blocking synchronous SDK call to a thread pool so the
            # FastAPI event loop is not stalled during the network round-trip.
            response = await asyncio.to_thread(
                client.generate,  # type: ignore[union-attr]
                prompt=combined_prompt,
            )
        except SceneReasoningError:
            raise
        except Exception as exc:
            raise SceneReasoningError(
                f"Granite provider failed: {exc}", cause=exc
            ) from exc

        # Extract the generated text from the response dict
        try:
            raw_text: str = (
                response["results"][0]["generated_text"].strip()
            )
        except (KeyError, IndexError, TypeError) as exc:
            raise SceneReasoningError(
                f"Unexpected response structure from Granite: {response!r}",
                cause=exc,
            ) from exc

        if not raw_text:
            raise SceneReasoningError(
                "Granite provider returned an empty response."
            )

        return raw_text


# ---------------------------------------------------------------------------
# Prompt construction helpers
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """\
You are an expert film director and cinematographer specialising in visual \
storytelling. Given a screenplay scene, you reason about its visual potential \
and produce a precise, English-language prompt suitable for AI storyboard image \
generation.

You MUST respond with a single valid JSON object — no prose, no markdown fences, \
no additional keys. Use exactly these keys:

{
  "visual_description": "<rich English-language image-generation prompt>",
  "shot_type": "<wide|medium|close_up|extreme_close_up|aerial>",
  "camera_angle": "<eye_level|low_angle|high_angle|dutch>",
  "lighting": "<lighting description>",
  "mood": "<neutral|romantic|tense|dark>",
  "environment": "<brief environment description>",
  "characters": ["<character name>", ...],
  "negative_prompt": "<comma-separated list of elements to exclude>"
}

Rules:
- If the scene text is in Arabic, reason about it in Arabic but write ALL \
output values in English.
- The visual_description must be a single string at least 20 characters long \
and describe the scene cinematically.
- negative_prompt must always include at minimum: text, watermarks, blurry, \
low quality, distorted.
- mood must be exactly one of: neutral, romantic, tense, dark.\
"""


def _build_user_prompt(scene: Scene, style: str) -> str:
    """Construct the user-turn prompt from a ``Scene`` and a style preference."""
    char_list = ", ".join(scene.characters) if scene.characters else "none"
    return (
        f"Scene heading: {scene.heading}\n"
        f"Location: {scene.location or 'unspecified'}\n"
        f"Time of day: {scene.time_of_day or 'unspecified'}\n"
        f"Mood: {scene.mood or 'neutral'}\n"
        f"Characters: {char_list}\n"
        f"Scene description (may be in Arabic or English):\n{scene.description}\n"
        f"Requested visual style: {style}\n"
        f"Scene language: {scene.language}"
    )


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class SceneReasoningService:
    """Provider-agnostic service that converts a ``Scene`` into a
    ``CinematicPrompt``.

    The service is responsible for:
    - Building the structured prompt from scene metadata.
    - Delegating generation to the configured provider.
    - Parsing and validating the provider's JSON response.
    - Mapping all failure modes to ``SceneReasoningError``.

    The router (or any caller) should only depend on this class.

    Usage::

        provider = GraniteSceneReasoningProvider()
        service  = SceneReasoningService(provider)
        prompt   = await service.reason(scene, style="cinematic")

    For testing without network access, inject any ``SceneReasoningProvider``
    implementation that returns controlled JSON strings.
    """

    def __init__(self, provider: SceneReasoningProvider) -> None:
        self._provider = provider

    async def reason(self, scene: Scene, style: str = "cinematic") -> CinematicPrompt:
        """Reason about a scene and return a validated ``CinematicPrompt``.

        Args:
            scene: A ``Scene`` dataclass from ``script_parser``.
            style: Visual style hint (e.g. "cinematic", "sketch", "anime").

        Returns:
            A fully validated ``CinematicPrompt``.

        Raises:
            SceneReasoningError: on provider failure or invalid structured output.
        """
        user_prompt = _build_user_prompt(scene, style)

        logger.debug(
            "SceneReasoningService.reason: scene_index=%d language=%s style=%s",
            scene.index,
            scene.language,
            style,
        )

        raw_text = await self._provider.generate(_SYSTEM_PROMPT, user_prompt)

        # Strip optional markdown code fences that some models emit
        cleaned = raw_text.strip()
        if cleaned.startswith("```"):
            lines = cleaned.splitlines()
            # drop the opening fence line and any closing fence line
            inner = [
                ln for ln in lines[1:]
                if not ln.strip().startswith("```")
            ]
            cleaned = "\n".join(inner).strip()

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise SceneReasoningError(
                f"Provider returned non-JSON output. "
                f"Parse error: {exc}. "
                f"Raw response (first 200 chars): {cleaned[:200]!r}",
                cause=exc,
            ) from exc

        if not isinstance(data, dict):
            raise SceneReasoningError(
                f"Provider returned JSON but not an object. Got: {type(data).__name__}."
            )

        try:
            prompt = CinematicPrompt(**data)
        except Exception as exc:
            raise SceneReasoningError(
                f"Invalid structured output from provider: {exc}",
                cause=exc,
            ) from exc

        return prompt
