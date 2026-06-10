"""
Prepare tidy datasets for analysis charting.

This module reads final TIMES output datasets, applies light aggregation or
classification, and returns dataframes intended for plotting use. It also
contains the small amount of comparison-data loading used by the analysis
charts.

It's a bit more adhoc than other modules for retrieval, as it's designed
to create small, custom datasets for specific purposes.
"""

import numpy as np
import pandas as pd
from times_nz_internal_qa.utilities.filepaths import (
    CONCORDANCE_PATCHES,
    FINAL_DATA,
    PREP_STAGE_3,
)

# Scenario display names ------------------------------------------------------

SCENARIO_MAP = {"steady-v307": "Steady", "shift-v307": "Shift"}


# Renewable fuel classifications ----------------------------------------------


def get_renewable_fuels():
    """
    Returns a df of each named fuel in the database, including a Renewable flag
    This is based on a raw input dataset which is also used for code concordance, so missing
    entries from the model are flagged in post-processing.

    All renewable definitions will be based on this input fuel

    Note: electricity is usually a mix of the two, so is flagged "electricity"
        and should be handled separately in renewable analysis
    """

    df = pd.read_csv(CONCORDANCE_PATCHES / "code_mapping/fuel_codes.csv")

    df = df.rename(columns={"Commodity": "Fuel"})

    return df[["Fuel", "Renewable"]]


# External comparison datasets ------------------------------------------------


def get_other_model_generation():
    """Reads pre-tidied df of non-TIMES generation results"""
    return pd.read_csv("analysis/data/other_model_gen.csv")


def get_other_model_emissions():
    """Reads pre-tidied df of non-TIMES emissions results"""
    return pd.read_csv("analysis/data/other_model_ems.csv")


# Final TIMES output loading --------------------------------------------------


def get_times_data(filename):
    """Read a final TIMES parquet file and map scenario codes to display names."""

    # read parquet
    df = pd.read_parquet(FINAL_DATA / filename)
    df["Scenario"] = df["Scenario"].map(SCENARIO_MAP)
    return df


def as_filter_list(values):
    """Return list-like filter values, with None or empty meaning no filter."""

    if values is None:
        return []
    if isinstance(values, str):
        return [values]
    return list(values)


def apply_filter_list(df, column, values):
    """Filter a dataframe column by list-like values if any are provided."""

    values = as_filter_list(values)
    if not values:
        return df
    return df[df[column].isin(values)]


def normalise_scenario_filter(scenarios):
    """Allow scenario filters to use either raw scenario codes or display names."""

    scenarios = as_filter_list(scenarios)
    return [SCENARIO_MAP.get(scenario, scenario) for scenario in scenarios]


# Main analysis datasets ------------------------------------------------------


def get_elec_gen(compare_other_models=False, groupby_cols=None):
    """Return annual electricity generation in TWh, optionally grouped by extra columns."""

    df = get_times_data("elec_generation.parquet")
    df = df[df["Variable"] == "Electricity generation"]

    if groupby_cols is None:
        groupby_cols = []
    elif isinstance(groupby_cols, str):
        groupby_cols = [groupby_cols]
    else:
        groupby_cols = list(groupby_cols)

    if groupby_cols and compare_other_models:
        raise ValueError(
            "compare_other_models cannot be used with detailed groupby_cols."
        )

    groupby_cols = ["Scenario", "Period", "Unit"] + groupby_cols
    df = df.groupby(groupby_cols)["Value"].sum().reset_index()
    df["Value"] = df["Value"] * 277.77777778
    df["Value"] = df["Value"] / 1000
    df["Unit"] = "TWh"
    if compare_other_models:
        # get electricity data
        other_model_gen = get_other_model_generation()
        df = pd.concat([df, other_model_gen])

    return df


def get_thermal_generation_fuel_use():
    """Return fuel used by thermal electricity generation plants in PJ."""

    df = get_times_data("elec_generation.parquet")
    df = df[df["Variable"] == "Electricity fuel use"]
    df = df[df["TechnologyGroup"] == "Thermal"]
    df = df.groupby(["Scenario", "Period", "Unit", "Fuel"])["Value"].sum().reset_index()
    return df


