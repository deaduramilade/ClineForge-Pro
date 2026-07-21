"""
Production budget estimator service.

Owned by: Data Science Lead
Responsibility: Estimate production costs from parsed script metadata.

All rates, multipliers, and currency conversion factors defined here are
transparent MVP planning assumptions for demonstration purposes only.
They are NOT authoritative industry rates, validated production-house data,
or live financial exchange rates.  They are centralized as named constants so
they can be replaced with validated data at any time without touching the
estimation logic.
"""

import math
from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal


# ---------------------------------------------------------------------------
# Shoot-day estimation constants
# (MVP planning assumptions — not validated industry benchmarks)
# ---------------------------------------------------------------------------

#: Average number of screenplay pages represented by one scene.
PAGES_PER_SCENE: Decimal = Decimal("0.5")

#: Number of screenplay pages a crew can realistically shoot per day.
PAGES_PER_DAY: Decimal = Decimal("5")

#: Extra shoot days added per unique location (covers travel/setup overhead).
LOCATION_DAY_FACTOR: Decimal = Decimal("0.4")

#: Extra shoot days added per principal character (covers rehearsal/makeup).
CHARACTER_DAY_FACTOR: Decimal = Decimal("0.1")


# ---------------------------------------------------------------------------
# Base day/unit cost rates in USD
# (MVP planning assumptions — not authoritative industry rates)
# ---------------------------------------------------------------------------

#: USD cost per shoot day for full crew package.
CREW_DAY_RATE_USD: Decimal = Decimal("3500")

#: USD cost per shoot day for camera/lighting/grip equipment.
EQUIP_DAY_RATE_USD: Decimal = Decimal("2000")

#: USD flat fee per unique location (permits, scouting, one-time setup).
LOCATION_FEE_USD: Decimal = Decimal("1200")

#: USD additional cost per location per shoot day (security, facilities).
LOCATION_DAY_FEE_USD: Decimal = Decimal("300")

#: USD cost per character per shoot day (talent fees, makeup, wardrobe).
CAST_DAY_RATE_USD: Decimal = Decimal("500")

#: USD cost per scene for post-production (edit, colour, sound).
POST_PER_SCENE_USD: Decimal = Decimal("400")

#: Contingency percentage applied to the pre-contingency subtotal.
CONTINGENCY_RATE: Decimal = Decimal("0.10")


# ---------------------------------------------------------------------------
# Regional cost multipliers
# (Configurable demo assumptions — not sourced from verified market data)
# ---------------------------------------------------------------------------

#: Multiplier applied to all base-USD costs for each supported region.
REGION_MULTIPLIERS: dict[str, Decimal] = {
    "international": Decimal("1.00"),
    "gulf": Decimal("0.85"),
    "egypt": Decimal("0.55"),
}

#: Human-readable labels for the supported regions.
SUPPORTED_REGIONS: frozenset[str] = frozenset(REGION_MULTIPLIERS.keys())


# ---------------------------------------------------------------------------
# Currency conversion rates from USD
# (Fixed demo estimation rates — NOT live financial exchange rates.
#  Last updated: July 2026 for demonstration purposes only.)
# ---------------------------------------------------------------------------

#: Conversion factor: 1 USD → X units of each supported currency.
CURRENCY_RATES: dict[str, Decimal] = {
    "USD": Decimal("1.000"),
    "SAR": Decimal("3.750"),
    "AED": Decimal("3.673"),
    "EGP": Decimal("48.500"),
}

#: Set of supported output currency codes.
SUPPORTED_CURRENCIES: frozenset[str] = frozenset(CURRENCY_RATES.keys())

# Quantisation target for all monetary output values (2 decimal places).
_TWO_PLACES = Decimal("0.01")


# ---------------------------------------------------------------------------
# Public dataclasses  (existing public surface — preserved exactly)
# ---------------------------------------------------------------------------


@dataclass
class BudgetLineItem:
    """A single line item in a production budget."""

    category: str  # crew, equipment, locations, cast, post_production, contingency
    description: str
    estimated_cost: float
    currency: str


