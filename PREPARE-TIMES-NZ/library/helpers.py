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




def select_and_rename(df, name_map):
    """
    Selects and renames columns in a DataFrame based on a provided mapping.
    
    Parameters:
    - df: The input DataFrame.
    - name_map: A dictionary where keys are the original column names and values are the new column names.
    
    Returns:
    - A DataFrame with selected and renamed columns.
    """
    # Select columns based on the mapping
    selected_df = df[list(name_map.keys())].copy()
    
    # Rename columns
    selected_df.rename(columns=name_map, inplace=True)
    
    return selected_df




# Some tests 


def check_table_grain(df, grain_list):
    """
    Check the grain of a DataFrame against a list of expected grains.
    
    Parameters:
    - df: The input DataFrame.
    - grain_list: A list of column names that should uniquely identify the rows in the Dataframe.
    
    Returns:
    - A boolean indicating whether the provided column names uniquely identify rows in the DataFrame.
    """
    return df.duplicated(subset=grain_list).sum() == 0


def test_table_grain(df, grain_list):

    """
    A wrapper and logging output for check_table_grain

    Parameters:
    - df: The input DataFrame.
    - grain_list: A list of column names that should uniquely identify the rows in the Dataframe.

    Outputs: logging information regarding the results of the test.
    
    """

    if(check_table_grain(df, grain_list)):
        logging.info(f"Success: rows are uniquely identified using the following variables:") 
        for var in grain_list:
            logging.info(f" - {var}")

    else: 
        logging.warning(f"Rows are NOT uniquely identified using the following variables - please review!") 
        for var in grain_list:
            logging.info(f" - {var}")