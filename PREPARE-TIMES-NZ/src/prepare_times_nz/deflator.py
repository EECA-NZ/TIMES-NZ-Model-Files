"""

Contains deflate_data(), which allows standardising of price values
in dataframes to match defined base years

This requires the input dataframes to include "PriceBaseYear", or the original
base year for the price data to deflate/inflate.


Depends on the extract_snz.py script running in order to populate the cpi data

"""

import logging

import numpy as np
import pandas as pd
from prepare_times_nz.filepaths import STAGE_1_DATA

# helper data for these functions

cpi_df = pd.read_csv(f"{STAGE_1_DATA}/statsnz/cpi.csv")  # this is the deflator data
cgpi_df = pd.read_csv(
    f"{STAGE_1_DATA}/statsnz/cgpi.csv"
)  # this is the capital deflator data


def deflate_value(current_year, base_year, current_value, method="cpi"):
    """
    Deflate the current value to the base year using the CPI or CGPI indexs.

    Parameters:
    - current_year: The year of the current value.
    - base_year: The year to deflate to.
    - current_value: The value to deflate
    - Treat any 2025 value as if it were 2024 (index tables stop at 2024).
    Returns:
    - deflated_value: The deflated value.

    This function relies on cpi_df or cgpi_df, which should be loaded in
    the script, contain the CPI or CGPI indexs for each year.
    """

    if current_year == base_year:
        return current_value

    if current_year == 2025:
        current_year = 2024

    if method == "cpi":
        idx_df = cpi_df
        idx_col = "CPI_Index"
        label = "CPI"
    elif method == "cgpi":
        idx_df = cgpi_df
        idx_col = "CGPI_Index"
        label = "CGPI"
    else:
        raise ValueError("method must be 'cpi' or 'cgpi'")

    idx_cur = idx_df.loc[idx_df["Year"] == current_year, idx_col]
    idx_base = idx_df.loc[idx_df["Year"] == base_year, idx_col]

    if idx_cur.empty or idx_base.empty or pd.isna(current_value):
        logging.warning(
            "%s missing for %s->%s; returning NaN", label, current_year, base_year
        )
        return np.nan

    return current_value * (idx_base.iloc[0] / idx_cur.iloc[0])


def deflate_columns_rowwise(
    df: pd.DataFrame,
    col_to_basecol: dict[str, str],
    target_year: int = 2023,
    out_suffix: str = "_nzd",
    method: str = "cpi",
) -> pd.DataFrame:
    """
    Deflate several money columns when *each row* may have a different
    base-year column, using CPI or CGPI.
    method: "cpi" or "cgpi"
    """
    missing = [c for c in col_to_basecol.values() if c not in df.columns]
    if missing:
        raise ValueError(f"Base-year column(s) not in DataFrame: {missing}")

    for value_col, base_col in col_to_basecol.items():
        if value_col not in df.columns:
            raise ValueError(f"Value column '{value_col}' not found in DataFrame")

        df[f"{value_col}{out_suffix}"] = df.apply(
            lambda row, _vc=value_col, _bc=base_col: deflate_value(
                current_year=row[_bc],
                base_year=target_year,
                current_value=row[_vc],
                method=method,
            ),
            axis=1,
        )
    return df


def deflate_data(
    df: pd.DataFrame,
    base_year: int,
    variables_to_deflate: list[str],
    method: str = "cpi",
) -> pd.DataFrame:
    """
    Deflate the specified variables in the DataFrame to the base
    year using the chosen deflator function.

    Parameters
    ----------
    variables_to_deflate : list of str Variable names to deflate.
    method : str, optional "cpi" or "cgpi" (default "cpi").

    Returns
    -------
    DataFrame
        The DataFrame with deflated variables and adjusted PriceBaseYear.
    """

    # Make a copy to avoid SettingWithCopyWarning
    df = df.copy()

    for variable in variables_to_deflate:
        if variable not in df.columns:
            raise ValueError(
                f"Variable '{variable}' not found in DataFrame - please review"
            )
    if "PriceBaseYear" not in df.columns:
        raise ValueError("The variable 'PriceBaseYear' not found in DataFrame")

    for variable in variables_to_deflate:
        df[variable] = df.apply(
            lambda row, _var=variable: deflate_value(
                row["PriceBaseYear"],
                base_year,
                row[_var],
                method=method,
            ),
            axis=1,
        )

    df["PriceBaseYear"] = base_year
    return df
