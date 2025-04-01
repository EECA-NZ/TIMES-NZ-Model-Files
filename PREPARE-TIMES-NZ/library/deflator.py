import sys 
import os 
#from openpyxl import Workbook, load_workbook
# from ast import literal_eval
import pandas as pd 
# import string
import shutil 
import logging


from filepaths import DATA_INTERMEDIATE

# helper data for these functions

cpi_df = pd.read_csv(f"{DATA_INTERMEDIATE}/stage_1_external_data/statsnz/cpi.csv") # this is the deflator data

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
        logging.info(f"Current year ({current_year}) is the same as base year ({base_year}). No deflation needed.")
        return current_value
    
    else: 
        # Get the CPI index for the current year and base year
        cpi_current = cpi_df.loc[cpi_df['Year'] == current_year, 'CPI_Index'].values[0]
        cpi_base = cpi_df.loc[cpi_df['Year'] == base_year, 'CPI_Index'].values[0]

        # Calculate the deflated value
        deflated_value = current_value * (cpi_base / cpi_current)

        return deflated_value
    