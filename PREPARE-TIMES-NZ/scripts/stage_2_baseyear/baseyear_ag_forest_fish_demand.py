"""
A wrapper to execute all the ag, forest, fish scripts in order.
Each depends on the previous
"""

import pandas as pd
from prepare_times_nz.stage_2.ag_forest_fish.add_assumptions import (
    main as add_assumptions,
)
from prepare_times_nz.stage_2.ag_forest_fish.align_eeud_sectors import (
    main as align_eeud_sectors,
)
from prepare_times_nz.stage_2.ag_forest_fish.common import (
    PREPRO_DF_NAME_STEP4,
    PREPROCESSING_DIR,
    save_output,
)
from prepare_times_nz.stage_2.ag_forest_fish.define_process_commodities import (
    main as generate_process_names,
)
from prepare_times_nz.stage_2.ag_forest_fish.disaggregate_regions import (
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
    save_output(
        df, "baseyear_ag_forest_fish_demand.csv", "baseyear ag, forest, fish demand"
    )


if __name__ == "__main__":
    main()
