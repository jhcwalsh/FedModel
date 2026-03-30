# FedModel — FRB/US Macroeconomic Scenario Builder

A Streamlit application for running economic shock simulations using the Federal Reserve Board's **FRB/US** macroeconomic model of the US economy.

---

## What is FRB/US?

FRB/US is the Federal Reserve Board's large-scale estimated general equilibrium model of the US economy, in continuous use since 1996. It contains:

- ~60 stochastic equations (estimated behavioural relationships)
- ~320 accounting identities (national accounts, sector balances)
- ~125 exogenous variables (policy settings, foreign conditions)

It covers all major components of GDP, the labour market, prices, financial conditions, and the fiscal sector.

---

## Project Structure

```
FedModel/
├── app/
│   ├── streamlit_app.py   # Main Streamlit UI entry point
│   ├── runner.py          # pyfrbus wrapper: load model, run simulations
│   ├── scenarios.py       # Shock scenario definitions and parameter metadata
│   └── charts.py          # Plotly chart builders (impulse response, level path)
├── pyfrbus/               # FRB/US Python package (from Fed zip)
│   ├── models/
│   │   └── model.xml      # Model equations
│   ├── data/
│   │   └── LONGBASE.TXT   # Historical + extrapolated data (not in git)
│   ├── demos/             # Fed-provided example scripts
│   └── pyfrbus/           # Python solver library
├── requirements.txt
└── README.md
```

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/jhcwalsh/FedModel.git
cd FedModel
```

### 2. Download the Fed model files (required — cannot be automated)

Go to: **https://www.federalreserve.gov/econres/us-models-python.htm**

Download both:
- **PyFRB/US package** (zip) — extract into the project root so `pyfrbus/` appears at the top level
- **Data package** (zip) — copy `LONGBASE.TXT` into `pyfrbus/data/`

### 3. Install dependencies

Install the `pyfrbus` package and app dependencies:

```bash
pip install -e pyfrbus/
pip install -r requirements.txt
```

### 4. Run the app

```bash
streamlit run app/streamlit_app.py
```

The app will open at `http://localhost:8501`.

---

## Available Scenarios

| Scenario | Shock Variable | Description |
|---|---|---|
| Monetary Tightening | `rffintay_aerr` | Raises FFR above the inertial Taylor rule |
| Monetary Easing | `rffintay_aerr` | Lowers FFR below the inertial Taylor rule |
| Fiscal Expansion | `egfet_aerr` | Increases federal total expenditure |
| Fiscal Consolidation | `egfet_aerr` | Reduces federal total expenditure |
| Oil Price Shock | `poilr_aerr` | Raises the real oil price |
| Productivity Shock | `mfpt_aerr` | Raises multifactor productivity trend |
| Demand Shock | `eco_aerr`, `ecd_aerr` | Consumer spending shock |

Shocks are applied via equation **add-factors** (`_aerr` variables), which override the model's endogenous tracking residuals.

---

## Expectations Modes

- **VAR-based** (default, fast — seconds): households and firms form expectations using a vector autoregression estimated on historical data.
- **Model-consistent / MCE** (slow — 2-5 minutes): fully rational forward-looking expectations consistent with the model solution.

The mode is selected in the sidebar and loads a separate cached model instance.

---

## Output Variables

| Tab | Variables |
|---|---|
| Output | Real GDP, Output Gap, Real GNP |
| Inflation | Core PCE, CPI (4Q), GDP Deflator |
| Labor | Unemployment, Payroll Employment, Hours, Productivity |
| Financial | Federal Funds Rate, 10yr Yield, Term Premium, Real FFR |
| Fiscal | Federal Expenditures, Receipts, Surplus, Debt/Potential GDP |

Results are shown as **impulse response functions** (deviation from baseline) or **level paths**, selectable in the sidebar.

---

## Source

Federal Reserve Board — FRB/US Project:
https://www.federalreserve.gov/econres/us-models-about.htm
