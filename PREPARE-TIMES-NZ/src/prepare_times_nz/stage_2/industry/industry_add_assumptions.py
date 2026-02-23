"""
Add technical and economic assumptions to TIMES-NZ industry demand data.

This script takes the industrial demand outputs from the regional disaggregation
stage and adds:

- Annual full availability (AFA)
- Efficiency
- Capital costs (CAPEX)
- Lifetimes
- Capacity estimates

It reshapes the data to a long format after setting units and variables.
The output is the final industrial sector base-year data, including all
required parameters for further modelling.

Run directly::

    python -m prepare_times_nz.stages.industry_add_assumptions

or import the :pyfunc:`main` function from elsewhere.
"""

from __future__ import annotations

import pandas as pd
from prepare_times_nz.stage_2.common.add_tech_assumptions import (
    add_afa,
    add_capex,
    add_efficiencies,
    add_lifetimes,
    add_opex,
    estimate_capacity,
)
from prepare_times_nz.stage_2.industry.common import (
    BASE_YEAR,
    INDUSTRY_ASSUMPTIONS,
    PREPRO_DF_NAME_STEP2,
    PREPRO_DF_NAME_STEP3,
    PREPROCESSING_DIR,
    save_preprocessing,
)

# Get DATA --------------------------------------------------------------

afa_data = pd.read_csv(INDUSTRY_ASSUMPTIONS / "tech_afa.csv")
cap_data = pd.read_csv(INDUSTRY_ASSUMPTIONS / "tech_fuel_capex.csv")
eff_data = pd.read_csv(INDUSTRY_ASSUMPTIONS / "tech_fuel_efficiencies.csv")
lif_data = pd.read_csv(INDUSTRY_ASSUMPTIONS / "tech_lifetimes.csv")


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


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


def get_industry_assumptions(df):
    """
    Wrapper for all industrial assumptions
    Convert demand units to PJ
    Apply all residential assumptions throgh join functions
    Then derive new variables (like capacity estimates)
    Make table long with unit var
    """

    df["Unit"] = "PJ"
    df = add_efficiencies(df, eff_data)
    df = add_lifetimes(df, lif_data)
    df = add_capex(df, cap_data, cols=["Technology", "Fuel"])
    df = add_opex(df, cap_data, cols=["Technology", "Fuel"])
    df = add_afa(df, afa_data)
    df = estimate_capacity(df)
    df = tidy_data(df)

    return df


# ---------------------------------------------------------------------------
# Main execution
# ---------------------------------------------------------------------------


def main() -> None:
    """Script entrypoint"""
    df = pd.read_csv(PREPROCESSING_DIR / PREPRO_DF_NAME_STEP2)
    df = get_industry_assumptions(df)
    save_preprocessing(
        df, PREPRO_DF_NAME_STEP3, "industry baseyear data with assumptions"
    )


if __name__ == "__main__":
    main()
