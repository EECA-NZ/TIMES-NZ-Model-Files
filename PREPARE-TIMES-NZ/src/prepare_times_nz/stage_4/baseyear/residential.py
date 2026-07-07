"""All baseyear residential veda files
Mostly built off of one input table, with additional inputs
including the variable selection/renaming
And a few other basic inputs defined in the constants section."""

import numpy as np
import pandas as pd
from prepare_times_nz.stage_4.common import (
    add_extra_input_to_topology,
    get_processes_with_input_commodity,
)
from prepare_times_nz.utilities.data_in_out import _save_data
from prepare_times_nz.utilities.filepaths import (
    ASSUMPTIONS,
    DATA_RAW,
    STAGE_2_DATA,
    STAGE_4_DATA,
)
from prepare_times_nz.utilities.helpers import select_and_rename

# FILEPATHS ---------------------------------------------------------------

INPUT_FILE = STAGE_2_DATA / "residential/baseyear_residential_demand.csv"
OUTPUT_DIR = STAGE_4_DATA / "base_year_res"
DEMAND_FLEX_ENABLED_TECHS_FILE = (
    ASSUMPTIONS / "residential/demand_flex_enabled_techs.csv"
)
MODEL_SWITCHES_FILE = DATA_RAW / "user_config/settings/model_switches.csv"
DEMAND_FLEX_INTERMEDIATES_SWITCH = "ResidentialDemandFlexIntermediates"

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
    "RESDSL": 0.92,
    "RESPET": 0.92,
    "RESWOD": 10,
}
# Helpers -----------------------------------------------------------------------


def parse_switch_value(value):
    """Parse a user switch value from CSV."""
    if isinstance(value, bool):
        return value

    normalized = str(value).strip().lower()
    if normalized in {"true", "1", "yes", "y", "on"}:
        return True
    if normalized in {"false", "0", "no", "n", "off"}:
        return False

    raise ValueError(f"Invalid switch value: {value}")


def get_model_switch(switch_name, default=True, filepath=MODEL_SWITCHES_FILE):
    """Read a named user-defined model switch from a simple CSV file."""
    if not filepath.exists():
        return default

    df = pd.read_csv(filepath, encoding="utf-8-sig")
    if not {"Switch", "Enabled"}.issubset(df.columns):
        raise ValueError(f"{filepath} must include 'Switch' and 'Enabled' columns")

    matches = df[df["Switch"] == switch_name]
    if matches.empty:
        return default
    if len(matches) > 1:
        raise ValueError(f"Duplicate model switch entries found for {switch_name}")

    return parse_switch_value(matches.iloc[0]["Enabled"])


def use_demand_flex_intermediates():
    """Return whether residential demand-flex intermediates are enabled."""
    return get_model_switch(DEMAND_FLEX_INTERMEDIATES_SWITCH, default=True)


def save_residential_veda_file(df, name, label, filepath=OUTPUT_DIR):
    """Wraps _save_data to send a file to the veda output"""
    label = f"Saving VEDA table for {label}"
    _save_data(df=df, name=name, label=label, filepath=filepath)


# Main input data =--------------------------------------------------------------


def get_residential_veda_table(df, input_map, enable_biogas=True):
    """convert input table to veda format
    Option to add biogas to input topology for specific processes
    """
    df = df.drop(columns="Unit")
    # we work wide - pivot
    index_vars = [col for col in df.columns if col not in ["Variable", "Value"]]
    df = df.pivot(index=index_vars, columns="Variable", values="Value").reset_index()
    # add some things
    df["CAP2ACT"] = CAP2ACT
    # shape output
    res_df = select_and_rename(df, input_map)

    if enable_biogas:
        # if a tech could use nga, we say it can also use biogas
        res_nga_processes = get_processes_with_input_commodity(res_df, "RESNGA")
        res_df = add_extra_input_to_topology(res_df, res_nga_processes, "RESBIM")

    return res_df


def get_commodity_demand(df):
    """Aggregate total service demand per commodity"""
    agg_df = df.groupby(["Region", "Comm-OUT"], as_index=False)["ACT_BND"].sum()
    # Note: have set label as "Demand" rather than "Demand~2023". Demand should default to base year
    agg_df = agg_df.rename(columns={"Comm-OUT": "CommName", "ACT_BND": "Demand"})
    return agg_df


