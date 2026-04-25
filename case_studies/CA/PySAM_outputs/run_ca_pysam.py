"""
CA PySAM Simulation: 6 scenarios (3 utilities × 2 systems)

Aligned with NC/MA workflow:
  PVWattsv8 -> solar generation
  Utilityrate5 -> bill calculation (TOU import + ACC export)
  Battwatts -> battery dispatch (Solar+Storage scenarios)

Outputs: CA_pysam_results.json with bill_wo, bill_w, savings for each scenario.
"""

import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import PySAM.Battwatts as batt
import PySAM.Pvwattsv8 as pvwatts
import PySAM.Utilityrate5 as utilityrate

# === Paths ===
BASE = Path(__file__).parent.parent
DATA = BASE / "data"
WEATHER = DATA / "weather"
ACC = DATA / "acc_export_rates"
LOAD_DIR = BASE / "CA county proxy load profiles"
OUTPUT = Path(__file__).parent

# === System Parameters (Tao Sun et al. 2025, Supplementary Table 15) ===
PV_KW = 6.05
BATTERY_KWH = 13.5
BATTERY_KW = 5.0
DC_AC_RATIO = 1.2
LOSSES = 14  # %
SOLAR_COST_PER_KW = 2860  # $/kW
BATT_COST_PER_KWH = 1091  # $/kWh
SOLAR_COST = SOLAR_COST_PER_KW * PV_KW
BATT_COST = BATT_COST_PER_KWH * BATTERY_KWH
TOTAL_PVS_COST = SOLAR_COST + BATT_COST

# === Utility Configurations ===
UTILITIES = {
    "PGE": {
        "name": "PG&E",
        "rate_name": "E-ELEC",
        "weather_file": WEATHER / "sacramento_tmy_hourly.csv",
        "load_profile": LOAD_DIR / "PGE Sacramento County" / "outputs" / "ca_pge_sacramento_representative_profile_hourly.csv",
        "acc_file": ACC / "pge_acc_export_8760_2026.csv",
        "fixed_charge_monthly": 24.14,  # $0.79343/day × ~30.44 days
        "min_charge_monthly": 0,
        # E-ELEC TOU periods (all year, including weekends):
        # Peak: 4-9 PM (hours 16-20)
        # Partial-Peak: 3-4 PM and 9 PM-12 AM (hours 15, 21-23)
        # Off-Peak: 12 AM-3 PM (hours 0-14)
        # Summer: Jun-Sep, Winter: Oct-May
        "tou_periods": {
            # (period, tier) -> rate
            # Period 1 = Off-Peak, Period 2 = Partial-Peak, Period 3 = Peak
            "summer": {  # Jun-Sep
                "peak": 0.55214,       # 4-9 PM
                "partial_peak": 0.39026, # 3-4 PM, 9 PM-12 AM
                "off_peak": 0.33358,   # 12 AM-3 PM
            },
            "winter": {  # Oct-May
                "peak": 0.32063,
                "partial_peak": 0.29854,
                "off_peak": 0.28468,
            },
        },
        # TOU schedule: 12×24 matrix, values are period numbers
        # Period 1=Off-Peak, 2=Partial-Peak, 3=Peak
        "schedule_builder": "pge_elec",
    },
    "SCE": {
        "name": "SCE",
        "rate_name": "TOU-D-PRIME",
        "weather_file": WEATHER / "riverside_tmy_hourly.csv",
        "load_profile": LOAD_DIR / "SCE Riverside County" / "outputs" / "ca_sce_riverside_representative_profile_hourly.csv",
        "acc_file": ACC / "sce_acc_export_8760_2026.csv",
        "fixed_charge_monthly": 24.00,
        "min_charge_monthly": 0,
        # TOU-D-PRIME:
        # Summer (Jun-Sep):
        #   On-Peak: 4-9 PM weekdays (period 3)
        #   Mid-Peak: 4-9 PM weekends (period 2)
        #   Off-Peak: all other (period 1)
        # Winter (Oct-May):
        #   Mid-Peak: 4-9 PM all days (period 2)
        #   Super Off-Peak: 8 AM-4 PM (period 4)
        #   Off-Peak: all other (period 1)
        "tou_periods": {
            "summer": {
                "on_peak": 0.59,      # 4-9 PM weekdays
                "mid_peak": 0.40,     # 4-9 PM weekends
                "off_peak": 0.26,     # all other
            },
            "winter": {
                "mid_peak": 0.56,     # 4-9 PM
                "super_off_peak": 0.24, # 8 AM-4 PM
                "off_peak": 0.24,     # all other
            },
        },
        "schedule_builder": "sce_tou_d_prime",
    },
    "SDGE": {
        "name": "SDG&E",
        "rate_name": "EV-TOU-5",
        "weather_file": WEATHER / "san_diego_tmy_hourly.csv",
        "load_profile": LOAD_DIR / "SDGE San Diego County" / "outputs" / "ca_sdge_sandiego_representative_profile_hourly.csv",
        "acc_file": ACC / "sdge_acc_export_8760_2026.csv",
        "fixed_charge_monthly": 24.14,
        "min_charge_monthly": 0,
        # EV-TOU-5:
        # Summer (Jun-Oct):
        #   On-Peak: 4-9 PM (period 3) = $0.79988
        #   Off-Peak: other daytime/evening (period 1) = $0.50245
        #   Super Off-Peak: 12 AM-6 AM, 10 AM-2 PM (period 4) = $0.12424
        # Winter (Nov-May):
        #   On-Peak: 4-9 PM (period 3) = $0.52926
        #   Off-Peak: other (period 1) = $0.47267
        #   Super Off-Peak: 12 AM-6 AM, 10 AM-2 PM (period 4) = $0.11686
        "tou_periods": {
            "summer": {
                "on_peak": 0.79988,
                "off_peak": 0.50245,
                "super_off_peak": 0.12424,
            },
            "winter": {
                "on_peak": 0.52926,
                "off_peak": 0.47267,
                "super_off_peak": 0.11686,
            },
        },
        "schedule_builder": "sdge_ev_tou_5",
    },
}


