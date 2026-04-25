# North Carolina Residential DER Financial Analysis
## Replicable Workflow & Verified Parameters

**Date:** March 24, 2026
**Authors:** Duke NSOE MEM 2026 Cohort
**Tools:** PySAM v7.1.0 (NREL), Python 3.12, openpyxl

---

## Step 1: System Specifications

| Parameter | Value | Source |
|-----------|-------|--------|
| PV Capacity | 5.77 kW DC | Tao Sun et al. (2025), NC state-level |
| Battery | 13.5 kWh / 5 kW | Tesla Powerwall equivalent |
| Tilt / Azimuth | 35° / 180° (south) | Latitude-optimal for Raleigh (35.78°N) |
| DC/AC Ratio | 1.2 | PySAM default |
| System Losses | 14% | PySAM default (soiling, shading, wiring) |
| Inverter Efficiency | 96% | PySAM default |

## Step 2: Weather Data

| Parameter | Value | Source |
|-----------|-------|--------|
| Location | Raleigh, NC (35.78°N, 78.64°W) | — |
| Dataset | NSRDB GOES Aggregated V4 | NREL |
| Year | 2023 (single-year hourly) | — |
| Resolution | 60-minute | — |
| API Endpoint | `nsrdb-GOES-aggregated-v4-0-0-download.csv` | developer.nrel.gov |
| File | `NC_raleigh_2023_hourly.csv` | Downloaded via NSRDB API |

**How to replicate:**
```
https://developer.nrel.gov/api/nsrdb/v2/solar/nsrdb-GOES-aggregated-v4-0-0-download.csv?
api_key=YOUR_KEY&wkt=POINT(-78.64 35.78)&names=2023&interval=60&utc=false&
email=YOUR_EMAIL&attributes=ghi,dni,dhi,air_temperature,wind_speed,surface_albedo
```

## Step 3: Load Profile

| Parameter | Value | Source |
|-----------|-------|--------|
| Source | ResStock (NREL) | OEDI Data Lake |
| Dataset | End-Use Load Profiles, 2022 release, AMY2018 | |
| State | North Carolina | |
| Method | State-level aggregate (mean of all NC households) | |
| Annual Consumption | 14,647 kWh/yr | ResStock aggregate |
| Peak | ~4.59 kW | ResStock aggregate |
| File | `nc_representative_profile_hourly.csv` | |

**How to replicate:**
Download from: `https://data.openei.org/s3_viewer?bucket=oedi-data-lake&prefix=nrel-pds-building-stock/end-use-load-profiles-for-us-building-stock/2022/resstock_amy2018_release_1/`

## Step 4: Rate Structures

### 4a. Duke Energy Carolinas (DEC) RS Flat Rate

| Component | Rate | Source |
|-----------|------|--------|
| Energy Charge | 12.76¢/kWh | DEC Leaf 11, NCUC Docket E-7 |
| Customer Charge | $14.00/mo | DEC Leaf 99, NCUC Docket E-7 |

### 4b. NMB (Net Metering Bridge / Net Billing)

| Component | Rate | Source |
|-----------|------|--------|
| Buy Rate | 12.76¢/kWh | DEC RS rate |
| Export Credit | 3.4¢/kWh | Avoided cost rate, net billing |
| Fixed Charge | $14.00/mo | DEC Leaf 99 |

### 4c. RSC (Residential Service TOU)

| Component | Rate | Source |
|-----------|------|--------|
| On-Peak (2-8pm weekdays) | 17.62¢/kWh | DEC RSC tariff, NCUC Docket E-7 |
| Off-Peak | 8.34¢/kWh | DEC RSC tariff |
| Discount (11pm-6am) | 5.89¢/kWh | DEC RSC tariff |
| Export Credit | 3.4¢/kWh | Avoided cost rate |
| Fixed Charge | $14.00/mo | DEC Leaf 99 |

**Source documents:** DEC tariff filings, NCUC Docket E-7

## Step 5: System Costs

| Component | $/unit | Total | Source |
|-----------|--------|-------|--------|
| Solar | $3,040/kW | $17,540.80 | Tao Sun et al. (2025), Supp Table 15, NC state-level |
| Battery | $1,214/kWh | $16,389.00 | Tao Sun et al. (2025), Supp Table 15, NC state-level |
| PV+Storage | — | $33,929.80 | Sum of above |

