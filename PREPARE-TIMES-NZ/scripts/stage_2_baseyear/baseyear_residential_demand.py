"""
A wrapper to execute all the residential scripts
"""

import pandas as pd
from prepare_times_nz.stage_2.residential.create_residential_assumptions import (
    main as create_assumptions,
)
from prepare_times_nz.stage_2.residential.disaggregate_residential_demand import (
    main as disaggregate_demand,
)
from prepare_times_nz.stage_2.residential.generate_residential_processes import (
    main as generate_processes,
)
from prepare_times_nz.utilities.filepaths import STAGE_2_DATA

RESIDENTIAL_DATA = STAGE_2_DATA / "residential"

if __name__ == "__main__":

    disaggregate_demand()
    create_assumptions(
        input_file=RESIDENTIAL_DATA / "residential_demand_by_island.csv",
        output_file=RESIDENTIAL_DATA / "residential_demand_with_assumptions.csv",
    )
    generate_processes(
        input_file=RESIDENTIAL_DATA / "residential_demand_with_assumptions.csv",
        output_file=RESIDENTIAL_DATA / "residential_demand_processes.csv",
    )

    # save the final output as baseyear data
    residential_baseyear_data = pd.read_csv(
        RESIDENTIAL_DATA / "residential_demand_processes.csv"
    )
    residential_baseyear_data.to_csv(
        RESIDENTIAL_DATA / "residential_baseyear_demand.csv", index=False
    )