@dataclass
class BudgetEstimate:
    """Full production budget estimate."""

    script_id: str
    currency: str
    region: str
    total_estimated_cost: float
    estimated_shoot_days: int
    line_items: list[BudgetLineItem] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Estimator
# ---------------------------------------------------------------------------


class BudgetEstimator:
    """
    Estimate film production budgets from parsed script metadata.

    All calculations are deterministic and use Python's ``Decimal`` type
    internally to prevent floating-point drift.  Line items and totals are
    rounded to 2 decimal places (ROUND_HALF_UP) after currency conversion,
    and ``total_estimated_cost`` is always set to the exact sum of line-item
    ``estimated_cost`` values so the invariant:

        total_estimated_cost == sum(item.estimated_cost for item in line_items)

    holds exactly.

    Usage::

        estimator = BudgetEstimator()
        result = await estimator.estimate(
            script_id="demo-001",
            scene_count=20,
            location_count=5,
            character_count=8,
            currency="USD",
            region="gulf",
        )

    Concrete worked example (20 scenes / 5 locations / 8 characters / gulf / USD):

        shoot_days       = 4
        crew             = 11 900.00 USD
        equipment        =  6 800.00 USD
        locations        =  6 120.00 USD
        cast             = 13 600.00 USD
        post_production  =  6 800.00 USD
        contingency      =  4 522.00 USD
        ─────────────────────────────────
        total            = 49 742.00 USD
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def estimate(
        self,
        script_id: str,
        scene_count: int,
        location_count: int,
        character_count: int,
        currency: str = "USD",
        region: str = "international",
    ) -> BudgetEstimate:
        """
        Estimate the production budget for a script.

        Args:
            script_id:       Non-empty identifier for the parsed script.
            scene_count:     Number of scenes (must be ≥ 1).
            location_count:  Number of unique locations (must be ≥ 0).
            character_count: Number of principal characters (must be ≥ 0).
            currency:        Output currency code (USD, SAR, AED, EGP).
            region:          Production region (international, gulf, egypt).

        Returns:
            BudgetEstimate with line items, shoot-day estimate, and total.

        Raises:
            ValueError: on invalid inputs, unsupported region, or unsupported
                currency.
        """
        self._validate_inputs(
            script_id, scene_count, location_count, character_count,
            currency, region,
        )

        shoot_days = self._estimate_shoot_days(
            scene_count, location_count, character_count
        )
        multiplier = REGION_MULTIPLIERS[region]
        fx_rate = CURRENCY_RATES[currency]

        line_items_decimal = self._build_line_items(
            scene_count=scene_count,
            location_count=location_count,
            character_count=character_count,
            shoot_days=shoot_days,
            multiplier=multiplier,
            fx_rate=fx_rate,
            currency=currency,
        )

        # Convert Decimal line items to BudgetLineItem with float costs.
        # total = exact sum of rounded items (invariant guaranteed).
        line_items: list[BudgetLineItem] = [
            BudgetLineItem(
                category=cat,
                description=desc,
                estimated_cost=float(cost),
                currency=currency,
            )
            for cat, desc, cost in line_items_decimal
        ]
        total = float(sum(cost for _, _, cost in line_items_decimal))

        return BudgetEstimate(
            script_id=script_id,
            currency=currency,
            region=region,
            total_estimated_cost=total,
            estimated_shoot_days=shoot_days,
            line_items=line_items,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _validate_inputs(
        self,
        script_id: str,
        scene_count: int,
        location_count: int,
        character_count: int,
        currency: str,
        region: str,
    ) -> None:
        """Raise ValueError for any invalid input."""
        if not script_id or not script_id.strip():
            raise ValueError("script_id must not be empty.")
        if scene_count < 1:
            raise ValueError(
                f"scene_count must be at least 1, got {scene_count}."
            )
        if location_count < 0:
            raise ValueError(
                f"location_count must not be negative, got {location_count}."
            )
        if character_count < 0:
            raise ValueError(
                f"character_count must not be negative, got {character_count}."
            )
        if region not in SUPPORTED_REGIONS:
            raise ValueError(
                f"Unsupported region '{region}'. "
                f"Supported regions: {sorted(SUPPORTED_REGIONS)}."
            )
        if currency not in SUPPORTED_CURRENCIES:
            raise ValueError(
                f"Unsupported currency '{currency}'. "
                f"Supported currencies: {sorted(SUPPORTED_CURRENCIES)}."
            )

    def _estimate_shoot_days(
        self,
        scene_count: int,
        location_count: int,
        character_count: int,
    ) -> int:
        """
        Deterministic shoot-day formula.

        All inputs are transparent MVP planning assumptions:

            pages  = scene_count  × PAGES_PER_SCENE
            days   = ceil(pages / PAGES_PER_DAY)
                   + floor(location_count  × LOCATION_DAY_FACTOR)
                   + floor(character_count × CHARACTER_DAY_FACTOR)

        Returns at least 1 for any valid (non-empty) production.
        """
        pages = Decimal(scene_count) * PAGES_PER_SCENE
        base_days = math.ceil(pages / PAGES_PER_DAY)
        loc_premium = math.floor(Decimal(location_count) * LOCATION_DAY_FACTOR)
        char_premium = math.floor(Decimal(character_count) * CHARACTER_DAY_FACTOR)
        return max(1, base_days + loc_premium + char_premium)

    def _round_currency(self, value: Decimal) -> Decimal:
        """Round to 2 decimal places using ROUND_HALF_UP."""
        return value.quantize(_TWO_PLACES, rounding=ROUND_HALF_UP)

    def _build_line_items(
        self,
        scene_count: int,
        location_count: int,
        character_count: int,
        shoot_days: int,
        multiplier: Decimal,
        fx_rate: Decimal,
        currency: str,
    ) -> list[tuple[str, str, Decimal]]:
        """
        Compute (category, description, rounded_cost) tuples.

        All costs are:
          1. calculated in USD using named constants
          2. scaled by the regional multiplier
          3. converted to the output currency
          4. rounded to 2 decimal places (ROUND_HALF_UP)

        Contingency is 10 % of the pre-contingency subtotal, applied after
        the regional multiplier and currency conversion.
        """
        sd = Decimal(shoot_days)
        lc = Decimal(location_count)
        cc = Decimal(character_count)
        sc = Decimal(scene_count)

        def convert(usd_amount: Decimal) -> Decimal:
            return self._round_currency(usd_amount * multiplier * fx_rate)

        crew_cost = convert(sd * CREW_DAY_RATE_USD)
        equip_cost = convert(sd * EQUIP_DAY_RATE_USD)
        loc_cost = convert(lc * LOCATION_FEE_USD + sd * LOCATION_DAY_FEE_USD)
        cast_cost = convert(cc * CAST_DAY_RATE_USD * sd)
        post_cost = convert(sc * POST_PER_SCENE_USD)

        subtotal = crew_cost + equip_cost + loc_cost + cast_cost + post_cost
        contingency_cost = self._round_currency(subtotal * CONTINGENCY_RATE)

        return [
            (
                "crew",
                f"Full crew package — {shoot_days} shoot day(s) "
                f"@ {currency} {float(self._round_currency(CREW_DAY_RATE_USD * multiplier * fx_rate))}/day",
                crew_cost,
            ),
            (
                "equipment",
                f"Camera, lighting & grip — {shoot_days} shoot day(s) "
                f"@ {currency} {float(self._round_currency(EQUIP_DAY_RATE_USD * multiplier * fx_rate))}/day",
                equip_cost,
            ),
            (
                "locations",
                f"{location_count} unique location(s): permit/scout fee "
                f"+ {shoot_days} day(s) facility cost",
                loc_cost,
            ),
            (
                "cast",
                f"{character_count} character(s) × {shoot_days} shoot day(s) "
                f"@ {currency} {float(self._round_currency(CAST_DAY_RATE_USD * multiplier * fx_rate))}/character/day",
                cast_cost,
            ),
            (
                "post_production",
                f"{scene_count} scene(s) @ {currency} "
                f"{float(self._round_currency(POST_PER_SCENE_USD * multiplier * fx_rate))}/scene "
                f"(edit, colour, sound)",
                post_cost,
            ),
            (
                "contingency",
                f"Contingency reserve — {int(CONTINGENCY_RATE * 100)}% of subtotal",
                contingency_cost,
            ),
        ]
