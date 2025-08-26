"""
A wrapper to execute all the residential scripts in order 
Each depends on the previous 
"""

import pandas as pd
from prepare_times_nz.stage_2.residential.add_assumptions import main as add_assumptions
from prepare_times_nz.stage_2.residential.common import (
    PREPRO_DF_NAME_STEP4,
    PREPROCESSING_DIR,
    save_output,
)
from prepare_times_nz.stage_2.residential.disaggregate_demand import (
    main as disaggregate_demand,
)
from prepare_times_nz.stage_2.residential.generate_process_names import (
    main as generate_process_names,
)
from prepare_times_nz.stage_2.residential.space_heating_model import (
    main as space_heating_model,
)


def main():
    """Script entrypoint"""

    # 1: space heating model
    space_heating_model()
    # 2: disaggregate other demand, and combine with space heating
    # aggregate per island
    disaggregate_demand()
    # 3: add all assumptions, infer capacity, tidy
    add_assumptions()
    # 4: Generate TIMES process names and definitions for the model
    generate_process_names()
    # 5: take the final output and save it to the output folder for downstream use
    df = pd.read_csv(PREPROCESSING_DIR / PREPRO_DF_NAME_STEP4)
    save_output(df, "residential_baseyear_demand.csv", "residential baseyear demand")


if __name__ == "__main__":
    main()
