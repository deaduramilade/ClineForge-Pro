"""Health check router — system status endpoint."""

import platform
import sys
from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str
    python_version: str
    platform: str


@router.get("", response_model=HealthResponse, summary="Health check")
async def health_check() -> HealthResponse:
    """Return the current health status of the API."""
    return HealthResponse(
        status="ok",
        timestamp=datetime.now(timezone.utc).isoformat(),
        version="0.1.0",
        python_version=sys.version,
        platform=platform.system(),
    )
