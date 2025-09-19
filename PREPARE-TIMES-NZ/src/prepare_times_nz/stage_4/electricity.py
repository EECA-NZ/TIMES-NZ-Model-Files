"""
Outputs electricity tech files for Veda

Organised separately for genstack, offshore, and distributed solar

For genstack files, the outputs are a function of selected
MBIE and NREL scenarios. So we output specific scenario files based on
MBIE/NREL selected inputs. These can be adjusted quite easily as needed.

For offshore/distributed solar, only the NREL scenario is relevant
As these are excluded from the MBIE data. So We currently just
output every file for these, and the config file can select
which to use


"""

import re

import numpy as np
import pandas as pd
from prepare_times_nz.utilities.data_cleaning import pascal_case, remove_diacritics
from prepare_times_nz.utilities.data_in_out import _save_data
from prepare_times_nz.utilities.filepaths import (
    ASSUMPTIONS,
    CONCORDANCES,
    STAGE_3_DATA,
    STAGE_4_DATA,
)

# Constants ----------------------------------------------------

USD_TO_NZD = 1.68


BASE_YEAR = 2023

# basic parameters

CAPACITY_UNIT = "GW"
ACTIVITY_UNIT = "PJ"
TIMESLICE_LEVEL = "DAYNITE"
VINTAGE_TRACKING = "YES"
SETS = "ELE"
CAP2ACT = 31.536

# Cost curve variables
# Only these have cost curves applied, so are treated differently
# Other variables get only one entry in the model which is assumed to carry forward

CURVE_VARIABLES = ["CAPEX", "FOM"]

# Set input data locations ----------------------------------------------------
ELECTRICITY_DATA = STAGE_3_DATA / "electricity"

ELC_ASSUMPTIONS = ASSUMPTIONS / "electricity_generation/future_techs"

# Data

genstack_file = ELECTRICITY_DATA / "genstack.csv"
offshore_wind = ELECTRICITY_DATA / "offshore_wind.csv"
residential_solar = ELECTRICITY_DATA / "residential_solar.csv"

# Assumptions and concordances
region_islands = CONCORDANCES / "region_island_concordance.csv"
tech_assumptions = ELC_ASSUMPTIONS / "TechnologyAssumptions.csv"
fuel_codes = CONCORDANCES / "electricity/future_tech_fuel_codes.csv"


# Set output location --------------------------------------------------------


OUTPUT_LOCATION = STAGE_4_DATA / "subres_elc"
OFFSHORE_OUT = OUTPUT_LOCATION / "offshore"
GENSTACK_OUT = OUTPUT_LOCATION / "genstack"
DSTSOLAR_OUT = OUTPUT_LOCATION / "dist_solar"


# ------------------------------------------------------------------------------------------
# HELPERS ---------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------


# I/O functions
def save_offshore(df, name, filepath=OFFSHORE_OUT):
    """Wrapper for offshore wind outputs"""
    label = "New offshore techs"
    _save_data(df, name, label, filepath=filepath)


def save_dist_solar(df, name, filepath=DSTSOLAR_OUT):
    """Wrapper for saving res solar files"""
    label = "Saving solar data"
    _save_data(df, name, label, filepath=filepath)


def save_genstack(df, name, filepath=GENSTACK_OUT):
    """Wrapper for genstack outputs"""
    label = "Saving genstack data"
    _save_data(df, name, label, filepath=filepath)


# Data processing


def add_islands(df):
    """Add island variable, assuming Region avaiable"""
    islands = pd.read_csv(region_islands)
    df = df.merge(islands, on="Region", how="left")
    return df


def create_process_file(df):
    """
    Takes an input file including TechName
    automatically produces the table appropriate for FI_Process
    """

    out = pd.DataFrame()
    out["TechName"] = df["TechName"].unique()

    out["Sets"] = SETS
    # arrange sets first
    out = out[["Sets", "TechName"]]
    # add the rest of the inputs for the process table

    out["Tact"] = ACTIVITY_UNIT
    out["Tcap"] = CAPACITY_UNIT
    out["Tslvl"] = TIMESLICE_LEVEL
    out["Vintage"] = VINTAGE_TRACKING

    return out


