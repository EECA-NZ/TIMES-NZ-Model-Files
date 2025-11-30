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
# Constants & File Paths
# ---------------------------------------------------------------------
INPUT_FILE = Path(STAGE_4_DATA) / "base_year_ind" / "industry_baseyear_details.csv"
OUTPUT_LOCATION = Path(STAGE_4_DATA) / "subres_ind"
OUTPUT_LOCATION.mkdir(parents=True, exist_ok=True)

NEW_TECHS_CAPEX = INDUSTRY_ASSUMPTIONS / "newtech_fuel_capex.csv"
NEW_TECHS_EFF = INDUSTRY_ASSUMPTIONS / "newtech_fuel_efficiencies.csv"
NEW_TECHS_LIFE = INDUSTRY_ASSUMPTIONS / "newtech_lifetimes.csv"
NEW_TECHS_FUEL = INDUSTRY_CONCORDANCES / "fuel_codes.csv"
NEW_TECHS = INDUSTRY_CONCORDANCES / "tech_codes.csv"
NEW_TECHS_SECTOR = INDUSTRY_CONCORDANCES / "sector_codes.csv"
NEW_TECHS_ENDUSE = INDUSTRY_CONCORDANCES / "use_codes.csv"

# ---------------------------------------------------------------------
# Modelling Constants
# ---------------------------------------------------------------------
START = 2025
ACTIVITY_UNIT = "PJ"
CAPACITY_UNIT = "GW"
AF = 0.5
VINTAGE = "YES"


# ---------------------------------------------------------------------
# Create New Tech Processes
# ---------------------------------------------------------------------
def create_newtech_process_df(_cfg: dict) -> pd.DataFrame:
    """Create DataFrame defining new commercial technologies."""
    df = pd.read_csv(INPUT_FILE).dropna(how="all")
    df.columns = df.columns.str.strip().str.replace(" ", "_").str.replace("-", "_")
    df = df.astype(str).apply(lambda col: col.str.strip())

    def make_filtered(df, condition, suffix, comm_in):
        temp = df[df["Comm_OUT"].str.endswith(condition)].copy()
        temp["Sector"] = temp["Comm_OUT"].str.split("-").str[0]
        temp["TechName"] = temp["Sector"] + suffix
        temp["Comm_IN"] = comm_in
        return temp.drop_duplicates(subset=["TechName", "Comm_OUT"])

    filtered_sets = [
        df[(df["Comm_IN"] == "INDCOA") & (df["Comm_OUT"].str.endswith("BOILR-PH_INT"))]
        .assign(
            Sector=lambda x: x["Comm_OUT"].str.split("-").str[0],
            TechName=lambda x: x["Comm_OUT"].str.split("-").str[0]
            + "-WOD-BOILR-PH_INT",
            Comm_IN="INDWOD",
        )
        .drop_duplicates(subset=["TechName", "Comm_OUT"]),
        make_filtered(df, "WH_LOW", "-ELC-BOILR-WH_LOW", "INDELC"),
        make_filtered(df, "WH_LOW", "-WOD-BOILR-WH_LOW", "INDWOD"),
        make_filtered(df, "SH_LOW", "-ELC-BOILR-SH_LOW", "INDLEC"),
        make_filtered(df, "PH_INT", "-ELC-SGHP-PH_INT", "INDELC"),
        make_filtered(df, "PH_INT", "-ELC-MVR-PH_INT", "INDELC"),
        make_filtered(df, "PH_LOW", "-ELC-PEF-PH_LOW", "INDELC"),
        make_filtered(df, "MTV_MOB", "-ELC-ICENG-MTV_MOB", "INDELC"),
        make_filtered(df, "MTV_MOB", "-H2R-ICENG-MTV_MOB", "INDH2R"),
        make_filtered(df, "MTV_MOB", "-PET-PHEV-MTV_MOB", "INDPET"),
        make_filtered(df, "MTV_MOB", "-ELC-PHEV-MTV_MOB", "INDELC"),
    ]

    combined = pd.concat(filtered_sets, ignore_index=True).drop_duplicates(
        subset=["TechName", "Comm_OUT"]
    )
    new_df = pd.DataFrame(
        {
            "Sets": "DMD",
            "TechName": combined["TechName"].unique(),
            "Tact": ACTIVITY_UNIT,
            "Tcap": CAPACITY_UNIT,
            "TsLvl": "DAYNITE",
            "Vintage": VINTAGE,
        }
    )

    return new_df, combined


