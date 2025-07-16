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

import logging
from pathlib import Path

import pandas as pd
from prepare_times_nz.deflator import deflate_data
from prepare_times_nz.filepaths import ASSUMPTIONS, STAGE_2_DATA
from prepare_times_nz.logger_setup import blue_text, h2, logger

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
CAP2ACT = 31.536
BASE_YEAR = 2023
RUN_TESTS = False

OUTPUT_LOCATION = Path(STAGE_2_DATA) / "industry" / "preprocessing"
OUTPUT_LOCATION.mkdir(parents=True, exist_ok=True)

CHECKS_LOCATION = Path(STAGE_2_DATA) / "industry" / "checks" / "3_parameter_assumptions"
CHECKS_LOCATION.mkdir(parents=True, exist_ok=True)

INDUSTRY_ASSUMPTIONS = Path(ASSUMPTIONS) / "industry_demand"

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def save_output(df: pd.DataFrame, name: str) -> None:
    """Save DataFrame as CSV to the preprocessing output directory."""
    filename = OUTPUT_LOCATION / name
    logger.info("Saving output:\n%s", blue_text(filename))
    df.to_csv(filename, index=False)


def check_missing_lifetimes(df: pd.DataFrame) -> None:
    """Log warning for technologies missing lifetime data."""
    missing_techs = df[df["Life"].isna()]["Technology"].drop_duplicates()
    if not missing_techs.empty:
        logger.warning("The following technologies have no lifetimes:")
        for tech in missing_techs:
            logger.warning("    %s", tech)
        logger.warning("These will have infinite lifetimes in the model.")


def add_lifetimes(df: pd.DataFrame, lifetimes: pd.DataFrame) -> pd.DataFrame:
    """Merge technology lifetime data into the main DataFrame."""
    df = df.merge(lifetimes, on="Technology", how="left")
    if RUN_TESTS:
        check_missing_lifetimes(df)
    return df.drop(columns=["Note"])


def check_missing_efficiencies(df: pd.DataFrame) -> None:
    """Log warning for technologies missing efficiency data."""
    missing_eff = df[df["Efficiency"].isna()][["Technology", "Fuel"]].drop_duplicates()
    if not missing_eff.empty:
        logger.warning("Technologies with missing efficiency:")
        for _, row in missing_eff.iterrows():
            logger.warning("    %s - %s", row["Technology"], row["Fuel"])


def add_efficiencies(df: pd.DataFrame, eff_data: pd.DataFrame) -> pd.DataFrame:
    """Merge efficiency data per fuel and technology into main DataFrame."""
    eff_data = eff_data[["Technology", "Fuel", "Efficiency"]]
    df = df.merge(eff_data, on=["Technology", "Fuel"], how="left")
    if RUN_TESTS:
        check_missing_efficiencies(df)
    df["Efficiency"] = df["Efficiency"].fillna(1)
    return df


def check_missing_capex(df: pd.DataFrame) -> None:
    """Log warning for technologies missing capital cost data."""
    missing_capex = df[df["CAPEX"].isna()][["Technology", "Fuel"]].drop_duplicates()
    if not missing_capex.empty:
        logger.warning("Processes with missing capital cost:")
        for _, row in missing_capex.iterrows():
            logger.warning("    %s - %s", row["Technology"], row["Fuel"])


def add_capex(df: pd.DataFrame, capex_data: pd.DataFrame) -> pd.DataFrame:
    """Merge and deflate capital costs into main DataFrame."""
    capex_data = capex_data[["Technology", "Fuel", "PriceBaseYear", "CAPEX"]]
    capex_data = deflate_data(
        capex_data, base_year=BASE_YEAR, variables_to_deflate=["CAPEX"]
    )
    df = df.merge(capex_data, on=["Technology", "Fuel"], how="left")
    if RUN_TESTS:
        check_missing_capex(df)
    return df


def add_afa(df: pd.DataFrame, afa_data: pd.DataFrame) -> pd.DataFrame:
    """Merge Annual Full Availability (AFA) data into main DataFrame."""
    afa_data = afa_data[["Technology", "AFA"]]
    return df.merge(afa_data, on="Technology", how="left")


def estimate_capacity(df: pd.DataFrame) -> pd.DataFrame:
    """Estimate process capacity from energy input, efficiency, and AFA."""
    df["InputEnergy"] = df["Value"]
    df["OutputEnergy"] = df["InputEnergy"] * df["Efficiency"]
    df["Capacity"] = df["OutputEnergy"] / CAP2ACT / df["AFA"]
    return df


def tidy_data(df: pd.DataFrame) -> pd.DataFrame:
    """Reshape DataFrame to long format with standardized units."""
    df = df.drop(columns=["Value", "Unit", "PriceBaseYear"])
    value_units = {
        "Life": "Years",
        "Efficiency": "%",
        "CAPEX": f"{BASE_YEAR} NZD/kW",
        "AFA": "%",
        "InputEnergy": "PJ",
        "OutputEnergy": "PJ",
        "Capacity": "GW",
    }
    id_cols = df.columns.difference(value_units.keys()).tolist()
    df = df.melt(id_vars=id_cols, var_name="Variable", value_name="Value")
    df["Unit"] = df["Variable"].map(value_units)
    return df


# ---------------------------------------------------------------------------
# Main execution
# ---------------------------------------------------------------------------


def main() -> None:
    """Entry-point for adding assumptions to industrial base-year data."""
    df = pd.read_csv(OUTPUT_LOCATION / "2_times_baseyear_regional_disaggregation.csv")

    tech_lifetimes = pd.read_csv(INDUSTRY_ASSUMPTIONS / "tech_lifetimes.csv")
    tech_afa = pd.read_csv(INDUSTRY_ASSUMPTIONS / "tech_afa.csv")
    tech_fuel_efficiencies = pd.read_csv(
        INDUSTRY_ASSUMPTIONS / "tech_fuel_efficiencies.csv"
    )
    tech_fuel_capex = pd.read_csv(INDUSTRY_ASSUMPTIONS / "tech_fuel_capex.csv")

    h2("Adding technology lifetimes")
    df = add_lifetimes(df, tech_lifetimes)

    h2("Adding efficiency per fuel and technology")
    df = add_efficiencies(df, tech_fuel_efficiencies)

    h2("Adding capital costs")
    df = add_capex(df, tech_fuel_capex)

    h2("Adding tech availabilities")
    df = add_afa(df, tech_afa)

    h2("Estimating capacity")
    df = estimate_capacity(df)

    h2("Cleaning up")
    df = tidy_data(df)

    save_output(df, "3_times_baseyear_with_assumptions.csv")


if __name__ == "__main__":
    main()
