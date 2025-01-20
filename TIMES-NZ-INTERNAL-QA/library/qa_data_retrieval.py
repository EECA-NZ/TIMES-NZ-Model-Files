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


def get_concordance_file():
    concordance_filepath = os.path.join(TIMES_LOCATION,
                                        "TIMES-NZ-OUTPUT-PROCESSING/data/input/concordance/",
                                        "attribute_process_commodity_concordance.csv")    
    df = pd.read_csv(concordance_filepath)
    return df

    
def add_concordance_to_vd(df):
    """
    Takes a TIMES VD file with Attribute/Process/Commodity data, and adds the local concordance file to it 
    Hardcodes the concordance file location, which must exist
    
    Parameters:
    df (str): the pandas dataframe we're adding the concordance to   

    Returns:
    a df with the new variables attached
    """
    concordance_data = get_concordance_file()
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

def get_all_veda_attributes(runs = qa_runs):

    attributes = ["VAR_FIn", "VAR_Cap", "VAR_FOut"]

    df = pd.DataFrame()    
    for run in runs:
        filepath = os.path.join(TIMES_OUTPUTS_RAW, run, f"{run}.vd")
        vd = read_vd(filepath)
        vd = vd[vd["Attribute"].isin(attributes)]
        vd["Scenario"] = run
        df = pd.concat([df, vd])        


    # rename the original df commodities as negco2 where they are currently tot, but the value is negative
    neg_c02_rows = df[(df["Commodity"] == "TOTCO2") & (df.PV < 0)]
    df.loc[neg_c02_rows.index, "Commodity"] = "NEGCO2"
    # this is just so they get added to the concordance properly and so the parameters work. 
    # We won't be doing any actual data manipulation though

    
    df = add_concordance_to_vd(df)

    # after adding concordance, we replace nulls with this "missing" string.
    # This could go elsewhere 
    string_columns = df.select_dtypes(include=['object']).columns
    string_columns = [col for col in string_columns if col != 'PV']
    # Replace NaN with "Missing" in those columns    
    df[string_columns] = df[string_columns].fillna('Missing')

    return df

# for filling in the periods

def complete_periods(df, period_list, category_cols=None, value_col = "PV"):
    """
    Fill in missing periods with explicit zero values for each category combination.
    
    Parameters:
    -----------
    df : pandas.DataFrame
        Input dataframe containing Period, PV (Value), and optional category columns
    period_list : list
        Complete list of all possible periods
    category_cols : list or None
        List of category column names to group by. If None, just completes periods globally
        
    Returns:
    --------
    pandas.DataFrame
        Complete dataframe with explicit zero values for missing periods
    """
    # Create a dataframe from the complete period list
    periods_df = pd.DataFrame({'Period': period_list})
    
    if category_cols:
        # Get unique combinations of category values
        categories = df[category_cols].drop_duplicates()
        
        # Create a cross product of periods with all category combinations
        template = periods_df.merge(categories, how='cross')
        
        # Merge with original data, filling missing values with 0
        result = template.merge(
            df,
            on=['Period'] + category_cols,
            how='left'
        )
    else:
        # If no categories, just merge periods with original data
        result = periods_df.merge(
            df,
            on='Period',
            how='left'
        )
    
    # Fill missing PV values with 0
    result[value_col] = result[value_col].fillna(0)   

    
    return result

