"""
Loads commercial data and adds all assumption inputs.

 - Availability factors
 - Capital and operating costs
 - Fuel efficiencies
 - Lifetimes

Then estimates capacity based on the inputs and reshapes data to be legible before saving to
preprocessing.
"""

from __future__ import annotations

import pandas as pd

from prepare_times_nz.stage_2.commercial.common import (
    BASE_YEAR,
    COMMERCIAL_ASSUMPTIONS,
    PREPRO_DF_NAME_STEP2,
    PREPRO_DF_NAME_STEP3,
    PREPROCESSING_DIR,
    save_preprocessing,
)
from prepare_times_nz.stage_2.common.add_tech_assumptions import (
    add_capital_assumptions,
    add_operating_assumptions,
)

# Get DATA --------------------------------------------------------------

# Assumption CSVs were saved with Windows-1252 on your machine; be tolerant on read.
_READ_OPTS = {"encoding": "cp1252", "encoding_errors": "replace"}

# Load and restrict to expected columns
afa_data = pd.read_csv(COMMERCIAL_ASSUMPTIONS / "tech_afa.csv", **_READ_OPTS)[
    ["Sector", "EndUse", "Technology", "AFA"]
]
cap_data = pd.read_csv(COMMERCIAL_ASSUMPTIONS / "tech_fuel_capex.csv", **_READ_OPTS)[
    ["Technology", "Fuel", "PriceBaseYear", "CAPEX"]
]
opex_data = pd.read_csv(COMMERCIAL_ASSUMPTIONS / "tech_fuel_opex.csv", **_READ_OPTS)[
    ["Technology", "Fuel", "PriceBaseYear", "OPEX"]
]
eff_data = pd.read_csv(
    COMMERCIAL_ASSUMPTIONS / "tech_fuel_efficiencies.csv", **_READ_OPTS
)[["Technology", "Fuel", "Efficiency"]]
lif_data = pd.read_csv(COMMERCIAL_ASSUMPTIONS / "tech_lifetimes.csv", **_READ_OPTS)[
    ["Technology", "Life"]
]

# Execute ----------------------------------------------


def get_commercial_assumptions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Wrapper for all commercial assumptions
    Convert demand units to PJ
    Apply all commercial assumptions through join functions
    Then derive new variables (like capacity estimates)
    Make table long with unit var
    """
    df = add_capital_assumptions(df, eff_data, lif_data, cap_data)

    # Adjust CAPEX for Education and Healthcare sectors
    if "Sector" in df.columns and "Technology" in df.columns and "CAPEX" in df.columns:
        df.loc[
            df["Sector"].isin(["Education", "Healthcare"])
            & (df["Technology"] == "Boiler Systems"),
            "CAPEX",
        ] *= 5

    if "Sector" in df.columns and "EndUse" in df.columns and "CAPEX" in df.columns:
        df.loc[
            df["Sector"].isin(["Healthcare"]) & (df["EndUse"] == "Lighting"), "CAPEX"
        ] *= 4

    if "Sector" in df.columns and "EndUse" in df.columns and "CAPEX" in df.columns:
        df.loc[
            df["Sector"].isin(["Office Blocks"]) & (df["EndUse"] == "Lighting"), "CAPEX"
        ] *= 2

    return add_operating_assumptions(df, opex_data, afa_data, BASE_YEAR)


def main() -> None:
    """Script entrypoint"""
    df = pd.read_csv(PREPROCESSING_DIR / PREPRO_DF_NAME_STEP2)
    df = get_commercial_assumptions(df)
    save_preprocessing(df, PREPRO_DF_NAME_STEP3, "3_commercial_demand_with_assumptions")


if __name__ == "__main__":
    main()
