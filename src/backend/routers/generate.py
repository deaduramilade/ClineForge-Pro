"""Generate router — storyboard and audio generation endpoints."""

import base64
import time

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from src.backend.services import script_store
from src.backend.services.huggingface_image_provider import (
    HuggingFaceImageGenerationProvider,
)
from src.backend.services.huggingface_scene_reasoning_provider import (
    HuggingFaceSceneReasoningProvider,
)
from src.backend.services.image_generation import (
    ImageGenerationError,
    ImageGenerationService,
)
from src.backend.services.scene_reasoning import (
    SceneReasoningError,
    SceneReasoningService,
)
from src.backend.services.storyboard_service import StoryboardGenerationService

router = APIRouter(tags=["generate"])


class StoryboardRequest(BaseModel):
    script_id: str = Field(
        ...,
        description="ID of a previously uploaded and parsed script",
    )
    scene_index: int = Field(
        ...,
        ge=0,
        description="Zero-based index of the scene to generate",
    )
    style: str = Field(
        default="cinematic",
        description="Visual style for the storyboard frame",
    )
    language: str = Field(
        default="en",
        description="Language of the scene description: 'en' or 'ar'",
    )


class StoryboardResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    scene_index: int
    image_data_b64: str
    mime_type: str
    provider_id: str
    model_id: str
    watermarked: bool
    style: str
    generation_time_ms: int


class AudioRequest(BaseModel):
    prompt: str = Field(
        ...,
        description="Text description of the audio or soundscape to generate",
    )


class AudioResponse(BaseModel):
    audio_url: str
    generation_time_ms: int


def _build_storyboard_service() -> StoryboardGenerationService:
    """Build the storyboard pipeline lazily from environment configuration."""
    reasoning_provider = HuggingFaceSceneReasoningProvider()
    reasoning_service = SceneReasoningService(reasoning_provider)

    image_provider = HuggingFaceImageGenerationProvider()
    image_service = ImageGenerationService(image_provider)

    return StoryboardGenerationService(
        reasoning_service=reasoning_service,
        image_service=image_service,
    )


@router.post(
    "/storyboard",
    response_model=StoryboardResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Generate a storyboard frame for a scene",
)
async def generate_storyboard(
    request: StoryboardRequest,
) -> StoryboardResponse:
    """Generate a storyboard frame from a previously parsed script scene."""
    start_time = time.perf_counter()

    parsed_script = script_store.get(request.script_id)

    if parsed_script is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Script not found.",
        )

    if request.scene_index >= len(parsed_script.scenes):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Scene index is out of range.",
        )

    scene = parsed_script.scenes[request.scene_index]

    try:
        service = _build_storyboard_service()
        result = await service.generate(
            scene,
            style=request.style,
        )
    except EnvironmentError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Storyboard generation service is not configured.",
        ) from exc
    except (SceneReasoningError, ImageGenerationError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Storyboard generation provider failed.",
        ) from exc

    generated_image = result.generated_image
    generation_time = int((time.perf_counter() - start_time) * 1000)

    return StoryboardResponse(
        scene_index=request.scene_index,
        image_data_b64=base64.b64encode(
            generated_image.image_bytes
        ).decode("ascii"),
        mime_type=generated_image.mime_type,
        provider_id=generated_image.provider_id,
        model_id=generated_image.model_id,
        watermarked=False,
        style=request.style,
        generation_time_ms=generation_time,
    )


@router.post(
    "/audio",
    response_model=AudioResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Generate background audio or soundscape",
)
async def generate_audio(request: AudioRequest) -> AudioResponse:
    """Generate an audio asset. Currently a development stub."""
    start_time = time.perf_counter()

    audio_url = "https://example.com/mock-audio-file.mp3"

    generation_time = int((time.perf_counter() - start_time) * 1000)

    return AudioResponse(
        audio_url=audio_url,
        generation_time_ms=generation_time,
    )