def load_weather_data(csv_path):
    """Load NSRDB CSV into PySAM solar_resource_data dict format."""
    df = pd.read_csv(csv_path, skiprows=2)
    # NSRDB format: Year,Month,Day,Hour,Minute,GHI,DHI,DNI,Wind Speed,Temperature,Surface Albedo
    data = {
        "lat": float(pd.read_csv(csv_path, nrows=1).iloc[0]["Latitude"]),
        "lon": float(pd.read_csv(csv_path, nrows=1).iloc[0]["Longitude"]),
        "tz": float(pd.read_csv(csv_path, nrows=1).iloc[0]["Local Time Zone"]),
        "elev": float(pd.read_csv(csv_path, nrows=1).iloc[0]["Elevation"]),
        "year": df["Year"].tolist(),
        "month": df["Month"].tolist(),
        "day": df["Day"].tolist(),
        "hour": df["Hour"].tolist(),
        "minute": df["Minute"].tolist(),
        "dn": df["DNI"].tolist(),
        "df": df["DHI"].tolist(),
        "gh": df["GHI"].tolist(),
        "wspd": df["Wind Speed"].tolist(),
        "tdry": df["Temperature"].tolist(),
        "albedo": df["Surface Albedo"].tolist() if "Surface Albedo" in df.columns else [0.2] * len(df),
    }
    return data


def load_hourly_load(csv_path):
    """Load county proxy hourly load profile (kW per home) -> 8760 array."""
    df = pd.read_csv(csv_path)
    # Column should be electric_kw_per_home or similar
    kw_col = [c for c in df.columns if "kw" in c.lower() or "kW" in c.lower()]
    if kw_col:
        load = df[kw_col[0]].values
    else:
        # Try second column
        load = df.iloc[:, 1].values
    # Ensure 8760
    if len(load) == 8761:
        load = load[:8760]
    elif len(load) != 8760:
        raise ValueError(f"Load profile has {len(load)} rows, expected 8760")
    return load.tolist()


def load_acc_export_rates(csv_path):
    """Load 8760 hourly ACC export rates ($/kWh)."""
    df = pd.read_csv(csv_path)
    rates = df["export_rate_kwh"].values
    if len(rates) != 8760:
        raise ValueError(f"ACC rates has {len(rates)} rows, expected 8760")
    return rates.tolist()


