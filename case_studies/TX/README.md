# Texas — Residential DER Case Study

Deregulated retail electricity market: Oncor (T&D) plus a representative Retail Electric Provider (REP) — Chariot GreenVolt with fixed buyback. Includes an ERCOT Real-Time Market (RTM) VPP revenue sensitivity.

## Key parameters

| Parameter | Value | Source |
|---|---:|---|
| PV capacity | 5.95 kW DC | TX state median |
| Battery | 13.5 kWh / 5 kW | Tesla Powerwall equivalent |
| Solar cost | $2,770/kW = $16,482 | Tao Sun (2025), Supp. Table 15 |
| Battery cost | $1,102/kWh = $14,877 | Tao Sun (2025), Supp. Table 15 |
| Loan rate / term | 7.24% / 25 yr | Unified |
| Discount rate | 6.4% | Unified |
| Escalation | 2.5%/yr | EIA historical |
| Federal ITC (2026) | 0% | Sec 25D expired Dec 2025 |

## Rate structure (Oncor + Chariot GreenVolt)

| Component | Value | Source |
|---|---:|---|
| REP energy charge | 10.2¢/kWh | Chariot GreenVolt, meterplan.com |
| TDU delivery (Oncor) | 5.62¢/kWh | electricityplans.com |
| **Total buy rate** | **15.82¢/kWh** | calculated |
| Buyback (export) | 7.0¢/kWh fixed | Chariot GreenVolt |
| TDU fixed | $4.23/mo | Oncor |
| REP base fee | $29.95/mo | Chariot GreenVolt |

No 1:1 NEM. No state tax credit. No state rebate. No utility DR program.

## VPP sensitivity (ERCOT RTM)

VPP revenue estimated from ERCOT RTM 2025 daily min/max arbitrage × 13.5 kWh × 89.7% efficiency, after 30% aggregator take:

| Hub | After-take revenue | $/kW/yr |
|---|---:|---:|
| Houston (CenterPoint) | $230/yr | $66 |
| North (Oncor) | $253/yr | $72 |

Source: ERCOT MIS settlement point prices, full year 2025.

## Reproduction

Run from the repo root, after `pip install -r requirements.txt` and `cp .env.example .env` (with your free NSRDB key filled in):

```bash
# 1. Fetch ResStock state-level load profiles + NSRDB weather
python shared/fetch_resstock.py --state TX
python shared/fetch_nsrdb.py  --state TX

# 2. Inspect the Excel financial models (TX uses formula-driven Excel —
#    no Python builder in this release).
open "case_studies/TX/TX Results for Upload/TX_Financial_Model_BaseCase_v3.xlsx"
open "case_studies/TX/TX Results for Upload/TX_Financial_Model_VPP_v3.xlsx"
```

Detailed workflow: [`TX Results for Upload/TX_Workflow_Replicable.md`](TX%20Results%20for%20Upload/TX_Workflow_Replicable.md).

## Key findings

- **Solar-only is nearly breakeven** without any incentives: NPV –$860, monthly net –$30. High solar irradiance (8,661 kWh/yr from 5.95 kW) compensates for the absence of incentives.
- **Battery adds only $11/yr** of bill savings under flat-rate net billing — simple dispatch does not exploit TOU arbitrage that doesn't exist at the retail level.
- **VPP $253/yr improves PV+Storage NPV** from –$16,751 to –$13,636 — meaningful but not sufficient.
- **TX has no state DER incentives** — no tax credit, no rebate, no production incentive, no utility DR program.
- **Buyback rate (7¢ = 44% of retail)** is better than NC's 3.4¢ avoided cost but far below MA's ~24¢ NEM.

## Caveats

- Chariot GreenVolt plan terms may change (12-month contracts).
- TDU delivery charges update March 1 / September 1.
- VPP revenue is highly volatile (2023: $475/kW; 2025: ~$17/kW per Modo Energy).
- ERCOT ADER pilot requires 100 kW minimum aggregation — single 5 kW battery cannot participate alone.
