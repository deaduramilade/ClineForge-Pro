"""
CineForge AI Pro — FastAPI Backend

Entry point for the application. Configures middleware, CORS, and mounts all routers.
"""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import animatic, budget, generate, health, scripts

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "info").upper(),
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown logic."""
    logger.info("CineForge AI Pro backend starting up…")
    yield
    logger.info("CineForge AI Pro backend shutting down.")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    allowed_origins = [
        origin.strip()
        for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
    ]

    app = FastAPI(
        title="CineForge AI Pro API",
        description=(
            "Secure multimodal AI pipeline: Arabic & English scripts → "
            "storyboards, animatics, and budget estimates via IBM Granite."
        ),
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )

    # Mount routers
    app.include_router(health.router, prefix="/api/health", tags=["health"])
    app.include_router(scripts.router, prefix="/api/scripts", tags=["scripts"])
    app.include_router(generate.router, prefix="/api/generate", tags=["generate"])
    app.include_router(animatic.router, prefix="/api/animatic", tags=["animatic"])
    app.include_router(budget.router, prefix="/api/budget", tags=["budget"])

    return app


app = create_app()
