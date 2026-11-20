"""
Commercial demand — Islandal (NI/SI) disaggregation using THREE inputs:

1) STAGE_2_DATA/commercial/preprocessing/1_times_eeud_alignment_baseyear.csv
   Required cols: Sector, Fuel, Unit, Value, [TechnologyGroup],
   [Technology], [EndUse], [EnduseGroup]

2) ASSUMPTIONS/commercial_demand/Islandal_splits_by_sector.csv
   Required cols: Sector, NI_Share   (sector default NI share in [0,1])

3) ASSUMPTIONS/commercial_demand/Islandal_splits_by_fuel.csv
   Required cols: Fuel, NI_Share     (override in [0,1])
   Optional:     Sector              (if present, overrides apply to (Sector, Fuel), else Fuel-only)

Rules:
- Prefer fuel override when present (e.g., Natural Gas / Geothermal = 1.0 → all NI).
- Otherwise use the sector default.
- NI = Value * NIShare ;  SI = Value - NI
- Output: long table with Island ∈ {NI, SI}

Outputs:
- STAGE_2_DATA/commercial/preprocessing/2_commercial_regional_demand_split.csv
- STAGE_2_DATA/commercial/checks/2_Island_disaggregation/commercial_fuel_sector_shares.csv
"""

from pathlib import Path

import pandas as pd

from prepare_times_nz.stage_2.commercial.common import PREPRO_DF_NAME_STEP2
from prepare_times_nz.stage_2.common.disaggregate_regions import (
    calculate_generic_regional_splits,
    create_fuel_sector_checks,
)
from prepare_times_nz.utilities.data_in_out import _save_data
from prepare_times_nz.utilities.filepaths import ASSUMPTIONS, STAGE_2_DATA

# -----------------------------------------------------------------------------
# Locations
# -----------------------------------------------------------------------------
OUTPUT_DIR = Path(STAGE_2_DATA) / "commercial" / "preprocessing"
CHECKS_DIR = Path(STAGE_2_DATA) / "commercial" / "checks" / "2_Island_disaggregation"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
CHECKS_DIR.mkdir(parents=True, exist_ok=True)

BASEYEAR_CSV = OUTPUT_DIR / "1_times_eeud_alignment_baseyear.csv"
SECTOR_SPLITS_CSV = (
    Path(ASSUMPTIONS) / "commercial_demand" / "regional_splits_by_sector.csv"
)
FUEL_OVERRIDES_CSV = (
    Path(ASSUMPTIONS) / "commercial_demand" / "regional_splits_by_fuel.csv"
)


# -----------------------------------------------------------------------------
# Load inputs
# -----------------------------------------------------------------------------
def load_inputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load data"""
    baseyear = pd.read_csv(BASEYEAR_CSV)
    sector = pd.read_csv(SECTOR_SPLITS_CSV)
    fuel = pd.read_csv(FUEL_OVERRIDES_CSV)
    return baseyear, sector, fuel


def main() -> None:
    """Load inputs, calculate regional demand, and save outputs and checks."""
    baseyear, sector_splits, fuel_overrides = load_inputs()
    commercial_regional_demand_split = calculate_generic_regional_splits(
        baseyear, sector_splits, fuel_overrides
    )

    _save_data(
        commercial_regional_demand_split,
        PREPRO_DF_NAME_STEP2,
        "Saving output",
        OUTPUT_DIR,
    )
    shares = create_fuel_sector_checks(commercial_regional_demand_split)
    _save_data(
        shares,
        "commercial_fuel_sector_shares.csv",
        "fuel × sector NI shares",
        CHECKS_DIR,
    )


if __name__ == "__main__":
    main()
