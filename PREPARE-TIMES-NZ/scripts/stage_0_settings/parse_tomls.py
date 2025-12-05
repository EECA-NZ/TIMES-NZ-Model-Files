"""
Parse TOML configuration files for the TIMES-NZ preparation pipeline.

Steps performed
----------------
1. Locate every "*.toml" file in "data_raw/user_config".
2. Normalise each file (expanding defaults) via
   :pyfunc:`prepare_times_nz.utilities.toml_readers.parse_toml_file`.
3. Save the normalised TOMLs to "data_intermediate/stage_0_config" so
   that later stages have a single, explicit source of truth.
4. Write a CSV ("config_metadata.csv") describing the workbook/table
   layout required for the Excel builder.

The script is idempotent and safe to run multiple times.

Run directly::

    python -m prepare_times_nz.stages.parse_tomls

or import the :pyfunc:`main` function from elsewhere in the pipeline
or tests.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List

import pandas as pd
import tomli_w
from prepare_times_nz.stage_0.generate_documentation import main as document
from prepare_times_nz.stage_0.toml_readers import parse_toml_file
from prepare_times_nz.utilities.filepaths import DATA_INTERMEDIATE, DATA_RAW

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
RAW_DATA_LOCATION = Path(DATA_RAW) / "user_config"
OUTPUT_LOCATION = Path(DATA_INTERMEDIATE) / "stage_0_config"

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def list_toml_files(folder_path: Path) -> List[Path]:
    """Return every '*.toml' file inside *folder_path* (recursive)."""
    if not folder_path.is_dir():
        logger.error("The folder '%s' does not exist.", folder_path)
        return []
    return list(folder_path.rglob("*.toml"))


def process_toml_file(toml_path: Path, output_dir: Path) -> pd.DataFrame:
    """Normalise *toml_path*, write it to *output_dir*, and return metadata."""
    toml_normalised = parse_toml_file(toml_path)

    # Write the fully-expanded TOML back out for later stages
    output_file = output_dir / toml_path.name
    with output_file.open("wb") as fp:
        tomli_w.dump(toml_normalised, fp)

    # Extract workbook-level information
    toml_normalised.pop("WorkBookName")

    rows = []
    for table_name, spec in toml_normalised.items():
        data_location = spec.get("DataLocation", toml_path.name)
        rows.append(
            {
                "WorkBookName": spec["WorkBookName"],
                "TableName": table_name,
                "SheetName": spec["SheetName"],
                "VedaTag": f"~{spec['TagName']}",
                "UC_Sets": spec["UCSets"],
                "DataLocation": data_location,
                "Description": spec["Description"],
            }
        )

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Main execution flow
# ---------------------------------------------------------------------------


def main() -> None:
    """Entry-point safe for direct execution or programmatic import."""

    OUTPUT_LOCATION.mkdir(parents=True, exist_ok=True)

    metadata_frames: list[pd.DataFrame] = []

    for toml_file in list_toml_files(RAW_DATA_LOCATION):
        logger.info("Normalising %s", toml_file.name)
        metadata_frames.append(process_toml_file(toml_file, OUTPUT_LOCATION))

    # Combine and write metadata CSV
    if metadata_frames:
        metadata_df = pd.concat(metadata_frames, ignore_index=True)
        metadata_csv = OUTPUT_LOCATION / "config_metadata.csv"
        metadata_df.to_csv(metadata_csv, index=False)
        logger.info("Wrote metadata to %s", metadata_csv)
    else:
        logger.warning("No TOML files found in %s", RAW_DATA_LOCATION)

    # generate documentation
    document()
    logger.info("Generating documentation")


if __name__ == "__main__":
    main()
