"""Budget router — production cost estimation."""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

router = APIRouter()


class BudgetRequest(BaseModel):
    script_id: str = Field(..., description="ID of a parsed script")
    currency: str = Field(
        default="USD",
        description="Output currency code (e.g. USD, SAR, AED)",
    )
    region: str = Field(
        default="international",
        description="Production region affects cost estimates (e.g. 'international', 'gulf', 'egypt')",
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
    line_items: list[BudgetLineItem]


@router.post(
    "/estimate",
    response_model=BudgetResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Estimate production budget for a script",
)
async def estimate_budget(request: BudgetRequest) -> BudgetResponse:
    """
    Generate a production budget estimate from a parsed script.

    Considers scene count, locations, characters, and regional cost data.
    """
    # TODO (Data Science Lead): implement budget_estimator service
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Budget estimator not yet implemented.",
    )