def get_demand_flex_enabled_techs(filepath=DEMAND_FLEX_ENABLED_TECHS_FILE):
    """Load demand-flex-enabled residential technologies."""
    if not filepath.exists():
        return set()

    df = pd.read_csv(filepath, encoding="utf-8-sig")
    return set(df["TechName"].dropna())


def get_intermediate_commodity_name(tech_name):
    """Return the detailed service commodity for a residential demand process."""
    parts = tech_name.split("-", maxsplit=3)
    if len(parts) != 4 or parts[0] != "RES":
        raise ValueError(f"Unexpected residential TechName format: {tech_name}")

    _, region, _fuel, tech_detail = parts
    return f"{region}-{tech_detail}"


def get_demand_flex_topology(df, demand_flex_enabled_techs):
    """Create intermediate commodity mapping for flex-enabled demand processes."""
    flex_df = df[df["TechName"].isin(demand_flex_enabled_techs)].copy()
    if flex_df.empty:
        return pd.DataFrame(columns=["TechName", "Comm-OUT", "Comm-IN"])

    flex_df["Comm-IN"] = flex_df["TechName"].map(get_intermediate_commodity_name)
    flex_df = flex_df[["TechName", "Comm-OUT", "Comm-IN"]].drop_duplicates()

    duplicates = flex_df.duplicated("TechName", keep=False)
    if duplicates.any():
        duplicate_techs = sorted(flex_df.loc[duplicates, "TechName"].unique())
        raise ValueError(
            "Demand-flex technologies map to multiple output commodities: "
            + ", ".join(duplicate_techs)
        )

    return flex_df


def add_demand_flex_intermediate_outputs(df, demand_flex_topology):
    """Route demand-flex technologies through detailed intermediate commodities."""
    if demand_flex_topology.empty:
        return df

    intermediate_commodities = demand_flex_topology.set_index("TechName")["Comm-IN"]
    df = df.copy()
    flex_mask = df["TechName"].isin(intermediate_commodities.index)
    df.loc[flex_mask, "Comm-OUT"] = df.loc[flex_mask, "TechName"].map(
        intermediate_commodities
    )
    return df


# Define processes ----------------------------------------------------------


def define_demand_processes(df, filename, label, demand_flex_enabled_techs=None):
    """Distinct processes for the FI_PRocess table
    Also add activity and capacity units just for clarity"""

    processes = df["TechName"].unique()
    demand_flex_enabled_techs = demand_flex_enabled_techs or set()

    demand_df = pd.DataFrame()
    demand_df["TechName"] = processes
    demand_df["Sets"] = "DMD"
    demand_df["Tact"] = ACTIVITY_UNIT
    demand_df["Tcap"] = CAPACITY_UNIT
    demand_df["Tslvl"] = np.where(
        demand_df["TechName"].isin(demand_flex_enabled_techs), "DAYNITE", ""
    )

    save_residential_veda_file(demand_df, name=filename, label=label)


# Define commodities ---------------------------------------------------------


def define_enduse_commodities(df, filename, label):
    """Distinct enduse commodities for the FI_Comm table
    Also add activity and capacity units just for clarity"""

    commodities = df["Comm-OUT"].unique()

    commodity_df = pd.DataFrame()
    commodity_df["CommName"] = commodities
    commodity_df["Csets"] = "DEM"
    commodity_df["Unit"] = ACTIVITY_UNIT
    commodity_df["TsLvl"] = "DAYNITE"

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
    fuel_df["TsLvl"] = np.where(fuel_df["CommName"] == "RESELC", "DAYNITE", "")

    save_residential_veda_file(fuel_df, name=filename, label=label)


