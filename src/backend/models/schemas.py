"""
Shared Pydantic models (request/response schemas) for CineForge AI Pro.
"""

from pydantic import BaseModel, Field


class SceneMetadata(BaseModel):
    """Metadata for a single scene extracted from a script."""

    index: int
    heading: str
    description: str
    characters: list[str] = Field(default_factory=list)
    location: str = ""
    time_of_day: str = ""
    mood: str = ""
    dialogue: list[str] = Field(default_factory=list)
    language: str = "en"


class ParsedScriptResponse(BaseModel):
    """API response for a fully parsed script."""

    script_id: str
    title: str
    language: str
    scene_count: int
    scenes: list[SceneMetadata]
    characters: list[str]
    locations: list[str]


class ErrorResponse(BaseModel):
    """Standard error response body."""

    error: str
    detail: str | None = None
