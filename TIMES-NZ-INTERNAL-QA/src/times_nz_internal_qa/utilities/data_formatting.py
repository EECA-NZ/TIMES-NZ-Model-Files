"""
Functions for data formatting used for web display

Any data manip functions used for actual data that we might distribute should not be included here
"""

import pandas as pd


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


def get_df_options(df, variable):
    """
    returns all the options for variable in df
    as a list. useful for dynamic app selection.
    """
    df = df.copy()
    return df[variable].unique().tolist()
