"""
streamlit_app.py — FRB/US Macroeconomic Scenario Builder

Run with:
    streamlit run app/streamlit_app.py
"""

import sys
from pathlib import Path

# Ensure project root is on the path so pyfrbus and app/ are importable
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd

from app.runner import (
    model_available,
    load_model,
    load_longbase,
    run_simulation,
    OUTPUT_SERIES,
)
from app.scenarios import SCENARIO_BUILDERS, SCENARIO_PARAMS
from app.charts import summary_grid, tab_charts

# ── Page config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="FRB/US Scenario Builder",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS (minimal, clean) ──────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stSidebar"] { background: #F9FAFB; }
h1 { font-size: 1.6rem !important; }
h2 { font-size: 1.2rem !important; color: #374151; }
.stTabs [data-baseweb="tab"] { font-size: 0.85rem; }
.model-missing { background: #FEF3C7; border-left: 4px solid #D97706;
                 padding: 1rem; border-radius: 4px; margin-bottom: 1rem; }
</style>
""", unsafe_allow_html=True)


# ── Model loading (cached) ────────────────────────────────────────────────────
@st.cache_resource(show_spinner="Loading FRB/US model…")
def get_model():
    return load_model()


@st.cache_resource(show_spinner="Loading LONGBASE data…")
def get_data():
    return load_longbase()


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🏛️ FRB/US Model")
    st.caption("Federal Reserve Board — US Macroeconomic Model")
    st.divider()

    # Model availability check
    if not model_available():
        st.warning(
            "**Model files not found.**\n\n"
            "Download the PyFRB/US package and LONGBASE.TXT from the Federal Reserve:\n\n"
            "https://www.federalreserve.gov/econres/us-models-python.htm\n\n"
            "Extract into `models/` in the project root.",
            icon="⚠️",
        )
        st.stop()

    st.subheader("Scenario")
    scenario_type = st.selectbox(
        "Shock type",
        options=list(SCENARIO_BUILDERS.keys()),
        help="Select the type of economic shock to simulate.",
    )

    # Dynamic parameter sliders for selected scenario
    param_values = {}
    params = SCENARIO_PARAMS.get(scenario_type, [])
    if params:
        st.markdown("**Parameters**")
        for p in params:
            if isinstance(p["default"], float):
                val = st.slider(
                    p["label"],
                    min_value=float(p["min"]),
                    max_value=float(p["max"]),
                    value=float(p["default"]),
                    step=float(p["step"]),
                )
            else:
                val = st.slider(
                    p["label"],
                    min_value=int(p["min"]),
                    max_value=int(p["max"]),
                    value=int(p["default"]),
                    step=int(p["step"]),
                )
            param_values[p["name"]] = val

    st.divider()

    st.subheader("Simulation")
    horizon = st.slider(
        "Forecast horizon (quarters)",
        min_value=4, max_value=40, value=20, step=4,
        help="Number of quarters to simulate after the shock.",
    )

    expectations_mode = st.radio(
        "Expectations formation",
        options=["VAR-based", "Model-consistent"],
        index=0,
        help=(
            "VAR-based: households/firms use historical patterns.\n"
            "Model-consistent: fully rational forward-looking expectations."
        ),
    )
    mce = "mcap+wp" if expectations_mode == "Model-consistent" else ""

    st.divider()

    chart_mode = st.radio(
        "Chart display",
        options=["Deviation from baseline", "Level path"],
        index=0,
    )
    mode = "deviation" if chart_mode == "Deviation from baseline" else "level"

    st.divider()
    run_btn = st.button("▶  Run Simulation", type="primary", use_container_width=True)


# ── Main panel ────────────────────────────────────────────────────────────────
st.title("FRB/US Macroeconomic Scenario Builder")

# Build the scenario object to show description before running
builder = SCENARIO_BUILDERS[scenario_type]
scenario = builder(**param_values)

col1, col2 = st.columns([3, 1])
with col1:
    st.markdown(f"**Scenario:** {scenario.label}")
    st.caption(scenario.description)
with col2:
    st.caption(f"Expectations: {expectations_mode}")
    st.caption(f"Horizon: {horizon}Q")

st.divider()

# Session state for results
if "results" not in st.session_state:
    st.session_state.results = None
if "last_scenario" not in st.session_state:
    st.session_state.last_scenario = None

if run_btn:
    try:
        model = get_model()
        data = get_data()

        # Determine simulation window
        last_obs = data.index[-1]
        start = str(last_obs)
        # Simple quarter arithmetic for pandas PeriodIndex
        end = str(data.index[-1] + horizon)

        with st.spinner(f"Running {scenario.label}…"):
            baseline, shocked = run_simulation(
                model=model,
                data=data,
                start=start,
                end=end,
                overrides=scenario.overrides,
                targ=scenario.targ,
                traj=scenario.traj,
                inst=scenario.inst,
                mce=mce,
            )

        st.session_state.results = (baseline, shocked)
        st.session_state.last_scenario = scenario.label
        st.success(f"Simulation complete: {scenario.label}", icon="✅")

    except FileNotFoundError as e:
        st.error(str(e))
    except ImportError:
        st.error(
            "**pyfrbus not found.** Make sure you have extracted the FRB/US Python package "
            "into the project root so that `pyfrbus/` is available."
        )
    except Exception as e:
        st.error(f"Simulation failed: {e}")

# ── Results display ───────────────────────────────────────────────────────────
if st.session_state.results is not None:
    baseline, shocked = st.session_state.results
    label = st.session_state.last_scenario

    st.subheader(f"Results — {label}")

    # Summary 4-panel grid at top
    st.plotly_chart(summary_grid(baseline, shocked), use_container_width=True)

    # Per-group tabs
    tab_names = list(OUTPUT_SERIES.keys())
    tabs = st.tabs(tab_names)

    for tab, group_name in zip(tabs, tab_names):
        with tab:
            charts = tab_charts(baseline, shocked, group_name, mode=mode)
            if not charts:
                st.info(f"No {group_name} variables available in this simulation.")
                continue

            # 2-column grid
            for i in range(0, len(charts), 2):
                cols = st.columns(2)
                for j, (lbl, fig) in enumerate(charts[i: i + 2]):
                    with cols[j]:
                        st.plotly_chart(fig, use_container_width=True)

    # Raw data expander
    with st.expander("Raw simulation data"):
        st.markdown("**Baseline**")
        st.dataframe(baseline, use_container_width=True)
        st.markdown("**Shocked**")
        st.dataframe(shocked, use_container_width=True)
        st.markdown("**Deviation (shocked − baseline)**")
        dev = shocked - baseline
        st.dataframe(dev, use_container_width=True)

else:
    # Placeholder before first run
    st.info(
        "Configure your scenario in the sidebar and click **▶ Run Simulation** to begin.",
        icon="ℹ️",
    )
    st.markdown("""
### About FRB/US

The **FRB/US model** is the Federal Reserve Board's large-scale macroeconomic model of the
US economy, in continuous use since 1996. It contains approximately:

- **~60 stochastic equations** — estimated behavioural relationships
- **~320 accounting identities** — national accounts, sector balances
- **~125 exogenous variables** — policy settings, foreign conditions

**Available scenarios in this app:**

| Scenario | Shock Variable | Description |
|---|---|---|
| Monetary Tightening | `rffintay` | Federal funds rate add-factor |
| Monetary Easing | `rffintay` | Federal funds rate add-factor |
| Fiscal Expansion | `egfos` | Federal spending add-factor |
| Fiscal Consolidation | `egfos` | Federal spending add-factor |
| Oil Price Shock | `epoil` | Real oil price add-factor |
| Productivity Shock | `lurnat` | Natural unemployment rate proxy |

**Expectations modes:**
- *VAR-based*: households and firms form expectations using historical VAR patterns
- *Model-consistent*: fully rational forward-looking (RE) expectations

**Source:** [Federal Reserve — FRB/US Project](https://www.federalreserve.gov/econres/us-models-about.htm)
""")
