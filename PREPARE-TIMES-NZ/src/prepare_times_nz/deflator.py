"""

Contains deflate_data(), which allows standardising of price values
in dataframes to match defined base years

This requires the input dataframes to include "PriceBaseYear", or the original
base year for the price data to deflate/inflate.


Depends on the extract_snz.py script running in order to populate the cpi data

"""

import pandas as pd
from prepare_times_nz.filepaths import STAGE_1_DATA
from prepare_times_nz.logger_setup import logger

# helper data for these functions

cpi_df = pd.read_csv(f"{STAGE_1_DATA}/statsnz/cpi.csv")  # this is the deflator data


def deflate_value(current_year, base_year, current_value):
    """
    Deflate the current value to the base year using the CPI index.

    Parameters:
    - current_year: The year of the current value.
    - base_year: The year to deflate to.
    - current_value: The value to deflate

    Returns:
    - deflated_value: The deflated value.

    This function relies on cpi_df, which should be loaded in the script.
    It contains the CPI index for each year.
    """

    if current_year == base_year:
        logger.info(
            "Current year (%s) is the same as base year (%s). No deflation needed.",
            current_year,
            base_year,
        )
        return current_value

    # Otherwise, the deflator runs:
    # Get the CPI index for the current year and base year
    cpi_current = cpi_df.loc[cpi_df["Year"] == current_year, "CPI_Index"].values[0]
    cpi_base = cpi_df.loc[cpi_df["Year"] == base_year, "CPI_Index"].values[0]

    # Calculate the deflated value
    deflated_value = current_value * (cpi_base / cpi_current)

    return deflated_value


def deflate_data(df, base_year, variables_to_deflate):
    """
    Deflate the specified variables in the DataFrame to the base year
     (using the deflator function defined earlier)

    Parameters:
    - df: The input DataFrame. MUST include PriceBaseYear and the variables to deflate.
    - base_year: The year to deflate to.
    - variables_to_deflate: A list of variable names to deflate.

    Returns:
    - df: The DataFrame with deflated variables and adjusted PriceBaseYear.
    """

    # Check if the DataFrame has the required columns
    for variable in variables_to_deflate:
        if variable not in df.columns:
            raise ValueError(
                f"Variable '{variable}' not found in DataFrame - please review"
            )

    # Check if the base year is in the DataFrame
    if "PriceBaseYear" not in df.columns:
        raise ValueError(
            "The variable 'PriceBaseYear' not found in DataFrame - aborting"
        )

    # Apply the deflator function to each variable in the DataFrame
    for variable in variables_to_deflate:
        df[variable] = df.apply(
            lambda row, var=variable: deflate_value(
                row["PriceBaseYear"], base_year, row[var]
            ),
            axis=1,
        )

    # With prices rebased, we can redefine the PriceBaseYear to be the base year
    df["PriceBaseYear"] = base_year

    return df