def get_battery_capacity(groupby_cols="TechnologyGroup"):
    """Return battery capacity in GW, grouped by technology group by default."""

    df = get_times_data("batteries.parquet")
    df = df[df["Variable"] == "Capacity"]

    if groupby_cols is None:
        groupby_cols = []
    elif isinstance(groupby_cols, str):
        groupby_cols = [groupby_cols]
    else:
        groupby_cols = list(groupby_cols)

    groupby_cols = ["Scenario", "Period", "Unit"] + groupby_cols
    df = df.groupby(groupby_cols)["Value"].sum().reset_index()
    return df


def get_transport_capacity(enduse_list):
    """Return light passenger vehicle capacity by technology group."""

    df = get_times_data("transport_capacity.parquet")

    # print('transport enduses')
    # for e in df["EndUse"].unique():
    #   print(e)
    df = df[df["EndUse"].isin(enduse_list)]
    df = (
        df.groupby(["Scenario", "Period", "Unit", "TechnologyGroup", "EndUse"])["Value"]
        .sum()
        .reset_index()
    )
    # ensure 0s
    df.loc[df["Value"].abs() < 1e-6, "Value"] = 0
    df["Unit"] = "Thousand vehicles"
    return df


def get_lpv_transport_capacity():
    """
    Getting transport capacity for LPV
    """
    df = get_transport_capacity(["Light Passenger Vehicle"])
    df = (
        df.groupby(["Scenario", "Period", "Unit", "TechnologyGroup"])["Value"]
        .sum()
        .reset_index()
    )
    return df


def get_lcv_transport_capacity():
    """
    Getting transport capacity for LPV
    """
    df = get_transport_capacity(["Light Commercial Vehicle"])
    df = (
        df.groupby(["Scenario", "Period", "Unit", "TechnologyGroup"])["Value"]
        .sum()
        .reset_index()
    )
    return df


def get_truck_transport_capacity():
    """
    truck capacity. migrate these filter methods to chart section, probably
    """

    truck_list = [
        "Heavy Truck",
        "Light Truck",
        "Medium Truck",
    ]

    return get_transport_capacity(truck_list)


def get_emissions(compare_other_models=False):
    """Return annual energy emissions by scenario in megatonnes CO2e."""

    df = get_times_data("emissions.parquet")
    df = df.groupby(["Scenario", "Period", "Unit"])["Value"].sum().reset_index()

    df["Value"] = df["Value"] / 1000
    df["Unit"] = "MT CO2e"

    if compare_other_models:
        # get emissions data
        other_model_ems = get_other_model_emissions()
        df = pd.concat([df, other_model_ems])

    return df


def get_emissions_by_sector_group():
    """Return annual energy emissions by scenario, year, and sector group."""

    df = get_times_data("emissions.parquet")
    df = (
        df.groupby(["Scenario", "Period", "Unit", "SectorGroup"])["Value"]
        .sum()
        .reset_index()
    )
    df["Value"] = df["Value"] / 1000
    df["Unit"] = "MT CO2e"
    return df


def get_fuel_use_by_island_and_sector(end_use=None, sector_group=None, scenario=None):
    """
    Return fuel use by island, sector, and fuel for configurable filter lists.

    Args:
        end_use: EndUse values to include. None or an empty list includes all.
        sector_group: SectorGroup values to include. None or an empty list includes all.
        scenario: Scenario display names or raw scenario codes to include. None
            or an empty list includes all.
    """

    df = get_times_data("energy_demand.parquet")
    df = df[df["Variable"] == "Energy demand"].copy()

    df = apply_filter_list(df, "EndUse", end_use)
    df = apply_filter_list(df, "SectorGroup", sector_group)
    df = apply_filter_list(df, "Scenario", normalise_scenario_filter(scenario))

    island_map = {
        "NI": "North Island",
        "SI": "South Island",
    }
    df["Island"] = df["Region"].map(island_map).fillna(df["Region"])

    df = (
        df.groupby(
            [
                "Scenario",
                "Period",
                "Unit",
                "Island",
                "SectorGroup",
                "Sector",
                "Fuel",
            ]
        )["Value"]
        .sum()
        .reset_index()
    )
    df.loc[df["Value"].abs() < 1e-6, "Value"] = 0
    return df


