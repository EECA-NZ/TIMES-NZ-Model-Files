"""

Loads residential data and adds all assumption inputs

 - Avaialbility factors
 - capital and opeerating costs
 - fuel efficiencies
 - lifteims

 Then estimates capacity based on the inupts and reshapes data to be legible before saving to
 preprocessing
"""

import pandas as pd
from prepare_times_nz.stage_2.common.add_tech_assumptions import (
    add_afa,
    add_capex,
    add_efficiencies,
    add_lifetimes,
    add_opex,
    estimate_capacity,
)
from prepare_times_nz.stage_2.residential.common import (
    BASE_YEAR,
    PREPRO_DF_NAME_STEP2,
    PREPRO_DF_NAME_STEP3,
    PREPROCESSING_DIR,
    RESIDENTIAL_ASSUMPTIONS,
    save_preprocessing,
)

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
    """
    Wrapper for all residential assumptions
    Convert demand units to PJ
    Apply all residential assumptions throgh join functions
    Then derive new variables (like capacity estimates)
    Make table long with unit var
    """
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


def main():
    """Script entrypoint"""
    df = pd.read_csv(PREPROCESSING_DIR / PREPRO_DF_NAME_STEP2)
    df = get_residential_assumptions(df)
    save_preprocessing(df, PREPRO_DF_NAME_STEP3, "Residential assumptions data")


if __name__ == "__main__":
    main()
