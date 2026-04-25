# DER Financial Analysis — General Workflow

> Master workflow for all state case studies. Read this file (and `AGENTS.md` for the AI-agent runbook) before starting a new pipeline run.

---

For the high-level data-flow diagram, see the [Pipeline at a glance](README.md#pipeline-at-a-glance) section in the top-level `README.md`. This document is the detailed step-by-step checklist that fills in each stage.

---

## State Parameters Table

| Parameter | NC | MA | CA | TX |
|-----------|----|----|----|-----|
| **PV Capacity (kW)** | 5.77 | 4.72 | 6.05 | 5.95 |
| **Solar $/kW** | $3,040 | $3,540 | $2,860 | $2,770 |
| **Battery $/kWh** | $1,214 | $1,488 | TBD | $1,102 |
| **Rate Structure** | NMB (flat+avoided cost) / RSC (TOU+CPP) | Flat NEM / E3 TOU sensitivity | NEM 3.0 (ACC-based) | Net billing (deregulated) |
| **Primary Utility** | Duke Energy Carolinas | Eversource, NGrid | PG&E, SCE, SDG&E | Oncor, CenterPoint |
| **Federal ITC (2026)** | 0% | 0% | 0% (homeowner) | 0% (homeowner) |
| **State Solar Credit** | None | 15%, $1K cap | None (SGIP for storage) | None |
| **Net Metering** | NMB (3.4¢ avoided cost export) | 1:1 retail NEM | NEM 3.0 (ACC-based) | Varies by retailer |
| **Storage Program** | EnergyWise $277/yr | ConnectedSolutions $1,375/yr | SGIP | None |
| **Status** | ✅ Complete | ✅ Complete | ✅ Complete | ✅ Complete |

**Cost source:** Tao Sun et al. (2025), Supplementary Table 15, state-level $/kW and $/kWh. Cross-reference: SAM default ($3.16/W solar, $1,144/kWh battery all-in national average).

---

## Step 1: Inputs — Detailed Checklist

### 1a. System Specifications
- [ ] PV capacity: use state median from table above
- [ ] Battery: 13.5 kWh / 5 kW (Tesla Powerwall) as baseline
- [ ] System costs: Tao Sun Supplementary Table 15 for state-level $/kW and $/kWh
- [ ] Solar total = $/kW × kW; Battery total = $/kWh × kWh; PV+S = sum

### 1b. Load Profile
- [ ] Check if ResStock aggregate exists in `{State} Scenarios/{state} load profile/outputs/`
- [ ] If not, request from ChatGPT or generate with SAM BELPE module
- [ ] ResStock profiles preferred over BELPE synthetic profiles
- [ ] Document: source, annual kWh, peak kW

### 1c. Weather Data
- [ ] Download from NSRDB: `nsrdb-GOES-aggregated-v4-0-0-download.csv`
- [ ] If sandbox can't download (S3 blocked), give user the URL to download manually
- [ ] API key + Email: register your own free key at https://developer.nrel.gov/signup/. Set in `.env` as `NSRDB_API_KEY` and `NSRDB_EMAIL` (see `.env.example`).
- [ ] Save to `{State} Scenarios/PySAM_outputs/{state}_{city}_{year}_hourly.csv`

### 1d. Rate Structures
- [ ] Identify primary utility(ies) for the state
- [ ] Find current residential rate schedule: utility website → tariff PDF
- [ ] Verify with URDB (OpenEI): `https://apps.openei.org/USURDB/`
- [ ] Document: volumetric rate, fixed charge, TOU periods, demand charges
- [ ] Document: net metering / net billing rules and export compensation rate
- [ ] **CRITICAL: Each rate track must use its OWN bill w/o as baseline for savings**
  - If customer is on flat rate, bill w/o = flat rate × load
  - If customer is on TOU, bill w/o = TOU rate × load (will be different from flat)
  - Do NOT use flat rate bill w/o as baseline for TOU scenarios

### 1e. Incentives
- [ ] Federal ITC: 0% for homeowner-owned (expired Dec 2025)
- [ ] State tax credits (verify cap, carryforward)
- [ ] Utility rebates (solar + battery, verify if funded)
- [ ] Performance/DR programs (ConnectedSolutions, EnergyWise, etc.)
- [ ] Document: amount, term, lock period, regulatory source
- [ ] All incentive data must have verifiable source

### 1f. Financial Parameters (Unified across all states)
- Loan interest rate: 7.24%
- Loan term: 25 years
- Customer discount rate: 6.4%
- Electricity cost escalation: 2.5%/yr
- 100% debt financing (no upfront customer outlay)

---

## Step 2: PySAM Simulation

### PySAM Bootstrap (required in sandbox)
```python
import sys, os
pkg_dir = '/opt/anaconda3/lib/python3.12/site-packages/PySAM'
sys.path.insert(0, '/opt/anaconda3/lib/python3.12/site-packages')
sys.modules['PySAM'] = type(sys)('PySAM')
sys.modules['PySAM'].__path__ = [pkg_dir]
sys.modules['PySAM'].__file__ = os.path.join(pkg_dir, '__init__.py')
```

If this fails (pysam genomics conflict), user must run: `pip uninstall pysam`

### Module Chain
```
Pvwattsv8 (solar generation)
    → Battwatts (battery dispatch, if PV+Storage)
    → Utilityrate5 (bill calculation per rate scenario)
```

### Utilityrate5 Configuration Notes
- `ur_ec_tou_mat`: (period, tier, max_usage, max_demand, buy_rate, sell_rate). Periods 1-indexed.
- `ur_ec_sched_weekday/weekend`: 12×24 matrix. Values = period numbers matching tou_mat.
- `ur_metering_option`: 0=NEM, 3=Net Billing Instantaneous
- **CRITICAL: For flat rate, must reset schedule to all-1s.** `ur.default()` comes with a multi-period schedule. If you set a single-period tou_mat without resetting the schedule, it will error.
```python
FLAT_SCHED = tuple(tuple([1]*24) for _ in range(12))
u.ElectricityRates.ur_ec_sched_weekday = FLAT_SCHED
u.ElectricityRates.ur_ec_sched_weekend = FLAT_SCHED
```

### Output
- Save to `{State} Scenarios/{State} Results for Upload/{state}_pysam_results_v3.json`
- Must include: bill_with_system, bill_without_system, year1_savings per config
- Metadata: PV annual kWh, load annual kWh, system costs, rate source

---

## Step 3: Excel Financial Models

### Structure
- **Inputs sheet**: all parameters, blue=input, black=formula, source annotations
- **Cash flow sheets**: one per rate track, 4 scenario blocks each
- **Each scenario block rows**: Debt Balance, Interest, Principal, P&I, Bill w/o, Bill w/, Bill Savings, Incentive Annual, Total Savings, Net Savings, Cumulative NPV, Simple Payback

### NPV Calculation Method (100% Debt Financed)
```
Cumulative NPV = sum of (net_savings / (1+discount)^year) for years 1-25
where net_savings = bill_savings + incentives - PMT
NO Year 0 investment outflow (100% debt financed)
```

This differs from textbook NPV which includes Year 0 = -investment. Our customers pay $0 upfront; all cost flows through the 25-year PMT.

### Simple Payback
```
Simple Payback = Initial Debt / (Y1 Bill Savings + Y1 Annual Incentives)
```

### Incentive Term Rules
- SMART (MA): 20 years, not 25 (225 CMR 28.13(1))
- ConnectedSolutions (MA): 5 years locked, then assumption ($1,375/yr)
- EnergyWise (NC): $277/yr, no stated term limit
- PowerPair (NC): one-time upfront rebate (reduces debt)

### Baseline Rule
**Each rate track uses its OWN bill w/o as baseline.**
- NMB savings = NMB bill w/o − NMB bill w/ system
- RSC savings = RSC bill w/o − RSC bill w/ system
- TOU savings = TOU bill w/o − TOU bill w/ system
- Do NOT cross-compare baselines across rate tracks

### Summary Tables
- Generate from JSON source data programmatically. NEVER hand-type numbers.
- Include: Guide sheet explaining every column, data table(s), takeaway sentence(s)
- Columns: Scenario, Rate Track, Bill Savings Y1, Monthly Net, 25yr NPV, NPV Breakeven Yr, Simple Payback
- Color coding: green=positive, red=negative for Monthly Net and NPV

### Quality Checklist
- [ ] Bill w/o system identical across Solar Only and PV+Storage for same utility AND rate track
- [ ] Each rate track uses its own bill w/o baseline
- [ ] PMT computed from initial debt, not current balance
- [ ] Incentive terms match regulatory source
- [ ] NPV uses discount rate (6.4%), not interest rate (7.24%)
- [ ] NPV has no Year 0 outflow (100% debt financed)
- [ ] Summary Tables generated from JSON, not hand-typed
- [ ] Simple Payback included in both financial models and summary tables

---

## Step 4: Verification & Deliverables

### Evaluator Checklist
- [ ] PySAM year1_savings = bill_wo - bill_w (for each track's OWN baseline)
- [ ] Python NPV calculation matches Summary Table NPV within $5
- [ ] Python Monthly Net matches Summary Table within $1
- [ ] Excel Inputs sheet values match JSON source data
- [ ] RSC/TOU savings < flat NEM savings for solar (if solar produces during off-peak)

### Output Files (per state)
```
{State} Results for Upload/
├── {state}_pysam_results_v3.json        ← PySAM source data
├── {state}_financial_summary.json       ← Verified financial calculations
├── {State}_Financial_Model_{Track1}.xlsx ← Financial model per rate track
├── {State}_Financial_Model_{Track2}.xlsx ← (if multiple tracks)
├── {State}_Summary_Tables.xlsx          ← Guide + presentation tables
└── {State}_Workflow_Replicable.md       ← State-specific parameters + sources
```

---

For per-state findings and rate-track details, see each `case_studies/{XX}/README.md`.
