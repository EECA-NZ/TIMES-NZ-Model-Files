"""
This script acts as a control file for processing TIMES-NZ files and creating the excel outputs

It wipes the data_intermediate and output folders, and then runs the scripts according to the stage order. 


"""
# libraries 
import os 
import sys


# get custom libraries/ locations 
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, "..", "library"))
from filepaths import PREP_LOCATION

from helpers import clear_data_intermediate, clear_output

# clear out the data_intermediate folder and output folder
clear_data_intermediate()
clear_output()

# Identify script locations 


STAGE_0_SCRIPTS = f"{PREP_LOCATION}/scripts/stage_0_settings/"
STAGE_1_SCRIPTS = f"{PREP_LOCATION}/scripts/stage_1_prep_raw_data/"
STAGE_2_SCRIPTS = f"{PREP_LOCATION}/scripts/stage_2_baseyear/"
# STAGE 3 SCRIPTS don't exist yet 
STAGE_4_SCRIPTS = f"{PREP_LOCATION}/scripts/stage_4_veda_format/"

# Execute TIMES excel file build from raw data

# Stage 0: Settings 
print(f"Reading settings files...")    
os.system(f"python {STAGE_0_SCRIPTS}/parse_tomls.py")    
# Stage 1: Prep raw data 
print(f"Preparing raw data...")    
os.system(f"python {STAGE_1_SCRIPTS}/extract_ea_data.py")    
os.system(f"python {STAGE_1_SCRIPTS}/extract_mbie_data.py")    
# Stage 2: Base Year 
print(f"Compiling base year files...")    
os.system(f"python {STAGE_2_SCRIPTS}/baseyear_electricity_generation.py")    
# Stage 3: Scenarios:
# no scripts exist yet. 
#Stage 4: Create excel files 
print(f"Building TIMES excel files based on .toml configuration files...")    
os.system(f"python {STAGE_4_SCRIPTS}/write_excel.py")    
print(f"Job complete")
    

