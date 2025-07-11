

# LIBRARIES -------------------------------------------------------------------------

import sys 
import os 
import pandas as pd 


current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, "../..", "library"))
from data_cleaning import rename_columns_to_pascal
from filepaths import DATA_RAW, STAGE_1_DATA


# Filepaths -------------------------------------------------------------------------
input_location = f"{DATA_RAW}/eeca_data/eeud"
output_location = f"{STAGE_1_DATA}/eeud"
os.makedirs(output_location, exist_ok = True)

eeud_filename = "Final EEUD Outputs 2017 - 2023 12032025.xlsx"



# Get data -------------------------------------------------------------------------

# read 
df = pd.read_excel(f"{input_location}/{eeud_filename}", engine='openpyxl', sheet_name = "Data")

# Process and save ---------------------------------------------------


def clean_eeud_data(df):

    # standard cases
    df = rename_columns_to_pascal(df)
    # add year 
    df["Year"] = df["PeriodEndDate"].dt.year
    # create Value - force not string (and replace with nulls if needed)
    df["Value"] = pd.to_numeric(df["EnergyValue"],errors="coerce")
     # label with unit variable
    df["Unit"] = "TJ"
    # remove old vars
    df = df.drop(["EnergyValue", "PeriodEndDate"], axis = 1)

    return df 

df = clean_eeud_data(df)

df.to_csv(f"{output_location}/eeud.csv", index = False )


