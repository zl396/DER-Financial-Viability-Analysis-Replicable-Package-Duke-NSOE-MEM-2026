# California Residential DER Financial Analysis
## Replicable Workflow & Verified Parameters

**Date:** March 24, 2026
**Authors:** Duke NSOE MEM 2026 Cohort
**Tools:** PySAM v7.1.0 (NREL), Python 3.12, openpyxl

---

## Step 1: System Specifications

| Parameter | Value | Source |
|-----------|-------|--------|
| PV Capacity | 6.05 kW DC | Tao Sun et al. (2025), CA state-level |
| Battery | 13.5 kWh / 5 kW | Tesla Powerwall equivalent |
| Tilt / Azimuth | Location-specific / 180 (south) | Latitude-optimal per utility territory |
| DC/AC Ratio | 1.2 | PySAM default |
| System Losses | 14% | PySAM default (soiling, shading, wiring) |
| Inverter Efficiency | 96% | PySAM default |

**Location-specific tilts:**

| Utility | Proxy City | Latitude | Tilt |
|---------|-----------|----------|------|
| PG&E | Sacramento | 38.58N | 39 |
| SCE | Riverside | 33.95N | 34 |
| SDG&E | San Diego | 32.72N | 33 |

## Step 2: Weather Data

| Utility | Location | Coordinates | Dataset | Year |
|---------|----------|-------------|---------|------|
| PG&E | Sacramento, CA | 38.58N, 121.49W | NSRDB GOES Aggregated V4 | 2023 |
| SCE | Riverside, CA | 33.95N, 117.40W | NSRDB GOES Aggregated V4 | 2023 |
| SDG&E | San Diego, CA | 32.72N, 117.16W | NSRDB GOES Aggregated V4 | 2023 |

All files: 60-minute resolution, downloaded via NSRDB API.

**How to replicate:**
```
https://developer.nrel.gov/api/nsrdb/v2/solar/nsrdb-GOES-aggregated-v4-0-0-download.csv?
api_key=YOUR_KEY&wkt=POINT(-121.49 38.58)&names=2023&interval=60&utc=false&
email=YOUR_EMAIL&attributes=ghi,dni,dhi,air_temperature,wind_speed,surface_albedo
```
Replace coordinates for each utility location.

## Step 3: Load Profiles

| Utility | County Proxy | FIPS | Annual kWh/home | Peak kW | Source |
|---------|-------------|------|-----------------|---------|--------|
| PG&E | Sacramento | G0600670 | 8,917 | 3.11 | ResStock county-level |
| SCE | Riverside | G0600650 | 8,431 | 4.09 | ResStock county-level |
| SDG&E | San Diego | G0600730 | 7,220 | 2.14 | ResStock county-level |

**Source:** NREL ResStock End-Use Load Profiles, 2022 release, AMY2018. County-level aggregates from OEDI S3 data lake. Each county weighted across 5 building types (single-family detached, attached, MF 2-4, MF 5+, mobile home) by housing stock share.

**How to replicate:**
Download from: `https://data.openei.org/s3_viewer?bucket=oedi-data-lake&prefix=nrel-pds-building-stock/end-use-load-profiles-for-us-building-stock/2022/resstock_amy2018_release_1/`

## Step 4: Rate Structures (NBT Mandatory)

Under California's Net Billing Tariff (effective April 2023), all new solar customers must enroll in electrification TOU rates. Export compensation is at hourly Avoided Cost Calculator (ACC) values, not retail rates.

### 4a. PG&E Schedule E-ELEC

| Period | Hours | Rate ($/kWh) |
|--------|-------|-------------|
| Summer Peak (Jun-Sep) | 4-9pm | $0.552 |
| Summer Off-Peak | All other | $0.334 |
| Winter Peak (Oct-May) | 4-9pm | $0.321 |
| Winter Off-Peak | All other | $0.285 |
| Fixed Monthly | — | $24.00 |

**Source:** PG&E Schedule E-ELEC, CPUC AL 7213-E

### 4b. SCE Schedule TOU-D-PRIME