def trim_cost_curves(df):
    """
    Current cost curve data is extended with a new row for every year

    This is helpful for data manip,
    but for Veda we save processing time/space by trimming redundant info

    This expects a dataframe of TechName, Attribute, Year, and Value
    It sorts by TechName, Attribute, and Year, then deletes the row
    if only the year variable is different from the previous row
    """
    # sort first to ensure "previous row" is meaningful
    df = df.sort_values(["TechName", "Attribute", "Year"]).reset_index(drop=True)

    # keep first row in each (TechName, Attribute) group and any row where Value changes
    changed = df.groupby(["TechName", "Attribute"])["Value"].transform(
        lambda s: s.ne(s.shift())
    )

    # return trimmed frame
    return df[changed].reset_index(drop=True)


def get_nrel_cost_curves(
    df,
    scenario="Moderate",
):
    """Simple function that renames CAPEX and FOM to Veda equivalents
    Outputs as "Attribute" so can be sent directly to a Veda table after"""

    # take the expected curve variables only
    df = df[df["Variable"].isin(CURVE_VARIABLES)]

    df = df[df["NRELScenario"] == scenario].copy()
    # probably should have just called them this to start with
    variable_map = {"CAPEX": "INVCOST", "FOM": "FIXOM"}

    df["Attribute"] = df["Variable"].map(variable_map)

    df = df[["TechName", "Attribute", "Year", "Value"]]

    # removing redundant rows - TIMES will interpolate duplicate entries anyway!
    # So this just saves time/space
    df = trim_cost_curves(df)
    return df


def get_island_definitions(df):
    """Creates the tables for regional availability of new techs"""

    df = df[["TechName", "Island"]].drop_duplicates()
    # labelling these as "region" by the TIMES definition,
    # so in theory can expand to more regions if we ever do that
    regions = df["Island"].unique()

    for region in regions:
        df[region] = np.where(df["Island"] == region, 1, 0)

    df = df.drop("Island", axis=1)
    # clarify these are process sets:
    df = df.rename(columns={"TechName": "Pset_PN"})

    return df


def add_assumptions(df):
    """
    Joining various assumptions on the Tech field from raw data
    """

    # bring in additional assumptions
    assumptions_df = pd.read_csv(tech_assumptions)
    df = df.merge(assumptions_df, on="Tech", how="left")

    fuels_df = pd.read_csv(fuel_codes)
    df = df.merge(fuels_df, on="Tech", how="left")

    return df


# misc cleaning functions


def remove_parentheses_if_generic_solar(name: str) -> str:
    """
    Removes text inside parentheses (and the parentheses themselves)
    only if the string contains 'Generic solar' (case-insensitive).
    """
    if re.search(r"\bGeneric\s+solar\b", name, re.IGNORECASE):
        return re.sub(r"\([^)]*\)", "", name).strip()
    return name


def create_process_name(df):
    """
    Designed to create a TIMES-appropriate process name based on some input variables
    Follows the original methods !!! We'll see how it all goes

    So, we need a fuel code for TIMES, as well as a technology code

    Then we'll take the hopefully distinct plantname (with the pascalification)

    And tack that on to ensure distinct processes

    We haven't actually made those yet !!!!!


    Should use consistent concordance methods between this and the base year stuff
    """
    df["TechName"] = (
        "ELC_"
        # + df["FuelType"]
        # + "_"
        + df["Tech"]
        + "_"
        + df["Plant"].apply(remove_diacritics).apply(clean_name)
    )

    return df


def clean_name(string):
    """Wraps our separate cleaning functions together"""
    string = remove_parentheses_if_generic_solar(string)
    string = pascal_case(string)
    return string


