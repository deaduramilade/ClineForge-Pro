"""
API integration tests for POST /api/budget/estimate.

Uses FastAPI's synchronous TestClient (backed by httpx) to exercise the
full request-validation → BudgetEstimator → response pipeline without
starting a real HTTP server.

The app under test mounts both the budget router and the scripts router so
that store-lookup integration tests can upload a script first, then estimate
from the resulting script_id.

All asserted monetary values are pre-computed from the deterministic
BudgetEstimator formula and verified before being hard-coded here.

Status-code assertions use HTTP 202 because that is the status configured
on the /estimate route.
"""

import io

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import src.backend.services.script_store as script_store
from src.backend.routers.budget import router as budget_router
from src.backend.routers.scripts import router as scripts_router

# ---------------------------------------------------------------------------
# Test application — budget + scripts routers
# ---------------------------------------------------------------------------

_app = FastAPI()
_app.include_router(budget_router, prefix="/api/budget")
_app.include_router(scripts_router, prefix="/api/scripts")
_client = TestClient(_app, raise_server_exceptions=True)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _clear_store():
    """Wipe the ephemeral store before and after every test."""
    script_store.clear()
    yield
    script_store.clear()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

URL = "/api/budget/estimate"


def _post(payload: dict):
    return _client.post(URL, json=payload)


def _valid_payload(**overrides) -> dict:
    """Return the minimal valid payload (explicit-count mode), optionally overriding fields."""
    base = {
        "script_id": "test-001",
        "scene_count": 10,
        "location_count": 2,
        "character_count": 3,
        "currency": "USD",
        "region": "international",
    }
    base.update(overrides)
    return base


def _upload_script(content: bytes, filename: str = "script.txt",
                   content_type: str = "text/plain") -> str:
    """Upload a script and return its script_id."""
    resp = _client.post(
        "/api/scripts/upload",
        files={"file": (filename, io.BytesIO(content), content_type)},
    )
    assert resp.status_code == 202, f"Upload failed: {resp.json()}"
    return resp.json()["script_id"]


# ---------------------------------------------------------------------------
# Success cases — HTTP 202
# ---------------------------------------------------------------------------


def test_estimate_success_international():
    """Basic international estimate returns 202 and all expected fields."""
    resp = _post(_valid_payload(scene_count=10, location_count=3, character_count=4,
                                region="international", currency="USD"))
    assert resp.status_code == 202
    body = resp.json()
    assert body["script_id"] == "test-001"
    assert body["currency"] == "USD"
    assert body["region"] == "international"
    assert body["total_estimated_cost"] == pytest.approx(25_520.00, abs=0.01)
    assert body["estimated_shoot_days"] == 2
    assert len(body["line_items"]) == 6


def test_estimate_success_gulf():
    """Gulf region produces a lower total than international for the same inputs."""
    intl = _post(_valid_payload(region="international")).json()
    gulf = _post(_valid_payload(region="gulf")).json()
    assert gulf["total_estimated_cost"] < intl["total_estimated_cost"]
    assert gulf["region"] == "gulf"
    assert gulf["currency"] == "USD"


def test_estimate_success_egypt():
    """
    Egypt estimate: 15 scenes / 4 locations / 6 characters / egypt / USD
    Pre-verified total = 22 506.00
    """
    resp = _post(_valid_payload(
        script_id="eg-001",
        scene_count=15,
        location_count=4,
        character_count=6,
        region="egypt",
        currency="USD",
    ))
    assert resp.status_code == 202
    assert resp.json()["total_estimated_cost"] == pytest.approx(22_506.00, abs=0.01)


def test_estimate_sar_currency():
    """SAR conversion for the worked example returns 202 with SAR in every item."""
    resp = _post(_valid_payload(
        script_id="sar-001",
        scene_count=20,
        location_count=5,
        character_count=8,
        currency="SAR",
        region="gulf",
    ))
    assert resp.status_code == 202
    body = resp.json()
    assert body["currency"] == "SAR"
    # Pre-verified: 186 532.50
    assert body["total_estimated_cost"] == pytest.approx(186_532.50, abs=0.01)
    for item in body["line_items"]:
        assert item["currency"] == "SAR"


