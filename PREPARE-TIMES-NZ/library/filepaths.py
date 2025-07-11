
"""
This file includes configuration directories
This way any scripts can use these without hardcoding, which maintains a bit more flexibility in separate environments
The structure will need to change if this file is moved, as it uses the current location:

PREPARE-TIMES-NZ/library
"""
import os 

# main directories
PREP_LIBRARY_LOCATION = os.path.dirname(os.path.abspath(__file__))
PREP_LOCATION = os.path.dirname(PREP_LIBRARY_LOCATION)
TIMES_LOCATION = os.path.dirname(PREP_LOCATION)


# data locations
# NOTE: OUTPUT_LOCATION is the directory for the final excel files. 
# It is regularly wiped and replaced with new files, so do not adjust this to the TIMES-NZ module without being careful
OUTPUT_LOCATION = os.path.join(PREP_LOCATION, "output") 
# DATA_INTERMEDIATE is gitignored and regularly wiped. It acts as a staging area but nothing should be stored here permanently.
DATA_INTERMEDIATE = os.path.join(PREP_LOCATION, "data_intermediate")
DATA_RAW = os.path.join(PREP_LOCATION, "data_raw")


# data raw subfolders
ASSUMPTIONS = os.path.join(DATA_RAW, "coded_assumptions")
CONCORDANCES = os.path.join(DATA_RAW, "concordances")


# data intermediate stages
STAGE_1_DATA = os.path.join(DATA_INTERMEDIATE, "stage_1_input_data")
STAGE_2_DATA = os.path.join(DATA_INTERMEDIATE, "stage_2_baseyear_data")
STAGE_3_DATA = os.path.join(DATA_INTERMEDIATE, "stage_3_scenario_data")
STAGE_4_DATA = os.path.join(DATA_INTERMEDIATE, "stage_4_veda_format")

# scripts 
STAGE_0_SCRIPTS = f"{PREP_LOCATION}/scripts/stage_0_settings"
STAGE_1_SCRIPTS = f"{PREP_LOCATION}/scripts/stage_1_prep_raw_data"
STAGE_2_SCRIPTS = f"{PREP_LOCATION}/scripts/stage_2_baseyear"
STAGE_3_SCRIPTS = f"{PREP_LOCATION}/scripts/stage_3_scenarios"
STAGE_4_SCRIPTS = f"{PREP_LOCATION}/scripts/stage_4_veda_format"



