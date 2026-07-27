"""
End-to-end integration test: storyboard generation (mocked provider,
real watermarking + frame storage) -> animatic export (real GIF/MP4
assembly).

Mocks only the external HuggingFace call (same pattern as
test_storyboard_endpoint.py) — everything downstream of that (watermark
embedding, frame_store, AnimaticService) is real.
"""

import shutil
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

import src.backend.services.frame_store as frame_store
from src.backend.main import app
from src.backend.routers import generate
from src.backend.services.image_generation import GeneratedImage
from src.backend.services.script_parser import ParsedScript, Scene
from src.backend.services.storyboard_service import StoryboardGenerationResult

client = TestClient(app)

_HAS_FFMPEG = shutil.which("ffmpeg") is not None

SCRIPT_ID = "test-animatic-integration-script"

SCENES = [
    Scene(
        index=0,
        heading="INT. BAKERY - DAWN",
        description="Mira kneads dough alone.",
        characters=["Mira"],
        location="BAKERY",
        time_of_day="DAWN",
        mood="neutral",
        dialogue=[],
        language="en",
    ),
    Scene(
        index=1,
        heading="EXT. STREET - NIGHT",
        description="Karim runs through the rain.",
        characters=["Karim"],
        location="STREET",
        time_of_day="NIGHT",
        mood="tense",
        dialogue=[],
        language="en",
    ),
]

SCRIPT = ParsedScript(
    title="Animatic Integration Test",
    language="en",
    scene_count=2,
    scenes=SCENES,
    characters=["Mira", "Karim"],
    locations=["BAKERY", "STREET"],
)


def _mock_generated_image(scene_index: int) -> GeneratedImage:
    import io

    from PIL import Image

    img = Image.new("RGB", (32, 32), (10 + scene_index * 50, 20, 30))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return GeneratedImage(
        image_bytes=buf.getvalue(),
        mime_type="image/png",
        provider_id="test-provider",
        model_id="test-model",
    )


@pytest.fixture(autouse=True)
def _clean_frame_store():
    frame_store.clear()
    yield
    frame_store.clear()


def _generate_frame(monkeypatch, scene_index: int):
    monkeypatch.setattr(generate.script_store, "get", lambda _: SCRIPT)

    service = AsyncMock()
    service.generate.return_value = StoryboardGenerationResult(
        cinematic_prompt=None,
        generated_image=_mock_generated_image(scene_index),
    )
    monkeypatch.setattr(generate, "_build_storyboard_service", lambda: service)

    return client.post(
        "/api/generate/storyboard",
        json={"script_id": SCRIPT_ID, "scene_index": scene_index, "style": "cinematic", "language": "en"},
    )


def test_storyboard_generation_watermarks_and_stores_frame(monkeypatch):
    assert not frame_store.has_frames(SCRIPT_ID)

    resp = _generate_frame(monkeypatch, scene_index=0)

    assert resp.status_code == 202
    assert resp.json()["watermarked"] is True
    assert frame_store.has_frames(SCRIPT_ID)
    stored = frame_store.get_frames(SCRIPT_ID)
    assert len(stored) == 1
    assert stored[0].watermarked is True


def test_frame_count_endpoint_reflects_generated_frames(monkeypatch):
    _generate_frame(monkeypatch, scene_index=0)
    _generate_frame(monkeypatch, scene_index=1)

    resp = client.get(f"/api/generate/frames/{SCRIPT_ID}")

    assert resp.status_code == 200
    assert resp.json() == {"script_id": SCRIPT_ID, "frame_count": 2}


def test_animatic_export_404s_with_no_frames_generated():
    resp = client.post("/api/animatic/export", json={"script_id": "never-generated"})

    assert resp.status_code == 404


def test_animatic_export_gif_after_generating_frames(monkeypatch):
    _generate_frame(monkeypatch, scene_index=0)
    _generate_frame(monkeypatch, scene_index=1)

    resp = client.post(
        "/api/animatic/export",
        json={"script_id": SCRIPT_ID, "format": "gif", "frame_duration_ms": 1500},
    )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["format"] == "gif"
    assert body["frame_count"] == 2
    assert body["duration_seconds"] == pytest.approx(3.0)
    assert body["export_url"].startswith("data:image/gif;base64,")


@pytest.mark.skipif(not _HAS_FFMPEG, reason="ffmpeg not installed on this host")
def test_animatic_export_mp4_after_generating_frames(monkeypatch):
    _generate_frame(monkeypatch, scene_index=0)

    resp = client.post(
        "/api/animatic/export",
        json={"script_id": SCRIPT_ID, "format": "mp4"},
    )

    assert resp.status_code == 200, resp.text
    assert resp.json()["export_url"].startswith("data:video/mp4;base64,")
