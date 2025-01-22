""" TODO: implement an automated TIMES configuration script """

# libraries 
import os 
import sys
from pathlib import Path
import pandas as pd 

# niche libraries (might not need these later!)
from openpyxl.utils import get_column_letter
from openpyxl import Workbook

# get custom libraries
current_dir = Path(__file__).resolve().parent
sys.path.append(os.path.join(current_dir, "..", "library"))
from helpers import write_workbook


# TEMPORARY - choosing which files to generated based on what is available in backup folder 

backup_path = "C:/Users/SearleL/Repos/TIMES-NZ-Model-Files/TIMES-NZ/Manual Files for TIMES 2"
backup_path = Path(backup_path)
backup_files = [f.stem for f in backup_path.glob('*.xlsx')]  

for file in backup_files:    
    # this currently writes to the autogen folder, will not overwrite actual TIMES files 
    # set output location in library/config
    write_workbook(file)
