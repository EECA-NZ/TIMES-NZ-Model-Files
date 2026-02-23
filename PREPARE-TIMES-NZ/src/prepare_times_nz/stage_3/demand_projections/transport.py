"""
This module creates indices for transport
demand projections based on MOT Base EV scenario.

We used the same indices for both Traditional
and Transformation scenarios.

- Input data: data_raw/external_data/mot/VFM202405_outputs_summary_V3
"""

import numpy as np
import pandas as pd
from prepare_times_nz.stage_0.stage_0_settings import BASE_YEAR
from prepare_times_nz.stage_3.demand_projections.population_projections import (
    get_national_population_growth_index,
)
from prepare_times_nz.utilities.data_in_out import _save_data
from prepare_times_nz.utilities.filepaths import EXTERNAL_DATA, STAGE_3_DATA

# CONSTANTS
# file paths
INPUT_DATA = EXTERNAL_DATA / "mot"
OUTPUT = STAGE_3_DATA / "demand_projections"

END_YEAR = 2050


# HELPERS
def save_tra_proj_data(df, name, label):
    """save data wrapper"""
    label = "Saving transport demand projections (" + label + ")"
    _save_data(df, name, label, filepath=OUTPUT)


# FUNCTIONS


def get_transport_growth_indices():
    """
    Creates yearly indices for transport sectors (BASE_YEAR–END_YEAR):
    - Aggregate vkt by veh_type & year (Base_EV only)
    - Index(Year>BASE_YEAR) = vkt(Year) / vkt(Year-1)
    - Index(BASE_YEAR) = 1.0
    Returns long format: [SectorGroup, Sector, Year, Scenario, Index]
    """
    # Load data
    df = pd.read_excel(
        INPUT_DATA / "VFM202405_outputs_summary_V3.xlsx",
        sheet_name="Raw data (wem202405)",
        skiprows=2,
    )

    # Keep needed cols and coerce types
    df = df[["scenario", "veh_type", "year", "vkt"]].copy()

    df["vkt"] = pd.to_numeric(df["vkt"], errors="coerce")
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df = df.dropna(subset=["vkt", "year"])

    # Filter range & scenario
    df = df[
        (df["year"] >= BASE_YEAR)
        & (df["year"] <= END_YEAR)
        & (df["scenario"] == "Base_EV")
    ].copy()

    # Aggregate
    df = df.groupby(["veh_type", "year"], as_index=False, dropna=False)["vkt"].sum()

    # Standardize names
    df = df.rename(columns={"veh_type": "Sector", "year": "Year"})

    # create index
    base_df = df[df["Year"] == BASE_YEAR].copy()
    base_df = base_df.rename(columns={"vkt": "vkt_base"})
    base_df = base_df.drop("Year", axis=1)
    df = df.merge(base_df, on=["Sector"], how="left")
    df["Index"] = df["vkt"] / df["vkt_base"]

    # After aggregating VKT but before computing indices
    # Create mapping for vehicle type renaming
    veh_type_map = {
        "L Truck": "Light Truck",
        "M Truck": "Medium Truck",
        "H Truck": "Heavy Truck",
    }

    # Rename vehicle types
    df["Sector"] = df["Sector"].replace(veh_type_map)

    # Add new Light Truck category by copying Medium Truck indices
    medium_truck = df[df["Sector"] == "Medium Truck"].copy()
    medium_truck["Sector"] = "Light Truck"

    # Combine original and new data
    df = pd.concat([df, medium_truck], ignore_index=True)

    # Sort to ensure consistent ordering
    df = df.sort_values(["Sector", "Year"])

    # Attach metadata & scenarios (same indices for both)
    df["SectorGroup"] = "Transport"
    scenarios = pd.DataFrame({"Scenario": ["Traditional", "Transformation"]})
    df = (
        df[["SectorGroup", "Sector", "Year", "Index"]]
        .assign(key=1)
        .merge(scenarios.assign(key=1), on="key")
        .drop(columns="key")[["SectorGroup", "Sector", "Year", "Scenario", "Index"]]
        .sort_values(["Scenario", "Sector", "Year"], ascending=[True, True, True])
    )
    return df


def get_reduced_demand_index(scale=0.01):
    """
    Uses population projection index and reduces these by an annual rate of 1% a year
    annual decline of per-capita demand can be adjusted via scale variable
    This becomes our simple index of reduced VKT growth
    """

    df = get_national_population_growth_index("50th percentile (median)")

    df = df.sort_values("Year").reset_index()
    df["ReducedIndex"] = df["Index"] * ((1 - scale) ** df.index)
    df = df[["Year", "ReducedIndex"]]

    return df


def main():
    """Script entrypoint"""

    df = get_transport_growth_indices()
    # get reduced indexes
    reduced_index = get_reduced_demand_index()
    sectors_to_reduce = ["LCV", "LPV"]
    df = df.merge(reduced_index, on="Year", how="left")

    # apply the new index for selected cases

    df["Index"] = np.where(
        (df["Sector"].isin(sectors_to_reduce)) & (df["Scenario"] == "Transformation"),
        df["ReducedIndex"],
        df["Index"],
    )

    df = df.drop("ReducedIndex", axis=1)
    save_tra_proj_data(df, "transport_demand_index.csv", "Transport demand index")


if __name__ == "__main__":

    main()