| Period | Hours | Rate ($/kWh) |
|--------|-------|-------------|
| Summer On-Peak (Jun-Sep) | 4-9pm weekdays | $0.590 |
| Summer Mid-Peak | 4-9pm weekends | $0.400 |
| Summer Off-Peak | All other | $0.260 |
| Winter Mid-Peak (Oct-May) | 4-9pm | $0.560 |
| Winter Off-Peak | 9pm-8am | $0.240 |
| Winter Super Off-Peak | 8am-4pm | $0.240 |
| Fixed Monthly | — | $24.00 |

**Source:** SCE Schedule TOU-D-PRIME, CPUC AL 5217-E

### 4c. SDG&E Schedule EV-TOU-5

| Period | Hours | Rate ($/kWh) |
|--------|-------|-------------|
| Summer On-Peak (Jun-Oct) | 4-9pm | $0.800 |
| Summer Off-Peak | 6am-12pm, 9pm-12am | $0.502 |
| Summer Super Off-Peak | 12am-6am, 12pm-4pm | $0.124 |
| Winter On-Peak (Nov-May) | 4-9pm | $0.529 |
| Winter Off-Peak | 6am-12pm, 9pm-12am | $0.473 |
| Winter Super Off-Peak | 12am-6am, 12pm-4pm | $0.117 |
| Fixed Monthly | — | $24.00 |

**Source:** SDG&E Schedule EV-TOU-5, CPUC AL 4259-E

### 4d. Export Compensation (ACC)

All three utilities use the CPUC Avoided Cost Calculator (ACC) to determine hourly export compensation rates. The 2026 vintage ACC values vary by hour of day, month, and utility territory.

| Utility | Annual Avg ACC ($/kWh) | Source File |
|---------|----------------------|-------------|
| PG&E | ~$0.097 | pge_acc_export_8760_2026.csv |
| SCE | ~$0.092 | sce_acc_export_8760_2026.csv |
| SDG&E | ~$0.090 | sdge_acc_export_8760_2026.csv |

**Source:** E3 Avoided Cost Calculator, 2024 update. PG&E 2026 EEC Price Sheet. SCE/SDG&E NBT MIDAS pricing files.

## Step 5: System Costs

| Component | $/unit | Total | Source |
|-----------|--------|-------|--------|
| Solar | $2,860/kW | $17,303 | Tao Sun et al. (2025), Supp Table 15, CA state-level |
| Battery | $1,091/kWh | $14,729 | Tao Sun et al. (2025), Supp Table 15, CA state-level |
| PV+Storage | — | $32,032 | Sum of above |

**Source:** Tao Sun, Olakunle Alao, Dalia Patino-Echeverri, "Economic valuation of distributed solar-plus-storage for US residential customers," *Nature Energy* (2025). Supplementary Table 15: State-level unit capital costs derived from 2023 NREL benchmark + state adjustment ratios.

## Step 6: Financial Parameters

| Parameter | Value | Source |
|-----------|-------|--------|
| Loan Interest Rate | 7.24% | Unified across configs |
| Loan Term | 25 years | Model standard |
| Customer Discount Rate | 6.4% | Standard residential |
| Electricity Cost Escalation | 2.5%/yr | EIA historical CA average |

## Step 7: Incentive Stack

### Federal

| Incentive | Value | Status | Source |
|-----------|-------|--------|--------|
| ITC (Sec. 25D) | 0% | Expired Dec 31, 2025 | IRS |

### State

| Incentive | Value | Status | Source |
|-----------|-------|--------|--------|
| SGIP (Self-Generation Incentive Program) | $0 | Closed (SB 700 expired Dec 2025) | CPUC |
| RSSE (AB 209, low-income only) | $1.10/Wh storage + $3.10/W PV | Fully reserved (waitlist) | CEC |

No active state incentives are available for average-income residential customers as of March 2026.

## Step 8: PySAM Simulation

**Module chain:** Pvwattsv8 -> Battwatts -> Utilityrate5

**Battery dispatch:** Custom TOU-aware algorithm. Charges during super off-peak (grid or PV excess), discharges during peak. Round-trip efficiency 90%.

**Configurations run:**
- 3 utilities (PG&E, SCE, SDG&E) x 2 system types (Solar, PV+S) = 6 configs

**Key PySAM outputs (Year 1):**