def get_process_heat():
    """Return industrial process heat demand by scenario, year, and fuel."""

    df = get_times_data("energy_demand.parquet")

    # industrial process heat

    df = df[df["SectorGroup"] == "Industry"]
    df = df[df["EnduseGroup"] == "Heating/Cooling"]

    heat_uses = [
        "Intermediate Heat (100-300 C), Process Requirements",
        "High Temperature Heat (>300 C), Process Requirements",
        "Low Temperature Heat (<100 C), Process Requirements",
    ]

    df = df[df["EndUse"].isin(heat_uses)]

    # agg fuels a bit more
    fuel_map = {
        "Biogas": "Biogas",
        "Coal": "Coal",
        "Diesel": "Other",
        "Electricity": "Electricity",
        "Fuel oil": "Other",
        "Geothermal": "Other",
        "LPG": "Other",
        "Natural gas": "Natural gas",
        "Wood": "Biomass",
        "Wood residuals (onsite)": "Biomass",
    }

    df["Fuel"] = df["Fuel"].map(fuel_map)
    df = df.groupby(["Scenario", "Period", "Unit", "Fuel"])["Value"].sum().reset_index()

    return df


# Renewable share metrics -----------------------------------------------------


def get_renewable_electricity_share():
    """
    Return renewable electricity generation share by scenario and year.

    Renewable electricity is allocated from plant-level input fuel shares rather
    than from fixed technology labels. For each scenario, period, process,
    region, and vintage, the function calculates:

        renewable fuel use / total fuel use

    It then applies that renewable input share to the matching electricity
    generation output for the plant. This means a mixed-fuel unit, such as a gas
    peaker using both natural gas and biogas, receives a partial renewable
    generation allocation. The method assumes each fuel has the same conversion
    efficiency within a mixed-fuel plant.

    Returns:
        A dataframe with Scenario, Period, Unit, and
        RenewableShareOfElectricity. The share is returned as a decimal from
        0 to 1, not a percentage.

    Raises:
        ValueError: If any electricity fuel use lacks a renewable fuel
            classification, or if generation cannot be matched to a fuel-use
            share.
    """

    df = get_times_data("elec_generation.parquet")

    plant_keys = ["Scenario", "Period", "Process", "Region", "Vintage"]

    # Classify each input fuel as renewable or non-renewable.
    fuel_use = df[df["Variable"] == "Electricity fuel use"].copy()
    fuel_use = fuel_use.merge(
        get_renewable_fuels(),
        on="Fuel",
        how="left",
        validate="many_to_one",
    )

    missing_fuels = sorted(
        fuel_use.loc[fuel_use["Renewable"].isna(), "Fuel"].dropna().unique()
    )
    if missing_fuels:
        raise ValueError(
            "Missing renewable fuel classification for: " + ", ".join(missing_fuels)
        )

    # Calculate each plant's annual renewable input share.
    fuel_use["RenewableFuelUse"] = np.where(
        fuel_use["Renewable"] == "Renewable",
        fuel_use["Value"],
        0,
    )

    plant_fuel_share = (
        fuel_use.groupby(plant_keys, dropna=False)
        .agg(
            TotalFuelUse=("Value", "sum"),
            RenewableFuelUse=("RenewableFuelUse", "sum"),
        )
        .reset_index()
    )
    plant_fuel_share["RenewableFuelShare"] = np.where(
        plant_fuel_share["TotalFuelUse"] == 0,
        np.nan,
        plant_fuel_share["RenewableFuelUse"] / plant_fuel_share["TotalFuelUse"],
    )

    # Apply the plant input share to matching generation output.
    generation = df[df["Variable"] == "Electricity generation"].copy()
    generation = generation.merge(
        plant_fuel_share[plant_keys + ["RenewableFuelShare"]],
        on=plant_keys,
        how="left",
        validate="many_to_one",
    )

    missing_share = generation["RenewableFuelShare"].isna() & generation["Value"].ne(0)
    if missing_share.any():
        missing_plants = sorted(generation.loc[missing_share, "Process"].unique())
        raise ValueError(
            "Missing fuel-use renewable share for generation from: "
            + ", ".join(missing_plants)
        )

    # Multi-fuel plants are allocated by input fuel share, assuming equal efficiency.
    generation["RenewableGeneration"] = generation["Value"] * generation[
        "RenewableFuelShare"
    ].fillna(0)

    # Aggregate all plant-level allocations to scenario/year electricity share.
    df = generation.groupby(["Scenario", "Period"], as_index=False).agg(
        TotalGeneration=("Value", "sum"),
        RenewableGeneration=("RenewableGeneration", "sum"),
    )
    df["RenewableShareOfElectricity"] = np.where(
        df["TotalGeneration"] == 0,
        np.nan,
        df["RenewableGeneration"] / df["TotalGeneration"],
    )
    df["Unit"] = "Share"

    return df[["Scenario", "Period", "Unit", "RenewableShareOfElectricity"]]


