"""
Executes building Veda files for new commercial techs
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from prepare_times_nz.stage_2.industry.common import (
    INDUSTRY_ASSUMPTIONS,
    INDUSTRY_CONCORDANCES,
)
from prepare_times_nz.utilities.deflator import deflate_data
from prepare_times_nz.utilities.filepaths import STAGE_4_DATA
from prepare_times_nz.utilities.logger_setup import logger

# ---------------------------------------------------------------------
# Constants & file paths
# ---------------------------------------------------------------------

INPUT_LOCATION = Path(STAGE_4_DATA) / "base_year_ind"
INPUT_FILE: Path = INPUT_LOCATION / "industry_baseyear_details.csv"

OUTPUT_LOCATION = Path(STAGE_4_DATA) / "subres_ind"
OUTPUT_LOCATION.mkdir(parents=True, exist_ok=True)

NEW_TECHS_CAPEX: Path = INDUSTRY_ASSUMPTIONS / "newtech_fuel_capex.csv"
NEW_TECHS_EFF: Path = INDUSTRY_ASSUMPTIONS / "newtech_fuel_efficiencies.csv"
NEW_TECHS_LIFE: Path = INDUSTRY_ASSUMPTIONS / "newtech_lifetimes.csv"

NEW_TECHS_FUEL: Path = INDUSTRY_CONCORDANCES / "fuel_codes.csv"
NEW_TECHS: Path = INDUSTRY_CONCORDANCES / "tech_codes.csv"

# ---------------------------------------------------------------------
# Modelling constants
# ---------------------------------------------------------------------
START = 2025
ACTIVITY_UNIT = "PJ"
CAPACITY_UNIT = "GW"
AFA = 0.05
VINTAGE = "YES"


# ---------------------------------------------------------------------
# Create New Tech Processes
# ---------------------------------------------------------------------
def create_newtech_process_df(_cfg: dict) -> pd.DataFrame:
    """Creates a DataFrame defining new commercial technologies."""
    # Load and clean input dataset
    df = pd.read_csv(INPUT_FILE, sep=",").dropna(how="all")
    df.columns = df.columns.str.strip().str.replace(" ", "_").str.replace("-", "_")
    df = df.astype(str).apply(lambda col: col.str.strip())

    # First set: Replace -COA-BOILR-PH_INT → -WOD-BOILR-PH_INT
    filtered_wod = df[
        (df["Comm_IN"] == "INDCOA") & (df["Comm_OUT"].str.endswith("BOILR-PH_INT"))
    ].copy()
    filtered_wod["Sector"] = filtered_wod["Comm_OUT"].str.split("-").str[0]
    filtered_wod["TechName"] = filtered_wod["Sector"] + "-WOD-BOILR-PH_INT"
    filtered_wod["Comm_IN"] = "INDWOD"
    filtered_wod = filtered_wod.drop_duplicates(subset=["TechName", "Comm_OUT"])

    # Second set: Add ELC-SGHP-PH_INT for all PH_INTs
    filtered_sghp = df[df["Comm_OUT"].str.endswith("PH_INT")].copy()
    filtered_sghp["Sector"] = filtered_sghp["Comm_OUT"].str.split("-").str[0]
    filtered_sghp["TechName"] = filtered_sghp["Sector"] + "-ELC-SGHP-PH_INT"
    filtered_sghp["Comm_IN"] = "INDELC"
    filtered_sghp = filtered_sghp.drop_duplicates(subset=["TechName", "Comm_OUT"])

    # Third set: Add ELC-MVR-PH_INT for all PH_INTs
    filtered_mvr = df[df["Comm_OUT"].str.endswith("PH_INT")].copy()
    filtered_mvr["Sector"] = filtered_mvr["Comm_OUT"].str.split("-").str[0]
    filtered_mvr["TechName"] = filtered_mvr["Sector"] + "-ELC-MVR-PH_INT"
    filtered_mvr["Comm_IN"] = "INDELC"
    filtered_mvr = filtered_mvr.drop_duplicates(subset=["TechName", "Comm_OUT"])

    # Fourth set: Add ELC-PEF-PH_LOW for all PH_LOWs
    filtered_pef = df[df["Comm_OUT"].str.endswith("PH_LOW")].copy()
    filtered_pef["Sector"] = filtered_pef["Comm_OUT"].str.split("-").str[0]
    filtered_pef["TechName"] = filtered_pef["Sector"] + "-ELC-PEF-PH_LOW"
    filtered_pef["Comm_IN"] = "INDELC"
    filtered_pef = filtered_pef.drop_duplicates(subset=["TechName", "Comm_OUT"])

    # Fifth set: Add ELC-ICENG-MTV_MOB for all MTV_MOBs
    filtered_iceng1 = df[df["Comm_OUT"].str.endswith("MTV_MOB")].copy()
    filtered_iceng1["Sector"] = filtered_iceng1["Comm_OUT"].str.split("-").str[0]
    filtered_iceng1["TechName"] = filtered_iceng1["Sector"] + "-ELC-ICENG-MTV_MOB"
    filtered_iceng1["Comm_IN"] = "INDELC"
    filtered_iceng1 = filtered_iceng1.drop_duplicates(subset=["TechName", "Comm_OUT"])

    # Sixth set: Add H2R-ICENG-MTV_MOB for all MTV_MOBs
    filtered_iceng2 = df[df["Comm_OUT"].str.endswith("MTV_MOB")].copy()
    filtered_iceng2["Sector"] = filtered_iceng2["Comm_OUT"].str.split("-").str[0]
    filtered_iceng2["TechName"] = filtered_iceng2["Sector"] + "-H2R-ICENG-MTV_MOB"
    filtered_iceng2["Comm_IN"] = "INDH2R"
    filtered_iceng2 = filtered_iceng2.drop_duplicates(subset=["TechName", "Comm_OUT"])

    # Seventh set: Add PET-PHEV-MTV_MOB for all MTV_MOBs
    filtered_phev1 = df[df["Comm_OUT"].str.endswith("MTV_MOB")].copy()
    filtered_phev1["Sector"] = filtered_phev1["Comm_OUT"].str.split("-").str[0]
    filtered_phev1["TechName"] = filtered_phev1["Sector"] + "-PET-PHEV-MTV_MOB"
    filtered_phev1["Comm_IN"] = "INDPET"
    filtered_phev1 = filtered_phev1.drop_duplicates(subset=["TechName", "Comm_OUT"])

    # Eighth set: Add ELC-PHEV-MTV_MOB for all MTV_MOBs
    filtered_phev2 = df[df["Comm_OUT"].str.endswith("MTV_MOB")].copy()
    filtered_phev2["Sector"] = filtered_phev2["Comm_OUT"].str.split("-").str[0]
    filtered_phev2["TechName"] = filtered_phev2["Sector"] + "-ELC-PHEV-MTV_MOB"
    filtered_phev2["Comm_IN"] = "INDELC"
    filtered_phev2 = filtered_phev2.drop_duplicates(subset=["TechName", "Comm_OUT"])

    # Combine all new techs
    combined = pd.concat(
        [
            filtered_wod,
            filtered_sghp,
            filtered_mvr,
            filtered_pef,
            filtered_iceng1,
            filtered_iceng2,
            filtered_phev1,
            filtered_phev2,
        ],
        ignore_index=True,
    ).drop_duplicates(subset=["TechName", "Comm_OUT"])

    # Build final new tech process DataFrame
    tech_names = combined["TechName"].unique()
    new_df = pd.DataFrame(
        {
            "Sets": "DMD",
            "TechName": tech_names,
            "Tact": ACTIVITY_UNIT,
            "Tcap": CAPACITY_UNIT,
            "Vintage": VINTAGE,
        }
    )

    return new_df, combined


# ---------------------------------------------------------------------
# Create Parameters for New Techs
# ---------------------------------------------------------------------
def create_newtech_process_parameters_df(cfg: dict) -> pd.DataFrame:
    """Builds the new tech parameter DataFrame with CAPEX, Efficiency, Life, etc."""
    # Get the list of new techs to parameterize
    _, combined = create_newtech_process_df(cfg)
    df = combined[["TechName", "Comm_IN", "Comm_OUT"]].copy()

    # Base columns
    df["START"] = START
    df["AFA"] = AFA

    # Load external assumption and concordance files
    capex = pd.read_csv(NEW_TECHS_CAPEX)
    eff = pd.read_csv(NEW_TECHS_EFF)
    life = pd.read_csv(NEW_TECHS_LIFE)
    fuel_map = pd.read_csv(NEW_TECHS_FUEL)
    tech_map = pd.read_csv(NEW_TECHS)

    # Normalize column headers
    for data in [capex, eff, life, fuel_map, tech_map]:
        data.columns = data.columns.str.strip()

    # Map Fuel and Technology to TIMES codes
    capex = capex.merge(fuel_map, on="Fuel", how="left")
    capex = capex.merge(tech_map, on="Technology", how="left")

    eff = eff.merge(fuel_map, on="Fuel", how="left")
    eff = eff.merge(tech_map, on="Technology", how="left")

    life = life.merge(tech_map, on="Technology", how="left")

    # Extract the fuel part from TechName (strip)
    df["Fuel_TIMES"] = df["TechName"].str.split("-").str[1]
    df["Technology_TIMES"] = df["TechName"].str.split("-").str[2]

    # Merge CAPEX, EFF, LIFE using concordance-based TIMES codes
    df = df.merge(
        capex[["Fuel_TIMES", "Technology_TIMES", "CAPEX"]],
        on=["Fuel_TIMES", "Technology_TIMES"],
        how="left",
    )
    df = df.merge(
        eff[["Fuel_TIMES", "Technology_TIMES", "Efficiency"]],
        on=["Fuel_TIMES", "Technology_TIMES"],
        how="left",
    )
    df = df.merge(life[["Technology_TIMES", "Life"]], on="Technology_TIMES", how="left")

    # Apply deflator to CAPEX (2022 → 2023)
    if "CAPEX" in df.columns:
        df["PriceBaseYear"] = 2022
        df = deflate_data(df, 2023, ["CAPEX"])

    # Clean and finalize
    df.drop(columns=["Fuel_TIMES", "Technology_TIMES"], inplace=True)
    df.rename(
        columns={"CAPEX": "INVCOST", "Efficiency": "EFF", "Life": "LIFE"}, inplace=True
    )

    # Ensure required columns exist
    requested_cols = cfg.get(
        "Columns",
        ["TechName", "Comm-IN", "Comm-OUT", "START", "EFF", "LIFE", "INVCOST", "AFA"],
    )
    for col in requested_cols:
        if col not in df.columns:
            df[col] = ""

    return df[requested_cols]


# ---------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------
def main() -> None:
    """Generates and exports TIMES-NZ commercial sector new technology
    definitions and parameters."""
    process_cols = ["Sets", "TechName", "Tact", "Tcap", "Vintage"]
    param_cols = [
        "TechName",
        "Comm_IN",
        "Comm_OUT",
        "START",
        "EFF",
        "LIFE",
        "INVCOST",
        "AFA",
    ]

    processes, _ = create_newtech_process_df({"Columns": process_cols})
    parameters = create_newtech_process_parameters_df({"Columns": param_cols})

    processes.to_csv(OUTPUT_LOCATION / "future_industry_processes.csv", index=False)
    parameters.to_csv(OUTPUT_LOCATION / "future_industry_parameters.csv", index=False)

    logger.info("New industry technology files successfully generated.")


if __name__ == "__main__":
    main()
