# California — Residential DER Case Study

Net Energy Metering 3.0 (NBT) under three IOUs: PG&E (Sacramento), SCE (Riverside), SDG&E (San Diego).

## Key parameters

| Parameter | Value | Source |
|---|---:|---|
| PV capacity | 6.05 kW DC | Tao Sun et al. (2025), CA state-level |
| Battery | 13.5 kWh / 5 kW | Tesla Powerwall equivalent |
| Solar cost | $2,860/kW = $17,303 | Tao Sun (2025), Supp. Table 15 |
| Battery cost | $1,091/kWh = $14,729 | Tao Sun (2025), Supp. Table 15, CA state-level |
| Loan rate / term | 7.24% / 25 yr | Unified across states |
| Discount rate | 6.4% | Unified |
| Escalation | 2.5%/yr | EIA historical |
| Federal ITC (2026) | 0% | Sec 25D expired Dec 2025 |

## Rate tracks (NBT mandatory under NEM 3.0)

| Utility | Tariff | Peak rate | Source |
|---|---|---:|---|
| PG&E | E-ELEC | $0.552/kWh (Summer 4–9pm) | CPUC AL 7213-E |
| SCE | TOU-D-PRIME | $0.590/kWh (Summer 4–9pm wkdy) | CPUC AL 5217-E |
| SDG&E | EV-TOU-5 | $0.800/kWh (Summer 4–9pm) | CPUC AL 4259-E |

Export compensation uses the **Avoided Cost Calculator (ACC)** hourly rates, not retail. Annual ACC averages ~$0.090–0.097/kWh — a 70–85% reduction from NEM 2.0.

## Reproduction

Run from the repo root, after `pip install -r requirements.txt` and `cp .env.example .env` (with your free NSRDB key filled in):

```bash
# 1. Fetch ResStock county-level load profiles + NSRDB weather
python shared/fetch_resstock.py --state CA
python shared/fetch_nsrdb.py  --state CA

# 2. Build the financial model (writes CA_Financial_Model_PhaseA.xlsx in the same folder as the script)
python "case_studies/CA/Financial Models/build_ca_model.py"

# 3. Build the summary tables (writes CA_Summary_Tables.xlsx)
python "case_studies/CA/CA Results for Upload/build_ca_summary_tables.py"
```

Detailed step-by-step workflow with all source citations: [`CA Results for Upload/CA_Workflow_Replicable.md`](CA%20Results%20for%20Upload/CA_Workflow_Replicable.md).

## Key findings

- All three IOUs require electrification TOU rates under NBT for new solar customers.
- SDG&E's EV-TOU-5 has the **widest peak-to-trough spread** in the country ($0.80 vs $0.12 = $0.68/kWh), making it the strongest market signal for battery TOU arbitrage.
- PG&E E-ELEC has a narrow spread ($0.22 summer, $0.04 winter), limiting battery arbitrage value.
- ACC export rates (~$0.09/kWh average across utilities) are far below retail, fundamentally changing residual export economics versus pre-NBT NEM 2.0.
