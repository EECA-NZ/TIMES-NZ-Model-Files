"""
Compare postprocessed TIMES-NZ outputs against historical calibration data.

Currently includes emissions calibration tables for:
- total energy emissions
- transport emissions
- electricity consumption
"""

from pathlib import Path

import pandas as pd
from times_nz_internal_qa.utilities.filepaths import FINAL_DATA

BASE_DIR = Path(__file__).resolve().parent
CALIBRATION_DATA = BASE_DIR / "calibration_data"
OUTPUT_DIR = BASE_DIR / "results"
GWH_PER_PJ = 277.77777778


ASSESSMENT_YEARS = [2023]


def get_times_data(filename):
    """Read postprocessed TIMES data."""
    return pd.read_parquet(FINAL_DATA / filename)


def get_historical_emissions():
    """Load historical calibration emissions and reshape to long format."""
    df = pd.read_csv(CALIBRATION_DATA / "emissions.csv")
    df = df.melt(
        id_vars="Sector",
        var_name="Period",
        value_name="HistoricalValue",
    )
    df["Period"] = pd.to_numeric(df["Period"], errors="coerce")
    df["HistoricalValue"] = pd.to_numeric(df["HistoricalValue"], errors="coerce")
    return df.dropna(subset=["Period", "HistoricalValue"])


def get_historical_electricity_consumption():
    """
    Load historical electricity consumption and align it with model sectors.

    Historical unallocated onsite consumption is compared as part of industrial
    demand because that load is assigned to industry in the model outputs.
    """
    df = pd.read_csv(CALIBRATION_DATA / "electricity.csv")
    df = df[df["Category"] == "Consumption"].copy()
    df = df.melt(
        id_vars=["Category", "sector", "Unit"],
        var_name="Period",
        value_name="HistoricalValue",
    )
    df["Period"] = pd.to_numeric(df["Period"], errors="coerce")
    df["HistoricalValue"] = pd.to_numeric(df["HistoricalValue"], errors="coerce")
    df = df.dropna(subset=["Period", "HistoricalValue"])

    onsite = df[df["sector"] == "Unallocated onsite consumption"].copy()
    if not onsite.empty:
        onsite["sector"] = "Industrial"
        df = pd.concat(
            [df[df["sector"] != "Unallocated onsite consumption"], onsite],
            ignore_index=True,
        )

    return (
        df.groupby(["sector", "Period", "Unit"], as_index=False)["HistoricalValue"]
        .sum()
        .rename(columns={"sector": "Sector"})
    )


def get_modelled_emissions():
    """
    Aggregate modelled emissions to the same level as the historical calibration file.

    Historical values are in kt CO2e, matching the postprocessed emissions output.
    """
    df = get_times_data("emissions.parquet")

    total = (
        df.groupby(["Scenario", "Period"], as_index=False)["Value"]
        .sum()
        .assign(Metric="Total emissions")
    )

    transport = (
        df[df["SectorGroup"] == "Transport"]
        .groupby(["Scenario", "Period"], as_index=False)["Value"]
        .sum()
        .assign(Metric="Transport emissions")
    )

    out = pd.concat([total, transport], ignore_index=True)
    return out.rename(columns={"Value": "ModelledValue"})


def get_modelled_electricity_consumption():
    """Aggregate modelled electricity consumption to match the historical sectors."""
    df = get_times_data("energy_demand.parquet")
    df = df[df["Fuel"] == "Electricity"].copy()

    sector_map = {
        "Agriculture, Forestry, and Fishing": "Agriculture, Forestry, and Fishing",
        "Industry": "Industrial",
        "Commercial": "Commercial",
        "Residential": "Residential",
        "Transport": "Transport",
    }
    df["Sector"] = df["SectorGroup"].map(sector_map)
    df = df[df["Sector"].notna()].copy()

    modelled = (
        df.groupby(["Scenario", "Sector", "Period"], as_index=False)["Value"]
        .sum()
        .rename(columns={"Value": "ModelledValue"})
    )
    modelled["ModelledValue"] = modelled["ModelledValue"] * GWH_PER_PJ
    return modelled


