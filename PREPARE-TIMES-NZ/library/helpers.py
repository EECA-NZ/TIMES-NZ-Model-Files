import sys 
import os 
from openpyxl import Workbook, load_workbook
from ast import literal_eval
import pandas as pd 
import string
import shutil 
import logging



# get custom locations
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, "..", "library"))
from filepaths import DATA_INTERMEDIATE, OUTPUT_LOCATION


def clear_data_intermediate():
    # Delete folder
    if os.path.exists(DATA_INTERMEDIATE):
        logging.debug(f"DATA_INTERMEDIATE = {DATA_INTERMEDIATE}")        
        shutil.rmtree(DATA_INTERMEDIATE)
    # and make fresh 
    os.makedirs(DATA_INTERMEDIATE)


def clear_output():
    # Delete folder
    if os.path.exists(OUTPUT_LOCATION):
        logging.debug(f"OUTPUT_LOCATION = {OUTPUT_LOCATION}")        
        shutil.rmtree(OUTPUT_LOCATION)
    # and make fresh 
    os.makedirs(OUTPUT_LOCATION)



