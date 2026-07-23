"""API contract tests for the storyboard generation endpoint."""

import base64
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from src.backend.main import app
from src.backend.routers import generate
from src.backend.services.image_generation import (
    GeneratedImage,
    ImageGenerationError,
)
from src.backend.services.script_parser import ParsedScript, Scene
from src.backend.services.storyboard_service import StoryboardGenerationResult


client = TestClient(app)

SCRIPT_ID = "test-storyboard-script"

SCENE = Scene(
    index=0,
    heading="INT. ROOM - DAY",
    description="A person walks into the room.",
    characters=[],
    location="ROOM",
    time_of_day="DAY",
    mood="neutral",
    dialogue=[],
    language="en",
)

SCRIPT = ParsedScript(
    title="Test Script",
    language="en",
    scene_count=1,
    scenes=[SCENE],
    characters=[],
    locations=["ROOM"],
)


def _payload(scene_index=0):
    return {
        "script_id": SCRIPT_ID,
        "scene_index": scene_index,
        "style": "cinematic",
        "language": "en",
    }


def test_unknown_script_returns_404(monkeypatch):
    monkeypatch.setattr(generate.script_store, "get", lambda _: None)

    response = client.post(
        "/api/generate/storyboard",
        json=_payload(),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Script not found."


def test_out_of_range_scene_returns_422(monkeypatch):
    monkeypatch.setattr(
        generate.script_store,
        "get",
        lambda _: SCRIPT,
    )

    response = client.post(
        "/api/generate/storyboard",
        json=_payload(scene_index=99),
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "Scene index is out of range."


def test_missing_configuration_returns_503(monkeypatch):
    monkeypatch.setattr(
        generate.script_store,
        "get",
        lambda _: SCRIPT,
    )

    def fail_to_build():
        raise EnvironmentError("missing credentials")

    monkeypatch.setattr(
        generate,
        "_build_storyboard_service",
        fail_to_build,
    )

    response = client.post(
        "/api/generate/storyboard",
        json=_payload(),
    )

    assert response.status_code == 503
    assert (
        response.json()["detail"]
        == "Storyboard generation service is not configured."
    )


def test_success_returns_generated_image(monkeypatch):
    monkeypatch.setattr(
        generate.script_store,
        "get",
        lambda _: SCRIPT,
    )

    image_bytes = b"\x89PNG\r\n\x1a\nfake-image-data"

    result = StoryboardGenerationResult(
        cinematic_prompt=None,
        generated_image=GeneratedImage(
            image_bytes=image_bytes,
            mime_type="image/png",
            provider_id="test-provider",
            model_id="test-model",
        ),
    )

    service = AsyncMock()
    service.generate.return_value = result

    monkeypatch.setattr(
        generate,
        "_build_storyboard_service",
        lambda: service,
    )

    response = client.post(
        "/api/generate/storyboard",
        json=_payload(),
    )

    assert response.status_code == 202

    body = response.json()

    assert body["scene_index"] == 0
    assert base64.b64decode(body["image_data_b64"]) == image_bytes
    assert body["mime_type"] == "image/png"
    assert body["provider_id"] == "test-provider"
    assert body["model_id"] == "test-model"
    assert body["watermarked"] is False
    assert body["style"] == "cinematic"
    assert isinstance(body["generation_time_ms"], int)

    service.generate.assert_awaited_once_with(
        SCENE,
        style="cinematic",
    )


def test_provider_failure_returns_502(monkeypatch):
    monkeypatch.setattr(
        generate.script_store,
        "get",
        lambda _: SCRIPT,
    )

    service = AsyncMock()
    service.generate.side_effect = ImageGenerationError(
        "provider failed"
    )

    monkeypatch.setattr(
        generate,
        "_build_storyboard_service",
        lambda: service,
    )

    response = client.post(
        "/api/generate/storyboard",
        json=_payload(),
    )

    assert response.status_code == 502
    assert (
        response.json()["detail"]
        == "Storyboard generation provider failed."
    )