# ---------------------------------------------------------------------
# Create Parameters for New Techs
# ---------------------------------------------------------------------
def create_newtech_process_parameters_df(cfg: dict) -> pd.DataFrame:
    """Build parameter DataFrame for new technologies (CAPEX, Efficiency, Life, etc.)."""
    _, combined = create_newtech_process_df(cfg)
    df = combined[["TechName", "Comm_IN", "Comm_OUT"]].copy()
    df["START"], df["AFA"] = START, AF

    # Load assumption & concordance files
    capex = pd.read_csv(NEW_TECHS_CAPEX)
    eff = pd.read_csv(NEW_TECHS_EFF)
    life = pd.read_csv(NEW_TECHS_LIFE)
    fuel_map = pd.read_csv(NEW_TECHS_FUEL)
    tech_map = pd.read_csv(NEW_TECHS)
    for data in [capex, eff, life, fuel_map, tech_map]:
        data.columns = data.columns.str.strip()

    # Merge concordances
    capex = capex.merge(fuel_map, on="Fuel", how="left").merge(
        tech_map, on="Technology", how="left"
    )
    eff = eff.merge(fuel_map, on="Fuel", how="left").merge(
        tech_map, on="Technology", how="left"
    )
    life = life.merge(tech_map, on="Technology", how="left")

    df["Fuel_TIMES"] = df["TechName"].str.split("-").str[1]
    df["Technology_TIMES"] = df["TechName"].str.split("-").str[2]

    df = (
        df.merge(
            capex[["Fuel_TIMES", "Technology_TIMES", "CAPEX"]],
            on=["Fuel_TIMES", "Technology_TIMES"],
            how="left",
        )
        .merge(
            eff[["Fuel_TIMES", "Technology_TIMES", "Efficiency"]],
            on=["Fuel_TIMES", "Technology_TIMES"],
            how="left",
        )
        .merge(life[["Technology_TIMES", "Life"]], on="Technology_TIMES", how="left")
    )

    if "CAPEX" in df.columns:
        df["PriceBaseYear"] = 2022
        df = deflate_data(df, 2023, ["CAPEX"])

    df.drop(columns=["Fuel_TIMES", "Technology_TIMES"], inplace=True)
    df.rename(
        columns={"CAPEX": "INVCOST", "Efficiency": "EFF", "Life": "LIFE"}, inplace=True
    )

    cols = cfg.get(
        "Columns",
        ["TechName", "Comm-IN", "Comm-OUT", "START", "EFF", "LIFE", "INVCOST", "AF"],
    )
    for col in cols:
        if col not in df.columns:
            df[col] = ""

    return df[cols]


def create_newtech_process_defintions(cfg: dict) -> pd.DataFrame:
    """Create DataFrame defining new industrial technologies
    to patch in the app from industrial concordances."""

    process_cols = [
        "Process",
        "CommodityIn",
        "CommodityOut",
        "Sector",
        "EnduseGroup",
        "EndUse",
        "TechnologyGroup",
        "Technology",
    ]

    _, combined = create_newtech_process_df(cfg)

    # Read concordances
    tech_map = pd.read_csv(NEW_TECHS)
    sector_map = pd.read_csv(NEW_TECHS_SECTOR)
    enduse_map = pd.read_csv(NEW_TECHS_ENDUSE)

    # Strip column names
    for d in [tech_map, sector_map, enduse_map]:
        d.columns = d.columns.str.strip()

    # --- Merge TIMES codes onto combined tech list ---
    df = combined.copy()
    df["Sector_TIMES"] = df["TechName"].str.split("-").str[0]
    df["Technology_TIMES"] = df["TechName"].str.split("-").str[2]
    df["EndUse_TIMES"] = df["TechName"].str.split("-").str[3]

    # --- Sector merge (use suffixes to avoid column collision) ---
    df = df.merge(
        sector_map[["Sector_TIMES", "Sector"]],
        on="Sector_TIMES",
        how="left",
        suffixes=("_orig", "_map"),
    )
    # Use mapped Sector from concordance, fallback to original
    df["Sector"] = df["Sector_map"].fillna(df["Sector_orig"])
    df = df.drop(columns=["Sector_orig", "Sector_map"])

    # --- Technology merge ---
    df = df.merge(
        tech_map[["Technology_TIMES", "Technology", "TechGroup"]],
        on="Technology_TIMES",
        how="left",
    )

    # --- EndUse merge ---
    df = df.merge(
        enduse_map[["EndUse_TIMES", "EndUse", "UseGroup"]],
        on="EndUse_TIMES",
        how="left",
    )

    # Rename columns
    df = df.rename(
        columns={
            "TechName": "Process",
            "Comm_IN": "CommodityIn",
            "Comm_OUT": "CommodityOut",
            "TechGroup": "TechnologyGroup",
            "UseGroup": "EnduseGroup",
        }
    )

    return df[process_cols]


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------
def main() -> None:
    """Generate and export TIMES-NZ new commercial tech definitions & parameters."""
    process_cols = ["Sets", "TechName", "Tact", "Tcap", "TsLvl", "Vintage"]
    param_cols = [
        "TechName",
        "Comm_IN",
        "Comm_OUT",
        "START",
        "EFF",
        "LIFE",
        "INVCOST",
        "AF",
    ]

    processes, _ = create_newtech_process_df({"Columns": process_cols})
    parameters = create_newtech_process_parameters_df({"Columns": param_cols})
    process_definitions = create_newtech_process_defintions({})

    processes.to_csv(OUTPUT_LOCATION / "future_industry_processes.csv", index=False)
    parameters.to_csv(OUTPUT_LOCATION / "future_industry_parameters.csv", index=False)
    process_definitions.to_csv(
        OUTPUT_LOCATION / "future_industry_process_definitions.csv", index=False
    )

    logger.info("New industry technology files successfully generated.")


if __name__ == "__main__":
    main()
