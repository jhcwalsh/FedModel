"""
runner.py — Wrapper around pyfrbus to load the FRB/US model and run simulations.

File layout expected (after extracting Fed zip):
  pyfrbus/models/model.xml    — model equations
  pyfrbus/data/LONGBASE.TXT   — historical + extrapolated data (not committed to git)
"""

import sys
from pathlib import Path

# Ensure pyfrbus package is importable from the project root
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd

MODEL_XML = PROJECT_ROOT / "pyfrbus" / "models" / "model.xml"
DATA_TXT = PROJECT_ROOT / "pyfrbus" / "data" / "LONGBASE.TXT"

# ── Output series shown in the UI ────────────────────────────────────────────
OUTPUT_SERIES = {
    "Output": {
        "xgdp":  "Real GDP",
        "xgap2": "Output Gap",
        "xb":    "Real GNP",
    },
    "Inflation": {
        "pcxfe": "Core PCE Inflation",
        "pic4":  "CPI Inflation (4Q)",
        "pgdp":  "GDP Deflator",
    },
    "Labor": {
        "lur":   "Unemployment Rate",
        "lep":   "Employment (Payroll)",
        "lhp":   "Aggregate Hours",
        "lprdt": "Labor Productivity",
    },
    "Financial": {
        "rff":   "Federal Funds Rate",
        "rg10":  "10yr Treasury Yield",
        "rg10p": "10yr Term Premium",
        "rrff":  "Real Federal Funds Rate",
    },
    "Fiscal": {
        "gfexpn":  "Federal Expenditures (nominal)",
        "gfrecn":  "Federal Receipts (nominal)",
        "gfsrpn":  "Federal Surplus (nominal)",
        "gfdbtnp": "Federal Debt / Potential GDP",
    },
}

ALL_SERIES = {k: v for group in OUTPUT_SERIES.values() for k, v in group.items()}

# Default simulation start (first future quarter in LONGBASE with stable extrapolation)
DEFAULT_START = pd.Period("2026Q1")

# Standard fiscal-rule switches applied every simulation
FISCAL_SWITCHES = {"dfpdbt": 0, "dfpsrp": 1}


def model_available() -> bool:
    return MODEL_XML.exists() and DATA_TXT.exists()


def load_model(mce: bool = False):
    """
    Load the FRB/US model.  Call once and cache with @st.cache_resource.

    Parameters
    ----------
    mce : bool
        True  → model-consistent expectations (mcap+wp)
        False → VAR-based expectations (default)
    """
    if not model_available():
        raise FileNotFoundError(
            f"FRB/US model files not found.\n"
            f"Expected:\n  {MODEL_XML}\n  {DATA_TXT}\n\n"
            "Download the PyFRB/US package + LONGBASE data from:\n"
            "  https://www.federalreserve.gov/econres/us-models-python.htm\n"
            "Extract the zip into the project root, then copy LONGBASE.TXT into pyfrbus/data/."
        )
    from pyfrbus.frbus import Frbus

    kwargs = {"mce": "mcap+wp"} if mce else {}
    return Frbus(str(MODEL_XML), **kwargs)


def load_longbase() -> pd.DataFrame:
    """Load the LONGBASE historical/extrapolated dataset."""
    from pyfrbus.load_data import load_data
    return load_data(str(DATA_TXT))


def run_simulation(
    model,
    data: pd.DataFrame,
    start: pd.Period,
    end: pd.Period,
    aerr_shocks: dict,          # {varname_aerr: scalar added to that period range}
    shock_end: pd.Period = None, # last quarter of shock (defaults to end)
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Run a simulation and return (baseline_df, shocked_df).

    Parameters
    ----------
    model       : Frbus instance from load_model()
    data        : LONGBASE dataframe from load_longbase()
    start       : simulation start (pd.Period)
    end         : simulation end   (pd.Period)
    aerr_shocks : {variable_aerr: delta} — add-factor overrides applied start→shock_end
    shock_end   : last quarter of shock (default = end)

    Returns
    -------
    (baseline, shocked) — DataFrames containing OUTPUT_SERIES columns over [start:end]
    """
    shock_end = shock_end or end

    # Apply standard fiscal rule switches
    for var, val in FISCAL_SWITCHES.items():
        data.loc[start:end, var] = val

    # Baseline: init_trac only (no extra overrides, then solve is implicit in init_trac)
    baseline = model.init_trac(start, end, data)

    # Shocked: copy baseline tracking solution, then apply add-factor shocks
    shocked = baseline.copy()
    for var, delta in aerr_shocks.items():
        if var in shocked.columns:
            shocked.loc[start:shock_end, var] += delta

    shocked = model.solve(start, end, shocked)

    available = [v for v in ALL_SERIES if v in baseline.columns and v in shocked.columns]
    return baseline.loc[start:end, available].copy(), shocked.loc[start:end, available].copy()