# ------------------------------------------------------------------------------------------
# Offshore wind ----------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------


def load_offshore():
    """Loads and tidies the offshore data
    Includes strict variable checking - this will need updating
    if input data structure changes"""
    # load
    df = pd.read_csv(offshore_wind)
    # strict filter to these
    expected_vars = ["CAPEX", "FOM", "Capacity"]
    df = df[df["Variable"].isin(expected_vars)].copy()

    # additional metadata
    df["TechName"] = "ELC_" + df["Tech"] + "_" + df["Region"]
    df["Comm-IN"] = "ELCWIN"
    df["Comm-Out"] = "ELC"  # ELC assumes going into grid rather than embedded

    df = add_islands(df)
    df["Region"] = df["Island"]

    return df


def get_offshore_base_file(df):
    """Pulls offshore from main, builds Veda table from capacity variable"""
    # base data on capacity only - we've saved the other stuff separately so just filter down
    df = df[df["Variable"] == "Capacity"].copy()
    # draw key assumptions
    # earliest year
    df["Start"] = df["CommissioningYear"]
    # limit capacity to assumption inputs (as "Value" in this df since we filtered to capacity)
    df["CAP_BND"] = df["Value"] / 1000  # convert GW
    # NOTE: must extrapolate this as CAP_BND defaults to just being for a specific year:
    df["CAP_BND~0"] = 5
    # additional assumptions

    df = add_assumptions(df)
    df = df.rename(columns={"PlantLife": "Life", "PeakContribution": "NCAP_PKCNT"})

    # filter to columns we want
    df = df[
        [
            "TechName",
            "Comm-IN",
            "Comm-Out",
            "Start",
            "CAP_BND",
            "CAP_BND~0",
            "Life",
            "NCAP_PKCNT",
        ]
    ]
    return df


def process_offshore_wind_data():
    """Orchestrates all offshore wind Veda outputs"""

    df = load_offshore()

    base_file = get_offshore_base_file(df)
    save_offshore(base_file, "base_file.csv")

    process_definitions = create_process_file(base_file)
    save_offshore(process_definitions, "process_definitions.csv")

    island_definitions = get_island_definitions(df)
    save_offshore(island_definitions, "island_definitions.csv")

    # cost curves
    # Advanced
    cost_curves_advanced = get_nrel_cost_curves(df, "Advanced")
    save_offshore(cost_curves_advanced, "cost_curves_advanced.csv")

    # Moderate
    cost_curves_moderate = get_nrel_cost_curves(df, "Moderate")
    save_offshore(cost_curves_moderate, "cost_curves_moderate.csv")

    # Conservative
    cost_curves_conservative = get_nrel_cost_curves(df, "Conservative")
    save_offshore(cost_curves_conservative, "cost_curves_conservative.csv")


# ------------------------------------------------------------------------------------------
# Genstack --------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------


def load_genstack():
    """Simply loads genstack data"""

    df = pd.read_csv(genstack_file)

    return df


def tidy_genstack(df):
    """

    Moderate manipulation of the genstack data
    This should probably be done in stage 3 instead for consistency.

    Generates the distinct process name for genstack plants
    Adds the island variable NI/SI
    Removes the Huntly wood plant in MBIE's genstack as TIMES can just input different
    fuels into the same plant, rather than being forced to
    create new plants for different fuels

    """
    #  really this whole function should go in stage 3. the surfaced s3 data should be tidier
    df = create_process_name(df)
    df = add_islands(df)

    # MBIE includes Huntly black pellets as a separate plant.
    # We will remove this because we can just feed different fuels to the rankines
    plants_to_remove = ["Huntly Unit 1 (Wood)", "Huntly Unit 2 (Wood)"]
    df = df[~df["Plant"].isin(plants_to_remove)]

    return df


def select_mbie_scenario(df, scenario):
    """filters a df on MBIE scenario"""
    df = df[df["Scenario"] == scenario]
    return df


