# DER Financial Viability Analysis — Replicable Package

> Public reproducibility package for the Duke Nicholas School of the Environment MEM 2026 master's project on residential Distributed Energy Resources (DER) rate and tariff economics.

This repository contains the data, code, financial models, and documentation needed to reproduce **four US state-level case studies** (CA, MA, NC, TX) of residential solar-plus-storage economics under each state's prevailing rate structure. (A fifth state, NY, is held out of this initial release pending collaborator review.)

## Pipeline at a glance

The same four-step pipeline runs in every state, with state-specific rate structures and incentives plugged in at the appropriate stage:

```mermaid
flowchart TB
    %% ───── External public data sources ─────
    subgraph EXT["📥 External public data sources"]
        direction LR
        E1["NREL ResStock<br/>OEDI S3 bucket"]
        E2["NREL NSRDB<br/>GOES V4 API"]
        E3["State PUC tariff PDFs<br/>+ OpenEI URDB"]
        E4["DSIRE · IRS · utility<br/>incentive databases"]
    end

    %% ───── 1. Inputs (per state, fetched on demand) ─────
    subgraph S1["1️⃣ INPUTS — per state, fetched on demand"]
        direction TB
        F1["shared/fetch_resstock.py<br/>--state STATE"]
        F2["shared/fetch_nsrdb.py<br/>--state STATE"]
        D1["load_profile.csv<br/>8760 hours × kW"]
        D2["weather.csv<br/>GHI · DNI · DHI · T · wind"]
        D3["rate_structure<br/>buy / export / TOU per utility"]
        F1 --> D1
        F2 --> D2
    end
    E1 --> F1
    E2 --> F2
    E3 --> D3

    %% ───── 2. Simulation (PySAM module chain) ─────
    subgraph S2["2️⃣ SIMULATION — PySAM module chain"]
        direction TB
        M1["Pvwattsv8<br/>hourly PV generation kWh"]
        M2["Battwatts<br/>hourly battery dispatch"]
        M3["Utilityrate5<br/>year-1 bill with vs bill without"]
        O2["pysam_results.json<br/>year1_savings per scenario"]
        M1 --> M2 --> M3 --> O2
    end
    D2 --> M1
    D1 --> M2
    D3 --> M3

    %% ───── 3. Financial model (Excel build) ─────
    subgraph S3["3️⃣ FINANCIAL MODEL — openpyxl-built Excel"]
        direction TB
        D4["incentive_stack<br/>federal ITC · state credits<br/>· utility rebates · DR"]
        UFP["Unified financial params<br/>loan 7.24% · 25 yr · 100% debt<br/>discount 6.4% · escalation 2.5%"]
        CALC["Per-scenario 25-year cash flow<br/>PMT loan amortization<br/>+ bill savings escalation<br/>+ incentive stream<br/>+ NPV at discount rate<br/>+ simple payback"]
        X1["STATE_Financial_Model.xlsx<br/>one workbook per rate track"]
        X2["STATE_Summary_Tables.xlsx<br/>presentation-ready"]
        D4 --> CALC
        UFP --> CALC
        CALC --> X1
        CALC --> X2
    end
    E4 --> D4
    O2 --> CALC

    %% ───── 4. Cross-state comparison ─────
    subgraph S4["4️⃣ CROSS-STATE COMPARISON — apples-to-apples"]
        direction LR
        C1["CA"]
        C2["MA"]
        C3["NC"]
        C4["TX"]
        FIN["ΔNPV per policy regime<br/>what makes DER work where"]
        C1 --> FIN
        C2 --> FIN
        C3 --> FIN
        C4 --> FIN
    end
    X1 -.repeat steps 1–3 per state.-> C1 & C2 & C3 & C4

    %% ───── Styling ─────
    classDef ext fill:#f5f5f5,stroke:#757575,color:#000
    classDef fetch fill:#e1f5fe,stroke:#0277bd,color:#000
    classDef data fill:#e3f2fd,stroke:#1976d2,color:#000
    classDef sim fill:#fff3e0,stroke:#f57c00,color:#000
    classDef simout fill:#ffe0b2,stroke:#ef6c00,color:#000
    classDef fin fill:#f3e5f5,stroke:#7b1fa2,color:#000
    classDef finout fill:#e1bee7,stroke:#6a1b9a,color:#000
    classDef cmp fill:#e8f5e9,stroke:#388e3c,color:#000
    classDef cmpfinal fill:#c8e6c9,stroke:#1b5e20,color:#000
    class E1,E2,E3,E4 ext
    class F1,F2 fetch
    class D1,D2,D3,D4 data
    class M1,M2,M3 sim
    class O2 simout
    class UFP,CALC fin
    class X1,X2 finout
    class C1,C2,C3,C4 cmp
    class FIN cmpfinal
```