def build_pge_elec_schedule():
    """Build 12×24 TOU schedule for PG&E E-ELEC.

    All days (including weekends):
      Off-Peak (period 1): hours 0-14
      Partial-Peak (period 2): hours 15, 21-23
      Peak (period 3): hours 16-20

    Returns weekday and weekend schedules (same for E-ELEC).
    """
    sched = []
    for month in range(12):  # 0-11 = Jan-Dec
        row = []
        for hour in range(24):
            if 16 <= hour <= 20:
                row.append(3)  # Peak
            elif hour == 15 or 21 <= hour <= 23:
                row.append(2)  # Partial-Peak
            else:
                row.append(1)  # Off-Peak
        sched.append(row)
    return sched, sched  # Same for weekday and weekend


def build_sce_tou_d_prime_schedule():
    """Build 12×24 TOU schedule for SCE TOU-D-PRIME.

    Summer (Jun-Sep = months 5-8):
      Weekday: On-Peak (3) 4-9PM, Off-Peak (1) other
      Weekend: Mid-Peak (2) 4-9PM, Off-Peak (1) other
    Winter (Oct-May = months 0-4, 9-11):
      All days: Mid-Peak (2) 4-9PM, Super Off-Peak (4) 8AM-4PM, Off-Peak (1) other
    """
    summer_months = {5, 6, 7, 8}  # Jun-Sep (0-indexed)

    weekday_sched = []
    weekend_sched = []
    for month in range(12):
        wd_row = []
        we_row = []
        for hour in range(24):
            if month in summer_months:
                if 16 <= hour <= 20:
                    wd_row.append(3)  # On-Peak weekday
                    we_row.append(2)  # Mid-Peak weekend
                else:
                    wd_row.append(1)  # Off-Peak
                    we_row.append(1)
            else:  # Winter
                if 16 <= hour <= 20:
                    wd_row.append(2)  # Mid-Peak
                    we_row.append(2)
                elif 8 <= hour <= 15:
                    wd_row.append(4)  # Super Off-Peak
                    we_row.append(4)
                else:
                    wd_row.append(1)  # Off-Peak
                    we_row.append(1)
        weekday_sched.append(wd_row)
        weekend_sched.append(we_row)
    return weekday_sched, weekend_sched


def build_sdge_ev_tou_5_schedule():
    """Build 12×24 TOU schedule for SDG&E EV-TOU-5.

    Summer (Jun-Oct = months 5-9):
      On-Peak (3): 4-9 PM
      Super Off-Peak (4): 12-6 AM and 10 AM-2 PM
      Off-Peak (1): all other
    Winter (Nov-May = months 0-4, 10-11):
      On-Peak (3): 4-9 PM
      Super Off-Peak (4): 12-6 AM and 10 AM-2 PM
      Off-Peak (1): all other
    """
    summer_months = {5, 6, 7, 8, 9}  # Jun-Oct (0-indexed)

    sched = []
    for month in range(12):
        row = []
        for hour in range(24):
            if 16 <= hour <= 20:
                row.append(3)  # On-Peak
            elif (0 <= hour <= 5) or (10 <= hour <= 13):
                row.append(4)  # Super Off-Peak
            else:
                row.append(1)  # Off-Peak
        sched.append(row)
    return sched, sched  # Same for weekday/weekend


