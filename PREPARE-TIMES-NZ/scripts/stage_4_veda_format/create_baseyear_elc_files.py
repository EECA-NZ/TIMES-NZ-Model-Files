"""
Generate all Veda-ready CSVs that describe:

* electricity-input commodities and “dummy fuel” processes
* existing generation process definitions, parameters and capacities
* electricity-distribution commodity / process tables
* emission factors
"""

from __future__ import annotations

import os
from typing import Dict, Tuple

import numpy as np
import pandas as pd
from prepare_times_nz.deflator import deflate_data
from prepare_times_nz.filepaths import ASSUMPTIONS, STAGE_2_DATA, STAGE_4_DATA
from prepare_times_nz.helpers import select_and_rename, test_table_grain
from prepare_times_nz.logger_setup import logger

# --------------------------------------------------------------------------- #
# CONSTANTS
# --------------------------------------------------------------------------- #

# so ideally we would have a library script that reads the data_intermediate
# config files and returns all the useful parameters, including base year,
# but also whatever else we might need, that any script could load in.

BASE_YEAR: int = 2023
CAP2ACT_PJGW: float = 31.536  # PJ per GW at 100 % utilisation (365 * 24 / 1000)


# Filepaths ---------------------------------------------------------------- #

OUTPUT_LOCATION = STAGE_4_DATA / "base_year_elc"

ELECTRICITY_INPUT_FILE = STAGE_2_DATA / "electricity/base_year_electricity_supply.csv"

DISTRIBUTION_INPUT_FILE = (
    ASSUMPTIONS / "electricity_generation/DistributionAssumptions.csv"
)
EF_INPUT_FILE = ASSUMPTIONS / "electricity_generation/EmissionFactors.csv"


# ----- Generation units  --------------------------------------- #
GENERATION_UNIT_MAP = {
    # old_unit: (new_unit, factor)
    "MW": ("GW", 1 / 1000),
    "GWh": ("PJ", 0.0036),
    "kWh": ("MWh", 1 / 1000),
    "MWh": ("GWh", 1 / 1000),
    "2023 NZD/MWh": ("2023 $m NZD/PJ", 0.27778),
    "2023 NZD/kw": ("2023 $m NZD/GW", 1),
    "2023 NZD/GJ": ("2023 $m NZD/PJ", 1),
}

# ----- Variables in real terms ------------------------------------- #
VARIABLES_TO_DEFLATE = ["INVCOST", "VAROM", "FIXOM"]

# ----- Commodity definitions --------------------------------------- #
FI_COMM_MAP = {
    "CommoditySets": "CSets",
    "Comm-OUT": "CommName",
    "ActivityUnit": "Unit",
    "CommodityTimeSlice": "CTSLvl",
    "CommodityType": "CType",
}

# ----- Process definitions ---------------------------------------- #
FI_PROCESS_MAP = {
    "Sets": "Sets",
    "TechName": "TechName",
    "ActivityUnit": "Tact",
    "CapacityUnit": "Tcap",
    "TimeSlice": "TSlvl",
}

# ----- Process parameters ----------------------------------------- #
DISTRIBUTION_PARAMETERS_MAP = {
    "TechName": "TechName",
    "Comm-IN": "Comm-IN",
    "Comm-OUT": "Comm-OUT",
    "Region": "Region",
    "NCAP_PASTI~2015": "NCAP_PASTI~2015",
    "AF": "AF",
    "CAP2ACT": "CAP2ACT",
    "INVCOST": "INVCOST",
    "VAROM": "VAROM",
    "FIXOM": "FIXOM",
    "Efficiency": "EFF",
    "Life": "Life",
}

# --------------------------------------------------------------------------- #
# HELPERS
# --------------------------------------------------------------------------- #


def convert_units(
    df: pd.DataFrame, conversion_map: Dict[str, Tuple[str, float]]
) -> pd.DataFrame:
    """
    Convert *Value* from one unit to another according to *conversion_map*.

    Parameters
    ----------
    df
        DataFrame that contains ``Unit`` and ``Value`` columns.
    conversion_map
        Mapping of ``old_unit -> (new_unit, factor)`` where *factor*
        is multiplied into ``Value`` to obtain the new unit.

    Returns
    -------
    pd.DataFrame
        Copy of *df* with units and values converted in-place.
    """
    out = df.copy()
    for old_unit, (new_unit, factor) in conversion_map.items():
        mask = out["Unit"] == old_unit
        out.loc[mask, "Value"] = out.loc[mask, "Value"] * factor
        out.loc[mask, "Unit"] = new_unit
    return out


