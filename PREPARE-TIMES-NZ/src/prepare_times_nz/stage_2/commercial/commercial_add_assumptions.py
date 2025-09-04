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
    add_afa,
    add_capex,
    add_efficiencies,
    add_lifetimes,
    add_opex,
    estimate_capacity,
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

# FUNCTIONS ----------------------------------------------


def tidy_data(df: pd.DataFrame) -> pd.DataFrame:
    """Tidy data and column selection."""
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

    # Rename first to avoid conflicts
    if "Value" in df.columns:
        df.rename(columns={"Value": "ExistingValue"}, inplace=True)

    melt_columns = [col for col in value_units if col in df.columns]
    id_cols = df.columns.difference(melt_columns).tolist()

    if not melt_columns:
        raise ValueError(
            "No columns to melt. Ensure assumption joins added the expected columns."
        )

    df = df.melt(
        id_vars=id_cols,
        value_vars=melt_columns,
        var_name="Variable",
        value_name="Value",
    )
    df["Unit"] = df["Variable"].map(value_units)

    # Drop the old Value column if it survived through as "ExistingValue"
    if "ExistingValue" in df.columns:
        df = df.drop(columns=["ExistingValue", "PriceBaseYear"])

    # desired_order = [
    #     "SectorGroup",
    #     "Sector",
    #     "SectorAnzsic",
    #     "FuelGroup",
    #     "Fuel",
    #     "TechnologyGroup",
    #     "Technology",
    #     "EnduseGroup",
    #     "EndUse",
    #     "Transport",
    #     "Island",
    #     "Variable",
    #     "Year",
    #     "Value",
    #     "Unit",
    # ]

    # # Keep only those columns that actually exist in df
    # cols = [c for c in desired_order if c in df.columns]
    # other_cols = [c for c in df.columns if c not in cols]

    # df = df[cols + other_cols]  # puts desired columns first, rest afterwards

    return df


# Execute ----------------------------------------------


def get_commercial_assumptions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Wrapper for all commercial assumptions
    Convert demand units to PJ
    Apply all commercial assumptions through join functions
    Then derive new variables (like capacity estimates)
    Make table long with unit var
    """
    df = df.copy()

    # Normalize keys in assumption datasets
    for dataset in [eff_data, lif_data, cap_data, opex_data, afa_data]:
        for col in ["Technology", "Fuel"]:
            if col in dataset.columns:
                dataset[col] = (
                    dataset[col]
                    .astype(str)
                    .str.replace("\ufeff", "", regex=False)
                    .str.replace(r"\s+", " ", regex=True)
                    .str.strip()
                )

    # Normalize keys in the input data
    for col in ["Technology", "Fuel"]:
        if col in df.columns:
            df[col] = (
                df[col]
                .astype(str)
                .str.replace("\ufeff", "", regex=False)
                .str.replace(r"\s+", " ", regex=True)
                .str.strip()
            )
    # print("Before joins:", len(df))

    # Assumptions joins
    df = add_efficiencies(df, eff_data)
    # print("Columns after add_efficiencies:", df.columns)
    # print("After efficiencies:", len(df))

    df = add_lifetimes(df, lif_data, cols=["Technology"])
    df = add_capex(df, cap_data, cols=["Technology", "Fuel"])
    df = add_opex(df, opex_data, cols=["Technology", "Fuel"])
    df = add_afa(df, afa_data)

    # Derived metrics
    df = estimate_capacity(df)

    # Long format with units
    df = tidy_data(df)
    # print("Columns before tidy_data:", df.columns)
    return df


def main() -> None:
    """Script entrypoint"""
    df = pd.read_csv(PREPROCESSING_DIR / PREPRO_DF_NAME_STEP2)
    df = get_commercial_assumptions(df)
    save_preprocessing(df, PREPRO_DF_NAME_STEP3, "3_commercial_demand_with_assumptions")


if __name__ == "__main__":
    main()
