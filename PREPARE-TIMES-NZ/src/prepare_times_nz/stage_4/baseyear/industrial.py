"""All baseyear industrial veda files.
Mostly built off of one input table, with additional inputs
including the variable selection/renaming
And a few other basic inputs defined in the constants section."""

import numpy as np
import pandas as pd

# _save_data should maybe go somewhere else if we're going to call it all the time
from prepare_times_nz.stage_2.industry.common import _save_data
from prepare_times_nz.stage_4.common import (
    add_extra_input_to_topology,
    get_processes_with_input_commodity,
)
from prepare_times_nz.utilities.filepaths import STAGE_2_DATA, STAGE_4_DATA
from prepare_times_nz.utilities.helpers import select_and_rename

# FILEPATHS ---------------------------------------------------------------

INPUT_FILE = STAGE_2_DATA / "industry/baseyear_industry_demand.csv"
COAL_COGEN = STAGE_2_DATA / "electricity/base_year_coal_cogen.csv"
OUTPUT_DIR = STAGE_4_DATA / "base_year_ind"

# should instead use save function pattern here!!
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# CONSTANTS ---------------------------------------------------------------
ACTIVITY_UNIT = "PJ"
CAPACITY_UNIT = "GW"
TSLVL = "DAYNITE"
CTSLVL = "DAYNITE"
CAP2ACT = 31.536
FIRST_FUTURE_MODEL_YEAR = 2026
BIOGAS_SHARE_CONSTRAINTS = {
    "base_year_share_up": 0,
    "future_share_year": FIRST_FUTURE_MODEL_YEAR,
    "future_share_up": 1,
}

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