def get_renewable_tfec():
    """
    Return renewable share of total final energy consumption by scenario and year.

    Direct fuel demand is classified with the renewable fuel concordance:
    renewable fuels count as 100% renewable, non-renewable fuels count as 0%,
    and electricity is allocated using the scenario/year renewable electricity
    share calculated by get_renewable_electricity_share(). International
    aviation and international shipping are excluded from both the numerator and
    denominator.

    Returns:
        A dataframe with Scenario, Period, Unit, and RenewableShareOfTFEC. The
        share is returned as a decimal from 0 to 1, not a percentage.

    Raises:
        ValueError: If any final energy fuel lacks a renewable classification,
            or if electricity demand cannot be matched to a renewable
            electricity share.
    """

    df = get_times_data("energy_demand.parquet")
    df = df[df["Variable"] == "Energy demand"].copy()
    df = df[~df["EndUse"].isin(["International Aviation", "International Shipping"])]

    # Classify all direct final energy fuels.
    df = df.merge(
        get_renewable_fuels(),
        on="Fuel",
        how="left",
        validate="many_to_one",
    )

    missing_fuels = sorted(df.loc[df["Renewable"].isna(), "Fuel"].dropna().unique())
    if missing_fuels:
        raise ValueError(
            "Missing renewable fuel classification for: " + ", ".join(missing_fuels)
        )

    # Electricity receives the modelled renewable generation share for that year.
    electricity_share = get_renewable_electricity_share()[
        ["Scenario", "Period", "RenewableShareOfElectricity"]
    ]
    df = df.merge(
        electricity_share,
        on=["Scenario", "Period"],
        how="left",
        validate="many_to_one",
    )

    missing_electricity_share = (
        (df["Renewable"] == "Electricity")
        & df["RenewableShareOfElectricity"].isna()
        & df["Value"].ne(0)
    )
    if missing_electricity_share.any():
        missing_periods = (
            df.loc[missing_electricity_share, ["Scenario", "Period"]]
            .drop_duplicates()
            .sort_values(["Scenario", "Period"])
        )
        missing_periods = [
            f"{row.Scenario} {row.Period}" for row in missing_periods.itertuples()
        ]
        raise ValueError(
            "Missing renewable electricity share for electricity demand in: "
            + ", ".join(missing_periods)
        )

    df["RenewableDemandShare"] = np.where(df["Renewable"] == "Renewable", 1.0, 0.0)
    df.loc[df["Renewable"] == "Electricity", "RenewableDemandShare"] = df.loc[
        df["Renewable"] == "Electricity", "RenewableShareOfElectricity"
    ]
    df["RenewableFinalEnergyConsumption"] = df["Value"] * df[
        "RenewableDemandShare"
    ].fillna(0)

    df = df.groupby(["Scenario", "Period"], as_index=False).agg(
        TotalFinalEnergyConsumption=("Value", "sum"),
        RenewableFinalEnergyConsumption=(
            "RenewableFinalEnergyConsumption",
            "sum",
        ),
    )
    df["RenewableShareOfTFEC"] = np.where(
        df["TotalFinalEnergyConsumption"] == 0,
        np.nan,
        df["RenewableFinalEnergyConsumption"] / df["TotalFinalEnergyConsumption"],
    )
    df["Unit"] = "Share"

    return df[["Scenario", "Period", "Unit", "RenewableShareOfTFEC"]]


def get_genstack():
    """
    This function relies on the workflow for PREPARE-TIMES-NZ

    as it uses the data_intermediate folders
    """

    genstack = pd.read_csv(PREP_STAGE_3 / "electricity/genstack.csv")

    return genstack


# Scratch entrypoint ----------------------------------------------------------


def main():
    """entrypoint (scratch only)"""
    get_lpv_transport_capacity()


if __name__ == "__main__":
    main()
