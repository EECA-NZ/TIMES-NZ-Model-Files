"""
Run base-year industry demand preprocessing steps and assemble the final dataset.

This script performs:
  1. Align EEUD and TIMES industrial sector categories.
  2. Calculate regional disaggregations based on input assumptions.
  3. Add technical parameters by assumption.
  4. Define processes and commodities.
  5. Copy the fully preprocessed output into baseyear_industry_demand.csv.

This script is idempotent: re-running will overwrite previous outputs.
"""

import subprocess
import sys
from pathlib import Path

import pandas as pd
from prepare_times_nz.utilities.filepaths import STAGE_2_DATA, STAGE_2_SCRIPTS
from prepare_times_nz.utilities.logger_setup import h1

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
INDUSTRY_SCRIPTS_DIR = Path(STAGE_2_SCRIPTS) / "industry"
PREPROCESS_INPUT = (
    Path(STAGE_2_DATA)
    / "industry"
    / "preprocessing"
    / "4_times_baseyear_with_commodity_definitions.csv"
)
OUTPUT_FILE = Path(STAGE_2_DATA) / "industry" / "baseyear_industry_demand.csv"

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def run_script(script_path: Path) -> None:
    """Run a script at *script_path* using the current Python interpreter."""
    subprocess.run([sys.executable, str(script_path)], check=True)


def run_all_preprocessing() -> None:
    """Execute the industry preprocessing scripts in the required sequence."""
    steps = [
        (
            "Aligning EEUD and TIMES industrial sector categories",
            "industry_align_eeud_sectors.py",
        ),
        (
            "Calculating regional disaggregations based on input assumptions",
            "industry_disaggregate_regions.py",
        ),
        ("Adding technical parameters by assumption", "industry_add_assumptions.py"),
        (
            "Defining processes and commodities",
            "industry_define_process_commodities.py",
        ),
    ]
    for message, script_name in steps:
        h1(message)
        script_path = INDUSTRY_SCRIPTS_DIR / script_name
        run_script(script_path)


def assemble_final_output() -> None:
    """Copy the final preprocessed CSV into the main base-year industry demand file."""
    df = pd.read_csv(PREPROCESS_INPUT)
    df.to_csv(OUTPUT_FILE, index=False)
    h1(f"Wrote final base-year industry demand to {OUTPUT_FILE}")


def main() -> None:
    """Main entry point."""
    run_all_preprocessing()
    assemble_final_output()


if __name__ == "__main__":
    main()
