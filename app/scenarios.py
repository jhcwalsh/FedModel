"""
scenarios.py — Pre-built shock scenario definitions for FRB/US simulations.

Each scenario returns a dict with:
  - label:     display name
  - overrides: {varname: scalar_delta} applied to the shocked simulation
  - targ:      target variables for mcontrol (empty list = free solve)
  - traj:      trajectory variables for mcontrol
  - inst:      instrument variables for mcontrol
  - description: human-readable explanation
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Scenario:
    label: str
    description: str
    overrides: dict[str, Any]
    targ: list[str] = field(default_factory=list)
    traj: list[str] = field(default_factory=list)
    inst: list[str] = field(default_factory=list)


def monetary_tightening(bps: float = 100, duration_quarters: int = 4) -> Scenario:
    """
    Raise the federal funds rate by `bps` basis points for `duration_quarters`.
    Uses the FFR add-factor (rffintay) to override the Taylor rule.
    """
    delta_pct = bps / 100.0
    return Scenario(
        label=f"Monetary Tightening +{int(bps)}bps ({duration_quarters}Q)",
        description=(
            f"Federal funds rate raised by {bps} basis points above baseline "
            f"for {duration_quarters} quarters, then returns to endogenous Taylor rule."
        ),
        overrides={"rffintay": delta_pct},
        targ=[],
        traj=[],
        inst=[],
    )


def monetary_easing(bps: float = 100, duration_quarters: int = 4) -> Scenario:
    """Lower the federal funds rate by `bps` basis points."""
    delta_pct = -bps / 100.0
    return Scenario(
        label=f"Monetary Easing -{int(bps)}bps ({duration_quarters}Q)",
        description=(
            f"Federal funds rate lowered by {bps} basis points below baseline "
            f"for {duration_quarters} quarters, then returns to endogenous Taylor rule."
        ),
        overrides={"rffintay": delta_pct},
    )


def fiscal_expansion(pct_gdp: float = 1.0, duration_quarters: int = 8) -> Scenario:
    """
    Increase federal government spending by `pct_gdp` percent of GDP
    for `duration_quarters`. Uses gftrd (federal spending) add-factor.
    """
    return Scenario(
        label=f"Fiscal Expansion +{pct_gdp:.1f}% GDP ({duration_quarters}Q)",
        description=(
            f"Federal government spending increased by {pct_gdp}% of GDP "
            f"for {duration_quarters} quarters."
        ),
        overrides={"egfos": pct_gdp},
    )


def fiscal_consolidation(pct_gdp: float = 1.0, duration_quarters: int = 8) -> Scenario:
    """Decrease federal government spending (fiscal tightening)."""
    return Scenario(
        label=f"Fiscal Consolidation -{pct_gdp:.1f}% GDP ({duration_quarters}Q)",
        description=(
            f"Federal government spending reduced by {pct_gdp}% of GDP "
            f"for {duration_quarters} quarters."
        ),
        overrides={"egfos": -pct_gdp},
    )


def oil_price_shock(pct_change: float = 50.0, duration_quarters: int = 4) -> Scenario:
    """
    Oil price increases by `pct_change` percent for `duration_quarters`.
    Uses poilr (real oil price) add-factor.
    """
    return Scenario(
        label=f"Oil Price Shock +{pct_change:.0f}% ({duration_quarters}Q)",
        description=(
            f"Real oil price rises {pct_change}% above baseline "
            f"for {duration_quarters} quarters."
        ),
        overrides={"epoil": pct_change / 100.0},
    )


def productivity_shock(pct_change: float = 1.0, duration_quarters: int = 8) -> Scenario:
    """Total factor productivity (TFP) shock."""
    return Scenario(
        label=f"Productivity Shock +{pct_change:.1f}% ({duration_quarters}Q)",
        description=(
            f"Total factor productivity increases by {pct_change}% "
            f"for {duration_quarters} quarters."
        ),
        overrides={"lurnat": -pct_change / 100.0},
    )


# Registry of all built-in scenario builders (label → callable)
SCENARIO_BUILDERS = {
    "Monetary Tightening": monetary_tightening,
    "Monetary Easing": monetary_easing,
    "Fiscal Expansion": fiscal_expansion,
    "Fiscal Consolidation": fiscal_consolidation,
    "Oil Price Shock": oil_price_shock,
    "Productivity Shock": productivity_shock,
}

SCENARIO_PARAMS = {
    "Monetary Tightening": [
        {"name": "bps", "label": "Rate hike (basis points)", "min": 25, "max": 500, "default": 100, "step": 25},
        {"name": "duration_quarters", "label": "Duration (quarters)", "min": 1, "max": 20, "default": 4, "step": 1},
    ],
    "Monetary Easing": [
        {"name": "bps", "label": "Rate cut (basis points)", "min": 25, "max": 500, "default": 100, "step": 25},
        {"name": "duration_quarters", "label": "Duration (quarters)", "min": 1, "max": 20, "default": 4, "step": 1},
    ],
    "Fiscal Expansion": [
        {"name": "pct_gdp", "label": "Spending increase (% of GDP)", "min": 0.1, "max": 5.0, "default": 1.0, "step": 0.1},
        {"name": "duration_quarters", "label": "Duration (quarters)", "min": 1, "max": 20, "default": 8, "step": 1},
    ],
    "Fiscal Consolidation": [
        {"name": "pct_gdp", "label": "Spending cut (% of GDP)", "min": 0.1, "max": 5.0, "default": 1.0, "step": 0.1},
        {"name": "duration_quarters", "label": "Duration (quarters)", "min": 1, "max": 20, "default": 8, "step": 1},
    ],
    "Oil Price Shock": [
        {"name": "pct_change", "label": "Oil price increase (%)", "min": 5.0, "max": 200.0, "default": 50.0, "step": 5.0},
        {"name": "duration_quarters", "label": "Duration (quarters)", "min": 1, "max": 20, "default": 4, "step": 1},
    ],
    "Productivity Shock": [
        {"name": "pct_change", "label": "TFP increase (%)", "min": 0.1, "max": 5.0, "default": 1.0, "step": 0.1},
        {"name": "duration_quarters", "label": "Duration (quarters)", "min": 1, "max": 20, "default": 8, "step": 1},
    ],
}