# --------------------------------------------------------------------- #
# LOAD DATA
# --------------------------------------------------------------------- #


def load_electricity_baseyear(filepath):
    """
    Loads the stage 2 data, and performs a rename
    Note that the rename probably should have happened in stage 2, not here
    """
    df = pd.read_csv(filepath)
    df = df.rename(columns={"Process": "TechName"})
    return df


def load_ef_data(filepath):
    """
    Loads the electricity emissions factor assumption file from path
    Adds new units to get required co2e/PJ definition
    returns df
    """

    df = pd.read_csv(filepath, encoding="utf-8-sig")

    df["kg/MJ"] = df["EF kg CO2e/unit"] / df["CV MJ/Unit"]
    df["kt CO2e/PJ"] = df["kg/MJ"] * 1e3

    return df


# --------------------------------------------------------------------- #
# PROCESS DATA
# --------------------------------------------------------------------- #


def define_commodities(df):
    """
    This section creates the tables for SECTOR_FUELS_ELC
    we have already defined ELC and ELCC02, and all the output commodities
    (like ELCDD etc) so these are just:
     - dummy commodites
     - processes for electricity input fuels.

    We extract electricity input fuels from the data,
    so this list updates automatically.

    saves outputs to csv for Veda

    """

    elc_input_commoditylist = df["Comm-IN"].unique()

    elc_input_commodity_definitions = pd.DataFrame(
        {
            "CommName": elc_input_commoditylist,
            "Csets": "NRG",
            "Unit": "PJ",
            "LimType": "FX",
        }
    )

    # ── Dummy fuel processes ──────────────────────────────────────────── #
    # We also define the dummy processes that turn the regular commodity into
    # the elc version. We'll start with the parameters (just in/out/100% efficiency)

    elc_dummy_fuel_process_parameters = pd.DataFrame()
    elc_dummy_fuel_process_parameters["Comm-Out"] = elc_input_commoditylist
    elc_dummy_fuel_process_parameters["Comm-In"] = elc_dummy_fuel_process_parameters[
        "Comm-Out"
    ].str.removeprefix("ELC")
    elc_dummy_fuel_process_parameters["TechName"] = (
        "FTE_" + elc_dummy_fuel_process_parameters["Comm-Out"]
    )
    # The next steps are just making sure the columns roughly match the TIMES 2.0
    # version, but they might actually all be unnecessary.
    elc_dummy_fuel_process_parameters = elc_dummy_fuel_process_parameters[
        ["TechName", "Comm-In", "Comm-Out"]
    ]
    elc_dummy_fuel_process_parameters["EFF"] = 1
    elc_dummy_fuel_process_parameters["Life"] = "100"
    # NOTE: we are not using these for fuel delivery costs anymore, as these
    # are done on a per-plant basis in the generation processes.

    # Dummy process definitions -----------------------------------------------------
    # Now we just provide the definitions for these processes in a separate table

    elc_dummy_fuel_process_definitions = pd.DataFrame(
        {
            "TechName": elc_dummy_fuel_process_parameters["TechName"],
            "Sets": "PRE",
            "Tact": "PJ",
            "Tcap": "GW",
        }
    )
    elc_dummy_fuel_process_definitions["Tslvl"] = np.where(
        elc_dummy_fuel_process_definitions["TechName"] == "FTE_ELCNGA",
        "DAYNITE",
        None,
    )

    # ── Save commodity tables ─────────────────────────────────────────── #

    elc_input_commodity_definitions.to_csv(
        f"{OUTPUT_LOCATION}/elc_input_commodity_definitions.csv",
        index=False,
        encoding="utf-8-sig",
    )
    elc_dummy_fuel_process_definitions.to_csv(
        f"{OUTPUT_LOCATION}/elc_dummy_fuel_process_definitions.csv",
        index=False,
        encoding="utf-8-sig",
    )
    elc_dummy_fuel_process_parameters.to_csv(
        f"{OUTPUT_LOCATION}/elc_dummy_fuel_process_parameters.csv",
        index=False,
        encoding="utf-8-sig",
    )


