"""
scenarios.py — Pre-built shock scenario definitions for FRB/US simulations.

Shocks are applied via _aerr (add-factor / equation residual) variables.
Each scenario returns a Scenario dataclass with aerr_shocks dict and UI metadata.
"""

from dataclasses import dataclass, field


@dataclass
class Scenario:
    label: str
    description: str
    aerr_shocks: dict          # {varname_aerr: scalar delta} applied over shock window
    shock_duration: int = 4    # quarters the shock persists (1 = one-shot)


def monetary_tightening(bps: float = 100, duration_quarters: int = 4) -> Scenario:
    """
    Raise the federal funds rate by bps above the Taylor rule for duration_quarters.
    rffintay_aerr is the add-factor to the inertial Taylor rule equation.
    """
    return Scenario(
        label=f"Monetary Tightening +{int(bps)}bps ({duration_quarters}Q)",
        description=(
            f"Federal funds rate raised {bps} basis points above the inertial Taylor rule "
            f"for {duration_quarters} quarters, then returns to endogenous determination."
        ),
        aerr_shocks={"rffintay_aerr": bps / 100.0},
        shock_duration=duration_quarters,
    )


def monetary_easing(bps: float = 100, duration_quarters: int = 4) -> Scenario:
    """Lower the federal funds rate by bps below the Taylor rule."""
    return Scenario(
        label=f"Monetary Easing -{int(bps)}bps ({duration_quarters}Q)",
        description=(
            f"Federal funds rate cut {bps} basis points below the inertial Taylor rule "
            f"for {duration_quarters} quarters."
        ),
        aerr_shocks={"rffintay_aerr": -bps / 100.0},
        shock_duration=duration_quarters,
    )


def fiscal_expansion(pct: float = 1.0, duration_quarters: int = 8) -> Scenario:
    """
    Increase federal government expenditure via egfet_aerr (total federal spending add-factor).
    pct is expressed as a fraction of GDP (rough approximation through add-factor).
    """
    return Scenario(
        label=f"Fiscal Expansion +{pct:.1f}% ({duration_quarters}Q)",
        description=(
            f"Federal government spending add-factor raised by {pct}% "
            f"for {duration_quarters} quarters."
        ),
        aerr_shocks={"egfet_aerr": pct / 100.0},
        shock_duration=duration_quarters,
    )


def fiscal_consolidation(pct: float = 1.0, duration_quarters: int = 8) -> Scenario:
    """Decrease federal government spending (fiscal tightening)."""
    return Scenario(
        label=f"Fiscal Consolidation -{pct:.1f}% ({duration_quarters}Q)",
        description=(
            f"Federal government spending add-factor reduced by {pct}% "
            f"for {duration_quarters} quarters."
        ),
        aerr_shocks={"egfet_aerr": -pct / 100.0},
        shock_duration=duration_quarters,
    )


def oil_price_shock(pct_change: float = 50.0, duration_quarters: int = 4) -> Scenario:
    """
    Oil price shock via poilr_aerr (real oil price add-factor).
    pct_change: percentage-point add to real oil price growth.
    """
    return Scenario(
        label=f"Oil Price Shock +{pct_change:.0f}% ({duration_quarters}Q)",
        description=(
            f"Real oil price add-factor raised by {pct_change / 100:.2f} "
            f"for {duration_quarters} quarters (~{pct_change:.0f}% price increase)."
        ),
        aerr_shocks={"poilr_aerr": pct_change / 100.0},
        shock_duration=duration_quarters,
    )


def productivity_shock(pct: float = 1.0, duration_quarters: int = 8) -> Scenario:
    """
    Multifactor productivity shock via mfpt_aerr.
    pct: percentage-point add to MFP trend growth.
    """
    return Scenario(
        label=f"Productivity Shock +{pct:.1f}% ({duration_quarters}Q)",
        description=(
            f"Multifactor productivity add-factor raised by {pct / 100:.3f} "
            f"for {duration_quarters} quarters."
        ),
        aerr_shocks={"mfpt_aerr": pct / 100.0},
        shock_duration=duration_quarters,
    )


