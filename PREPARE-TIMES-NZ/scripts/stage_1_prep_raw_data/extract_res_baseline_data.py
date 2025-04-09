# Here we find the mbie excel files and create data_intermediate/stage_1_external_data/res_baseline/*
# this will include any edgs assumptions we want to use and any official figures we want 
# We also do some tidying/standardising here

#region LIBRARIES 

import sys 
import os 
import pandas as pd 
import glob 

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, "../..", "library"))
from filepaths import DATA_RAW, DATA_INTERMEDIATE
from helpers import clear_data_intermediate


#clear_data_intermediate()
#endregion

#region FILEPATHS
input_location = f"{DATA_RAW}/external_data/res_baseline_study"
output_location = f"{DATA_INTERMEDIATE}/stage_1_external_data/res_baseline"
os.makedirs(output_location, exist_ok = True)

res_baseline = f"{input_location}/power_demand_by_time_of_use_data.xlsx"

#endregion


#region EXTRACTING DATA
def get_edgs_assumptions(SheetName):
    df = pd.read_excel(res_baseline, sheet_name=SheetName)
    return df 
# save
get_edgs_assumptions("Demand.Data").to_csv(f"{output_location}/res_baseline_data.csv", index=False)
#endregion