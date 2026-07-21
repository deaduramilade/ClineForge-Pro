"""Budget router — production cost estimation.

Integration note (MVP / demo):
    script_id is currently a client-supplied tracking label only.  It is
    echoed back in the response for traceability but is NOT used to look up
    any stored script.

    scene_count, location_count, and character_count are also client-supplied
    because no parse-and-persist workflow exists yet.  When a script-storage
    layer is added, this endpoint should instead accept a script_id and derive
    the counts from the stored ParsedScript.
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from services.budget_estimator import BudgetEstimator

router = APIRouter()

_estimator = BudgetEstimator()


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------


class BudgetRequest(BaseModel):
    # Tracking label — echoed in the response; not used to look up stored data.
    script_id: str = Field(
        ...,
        min_length=1,
        description=(
            "Non-empty tracking identifier for this estimate request.  "
            "Currently a client-supplied label; will reference a stored "
            "ParsedScript once a parse-and-persist workflow is in place."
        ),
    )

    # Production complexity inputs — client-supplied until parse-and-persist exists.
    scene_count: int = Field(
        ...,
        ge=1,
        description="Number of scenes in the script (must be ≥ 1).",
    )
    location_count: int = Field(
        default=0,
        ge=0,
        description="Number of unique locations in the script (must be ≥ 0).",
    )
    character_count: int = Field(
        default=0,
        ge=0,
        description="Number of principal characters in the script (must be ≥ 0).",
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

    Accepts script complexity metadata (scene count, unique locations,
    principal character count) alongside output preferences (currency,
    region) and returns a line-item budget with an estimated shoot-day count.

    All rates and regional multipliers are transparent MVP planning
    assumptions documented in ``services/budget_estimator.py``.

    Returns HTTP 422 for invalid inputs (unsupported region/currency, or
    constraint violations not already caught by Pydantic field validation).
    """
    try:
        result = await _estimator.estimate(
            script_id=request.script_id,
            scene_count=request.scene_count,
            location_count=request.location_count,
            character_count=request.character_count,
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