def configure_utilityrate(ur, utility_key, acc_rates, load_kwh_annual):
    """Configure Utilityrate5 for a CA utility with TOU + ACC export."""
    cfg = UTILITIES[utility_key]

    # Analysis period and system parameters
    ur.Lifetime.analysis_period = 25
    ur.Lifetime.system_use_lifetime_output = 0
    ur.Lifetime.inflation_rate = 2.5
    ur.SystemOutput.degradation = [0.5]  # 0.5%/year degradation

    # Metering: Net billing (instantaneous netting)
    ur.ElectricityRates.ur_metering_option = 2  # Net billing

    # Fixed monthly charge
    ur.ElectricityRates.ur_monthly_fixed_charge = cfg["fixed_charge_monthly"]
    ur.ElectricityRates.ur_monthly_min_charge = cfg["min_charge_monthly"]

    # Build TOU schedule
    builder = cfg["schedule_builder"]
    if builder == "pge_elec":
        wd_sched, we_sched = build_pge_elec_schedule()
    elif builder == "sce_tou_d_prime":
        wd_sched, we_sched = build_sce_tou_d_prime_schedule()
    elif builder == "sdge_ev_tou_5":
        wd_sched, we_sched = build_sdge_ev_tou_5_schedule()

    ur.ElectricityRates.ur_ec_sched_weekday = wd_sched
    ur.ElectricityRates.ur_ec_sched_weekend = we_sched

    # Build TOU energy charge matrix
    # Format: rows of [period, tier, max_usage, max_usage_units, buy_rate, sell_rate]
    # max_usage_units: 0=kWh, 1=kWh/kW
    # We use a single tier with 1e38 max usage
    tou_mat = []
    tou = cfg["tou_periods"]

    if utility_key == "PGE":
        # Summer: periods 1(off), 2(part), 3(peak) - months Jun-Sep
        # Winter: periods 1(off), 2(part), 3(peak) - months Oct-May
        # Since E-ELEC has same period structure year-round but different rates by season,
        # we need 6 rate entries. But PySAM TOU schedule assigns period per month-hour.
        # The schedule is the SAME all year, so we need to differentiate summer vs winter
        # via different period numbers.
        # Solution: Use periods 1-3 for winter (Oct-May), 4-6 for summer (Jun-Sep)
        # Rebuild schedule with this mapping
        sched = []
        for month in range(12):
            row = []
            is_summer = month in {5, 6, 7, 8}  # Jun-Sep
            offset = 3 if is_summer else 0
            for hour in range(24):
                if 16 <= hour <= 20:
                    row.append(3 + offset)  # Peak
                elif hour == 15 or 21 <= hour <= 23:
                    row.append(2 + offset)  # Partial-Peak
                else:
                    row.append(1 + offset)  # Off-Peak
            sched.append(row)
        ur.ElectricityRates.ur_ec_sched_weekday = sched
        ur.ElectricityRates.ur_ec_sched_weekend = sched

        tou_mat = [
            # Winter periods (Oct-May)
            [1, 1, 1e38, 0, tou["winter"]["off_peak"], 0],
            [2, 1, 1e38, 0, tou["winter"]["partial_peak"], 0],
            [3, 1, 1e38, 0, tou["winter"]["peak"], 0],
            # Summer periods (Jun-Sep)
            [4, 1, 1e38, 0, tou["summer"]["off_peak"], 0],
            [5, 1, 1e38, 0, tou["summer"]["partial_peak"], 0],
            [6, 1, 1e38, 0, tou["summer"]["peak"], 0],
        ]

    elif utility_key == "SCE":
        # Summer weekday: On-Peak(3), Off-Peak(1)
        # Summer weekend: Mid-Peak(2), Off-Peak(1)
        # Winter: Mid-Peak(2), Super Off-Peak(4), Off-Peak(1)
        # Need different rates for summer vs winter mid-peak (period 2)
        # Solution: summer periods 1,2,3; winter periods 5,6,7 (shift winter)
        summer_months = {5, 6, 7, 8}
        wd_sched = []
        we_sched = []
        for month in range(12):
            wd_row = []
            we_row = []
            is_summer = month in summer_months
            for hour in range(24):
                if is_summer:
                    if 16 <= hour <= 20:
                        wd_row.append(3)  # Summer On-Peak
                        we_row.append(2)  # Summer Mid-Peak
                    else:
                        wd_row.append(1)  # Summer Off-Peak
                        we_row.append(1)
                else:
                    if 16 <= hour <= 20:
                        wd_row.append(5)  # Winter Mid-Peak
                        we_row.append(5)
                    elif 8 <= hour <= 15:
                        wd_row.append(6)  # Winter Super Off-Peak
                        we_row.append(6)
                    else:
                        wd_row.append(4)  # Winter Off-Peak
                        we_row.append(4)
            wd_sched.append(wd_row)
            we_sched.append(we_row)
        ur.ElectricityRates.ur_ec_sched_weekday = wd_sched
        ur.ElectricityRates.ur_ec_sched_weekend = we_sched

        tou_mat = [
            [1, 1, 1e38, 0, tou["summer"]["off_peak"], 0],
            [2, 1, 1e38, 0, tou["summer"]["mid_peak"], 0],
            [3, 1, 1e38, 0, tou["summer"]["on_peak"], 0],
            [4, 1, 1e38, 0, tou["winter"]["off_peak"], 0],
            [5, 1, 1e38, 0, tou["winter"]["mid_peak"], 0],
            [6, 1, 1e38, 0, tou["winter"]["super_off_peak"], 0],
        ]

    elif utility_key == "SDGE":
        # Same period structure summer vs winter but different rates
        summer_months = {5, 6, 7, 8, 9}  # Jun-Oct
        sched = []
        for month in range(12):
            row = []
            is_summer = month in summer_months
            offset = 0 if is_summer else 3
            for hour in range(24):
                if 16 <= hour <= 20:
                    row.append(3 + offset)  # On-Peak
                elif (0 <= hour <= 5) or (10 <= hour <= 13):
                    row.append(2 + offset)  # Super Off-Peak
                else:
                    row.append(1 + offset)  # Off-Peak
            sched.append(row)
        ur.ElectricityRates.ur_ec_sched_weekday = sched
        ur.ElectricityRates.ur_ec_sched_weekend = sched

        tou_mat = [
            # Summer (Jun-Oct)
            [1, 1, 1e38, 0, tou["summer"]["off_peak"], 0],
            [2, 1, 1e38, 0, tou["summer"]["super_off_peak"], 0],
            [3, 1, 1e38, 0, tou["summer"]["on_peak"], 0],
            # Winter (Nov-May)
            [4, 1, 1e38, 0, tou["winter"]["off_peak"], 0],
            [5, 1, 1e38, 0, tou["winter"]["super_off_peak"], 0],
            [6, 1, 1e38, 0, tou["winter"]["on_peak"], 0],
        ]

    ur.ElectricityRates.ur_ec_tou_mat = tou_mat

    # Sell rate = 0 in TOU matrix (we use timestep sell rates instead)
    ur.ElectricityRates.ur_sell_eq_buy = 0

    # Enable hourly ACC export rates
    ur.ElectricityRates.ur_en_ts_sell_rate = 1
    ur.ElectricityRates.ur_ts_sell_rate = acc_rates

    return ur


