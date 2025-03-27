"""
This script acts as a control file for processing TIMES-NZ files and creating the excel outputs

"""
# libraries 
import os 
import sys
import shutil



# get custom libraries/ locations 
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, "..", "library"))
from filepaths import PREP_LOCATION, DATA_INTERMEDIATE, OUTPUT_LOCATION

# NOTE: here `INPUT_LOCATION` refers to the intermediate files that will be created in data_intermediate

# file locations 
table_location = os.path.join(PREP_LOCATION, "data_raw", "archive") # archived summary table, won't update with new loads  
file_location = f"{table_location}/raw_tables.txt"


# Clear out DATA_INTERMEDIATE for fresh start 

if os.path.exists(DATA_INTERMEDIATE):
    print(f"DATA_INTERMEDIATE = {DATA_INTERMEDIATE}")
    shutil.rmtree(DATA_INTERMEDIATE)
# and make fresh 
os.makedirs(DATA_INTERMEDIATE)


# Set method 

# method options are 'times_2' (recreates times 2 based on the summary table)
# or 'times_3' (builds the new times model from source files) (currently very barebones implementation)

method = "times_3" 


# Execute 

if method == "times_2":
    print(f"Reading the archived summary data")
    os.system(f"python {PREP_LOCATION}/scripts/times_2_methods/read_archive_summary.py")
    print(f"Creating TIMES excel files in {OUTPUT_LOCATION}")
    os.system(f"python {PREP_LOCATION}/scripts/times_2_methods/prepare_times_nz_from_archive.py")
    
    

if method == "times_3":
    print(f"Building TIMES excel files based on .toml configuration files...")    
    os.system(f"python {PREP_LOCATION}/scripts/stage_4_veda_format/write_excel.py")    
    print(f"Job complete")
    

