"""
Compare postprocessed TIMES-NZ outputs against historical calibration data.

Currently includes emissions calibration tables for:
- total energy emissions
- transport emissions
- electricity consumption
- electricity generation
"""

from pathlib import Path

import pandas as pd

# pylint: disable = import-error
from times_nz_internal_qa.utilities.filepaths import FINAL_DATA

BASE_DIR = Path(__file__).resolve().parent
CALIBRATION_DATA = BASE_DIR / "calibration_data"
OUTPUT_DIR = BASE_DIR / "results"
GWH_PER_PJ = 277.77777778


ASSESSMENT_YEARS = [2023]
MODELLED_GENERATION_CATEGORY_MAP = {
    "Hydro (Run-of-river)": "Hydro",
    "Hydro (Schedulable)": "Hydro",
    "Geothermal": "Geothermal",
    "Geothermal Cogen": "Geothermal",
    "Reciprocating Biogas": "Biogas",
    "Biogas Cogen": "Biogas",
    "Wood Cogen": "Wood",
    "Onshore wind": "Wind",
    "Distributed solar": "Solar",
    "Utility Solar (Tracking)": "Solar",
    "Diesel peaker": "Oil",
    "Coal Cogen": "Coal",
    "CCGT": "Gas",
    "Natural gas peaker": "Gas",
    "Natural gas cogen": "Gas",
}
RANKINE_FUEL_TO_GENERATION_CATEGORY_MAP = {
    "Coal": "Coal",
    "Natural gas": "Gas",
}


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


def get_historical_electricity_generation():
    """Load historical electricity generation in MBIE categories."""
    df = pd.read_csv(CALIBRATION_DATA / "electricity.csv")
    df = df[df["Category"] == "Net generation"].copy()
    df = df.melt(
        id_vars=["Category", "sector", "Unit"],
        var_name="Period",
        value_name="HistoricalValue",
    )
    df["Period"] = pd.to_numeric(df["Period"], errors="coerce")
    df["HistoricalValue"] = pd.to_numeric(df["HistoricalValue"], errors="coerce")
    df = df.dropna(subset=["Period", "HistoricalValue"])
    return df.rename(columns={"sector": "GenerationCategory"})


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


def get_modelled_electricity_generation():
    """
    Aggregate modelled electricity generation to MBIE categories.

    Rankine output is split between Coal and Gas using the modelled Rankine
    fuel-use shares for each scenario and period.
    """
    df = get_times_data("elec_generation.parquet")
    generation = df[df["Variable"] == "Electricity generation"].copy()
    rankine_generation = generation[generation["Technology"] == "Rankine"].copy()
    non_rankine_generation = generation[generation["Technology"] != "Rankine"].copy()

    non_rankine_generation["GenerationCategory"] = non_rankine_generation[
        "Technology"
    ].map(MODELLED_GENERATION_CATEGORY_MAP)

    unmapped = (
        non_rankine_generation[non_rankine_generation["GenerationCategory"].isna()][
            "Technology"
        ]
        .dropna()
        .drop_duplicates()
        .tolist()
    )
    if unmapped:
        print(
            "Unmapped electricity generation technologies excluded from calibration:",
            ", ".join(sorted(unmapped)),
        )

    non_rankine_generation = non_rankine_generation[
        non_rankine_generation["GenerationCategory"].notna()
    ].copy()
    non_rankine_generation = (
        non_rankine_generation.groupby(
            ["Scenario", "GenerationCategory", "Period"], as_index=False
        )["Value"]
        .sum()
        .rename(columns={"Value": "ModelledValue"})
    )
    rankine_fuel_use = df[df["Variable"] == "Electricity fuel use"].copy()
    rankine_fuel_use = rankine_fuel_use[
        rankine_fuel_use["Technology"] == "Rankine"
    ].copy()
    rankine_fuel_use["GenerationCategory"] = rankine_fuel_use["Fuel"].map(
        RANKINE_FUEL_TO_GENERATION_CATEGORY_MAP
    )
    rankine_fuel_use = rankine_fuel_use[
        rankine_fuel_use["GenerationCategory"].notna()
    ].copy()
    rankine_fuel_use = rankine_fuel_use.groupby(
        ["Scenario", "Period", "GenerationCategory"], as_index=False
    )["Value"].sum()
    rankine_totals = rankine_fuel_use.groupby(["Scenario", "Period"], as_index=False)[
        "Value"
    ].sum()
    rankine_totals = rankine_totals.rename(columns={"Value": "RankineFuelTotal"})
    rankine_fuel_use = rankine_fuel_use.merge(
        rankine_totals,
        on=["Scenario", "Period"],
        how="left",
    )
    rankine_fuel_use["RankineShare"] = (
        rankine_fuel_use["Value"] / rankine_fuel_use["RankineFuelTotal"]
    )

    rankine_generation = rankine_generation.groupby(
        ["Scenario", "Period"], as_index=False
    )["Value"].sum()
    rankine_generation = rankine_generation.merge(
        rankine_fuel_use[["Scenario", "Period", "GenerationCategory", "RankineShare"]],
        on=["Scenario", "Period"],
        how="left",
    )
    rankine_generation = rankine_generation[
        rankine_generation["GenerationCategory"].notna()
    ].copy()
    rankine_generation["ModelledValue"] = (
        rankine_generation["Value"] * rankine_generation["RankineShare"]
    )
    rankine_generation = rankine_generation[
        ["Scenario", "GenerationCategory", "Period", "ModelledValue"]
    ]

    modelled = pd.concat(
        [non_rankine_generation, rankine_generation],
        ignore_index=True,
    )
    modelled = modelled.groupby(
        ["Scenario", "GenerationCategory", "Period"], as_index=False
    )["ModelledValue"].sum()
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


