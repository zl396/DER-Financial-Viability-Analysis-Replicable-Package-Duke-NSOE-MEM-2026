# Massachusetts Residential DER Financial Analysis
## Replicable Workflow & Verified Parameters

**Date:** March 22, 2026
**Authors:** Duke NSOE MEM 2026 Cohort
**Tools:** PySAM v7.1.0 (NREL), Python 3.12, openpyxl

---

## Step 1: System Specifications

| Parameter | Value | Source |
|-----------|-------|--------|
| PV Capacity | 4.72 kW DC | MA state median residential (EIA/EnergySage) |
| Battery | 13.5 kWh / 5 kW | Tesla Powerwall equivalent |
| Tilt / Azimuth | 42° / 180° (south) | Latitude-optimal for Boston (42.37°N) |
| DC/AC Ratio | 1.2 | PySAM default |
| System Losses | 14% | PySAM default (soiling, shading, wiring) |
| Inverter Efficiency | 96% | PySAM default |

## Step 2: Weather Data

| Parameter | Value | Source |
|-----------|-------|--------|
| Location | Boston, MA (42.37°N, 71.06°W) | — |
| Dataset | NSRDB GOES Aggregated V4 | NREL |
| Year | 2023 (single-year hourly) | — |
| Resolution | 60-minute | — |
| API Endpoint | `nsrdb-GOES-aggregated-v4-0-0-download.csv` | developer.nrel.gov |
| File | `MA_boston_2023_hourly.csv` | Downloaded via NSRDB API |

**How to replicate:**
```
https://developer.nrel.gov/api/nsrdb/v2/solar/nsrdb-GOES-aggregated-v4-0-0-download.csv?
api_key=YOUR_KEY&wkt=POINT(-71.06 42.37)&names=2023&interval=60&utc=false&
email=YOUR_EMAIL&attributes=ghi,dni,dhi,air_temperature,wind_speed,surface_albedo
```

## Step 3: Load Profile

| Parameter | Value | Source |
|-----------|-------|--------|
| Source | ResStock (NREL) | OEDI Data Lake |
| Dataset | End-Use Load Profiles, 2022 release, AMY2018 | |
| State | Massachusetts | |
| Method | State-level aggregate (mean of all MA households) | |
| Annual Consumption | 8,834 kWh/yr | ResStock aggregate |
| Peak | ~3.5 kW | ResStock aggregate |
| File | `ma_representative_profile_hourly.csv` | |

**How to replicate:**
Download from: `https://data.openei.org/s3_viewer?bucket=oedi-data-lake&prefix=nrel-pds-building-stock/end-use-load-profiles-for-us-building-stock/2022/resstock_amy2018_release_1/`

## Step 4: Rate Structures

### 4a. Eversource (current flat rate, R-1)

| Component | Rate | Source |
|-----------|------|--------|
| Supply + Delivery | 24.957¢/kWh | Eversource R-1 tariff, MDPU |
| Customer Charge | $7.50/mo | Eversource R-1 tariff |
| NM Export Credit | ~23.75¢/kWh | Retail minus non-bypassable charges |
| NM Recovery Surcharge | 0.625¢/kWh | Eversource tariff (non-bypassable) |
| Distributed Solar Charge | 0.583¢/kWh | Eversource tariff (non-bypassable) |
| Net Metering | 1:1 retail credit, indefinite rollover | MA G.L. c. 164, §139 |

**Source documents:** Eversource Schedule R-1 tariff filing (PDF in source docs folder)

### 4b. National Grid (current flat rate, R-1)

| Component | Rate | Source |
|-----------|------|--------|
| Supply + Delivery | 36.029¢/kWh | National Grid R-1 tariff, MDPU |
| Customer Charge | $10.00/mo | National Grid R-1 tariff |
| NM Export Credit | ~33.58¢/kWh | Retail minus non-bypassable charges |
| NM Recovery Surcharge | 1.724¢/kWh | NGrid tariff (non-bypassable) |
| Distributed Solar Charge | 0.729¢/kWh | NGrid tariff (non-bypassable) |

**Source documents:** National Grid Schedule R-1 tariff filing (PDF in source docs folder)

### 4c. E3 2035 Illustrative TOU Rates (Sensitivity)

| Period | Winter (Nov-Apr) | Summer (May-Oct) |
|--------|-----------------|-------------------|
| On-Peak (5-8pm weekdays) | 43¢/kWh | 27¢/kWh |
| Mid-Peak | 33¢/kWh | 23¢/kWh |
| Off-Peak (10pm-6am) | 21¢/kWh | 19¢/kWh |
| Fixed Monthly | $40 | $40 |

**Source:** E3, *Long-Term Ratemaking Study* (Feb 2025), Figure 8, $40/mo fixed charge option. Revenue-neutral with National Grid 2024 rates. Values read from figure (approximate). E3 report downloaded locally.

**Export compensation scenarios (analytical, not E3 recommendations):**
- NM: 1:1 at TOU rate
- NB75: Net billing at 75% of TOU rate
- NB50: Net billing at 50% of TOU rate

## Step 5: System Costs

| Component | $/unit | Total | Source |
|-----------|--------|-------|--------|
| Solar | $3,540/kW | $16,709 | Tao Sun et al. (2025), Supp Table 15, MA state-level |
| Battery | $1,488/kWh | $20,088 | Tao Sun et al. (2025), Supp Table 15, MA state-level |
| PV+Storage | — | $36,797 | Sum of above |

**Source:** Tao Sun, Olakunle Alao, Dalia Patino-Echeverri, "Economic valuation of distributed solar-plus-storage for US residential customers," *Nature Energy* (2025). Supplementary Table 15: State-level unit capital costs derived from 2023 NREL benchmark + state adjustment ratios.