def define_generation_processes(df):
    """
    # EXISTING GENERATION PROCESS DEFINITIONS

    saves outputs to csv for Veda

    """

    existing_techs_process_df = df[["TechName", "Region"]].drop_duplicates().copy()
    existing_techs_process_df["Sets"] = "ELE"
    existing_techs_process_df["Tact"] = "PJ"
    existing_techs_process_df["Tcap"] = "GW"
    existing_techs_process_df["Tslvl"] = "DAYNITE"
    existing_techs_process_df = existing_techs_process_df[
        ["Sets", "Region", "TechName", "Tact", "Tcap"]
    ]

    existing_techs_process_df.to_csv(
        f"{OUTPUT_LOCATION}/existing_tech_process_definitions.csv", index=False
    )


def define_generation_capacity(df):
    """
    Define parameters of existing capacity
    This allows us to set when the plant was built
    or, in the case of distributed solar, apply the PRC_RESID stock model

    saves outputs to csv for Veda

    """

    existing_techs_df = convert_units(df, GENERATION_UNIT_MAP)

    # --- NCAP_PASTI / PRC_RESID capacity treatment ---------------------- #

    existing_techs_capacity = existing_techs_df[
        existing_techs_df["Variable"] == "Capacity"
    ].copy()

    def _capacity_attribute(row: pd.Series) -> str:
        return "PRC_RESID" if pd.isna(row["YearCommissioned"]) else "NCAP_PASTI"

    existing_techs_capacity["Attribute"] = existing_techs_capacity.apply(
        _capacity_attribute, axis=1
    )
    existing_techs_capacity.rename(columns={"YearCommissioned": "Year"}, inplace=True)
    existing_techs_capacity["Year"] = existing_techs_capacity["Year"].fillna(BASE_YEAR)
    existing_techs_capacity = existing_techs_capacity[
        ["TechName", "Region", "Attribute", "Year", "Value"]
    ]

    existing_techs_capacity.to_csv(
        f"{OUTPUT_LOCATION}/existing_tech_capacity.csv",
        index=False,
        encoding="utf-8-sig",
    )


def define_generation_parameters(df):
    """
    Parameters of existing technologies

    saves outputs to csv
    """

    existing_techs_df = convert_units(df, GENERATION_UNIT_MAP)
    index_variables = ["TechName", "Comm-IN", "Comm-OUT", "Region"]
    existing_techs_parameters = (
        existing_techs_df[index_variables + ["Variable", "Value"]]
        .loc[lambda d: d["Variable"] != "Capacity"]
        .pivot_table(index=index_variables, columns="Variable", values="Value")
        .reset_index()
        .rename(
            columns={
                "CapacityFactor": "AFA",
                "FuelDelivCost": "FLO_DELIV",
                "Generation": f"ACT_BND~FX~{BASE_YEAR}",
                "PeakContribution": "NCAP_PKCNT",
                "PlantLife": "NCAP_TLIFE",
                "VarOM": "ACTCOST",
                "FixOM": "NCAP_FOM",
                "FuelEfficiency": "EFF",
            }
        )
    )

    # additional hard-coded parameters
    existing_techs_parameters["NCAP_BND"] = 0
    existing_techs_parameters["NCAP_BND~0"] = 5
    existing_techs_parameters["CAP2ACT"] = CAP2ACT_PJGW
    existing_techs_parameters["ACT_BND~0"] = 1

    existing_techs_parameters.to_csv(
        f"{OUTPUT_LOCATION}/existing_tech_parameters.csv", index=False
    )


def create_distribution_tables():
    """
    Builds the distribution data csvs from raw table input and saves
    """

    distribution_df = pd.read_csv(DISTRIBUTION_INPUT_FILE)

    distribution_df_deflated = deflate_data(
        distribution_df, BASE_YEAR, VARIABLES_TO_DEFLATE
    )

    distribution_commodities = select_and_rename(
        distribution_df_deflated, FI_COMM_MAP
    ).drop_duplicates()

    distribution_processes = select_and_rename(
        distribution_df_deflated, FI_PROCESS_MAP
    ).drop_duplicates()

    distribution_parameters = select_and_rename(
        distribution_df_deflated, DISTRIBUTION_PARAMETERS_MAP
    )
    distribution_parameters["EFF~0"] = 0

    # ----- Grain checks & save ---------------------------------------- #
    test_table_grain(distribution_commodities, ["CommName"])
    test_table_grain(distribution_processes, ["TechName"])
    test_table_grain(distribution_parameters, ["TechName", "Region"])

    distribution_commodities.to_csv(
        f"{OUTPUT_LOCATION}/distribution_commodities.csv",
        index=False,
        encoding="utf-8-sig",
    )
    distribution_processes.to_csv(
        f"{OUTPUT_LOCATION}/distribution_processes.csv",
        index=False,
        encoding="utf-8-sig",
    )
    distribution_parameters.to_csv(
        f"{OUTPUT_LOCATION}/distribution_parameters.csv",
        index=False,
        encoding="utf-8-sig",
    )


