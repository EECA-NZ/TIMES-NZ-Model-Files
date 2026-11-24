"""
Ag, forest, and fish demand — Islandal (NI/SI) disaggregation using THREE inputs:

1) STAGE_2_DATA/ag_forest_fish/preprocessing/1_times_eeud_alignment_baseyear.csv
   Required cols: Sector, Fuel, Unit, Value, [TechnologyGroup],
   [Technology], [EndUse], [EnduseGroup]

2) ASSUMPTIONS/ag_forest_fish_demand/regional_splits.csv
   Required cols: Sector, Fuel, Technology, NI_Share   (sector default NI share in [0,1])

Outputs:
- STAGE_2_DATA/ag_forest_fish/preprocessing/2_ag_forest_fish_regional_demand_split.csv
- STAGE_2_DATA/ag_forest_fish/checks/2_Regional_disaggregation/ag_forest_fish_fuel_sector_shares.csv
"""

from pathlib import Path

import pandas as pd

from prepare_times_nz.stage_2.ag_forest_fish.common import PREPRO_DF_NAME_STEP2
from prepare_times_nz.stage_2.common.disaggregate_regions import (
    calculate_generic_regional_splits,
    create_fuel_sector_checks,
)
from prepare_times_nz.utilities.data_in_out import _save_data
from prepare_times_nz.utilities.filepaths import ASSUMPTIONS, STAGE_2_DATA

# -----------------------------------------------------------------------------
# Locations
# -----------------------------------------------------------------------------
OUTPUT_DIR = Path(STAGE_2_DATA) / "ag_forest_fish" / "preprocessing"
CHECKS_DIR = (
    Path(STAGE_2_DATA) / "ag_forest_fish" / "checks" / "2_Regional_disaggregation"
)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
CHECKS_DIR.mkdir(parents=True, exist_ok=True)

BASEYEAR_CSV = OUTPUT_DIR / "1_times_eeud_alignment_baseyear.csv"
SPLITS_CSV = Path(ASSUMPTIONS) / "ag_forest_fish_demand" / "regional_splits.csv"


# -----------------------------------------------------------------------------
# Load inputs
# -----------------------------------------------------------------------------
def load_inputs() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load data"""
    baseyear = pd.read_csv(BASEYEAR_CSV)
    sector = pd.read_csv(SPLITS_CSV)
    return baseyear, sector


def main() -> None:
    """Load inputs, calculate regional demand, and save outputs and checks."""
    baseyear, sector_splits = load_inputs()
    ag_forest_fish_regional_demand_split = calculate_generic_regional_splits(
        baseyear, sector_splits
    )

    _save_data(
        ag_forest_fish_regional_demand_split,
        PREPRO_DF_NAME_STEP2,
        "Saving output",
        OUTPUT_DIR,
    )
    shares = create_fuel_sector_checks(ag_forest_fish_regional_demand_split)
    _save_data(
        shares,
        "ag_forest_fish_fuel_sector_shares.csv",
        "fuel × sector NI shares",
        CHECKS_DIR,
    )


if __name__ == "__main__":
    main()