| Config | Bill w/o | Bill w/ System | Bill Savings |
|--------|---------|----------------|-------------|
| PG&E Solar Only | $3,364 | $1,994 | $1,371 |
| PG&E PV+Storage | $3,364 | $1,256 | $2,108 |
| SCE Solar Only | $3,184 | $1,986 | $1,198 |
| SCE PV+Storage | $3,184 | $1,373 | $1,812 |
| SDG&E Solar Only | $3,226 | $1,908 | $1,318 |
| SDG&E PV+Storage | $3,226 | $807 | $2,419 |

**Critical note on CA NBT:** Export compensation uses hourly ACC values (average ~$0.09/kWh), not retail rates. This is a 70-85% reduction compared to NEM 2.0's retail-rate credits. The TOU import rates and ACC export rates are fully decoupled, creating strong incentives for self-consumption and battery storage.

## Step 9: Excel Financial Models

**Structure per model (one per utility):**
- Inputs sheet with all parameters and source annotations
- Solar Only cash flow sheet (25-year)
- PV+Storage cash flow sheet (25-year)
- Summary sheet

**Key formulas:**
- PMT: `=PMT(rate, term, -debt)`
- Bill escalation: `=Y1_bill * (1 + escalation)^(year-1)`
- Cumulative NPV: `=prior_NPV + net_savings / (1+discount)^year` (no Year 0 outflow, 100% debt financed)

## Step 10: Verification

- Python independent calculation matches Excel formula outputs
- PySAM bill outputs cross-checked with manual rate x consumption
- ACC export rates verified against CPUC/E3 Avoided Cost Calculator documentation
- All rate structures traced to official utility tariff filings

---

## Output Files

| File | Description |
|------|-------------|
| `CA_Financial_Model_PGE_v3.xlsx` | PG&E 2-scenario model (Solar, PV+S) |
| `CA_Financial_Model_SCE_v3.xlsx` | SCE 2-scenario model (Solar, PV+S) |
| `CA_Financial_Model_SDGE_v3.xlsx` | SDG&E 2-scenario model (Solar, PV+S) |
| `CA_Summary_Tables.xlsx` | Presentation-ready tables (Guide + Results + Battery Value + Rates) |
| `CA_financial_summary.json` | Verified financial calculations |
| `CA_pysam_results_v3.json` | Raw PySAM outputs with full metadata |

---

## Risks & Caveats

1. **Federal ITC expired (Dec 2025).** The 30% credit was the most impactful single incentive. Its absence significantly weakens DER economics across all three utilities.

2. **SGIP closed, RSSE fully reserved.** No active state battery incentive exists for average-income customers. Low-income customers on the RSSE waitlist may eventually receive $1.10/Wh, which would cover nearly the full battery cost.

3. **NBT export rates average ~$0.09/kWh.** This is 70-85% below NEM 2.0 retail-rate credits. Solar-only systems lose most of their exported energy value, making system sizing and self-consumption critical.

4. **SDG&E EV-TOU-5 has the widest residential TOU spread in the nation.** The $0.68/kWh summer peak-to-trough gap ($0.80 vs $0.12) makes battery storage uniquely viable in SDG&E territory without incentives.

5. **County-proxy load profiles are approximations.** Sacramento, Riverside, and San Diego represent their respective utility territories, but each IOU covers diverse climate zones. PG&E's territory spans from hot inland valleys to cool coastal areas.

6. **ACC values are for 2026 vintage only.** Future vintages will have different hourly profiles as the grid evolves. The 9-year ACC lock-in for early NBT adopters may differ from later vintages.

7. **Battery dispatch is heuristic, not optimal.** The TOU-aware charge/discharge algorithm approximates but does not guarantee globally optimal dispatch. A mixed-integer linear program (MILP) would yield higher theoretical savings.

8. **PV+Storage is NPV-positive only at SDG&E.** At PG&E and SCE, battery financing cost ($2,808/yr) exceeds total bill savings ($2,108 and $1,812/yr respectively). Battery storage requires either lower interest rates, lower battery costs, or incentive support to break even in these territories.

9. **Solar-only is NPV-positive at PG&E and SDG&E but marginal at SCE.** SCE's TOU-D-PRIME rate structure produces lower bill-without-system ($3,184 vs $3,364 for PG&E) despite similar rate levels, due to the Riverside load profile's alignment with off-peak hours.

10. **No Title 24 analysis.** This study examines voluntary retrofit installations only. New construction in California is subject to mandatory solar requirements under Title 24, which changes the economic baseline.
