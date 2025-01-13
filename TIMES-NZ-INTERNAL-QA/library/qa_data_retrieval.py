# data retrival functions 

import pandas as pd
import re
import os


# configuration variables
from config import TIMES_LOCATION, TIMES_OUTPUTS_RAW, qa_runs


def read_vd(filepath):
    """
    Reads a VD file, using column names extracted from the file's
    header with regex, skipping non-CSV formatted header lines.

    :param filepath: Path to the VD file.
    :param scen_label: Label for the 'scen' column for rows from this file.
    """
    dimensions_pattern = re.compile(r"\*\s*Dimensions-")

    # Determine the number of rows to skip and the column names
    with open(filepath, "r", encoding="utf-8") as file:
        columns = None
        skiprows = 0
        for line in file:
            if dimensions_pattern.search(line):
                columns_line = line.split("- ")[1].strip()
                columns = columns_line.split(";")
                continue
            if line.startswith('"'):
                break
            skiprows += 1

    # Read the CSV file with the determined column names and skiprows
    vd_df = pd.read_csv(
        filepath, skiprows=skiprows, names=columns, header=None, low_memory=False
    )
    return vd_df


def get_attribute_df_single_run(attribute, run_name): 
    """
    Reads a TIMES vd file and returns a dataframe filtered to a specific attribute 
    
    Parameters:
    attribute (str): Attribute from a TIMES vd file to filter on 
    run_name (str): The name of the run this file is from. This must exist in the specified df
    
    Returns:
    Dataframe - untouched vd output but on a specific attribute and with a run label 
    """

    filepath = os.path.join(TIMES_OUTPUTS_RAW, run_name, f"{run_name}.vd")
    vd = read_vd(filepath)
    vd = vd[vd["Attribute"] == attribute]
    vd["Scenario"] = run_name
    return vd
    
def add_concordance_to_vd(df):
    """
    Takes a TIMES VD file with Attribute/Process/Commodity data, and adds the local concordance file to it 
    Hardcodes the concordance file location, which must exist
    
    Parameters:
    df (str): the pandas dataframe we're adding the concordance to   

    Returns:
    a df with the new variables attached
    """

    concordance_filepath = os.path.join(TIMES_LOCATION,
                                        "TIMES-NZ-OUTPUT-PROCESSING/data/input/concordance/",
                                        "attribute_process_commodity_concordance.csv")
    
    concordance_data = pd.read_csv(concordance_filepath)

    df = df.merge(concordance_data,
                  how = "left",
                  on = ["Attribute", "Process", "Commodity"])
    return df

    

def get_veda_data_no_concordance(attribute, runs = qa_runs):
    """
    Combines previous functions to get the same attribute data for all relevant runs
    then attach the concordance file for easy perusal. 
    
    Parameters:
    attribute (str): the VD attribute this pulls
    runs (array): an array of run names stored as strings. Defaults to the `qa_runs` defined earlier 

    Returns:
    a df 
    """
    
    # actual function
    
    df = pd.DataFrame()

    for run in runs: 
        vd_df = get_attribute_df_single_run(attribute, run)
        df = pd.concat([df, vd_df])    

    return df


def get_veda_data(attribute, runs = qa_runs):    
    
    df = get_veda_data_no_concordance(attribute, runs)
    df = add_concordance_to_vd(df)

    return df 