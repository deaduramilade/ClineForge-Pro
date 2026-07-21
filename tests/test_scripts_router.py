"""
API integration tests for the scripts router.

  POST /api/scripts/upload  — parse-on-upload workflow
  GET  /api/scripts/{id}    — retrieve parsed metadata

Tests use FastAPI's synchronous TestClient mounted directly from the scripts
router, following the same pattern as test_budget_router.py.

Each test calls ``script_store.clear()`` during setup to ensure full isolation
between tests regardless of execution order.  The ``clear()`` helper is
intentionally provided for test use only.
"""

import io

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

# conftest.py inserts src/backend onto sys.path.
import services.script_store as script_store
from routers.scripts import router as scripts_router

# ---------------------------------------------------------------------------
# Test application
# ---------------------------------------------------------------------------

_app = FastAPI()
_app.include_router(scripts_router, prefix="/api/scripts")
_client = TestClient(_app, raise_server_exceptions=True)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

# Minimal multi-scene English screenplay — enough for the parser to find
# 3 scene headings, characters, and locations.
_EN_SCRIPT = (
    "INT. BAKERY - DAY\n\n"
    "The smell of fresh bread fills the air.\n\n"
    "BAKER\nGood morning.\n\n"
    "EXT. STREET - NIGHT\n\n"
    "Alice walks home alone.\n\n"
    "ALICE\nSomething feels wrong.\n\n"
    "INT. APARTMENT - CONTINUOUS\n\n"
    "The door creaks open.\n"
)
_EN_BYTES = _EN_SCRIPT.encode("utf-8")


def _upload(content: bytes, filename: str = "script.txt",
            content_type: str = "text/plain"):
    """POST /api/scripts/upload with the given bytes."""
    return _client.post(
        "/api/scripts/upload",
        files={"file": (filename, io.BytesIO(content), content_type)},
    )


@pytest.fixture(autouse=True)
def _clear_store():
    """Wipe the ephemeral store before every test."""
    script_store.clear()
    yield
    script_store.clear()


# ---------------------------------------------------------------------------
# Upload — success paths
# ---------------------------------------------------------------------------


def test_upload_returns_202():
    resp = _upload(_EN_BYTES)
    assert resp.status_code == 202


def test_upload_response_fields_present():
    body = _upload(_EN_BYTES).json()
    assert "script_id" in body
    assert "filename" in body
    assert "size_bytes" in body
    assert "message" in body
    assert "title" in body
    assert "language" in body
    assert "scene_count" in body


def test_upload_produces_real_script_id():
    body = _upload(_EN_BYTES).json()
    assert body["script_id"] != "placeholder-script-id"
    assert len(body["script_id"]) == 16  # SHA-256 prefix length


def test_upload_reports_correct_language():
    body = _upload(_EN_BYTES).json()
    assert body["language"] == "en"


def test_upload_reports_scene_count():
    body = _upload(_EN_BYTES).json()
    assert body["scene_count"] == 3


def test_upload_idempotent():
    """Uploading the same bytes twice returns the same script_id, no error."""
    first = _upload(_EN_BYTES).json()
    second = _upload(_EN_BYTES).json()
    assert first["script_id"] == second["script_id"]
    assert second["message"] == "Script already parsed; returning cached result."


def test_upload_deterministic_script_id():
    """Same bytes always produce the same script_id."""
    id1 = _upload(_EN_BYTES).json()["script_id"]
    script_store.clear()
    id2 = _upload(_EN_BYTES).json()["script_id"]
    assert id1 == id2


# ---------------------------------------------------------------------------
# Upload — rejection paths
# ---------------------------------------------------------------------------


def test_upload_unsupported_mime_returns_415():
    resp = _upload(_EN_BYTES, filename="photo.png", content_type="image/png")
    assert resp.status_code == 415


def test_upload_empty_file_returns_422():
    resp = _upload(b"", filename="empty.txt")
    assert resp.status_code == 422


def test_upload_unsupported_extension_returns_422():
    """Parser rejects .xyz extension → 422."""
    resp = _upload(b"some data", filename="script.xyz")
    assert resp.status_code == 422


def test_upload_size_limit_enforced():
    # Build content just over 50 MB.
    big = b"a" * (50 * 1024 * 1024 + 1)
    resp = _upload(big)
    assert resp.status_code == 413


# ---------------------------------------------------------------------------
# GET — success paths
# ---------------------------------------------------------------------------


def test_get_script_after_upload_returns_200():
    script_id = _upload(_EN_BYTES).json()["script_id"]
    resp = _client.get(f"/api/scripts/{script_id}")
    assert resp.status_code == 200


def test_get_script_response_shape():
    script_id = _upload(_EN_BYTES).json()["script_id"]
    body = _client.get(f"/api/scripts/{script_id}").json()
    assert body["script_id"] == script_id
    assert "title" in body
    assert "language" in body
    assert "scene_count" in body
    assert "scenes" in body
    assert "characters" in body
    assert "locations" in body


def test_get_script_has_scenes():
    script_id = _upload(_EN_BYTES).json()["script_id"]
    body = _client.get(f"/api/scripts/{script_id}").json()
    assert body["scene_count"] == 3
    assert len(body["scenes"]) == 3


def test_get_script_has_characters():
    script_id = _upload(_EN_BYTES).json()["script_id"]
    body = _client.get(f"/api/scripts/{script_id}").json()
    assert "BAKER" in body["characters"]
    assert "ALICE" in body["characters"]


def test_get_script_has_locations():
    script_id = _upload(_EN_BYTES).json()["script_id"]
    body = _client.get(f"/api/scripts/{script_id}").json()
    assert "BAKERY" in body["locations"]
    assert "STREET" in body["locations"]
    assert "APARTMENT" in body["locations"]


def test_get_scene_metadata_fields():
    """Every scene in the response exposes all expected metadata fields."""
    script_id = _upload(_EN_BYTES).json()["script_id"]
    scenes = _client.get(f"/api/scripts/{script_id}").json()["scenes"]
    for scene in scenes:
        assert "index" in scene
        assert "heading" in scene
        assert "description" in scene
        assert "characters" in scene
        assert "location" in scene
        assert "time_of_day" in scene
        assert "mood" in scene
        assert "dialogue" in scene
        assert "language" in scene


# ---------------------------------------------------------------------------
# GET — rejection paths
# ---------------------------------------------------------------------------


def test_get_unknown_script_id_returns_404():
    resp = _client.get("/api/scripts/nonexistent-id")
    assert resp.status_code == 404


def test_get_returns_404_before_upload():
    """Deterministic script_id for our fixture, but store is empty → 404."""
    import hashlib
    sid = hashlib.sha256(_EN_BYTES).hexdigest()[:16]
    resp = _client.get(f"/api/scripts/{sid}")
    assert resp.status_code == 404
