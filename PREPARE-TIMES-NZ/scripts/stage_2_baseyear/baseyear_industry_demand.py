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

import pandas as pd
from prepare_times_nz.stage_2.industry.common import (
    PREPRO_DF_NAME_STEP4,
    PREPROCESSING_DIR,
    save_output,
)
from prepare_times_nz.stage_2.industry.industry_add_assumptions import (
    main as add_assumptions,
)
from prepare_times_nz.stage_2.industry.industry_align_eeud_sectors import (
    main as align_eeud_sectors,
)
from prepare_times_nz.stage_2.industry.industry_define_process_commodities import (
    main as generate_process_names,
)
from prepare_times_nz.stage_2.industry.industry_disaggregate_regions import (
    main as disaggregate_demand,
)


# pylint: disable=duplicate-code
def main():
    """Script entrypoint"""

    # 1: align eeud sectors and make other adjustments
    align_eeud_sectors()
    # 2: disaggregate demand - aggregate per island
    disaggregate_demand()
    # 3: add all assumptions, infer capacity, tidy
    add_assumptions()
    # 4: Generate TIMES process names and definitions for the model
    generate_process_names()
    # 5: take the final output and save it to the output folder for downstream use
    df = pd.read_csv(PREPROCESSING_DIR / PREPRO_DF_NAME_STEP4)
    save_output(df, "baseyear_industry_demand.csv", "baseyear industry demand")


if __name__ == "__main__":
    main()
