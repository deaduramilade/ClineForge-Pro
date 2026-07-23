"""Application service for storyboard generation."""

from dataclasses import dataclass

from src.backend.services.image_generation import (
    GeneratedImage,
    ImageGenerationService,
)
from src.backend.services.scene_reasoning import (
    CinematicPrompt,
    SceneReasoningService,
)
from src.backend.services.script_parser import Scene


@dataclass(frozen=True)
class StoryboardGenerationResult:
    """Result produced by the storyboard generation pipeline."""

    cinematic_prompt: CinematicPrompt
    generated_image: GeneratedImage


class StoryboardGenerationService:
    """Coordinate scene reasoning and image generation."""

    def __init__(
        self,
        reasoning_service: SceneReasoningService,
        image_service: ImageGenerationService,
    ) -> None:
        self._reasoning_service = reasoning_service
        self._image_service = image_service

    async def generate(
        self,
        scene: Scene,
        style: str = "cinematic",
    ) -> StoryboardGenerationResult:
        cinematic_prompt = await self._reasoning_service.reason(
            scene,
            style=style,
        )

        generated_image = await self._image_service.generate(
            cinematic_prompt,
        )

        return StoryboardGenerationResult(
            cinematic_prompt=cinematic_prompt,
            generated_image=generated_image,
        )
