"""

Extracts and tidies the NREL future cost projection data

outputs a single csv

"""

from __future__ import annotations

import pandas as pd
from prepare_times_nz.utilities.filepaths import DATA_RAW, STAGE_1_DATA
from prepare_times_nz.utilities.logger_setup import logger

#### CONSTANTS

# NREL price data is USD 2022
PRICE_BASE_YEAR = 2022

CAPEX_FILE = DATA_RAW / "external_data/nrel/NREL_electricity_capex.csv"
FOM_FILE = DATA_RAW / "external_data/nrel/NREL_electricity_opex.csv"

OUTPUT_LOCATION = STAGE_1_DATA / "nrel"


## Functions


def pivot_years(df):
    """

    Takes an input dataset with years as column names
    pivots out the values to create a Year variable

    """

    year_cols = [col for col in df.columns if str(col).isdigit()]
    # The rest are metadata
    id_cols = [col for col in df.columns if col not in year_cols]

    df = df.melt(
        id_vars=id_cols, value_vars=year_cols, var_name="Year", value_name="Value"
    )

    return df


def clean_nrel_data(filepath, varname, unit):
    """
    Takes the data at filepath,
    pivots, cleans,
    adds a variable name and unit based on user input

    returns a df
    """
    df = pd.read_csv(filepath)
    df = pivot_years(df)
    df["Value"] = df["Value"].replace(r"[\$,]", "", regex=True).astype(float)
    df["Variable"] = varname
    df["PriceBaseYear"] = PRICE_BASE_YEAR
    df["Unit"] = unit

    return df


def main():
    """
    Load, clean, combine the NREL data
    Add labels, join and save
    """
    OUTPUT_LOCATION.mkdir(parents=True, exist_ok=True)

    nrel_capex = clean_nrel_data(CAPEX_FILE, "CAPEX", "USD/kW")
    nrel_fom = clean_nrel_data(FOM_FILE, "FOM", "USD/kW/year")

    nrel_data = pd.concat(([nrel_capex, nrel_fom]))

    file_location = f"{OUTPUT_LOCATION}/future_electricity_costs.csv"
    logger.info("Saving NREL Data to %s", file_location)
    nrel_data.to_csv(file_location, index=False)


if __name__ == "__main__":
    main()
