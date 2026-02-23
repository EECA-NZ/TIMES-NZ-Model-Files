"""
Load carbon price path assumptions from raw data
and shape to match Veda COM_TAXNET for TOTCO2
for each scenario



1) Reads raw carbon price path assumption data
2) Identifies all scenarios
3) deflates data if necessary (assumes price base year is base year if not provided)
4


"""

import pandas as pd
from prepare_times_nz.stage_0.stage_0_settings import BASE_YEAR
from prepare_times_nz.utilities.data_cleaning import pascal_case
from prepare_times_nz.utilities.data_in_out import _save_data
from prepare_times_nz.utilities.deflator import deflate_data
from prepare_times_nz.utilities.filepaths import ASSUMPTIONS, STAGE_4_DATA

# CONSTANTS --------------------------------------------------------
OUTPUT_LOCATION = STAGE_4_DATA / "scen_carbon_price"

# HELPERS --------------------------------------------------------


def save_carbon_price(df, scenario):
    """
    Wrapper for save function
    """
    label = f"Saving '{scenario}' carbon price"
    scenario_pascal = pascal_case(scenario).lower()
    name = f"carbon_price_{scenario_pascal}.csv"

    _save_data(df, name, label, filepath=OUTPUT_LOCATION)


def write_veda_scen(df, scenario):
    """
    Reshapes a carbon price path to veda
    and saves to a unique file per scenario
    """

    df = df[df["Scenario"] == scenario].copy()

    # add key vars
    df["Attribute"] = "COM_TAXNET"
    df["Cset_CN"] = "TOTCO2"
    # convert nzd/t to mnzd/kt
    df["AllRegions"] = df["Price"] / 1000

    # select only important vars
    df = df[["Attribute", "Cset_CN", "Year", "AllRegions"]]
    # save
    save_carbon_price(df, scenario)


def write_all_carbon_scens():
    """
    Takes all assumption carbon scenarios and writes to unique veda
    Rebases the prices
    """

    df = pd.read_csv(ASSUMPTIONS / "carbon_prices/carbon_prices.csv")
    df = deflate_data(df, BASE_YEAR, variables_to_deflate=["Price"])
    scens = df["Scenario"].unique().tolist()
    for scen in scens:
        write_veda_scen(df, scen)


def main():
    """
    script entry point
    """
    write_all_carbon_scens()


if __name__ == "__main__":
    main()