The unified parameters in stage 3 are what make cross-state comparison apples-to-apples: any ΔNPV between states reflects policy + rate differences, not financing assumptions. See [`docs/parameters.md`](docs/parameters.md) for full sourcing.

---

## What's inside

| Path | Contents |
|---|---|
| `case_studies/{CA,MA,NC,TX}/` | Per-state inputs, code, financial models, outputs, sources |
| `shared/` | NSRDB weather + NREL ResStock load-profile fetch utilities |
| `docs/` | Cross-state methodology and unified parameter table |
| `WORKFLOW.md` | Original four-step methodology document |
| `AGENTS.md` | Runbook for AI agents (Claude Code, Codex, etc.) reproducing the analyses |

## Quick start

```bash
# 1. Clone
git clone https://github.com/zl396/DER-Financial-Viability-Analysis-Replicable-Package-Duke-NSOE-MEM-2026.git
cd DER-Financial-Viability-Analysis-Replicable-Package-Duke-NSOE-MEM-2026

# 2. Install Python deps (Python 3.11+ recommended; conda preferred on Apple Silicon for PySAM)
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 3. Add your free NSRDB API key
cp .env.example .env
# Edit .env: register at https://developer.nrel.gov/signup/, paste your key + email

# 4. Fetch raw inputs for one state (e.g. NC, the smallest)
python shared/fetch_resstock.py --state NC
python shared/fetch_nsrdb.py  --state NC

# 5. Build the financial model (writes Excel under case_studies/NC/Financial Models/)
python "case_studies/NC/Financial Models/build_model.py"
```

See [`AGENTS.md`](AGENTS.md) for the full per-state pipeline and `docs/` for the methodology.

## Methodology summary

For each state, the unified pipeline is:

1. **Inputs** — representative residential load profile (NREL ResStock, fetched on demand), hourly weather (NSRDB, fetched on demand), state utility rate structure (URDB + tariff PDFs), incentive programs.
2. **Simulation** — PySAM `Pvwattsv8` + `Battwatts` + `Utilityrate5` for hourly PV generation, battery dispatch, and bill-with vs. bill-without calculations.
3. **Financial model** — 25-year cash flow with NPV under unified parameters: 7.24% loan rate, 25-year term, 6.4% customer discount rate, 2.5% electricity escalation, 100% debt financing.
4. **Verification** — each rate track uses its own bill-without as the savings baseline (the most common error source documented in `WORKFLOW.md`).

See `docs/methodology.md` for full details and `docs/parameters.md` for the unified parameter table with sources.

## State coverage

| State | Utility(ies) | Rate Tracks | Status |
|---|---|---|---|
| CA | PG&E, SCE, SDG&E | NEM 3.0 (ACC export) | Complete |
| MA | Eversource, National Grid | Flat NEM, TOU 2035 sensitivity, ConnectedSolutions DR | Complete |
| NC | Duke Energy Carolinas | NMB (flat) + RSC (TOU); TOBF financing analysis | Complete |
| TX | Oncor + retail providers | Net billing (deregulated); ERCOT VPP sensitivity | Complete |

## Data not included in this repo

To keep the repository under 50 MB, **two large public datasets are fetched on demand** rather than committed:

- **NREL ResStock End Use Load Profiles** — fetched by `shared/fetch_resstock.py`. Public, free.
- **NSRDB hourly weather data** — fetched by `shared/fetch_nsrdb.py`. Free with an API key.

Per-state derived summaries (representative profiles, monthly aggregates) **are** committed for reproducibility verification.

## Reproducibility for AI agents

This repo is designed so that an AI agent (e.g., Claude Code, Codex) can clone it, read `AGENTS.md`, and reproduce every analysis end-to-end without further human guidance. See `AGENTS.md` for the full runbook, expected outputs, and self-verification checks.

## Citation

If you use this package, please cite as:

> Duke Nicholas School of the Environment, MEM 2026 master's project — DER Financial Viability Analysis Replicable Package. https://github.com/<your-org>/DER-Financial-Viability-Analysis-Replicable-Package-Duke-NSOE-MEM-2026

## License

MIT — see `LICENSE`. You may use, modify, and redistribute the code, models, and documentation with attribution. Note: third-party datasets fetched at runtime (NREL ResStock, NSRDB) carry their own license terms; consult the original sources.
