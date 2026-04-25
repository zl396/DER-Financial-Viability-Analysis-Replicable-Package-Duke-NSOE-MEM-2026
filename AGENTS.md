# AGENTS.md — Runbook for AI Agents

> If you are an AI agent (Claude Code, Codex, etc.) reproducing this repository's analyses, **read this file completely before running anything**.
> A human reading this file should also find it useful, but its purpose is to give a fresh agent everything it needs without back-and-forth.

---

## 0. What this repository is for

A reproducibility package for four US state-level case studies (CA, MA, NC, TX) on residential solar-plus-storage economics under each state's prevailing rate structure. Each case study runs the same four-step pipeline (inputs → PySAM simulation → Excel financial model → verification) with state-specific parameters.

**Your goal**, when the user asks you to "reproduce" a state: run the pipeline from raw inputs to the final Excel model and verify the outputs match the committed baseline within float tolerance.

## 1. Hard rules — do not violate

1. **Never commit the `.env` file** — it contains *your* NSRDB API key (whatever you registered at https://developer.nrel.gov/signup/). Treat it as personal credentials. `.gitignore` already excludes it; do not bypass.
2. **Never write to anything outside this repo's working tree** — staging or system directories are off-limits.
3. **Do not modify the committed Excel reference models** in `case_studies/*/Financial Models/*.xlsx` or `case_studies/*/{State} Results for Upload/*.xlsx`. They are deliverables, not scratch space. To experiment, copy them first.
4. **Do not invent your own load profiles or rate parameters.** Use the values in the per-state README (sourced from regulatory filings and NREL data). If a parameter is missing or seems wrong, *stop and ask the user* — do not improvise.
5. **If PySAM output and the Excel model disagree, trust the Excel model.** It is the deliverable; PySAM is an input. An agent that "fixes" a discrepancy by editing the Excel is breaking the deliverable.

## 2. Prerequisites

- Python **3.11+** (Python 3.12 also works; tested on 3.11)
- conda **or** venv (conda strongly recommended on Apple Silicon for PySAM compatibility)
- A free **NSRDB API key** — register at https://developer.nrel.gov/signup/

## 3. Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env: paste your registered NSRDB_API_KEY and NSRDB_EMAIL
```

Verify the environment:

```bash
python -c "import PySAM.Pvwattsv8, PySAM.Battwatts, PySAM.Utilityrate5; print('PySAM OK')"
python -c "import openpyxl, pandas, requests; print('deps OK')"
```

If PySAM imports fail on Apple Silicon, see *Troubleshooting* (§7).

## 4. End-to-end reproduction (per state)

The general pattern, with state code in `{XX}`:

```bash
# Step 1 — fetch raw inputs (idempotent; skipped if already cached)
python shared/fetch_resstock.py --state {XX}     # NREL ResStock load profiles
python shared/fetch_nsrdb.py --state {XX}        # NSRDB hourly weather

# Step 2 — analyze the load profile (produces representative profile + summaries)
python "case_studies/{XX}/{XX} load profile/analyze_{xx}_representative_profile.py"

# Step 3 — run PySAM (PV + battery + utility rate)
python "case_studies/{XX}/code/run_pysam.py"     # see per-state README for actual script name

# Step 4 — build the financial Excel model
python "case_studies/{XX}/Financial Models/build_{xx}_model.py"

# Step 5 — verify by inspecting the generated Excel against the JSON outputs
#   in case_studies/{XX}/PySAM_outputs/ and {XX} Results for Upload/
```

**Per-state runtime estimates** (clean run, no caching):
- NC: ~3 min (smallest)
- MA: ~3 min
- TX: ~4 min
- CA: ~6 min (3 utilities × 2 systems = 6 scenarios)

Per-state details, exact script names, and scenario counts live in each state's `README.md` (`case_studies/{XX}/README.md`).

## 5. Unified financial parameters

All four states use the same financial parameters so cross-state comparison is apples-to-apples:

| Parameter | Value | Source |
|---|---|---|
| Loan rate | 7.24% | National avg residential solar loan, 2024 |
| Loan term | 25 years | Industry standard |
| Customer discount rate | 6.4% | Risk-adjusted, residential energy |
| Electricity escalation | 2.5%/yr | Long-run EIA AEO trend |
| Debt financing | 100% | Conservative — no upfront equity |
| ITC | 30% | Federal Investment Tax Credit, IRA |
| Analysis horizon | 25 years | Match loan term + system warranty |

Full sourcing and rationale: `docs/parameters.md`. **Do not change these without user instruction** — they are the basis of cross-state comparability.

## 6. State-specific gotchas

- **CA (NEM 3.0):** Export compensation uses the Avoided Cost Calculator (ACC) hourly rates, not retail rate. Three IOUs (PG&E E-ELEC, SCE TOU-D-PRIME, SDG&E EV-TOU-5) — each must use its *own* bill-without as savings baseline.
- **MA:** SMART 3.0 incentive runs 20 years (not 25). ConnectedSolutions demand response is $1,375/yr per battery and is the dominant economic driver — not battery cost.
- **NC:** Duke Energy NMB (flat rate, 12.76¢ buy / 3.4¢ export) and RSC (TOU + 3.4¢ export) are the two rate tracks. All scenarios are NPV-negative without ITC; battery adds ~$39–58/yr incremental value (minimal). TOBF (Tariff On-Bill Financing) sub-analysis in `case_studies/NC/NC_Tariff_On_Bill_Financing/`.
- **TX:** Deregulated retail electricity market. No standard NEM; export rates are per retailer (Chariot GreenVolt + Oncor T&D modeled). VPP scenario uses ERCOT RTM 2025 prices (~$253/yr after aggregator take). Solar-only is nearly breakeven; PV+Storage NPV deeply negative without incentives.

## 7. Troubleshooting

- **`ImportError: PySAM` on macOS Apple Silicon** — `nrel-pysam` PyPI wheel sometimes has issues on arm64. Workaround: `conda install -c nrel pysam` instead.
- **NSRDB 429 rate limit** — free tier is 1,000 requests/day. The fetcher caches results in `weather_cache/`; re-runs are free.
- **NSRDB 404 on `psm3-download.csv`** — the V3 endpoint is deprecated. Use `nsrdb-GOES-aggregated-v4-0-0-download.csv` (already coded in `shared/fetch_nsrdb.py`).
- **Excel `~$Filename.xlsx` lock files** — these are created by Office while a workbook is open. Close the workbook before re-running model builders.
- **"Bill mismatch" error in verify step** — almost always means a baseline mismatch (the rate track was compared against the wrong bill-without). Reread `WORKFLOW.md` §1d.

## 8. Decision log — why these choices

- **Why MIT license?** Maximum reuse latitude for code; users can fork freely. Third-party data (NREL ResStock, NSRDB) carries its own license — consult the source.
- **Why fetch ResStock + NSRDB on demand instead of committing them?** Repo size constraint (would push to ~1 GB). Both are public, stable, and the fetch scripts cache locally.
- **Why 100% debt financing?** Conservative assumption — most realistic for households without equity capital. If the analysis is NPV-positive at 100% debt, it is a fortiori positive with any equity contribution.
- **Why 6.4% discount rate for customers (not the loan rate)?** The customer's opportunity cost (risk-adjusted retail rate of return on alternative investments) is independent of the financing rate.
- **Why no incentives in CA Phase A?** SGIP and other CA incentives have eligibility rules that vary by household. Phase A reports baseline economics; Phase C (future) layers incentives.

## 9. When to stop and ask the user

Stop and ask if you encounter any of the following:
- A parameter in this repo conflicts with a parameter in an upstream source (e.g., URDB updated a tariff).
- An Excel reference model fails to open or compute.
- A state's reproduced PySAM output deviates from the committed JSON by more than ~5% — likely a real bug, not float-precision noise.
- You need to add a new scenario, utility, or rate track not currently covered.
- Anything looks like it might leak personal information, API keys, or other credentials.

---

**Final note for agents:** This repository was deliberately scrubbed of personal API keys, email addresses, and absolute paths before publication. **The absence of a secret is the correct state.** If you find a placeholder like `${NSRDB_API_KEY}` or a missing value, do NOT try to "fix" it by adding a real value to a committed file. The right action is to set it in `.env` (gitignored) or flag the gap to whoever is running you.
