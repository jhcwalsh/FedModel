"""
runner.py — Wrapper around pyfrbus to load the FRB/US model and run simulations.

The FRB/US model must be extracted from the Fed zip into the project root:
  - models/model.xml   (model equations)
  - models/LONGBASE.TXT (historical data — not committed to git)

pyfrbus API reference:
  from pyfrbus.frbus import Frbus
  from pyfrbus.load_data import load_data
"""

import os
import pandas as pd
from pathlib import Path

MODEL_PATH = Path(__file__).parent.parent / "models" / "model.xml"
DATA_PATH = Path(__file__).parent.parent / "models" / "LONGBASE.TXT"

# Key output series to track across all simulations
OUTPUT_SERIES = {
    "Output": {
        "xgdp": "Real GDP",
        "xgdpgap": "Output Gap",
        "xgdppotential": "Potential GDP",
    },
    "Inflation": {
        "pcxfe": "Core PCE Inflation",
        "pic4": "CPI Inflation (4Q)",
        "pgdp": "GDP Deflator",
    },
    "Labor": {
        "lur": "Unemployment Rate",
        "lex": "Employment",
        "lww": "Average Weekly Hours",
        "lxnfct": "Compensation per Hour",
    },
    "Financial": {
        "rff": "Federal Funds Rate",
        "rg10": "10yr Treasury Yield",
        "rg10p": "10yr Term Premium",
        "drxy": "Real Exchange Rate",
    },
    "Fiscal": {
        "gftrd": "Federal Spending",
        "trfpt": "Federal Tax Revenues",
        "gfdbtnipa": "Federal Deficit (NIPA)",
    },
}

# Flat mapping of variable name → label
ALL_SERIES = {k: v for group in OUTPUT_SERIES.values() for k, v in group.items()}


def model_available() -> bool:
    return MODEL_PATH.exists() and DATA_PATH.exists()


def load_model():
    """Load the FRB/US model. Call once and cache with @st.cache_resource."""
    if not model_available():
        raise FileNotFoundError(
            f"FRB/US model files not found.\n"
            f"Expected:\n  {MODEL_PATH}\n  {DATA_PATH}\n\n"
            "Please download the PyFRB/US package and LONGBASE.TXT from:\n"
            "https://www.federalreserve.gov/econres/us-models-python.htm\n"
            "and extract them into the models/ directory."
        )
    from pyfrbus.frbus import Frbus
    return Frbus(str(MODEL_PATH))


def load_longbase() -> pd.DataFrame:
    """Load LONGBASE historical dataset."""
    from pyfrbus.load_data import load_data
    return load_data(str(DATA_PATH))


def run_simulation(
    model,
    data: pd.DataFrame,
    start: str,
    end: str,
    overrides: dict,
    targ: list,
    traj: list,
    inst: list,
    mce: str = "mcap+wp",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Run a simulation and return (baseline_df, shocked_df) for output series.

    Parameters
    ----------
    model       : Frbus instance from load_model()
    data        : LONGBASE dataframe from load_longbase()
    start       : simulation start quarter, e.g. "2024Q1"
    end         : simulation end quarter, e.g. "2029Q4"
    overrides   : dict of {varname: pd.Series or scalar} applied to sim before solve
    targ        : list of target variable names (for mcontrol)
    traj        : list of trajectory variable names (for mcontrol)
    inst        : list of instrument variable names (for mcontrol)
    mce         : model-consistent expectations flag; "" for VAR-based

    Returns
    -------
    baseline    : DataFrame of baseline (no shock) values
    shocked     : DataFrame of shocked simulation values
    Both contain only the series in ALL_SERIES.
    """
    # --- Baseline (no overrides) ---
    baseline_sim = model.init_trac(start, end, data)
    if targ:
        baseline_sim = model.mcontrol(start, end, baseline_sim, targ, traj, inst, mce=mce)
    else:
        baseline_sim = model.solve(start, end, baseline_sim, mce=mce)

    # --- Shocked simulation ---
    shocked_sim = model.init_trac(start, end, data)
    for var, values in overrides.items():
        if isinstance(values, (int, float)):
            shocked_sim.loc[start:end, var] = shocked_sim.loc[start:end, var] + values
        else:
            shocked_sim.loc[start:end, var] = values

    if targ:
        shocked_sim = model.mcontrol(start, end, shocked_sim, targ, traj, inst, mce=mce)
    else:
        shocked_sim = model.solve(start, end, shocked_sim, mce=mce)

    available = [v for v in ALL_SERIES if v in baseline_sim.columns]
    return baseline_sim[available].copy(), shocked_sim[available].copy()


def get_simulation_dates(data: pd.DataFrame, horizon_quarters: int) -> tuple[str, str]:
    """Return (start, end) simulation period based on last available data + horizon."""
    last_date = data.index[-1]
    # FRB/US uses quarterly period index — convert to string
    start = str(last_date)
    # Add horizon quarters
    end_period = last_date + horizon_quarters
    end = str(end_period)
    return start, end