def reshape_genstack(df):
    """
    Assumes an input file with scenario already filter for MBIE scenario
    Then excludes all the curve variables (so all inputs are just for one year)
    This means NREL scenario is not relevant here

    Then just adds all the necessary variables per plant

    This is our main data used by a few separate downstream functions
    """

    # no curve variables (these done separately)
    df = df[~df["Variable"].isin(CURVE_VARIABLES)]

    # pivot variables out again
    index_vars = [
        col
        for col in df.columns
        if col not in ["Variable", "Value", "Unit", "NRELScenario"]
    ]
    df = df.pivot(index=index_vars, columns="Variable", values="Value").reset_index()

    # Some additional units to use
    df["Efficiency"] = 3600 / df["HeatRate"]  # convert to GJ /GJ
    df["CapacityGW"] = df["Capacity"] / 1000  # convert GW

    # add assumptions and fuel concordances
    df = add_assumptions(df)

    # rename some vars
    df = df.rename(
        columns={
            "CapacityGW": "CAP_BND",
            "FuelDeliveryCost": "FLO_DELIV",
            "Efficiency": "EFF",
            "PeakContribution": "NCAP_PKCNT",
            "PlantLife": "Life",
            "VAROM": "VAROM",
        }
    )

    df["CAP_BND~0"] = 5  # extrapolate the capacity bound through whole horizon

    # add the start years.
    # Note that plants with fixed commissioning dates will get a different table
    df["NCAP_START"] = np.where(
        df["CommissioningType"] == "Earliest year",
        df["CommissioningYear"],
        BASE_YEAR + 1,
    )

    df["Comm-OUT"] = "ELC"
    df["Comm-IN"] = "ELC" + df["Fuel_TIMES"]
    df["CAP2ACT"] = CAP2ACT

    return df


def select_veda_genstack_vars(df):
    """
    The main table has everything you need,
    This just selects only the necessary variables for Veda"""

    # Trim to only the Veda columns needed
    df = df[
        [
            "TechName",
            "Comm-IN",
            "Comm-OUT",
            "CAP2ACT",
            "NCAP_START",
            "FLO_DELIV",
            "EFF",
            "Life",
            "NCAP_PKCNT",
            "AFA",
            "CAP_BND",
            "CAP_BND~0",
        ]
    ]

    return df


def get_fixed_installation_dates(df):
    """
    Making a separate tagged table for plants with fixed installation years

    Here, we need to input a few different parameters for NCAP_PASTI
    To fix investment for future years

    This means we pull the fixed plants,
    and reshape the capacity and commissioning year
    and output a separate tag for Veda
    Its possible to also spam NCAP_PASTI~Year variables in the outputs
    But that's a bit messy
    """

    df = df[df["CommissioningType"] == "Fixed"].copy()
    df["Attribute"] = "NCAP_PASTI"
    df["Value"] = df["CAP_BND"]
    df["Year"] = df["CommissioningYear"]

    df = df[["TechName", "Attribute", "Year", "Value"]]

    return df


def process_genstack_files(times_scenario, mbie_scenario, nrel_scenario):
    """
    Orchestrates the genstack files.

    Uses "times_scenario" as an input,
    which is literally just used to name the files

    Then selects the mbie and nrel scenario to use for these,
    and saves outputs based on the times scenario selected

    Generates:

    1) Process Declarations
    2) Process basic parameters
    3) Fixed installation dates (for relevant plants)
    4) Cost curve tables
    """
    df = load_genstack()
    df = select_mbie_scenario(df, scenario=mbie_scenario)
    df = tidy_genstack(df)

    df_veda = reshape_genstack(df)

    island_definitions = get_island_definitions(df)

    # for each, you need:
    # a) the fi_process table
    # b) the base file
    # c) the NCAP_PASTI fixed installation file
    # d) the cost curves
    process_file = create_process_file(df_veda)
    df_parameters = select_veda_genstack_vars(df_veda)

    fixed_installs = get_fixed_installation_dates(df_veda)
    cost_curves = get_nrel_cost_curves(df, scenario=nrel_scenario)
    # ref_fixed_installation =

    save_genstack(process_file, f"{times_scenario}_process.csv")
    save_genstack(df_parameters, f"{times_scenario}_parameters.csv")
    save_genstack(fixed_installs, f"{times_scenario}_fixed_installs.csv")
    save_genstack(cost_curves, f"{times_scenario}_cost_curves.csv")
    save_genstack(island_definitions, f"{times_scenario}_island_definitions.csv")


