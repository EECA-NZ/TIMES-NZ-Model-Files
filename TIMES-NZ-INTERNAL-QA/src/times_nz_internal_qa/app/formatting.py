"""
This module formats data outputs for the app

Changing vars, adding groups, ensuring json valid, etc
"""

import pandas as pd
from times_nz_internal_qa.utilities.filepaths import FINAL_DATA


def get_ele_gen_df():
    """
    Formatting for electricity generation. Outputs the main data ready for web ingestion
    Also outputs a variable/unit map for web processing

    """

    ele_gen_df = pd.read_csv(FINAL_DATA / "elec_generation.csv")
    ele_gen_df = ele_gen_df.fillna("-")

    cols = [
        "Scenario",
        "Attribute",
        "Variable",
        "PlantName",
        "TechnologyGroup",
        "Technology",
        "Fuel",
        "Region",
        "Period",
        "Unit",
    ]

    ele_gen_df = ele_gen_df.groupby(cols)["Value"].sum().reset_index()

    unit_map = ele_gen_df.set_index("Variable")["Unit"].to_dict()

    return ele_gen_df, unit_map
