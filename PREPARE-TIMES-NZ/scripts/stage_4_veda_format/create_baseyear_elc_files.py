"""
Generate all Veda-ready CSVs that describe:

* electricity-input commodities and “dummy fuel” processes
* existing generation process definitions, parameters and capacities
* electricity-distribution commodity / process tables
* emission factors
"""

from __future__ import annotations

from typing import Dict, Tuple

import numpy as np
import pandas as pd
from prepare_times_nz.stage_0.stage_0_settings import BASE_YEAR, CAP2ACT_PJGW
from prepare_times_nz.utilities.data_in_out import _save_data
from prepare_times_nz.utilities.deflator import deflate_data
from prepare_times_nz.utilities.filepaths import ASSUMPTIONS, STAGE_2_DATA, STAGE_4_DATA
from prepare_times_nz.utilities.helpers import select_and_rename
from prepare_times_nz.utilities.logger_setup import logger

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
    "NCAP_PASTI": "NCAP_PASTI",
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


def save_elc_data(df, name):
    """Wrapper for data save function"""
    _save_data(df=df, name=name, label="Baseyear electricity", filepath=OUTPUT_LOCATION)


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

    save_elc_data(
        elc_input_commodity_definitions, "elc_input_commodity_definitions.csv"
    )
    save_elc_data(
        elc_dummy_fuel_process_definitions, "elc_dummy_fuel_process_definitions.csv"
    )
    save_elc_data(
        elc_dummy_fuel_process_parameters, "elc_dummy_fuel_process_parameters.csv"
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

    save_elc_data(existing_techs_process_df, "existing_tech_process_definitions.csv")


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

    # make distinct (this mostly just catches the huntly doubleup but is good practise)
    existing_techs_capacity = existing_techs_capacity.drop_duplicates()

    # pivot this because Veda doesn't accept "Value" :(
    existing_techs_capacity = existing_techs_capacity.pivot(
        index=["TechName", "Attribute", "Year"], columns="Region", values="Value"
    ).reset_index()

    # must convert years to integers after pivot

    existing_techs_capacity["Year"] = existing_techs_capacity["Year"].astype(int)

    # save
    save_elc_data(existing_techs_capacity, "existing_tech_capacity.csv")


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
                "Generation": f"ACT_BND~UP~{BASE_YEAR}",
                "PeakContribution": "NCAP_PKCNT",
                # trying Life instead of NCAP_TLIFE - will Veda default to infinite rather than 10?
                "PlantLife": "Life",
                "VarOM": "ACTCOST",
                "FixOM": "NCAP_FOM",
                "FuelEfficiency": "EFF",
            }
        )
    )

    # additional hard-coded parameters
    # no new investment
    # existing_techs_parameters["NCAP_BND"] = 0
    existing_techs_parameters[f"NCAP_BND~{BASE_YEAR+1}"] = 0
    existing_techs_parameters["NCAP_BND~0"] = 5
    # standard cap2act method (should this not go in FI_Process?)
    existing_techs_parameters["CAP2ACT"] = CAP2ACT_PJGW
    # no extrapolation of activity bound
    existing_techs_parameters["ACT_BND~0"] = 1

    # drop the AFA - we do this in a separate table
    existing_techs_parameters = existing_techs_parameters.drop("AFA", axis=1)

    # hacky patch - need to fix AFAs for ren techs!!

    techs_to_loosen = [
        "ELC_SolarDist_Commercial",
        "ELC_SolarDist_Residential",
        "ELC_SolarDist_Industrial",
    ]

    logger.warning("Inserting manual patch into outputs for some base year generation!")
    # This removes activity bound limits for some techs
    #       where our AFAs don't align well with renewable AFs
    # It's not very robust to code changes elsewhere
    #       so it would be better to align the basic AFs with annual average renewable AFs

    existing_techs_parameters["ACT_BND~UP~2023"] = np.where(
        existing_techs_parameters["TechName"].isin(techs_to_loosen),
        np.nan,
        existing_techs_parameters["TechName"],
    )

    save_elc_data(existing_techs_parameters, "existing_tech_parameters.csv")


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

    # ----- Save ---------------------------------------- #

    save_elc_data(distribution_commodities, "distribution_commodities.csv")
    save_elc_data(distribution_processes, "distribution_processes.csv")
    save_elc_data(distribution_parameters, "distribution_parameters.csv")


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

    save_elc_data(df, "emission_factors_elc_fuels.csv")


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

    # save
    save_elc_data(df, "emission_factors_geo.csv")


def make_capacity_factors(df):
    """
    So, it's possible that some of our capacity factors are too low in the base year
    This can lead to infeasibilities if a plant outperformed our assumptions during the base year

    So the solution is to apply the implied capacity factor for the base year

    By setting AFA~[BASE_YEAR], we lock that year's performance for that plant
    This should ensure high calibration with actual data.
    This also provides a table we can use to tweak individual plant's future performances
    """

    df = df[df["Variable"] == "CapacityFactor"].copy()
    base_afa_var = f"AFA~{BASE_YEAR}"
    next_afa_var = f"AFA~{BASE_YEAR+1}"

    df[base_afa_var] = np.where(
        df["GenerationMethod"] == "EMI", df["ImpliedCapacityFactor"], df["Value"]
    )
    df[next_afa_var] = df["Value"]
    df["AFA~0"] = 5
    df = df[["TechName", base_afa_var, next_afa_var, "AFA~0"]].drop_duplicates()

    save_elc_data(df, "base_year_capacity_factors.csv")


# --------------------------------------------------------------------------- #
# MAIN
# --------------------------------------------------------------------------- #


def main() -> None:
    """
    Main entrypoint for this script.
    """

    ele_data = load_electricity_baseyear(ELECTRICITY_INPUT_FILE)
    ef_data = load_ef_data(EF_INPUT_FILE)

    define_commodities(ele_data)
    define_generation_processes(ele_data)
    define_generation_capacity(ele_data)
    define_generation_parameters(ele_data)
    make_capacity_factors(ele_data)

    create_distribution_tables()

    create_elc_fuel_emissions(ef_data)
    create_elc_geo_emissions(ef_data, ele_data)


# --------------------------------------------------------------------------- #
# SCRIPT ENTRY-POINT
# --------------------------------------------------------------------------- #

if __name__ == "__main__":
    main()
