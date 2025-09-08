"""All baseyear industrial veda files.
Mostly built off of one input table, with additional inputs
including the variable selection/renaming
And a few other basic inputs defined in the constants section."""

import pandas as pd

# _save_data should maybe go somewhere else if we're going to call it all the time
from prepare_times_nz.stage_2.industry.common import _save_data
from prepare_times_nz.utilities.filepaths import STAGE_2_DATA, STAGE_4_DATA
from prepare_times_nz.utilities.helpers import select_and_rename

# FILEPATHS ---------------------------------------------------------------

INPUT_FILE = STAGE_2_DATA / "industry/baseyear_industry_demand.csv"
OUTPUT_DIR = STAGE_4_DATA / "base_year_ind"

# should instead use save function pattern here!!
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# CONSTANTS ---------------------------------------------------------------
ACTIVITY_UNIT = "PJ"
CAPACITY_UNIT = "GW"
TSLVL = "DAYNITE"
CTSLVL = "DAYNITE"
CAP2ACT = 31.536
NCAP_BND_2025 = 0
NCAP_BND_0 = 5

# pylint: disable=duplicate-code

INDUSTRY_DEMAND_VARIABLE_MAP = {
    "Process": "TechName",
    "CommodityIn": "Comm-IN",
    "CommodityOut": "Comm-OUT",
    "Region": "Region",
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
    "INDNGA": 0.746,
    "INDDSL": 0.92,
    "INDPET": 0.92,
    "INDFOL": 0.92,
}

# Helpers -----------------------------------------------------------------------


def save_industry_veda_file(df, name, label, filepath=OUTPUT_DIR):
    """Wraps _save_data to send a file to the veda output"""
    label = f"Saving VEDA table for {label}"
    _save_data(df=df, name=name, label=label, filepath=filepath)


# Main input data =--------------------------------------------------------------


def get_industry_veda_table(df, input_map):
    """convert input table to veda format"""
    df = df.drop(columns="Unit")
    # we work wide - pivot
    index_vars = [col for col in df.columns if col not in ["Variable", "Value"]]
    df = df.pivot(index=index_vars, columns="Variable", values="Value").reset_index()
    # add some things
    df["CAP2ACT"] = CAP2ACT
    df["NCAP_BND~0"] = NCAP_BND_0
    df["NCAP_BND~2025"] = NCAP_BND_2025
    # shape output
    ind_df = select_and_rename(df, input_map)
    return ind_df


def get_commodity_demand(df):
    """Aggregate total service demand per commodity"""
    agg_df = df.groupby(["Region", "Comm-OUT"], as_index=False)["ACT_BND"].sum()
    # Note: have set label as "Demand" rather than "Demand~2023". Demand should default to base year
    agg_df = agg_df.rename(columns={"Comm-OUT": "CommName", "ACT_BND": "Demand"})
    return agg_df


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
    demand_df["Tslvl"] = TSLVL

    save_industry_veda_file(demand_df, name=filename, label=label)


# Define commodities ---------------------------------------------------------


def define_enduse_commodities(df, filename, label):
    """Distinct enduse commodities for the FI_Comm table
    Also add activity and capacity units just for clarity"""

    commodities = df["Comm-OUT"].unique()

    commodity_df = pd.DataFrame()
    commodity_df["CommName"] = commodities
    # why are the commodities "DEM" and the processes "DMD"?
    commodity_df["Csets"] = "DEM"
    commodity_df["Unit"] = ACTIVITY_UNIT
    commodity_df["CTSLvl"] = CTSLVL

    save_industry_veda_file(commodity_df, name=filename, label=label)


def define_fuel_commodities(df, filename, label):
    """Distinct fuel commodities for the FI_Comm table
    Also add activity and capacity units just for clarity"""

    fuels = df["Comm-IN"].unique()

    fuel_df = pd.DataFrame()
    fuel_df["CommName"] = fuels
    fuel_df["Csets"] = "NRG"
    fuel_df["Unit"] = ACTIVITY_UNIT
    fuel_df["LimType"] = "FX"

    save_industry_veda_file(fuel_df, name=filename, label=label)


# Fuel delivery tables ------------------------------------------------------


def define_fuel_delivery(df):
    """
    Generates fuel delivery processes for each fuel used in industrial sector
    Adds fuel delivery costs by assumption
    """

    fuels = df["Comm-IN"].unique()

    fuel_deliv_parameters = pd.DataFrame()
    fuel_deliv_parameters["Comm-OUT"] = fuels
    fuel_deliv_parameters["Comm-IN"] = fuel_deliv_parameters[
        "Comm-OUT"
    ].str.removeprefix("IND")
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

    save_industry_veda_file(
        fuel_deliv_parameters,
        "fuel_delivery_parameters.csv",
        "fuel delivery parameters",
    )
    save_industry_veda_file(
        fuel_deliv_definitions,
        "fuel_delivery_definitions.csv",
        "fuel delivery definitions",
    )


# Main ----------------------------------------------------------------------


def main():
    """script entry point"""
    # get and transform data
    raw_df = pd.read_csv(INPUT_FILE)
    ind_veda = get_industry_veda_table(raw_df, INDUSTRY_DEMAND_VARIABLE_MAP)
    agg_df = get_commodity_demand(ind_veda)

    # main table
    save_industry_veda_file(
        ind_veda,
        name="industry_baseyear_details.csv",
        label="industry baseyear details",
    )

    save_industry_veda_file(
        agg_df,
        name="industry_commodity_demand.csv",
        label="industry commodity demand",
    )
    # commodity definitions for fi_comm
    # (Note emissions commodity declared directly in user config file)
    define_enduse_commodities(
        ind_veda,
        filename="enduse_commodity_definitions.csv",
        label="enduse commodity definitions",
    )
    define_fuel_commodities(
        ind_veda,
        filename="fuel_commodity_definitions.csv",
        label="fuel commodity definitions",
    )

    # process definitions for fi_process
    define_demand_processes(
        ind_veda,
        filename="demand_process_definitions.csv",
        label="demand process definitions",
    )

    define_fuel_delivery(ind_veda)


if __name__ == "__main__":
    main()