def demand_shock(pct: float = 1.0, duration_quarters: int = 4) -> Scenario:
    """
    Aggregate demand shock: simultaneous add-factors to consumer spending (eco_aerr)
    and consumer durables (ecd_aerr).
    """
    return Scenario(
        label=f"Demand Shock +{pct:.1f}% ({duration_quarters}Q)",
        description=(
            f"Positive aggregate demand shock: consumer spending and durable goods "
            f"add-factors each raised by {pct / 100:.3f} for {duration_quarters} quarters."
        ),
        aerr_shocks={
            "eco_aerr": pct / 100.0,
            "ecd_aerr": pct / 100.0,
        },
        shock_duration=duration_quarters,
    )


# ── Registry ─────────────────────────────────────────────────────────────────

SCENARIO_BUILDERS = {
    "Monetary Tightening":  monetary_tightening,
    "Monetary Easing":      monetary_easing,
    "Fiscal Expansion":     fiscal_expansion,
    "Fiscal Consolidation": fiscal_consolidation,
    "Oil Price Shock":      oil_price_shock,
    "Productivity Shock":   productivity_shock,
    "Demand Shock":         demand_shock,
}

SCENARIO_PARAMS = {
    "Monetary Tightening": [
        {"name": "bps",               "label": "Rate hike (basis points)",  "min": 25,  "max": 500,  "default": 100,  "step": 25,  "float": False},
        {"name": "duration_quarters", "label": "Duration (quarters)",        "min": 1,   "max": 20,   "default": 4,    "step": 1,   "float": False},
    ],
    "Monetary Easing": [
        {"name": "bps",               "label": "Rate cut (basis points)",   "min": 25,  "max": 500,  "default": 100,  "step": 25,  "float": False},
        {"name": "duration_quarters", "label": "Duration (quarters)",        "min": 1,   "max": 20,   "default": 4,    "step": 1,   "float": False},
    ],
    "Fiscal Expansion": [
        {"name": "pct",               "label": "Spending increase (%)",     "min": 0.1, "max": 5.0,  "default": 1.0,  "step": 0.1, "float": True},
        {"name": "duration_quarters", "label": "Duration (quarters)",        "min": 1,   "max": 20,   "default": 8,    "step": 1,   "float": False},
    ],
    "Fiscal Consolidation": [
        {"name": "pct",               "label": "Spending cut (%)",          "min": 0.1, "max": 5.0,  "default": 1.0,  "step": 0.1, "float": True},
        {"name": "duration_quarters", "label": "Duration (quarters)",        "min": 1,   "max": 20,   "default": 8,    "step": 1,   "float": False},
    ],
    "Oil Price Shock": [
        {"name": "pct_change",        "label": "Oil price increase (%)",    "min": 5.0, "max": 200.0,"default": 50.0, "step": 5.0, "float": True},
        {"name": "duration_quarters", "label": "Duration (quarters)",        "min": 1,   "max": 20,   "default": 4,    "step": 1,   "float": False},
    ],
    "Productivity Shock": [
        {"name": "pct",               "label": "TFP increase (%)",          "min": 0.1, "max": 5.0,  "default": 1.0,  "step": 0.1, "float": True},
        {"name": "duration_quarters", "label": "Duration (quarters)",        "min": 1,   "max": 20,   "default": 8,    "step": 1,   "float": False},
    ],
    "Demand Shock": [
        {"name": "pct",               "label": "Demand increase (%)",       "min": 0.1, "max": 5.0,  "default": 1.0,  "step": 0.1, "float": True},
        {"name": "duration_quarters", "label": "Duration (quarters)",        "min": 1,   "max": 20,   "default": 4,    "step": 1,   "float": False},
    ],
}