def build_total_electricity_consumption_comparison(electricity_consumption_comparison):
    """Return a total electricity consumption comparison table."""
    comparison = (
        electricity_consumption_comparison.groupby(
            ["Scenario", "Period"], as_index=False
        )[["HistoricalValue", "ModelledValue"]]
        .sum()
        .assign(Metric="Total electricity consumption")
    )
    comparison["Difference"] = (
        comparison["ModelledValue"] - comparison["HistoricalValue"]
    )
    comparison["PercentDifference"] = (
        comparison["Difference"] / comparison["HistoricalValue"] * 100
    )
    return comparison[
        [
            "Metric",
            "Scenario",
            "Period",
            "HistoricalValue",
            "ModelledValue",
            "Difference",
            "PercentDifference",
        ]
    ].sort_values(["Period", "Scenario"])


def build_electricity_generation_comparison():
    """Return the electricity generation calibration comparison table."""
    historical = get_historical_electricity_generation()
    modelled = get_modelled_electricity_generation()

    historical_years = sorted(historical["Period"].unique())
    modelled = modelled[modelled["Period"].isin(historical_years)].copy()
    scenarios = pd.DataFrame({"Scenario": sorted(modelled["Scenario"].unique())})
    historical_index = historical[
        ["GenerationCategory", "Period", "HistoricalValue"]
    ].copy()
    historical_index["key"] = 1
    scenarios["key"] = 1
    comparison = historical_index.merge(scenarios, on="key", how="left").drop(
        columns="key"
    )
    comparison = comparison.merge(
        modelled[["Scenario", "GenerationCategory", "Period", "ModelledValue"]],
        on=["Scenario", "GenerationCategory", "Period"],
        how="left",
    )
    comparison["ModelledValue"] = comparison["ModelledValue"].fillna(0)

    comparison["Difference"] = (
        comparison["ModelledValue"] - comparison["HistoricalValue"]
    )
    comparison["PercentDifference"] = (
        comparison["Difference"] / comparison["HistoricalValue"] * 100
    )

    comparison = comparison[
        [
            "GenerationCategory",
            "Scenario",
            "Period",
            "HistoricalValue",
            "ModelledValue",
            "Difference",
            "PercentDifference",
        ]
    ].sort_values(["Scenario", "GenerationCategory", "Period"])

    return comparison


def build_total_generation_comparison(electricity_generation_comparison):
    """Return a total electricity generation comparison table."""
    comparison = (
        electricity_generation_comparison.groupby(
            ["Scenario", "Period"], as_index=False
        )[["HistoricalValue", "ModelledValue"]]
        .sum()
        .assign(Metric="Total generation")
    )
    comparison["Difference"] = (
        comparison["ModelledValue"] - comparison["HistoricalValue"]
    )
    comparison["PercentDifference"] = (
        comparison["Difference"] / comparison["HistoricalValue"] * 100
    )
    return comparison[
        [
            "Metric",
            "Scenario",
            "Period",
            "HistoricalValue",
            "ModelledValue",
            "Difference",
            "PercentDifference",
        ]
    ].sort_values(["Period", "Scenario"])


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


def main():
    """Run calibration comparisons and print summary tables."""
    emissions_comparison = build_emissions_comparison()
    electricity_consumption_comparison = build_electricity_consumption_comparison()
    total_electricity_consumption_comparison = (
        build_total_electricity_consumption_comparison(
            electricity_consumption_comparison
        )
    )
    electricity_generation_comparison = build_electricity_generation_comparison()
    total_generation_comparison = build_total_generation_comparison(
        electricity_generation_comparison
    )
    emissions_comparison = filter_assessment_years(emissions_comparison)
    electricity_consumption_comparison = filter_assessment_years(
        electricity_consumption_comparison
    )
    total_electricity_consumption_comparison = filter_assessment_years(
        total_electricity_consumption_comparison
    )
    electricity_generation_comparison = filter_assessment_years(
        electricity_generation_comparison
    )
    total_generation_comparison = filter_assessment_years(total_generation_comparison)
    for metric, metric_df in emissions_comparison.groupby("Metric", sort=False):
        print(f"\n{metric}")
        print(format_table(metric_df).to_string(index=False))

    print("\nElectricity consumption")
    print(format_table(electricity_consumption_comparison).to_string(index=False))

    print("\nTotal electricity consumption")
    print(format_table(total_electricity_consumption_comparison).to_string(index=False))

    print("\nElectricity generation")
    print(format_table(electricity_generation_comparison).to_string(index=False))

    print("\nTotal generation")
    print(format_table(total_generation_comparison).to_string(index=False))


if __name__ == "__main__":
    main()
