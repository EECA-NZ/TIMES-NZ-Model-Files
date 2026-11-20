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
    add_capital_assumptions,
    add_operating_assumptions,
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


# Execute


def get_industry_assumptions(df):
    """
    Wrapper for all industrial assumptions
    Convert demand units to PJ
    Apply all residential assumptions throgh join functions
    Then derive new variables (like capacity estimates)
    Make table long with unit var
    """

    df = add_capital_assumptions(df, eff_data, lif_data, cap_data)
    return add_operating_assumptions(df, cap_data, afa_data, BASE_YEAR)


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