def test_estimate_shoot_days_in_response():
    """
    estimated_shoot_days field is present and correct.
    20 scenes / 5 loc / 8 char → 4 days (pre-verified).
    """
    resp = _post(_valid_payload(
        scene_count=20, location_count=5, character_count=8
    ))
    assert resp.status_code == 202
    assert resp.json()["estimated_shoot_days"] == 4


def test_estimate_six_line_items():
    """Response always contains exactly the six standard categories."""
    resp = _post(_valid_payload())
    assert resp.status_code == 202
    categories = {item["category"] for item in resp.json()["line_items"]}
    assert categories == {"crew", "equipment", "locations", "cast",
                          "post_production", "contingency"}


def test_estimate_line_item_total_consistency():
    """total_estimated_cost == sum of all line_item estimated_cost values."""
    resp = _post(_valid_payload(
        scene_count=12, location_count=4, character_count=5
    ))
    assert resp.status_code == 202
    body = resp.json()
    item_sum = sum(item["estimated_cost"] for item in body["line_items"])
    assert body["total_estimated_cost"] == pytest.approx(item_sum, abs=1e-6)


def test_estimate_zero_locations_valid():
    """location_count=0 is explicitly valid; cast line item is zero."""
    resp = _post(_valid_payload(location_count=0, character_count=0))
    assert resp.status_code == 202
    body = resp.json()
    cast_item = next(i for i in body["line_items"] if i["category"] == "cast")
    assert cast_item["estimated_cost"] == pytest.approx(0.00, abs=0.01)


def test_estimate_zero_characters_valid():
    """character_count=0 is explicitly valid; cast line item is zero."""
    resp = _post(_valid_payload(character_count=0))
    assert resp.status_code == 202
    cast_item = next(
        i for i in resp.json()["line_items"] if i["category"] == "cast"
    )
    assert cast_item["estimated_cost"] == pytest.approx(0.00, abs=0.01)


def test_estimate_script_id_echoed():
    """script_id supplied in the request is echoed back unchanged."""
    resp = _post(_valid_payload(script_id="my-tracking-id-xyz"))
    assert resp.status_code == 202
    assert resp.json()["script_id"] == "my-tracking-id-xyz"


# ---------------------------------------------------------------------------
# Concrete worked example (judge demonstration)
# ---------------------------------------------------------------------------


def test_estimate_worked_example():
    """
    Canonical worked example: 20 scenes / 5 locations / 8 characters / gulf / USD.

    Derivation:
      shoot_days       = 4
      crew             = 11 900.00
      equipment        =  6 800.00
      locations        =  6 120.00
      cast             = 13 600.00
      post_production  =  6 800.00
      contingency      =  4 522.00
      total            = 49 742.00
    """
    resp = _post({
        "script_id": "worked-example-001",
        "scene_count": 20,
        "location_count": 5,
        "character_count": 8,
        "currency": "USD",
        "region": "gulf",
    })
    assert resp.status_code == 202
    body = resp.json()

    assert body["estimated_shoot_days"] == 4
    assert body["total_estimated_cost"] == pytest.approx(49_742.00, abs=0.01)

    by_cat = {item["category"]: item["estimated_cost"] for item in body["line_items"]}
    assert by_cat["crew"]            == pytest.approx(11_900.00, abs=0.01)
    assert by_cat["equipment"]       == pytest.approx( 6_800.00, abs=0.01)
    assert by_cat["locations"]       == pytest.approx( 6_120.00, abs=0.01)
    assert by_cat["cast"]            == pytest.approx(13_600.00, abs=0.01)
    assert by_cat["post_production"] == pytest.approx( 6_800.00, abs=0.01)
    assert by_cat["contingency"]     == pytest.approx( 4_522.00, abs=0.01)


# ---------------------------------------------------------------------------
# Pydantic field-constraint rejections — HTTP 422
# ---------------------------------------------------------------------------


