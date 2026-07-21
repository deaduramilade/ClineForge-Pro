"""
End-to-end workflow tests for CineForge AI Pro.

All tests run against the *real* application imported from
``src.backend.main:app`` — identical to the production entry point used by:

    python -m uvicorn src.backend.main:app

No isolated mini-app is constructed here.  Tests exercise the complete chain:

    POST /api/scripts/upload
    → ephemeral store (script_store)
    → GET /api/scripts/{script_id}
    → POST /api/budget/estimate (store-lookup mode: no scene_count supplied)
    → budget response

Covered cases
-------------
1. test_e2e_full_workflow                         — happy path, full chain
2. test_e2e_budget_unknown_script_id              — 404 when script not in store
3. test_e2e_upload_then_budget_idempotent         — idempotent upload + budget
4. test_e2e_upload_rejected_mime_does_not_pollute_store — 415 leaves store empty
"""

import hashlib
import io

import pytest
from fastapi.testclient import TestClient

import src.backend.services.script_store as script_store
from src.backend.main import app

# ---------------------------------------------------------------------------
# Test client — real production app
# ---------------------------------------------------------------------------

client = TestClient(app, raise_server_exceptions=True)

# ---------------------------------------------------------------------------
# Shared script fixture content
# ---------------------------------------------------------------------------

# Minimal 3-scene English screenplay: 3 scenes, 2 characters, 3 locations.
_SCRIPT_TEXT = (
    "INT. BAKERY - DAY\n\n"
    "The smell of fresh bread fills the air.\n\n"
    "BAKER\nGood morning.\n\n"
    "EXT. STREET - NIGHT\n\n"
    "Alice walks home alone.\n\n"
    "ALICE\nSomething feels wrong.\n\n"
    "INT. APARTMENT - CONTINUOUS\n\n"
    "The door creaks open.\n"
)
_SCRIPT_BYTES = _SCRIPT_TEXT.encode("utf-8")

# Deterministic script_id for the fixture above (16-char SHA-256 prefix).
_EXPECTED_SCRIPT_ID = hashlib.sha256(_SCRIPT_BYTES).hexdigest()[:16]