def create_elc_fuel_emissions(df):
    """
    Using the input dataframe of raw data,
    defines and shapes the emission factors
    Maps the fuels to our commodities
    and saves along the index expected by Veda

    Note:
        We call Diesel oil but we assume all diesel (no fuel oil generation anymore)
            (assumes 10ppt sulphur)
        For wood, there's an argument for instead taking other wood types,
            or the mean of other wood types. They're all quite similar.
    """

    elec_ef_mapping = {
        "Coal - Sub-Bituminous": "ELCCOA",
        "Natural Gas": "ELCNGA",
        "Diesel": "ELCOIL",
        "Biogas": "ELCBIG",
        "Wood - Pellets": "ELCWOD",
    }

    df = df[df["Sector"] == "Industrial"]
    df = df[df["Fuel"].isin(elec_ef_mapping.keys())]
    df["FuelCode"] = df["Fuel"].map(elec_ef_mapping)
    df["CommName"] = "ELCCO2"

    emission_factors_elc_names = {
        "CommName": "CommName",
        "FuelCode": "Fuel",
        "kt CO2e/PJ": "Value",
    }
    df = select_and_rename(df, emission_factors_elc_names)

    df = df.pivot(index="CommName", columns="Fuel", values="Value").reset_index()

    df.to_csv(f"{OUTPUT_LOCATION}/emission_factors_elc_fuels.csv", index=False)


def create_elc_geo_emissions(df, plant_data):
    """

    Creates the individual geothermal plant emission factors

    df: the input emission factor assumptions
    plant_data: the main baseyear dataframe
    """

    df = df[df["Fuel"] == "Geothermal"]

    default_geo_factor = df.loc[df["SectorDetail"] == "Median", "kt CO2e/PJ"].iloc[0]

    geo_name_map = {
        "Fuel": "CommName",
        "kt CO2e/PJ": "Value",
        "SectorDetail": "PlantName",  # for joining the values to our main table
    }

    df = select_and_rename(df, geo_name_map)

    # Step 1: Filter geothermal plants and select relevant columns
    geo_plants = plant_data[plant_data["FuelType"] == "Geothermal"]
    geo_plants = geo_plants[["PlantName", "TechName"]]
    geo_plants = geo_plants.drop_duplicates()
    geo_plants = geo_plants.sort_values("PlantName")  # Optional, just for cleanliness

    # Join factors to plants
    df = geo_plants.merge(df, on="PlantName", how="left")

    # Fill nulls with default median value
    df["Value"] = df["Value"].fillna(default_geo_factor)

    # Rename columns for TIMES format
    df = df.rename(columns={"Value": "ENV_ACT~ELCCO2"})

    # Select final columns
    df = df[["TechName", "ENV_ACT~ELCCO2"]]

    # Save
    df.to_csv(
        f"{OUTPUT_LOCATION}/emission_factors_geo.csv", encoding="utf-8-sig", index=False
    )


# --------------------------------------------------------------------------- #
# MAIN
# --------------------------------------------------------------------------- #


def main() -> None:
    """
    Main entrypoint for this script.
    """
    logger.info("Generating electricity baseyear files")
    os.makedirs(OUTPUT_LOCATION, exist_ok=True)

    ele_data = load_electricity_baseyear(ELECTRICITY_INPUT_FILE)
    ef_data = load_ef_data(EF_INPUT_FILE)

    define_commodities(ele_data)
    define_generation_processes(ele_data)
    define_generation_capacity(ele_data)
    define_generation_parameters(ele_data)

    create_distribution_tables()

    create_elc_fuel_emissions(ef_data)
    create_elc_geo_emissions(ef_data, ele_data)


# --------------------------------------------------------------------------- #
# SCRIPT ENTRY-POINT
# --------------------------------------------------------------------------- #

if __name__ == "__main__":
    main()