**Source:** Tao Sun, Olakunle Alao, Dalia Patino-Echeverri, "Economic valuation of distributed solar-plus-storage for US residential customers," *Nature Energy* (2025). Supplementary Table 15.

## Step 6: Financial Parameters

| Parameter | Value | Source |
|-----------|-------|--------|
| Loan Interest Rate | 7.24% | Unified across configs |
| Loan Term | 25 years | Model standard |
| Customer Discount Rate | 6.4% | Standard residential |
| Electricity Cost Escalation | 2.5%/yr | EIA historical NC average |

## Step 7: Incentive Stack

### Federal

| Incentive | Value | Status | Source |
|-----------|-------|--------|--------|
| ITC (Sec. 25D) | 0% | Expired Dec 31, 2025 | IRS |

### State

| Incentive | Value | Status | Source |
|-----------|-------|--------|--------|
| State Solar Tax Credit | None | NC does not offer one | DSIRE |

### Duke Energy PowerPair Program (NCUC Docket E-7)

| Component | Value | Type | Source |
|-----------|-------|------|--------|
| Solar Rebate | $0.36/W = $2,077 | One-time (reduces debt) | Duke Energy PowerPair |
| Battery Rebate | $400/kWh, cap $5,400 = $5,400 | One-time (reduces debt) | Duke Energy PowerPair |
| Eligibility | PV+Storage paired system only | Program rule | Duke Energy PowerPair FAQ; NCUC Docket E-7 Sub 1276 |

Note: PowerPair is a paired-system program. The Solar Rebate and Battery Rebate components are not independently available; a customer must enroll a qualifying solar + battery installation to receive either. Scenarios that apply only the Solar Rebate to a solar-only configuration are counterfactual and flagged as such in `NC_financial_summary.json`.

### Duke Energy EnergyWise

| Parameter | Value | Source |
|-----------|-------|--------|
| Annual Payment | $277/yr | Duke Energy |
| Eligibility | PV+Storage only | — |
| Term | No stated limit | — |

## Step 8: PySAM Simulation

**Module chain:** Pvwattsv8 -> Battwatts -> Utilityrate5

**Configurations run:**
- 2 rate tracks (NMB, RSC) x 2 system types (Solar, PV+S) = 4 configs

**Key PySAM outputs (Year 1):**

| Config | Bill w/o | Bill w/ System | Bill Savings |
|--------|---------|----------------|-------------|
| NMB Solar Only | $2,036.92 (RS flat) | $1,295.05 | $741.87 |
| NMB PV+Storage | $2,036.92 (RS flat) | $1,256.10 | $780.82 |
| RSC Solar Only | $1,472.60 (RSC TOU) | $955.55 | $517.05 |
| RSC PV+Storage | $1,472.60 (RSC TOU) | $897.93 | $574.67 |

**Critical note on savings calculation:** Each rate track uses its OWN bill w/o as baseline. NMB customers are billed at RS flat rate (12.76¢/kWh), so their baseline is $2,037. RSC customers are billed at TOU rates (5.89-17.62¢/kWh weighted average lower than flat), so their baseline is $1,473. Savings = bill w/o under that track − bill w/ system under that track. Do NOT cross-compare by using RS baseline for RSC scenarios.

## Step 9: Excel Financial Models

**Structure per model:**
- Inputs sheet with all parameters and source annotations
- Cash Flows sheet with 4 scenario blocks (25-year amortization + bill savings + incentives)

**Scenarios per model:**

| # | Scenario | Initial Debt | Annual Savings | Annual Incentive |
|---|----------|-------------|----------------|-----------------|
| 1 | Solar Only — Rebate Sensitivity (counterfactual)\* | $15,463.80 | rate-specific | $0 |
| 2 | Solar Only — No Incentives | $17,540.80 | rate-specific | $0 |
| 3 | PV+S — All Incentives | $26,452.80 | rate-specific | $277 (EnergyWise) |
| 4 | PV+S — No Incentives | $33,929.80 | rate-specific | $0 |

