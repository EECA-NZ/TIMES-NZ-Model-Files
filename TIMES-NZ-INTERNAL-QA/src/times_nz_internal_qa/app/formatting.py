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

    ele_gen_df = pd.read_csv(FINAL_DATA / "elec_generation.csv", low_memory=False)
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


def complete_periods(df, period_list, category_cols=None, value_col="Value"):
    """
    Fill in missing periods with explicit zero values for each category combination.

    Parameters:
    -----------
    df : pandas.DataFrame
        Input dataframe containing Period, PV (Value), and optional category columns
    period_list : list
        Complete list of all possible periods
    category_cols : list or None
        List of category column names to group by. If None, just completes periods globally

    Returns:
    --------
    pandas.DataFrame
        Complete dataframe with explicit zero values for missing periods
    """
    # Create a dataframe from the complete period list
    periods_df = pd.DataFrame({"Period": period_list})

    if category_cols:
        # Get unique combinations of category values
        categories = df[category_cols].drop_duplicates()

        # Create a cross product of periods with all category combinations
        template = periods_df.merge(categories, how="cross")

        # Merge with original data, filling missing values with 0
        result = template.merge(df, on=["Period"] + category_cols, how="left")
    else:
        # If no categories, just merge periods with original data
        result = periods_df.merge(df, on="Period", how="left")

    # Fill missing PV values with 0
    result[value_col] = result[value_col].fillna(0)

    return result
