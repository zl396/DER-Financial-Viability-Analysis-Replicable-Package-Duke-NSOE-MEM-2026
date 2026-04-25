# Unified Financial Parameters

> Every cross-state comparison in this repository uses the same financial parameters. Changing them invalidates the cross-state apples-to-apples claim.

## Canonical values

| Parameter | Value | Type | Source / rationale |
|---|---:|---|---|
| Loan interest rate | 7.24% | annual nominal | National avg residential solar loan, 2024 (Wood Mackenzie / SEIA quarterly market reports) |
| Loan term | 25 years | years | Industry standard residential solar loan |
| Customer discount rate | 6.4% | annual real | Risk-adjusted residential opportunity cost — independent of financing |
| Electricity escalation | 2.5% | annual nominal | Long-run EIA AEO residential rate trend |
| Debt fraction | 100% | — | Conservative; no upfront equity |
| Federal ITC (Sec 25D) | 0% post-2026 | — | One Big Beautiful Bill Act, IRS Notice |
| Federal ITC (Sec 48 commercial) | n/a | — | Residential analysis |
| Analysis horizon | 25 years | years | Match loan term + system warranty |
| Battery degradation | per PySAM Battwatts default | — | Chemistry-specific; ~80% capacity at year 15 |
| PV degradation | 0.5%/yr | linear | PySAM default |
| Inverter efficiency | 96% | — | PySAM default |
| System losses | 14% | — | PySAM default (soiling + shading + wiring + clipping) |
| DC/AC ratio | 1.2 | — | PySAM default |

## Rationale for non-obvious choices

### Why 6.4% discount rate (not the 7.24% loan rate)?

The customer's discount rate is the **opportunity cost of their own capital** — what they could earn elsewhere on a similar-risk investment. It is independent of how the project is financed. Using the loan rate as the discount rate would double-count financing cost (already in the cash flow as PMT) and is methodologically incorrect.

6.4% reflects a residential customer's risk-adjusted return on a long-duration asset (compared to S&P 500 historical real return ~7%, residential real estate ~3–4%, intermediate-term Treasury ~2%).

### Why 100% debt financing?

Conservative assumption. Most realistic for households without spare equity capital. Models with cash-purchase financing (0% debt) systematically over-state DER NPV because they ignore the household's foregone return on the invested cash. **If the analysis is NPV-positive at 100% debt, it is a fortiori positive with any equity contribution.**

### Why 2.5%/yr electricity escalation?

EIA AEO Reference Case projects residential electricity prices growing 1.8–2.7%/yr nominally over 2025–2050. 2.5% is the midpoint of recent AEO vintages and matches the 20-year historical trend in the four modeled states (per EIA Form 826 monthly retail prices). State-specific deviations are within ±0.5%/yr — small relative to other model uncertainties.

### Why no Year 0 outflow under 100% debt?

Under 100% debt financing, the customer pays $0 upfront. The system cost flows through 25 annual loan payments (PMT × 25). NPV is computed on the **net annual cash flow** (savings + incentives − PMT) discounted from Year 1, not on a Year 0 –cost outflow plus undiscounted operations.

This was the **#1 modeling error** observed in earlier drafts: mixing cash-purchase NPV (Year 0 cost outflow + 25 years of pure savings) with debt-financed NPV (no Year 0 outflow + 25 years of net savings after PMT). Mixing these methods produced $15K–$35K NPV errors. See `WORKFLOW.md` lessons learned.

## State-specific overrides (none)

All four states use the canonical values above. State-specific data (rates, incentives, utility programs) sits **outside** the financial parameters table and varies by case study. The financial parameters are deliberately held constant.

## Sensitivity ranges (informational)

The base case uses the canonical values. Sensitivity tests in per-state workbooks vary:
- Loan rate: 6% / 7.24% / 8.5%
- Discount rate: 5% / 6.4% / 8%
- Escalation: 1.5% / 2.5% / 3.5%

These illustrate how robust each state's NPV verdict is to financing assumptions. They do not change the canonical parameters.