def run_solar_only(utility_key):
    """Run PVWatts + Utilityrate5 for Solar-Only scenario."""
    cfg = UTILITIES[utility_key]
    print(f"\n  Running {cfg['name']} Solar Only...")

    # --- PVWatts ---
    pv = pvwatts.default("PVWattsResidential")
    weather = load_weather_data(cfg["weather_file"])
    pv.SolarResource.solar_resource_data = weather
    pv.SystemDesign.system_capacity = PV_KW
    pv.SystemDesign.dc_ac_ratio = DC_AC_RATIO
    pv.SystemDesign.azimuth = 180
    pv.SystemDesign.tilt = weather["lat"]
    pv.SystemDesign.array_type = 1  # Fixed roof mount
    pv.SystemDesign.module_type = 0  # Standard
    pv.SystemDesign.losses = LOSSES
    pv.AdjustmentFactors.adjust_constant = 0
    pv.execute()

    gen = list(pv.Outputs.gen)  # kW per hour, 8760
    pv_annual_kwh = sum(gen)
    print(f"    PV annual: {pv_annual_kwh:.0f} kWh")

    # --- Load ---
    load = load_hourly_load(cfg["load_profile"])
    load_annual = sum(load)
    print(f"    Load annual: {load_annual:.0f} kWh")

    # --- ACC export rates ---
    acc_rates = load_acc_export_rates(cfg["acc_file"])

    # --- Utilityrate5: Bill WITH system ---
    ur_w = utilityrate.new()
    ur_w.SystemOutput.gen = gen
    ur_w.Load.load = load
    configure_utilityrate(ur_w, utility_key, acc_rates, load_annual)
    ur_w.execute()
    bill_w = ur_w.Outputs.utility_bill_w_sys_year1

    # --- Utilityrate5: Bill WITHOUT system ---
    ur_wo = utilityrate.new()
    ur_wo.SystemOutput.gen = [0] * 8760
    ur_wo.Load.load = load
    configure_utilityrate(ur_wo, utility_key, acc_rates, load_annual)
    ur_wo.execute()
    bill_wo = ur_wo.Outputs.utility_bill_wo_sys_year1

    savings = bill_wo - bill_w
    print(f"    Bill w/o: ${bill_wo:.2f}, Bill w/: ${bill_w:.2f}, Savings: ${savings:.2f}")

    return {
        "bill_wo": round(bill_wo, 2),
        "bill_w": round(bill_w, 2),
        "savings": round(savings, 2),
        "pv_annual_kwh": round(pv_annual_kwh, 0),
        "load_annual_kwh": round(load_annual, 0),
    }