# Standard line-item categories produced by BudgetEstimator.
_EXPECTED_CATEGORIES = {"crew", "equipment", "locations", "cast", "post_production", "contingency"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _upload(content: bytes = _SCRIPT_BYTES,
            filename: str = "script.txt",
            content_type: str = "text/plain"):
    """POST /api/scripts/upload and return the Response."""
    return client.post(
        "/api/scripts/upload",
        files={"file": (filename, io.BytesIO(content), content_type)},
    )


def _get_script(script_id: str):
    """GET /api/scripts/{script_id} and return the Response."""
    return client.get(f"/api/scripts/{script_id}")


def _estimate(payload: dict):
    """POST /api/budget/estimate and return the Response."""
    return client.post("/api/budget/estimate", json=payload)


# ---------------------------------------------------------------------------
# Autouse fixture — isolate every test from store side-effects
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _clear_store():
    """Wipe the ephemeral store before and after every test."""
    script_store.clear()
    yield
    script_store.clear()


# ---------------------------------------------------------------------------
# 1. Happy-path full chain
# ---------------------------------------------------------------------------


def test_e2e_full_workflow():
    """
    Complete workflow: upload → retrieve → budget (store-lookup mode).

    Assertions:
    - Upload returns 202 with a 16-char script_id.
    - Retrieve returns 200 with correct scene, character, and location counts.
    - Budget estimate returns 202 with valid financial fields.
    - Line-item sum equals total_estimated_cost (invariant).
    - All six standard categories are present.
    """
    # --- Step 1: upload ---
    upload_resp = _upload()
    assert upload_resp.status_code == 202, f"Upload failed: {upload_resp.json()}"
    upload_body = upload_resp.json()
    script_id = upload_body["script_id"]
    assert len(script_id) == 16
    assert script_id == _EXPECTED_SCRIPT_ID
    assert upload_body["scene_count"] == 3

    # --- Step 2: retrieve ---
    get_resp = _get_script(script_id)
    assert get_resp.status_code == 200, f"Retrieve failed: {get_resp.json()}"
    get_body = get_resp.json()
    assert get_body["script_id"] == script_id
    assert get_body["scene_count"] == 3
    assert len(get_body["scenes"]) == 3
    assert "BAKER" in get_body["characters"]
    assert "ALICE" in get_body["characters"]
    assert "BAKERY" in get_body["locations"]
    assert "STREET" in get_body["locations"]
    assert "APARTMENT" in get_body["locations"]

    # --- Step 3: budget estimate (store-lookup mode — no scene_count) ---
    budget_resp = _estimate({
        "script_id": script_id,
        "currency": "USD",
        "region": "international",
    })
    assert budget_resp.status_code == 202, f"Budget failed: {budget_resp.json()}"
    budget_body = budget_resp.json()

    assert budget_body["script_id"] == script_id
    assert budget_body["currency"] == "USD"
    assert budget_body["region"] == "international"
    assert budget_body["estimated_shoot_days"] >= 1
    assert budget_body["total_estimated_cost"] > 0.0
    assert len(budget_body["line_items"]) == 6
    assert {item["category"] for item in budget_body["line_items"]} == _EXPECTED_CATEGORIES

    # Line-item sum invariant.
    item_sum = sum(item["estimated_cost"] for item in budget_body["line_items"])
    assert budget_body["total_estimated_cost"] == pytest.approx(item_sum, abs=1e-6)


# ---------------------------------------------------------------------------
# 2. Budget request with unknown script_id returns 404
# ---------------------------------------------------------------------------


def test_e2e_budget_unknown_script_id():
    """
    POST /api/budget/estimate in store-lookup mode (no scene_count) when
    the script_id does not exist in the store must return HTTP 404 with a
    non-empty detail message.

    The store is empty (cleared by the autouse fixture), so no prior upload
    is needed.
    """
    resp = _estimate({
        "script_id": "no-such-script-id",
        "currency": "USD",
        "region": "gulf",
    })
    assert resp.status_code == 404
    body = resp.json()
    assert "detail" in body
    assert body["detail"]  # must be non-empty


# ---------------------------------------------------------------------------
# 3. Idempotent upload + budget
# ---------------------------------------------------------------------------


def test_e2e_upload_then_budget_idempotent():
    """
    Uploading the same bytes twice is idempotent (same script_id, cached
    message on the second upload).  A budget estimate requested after the
    second upload must still succeed with HTTP 202.
    """
    first_resp = _upload()
    assert first_resp.status_code == 202
    first_id = first_resp.json()["script_id"]

    second_resp = _upload()
    assert second_resp.status_code == 202
    second_body = second_resp.json()
    assert second_body["script_id"] == first_id
    assert second_body["message"] == "Script already parsed; returning cached result."

    # Budget estimate after the idempotent upload must still work.
    budget_resp = _estimate({
        "script_id": first_id,
        "currency": "SAR",
        "region": "gulf",
    })
    assert budget_resp.status_code == 202
    budget_body = budget_resp.json()
    assert budget_body["script_id"] == first_id
    assert budget_body["currency"] == "SAR"
    assert budget_body["total_estimated_cost"] > 0.0


# ---------------------------------------------------------------------------
# 4. Rejected MIME upload does not pollute the store
# ---------------------------------------------------------------------------


def test_e2e_upload_rejected_mime_does_not_pollute_store():
    """
    A rejected upload (415 Unsupported Media Type) must not write anything to
    the ephemeral store.  A subsequent budget estimate using the would-be
    script_id must return 404, not 202.
    """
    # Attempt to upload a PNG — must be rejected.
    reject_resp = _upload(
        content=_SCRIPT_BYTES,
        filename="photo.png",
        content_type="image/png",
    )
    assert reject_resp.status_code == 415

    # The would-be script_id (deterministic from content) must not be in store.
    assert not script_store.exists(_EXPECTED_SCRIPT_ID)

    # Budget request using that id must return 404.
    budget_resp = _estimate({
        "script_id": _EXPECTED_SCRIPT_ID,
        "currency": "USD",
        "region": "international",
    })
    assert budget_resp.status_code == 404
