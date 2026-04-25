# Massachusetts — Residential DER Case Study

Eversource and National Grid under flat-rate net metering plus an E3 2035 illustrative TOU sensitivity.

## Key parameters

| Parameter | Value | Source |
|---|---:|---|
| PV capacity | 4.72 kW DC | MA state median (EIA / EnergySage) |
| Battery | 13.5 kWh / 5 kW | Tesla Powerwall equivalent |
| Solar cost | $3,540/kW = $16,709 | Tao Sun (2025), Supp. Table 15 |
| Battery cost | $1,488/kWh = $20,088 | Tao Sun (2025), Supp. Table 15 |
| Loan rate / term | 7.24% / 25 yr | Unified across states |
| Discount rate | 6.4% | Unified |
| Escalation | 2.5%/yr | EIA historical MA |
| Federal ITC (2026) | 0% | Sec 25D expired Dec 2025 |

## Rate tracks

| Utility | Buy rate (current flat) | Export credit | Source |
|---|---:|---:|---|
| Eversource R-1 | 24.957¢/kWh | ~23.75¢/kWh (NEM minus surcharges) | Eversource MDPU filing |
| National Grid R-1 | 36.029¢/kWh | ~33.58¢/kWh | National Grid MDPU filing |

**E3 2035 TOU sensitivity:** On-peak 27¢ summer / 43¢ winter; mid-peak 23¢ / 33¢; off-peak 19¢ / 21¢; $40/mo fixed. From E3 *Long-Term Ratemaking Study* (Feb 2025), Figure 8.

## Incentive stack

| Incentive | Value | Term |
|---|---:|---|
| MA state solar credit | 15% (cap $1,000) | One-time |
| SMART 3.0 production incentive | $0.06–0.10/kWh | 20 years |
| ConnectedSolutions DR (battery) | $1,375/yr | 5-year rate lock |

ConnectedSolutions is the **dominant economic driver** for PV+Storage, not the battery hardware cost.

## Reproduction

Run from the repo root, after `pip install -r requirements.txt` and `cp .env.example .env` (with your free NSRDB key filled in):

```bash
# 1. Fetch ResStock state-level load profiles + NSRDB weather
python shared/fetch_resstock.py --state MA
python shared/fetch_nsrdb.py  --state MA

# 2. Inspect / extend the Excel financial models (MA uses formula-driven Excel,
#    not a Python builder — open the workbook directly).
open "case_studies/MA/MA Results for Upload/MA_Financial_Model_FlatRate_v3.xlsx"
open "case_studies/MA/MA Results for Upload/MA_Financial_Model_TOU_v3.xlsx"
```

Cash flows are entirely formula-driven inside the Excel workbooks — no Python build script needed once PySAM outputs (`PySAM_outputs/pysam_results.json`) are regenerated.

Detailed step-by-step workflow: [`MA Results for Upload/MA_Workflow_Replicable.md`](MA%20Results%20for%20Upload/MA_Workflow_Replicable.md).
Project context document: [`MA scenarios.docx`](MA%20scenarios.docx) (early scoping notes — superseded by the Workflow_Replicable above).

## Key findings

- Solar Only is **Day-1 NPV-positive** for both utilities at current flat NEM rates.
- PV+Storage is viable only with ConnectedSolutions ($1,375/yr per battery).
- National Grid economics significantly stronger than Eversource (higher rates → more savings).
- E3 2035 TOU improves DER NPV by 10–18% vs. flat rate under NEM.
- SMART 3.0 has a 20-year term (not 25 like the loan) — financial models must reflect this asymmetry.