def get_industry_veda_table(df, input_map, enable_biogas=True):
    """convert input table to veda format"""
    df = df.drop(columns="Unit")
    # we work wide - pivot
    index_vars = [col for col in df.columns if col not in ["Variable", "Value"]]
    df = df.pivot(index=index_vars, columns="Variable", values="Value").reset_index()
    # add some things
    df["CAP2ACT"] = CAP2ACT
    # shape output
    ind_df = select_and_rename(df, input_map)
    # set infinite life if blank life
    # we should probably change default t_life in the model somewhere
    ind_df["Life"] = ind_df["Life"].fillna(100)

    if enable_biogas:
        ind_nga_processes = get_processes_with_input_commodity(ind_df, "INDNGA")
        # exclude Methanol/Urea from this
        ind_nga_processes = [
            process
            for process in ind_nga_processes
            if "METH" not in process and "UREA" not in process and "OTHR" not in process
            # alternatively: just exclude feedstock options
            # if "FSTK" not in process
        ]
        ind_df = add_extra_input_to_topology(
            ind_df,
            ind_nga_processes,
            "INDBIG",
            share_constraints=BIOGAS_SHARE_CONSTRAINTS,
        )

        ind_lpg_processes = get_processes_with_input_commodity(ind_df, "INDLPG")
        ind_lpg_processes = [
            process for process in ind_lpg_processes if "OTHR" not in process
        ]
        ind_df = add_extra_input_to_topology(
            ind_df,
            ind_lpg_processes,
            "INDBIG",
            share_constraints=BIOGAS_SHARE_CONSTRAINTS,
        )

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
    Also add activity and capacity units just for clarity
    We include regions here"""

    demand_df = df[["TechName", "Region"]].drop_duplicates()
    demand_df["Sets"] = "DMD"
    demand_df["Tact"] = ACTIVITY_UNIT
    demand_df["Tcap"] = CAPACITY_UNIT
    demand_df["Tslvl"] = ""

    save_industry_veda_file(demand_df, name=filename, label=label)


# Define commodities ---------------------------------------------------------


def define_enduse_commodities(df, filename, label):
    """Distinct enduse commodities for the FI_Comm table
    Also add activity and capacity units just for clarity
    Include regions: eg we do not declare aluminium production in NI
    """

    commodity_df = df[["Comm-OUT", "Region"]].drop_duplicates()

    commodity_df = commodity_df.rename(columns={"Comm-OUT": "CommName"})

    commodity_df["Csets"] = "DEM"
    commodity_df["Unit"] = ACTIVITY_UNIT
    commodity_df["CTSLvl"] = CTSLVL

    save_industry_veda_file(commodity_df, name=filename, label=label)


def define_fuel_commodities(df, filename, label):
    """Distinct fuel commodities for the FI_Comm table
    Also add activity and capacity units just for clarity"""

    fuels = df["Comm-IN"].dropna().unique().tolist()

    # patch: addhydrogen
    if "INDH2R" not in fuels:
        fuels.append("INDH2R")

    fuel_df = pd.DataFrame()
    fuel_df["CommName"] = fuels
    fuel_df["Csets"] = "NRG"
    fuel_df["Unit"] = ACTIVITY_UNIT
    fuel_df["LimType"] = "FX"
    fuel_df["TsLvl"] = np.where(fuel_df["CommName"] == "INDELC", "DAYNITE", "")

    save_industry_veda_file(fuel_df, name=filename, label=label)


# Fuel delivery tables ------------------------------------------------------


def define_fuel_delivery(df):
    """
    Generates fuel delivery processes for each fuel used in industrial sector
    Adds fuel delivery costs by assumption
    """

    fuels = pd.Series(df["Comm-IN"]).dropna().unique().tolist()

    # patch: add hydrogen
    if "INDH2R" not in fuels:
        fuels.append("INDH2R")

    fuel_deliv_parameters = pd.DataFrame()
    fuel_deliv_parameters["Comm-OUT"] = fuels
    fuel_deliv_parameters["Comm-IN"] = fuel_deliv_parameters[
        "Comm-OUT"
    ].str.removeprefix("IND")

    fuel_deliv_parameters["Comm-IN"] = fuel_deliv_parameters[
        "Comm-IN"
    ].str.removeprefix("FSTK")

    fuel_deliv_parameters["TechName"] = "FTE_" + fuel_deliv_parameters["Comm-OUT"]

    fuel_deliv_parameters["LIFE"] = 100  # pretty sure we don't need this
    fuel_deliv_parameters["EFF"] = 1  # pretty sure we don't need this

    fuel_deliv_parameters["VAROM"] = fuel_deliv_parameters["Comm-OUT"].map(
        DELIVERY_COST_ASSUMPTIONS
    )

    # remove any processes which just pass a commodity through without change
    # (for non-energy coal/gas)
    fuel_deliv_parameters = fuel_deliv_parameters[
        fuel_deliv_parameters["Comm-IN"] != fuel_deliv_parameters["Comm-OUT"]
    ]

    # Ensure this uses only distributed electricity, gas, or biomethanol
    dist_fuels = ["ELC", "NGA", "BIM"]
    fuel_deliv_parameters["Comm-IN"] = np.where(
        fuel_deliv_parameters["Comm-IN"].isin(dist_fuels),
        fuel_deliv_parameters["Comm-IN"] + "DD",
        fuel_deliv_parameters["Comm-IN"],
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
    fuel_deliv_definitions["TsLvl"] = np.where(
        fuel_deliv_definitions["TechName"] == "FTE_INDELC", "DAYNITE", ""
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


# "Other" industry flo_shares


def lock_other_industry(df, exceptions, slack=0.01):
    """
    Identifies "other" industry and creates FLO_MARKs
    to lock demand splits over time

    Adds a new column with each process's share of total output
    within its CommodityOut group.

    We list exceptions for specific input commodities:
    For these we add no lower bounds

    We also add a slack variable - allowing production to fall
    x% lower than the share provided
    This is mostly just to help the model perform a little easier
    (rigidity makes for slower solves)
    """
    # other industry output energy
    df = df[df["Sector"] == "Other Industry"].copy()
    df = df[df["Variable"] == "OutputEnergy"]

    # get process shares of production
    df["Total"] = df.groupby(["Region", "CommodityOut"])["Value"].transform("sum")
    df["Share"] = np.where(
        df["Total"] != 0,
        df["Value"] / df["Total"],
        0,
    )
    # apply slack to share
    df["Share"] = df["Share"] * (1 - slack)
    # remove lower bound qualifiers for our exceptions
    df["Share"] = np.where(df["CommodityIn"].isin(exceptions), 0, df["Share"])
    # zero-share rows do not create meaningful locks, so omit them entirely
    df = df[df["Share"] > 0].copy()

    # column renaming
    flo_mark_map = {
        "Process": "TechName",
        "CommodityOut": "Comm-OUT",
        "Region": "Region",
        "Share": "FLO_MARK~LO",
    }
    df = select_and_rename(df, flo_mark_map)
    # add interp
    df["FLO_MARK~LO~0"] = 5

    return df


# Main ----------------------------------------------------------------------


def main():
    """script entry point"""
    # get and transform data
    raw_df = pd.read_csv(INPUT_FILE)
    ind_veda = get_industry_veda_table(raw_df, INDUSTRY_DEMAND_VARIABLE_MAP)

    # save details
    save_industry_veda_file(
        ind_veda,
        name="industry_baseyear_details.csv",
        label="industry baseyear details",
    )
    # remove indelc from ind_veda for next steps (commodity definitions etc)
    ind_veda = ind_veda[ind_veda["Comm-OUT"] != "INDELC"]

    agg_df = get_commodity_demand(ind_veda)

    # main table
    save_industry_veda_file(
        agg_df,
        name="industry_commodity_demand.csv",
        label="industry commodity demand",
    )
    # locking other industry

    # Note: must exclude coal to allow flex away for NDGHG
    # must exclude NGA to allow flex away for declining supply
    # must exclude pet/fol as capacity may not meet demand
    # (these are in banned base year techs as we assume no more construction)
    other_industry = lock_other_industry(
        raw_df, exceptions=["INDNGA", "INDCOA", "INDPET", "INDFOL"]
    )

    save_industry_veda_file(
        other_industry,
        name="lock_other_industry.csv",
        label="'Other Industry' locks",
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
