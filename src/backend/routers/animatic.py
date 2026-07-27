"""Animatic router — motion animatic export pipeline."""

import base64

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from src.backend.services import frame_store
from src.backend.services.animatic import AnimaticError, AnimaticFrame, AnimaticService

router = APIRouter()

_animatic_service = AnimaticService()


class AnimaticRequest(BaseModel):
    script_id: str = Field(..., description="ID of a previously generated storyboard")
    frame_duration_ms: int = Field(
        default=2000,
        ge=500,
        le=10000,
        description="Duration each frame is displayed (milliseconds)",
    )
    format: str = Field(
        default="mp4",
        description=(
            "Output format: 'mp4' (requires ffmpeg installed on the backend "
            "host) or 'gif' (works everywhere, no system dependency)"
        ),
    )


class AnimaticResponse(BaseModel):
    script_id: str
    export_url: str
    format: str
    duration_seconds: float
    frame_count: int


@router.post(
    "/export",
    response_model=AnimaticResponse,
    status_code=status.HTTP_200_OK,
    summary="Export motion animatic for a script",
)
async def export_animatic(request: AnimaticRequest) -> AnimaticResponse:
    """
    Generate a motion animatic (hard cuts only — see AnimaticService
    docstring for the transitions gap) from previously-generated,
    watermarked storyboard frames.

    Requires at least one successful ``POST /api/generate/storyboard``
    call for this ``script_id`` first.
    """
    stored_frames = frame_store.get_frames(request.script_id)
    if not stored_frames:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No storyboard frames found for script '{request.script_id}'. "
            "Generate at least one frame first via POST /api/generate/storyboard.",
        )

    frames = [
        AnimaticFrame(
            scene_index=f.scene_index,
            image_bytes=f.image_bytes,
            duration_ms=request.frame_duration_ms,
        )
        for f in stored_frames
    ]

    try:
        result = await _animatic_service.export(
            request.script_id, frames, output_format=request.format
        )
    except AnimaticError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    mime = "image/gif" if result.format == "gif" else "video/mp4"
    export_url = f"data:{mime};base64," + base64.b64encode(result.file_bytes).decode("ascii")

    return AnimaticResponse(
        script_id=result.script_id,
        export_url=export_url,
        format=result.format,
        duration_seconds=result.duration_seconds,
        frame_count=result.frame_count,
    )
