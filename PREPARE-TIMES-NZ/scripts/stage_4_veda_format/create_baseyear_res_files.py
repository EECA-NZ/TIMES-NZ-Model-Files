"""All baseyear residential veda files
Mostly built off of one input table, with additional inputs
including the variable selection/renaming
And a few other basic inputs defined in the constants section."""

import pandas as pd

# _save_data should maybe go somewhere else if we're going to call it all the time
from prepare_times_nz.stage_2.residential.common import _save_data
from prepare_times_nz.utilities.filepaths import STAGE_2_DATA, STAGE_4_DATA
from prepare_times_nz.utilities.helpers import select_and_rename

# from prepare_times_nz.utilities.logger_setup import logger


# FILEPATHS ---------------------------------------------------------------

INPUT_FILE = STAGE_2_DATA / "residential/baseyear_residential_demand.csv"
OUTPUT_DIR = STAGE_4_DATA / "base_year_res"

# should instead use save function pattern here!!
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# CONSTANTS ---------------------------------------------------------------
ACTIVITY_UNIT = "PJ"
CAPACITY_UNIT = "GW"
CAP2ACT = 31.536

# pylint: disable=duplicate-code

RESIDENTIAL_DEMAND_VARIABLE_MAP = {
    "Process": "TechName",
    "CommodityIn": "Comm-IN",
    "CommodityOut": "Comm-OUT",
    "Island": "Region",
    "Capacity": "PRC_RESID",
    "AFA": "AFA",
    "CAPEX": "INVCOST",
    "OPEX": "FIXOM",
    "Efficiency": "EFF",
    "Life": "Life",
    "CAP2ACT": "CAP2ACT",
    "OutputEnergy": "ACT_BND",
}

DELIVERY_COST_ASSUMPTIONS = {
    # put me in an assumptions file!!
    # these are NZDm/PJ or NZD/GJ
    # anything not listed is assumed 0 (incl LPG)
    "RESNGA": 25,
    "RESDSL": 0.92,
    "RESPET": 0.92,
    "RESWOD": 10,
}
# Helpers -----------------------------------------------------------------------


def save_residential_veda_file(df, name, label, filepath=OUTPUT_DIR):
    """Wraps _save_data to send a file to the veda output"""
    label = f"Saving VEDA table for {label}"
    _save_data(df=df, name=name, label=label, filepath=filepath)


# Main input data =--------------------------------------------------------------


def get_residential_veda_table(df, input_map):
    """convert input table to veda format"""
    df = df.drop(columns="Unit")
    # we work wide - pivot
    index_vars = [col for col in df.columns if col not in ["Variable", "Value"]]
    df = df.pivot(index=index_vars, columns="Variable", values="Value").reset_index()
    # add some things
    df["CAP2ACT"] = CAP2ACT
    # shape output
    res_df = select_and_rename(df, input_map)
    return res_df


# Define processes ----------------------------------------------------------


def define_demand_processes(df, filename, label):
    """Distinct processes for the FI_PRocess table
    Also add activity and capacity units just for clarity"""

    processes = df["TechName"].unique()

    demand_df = pd.DataFrame()
    demand_df["TechName"] = processes
    demand_df["Sets"] = "DMD"
    demand_df["Tact"] = ACTIVITY_UNIT
    demand_df["Tcap"] = CAPACITY_UNIT

    save_residential_veda_file(demand_df, name=filename, label=label)


# Define commodities ---------------------------------------------------------


def define_enduse_commodities(df, filename, label):
    """Distinct enduse commodities for the FI_Comm table
    Also add activity and capacity units just for clarity"""

    commodities = df["Comm-OUT"].unique()

    commodity_df = pd.DataFrame()
    commodity_df["TechName"] = commodities
    # why are the commodities "DEM" and the processes "DMD"?
    commodity_df["Csets"] = "DEM"
    commodity_df["Unit"] = ACTIVITY_UNIT

    save_residential_veda_file(commodity_df, name=filename, label=label)


def define_fuel_commodities(df, filename, label):
    """Distinct fuel commodities for the FI_Comm table
    Also add activity and capacity units just for clarity"""

    fuels = df["Comm-IN"].unique()

    fuel_df = pd.DataFrame()
    fuel_df["CommName"] = fuels
    fuel_df["Csets"] = "NRG"
    fuel_df["Unit"] = ACTIVITY_UNIT
    fuel_df["LimType"] = "FX"

    save_residential_veda_file(fuel_df, name=filename, label=label)


# Fuel delivery tables ------------------------------------------------------


def define_fuel_delivery(df):
    """
    Generates fuel delivery processes for each fuel used in residential sector
    Adds fuel delivery costs by assumption
    """

    fuels = df["Comm-IN"].unique()

    fuel_deliv_parameters = pd.DataFrame()
    fuel_deliv_parameters["Comm-OUT"] = fuels
    fuel_deliv_parameters["Comm-IN"] = fuel_deliv_parameters[
        "Comm-OUT"
    ].str.removeprefix("RES")
    fuel_deliv_parameters["TechName"] = "FTE_" + fuel_deliv_parameters["Comm-OUT"]

    fuel_deliv_parameters["LIFE"] = 100  # pretty sure we don't need this
    fuel_deliv_parameters["EFF"] = 1  # pretty sure we don't need this

    fuel_deliv_parameters["VAROM"] = fuel_deliv_parameters["Comm-OUT"].map(
        DELIVERY_COST_ASSUMPTIONS
    )

    # with the structure defined, we also define the new processes in a separate file (FI_Process)
    fuel_deliv_definitions = pd.DataFrame(
        {
            "TechName": fuel_deliv_parameters["TechName"].unique(),
            "Sets": "PRE",
            "Tact": ACTIVITY_UNIT,
            "Tcap": CAPACITY_UNIT,
        }
    )

    save_residential_veda_file(
        fuel_deliv_parameters,
        "fuel_delivery_parameters.csv",
        "fuel delivery parameters",
    )
    save_residential_veda_file(
        fuel_deliv_definitions,
        "fuel_delivery_definitions.csv",
        "fuel delivery definitions",
    )


# Main ----------------------------------------------------------------------


def main():
    """script entry point"""
    # get and transform data
    raw_df = pd.read_csv(INPUT_FILE)
    res_veda = get_residential_veda_table(raw_df, RESIDENTIAL_DEMAND_VARIABLE_MAP)

    agg_df = res_veda.groupby(["Region", "Comm-OUT"], as_index=False)["ACT_BND"].sum()
    agg_df = agg_df.rename(columns={"Comm-OUT": "CommName", "ACT_BND": "Demand~2023"})

    # main table
    save_residential_veda_file(
        res_veda,
        name="residential_baseyear_demand.csv",
        label="residential baseyear demand",
    )

    save_residential_veda_file(
        agg_df,
        name="residential_baseyear_demand2.csv",
        label="residential baseyear demand2",
    )
    # commodity definitions for fi_comm
    # (Note emissions commodity declared directly in user config file)
    define_enduse_commodities(
        res_veda,
        filename="enduse_commodity_definitions.csv",
        label="enduse commodity definitions",
    )
    define_fuel_commodities(
        res_veda,
        filename="fuel_commodity_definitions.csv",
        label="fuel commodity definitions",
    )

    # process definitions for fi_process
    define_demand_processes(
        res_veda,
        filename="demand_process_definitions.csv",
        label="demand process definitions",
    )

    define_fuel_delivery(res_veda)


if __name__ == "__main__":
    main()
