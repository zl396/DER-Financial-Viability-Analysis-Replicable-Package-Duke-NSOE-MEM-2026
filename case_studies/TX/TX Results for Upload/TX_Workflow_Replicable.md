# TX DER Financial Analysis — Replicable Workflow

## 1. System Specifications

| Parameter | Value | Source |
|---|---|---|
| PV Capacity | 5.95 kW | State median (TX) |
| Battery | 13.5 kWh / 5 kW | Tesla Powerwall equivalent |
| Solar Cost | $2,770/kW = $16,482 | Tao Sun Supp Table 15, p73 |
| Battery Cost | $1,102/kWh = $14,877 | Tao Sun Supp Table 15, p73 |
| PV+S Total | $31,359 | Calculated |

## 2. Rate Structure (Oncor + Chariot GreenVolt)

| Parameter | Value | Source |
|---|---|---|
| REP Energy Charge | 10.2¢/kWh | Chariot GreenVolt, meterplan.com |
| TDU Delivery | 5.62¢/kWh | Oncor, electricityplans.com |
| Total Buy Rate | 15.82¢/kWh | Calculated |
| Buyback Rate | 7.0¢/kWh fixed | Chariot GreenVolt, meterplan.com |
| TDU Fixed | $4.23/mo | Oncor, electricityplans.com |
| REP Base Fee | $29.95/mo | Chariot GreenVolt, meterplan.com |
| Total Fixed | $34.18/mo | Calculated |
| Metering | Net billing | Not 1:1 NEM |

TX is deregulated (ERCOT). Customers choose REP. Chariot GreenVolt selected as representative mid-tier plan with fixed buyback. Oncor selected as largest TDU (Dallas/Ft Worth).

## 3. Incentives

| Incentive | Value | Source |
|---|---|---|
| Federal ITC | $0 | Expired Dec 2025 |
| State Tax Credit | $0 | TX has none |
| State Rebate | $0 | No statewide program |
| VPP Revenue (base case) | $0 | Base case assumption |
| VPP Revenue (VPP scenario) | $253/yr | ERCOT RTM 2025 full year, HB_NORTH, after 30% aggregator take |

## 4. Financial Parameters

| Parameter | Value | Source |
|---|---|---|
| Loan Rate | 7.24% | Unified across states |
| Loan Term | 25 years | Standard |
| Discount Rate | 6.4% | Customer discount rate |
| Escalation | 2.5%/yr | EIA historical |

## 5. Load Profile

- Source: ResStock TX aggregate
- Annual: 15,024 kWh/yr
- Peak: 5.38 kW
- Highest of all 5 states (AC-heavy climate)

## 6. Weather Data

- Source: NSRDB GOES Aggregated V4, Houston TX (29.76, -95.37), 2023
- File: PySAM_outputs/TX_houston_2023_hourly.csv

## 7. PySAM Simulation

- PV annual generation: 8,661 kWh
- PV+S net generation: 8,490 kWh
- Bill w/o system: $2,786.95/yr
- Solar Only savings: $1,088.02/yr
- PV+S savings: $1,098.80/yr

## 8. Financial Results

| Scenario | Bill Savings | Monthly Net | Simple PB | 25yr NPV | NPV BE |
|---|---:|---:|---:|---:|---|
| TX Solar No Incentives | $1,088 | $-30 | 15.1 yr | $-860 | Never |
| TX PV+S No Incentives | $1,099 | $-138 | 28.5 yr | $-16,751 | Never |
| TX PV+S VPP ($253/yr) | $1,099 | $-116 | 23.2 yr | $-13,636 | Never |

## 9. VPP Analysis

VPP revenue estimated from ERCOT RTM Settlement Point Prices (full year 2025, 12 monthly sheets).

| Hub | Gross Annual | After 30% Take | Per kW/yr |
|---|---:|---:|---:|
| Houston (CenterPoint) | $328/yr | $230/yr | $66/kW/yr |
| North (Oncor) | $361/yr | $253/yr | $72/kW/yr |

Method: Daily min/max price arbitrage × 13.5 kWh × 89.7% efficiency. Optimistic — assumes perfect daily cycling.

Source: rpt.00013061 RTMLZHBSPP_2025.xlsx (ERCOT MIS, 805,920 rows, 15 settlement points × 365 days × 96 intervals)

## 10. Key Findings

1. **TX solar-only is nearly breakeven without any incentives** (NPV -$860, monthly -$30). High solar irradiance (8,661 kWh/yr for 5.95 kW) partially compensates for lack of incentives.
2. **Battery adds minimal bill savings** (+$11/yr over solar-only) because simple dispatch does not do TOU arbitrage under flat rate net billing.
3. **VPP participation improves PV+S by $253/yr** but is far from sufficient — NPV improves from -$16,751 to -$13,636, still deeply negative.
4. **TX has NO state incentives for residential DER** — no tax credit, no rebate, no production incentive, no utility DR program (unlike MA ConnectedSolutions or NC EnergyWise).
5. **The 7¢ buyback rate (44% of retail)** is better than NC's 3.4¢ avoided cost but far below MA's ~24¢ NEM credit.
6. **ERCOT wholesale battery revenue collapsed 96%** from $475/kW/yr (2023) to ~$17/kW/yr (2025 Modo benchmark) due to 10 GW solar+storage buildout saturating the market.

## 11. Caveats

- Chariot GreenVolt plan terms may change (12-month contract)
- TDU delivery charges update March 1 and September 1
- VPP revenue is highly volatile (2023: $475/kW vs 2025: $17/kW per Modo Energy)
- Battery dispatch uses simple peak-shaving, not optimal TOU arbitrage
- 30% aggregator take rate is estimated — actual rates are private contracts
- ADER pilot requires 100 kW minimum aggregation — single 5 kW battery cannot participate alone
