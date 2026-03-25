"""
Exogenous distributed solar forecasts based on EDGS 2024 modelling assumptions.

Pipeline:
1) Load raw data from csv
2) Extract total capacity (MW) by year for com, res, and ind sectors.
3) distribute these per island according to existing island shares
4) Map EDGS Reference scenario to TIMES-NZ Traditional,
    and EDGS Innovation scenario to TIMES-NZ Transformation.
5) Export scenario workbooks.


"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from prepare_times_nz.utilities.data_in_out import _save_data
from prepare_times_nz.utilities.filepaths import (
    EXTERNAL_DATA,
    STAGE_2_DATA,
    STAGE_3_DATA,
)

# CONSTANTS

EDGS_FILEPATH = (
    Path(EXTERNAL_DATA)
    / "mbie"
    / "electricity-demand-generation-scenarios-2024-assumptions.xlsx"
)
BASE_YEAR_ELC_FILE = STAGE_2_DATA / "electricity/base_year_electricity_supply.csv"

SCENARIOS = {"Traditional": "Reference", "Transformation": "Innovation"}


OUTPUT_DIR = STAGE_3_DATA / "distributed_solar"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# Mapping for sectors
SECTOR_MAP = {
    "Commercial": "ELC_SolarDistBifacial_Commercial",
    "Residential": "ELC_SolarDistSmall_Residential",
    "Industrial": "ELC_SolarDistBifacial_Industrial",
}


def get_island_shares():
    """
    Find NI/SI share percentages of installations for each solar type
    Using base year data
    """

    df = pd.read_csv(BASE_YEAR_ELC_FILE)

    dist_solar_techs = ["SolarDistSmall", "SolarDistBifacial"]

    df = df[df["Tech_TIMES"].isin(dist_solar_techs)]
    df = df[df["Variable"] == "Capacity"]

    df = df[["PlantName", "Region", "Value"]]

    # Compute each plant's share of its region total
    region_totals = df.groupby(["PlantName"], as_index=False)["Value"].sum()
    region_totals = region_totals.rename(columns={"Value": "RegionTotal"})

    df = df.merge(region_totals, on=["PlantName"], how="left")
    df["RegionShare"] = df["Value"] / df["RegionTotal"]

    # just need shares

    df = df[["PlantName", "Region", "RegionShare"]]

    df = df.rename(columns={"PlantName": "Sector"})

    return df


def split_capacity_by_island(df):
    """Allocate capacity to islands and pivot regions into columns.

    Merges base-year island shares by sector, applies those shares to `Value`,
    drops the share column, and pivots `Region` into one `Value_<Region>` column
    per region.
    """
    # add shares
    island_shares = get_island_shares()
    df = df.merge(island_shares, on="Sector", how="left")

    # new values
    df["Value"] = df["Value"] * df["RegionShare"]
    df = df.drop(columns=["RegionShare"])

    # pivot
    id_cols = [c for c in df.columns if c not in ["Region", "Value"]]
    df = df.pivot_table(
        index=id_cols,
        columns="Region",
        values="Value",
        aggfunc="sum",
    ).reset_index()
    return df


def get_scenario_for_veda(df, mbie_scenario):
    """
    Shape to acceptable format for TFM_INS, filtered by specific mbie scenario
    """

    df = df[df["Scenario"] == mbie_scenario].copy()

    df["Attribute"] = "NCAP_PASTI"

    out_cols = ["TechName", "Year", "Attribute", "NI", "SI"]

    df = df[out_cols]

    return df


def save_solar_data_for_scenario(df, scenario):
    """
    Filters df for scenario, formats for veda,
    saves to correct output dir
    """

    out = get_scenario_for_veda(df, SCENARIOS[scenario])
    filename = f"distributed_solar_{scenario}.csv"
    label = f"Distributed solar data ({scenario})"
    _save_data(out, filename, label, OUTPUT_DIR)


def get_cumulative_build_projections():
    """Load EDGS distributed solar assumptions and compute annual builds.

    Reads the "Distributed solar PV" sheet, filters to cumulative new capacity,
    maps sectors to TIMES-NZ technologies, and converts cumulative values to
    annual additions by scenario and technology.
    """
    # Load the Distributed solar PV sheet
    df = pd.read_excel(EDGS_FILEPATH, sheet_name="Distributed solar PV")

    # Filter for Variable: Total capacity
    df = df[df["Variable"] == "Cumulative new capacity"]

    # Map TimePeriod to Year
    df = df.rename(columns={"TimePeriod": "Year"})
    df = df[df["Year"] >= 2024]

    # Map sectors
    df["TechName"] = df["Sector"].map(SECTOR_MAP)
    df = df[df["TechName"].notnull()]

    # Sort for diff calculation
    df = df.sort_values(["Scenario", "TechName", "Year"])

    # Compute annual new capacity
    df["Value"] = (
        df.groupby(["Scenario", "TechName"])["Value"].diff().fillna(df["Value"])
    )

    # convert GW
    df["Value"] = df["Value"] / 1e3
    df["Unit"] = "GW"

    return df


def main():
    """Main execution function."""
    df = get_cumulative_build_projections()
    df = split_capacity_by_island(df)

    save_solar_data_for_scenario(df, "Traditional")
    save_solar_data_for_scenario(df, "Transformation")


if __name__ == "__main__":
    main()