def get_hourly_import_rates(utility_key):
    """Build 8760 array of import rates ($/kWh) for TOU dispatch."""
    cfg = UTILITIES[utility_key]
    tou = cfg["tou_periods"]
    from datetime import datetime, timedelta

    # Use 2026 calendar (non-leap year)
    start = datetime(2026, 1, 1)
    rates = []

    from datetime import date
    FEDERAL_HOLIDAYS_2026_SET = {
        date(2026, 1, 1), date(2026, 1, 19), date(2026, 2, 16),
        date(2026, 5, 25), date(2026, 7, 3), date(2026, 9, 7),
        date(2026, 11, 11), date(2026, 11, 26), date(2026, 12, 25),
    }

    for h in range(8760):
        dt = start + timedelta(hours=h)
        month_0 = dt.month - 1  # 0-indexed
        hour = dt.hour
        is_weekend = dt.weekday() >= 5 or dt.date() in FEDERAL_HOLIDAYS_2026_SET

        if utility_key == "PGE":
            is_summer = month_0 in {5, 6, 7, 8}
            season = "summer" if is_summer else "winter"
            if 16 <= hour <= 20:
                rates.append(tou[season]["peak"])
            elif hour == 15 or 21 <= hour <= 23:
                rates.append(tou[season]["partial_peak"])
            else:
                rates.append(tou[season]["off_peak"])

        elif utility_key == "SCE":
            is_summer = month_0 in {5, 6, 7, 8}
            if is_summer:
                if 16 <= hour <= 20:
                    rates.append(tou["summer"]["on_peak"] if not is_weekend else tou["summer"]["mid_peak"])
                else:
                    rates.append(tou["summer"]["off_peak"])
            else:
                if 16 <= hour <= 20:
                    rates.append(tou["winter"]["mid_peak"])
                elif 8 <= hour <= 15:
                    rates.append(tou["winter"]["super_off_peak"])
                else:
                    rates.append(tou["winter"]["off_peak"])

        elif utility_key == "SDGE":
            is_summer = month_0 in {5, 6, 7, 8, 9}
            season = "summer" if is_summer else "winter"
            if 16 <= hour <= 20:
                rates.append(tou[season]["on_peak"])
            elif (0 <= hour <= 5) or (10 <= hour <= 13):
                rates.append(tou[season]["super_off_peak"])
            else:
                rates.append(tou[season]["off_peak"])

    return rates


