"""
Here we find the Electricity Authority (EA) Excel files, extract the
datasets and write them to the
"data_intermediate/stage_1_external_data/electricity_authority" folder.
This will include any EDGS assumptions we want to use and any official figures we want.
We also do some tidying/standardising here.

Outputs
-------
* "emi_md.parquet"               - half-hourly Generation_MD files (combined).
* "emi_distributed_solar.csv"    - tidy distributed-solar summary.
* "emi_nsp_concordances.csv"     - POC → region / zone / island concordance.

Run directly::

    python -m prepare_times_nz.stages.extract_ea_data
"""

from __future__ import annotations

import glob
import logging
from pathlib import Path
from typing import List

import pandas as pd
from prepare_times_nz.filepaths import DATA_RAW, STAGE_1_DATA

# --------------------------------------------------------------------------- #
# Logging
# --------------------------------------------------------------------------- #
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# --------------------------------------------------------------------------- #
# Constants - all paths use pathlib for cross-platform consistency
# --------------------------------------------------------------------------- #
INPUT_LOCATION = Path(DATA_RAW) / "external_data" / "electricity_authority"
OUTPUT_LOCATION = Path(STAGE_1_DATA) / "electricity_authority"
OUTPUT_LOCATION.mkdir(parents=True, exist_ok=True)

EMI_MD_FOLDER: Path = INPUT_LOCATION / "emi_md"
EMI_FLEET_FILE: Path = (
    INPUT_LOCATION / "emi_fleet_data" / "20230601_DispatchedGenerationPlant.csv"
)  # currently unused, retained for future work
EMI_NSP_TABLE: Path = (
    INPUT_LOCATION / "emi_nsp_table" / "20250308_NetworkSupplyPointsTable.csv"
)
EMI_DISTRIBUTED_SOLAR_DIR: Path = INPUT_LOCATION / "emi_distributed_solar"

# --------------------------------------------------------------------------- #
# Helper functions
# --------------------------------------------------------------------------- #


def combine_md_generation(csv_folder: Path) -> pd.DataFrame:
    """Load every "*.csv" in *csv_folder* and return a long-format DataFrame."""
    files = glob.glob(str(csv_folder / "*.csv"))
    if not files:
        logger.warning("No Generation_MD files found in %s", csv_folder)
        return pd.DataFrame()

    frames: List[pd.DataFrame] = []
    for file in files:
        logger.info("Reading Generation_MD file %s", Path(file).name)
        frames.append(pd.read_csv(file))

    md_df = pd.concat(frames, ignore_index=True)

    # Identify trading-period columns (TP1 … TP48)
    tp_cols = [col for col in md_df.columns if col.startswith("TP")]

    md_df = pd.melt(
        md_df,
        id_vars=md_df.columns.difference(tp_cols),
        value_vars=tp_cols,
        var_name="Trading_Period",
        value_name="Value",
    )
    return md_df


def read_distributed_solar(sector: str) -> pd.DataFrame:
    """
    Load a distributed-solar CSV for *sector* (Residential / Commercial / Industrial).
    The EA files live at https://www.emi.ea.govt.nz/Retail/Reports/GUEHMT.
    """
    filename = f"solar_{sector.lower()}.csv"
    path = EMI_DISTRIBUTED_SOLAR_DIR / filename
    logger.info("Reading %s solar data", sector)
    df = pd.read_csv(path, skiprows=12)
    df["Sector"] = sector
    return df


def tidy_distributed_solar() -> pd.DataFrame:
    """Return a cleaned DataFrame combining all distributed-solar sectors."""
    solar_df = pd.concat(
        [
            read_distributed_solar("Residential"),
            read_distributed_solar("Commercial"),
            read_distributed_solar("Industrial"),
        ],
        ignore_index=True,
    )

    # Drop columns we don’t currently use (fuel type retained for future battery split)
    solar_df = solar_df.drop(columns=["Region ID", "Capacity", "Fuel type"])

    solar_df = solar_df.rename(
        columns={
            "Avg. capacity installed (kW)": "avg_cap_kw",
            "Avg. capacity - new installations (kW)": "avg_cap_new_kw",
            "ICP count - new installations": "icp_count_new",
            "ICP uptake rate (%)": "icp_uptake_proportion",
            "Total capacity installed (MW)": "capacity_installed_mw",
            "ICP count": "icp_count",
            "Region name": "Region",
            "Month end": "Month",
        }
    )

    # Convert percentage and date
    solar_df["icp_uptake_proportion"] = solar_df["icp_uptake_proportion"] / 100
    solar_df["Month"] = pd.to_datetime(solar_df["Month"], dayfirst=True)

    return solar_df


def build_nsp_concordance(nsp_csv: Path) -> pd.DataFrame:
    """Create a POC → region / zone / island concordance table."""
    df = pd.read_csv(nsp_csv)
    df = df[df["Current flag"] == 1].copy()

    # Simple three-letter POC code
    df["POC"] = df["POC code"].str[:3]

    cols = ["POC", "Network reporting region", "Zone", "Island"]
    df = df[cols].drop_duplicates()
    df = df.rename(columns={"Network reporting region": "Network_reporting_region"})
    return df


# --------------------------------------------------------------------------- #
# Main execution
# --------------------------------------------------------------------------- #


def main() -> None:
    """Run all EA-data extraction steps."""
    # 1. Generation_MD
    md_df = combine_md_generation(EMI_MD_FOLDER)
    if not md_df.empty:
        md_path = OUTPUT_LOCATION / "emi_md.parquet"
        md_df.to_parquet(md_path, engine="pyarrow")
        logger.info("Wrote Generation_MD parquet to %s", md_path)

    # 2. Distributed solar
    solar_df = tidy_distributed_solar()
    solar_path = OUTPUT_LOCATION / "emi_distributed_solar.csv"
    solar_df.to_csv(solar_path, index=False)
    logger.info("Wrote distributed-solar CSV to %s", solar_path)

    # 3. NSP concordance
    nsp_df = build_nsp_concordance(EMI_NSP_TABLE)
    nsp_path = OUTPUT_LOCATION / "emi_nsp_concordances.csv"
    nsp_df.to_csv(nsp_path, index=False)
    logger.info("Wrote NSP concordance CSV to %s", nsp_path)


if __name__ == "__main__":
    main()
