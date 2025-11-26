"""
Aggregate regional biomass CSVs into EECA feedstock classifications.

Pipeline:
1) Load all CSV biomass feedstock files (regional × time period)
2) Map and aggregate by feedstock family (Residual Woody Biomass, etc.)
3) Export classification-level CSVs
4) Export combined workbook for QA

Outputs:
  - Aggregated CSVs: <OUTPUT_DIR>
  - Combined workbook: <OUTPUT_DIR>/Aggregated_Biomass_All.xlsx

Notes:
 - To maintain soil nutrition and health, it is assumed that
   half of all straw and stover must remain on-site, accordingly,
   the gross available material is reduced by 50% to reflect this retention requirement.
 - Gross wood processing residues supply is after incumbent use.
   Some regions have negative supply values.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from prepare_times_nz.utilities.filepaths import EXTERNAL_DATA, STAGE_3_DATA
from prepare_times_nz.utilities.logger_setup import blue_text, logger

# ----------------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------------

INPUT_DIR = Path(EXTERNAL_DATA) / "scion" / "residual_biomass"
OUTPUT_DIR = STAGE_3_DATA / "biofuel"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------
def load_csvs(input_dir: Path) -> dict[str, pd.DataFrame]:
    """Load all CSVs into a dictionary keyed by filename stem, handling commas and text.

    Parameters
    ----------
    input_dir : Path
        Directory containing CSV input files.

    Returns
    -------
    dict[str, pd.DataFrame]
        Dictionary mapping file stems to loaded DataFrames.
    """
    csv_files = list(input_dir.glob("*.csv"))
    data: dict[str, pd.DataFrame] = {}
    if not csv_files:
        logger.warning("No CSV files found → %s", blue_text(input_dir))
        return data

    for file_path in csv_files:
        name = file_path.stem.lower()
        try:
            df = pd.read_csv(file_path, thousands=",", skip_blank_lines=True)
            df.columns = [c.strip() for c in df.columns]

            # Convert all numeric-looking columns (years like "2024-2028")
            for col in df.columns:
                if "-" in col or col.replace("-", "").isdigit():
                    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

            data[name] = df
            logger.info(
                "Loaded file → %s (numeric columns parsed)", blue_text(file_path.name)
            )

        except (OSError, ValueError, pd.errors.ParserError) as err:
            logger.error("Error reading %s: %s", file_path.name, err)

    return data


def expand_year_range(colname: str) -> list[int]:
    """Expand a year-range column name like '2024-2028' into a list of years."""
    try:
        start, end = map(int, colname.split("-"))
        return list(range(start, end + 1))
    except (ValueError, AttributeError):
        return []


# pylint: disable=too-many-locals
def aggregate_all_files(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Aggregate all biomass CSVs by file name (ignore classification)."""
    all_records = []

    for key, df in data.items():
        df = df.copy()
        df["BiomassType"] = key

        if "Unnamed: 0" in df.columns:
            df = df.rename(columns={"Unnamed: 0": "Region"})

        numeric_cols = df.select_dtypes(include="number").columns
        year_cols = [c for c in df.columns if "-" in c and c.replace("-", "").isdigit()]
        year_cols = list(set(year_cols) | set(numeric_cols))
        keep_cols = ["Region", "BiomassType"] + year_cols
        df = df[keep_cols]

        grouped = df.groupby(["BiomassType", "Region"], as_index=False)[year_cols].sum()
        all_records.append(grouped)

    if not all_records:
        logger.warning("No aggregated data produced.")
        return pd.DataFrame()

    logger.info("Merging all files into one dataset…")
    combined_all = pd.concat(all_records, ignore_index=True)

    long_df = combined_all.melt(
        id_vars=["BiomassType", "Region"], var_name="YearRange", value_name="Value"
    )
    long_df["Value"] = pd.to_numeric(long_df["Value"], errors="coerce").fillna(0.0)

    # Expand year ranges
    expanded_records = [
        {
            "BiomassType": row["BiomassType"],
            "Region": row["Region"],
            "Year": int(y),
            "Value": float(row["Value"]) if pd.notna(row["Value"]) else None,
        }
        for _, row in long_df.iterrows()
        for y in expand_year_range(str(row["YearRange"]))
    ]

    expanded_df = pd.DataFrame(expanded_records)
    expanded_df["Value"] = expanded_df["Value"] / 1e6

    all_years = expanded_df["Year"].unique()
    all_regions = expanded_df["Region"].unique()
    all_types = expanded_df["BiomassType"].unique()

    # Create a full MultiIndex
    full_index = pd.MultiIndex.from_product(
        [all_types, all_regions, all_years], names=["BiomassType", "Region", "Year"]
    )

    # Reindex → missing years become NaN
    expanded_df = (
        expanded_df.set_index(["BiomassType", "Region", "Year"])
        .reindex(full_index)
        .reset_index()
    )

    expanded_df["Unit"] = "PJ"

    expanded_df = expanded_df.sort_values(
        by=["BiomassType", "Region", "Year"]
    ).reset_index(drop=True)

    logger.info("Converted all energy values to PJ and added Unit column.")
    logger.info("Expanded year ranges into %d rows total.", len(expanded_df))
    return expanded_df


def save_outputs(df: pd.DataFrame, output_dir: Path) -> None:
    """Save combined long-format dataset."""
    output_path = output_dir / "aggregated_regional_biomass_supply_projections.csv"
    df.to_csv(output_path, index=False)
    logger.info("Saved combined output → %s", blue_text(output_path))


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------
def main() -> None:
    """Main entry point for biomass aggregation pipeline."""
    logger.info("Reading input files from %s", blue_text(INPUT_DIR))
    data = load_csvs(INPUT_DIR)

    logger.info("Aggregating by feedstock classification and reshaping…")
    df = aggregate_all_files(data)

    if df.empty:
        logger.warning("No final output created.")
        return

    save_outputs(df, OUTPUT_DIR)
    logger.info("Biomass aggregation complete: %s rows", len(df))


if __name__ == "__main__":
    main()
