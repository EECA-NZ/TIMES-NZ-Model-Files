"""All baseyear ag.forest, fish veda files
Mostly built off of one input table, with additional inputs
including the variable selection/renaming
And a few other basic inputs defined in the constants section."""

import pandas as pd

# _save_data should maybe go somewhere else if we're going to call it all the time
from prepare_times_nz.stage_2.ag_forest_fish.common import _save_data
from prepare_times_nz.utilities.filepaths import STAGE_2_DATA, STAGE_4_DATA
from prepare_times_nz.utilities.helpers import select_and_rename

# FILEPATHS ---------------------------------------------------------------

INPUT_FILE = STAGE_2_DATA / "ag_forest_fish/baseyear_ag_forest_fish_demand.csv"
OUTPUT_DIR = STAGE_4_DATA / "base_year_agr"

# should instead use save function pattern here!!
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# CONSTANTS ---------------------------------------------------------------
ACTIVITY_UNIT = "PJ"
CAPACITY_UNIT = "GW"
CAP2ACT = 31.536

# pylint: disable=duplicate-code
AGR_DEMAND_VARIABLE_MAP = {
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

VAROM_COST_ASSUMPTIONS = {
    # NZDm/PJ or NZD/GJ
    "AGRNGA": 2.81,
    "AGRDSL": 0.92,
    "AGRPET": 0.92,
}
DELIVERY_COST_ASSUMPTIONS = {
    # NZDm/PJ or NZD/GJ
    "DID": 2.4,
}

# Helpers -----------------------------------------------------------------------


def save_agr_veda_file(df, name, label, filepath=OUTPUT_DIR):
    """Wraps _save_data to send a file to the veda output"""
    label = f"Saving VEDA table for {label}"
    _save_data(df=df, name=name, label=label, filepath=filepath)


# Main input data =--------------------------------------------------------------


def get_agr_veda_table(df, input_map):
    """convert input table to veda format"""
    df = df.drop(columns="Unit")
    # we work wide - pivot
    index_vars = [col for col in df.columns if col not in ["Variable", "Value"]]
    df = df.pivot(index=index_vars, columns="Variable", values="Value").reset_index()
    # add some things
    df["CAP2ACT"] = CAP2ACT
    # shape output
    agr_df = select_and_rename(df, input_map)
    return agr_df


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

    save_agr_veda_file(demand_df, name=filename, label=label)


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

    save_agr_veda_file(commodity_df, name=filename, label=label)


def define_fuel_commodities(df, filename, label):
    """Distinct fuel commodities for the FI_Comm table
    Also add activity and capacity units just for clarity"""

    fuels = df["Comm-IN"].dropna().unique().tolist()
    if "AGRCO2" not in fuels:
        fuels.append("AGRCO2")

    fuel_df = pd.DataFrame({"CommName": fuels})
    fuel_df["Csets"] = fuel_df["CommName"].apply(
        lambda x: "ENV" if x == "AGRCO2" else "NRG"
    )
    fuel_df["Unit"] = fuel_df["CommName"].apply(
        lambda x: "Kt" if x == "AGRCO2" else ACTIVITY_UNIT
    )
    fuel_df["LimType"] = fuel_df["CommName"].apply(
        lambda x: "" if x == "AGRCO2" else "FX"
    )
    fuel_df["CTSLvl"] = fuel_df["CommName"].apply(
        lambda x: "" if x == "AGRCO2" else "ANNUAL"
    )

    save_agr_veda_file(fuel_df, name=filename, label=label)


# Fuel delivery tables ------------------------------------------------------


def define_fuel_delivery(df: pd.DataFrame) -> None:
    """
    Generates fuel delivery processes for each fuel used in ag/forest/fish sector.
    Expands multi-input fuels (e.g. AGRDSL -> DSL + DID) and applies cost assumptions.
    """

    fuels = pd.Series(df["Comm-IN"]).dropna().unique()

    fuel_deliv_parameters = pd.DataFrame({"Comm-OUT": fuels})

    fuel_deliv_parameters["Comm-IN"] = (
        fuel_deliv_parameters["Comm-OUT"].astype(str).str.removeprefix("AGR")
    )

    expand_map = {
        "DSL": ["DSL", "DID"],  # <- this will add the DID row
    }

    fuel_deliv_parameters["Comm-IN"] = fuel_deliv_parameters["Comm-IN"].map(
        lambda x: expand_map.get(x, [x])
    )

    fuel_deliv_parameters = fuel_deliv_parameters.explode("Comm-IN", ignore_index=True)

    fuel_deliv_parameters["TechName"] = "FTE_" + fuel_deliv_parameters["Comm-OUT"]

    fuel_deliv_parameters["LIFE"] = 100
    fuel_deliv_parameters["EFF"] = 1

    fuel_deliv_parameters["VAROM"] = fuel_deliv_parameters["Comm-OUT"].map(
        VAROM_COST_ASSUMPTIONS
    )

    fuel_deliv_parameters["FLO_DELIV"] = fuel_deliv_parameters["Comm-IN"].map(
        DELIVERY_COST_ASSUMPTIONS
    )

    did_mask = fuel_deliv_parameters["Comm-IN"].eq("DID")
    cols_to_blank = ["Comm-OUT", "TechName", "LIFE", "EFF", "VAROM"]
    for c in cols_to_blank:
        fuel_deliv_parameters.loc[did_mask, c] = pd.NA

    techs = (
        fuel_deliv_parameters.loc[
            ~fuel_deliv_parameters["Comm-IN"].eq("DID"), "TechName"
        ]
        .dropna()
        .astype(str)
        .str.strip()
        .unique()
    )

    fuel_deliv_definitions = pd.DataFrame(
        {
            "TechName": techs,
            "Sets": "PRE",
            "Tact": ACTIVITY_UNIT,
            "Tcap": CAPACITY_UNIT,
            "Tslvl": "ANNUAL",
        }
    )

    save_agr_veda_file(
        fuel_deliv_parameters,
        "fuel_delivery_parameters.csv",
        "fuel delivery parameters",
    )
    save_agr_veda_file(
        fuel_deliv_definitions,
        "fuel_delivery_definitions.csv",
        "fuel delivery definitions",
    )


# Emissions ----------------------------------------------------------------------


def emission_factors_df(emi_df, filename, label):
    """Returns emission factors for selected ag, forest, fish fuels"""

    emi_df = pd.DataFrame()
    emi_df["CommName"] = ["AGRCO2"]
    emi_df["AGRCOA"] = [82.37]
    emi_df["AGRNGA"] = [54.10]
    emi_df["AGRLPG"] = [59.32]
    emi_df["AGRDSL"] = [69.63]
    emi_df["AGRGEO"] = [None]
    emi_df["AGRPET"] = [68.79]

    save_agr_veda_file(emi_df, name=filename, label=label)


# Main ----------------------------------------------------------------------


def main():
    """script entry point"""
    # get and transform data
    raw_df = pd.read_csv(INPUT_FILE)
    agr_veda = get_agr_veda_table(raw_df, AGR_DEMAND_VARIABLE_MAP)

    agg_df = agr_veda.groupby(["Region", "Comm-OUT"], as_index=False)["ACT_BND"].sum()
    agg_df = agg_df.rename(columns={"Comm-OUT": "CommName", "ACT_BND": "Demand~2023"})

    # main table
    save_agr_veda_file(
        agr_veda,
        name="agr_baseyear_demand.csv",
        label="agr baseyear demand",
    )
    save_agr_veda_file(
        agg_df,
        name="agr_baseyear_demand2.csv",
        label="agr baseyear demand2",
    )

    # commodity definitions for fi_comm
    define_enduse_commodities(
        agr_veda,
        filename="enduse_commodity_definitions.csv",
        label="enduse commodity definitions",
    )
    define_fuel_commodities(
        agr_veda,
        filename="fuel_commodity_definitions.csv",
        label="fuel commodity definitions",
    )

    # process definitions for fi_process
    define_demand_processes(
        agr_veda,
        filename="demand_process_definitions.csv",
        label="demand process definitions",
    )

    define_fuel_delivery(agr_veda)

    # emission factors
    emission_factors_df(
        agr_veda,
        filename="agr_emission_factors.csv",
        label="agr emission factors",
    )


if __name__ == "__main__":
    main()
