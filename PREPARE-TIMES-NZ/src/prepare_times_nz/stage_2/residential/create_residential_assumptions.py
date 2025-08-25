import numpy as np
import pandas as pd
from prepare_times_nz.stage_2.common.add_tech_assumptions import (
    add_afa,
    add_capex,
    add_efficiencies,
    add_lifetimes,
    add_opex,
    estimate_capacity,
)
from prepare_times_nz.utilities.filepaths import (
    ASSUMPTIONS,
    CONCORDANCES,
    STAGE_1_DATA,
    STAGE_2_DATA,
)
from prepare_times_nz.utilities.logger_setup import blue_text, logger

# Main filepaths --------------------------------------------

RESIDENTIAL_ASSUMPTIONS = ASSUMPTIONS / "residential"
OUTPUT_LOCATION = STAGE_2_DATA / "residential"
CHECKS_LOCATION = OUTPUT_LOCATION / "checks"


# constants -----------------

BASE_YEAR = 2023
RUN_TESTS = False
CAP2ACT = 31.536

# get data
# do a bunch of joins
# add some derived variables (like capacity or whatever)
# deflate all costs ( to re-output for the document)

# save

# roughhly copying the industry approach

# get data here i guess


# Get DATA --------------------------------------------------------------

afa_data = pd.read_csv(RESIDENTIAL_ASSUMPTIONS / "afa_assumptions.csv")
cap_data = pd.read_csv(RESIDENTIAL_ASSUMPTIONS / "capex_assumptions.csv")
eff_data = pd.read_csv(RESIDENTIAL_ASSUMPTIONS / "eff_by_tech_and_fuel.csv")
lif_data = pd.read_csv(RESIDENTIAL_ASSUMPTIONS / "lifetime_assumptions.csv")


# FUNCTIONS ----------------------------------------------


def tidy_data(df: pd.DataFrame) -> pd.DataFrame:
    """Reshape DataFrame to long format with standardized units."""
    df = df.drop(columns=["Value", "Unit", "PriceBaseYear"])
    value_units = {
        "Life": "Years",
        "Efficiency": "%",
        "CAPEX": f"{BASE_YEAR} NZD/kW",
        "OPEX": f"{BASE_YEAR} NZD/kW/year",
        "AFA": "%",
        "InputEnergy": "PJ",
        "OutputEnergy": "PJ",
        "Capacity": "GW",
    }
    id_cols = df.columns.difference(value_units.keys()).tolist()
    df = df.melt(id_vars=id_cols, var_name="Variable", value_name="Value")
    df["Unit"] = df["Variable"].map(value_units)
    return df


# Execute


def get_residential_assumptions(df):
    df["Value"] = df["Value"] / 1e3  # TJ - PJ
    df["Unit"] = "PJ"
    df = add_efficiencies(df, eff_data)
    df = add_lifetimes(df, lif_data, cols=["Technology", "Fuel", "EndUse"])
    df = add_capex(df, cap_data, cols=["Technology", "Fuel", "EndUse", "DwellingType"])
    df = add_opex(df, cap_data, cols=["Technology", "Fuel", "EndUse", "DwellingType"])
    df = add_afa(df, afa_data)
    df = estimate_capacity(df)
    df = tidy_data(df)

    return df


def main(
    input_file=OUTPUT_LOCATION / "residential_demand_by_island.csv",
    output_file=OUTPUT_LOCATION / "residential_demand_with_assumptions.csv",
):
    df = pd.read_csv(input_file)
    df = get_residential_assumptions(df)
    df.to_csv(output_file, index=False)


if __name__ == "__main__":
    main()
