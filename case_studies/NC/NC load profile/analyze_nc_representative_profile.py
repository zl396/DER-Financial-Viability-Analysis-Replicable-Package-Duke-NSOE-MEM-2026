import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DATA_DIR = BASE_DIR / "nc_resstock_2022_agg"
DEFAULT_OUTPUT_DIR = BASE_DIR / "nc_resstock_analysis"


def season_for_month(month: int) -> str:
    if month in (12, 1, 2):
        return "Winter"
    if month in (3, 4, 5):
        return "Spring"
    if month in (6, 7, 8):
        return "Summer"
    return "Fall"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data_dir = args.data_dir.resolve()
    output_dir = args.output_dir.resolve()

    output_dir.mkdir(exist_ok=True, parents=True)

    csv_paths = sorted(data_dir.glob("*.csv"))
    if not csv_paths:
        raise FileNotFoundError(f"No CSV files found in {data_dir}")

    first_columns = pd.read_csv(csv_paths[0], nrows=0).columns.tolist()
    electric_cols = [
        col
        for col in first_columns
        if col.startswith("out.electricity.") and col.endswith(".energy_consumption.kwh")
    ]
    total_col = "out.electricity.total.energy_consumption.kwh"
    excluded_end_use_cols = {
        total_col,
        "out.electricity.net.energy_consumption.kwh",
    }
    end_use_cols = [col for col in electric_cols if col not in excluded_end_use_cols]
    usecols = ["timestamp", "in.geometry_building_type_recs", "units_represented", *electric_cols]

    statewide = None
    units_by_type = {}

    for path in csv_paths:
        df = pd.read_csv(path, usecols=usecols, parse_dates=["timestamp"])
        building_type = df["in.geometry_building_type_recs"].iat[0]
        represented_units = float(df["units_represented"].iat[0])
        units_by_type[building_type] = represented_units

        electric_only = df[electric_cols].copy()
        electric_only.insert(0, "timestamp", df["timestamp"])

        if statewide is None:
            statewide = electric_only
        else:
            statewide[electric_cols] = statewide[electric_cols].add(electric_only[electric_cols], fill_value=0.0)

    if statewide is None:
        raise RuntimeError("No data loaded")

    total_units = sum(units_by_type.values())
    statewide["total_electric_kwh"] = statewide[total_col]
    statewide["electric_kwh_per_home"] = statewide["total_electric_kwh"] / total_units
    statewide["electric_kw_per_home"] = statewide["electric_kwh_per_home"] * 4.0

    per_home = pd.DataFrame({"timestamp": statewide["timestamp"]})
    per_home["electric_kw_per_home"] = statewide["electric_kw_per_home"]
    per_home["electric_kwh_per_home"] = statewide["electric_kwh_per_home"]
    per_home["season"] = per_home["timestamp"].dt.month.map(season_for_month)
    per_home["time_of_day"] = per_home["timestamp"].dt.strftime("%H:%M")

    hourly = (
        per_home.set_index("timestamp")["electric_kwh_per_home"]
        .resample("1h")
        .sum()
        .rename("electric_kw_per_home")
        .to_frame()
    )
    daily = hourly.resample("1D").mean()
    monthly = (
        per_home.set_index("timestamp")["electric_kwh_per_home"]
        .resample("ME")
        .sum()
        .rename("monthly_kwh_per_home")
        .to_frame()
    )

    end_use_per_home = pd.Series(
        {col: statewide[col].sum() / total_units for col in end_use_cols},
        name="annual_kwh_per_home",
    ).sort_values(ascending=False)

    top_end_uses = end_use_per_home.head(8).copy()
    top_end_uses.index = (
        top_end_uses.index.str.removeprefix("out.electricity.")
        .str.removesuffix(".energy_consumption.kwh")
        .str.replace("_", " ", regex=False)
        .str.title()
    )

    building_type_weights = (
        pd.Series(units_by_type, name="represented_units")
        .sort_values(ascending=False)
        .to_frame()
    )
    building_type_weights["share"] = building_type_weights["represented_units"] / total_units

    seasonal_profile = (
        per_home.groupby(["season", "time_of_day"])["electric_kw_per_home"]
        .mean()
        .reset_index()
    )

    peak_row = per_home.loc[per_home["electric_kw_per_home"].idxmax()]

    summary = pd.DataFrame(
        [
            ("represented_units", total_units),
            ("annual_kwh_per_home", per_home["electric_kwh_per_home"].sum()),
            ("average_daily_kwh_per_home", per_home["electric_kwh_per_home"].sum() / 365),
            ("peak_kw_per_home", peak_row["electric_kw_per_home"]),
            ("peak_timestamp", peak_row["timestamp"].isoformat()),
            ("minimum_kw_per_home", per_home["electric_kw_per_home"].min()),
        ],
        columns=["metric", "value"],
    )

    per_home.to_csv(output_dir / "nc_representative_profile_15min.csv", index=False)
    hourly.reset_index().to_csv(output_dir / "nc_representative_profile_hourly.csv", index=False)
    monthly.reset_index().to_csv(output_dir / "nc_monthly_kwh_per_home.csv", index=False)
    top_end_uses.to_csv(output_dir / "nc_top_end_uses_kwh_per_home.csv", header=True)
    building_type_weights.to_csv(output_dir / "nc_building_type_weights.csv")
    summary.to_csv(output_dir / "nc_profile_summary.csv", index=False)

    fig, axes = plt.subplots(3, 1, figsize=(14, 14), constrained_layout=True)

    axes[0].plot(daily.index, daily["electric_kw_per_home"], color="#0b6e4f", linewidth=1.5)
    axes[0].set_title("NC Representative Residential Electric Load, Daily Mean")
    axes[0].set_ylabel("kW per home")
    axes[0].grid(alpha=0.25)

    season_order = ["Winter", "Spring", "Summer", "Fall"]
    season_colors = {
        "Winter": "#355070",
        "Spring": "#6d597a",
        "Summer": "#e56b6f",
        "Fall": "#b56576",
    }
    for season in season_order:
        subset = seasonal_profile[seasonal_profile["season"] == season]
        axes[1].plot(
            subset["time_of_day"],
            subset["electric_kw_per_home"],
            label=season,
            linewidth=2,
            color=season_colors[season],
        )
    axes[1].set_title("Average 15-Minute Load Shape by Season")
    axes[1].set_ylabel("kW per home")
    axes[1].set_xlabel("Time of day")
    axes[1].tick_params(axis="x", rotation=45)
    axes[1].grid(alpha=0.25)
    axes[1].legend(frameon=False, ncol=4)

    axes[2].barh(top_end_uses.index[::-1], top_end_uses.values[::-1], color="#4c956c")
    axes[2].set_title("Top Electric End Uses, Annual kWh per Home")
    axes[2].set_xlabel("kWh per home-year")
    axes[2].grid(axis="x", alpha=0.25)

    fig.savefig(output_dir / "nc_representative_profile_summary.png", dpi=180)
    plt.close(fig)

    print(summary.to_string(index=False))
    print("\nBuilding type shares:")
    print((building_type_weights["share"] * 100).round(2).to_string())
    print("\nTop electric end uses (kWh per home-year):")
    print(top_end_uses.round(1).to_string())


if __name__ == "__main__":
    main()
