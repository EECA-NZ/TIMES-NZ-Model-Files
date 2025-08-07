"""
Extract and reshape Gas Industry Company (GIC) production / consumption data
for the TIMES-NZ preparation pipeline.

Steps performed
---------------
1. Read the "Prod_Cons" and "Rep Major Users" sheets from
   "data_raw/external_data/gic/ProductionConsumption.xlsx".
2. Merge them on the "Date" column (outer merge to keep every row).
3. Tidy / pivot to long format.
4. Label each participant as a *Producer* or *Consumer*.
5. Save the result to
   "data_intermediate/stage_1_external_data/gic/gic_production_consumption.csv".

Run directly::

    python -m prepare_times_nz.stages.extract_gic_data
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List

import pandas as pd
from prepare_times_nz.utilities.filepaths import DATA_RAW, STAGE_1_DATA

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
INPUT_DIR: Path = Path(DATA_RAW) / "external_data" / "gic"
OUTPUT_DIR: Path = Path(STAGE_1_DATA) / "gic"
GIC_FILENAME = "ProductionConsumption.xlsx"

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def read_gic_sheet(sheet_name: str) -> pd.DataFrame:
    """Read *sheet_name* from the GIC workbook and return a DataFrame."""
    gic_path = INPUT_DIR / GIC_FILENAME
    logger.debug("Reading sheet '%s' from %s", sheet_name, gic_path)
    return pd.read_excel(gic_path, sheet_name=sheet_name)


def get_all_gic_data() -> pd.DataFrame:
    """
    Merge production/consumption and major-user sheets on the "Date" column.

    Uses an outer join so that rows present in only one sheet are retained.
    """
    df_prod_cons = read_gic_sheet("Prod_Cons")
    df_major_users = read_gic_sheet("Rep Major Users")
    merged = pd.merge(df_prod_cons, df_major_users, on="Date", how="outer")
    return merged


def pivot_gic_data(df: pd.DataFrame) -> pd.DataFrame:
    """Convert wide DataFrame to long format with *Participant* / *Value* columns."""
    return df.melt(id_vars="Date", var_name="Participant", value_name="Value")


def define_producers_and_consumers(df: pd.DataFrame) -> pd.DataFrame:
    """
    Label each *Participant* as **Producer** or **Consumer**.

    The list of producers is based on the GIC producer/consumer list.
    """
    producers: List[str] = [
        "Pohokura",
        "Maui",
        "McKee/Mangahewa",
        "Turangi and Kowhai",
        "Kupe",
        "Kapuni",
        "Kaimiro",
        "Mokoia",
        "Cheal",
        "Sidewinder",
    ]

    df["UserType"] = "Consumer"
    df.loc[df["Participant"].isin(producers), "UserType"] = "Producer"
    return df


def label_and_rearrange(df: pd.DataFrame) -> pd.DataFrame:
    """Add "Unit" column and reorder for final output."""
    df["Unit"] = "TJ"
    return df[["Date", "UserType", "Participant", "Unit", "Value"]]


# ---------------------------------------------------------------------------
# Main execution flow
# ---------------------------------------------------------------------------


def main() -> None:
    """Orchestrate reading, processing, and writing of GIC data."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    df = get_all_gic_data()
    df = pivot_gic_data(df)
    df = define_producers_and_consumers(df)
    df = label_and_rearrange(df)

    out_path = OUTPUT_DIR / "gic_production_consumption.csv"
    df.to_csv(out_path, index=False)
    logger.info("Wrote cleaned GIC data to %s", out_path)


if __name__ == "__main__":
    main()