\* Scenario 1 applies the $2,077 PowerPair solar-rebate component to a solar-only system. PowerPair enrollment requires a paired battery, so this configuration is not available to a real household. Retained as a sensitivity case to isolate the rebate's NPV effect. Only scenarios 2, 3, and 4 are enrollable per rate track, yielding six feasible scenarios across NMB and RSC.

**Key formulas:**
- PMT: `=PMT(rate, term, -debt)`
- Bill escalation: `=Y1_bill * (1 + escalation)^(year-1)`
- EnergyWise: constant $277/yr (PV+S All Incentives only, no term limit)
- Cumulative NPV: `=prior_NPV + net_savings / (1+discount)^year` (no Year 0 investment outflow — 100% debt financed)

## Step 10: Verification

- Python independent calculation matches Excel formula outputs
- PySAM bill outputs cross-checked with manual rate x consumption
- All incentive parameters traced to Duke Energy program documents and NCUC filings
- Debt calculations verified against user-specified values

---

## Output Files

| File | Description |
|------|-------------|
| `NC_Financial_Model_NMB_v3.xlsx` | 4-scenario NMB/net billing model |
| `NC_Financial_Model_RSC_v3.xlsx` | 4-scenario RSC/TOU model |
| `NC_Summary_Tables.xlsx` | Presentation-ready table with Guide + unified 8-scenario results |
| `NC_financial_summary.json` | Verified financial calculations (source of truth for Summary Tables) |
| `NC_pysam_results_v3.json` | Raw PySAM outputs |

---

## Risks & Caveats

1. **NC has NO state solar tax credit.** Unlike MA ($1,000 cap), NC offers zero state-level tax incentives for residential solar. This eliminates one of the key cost-reduction levers available in other states.

2. **Federal ITC expired (Dec 2025).** The 30% ITC was the single largest incentive for residential DER. Its absence makes NC DER economics very challenging. All scenarios show deeply negative 25-year NPV.

3. **NMB export at avoided cost (3.4 cents/kWh) is only 27% of retail (12.76 cents).** This is among the lowest export compensation ratios in the country. Customers lose 73% of the value of each exported kWh compared to 1:1 net metering.

4. **RSC actually worsens solar economics compared to NMB.** Solar generates during off-peak/discount hours (5.89-8.34 cents), not during on-peak (17.62 cents). RSC bill w/o system ($1,473) is much lower than RS flat ($2,037) because TOU weighted average is cheaper than flat rate. RSC Solar-only NPV = -$10,888 vs NMB Solar-only NPV = -$7,390 (both at no incentives, the only real option for solar-only because PowerPair is PV+S paired). NMB is the better track for solar.

5. **EnergyWise ($277/yr) is the only annual incentive.** MA's ConnectedSolutions pays $1,375/yr, nearly 5x more. NC's annual incentive stream is insufficient to offset the loan payment gap.

6. **PowerPair program availability needs verification for 2026.** The rebate amounts ($0.36/W solar, $400/kWh battery) are from current Duke Energy filings. Program continuation and funding levels should be confirmed with Duke Energy or NCUC.

7. **No SMART-equivalent production incentive exists in NC.** MA's SMART 3.0 provides $0.06-0.10/kWh for 20 years. NC has no comparable long-term production-based incentive.

8. **Load profile is ResStock aggregate (14,647 kWh/yr).** NC households consume 66% more electricity than MA households (8,834 kWh/yr), largely due to air conditioning. This higher load means solar offsets a smaller fraction of total consumption.

9. **Battery adds minimal incremental savings.** Under NMB, battery adds only $39/yr over solar-only ($780.82 vs $741.87). Under RSC, battery adds $58/yr ($574.67 vs $517.05). The battery cost ($16,389) is not justified by these marginal savings without a robust demand response program.

10. **All feasible scenarios show negative monthly cash flow and negative 25-year NPV.** Without Federal ITC or a meaningful state incentive, NC residential DER does not achieve positive economics under any enrollable configuration. Among the six feasible scenarios, monthly out-of-pocket costs range from $66 (NMB Solar-only, no incentives) to $200 (RSC PV+Storage, no incentives). The least negative NPV is NMB Solar-only with no incentives at -$7,390; the least negative realistic PV+Storage scenario is NMB PV+Storage with PowerPair + EnergyWise at -$12,993. The two "Solar All" rows in the scenario table are counterfactual, because PowerPair requires a paired battery.
