""" TODO: implement an automated TIMES configuration script """

# libraries 
import os 
import sys
from pathlib import Path
import pandas as pd 


# get custom libraries
current_dir = Path(__file__).resolve().parent
sys.path.append(os.path.join(current_dir, "..", "library"))
from helpers import write_workbook
from config import OUTPUT_LOCATION


# TEMPORARY - choosing which files to generated based on what is available in backup folder
# Later once this is all working then we will just do all of them and adjust this logic somewhat 
backup_path = os.path.join(OUTPUT_LOCATION, "manual_file_backups")
backup_path = Path(backup_path)
backup_files = [f.stem for f in backup_path.glob('*.xlsx')]  
backup_files = [s.removeprefix('MANUAL_') for s in backup_files ]

for file in backup_files:    
    # this currently writes to the autogen folder, will not overwrite actual TIMES files 
    # set output location in library/config
    print(file)
    # write_workbook(file)

write_workbook("SuppXLS/Scen_Base_constraints")