def get_historical_metric_map():
    """Map historical sectors to the calibration metrics we want to compare."""
    return {
        "Energy": "Total emissions",
        "Transport": "Transport emissions",
    }


def build_emissions_comparison():
    """Return the emissions calibration comparison table."""
    historical = get_historical_emissions()
    metric_map = get_historical_metric_map()

    historical = historical[historical["Sector"].isin(metric_map)].copy()
    historical["Metric"] = historical["Sector"].map(metric_map)

    modelled = get_modelled_emissions()

    historical_years = sorted(historical["Period"].unique())
    modelled = modelled[modelled["Period"].isin(historical_years)].copy()

    comparison = modelled.merge(
        historical[["Metric", "Period", "HistoricalValue"]],
        on=["Metric", "Period"],
        how="inner",
    )

    comparison["Difference"] = (
        comparison["ModelledValue"] - comparison["HistoricalValue"]
    )
    comparison["PercentDifference"] = (
        comparison["Difference"] / comparison["HistoricalValue"] * 100
    )

    comparison = comparison[
        [
            "Metric",
            "Scenario",
            "Period",
            "HistoricalValue",
            "ModelledValue",
            "Difference",
            "PercentDifference",
        ]
    ].sort_values(["Metric", "Period", "Scenario"])

    return comparison


def build_electricity_consumption_comparison():
    """Return the electricity consumption calibration comparison table."""
    historical = get_historical_electricity_consumption()
    modelled = get_modelled_electricity_consumption()

    historical_years = sorted(historical["Period"].unique())
    modelled = modelled[modelled["Period"].isin(historical_years)].copy()

    comparison = modelled.merge(
        historical[["Sector", "Period", "HistoricalValue"]],
        on=["Sector", "Period"],
        how="inner",
    )

    comparison["Difference"] = (
        comparison["ModelledValue"] - comparison["HistoricalValue"]
    )
    comparison["PercentDifference"] = (
        comparison["Difference"] / comparison["HistoricalValue"] * 100
    )

    comparison = comparison[
        [
            "Sector",
            "Scenario",
            "Period",
            "HistoricalValue",
            "ModelledValue",
            "Difference",
            "PercentDifference",
        ]
    ].sort_values(["Scenario", "Sector", "Period"])

    return comparison


def format_table(df):
    """Format numeric columns for console-friendly table output."""
    out = df.copy()
    for col in ["HistoricalValue", "ModelledValue", "Difference"]:
        out[col] = out[col].map(lambda value: f"{value:,.2f}")
    out["PercentDifference"] = out["PercentDifference"].map(
        lambda value: f"{value:,.2f}%"
    )
    return out


def filter_assessment_years(df):
    """Restrict output rows to configured assessment years."""
    if not ASSESSMENT_YEARS:
        return df
    return df[df["Period"].isin(ASSESSMENT_YEARS)].copy()


def save_outputs(emissions_comparison, electricity_consumption_comparison):
    """Write calibration tables to CSV for easy inspection."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    emissions_comparison.to_csv(
        OUTPUT_DIR / "calibration_emissions_comparison.csv", index=False
    )
    electricity_consumption_comparison.to_csv(
        OUTPUT_DIR / "calibration_electricity_consumption_comparison.csv",
        index=False,
    )


def main():
    """Run calibration comparisons and print summary tables."""
    emissions_comparison = build_emissions_comparison()
    electricity_consumption_comparison = build_electricity_consumption_comparison()
    emissions_comparison = filter_assessment_years(emissions_comparison)
    electricity_consumption_comparison = filter_assessment_years(
        electricity_consumption_comparison
    )
    # save_outputs(emissions_comparison, electricity_consumption_comparison)

    for metric, metric_df in emissions_comparison.groupby("Metric", sort=False):
        print(f"\n{metric}")
        print(format_table(metric_df).to_string(index=False))

    print("\nElectricity consumption")
    print(format_table(electricity_consumption_comparison).to_string(index=False))


if __name__ == "__main__":
    main()
