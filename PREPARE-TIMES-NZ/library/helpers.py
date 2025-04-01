import sys 
import os 
#from openpyxl import Workbook, load_workbook
# from ast import literal_eval
import pandas as pd 
# import string
import shutil 
import logging



# get custom locations
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, "..", "library"))
from filepaths import DATA_INTERMEDIATE, OUTPUT_LOCATION

# helper data for these functions

cpi_df = pd.read_csv(f"{DATA_INTERMEDIATE}/stage_1_external_data/statsnz/cpi.csv") # this is the deflator data


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


# Some data manipulation functions 

def deflate_data(current_year, base_year, current_value):
    """
    Deflate the current value to the base year using the CPI index.
    
    Parameters:
    - current_year: The year of the current value.
    - base_year: The year to deflate to.    
    - current_value: The value to deflate 
    
    Returns:
    - deflated_value: The deflated value.

    This function relies on cpi_df, which should be loaded in the script. It contains the CPI index for each year.
    """

    if current_year == base_year:
        return current_value
    
    else: 
        # Get the CPI index for the current year and base year
        cpi_current = cpi_df.loc[cpi_df['Year'] == current_year, 'CPI_Index'].values[0]
        cpi_base = cpi_df.loc[cpi_df['Year'] == base_year, 'CPI_Index'].values[0]

        # Calculate the deflated value
        deflated_value = current_value * (cpi_base / cpi_current)
                
        return deflated_value



