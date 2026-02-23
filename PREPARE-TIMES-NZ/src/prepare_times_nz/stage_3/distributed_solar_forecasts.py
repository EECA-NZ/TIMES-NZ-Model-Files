"""
Exogenous distributed solar forecasts based on EDGS 2024 modelling assumptions.

Pipeline:
1) Load raw data from csv
2) Extract total capacity (MW) by year for com, res, and ind sectors.
3) Map EDGS Reference scenario to TIMES-NZ Traditional,
    and EDGS Innovation scenario to TIMES-NZ Transformation.
4) Export scenario workbooks.


"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from prepare_times_nz.utilities.filepaths import EXTERNAL_DATA, STAGE_3_DATA

INPUT_DIR = (
    Path(EXTERNAL_DATA)
    / "mbie"
    / "electricity-demand-generation-scenarios-2024-assumptions.xlsx"
)
OUTPUT_DIR = STAGE_3_DATA / "distributed_solar"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TRADITIONAL_CSV = OUTPUT_DIR / "traditional_distributed_solar_forecasts.csv"
TRANSFORMATION_CSV = OUTPUT_DIR / "transformation_distributed_solar_forecasts.csv"


# Mapping for sectors
SECTOR_MAP = {
    "Commercial": "ELC_SolarDist_Commercial",
    "Residential": "ELC_SolarDist_Residential",
    "Industrial": "ELC_SolarDist_Industrial",
}


def extract_and_save_distributed_solar():
    """Extract distributed solar forecasts from EDGS assumptions
    and save to CSV."""
    # Load the Distributed solar PV sheet
    df = pd.read_excel(INPUT_DIR, sheet_name="Distributed solar PV")

    # Filter for Variable: Total capacity
    df = df[df["Variable"] == "Total capacity"]

    # Map TimePeriod to Year, Variable to NCAP_BND~FX
    df = df.rename(columns={"TimePeriod": "Year"})
    # Filter only years from 2023 and ahead
    df = df[df["Year"] >= 2023]
    df["NCAP_BND~FX"] = df["Value"]

    # Map sectors
    df["TechName"] = df["Sector"].map(SECTOR_MAP)
    df = df[df["TechName"].notnull()]

    # Scenario mapping
    # EDGS Reference -> TIMES-NZ Traditional (output: traditional CSV)
    # EDGS Innovation -> TIMES-NZ Transformation (output: transformation CSV)
    out_cols = ["TechName", "Year", "NCAP_BND~FX"]

    # Traditional/Innovation: filter Reference scenario
    df_trad = df[df["Scenario"] == "Reference"]
    df_trad_out = df_trad[out_cols]
    df_trad_out.to_csv(TRADITIONAL_CSV, index=False)

    # Transformation: filter Transformation scenario
    df_trans = df[df["Scenario"] == "Innovation"]
    df_trans_out = df_trans[out_cols]
    df_trans_out.to_csv(TRANSFORMATION_CSV, index=False)


def main():
    """Main execution function."""
    extract_and_save_distributed_solar()


if __name__ == "__main__":
    main()