def define_demand_flex_intermediates(demand_flex_topology):
    """Generate intermediate commodity and pass-through process tables."""
    if demand_flex_topology.empty:
        intermediate_commodities = pd.DataFrame(
            columns=["CommName", "Csets", "Unit", "LimType", "TsLvl"]
        )
        intermediate_definitions = pd.DataFrame(
            columns=["TechName", "Sets", "Tact", "Tcap", "TsLvl"]
        )
        intermediate_parameters = pd.DataFrame(
            columns=["Comm-OUT", "Comm-IN", "TechName", "LIFE", "EFF"]
        )

        save_residential_veda_file(
            intermediate_commodities,
            "intermediate_commodity_definitions.csv",
            "demand flex intermediate commodity definitions",
        )
        save_residential_veda_file(
            intermediate_definitions,
            "intermediate_process_definitions.csv",
            "demand flex intermediate process definitions",
        )
        save_residential_veda_file(
            intermediate_parameters,
            "intermediate_process_parameters.csv",
            "demand flex intermediate process parameters",
        )
        return

    intermediate_commodities = pd.DataFrame()
    intermediate_commodities["CommName"] = demand_flex_topology["Comm-IN"].unique()
    intermediate_commodities["Csets"] = "NRG"
    intermediate_commodities["Unit"] = ACTIVITY_UNIT
    intermediate_commodities["LimType"] = "FX"
    intermediate_commodities["TsLvl"] = "DAYNITE"

    intermediate_parameters = demand_flex_topology[
        ["Comm-OUT", "Comm-IN"]
    ].drop_duplicates()
    intermediate_parameters["TechName"] = "FTE_" + intermediate_parameters["Comm-IN"]
    intermediate_parameters["LIFE"] = 100
    intermediate_parameters["EFF"] = 1

    intermediate_definitions = pd.DataFrame(
        {
            "TechName": intermediate_parameters["TechName"].unique(),
            "Sets": "PRE",
            "Tact": ACTIVITY_UNIT,
            "Tcap": "PJa",
            "TsLvl": "DAYNITE",
        }
    )

    save_residential_veda_file(
        intermediate_commodities,
        "intermediate_commodity_definitions.csv",
        "demand flex intermediate commodity definitions",
    )
    save_residential_veda_file(
        intermediate_definitions,
        "intermediate_process_definitions.csv",
        "demand flex intermediate process definitions",
    )
    save_residential_veda_file(
        intermediate_parameters,
        "intermediate_process_parameters.csv",
        "demand flex intermediate process parameters",
    )


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

    fuel_deliv_parameters["LIFE"] = 100  # note default to ten years otherwise
    fuel_deliv_parameters["EFF"] = 1  # pretty sure we don't need this

    fuel_deliv_parameters["VAROM"] = fuel_deliv_parameters["Comm-OUT"].map(
        DELIVERY_COST_ASSUMPTIONS
    )

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
        fuel_deliv_definitions["TechName"] == "FTE_RESELC", "DAYNITE", ""
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
    base_res_veda = get_residential_veda_table(raw_df, RESIDENTIAL_DEMAND_VARIABLE_MAP)
    agg_df = get_commodity_demand(base_res_veda)
    demand_flex_enabled_techs = (
        get_demand_flex_enabled_techs() if use_demand_flex_intermediates() else set()
    )
    demand_flex_topology = get_demand_flex_topology(
        base_res_veda, demand_flex_enabled_techs
    )
    res_veda = add_demand_flex_intermediate_outputs(base_res_veda, demand_flex_topology)

    # main table
    save_residential_veda_file(
        res_veda,
        name="residential_baseyear_details.csv",
        label="residential baseyear details",
    )

    save_residential_veda_file(
        agg_df,
        name="residential_commodity_demand.csv",
        label="residential commodity demand",
    )
    # commodity definitions for fi_comm
    # (Note emissions commodity declared directly in user config file)
    define_enduse_commodities(
        base_res_veda,
        filename="enduse_commodity_definitions.csv",
        label="enduse commodity definitions",
    )
    define_fuel_commodities(
        res_veda,
        filename="fuel_commodity_definitions.csv",
        label="fuel commodity definitions",
    )
    define_demand_flex_intermediates(demand_flex_topology)

    # process definitions for fi_process
    define_demand_processes(
        res_veda,
        filename="demand_process_definitions.csv",
        label="demand process definitions",
        demand_flex_enabled_techs=demand_flex_enabled_techs,
    )

    define_fuel_delivery(res_veda)


if __name__ == "__main__":
    main()
