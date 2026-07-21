"""Budget router — production cost estimation.

Two estimation modes
---------------------
1. **Explicit-count mode** (backward-compatible, original behaviour):
   Supply ``scene_count`` (required ≥ 1) along with ``script_id``,
   ``currency``, and ``region``.  ``location_count`` and ``character_count``
   are optional (default 0).  The store is NOT consulted.

2. **Store-lookup mode** (new, requires parse-on-upload workflow):
   Omit ``scene_count`` and supply only ``script_id``, ``currency``, and
   ``region``.  The router looks up the ``ParsedScript`` in the ephemeral
   store and derives ``scene_count``, ``location_count``, and
   ``character_count`` automatically.

   Returns HTTP 404 if the ``script_id`` is unknown.
   Returns HTTP 422 if the stored script has zero scenes (should not happen
   in practice, but is guarded defensively).

MVP limitation
--------------
The store is process-scoped and ephemeral; see ``services/script_store.py``.
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from services.budget_estimator import BudgetEstimator
from services.script_store import get as store_get

router = APIRouter()

_estimator = BudgetEstimator()


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------


class BudgetRequest(BaseModel):
    # Tracking label — echoed in the response.
    # In store-lookup mode it is also used to resolve parsed metadata.
    script_id: str = Field(
        ...,
        min_length=1,
        description=(
            "Non-empty tracking identifier.  "
            "When ``scene_count`` is omitted the server looks this up in the "
            "ephemeral script store to derive complexity counts automatically."
        ),
    )

    # Production complexity inputs.
    # Optional: when None the store-lookup mode is activated.
    scene_count: int | None = Field(
        default=None,
        ge=1,
        description=(
            "Number of scenes (must be ≥ 1 if supplied).  "
            "Omit to derive automatically from a previously uploaded script."
        ),
    )
    location_count: int = Field(
        default=0,
        ge=0,
        description="Number of unique locations (must be ≥ 0).  Ignored in store-lookup mode.",
    )
    character_count: int = Field(
        default=0,
        ge=0,
        description="Number of principal characters (must be ≥ 0).  Ignored in store-lookup mode.",
    )

    # Output preferences — unchanged from original contract.
    currency: str = Field(
        default="USD",
        description="Output currency code (USD, SAR, AED, EGP).",
    )
    region: str = Field(
        default="international",
        description=(
            "Production region for cost multiplier "
            "(international, gulf, egypt)."
        ),
    )


class BudgetLineItem(BaseModel):
    category: str
    description: str
    estimated_cost: float
    currency: str


class BudgetResponse(BaseModel):
    script_id: str
    currency: str
    region: str
    total_estimated_cost: float
    estimated_shoot_days: int
    line_items: list[BudgetLineItem]


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------


@router.post(
    "/estimate",
    response_model=BudgetResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Estimate production budget for a script",
)
async def estimate_budget(request: BudgetRequest) -> BudgetResponse:
    """
    Generate a deterministic production budget estimate.

    **Explicit-count mode** — supply ``scene_count`` directly:

        {
          "script_id": "my-label",
          "scene_count": 20,
          "location_count": 5,
          "character_count": 8,
          "currency": "USD",
          "region": "gulf"
        }

    **Store-lookup mode** — omit ``scene_count``; the server resolves counts
    from a previously uploaded and parsed script:

        {
          "script_id": "<id returned by POST /api/scripts/upload>",
          "currency": "USD",
          "region": "gulf"
        }

    All rates and regional multipliers are transparent MVP planning
    assumptions documented in ``services/budget_estimator.py``.
    """
    # Resolve complexity counts.
    if request.scene_count is not None:
        # Explicit-count mode — use client-supplied values unchanged.
        scene_count = request.scene_count
        location_count = request.location_count
        character_count = request.character_count
    else:
        # Store-lookup mode — derive counts from the stored ParsedScript.
        parsed = store_get(request.script_id)
        if parsed is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    f"Script '{request.script_id}' not found in the store. "
                    "Upload and parse the script first via "
                    "POST /api/scripts/upload, then retry."
                ),
            )
        scene_count = parsed.scene_count
        location_count = len(parsed.locations)
        character_count = len(parsed.characters)

        if scene_count < 1:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    f"Stored script '{request.script_id}' has "
                    f"scene_count={scene_count}, which is invalid for estimation."
                ),
            )

    try:
        result = await _estimator.estimate(
            script_id=request.script_id,
            scene_count=scene_count,
            location_count=location_count,
            character_count=character_count,
            currency=request.currency,
            region=request.region,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    return BudgetResponse(
        script_id=result.script_id,
        currency=result.currency,
        region=result.region,
        total_estimated_cost=result.total_estimated_cost,
        estimated_shoot_days=result.estimated_shoot_days,
        line_items=[
            BudgetLineItem(
                category=item.category,
                description=item.description,
                estimated_cost=item.estimated_cost,
                currency=item.currency,
            )
            for item in result.line_items
        ],
    )
