"""All baseyear residential veda files
Mostly built off of one input table, with additional inputs
including the variable selection/renaming
And a few other basic inputs defined in the constants section"""

from prepare_times_nz.utilities.filepaths import STAGE_2_DATA
from prepare_times_nz.utilities.helpers import select_and_rename

# from prepare_times_nz.utilities.logger_setup import logger

INPUT_FILE = STAGE_2_DATA / "residential/residential_baseyear_demand.csv"
CAP2ACT = 31.536

RESIDENTIAL_DEMAND_VARIABLE_MAP = {
    "Process": "TechName",
    "CommodityIn": "Comm-IN",
    "CommodityOut": "Comm-OUT",
    "Island": "Region",
    "Capacity": "NCAP_PASTI",
    "AFA": "AFA",
    "CAPEX": "INVCOST",
    "OPEX": "FIXOM",
    "Efficiency": "EFF",
    "Life": "Life",
    "CAP2ACT": "CAP2ACT",
    "OutputEnergy": "ACT_BND",
}


def get_residential_veda_table(df, input_map):
    """convert input table to veda format"""

    # store unit map
    # var_units = df[["Variable", "Unit"]].drop_duplicates()
    # melt
    df = df.drop(columns="Unit").copy()
    # we work wide - pivot
    index_vars = [col for col in df.columns if col not in ["Variable", "Value"]]
    df = df.pivot(index=index_vars, columns="Variable", values="Value").reset_index()
    # add some things
    df["CAP2ACT"] = CAP2ACT
    # shape output
    res_df = select_and_rename(df, input_map)

    return res_df