# ------------------------------------------------------------------------------------------
# Solar ------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------


def load_solar():
    """Just reads solar data and renames the TechName to meet standards"""
    df = pd.read_csv(residential_solar)
    # adjust techname to be a bit more sensible. Move to stage 3 probably
    df["TechName"] = "ELC_" + df["Tech"] + "_Res"
    return df


def reshape_solar_file(df):
    """Creates parameter file for dist solar"""

    # we'll make a base file by removing the curve data

    df = df[df["Variable"] == "Capacity"].copy()
    # summarise regions
    df = df.groupby(["Tech", "TechName"])["Value"].sum().reset_index()
    df["CAP_BND"] = df["Value"] / 1000  # convert GW

    df = add_assumptions(df)

    df["Comm-IN"] = "ELC" + df["Fuel_TIMES"]
    df["Comm-OUT"] = "ELCDD"

    df = df.rename(
        columns={
            "PeakContribution": "NCAP_PKCNT",
            "PlantLife": "Life",
        }
    )

    df["CAP_BND~0"] = 5  # extrapolate the capacity bound through whole horizon

    df["EFF"] = 1
    df["NCAP_START"] = BASE_YEAR + 1
    df["CAP2ACT"] = CAP2ACT

    return df


def get_solar_params(df):
    """Just Selects whats needed for the solar parameters"""

    df = df[
        [
            "TechName",
            "Comm-IN",
            "Comm-OUT",
            "CAP2ACT",
            "NCAP_START",
            "EFF",
            "Life",
            "NCAP_PKCNT",
            "AFA",
            "CAP_BND",
            "CAP_BND~0",
        ]
    ]
    return df


def process_solar_files():
    """Orchestrates all distributed solar Veda outputs"""

    df = load_solar()

    base_file = reshape_solar_file(df)
    params = get_solar_params(base_file)

    save_dist_solar(params, "parameters.csv")

    process_definitions = create_process_file(base_file)
    save_dist_solar(process_definitions, "process_definitions.csv")

    # cost curves
    # Advanced
    cost_curves_advanced = get_nrel_cost_curves(df, "Advanced")
    save_dist_solar(cost_curves_advanced, "cost_curves_advanced.csv")

    # Moderate
    cost_curves_moderate = get_nrel_cost_curves(df, "Moderate")
    save_dist_solar(cost_curves_moderate, "cost_curves_moderate.csv")

    # Conservative
    cost_curves_conservative = get_nrel_cost_curves(df, "Conservative")
    save_dist_solar(cost_curves_conservative, "cost_curves_conservative.csv")


# ------------------------------------------------------------------------------------------
# Execute ----------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------


def main():
    """Wrapper for all functions
    Note that here is where we define the MBIE/NREL scenarios used
    for Traditional/Transformation
    It would be straightforward to either adjust the scenarios used
    Or create new ones by specifying new genstack processing"""

    # offshore wind and dist solar outputs all cost curves
    # can select options by changing inputs in config file
    process_offshore_wind_data()
    process_solar_files()
    # Traditional settings for genstack:
    # Reference MBIE + conservative NREL
    process_genstack_files("Traditional", "Reference", "Conservative")
    # Transformation settings for genstack:
    # Innovation MBIE + Moderate NREL
    process_genstack_files("Transformation", "Innovation", "Moderate")


if __name__ == "__main__":
    main()
