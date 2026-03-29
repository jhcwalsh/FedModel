"""
streamlit_app.py — FRB/US Macroeconomic Scenario Builder

Run with:
    streamlit run app/streamlit_app.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import streamlit as st

from app.runner import (
    model_available,
    load_model,
    load_longbase,
    run_simulation,
    OUTPUT_SERIES,
    DEFAULT_START,
)
from app.scenarios import SCENARIO_BUILDERS, SCENARIO_PARAMS
from app.charts import summary_grid, tab_charts

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="FRB/US Scenario Builder",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
[data-testid="stSidebar"] { background: #F9FAFB; }
h1 { font-size: 1.6rem !important; }
h2 { font-size: 1.2rem !important; color: #374151; }
.stTabs [data-baseweb="tab"] { font-size: 0.85rem; }
</style>
""", unsafe_allow_html=True)


# ── Cached resources ─────────────────────────────────────────────────────────
@st.cache_resource(show_spinner="Loading LONGBASE data…")
def get_data():
    return load_longbase()


@st.cache_resource(show_spinner="Loading FRB/US model (VAR)…")
def get_model_var():
    return load_model(mce=False)


@st.cache_resource(show_spinner="Loading FRB/US model (MCE)…")
def get_model_mce():
    return load_model(mce=True)


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🏛️ FRB/US Model")
    st.caption("Federal Reserve Board — US Macroeconomic Model")
    st.divider()

    if not model_available():
        st.warning(
            "**Model files not found.**\n\n"
            "Download PyFRB/US + LONGBASE from:\n"
            "https://www.federalreserve.gov/econres/us-models-python.htm\n\n"
            "Extract zip to project root, copy LONGBASE.TXT → `pyfrbus/data/`.",
            icon="⚠️",
        )
        st.stop()

    # Expectations mode — controls which model instance is used
    st.subheader("Expectations")
    expectations_mode = st.radio(
        "Formation",
        options=["VAR-based", "Model-consistent (MCE)"],
        index=0,
        help=(
            "VAR-based: agents use historical patterns to form expectations (faster).\n"
            "MCE: fully rational forward-looking expectations (slower, ~2-5 min)."
        ),
    )
    use_mce = expectations_mode == "Model-consistent (MCE)"
    if use_mce:
        st.caption("MCE simulations may take 2-5 minutes.")

    st.divider()

    # Scenario selector
    st.subheader("Scenario")
    scenario_type = st.selectbox("Shock type", options=list(SCENARIO_BUILDERS.keys()))

    # Dynamic parameter sliders
    param_values = {}
    params = SCENARIO_PARAMS.get(scenario_type, [])
    if params:
        st.markdown("**Parameters**")
        for p in params:
            if p.get("float"):
                val = st.slider(p["label"], min_value=float(p["min"]), max_value=float(p["max"]),
                                value=float(p["default"]), step=float(p["step"]))
            else:
                val = st.slider(p["label"], min_value=int(p["min"]), max_value=int(p["max"]),
                                value=int(p["default"]), step=int(p["step"]))
            param_values[p["name"]] = val

    st.divider()

    # Simulation horizon
    st.subheader("Simulation")
    horizon = st.slider("Forecast horizon (quarters)", min_value=4, max_value=40, value=20, step=4)

    start_str = st.text_input("Start quarter", value=str(DEFAULT_START),
                              help="e.g. 2026Q1 — must be within LONGBASE range")
    try:
        sim_start = pd.Period(start_str, freq="Q")
    except Exception:
        st.error("Invalid quarter format. Use e.g. 2026Q1")
        st.stop()

    st.divider()

    chart_mode = st.radio("Chart display",
                          options=["Deviation from baseline", "Level path"], index=0)
    mode = "deviation" if "Deviation" in chart_mode else "level"

    st.divider()
    run_btn = st.button("▶  Run Simulation", type="primary", use_container_width=True)