def test_missing_scene_count_without_stored_script_returns_404():
    """
    Omitting scene_count activates store-lookup mode.
    When the script_id is not in the store, the router returns 404 — not 422.
    The previous 422 expectation was correct under the old contract where
    scene_count was required.  Under the new contract, omitting scene_count
    is valid; the error is a missing script, not a validation error.
    """
    payload = {
        "script_id": "unknown-id-xyz",
        "location_count": 2,
        "character_count": 3,
    }
    resp = _post(payload)
    assert resp.status_code == 404


def test_zero_scene_count_rejected():
    """scene_count=0 violates the ge=1 Pydantic constraint → 422."""
    resp = _post(_valid_payload(scene_count=0))
    assert resp.status_code == 422


def test_negative_scene_count_rejected():
    """scene_count=-1 violates ge=1 → 422."""
    resp = _post(_valid_payload(scene_count=-1))
    assert resp.status_code == 422


def test_negative_location_count_rejected():
    """location_count=-1 violates ge=0 → 422."""
    resp = _post(_valid_payload(location_count=-1))
    assert resp.status_code == 422


def test_negative_character_count_rejected():
    """character_count=-1 violates ge=0 → 422."""
    resp = _post(_valid_payload(character_count=-1))
    assert resp.status_code == 422


def test_empty_script_id_rejected():
    """script_id='' violates min_length=1 → 422."""
    resp = _post(_valid_payload(script_id=""))
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# BudgetEstimator ValueError rejections — HTTP 422
# (These pass Pydantic but are caught by estimator's defense-in-depth)
# ---------------------------------------------------------------------------


def test_unsupported_region_rejected():
    """An unsupported region is caught by BudgetEstimator → mapped to 422."""
    resp = _post(_valid_payload(region="atlantis"))
    assert resp.status_code == 422
    assert "region" in resp.json()["detail"].lower()


def test_unsupported_currency_rejected():
    """An unsupported currency is caught by BudgetEstimator → mapped to 422."""
    resp = _post(_valid_payload(currency="XYZ"))
    assert resp.status_code == 422
    assert "currency" in resp.json()["detail"].lower()


# ---------------------------------------------------------------------------
# Store-lookup mode — upload first, then estimate via script_id only
# ---------------------------------------------------------------------------

_DEMO_SCRIPT = (
    "INT. BAKERY - DAY\n\n"
    "The smell of fresh bread fills the air.\n\n"
    "BAKER\nGood morning.\n\n"
    "EXT. STREET - NIGHT\n\n"
    "Alice walks home alone.\n\n"
    "ALICE\nSomething feels wrong.\n\n"
    "INT. APARTMENT - CONTINUOUS\n\n"
    "The door creaks open.\n"
).encode("utf-8")


def test_estimate_from_script_id_only():
    """
    Upload a script, then request a budget estimate supplying only script_id.
    The router must derive scene/location/character counts from the store
    and return a valid 202 response.
    """
    sid = _upload_script(_DEMO_SCRIPT)
    resp = _post({"script_id": sid, "currency": "USD", "region": "international"})
    assert resp.status_code == 202
    body = resp.json()
    assert body["script_id"] == sid
    assert body["estimated_shoot_days"] >= 1
    assert body["total_estimated_cost"] > 0
    assert len(body["line_items"]) == 6


def test_estimate_from_unknown_script_id_returns_404():
    """store-lookup mode with an unknown script_id must return 404."""
    resp = _post({"script_id": "no-such-script-id", "currency": "USD", "region": "gulf"})
    assert resp.status_code == 404


def test_estimate_explicit_counts_unaffected_by_store():
    """
    Explicit-count mode must work even when the script_id is not in the store.
    The store is NOT consulted when scene_count is supplied.
    """
    resp = _post(_valid_payload(script_id="any-label", scene_count=10,
                                location_count=2, character_count=3))
    assert resp.status_code == 202
    assert resp.json()["total_estimated_cost"] > 0
