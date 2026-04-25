# North Carolina — Residential DER Case Study

Duke Energy Carolinas (DEC) under two rate tracks: NMB (Net Metering Bridge / net billing, flat) and RSC (Residential Service TOU). Includes a Tariff On-Bill Financing (TOBF) sub-analysis.

## Key parameters

| Parameter | Value | Source |
|---|---:|---|
| PV capacity | 5.77 kW DC | Tao Sun (2025), NC state-level |
| Battery | 13.5 kWh / 5 kW | Tesla Powerwall equivalent |
| Solar cost | $3,040/kW = $17,541 | Tao Sun (2025), Supp. Table 15 |
| Battery cost | $1,214/kWh = $16,389 | Tao Sun (2025), Supp. Table 15 |
| Loan rate / term | 7.24% / 25 yr | Unified |
| Discount rate | 6.4% | Unified |
| Escalation | 2.5%/yr | EIA historical NC |
| Federal ITC (2026) | 0% | Sec 25D expired Dec 2025 |

## Rate tracks

| Track | Energy | Export | Customer | Source |
|---|---|---:|---:|---|
| NMB (flat / net billing) | 12.76¢/kWh | 3.4¢/kWh (avoided cost) | $14.00/mo | DEC Leaf 99 + 11, NCUC E-7 |
| RSC (TOU) | On-peak 17.62¢ / off 8.34¢ / discount 5.89¢ | 3.4¢/kWh | $14.00/mo | DEC RSC tariff, NCUC E-7 |

## Incentive stack

| Incentive | Value | Eligibility |
|---|---:|---|
| Duke PowerPair — Solar Rebate | $0.36/W ($2,077) | PV+Storage paired |
| Duke PowerPair — Battery Rebate | $400/kWh capped at $5,400 | PV+Storage paired |
| Duke EnergyWise | $277/yr | PV+Storage only |

## Reproduction

Run from the repo root, after `pip install -r requirements.txt` and `cp .env.example .env` (with your free NSRDB key filled in):

```bash
# 1. Fetch ResStock state-level load profiles + NSRDB weather
python shared/fetch_resstock.py --state NC
python shared/fetch_nsrdb.py  --state NC

# 2. (Optional) Re-run an earlier exploratory financial-model builder.
#    Both scripts write NC_Solar_Financing_Model.xlsx in their own folder.
#    These are pre-v3 prototypes; the *canonical* deliverables are the
#    v3 workbooks in NC Results for Upload/ (see below).
python "case_studies/NC/Financial Models/build_model.py"
python "case_studies/NC/Financial Models/build_model_v2.py"
```

**Canonical deliverables** (already committed; built off the latest PySAM run):

- [`NC Results for Upload/NC_Financial_Model_NMB_v3.xlsx`](NC%20Results%20for%20Upload/NC_Financial_Model_NMB_v3.xlsx) — 4 scenarios under the NMB (flat / net billing) track.
- [`NC Results for Upload/NC_Financial_Model_RSC_v3.xlsx`](NC%20Results%20for%20Upload/NC_Financial_Model_RSC_v3.xlsx) — 4 scenarios under the RSC (TOU) track.
- [`NC Results for Upload/NC_Summary_Tables.xlsx`](NC%20Results%20for%20Upload/NC_Summary_Tables.xlsx) — presentation-ready unified 8-scenario table.

Detailed step-by-step workflow with all source citations and verification logic: [`NC Results for Upload/NC_Workflow_Replicable.md`](NC%20Results%20for%20Upload/NC_Workflow_Replicable.md).

## Key findings

- **All scenarios are NPV-negative without ITC.** Best feasible: NMB Solar-only at –$7,390 (no incentives). Worst: RSC PV+Storage at >–$30K.
- **Battery adds minimal value** (~$39/yr under NMB, ~$58/yr under RSC) — far below its $16,389 cost.
- **NMB > RSC for solar** because TOU off-peak/discount hours coincide with PV generation. RSC's lower bill-without baseline ($1,473 vs NMB $2,037) means less savings absolute.
- **No state solar credit, no production incentive.** EnergyWise ($277/yr) is the only annual incentive — far below MA's ConnectedSolutions ($1,375/yr).
- **PowerPair requires paired battery.** "Solar-only with PowerPair" is a counterfactual sensitivity, not an enrollable option.

## Additional analysis: NC Tariff On-Bill Financing (TOBF)

Folder: [`NC_Tariff_On_Bill_Financing/`](NC_Tariff_On_Bill_Financing/) — independent author-built model exploring whether on-bill financing structure changes residential DER viability under NC's PAYS®-style framework. Includes battery replacement assumptions over the 25-year horizon.

- Excel model: [`NC_TOBF_Financial_Model.xlsx`](NC_Tariff_On_Bill_Financing/NC_TOBF_Financial_Model.xlsx)
- References (citations + URLs to all 14 sources, no PDFs redistributed): [`References/sources.md`](NC_Tariff_On_Bill_Financing/References/sources.md)
