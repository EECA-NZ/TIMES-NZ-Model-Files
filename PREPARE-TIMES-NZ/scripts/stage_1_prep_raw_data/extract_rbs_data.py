"""
This script takes the residential baseline study data
and simply copies it to the staging area

Note that the RBS data has already been extracted from the raw input file

Found here:
https://www.energyrating.gov.au/sites/default/files/2022-12/power_demand_by_time_of_use_data.xlsx

We extracted the full data then compressed to parquet
This avoids dumping 40MB into the repo

"""

# LIBRARIES -------------------------------------
import pandas as pd
from prepare_times_nz.filepaths import DATA_RAW, STAGE_1_DATA
from prepare_times_nz.logger_setup import logger

# CONSTANTS -------------------------------------
SAVE_CSV = False
# LOCATIONS -------------------------------------

OUTPUT_LOCATION = STAGE_1_DATA / "res_baseline"
INPUT_LOCATION = DATA_RAW / "external_data/res_baseline_study"

INPUT_FILE = INPUT_LOCATION / "power_demand_by_time_of_use_data.parquet"
OUTPUT_FILE = OUTPUT_LOCATION / "power_demand_by_time_of_use_data.parquet"

# FUNCTIONS -------------------------------------


def main():
    """Moves RBS data to staging dir"""
    OUTPUT_LOCATION.mkdir(parents=True, exist_ok=True)
    df = pd.read_parquet(INPUT_FILE)
    logger.info("Saving RBS data to %s", OUTPUT_FILE)
    df.to_parquet(OUTPUT_FILE, index=False)


if __name__ == "__main__":
    main()
