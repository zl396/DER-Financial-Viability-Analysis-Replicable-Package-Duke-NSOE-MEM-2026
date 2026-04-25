# Cross-State Methodology

> One-page summary of the analytical pipeline shared by all four state case studies.
> For per-state details, see each `case_studies/{XX}/README.md` and the corresponding `*_Workflow_Replicable.md`.

## Goal

Estimate the 25-year financial viability of a representative residential solar-plus-storage system under each state's prevailing rate structure, post-2025 federal ITC expiration. Produce comparable, reproducible NPV results across states.

## Pipeline (4 steps)

1. **Inputs** — assemble state-specific parameters from public sources:
   - System sizing: residential median PV + 13.5 kWh battery (Tao Sun et al. 2025, Supp. Table 15 for cost/kW)
   - Hourly load profile: NREL ResStock state-level (or county-level for CA), aggregated across building types
   - Hourly weather: NSRDB GOES Aggregated V4, 2023, 60-minute resolution
   - Rate structure: utility tariff filings + URDB cross-check
   - Incentives: federal (none post-2025), state, utility programs

2. **Simulation** — PySAM module chain `Pvwattsv8` → `Battwatts` → `Utilityrate5`. Generates hourly PV output, battery dispatch, and Year 1 bills with and without the system. Each rate track uses its **own** bill-without as the savings baseline (not the flat rate).

3. **Financial model** — Excel workbooks (openpyxl-built or hand-authored) with 25-year cash flow per scenario:
   - Loan amortization (PMT) at 7.24% / 25 years, 100% debt
   - Bill savings escalating at 2.5%/yr
   - Annual incentives where applicable (e.g., MA ConnectedSolutions, NC EnergyWise)
   - One-time incentives applied as up-front debt reduction
   - NPV at 6.4% customer discount rate, 25-year horizon

4. **Verification** — independent Python recalculation of NPV from cash flows, cross-checked against Excel formulas. Rate-track baseline match audited (the most common error source — see `WORKFLOW.md`).

## Cross-state controls

| Control | Value | Reason |
|---|---|---|
| System size | State median PV + 13.5 kWh battery | Removes household-specific size effects |
| Discount rate | 6.4% | Customer opportunity cost, not loan rate |
| Loan rate / term | 7.24% / 25 yr | Common residential solar loan benchmark |
| Escalation | 2.5%/yr | Long-run EIA AEO residential trend |
| Debt financing | 100% | Conservative; no equity contribution |
| Year-1 bill | PySAM output, not URDB calculator | Avoids double-counting fixed charges |

## Why this design

- **Public reproducibility:** every parameter has a primary public source. Anyone with an NSRDB key can re-run the full pipeline.
- **Cross-state comparability:** unified financial parameters make cross-state ΔNPV interpretable as policy difference, not financing difference.
- **Conservative bias:** 100% debt + 0% federal ITC + customer discount > loan rate stresses the analysis. NPV-positive results survive most household-specific variations.

## Known limitations

- Single representative load profile per state (or per county for CA). Real households vary widely.
- Single weather year (2023) — does not capture inter-annual irradiance variability.
- Fixed battery dispatch (peak-shaving), not optimal TOU arbitrage. Underestimates battery value where TOU spreads are wide (e.g., SDG&E EV-TOU-5).
- No tax-treatment optimization (depreciation, MACRS for residential — not applicable; ITC carryback — N/A post-2025).
- VPP / ancillary services revenue modeled as sensitivity, not base case (TX only).