def build_tou_battery_dispatch(gen_pv, load, utility_key):
    """Simulate TOU-aware battery dispatch and return adjusted gen array.

    Strategy:
    1. Self-consume PV first (reduce grid import)
    2. Charge battery from excess PV during any hour
    3. If battery not full, charge from grid during super-off-peak / lowest-rate hours
    4. Discharge during peak hours to offset grid imports

    Returns: 8760 gen array (PV + battery net) for Utilityrate5.
    """
    import_rates = get_hourly_import_rates(utility_key)
    gen_pv = np.array(gen_pv)
    load_arr = np.array(load)

    batt_kwh = BATTERY_KWH
    batt_kw = BATTERY_KW
    efficiency = 0.90  # roundtrip
    charge_eff = np.sqrt(efficiency)
    discharge_eff = np.sqrt(efficiency)
    soc_min = 0.10 * batt_kwh  # 10% min SOC
    soc_max = 0.95 * batt_kwh  # 95% max SOC
    soc = 0.50 * batt_kwh  # start at 50%

    # Determine daily rate thresholds for each day
    # For each hour: compute net_load = load - pv
    net_load = load_arr - gen_pv  # positive = need grid, negative = excess PV

    gen_out = np.zeros(8760)
    total_charge_grid = 0
    total_charge_pv = 0
    total_discharge = 0

    for h in range(8760):
        pv_h = gen_pv[h]
        load_h = load_arr[h]
        rate_h = import_rates[h]
        net_h = load_h - pv_h  # positive = import, negative = export

        batt_action = 0  # positive = discharge, negative = charge (kW)

        # Determine the rate tier for this hour
        # Find the daily max rate to know what "peak" is
        day_start = (h // 24) * 24
        day_rates = import_rates[day_start:day_start + 24]
        max_rate = max(day_rates)
        min_rate = min(day_rates)
        rate_spread = max_rate - min_rate

        if rate_spread < 0.05:
            # Flat-ish rates: just self-consume
            if net_h < 0:
                # Excess PV — charge battery
                excess = -net_h
                charge = min(excess, batt_kw, (soc_max - soc) / charge_eff)
                charge = max(0, charge)
                batt_action = -charge
                soc += charge * charge_eff
                total_charge_pv += charge * charge_eff
            elif net_h > 0:
                # Need grid — discharge battery
                needed = net_h
                discharge = min(needed, batt_kw, (soc - soc_min) * discharge_eff)
                discharge = max(0, discharge)
                batt_action = discharge
                soc -= discharge / discharge_eff
                total_discharge += discharge

        elif rate_h >= max_rate - 0.01:
            # PEAK HOUR: discharge battery to offset imports
            if net_h > 0:
                # Need grid power — discharge to cover it
                discharge = min(net_h, batt_kw, (soc - soc_min) * discharge_eff)
                discharge = max(0, discharge)
                batt_action = discharge
                soc -= discharge / discharge_eff
                total_discharge += discharge
            elif net_h < 0:
                # Excess PV during peak — still export (high ACC value)
                # But charge if SOC low (unlikely during peak)
                pass

        elif rate_h <= min_rate + 0.01:
            # SUPER OFF-PEAK: charge battery (from PV excess or grid)
            if net_h < 0:
                # Excess PV — charge from PV
                excess = -net_h
                charge = min(excess, batt_kw, (soc_max - soc) / charge_eff)
                charge = max(0, charge)
                batt_action = -charge
                soc += charge * charge_eff
                total_charge_pv += charge * charge_eff
            else:
                # No excess PV — charge from grid at low rate
                charge = min(batt_kw, (soc_max - soc) / charge_eff)
                charge = max(0, charge)
                batt_action = -charge
                soc += charge * charge_eff
                total_charge_grid += charge * charge_eff

        else:
            # MID / OFF-PEAK: self-consume excess PV, modest discharge for imports
            if net_h < 0:
                excess = -net_h
                charge = min(excess, batt_kw, (soc_max - soc) / charge_eff)
                charge = max(0, charge)
                batt_action = -charge
                soc += charge * charge_eff
                total_charge_pv += charge * charge_eff
            elif net_h > 0 and rate_h > (min_rate + max_rate) / 2:
                # Above-average rate: discharge partially
                discharge = min(net_h * 0.5, batt_kw, (soc - soc_min) * discharge_eff)
                discharge = max(0, discharge)
                batt_action = discharge
                soc -= discharge / discharge_eff
                total_discharge += discharge

        # Clamp SOC
        soc = max(soc_min, min(soc_max, soc))

        # gen_out = PV + battery discharge (or PV - battery charge)
        gen_out[h] = pv_h + batt_action

    pvs_annual = sum(gen_out)
    print(f"    Battery dispatch: charge_pv={total_charge_pv:.0f} charge_grid={total_charge_grid:.0f} discharge={total_discharge:.0f} kWh")
    print(f"    PV annual: {sum(gen_pv):.0f} kWh, PV+S net: {pvs_annual:.0f} kWh")

    return gen_out.tolist()


def run_solar_battery(utility_key):
    """Run PVWatts + Battwatts + Utilityrate5 for Solar+Storage scenario."""
    cfg = UTILITIES[utility_key]
    print(f"\n  Running {cfg['name']} Solar+Storage...")

    # --- PVWatts ---
    pv = pvwatts.default("PVWattsResidential")
    weather = load_weather_data(cfg["weather_file"])
    pv.SolarResource.solar_resource_data = weather
    pv.SystemDesign.system_capacity = PV_KW
    pv.SystemDesign.dc_ac_ratio = DC_AC_RATIO
    pv.SystemDesign.azimuth = 180
    pv.SystemDesign.tilt = weather["lat"]
    pv.SystemDesign.array_type = 1
    pv.SystemDesign.module_type = 0
    pv.SystemDesign.losses = LOSSES
    pv.AdjustmentFactors.adjust_constant = 0
    pv.execute()
    gen = list(pv.Outputs.gen)
    pv_annual_kwh = sum(gen)

    # --- Load ---
    load = load_hourly_load(cfg["load_profile"])
    load_annual = sum(load)

    # --- Battery: TOU-aware custom dispatch ---
    # Build hourly import rate map to determine charge/discharge strategy
    gen_with_batt = build_tou_battery_dispatch(gen, load, utility_key)
    pvs_annual_kwh = sum(gen_with_batt)
    print(f"    PV annual: {pv_annual_kwh:.0f} kWh, PV+S net: {pvs_annual_kwh:.0f} kWh")
    print(f"    Load annual: {load_annual:.0f} kWh")

    # --- ACC export rates ---
    acc_rates = load_acc_export_rates(cfg["acc_file"])

    # --- Utilityrate5: Bill WITH system ---
    ur_w = utilityrate.new()
    ur_w.SystemOutput.gen = gen_with_batt
    ur_w.Load.load = load
    configure_utilityrate(ur_w, utility_key, acc_rates, load_annual)
    ur_w.execute()
    bill_w = ur_w.Outputs.utility_bill_w_sys_year1

    # --- Bill WITHOUT (same as solar-only) ---
    ur_wo = utilityrate.new()
    ur_wo.SystemOutput.gen = [0] * 8760
    ur_wo.Load.load = load
    configure_utilityrate(ur_wo, utility_key, acc_rates, load_annual)
    ur_wo.execute()
    bill_wo = ur_wo.Outputs.utility_bill_wo_sys_year1

    savings = bill_wo - bill_w
    print(f"    Bill w/o: ${bill_wo:.2f}, Bill w/: ${bill_w:.2f}, Savings: ${savings:.2f}")

    return {
        "bill_wo": round(bill_wo, 2),
        "bill_w": round(bill_w, 2),
        "savings": round(savings, 2),
        "pv_annual_kwh": round(pv_annual_kwh, 0),
        "pvs_annual_kwh": round(pvs_annual_kwh, 0),
        "load_annual_kwh": round(load_annual, 0),
    }


def main():
    print("=" * 60)
    print("CA PySAM Simulation — 6 Scenarios")
    print("=" * 60)

    results = {}

    for utility_key in ["PGE", "SCE", "SDGE"]:
        cfg = UTILITIES[utility_key]
        print(f"\n{'='*40}")
        print(f"Utility: {cfg['name']} ({cfg['rate_name']})")
        print(f"{'='*40}")

        solar = run_solar_only(utility_key)
        results[f"{utility_key}_SolarOnly"] = solar

        battery = run_solar_battery(utility_key)
        results[f"{utility_key}_SolarBattery"] = battery

        # Incremental battery value
        batt_incremental = battery["savings"] - solar["savings"]
        print(f"\n  Battery incremental savings: ${batt_incremental:.2f}/yr")

    # Add metadata
    results["_meta"] = {
        "pv_kw": PV_KW,
        "battery_kwh": BATTERY_KWH,
        "battery_kw": BATTERY_KW,
        "solar_cost_per_kw": SOLAR_COST_PER_KW,
        "batt_cost_per_kwh": BATT_COST_PER_KWH,
        "solar_cost": SOLAR_COST,
        "batt_cost": BATT_COST,
        "total_pvs_cost": TOTAL_PVS_COST,
        "dc_ac_ratio": DC_AC_RATIO,
        "losses_pct": LOSSES,
        "itc_pct": 0,
        "state_incentives": 0,
        "loan_rate": 0.0724,
        "loan_term_years": 25,
        "discount_rate": 0.064,
        "escalation_rate": 0.025,
    }

    # Save
    outpath = OUTPUT / "CA_pysam_results.json"
    with open(outpath, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n{'='*60}")
    print(f"Results saved to: {outpath}")
    print(f"{'='*60}")

    # Summary table
    print(f"\n{'Scenario':<25} {'Bill w/o':>10} {'Bill w/':>10} {'Savings':>10}")
    print("-" * 55)
    for key, val in results.items():
        if key.startswith("_"):
            continue
        print(f"{key:<25} ${val['bill_wo']:>9,.2f} ${val['bill_w']:>9,.2f} ${val['savings']:>9,.2f}")


if __name__ == "__main__":
    main()
