import subprocess
import sys

import pandas as pd
from prepare_times_nz.filepaths import STAGE_2_DATA, STAGE_2_SCRIPTS
from prepare_times_nz.logger_setup import h1

# This just runs all the base year industry scripts in the required sequence
INDUSTRY_SCRIPTS = f"{STAGE_2_SCRIPTS}/industry"


def run_script(script_path):
    """Run a script and print the output."""
    subprocess.run([sys.executable, script_path], check=True)


# execute scripts in order
h1("Aligning EEUD and TIMES industrial sector categories")
run_script(f"{INDUSTRY_SCRIPTS}/industry_align_eeud_sectors.py")
h1("Calculating regional disaggregations based on input assumptions")
run_script(f"{INDUSTRY_SCRIPTS}/industry_disaggregate_regions.py")
h1("Adding technical parameters by assumption")
run_script(f"{INDUSTRY_SCRIPTS}/industry_add_assumptions.py")
h1("Defining process and commodities")
run_script(f"{INDUSTRY_SCRIPTS}/industry_define_process_commodities.py")

# copy the final output of preprocessing into the main workflow

df = pd.read_csv(
    f"{STAGE_2_DATA}/industry/preprocessing/4_times_baseyear_with_commodity_definitions.csv"
)
df.to_csv(f"{STAGE_2_DATA}/industry/baseyear_industry_demand.csv", index=False)
