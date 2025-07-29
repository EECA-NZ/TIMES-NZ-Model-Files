"""
This script acts as a control file for processing
TIMES-NZ files and creating the excel outputs.

It wipes the data_intermediate and output folders,
and then runs the scripts according to the stage order.

Note that the true configuration of the final outputs
is defined by the toml files in the data_raw/user_config folder.
"""

# libraries
import subprocess
import sys
import time

from prepare_times_nz.filepaths import (
    STAGE_0_SCRIPTS,
    STAGE_1_SCRIPTS,
    STAGE_2_SCRIPTS,
    STAGE_3_SCRIPTS,
    STAGE_4_SCRIPTS,
)
from prepare_times_nz.helpers import clear_data_intermediate, clear_output

# start timer
start_time = time.time()

# clear out the data_intermediate folder and output folder
clear_data_intermediate()
clear_output()


def run_script(script_path):
    """Run a script and print the output."""
    subprocess.run([sys.executable, script_path], check=True)


# Execute TIMES excel file build from raw data
# Stage 0: Settings
print("Reading settings files...")
run_script(f"{STAGE_0_SCRIPTS}/parse_tomls.py")
# Stage 1: Prep raw data
print("Preparing raw data...")
run_script(f"{STAGE_1_SCRIPTS}/extract_eeud.py")
run_script(f"{STAGE_1_SCRIPTS}/extract_ea_data.py")
run_script(f"{STAGE_1_SCRIPTS}/extract_mbie_data.py")
run_script(f"{STAGE_1_SCRIPTS}/extract_snz_data.py")
run_script(f"{STAGE_1_SCRIPTS}/extract_gic_data.py")
run_script(f"{STAGE_1_SCRIPTS}/extract_mvr_fleet_data.py")
run_script(f"{STAGE_1_SCRIPTS}/extract_fleet_vkt_pj_data.py")
run_script(f"{STAGE_1_SCRIPTS}/extract_vkt_tertile_shares.py")
run_script(f"{STAGE_1_SCRIPTS}/extract_vehicle_costs_data.py")
run_script(f"{STAGE_1_SCRIPTS}/extract_vehicle_future_costs_data.py")
# Stage 2: Base Year
print("Compiling base year files...")
run_script(f"{STAGE_2_SCRIPTS}/baseyear_electricity_generation.py")
run_script(f"{STAGE_2_SCRIPTS}/baseyear_industry_demand.py")
run_script(f"{STAGE_2_SCRIPTS}/baseyear_transport_demand.py")
# Stage 3: Scenarios:
run_script(f"{STAGE_3_SCRIPTS}/industry/industry_get_demand_growth.py")
# Stage 4: Create excel files
print("Reshaping data to match Veda formatting...")
run_script(f"{STAGE_4_SCRIPTS}/create_baseyear_elc_files.py")
run_script(f"{STAGE_4_SCRIPTS}/create_baseyear_tra_files.py")
print("Building TIMES excel files based on .toml configuration files...")
run_script(f"{STAGE_4_SCRIPTS}/write_excel.py")


end_time = time.time()
execution_time = end_time - start_time
print("Job complete")
print(f"Preparing TIMES-NZ from raw data took {execution_time:.4f} seconds")