## Step 6: Financial Parameters

| Parameter | Value | Source |
|-----------|-------|--------|
| Loan Interest Rate | 7.24% | User decision (unified across configs) |
| Loan Term | 25 years | Model standard |
| Customer Discount Rate | 6.4% | Standard residential |
| Electricity Cost Escalation | 2.5%/yr | EIA historical MA average |

## Step 7: Incentive Stack

### Federal

| Incentive | Value | Status | Source |
|-----------|-------|--------|--------|
| ITC (Sec. 25D) | 0% | Expired Dec 31, 2025 | IRS |

### State

| Incentive | Value | Duration | Source |
|-----------|-------|----------|--------|
| State Income Tax Credit | 15% of cost, cap $1,000 | One-time (Year 0) | Mass.gov Schedule EC |
| Sales Tax Exemption | 6.25% | — | Mass.gov |
| Property Tax Exemption | 20 years | — | Mass.gov |

### SMART 3.0 (225 CMR 28.00)

| Component | Rate | Source |
|-----------|------|--------|
| Flat Incentive (≤25 kW) | $0.03/kWh | 225 CMR 28.05(7), 28.14(3) |
| Building Mounted Adder | $0.03/kWh | 225 CMR 28.13(3)(b) |
| Energy Storage Adder | $0.04/kWh | 225 CMR 28.13(3)(e) |
| **Compensation Term** | **20 years** | 225 CMR 28.13(1) |
| Solar Only annual | $348/yr | 5,794 kWh × $0.06 |
| PV+Storage annual | $579/yr | 5,794 kWh × $0.10 |
| Status | Pending DPU approval | DPU Docket 25-175 |

### ConnectedSolutions

| Parameter | Value | Source |
|-----------|-------|--------|
| Rate | $275/kW of avg summer contribution | MassSave.com |
| Annual (5 kW battery) | $1,375/yr | Calculated |
| Rate Lock | 5 years | MassSave.com |
| Post-lock | Assumption (maintained at $1,375) | — |

### Eversource Battery Rebate

| Parameter | Value | Source |
|-----------|-------|--------|
| One-time rebate | $500 | EnergySage |
| Eligibility | Eversource territory, PV+Storage only | — |

## Step 8: PySAM Simulation

**Module chain:** Pvwattsv8 → Battwatts → Utilityrate5

**PySAM bootstrap (if needed in sandbox):**
```python
import sys, os
sys.path.insert(0, '/opt/anaconda3/lib/python3.12/site-packages')
```

**Configurations run:**
- 2 utilities (Eversource, National Grid) × 2 system types (Solar, PV+S) = 4 flat rate configs
- 4 export scenarios (NM, NB100, NB75, NB50) × 2 system types = 8 TOU configs

**Key PySAM outputs (Year 1):**

| Config | Bill w/o | Bill w/ | Savings |
|--------|---------|---------|---------|
| EV Solar Only | $2,295 | $849 | $1,446 |
| EV PV+Storage | $2,295 | $864 | $1,431 |
| NG Solar Only | $3,303 | $1,215 | $2,088 |
| NG PV+Storage | $3,303 | $1,238 | $2,065 |
| TOU NM Solar | $2,853 | $1,325 | $1,528 |
| TOU NM PV+S | $2,853 | $1,343 | $1,510 |
| TOU NB75 Solar | $2,853 | $1,358 | $1,495 |
| TOU NB50 PV+S | $2,853 | $1,532 | $1,320 |

## Step 9: Excel Financial Models

**Structure per model:**
- Inputs sheet: all parameters with source annotations
- Cash flow sheets: 25-year amortization + bill savings + incentives
- Summary sheet: NPV, payback, monthly net for all scenarios
- Incentive schedule: SMART 20yr, ConnSol 5yr lock + assumption

**Key formulas:**
- PMT: `=PMT(rate, term, -debt)`
- Bill escalation: `=Y1_bill * (1 + escalation)^(year-1)`
- SMART cutoff: `=IF(year<=20, SMART_annual, 0)`
- Cumulative NPV: `=prior_NPV + net_savings / (1+discount)^year`
- NPV Breakeven: first year cumulative NPV >= 0

## Step 10: Verification

- Python independent calculation matches Excel formula outputs
- PySAM bill outputs cross-checked with manual rate × consumption
- All incentive parameters traced to regulatory filings

---

## Output Files

| File | Description |
|------|-------------|
| `MA_Financial_Model_FlatRate_v3.xlsx` | 10-scenario flat rate model (2 utilities × 5 scenarios) |
| `MA_Financial_Model_TOU_v3.xlsx` | 12-scenario E3 TOU sensitivity (3 export rules × 4 scenarios) |
| `MA_Summary_Tables.md` | Presentation-ready tables with takeaways |
| `MA_pysam_results_v3.json` | Raw PySAM flat rate outputs |
| `MA_tou_pysam_results_v3.json` | Raw PySAM TOU outputs |

---

## Risks & Caveats

1. **SMART 3.0 pending DPU approval** — payments not yet issued, will not be backdated
2. **ConnectedSolutions rate uncertainty post-Year 5** — $275/kW locked for 5 years only
3. **Federal ITC expired** — 30% credit no longer available for homeowner-owned systems
4. **E3 TOU rates are illustrative** — not proposals, from Figure 8 (visually read, approximate)
5. **NB75/NB50 are analytical scenarios** — no MA policy basis for these specific percentages
6. **Load profile is ResStock aggregate** — smooths individual household peaks
7. **Non-bypassable charges approximated** — only NM Recovery + Distributed Solar excluded from sell rate