# ── Main panel ────────────────────────────────────────────────────────────────
st.title("FRB/US Macroeconomic Scenario Builder")

builder = SCENARIO_BUILDERS[scenario_type]
scenario = builder(**param_values)

c1, c2 = st.columns([3, 1])
with c1:
    st.markdown(f"**Scenario:** {scenario.label}")
    st.caption(scenario.description)
with c2:
    st.caption(f"Expectations: {expectations_mode}")
    st.caption(f"Start: {sim_start} | Horizon: {horizon}Q")

st.divider()

if "results" not in st.session_state:
    st.session_state.results = None
if "last_label" not in st.session_state:
    st.session_state.last_label = None

if run_btn:
    try:
        data = get_data()
        model = get_model_mce() if use_mce else get_model_var()

        sim_end = sim_start + horizon - 1
        shock_end = sim_start + scenario.shock_duration - 1

        with st.spinner(f"Running {scenario.label}…"):
            baseline, shocked = run_simulation(
                model=model,
                data=data,
                start=sim_start,
                end=sim_end,
                aerr_shocks=scenario.aerr_shocks,
                shock_end=shock_end,
            )

        st.session_state.results = (baseline, shocked)
        st.session_state.last_label = scenario.label
        st.success(f"Complete: {scenario.label}", icon="✅")

    except FileNotFoundError as e:
        st.error(str(e))
    except ImportError:
        st.error("pyfrbus not found — extract the Fed zip to the project root so `pyfrbus/` is present.")
    except Exception as e:
        st.error(f"Simulation failed: {e}")
        st.exception(e)

# ── Results ───────────────────────────────────────────────────────────────────
if st.session_state.results is not None:
    baseline, shocked = st.session_state.results

    st.subheader(f"Results — {st.session_state.last_label}")
    st.plotly_chart(summary_grid(baseline, shocked), use_container_width=True)

    tabs = st.tabs(list(OUTPUT_SERIES.keys()))
    for tab, group_name in zip(tabs, OUTPUT_SERIES.keys()):
        with tab:
            charts = tab_charts(baseline, shocked, group_name, mode=mode)
            if not charts:
                st.info(f"No {group_name} variables available.")
                continue
            for i in range(0, len(charts), 2):
                cols = st.columns(2)
                for j, (lbl, fig) in enumerate(charts[i: i + 2]):
                    with cols[j]:
                        st.plotly_chart(fig, use_container_width=True)

    with st.expander("Raw data"):
        st.markdown("**Baseline**")
        st.dataframe(baseline, use_container_width=True)
        st.markdown("**Shocked**")
        st.dataframe(shocked, use_container_width=True)
        st.markdown("**Deviation**")
        st.dataframe(shocked - baseline, use_container_width=True)

else:
    st.info("Configure your scenario in the sidebar and click **▶ Run Simulation**.", icon="ℹ️")
    st.markdown("""
### About FRB/US

The **FRB/US model** is the Federal Reserve Board's large-scale macroeconomic model of the US
economy, in use since 1996. It contains ~60 stochastic equations, ~320 identities, and
~125 exogenous variables across 11 economic sectors.

**Shocks are applied via equation add-factors (`_aerr` variables):**

| Scenario | Add-factor | Interpretation |
|---|---|---|
| Monetary Tightening/Easing | `rffintay_aerr` | Override on inertial Taylor rule |
| Fiscal Expansion/Consolidation | `egfet_aerr` | Federal total expenditure shock |
| Oil Price Shock | `poilr_aerr` | Real oil price shock |
| Productivity Shock | `mfpt_aerr` | Multifactor productivity shock |
| Demand Shock | `eco_aerr`, `ecd_aerr` | Consumer spending shocks |

**Expectations modes:**
- *VAR-based*: fast (~seconds); expectations from historical VAR
- *MCE*: slow (~minutes); fully model-consistent rational expectations

**Source:** [Federal Reserve — FRB/US Project](https://www.federalreserve.gov/econres/us-models-about.htm)
""")
