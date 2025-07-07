

# LIBRARIES -------------------------------------------------------------------------

import sys 
import os 
import polars as pl # we're trying polars in this script instead of pandas
# import pandas as pd 


current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, "../..", "library"))
from data_cleaning import rename_columns_to_pascal
from filepaths import DATA_RAW, STAGE_1_DATA


# FILEPATHS -------------------------------------------------------------------------
input_location = f"{DATA_RAW}/eeca_data/eeud"
output_location = f"{STAGE_1_DATA}/eeud"
os.makedirs(output_location, exist_ok = True)

eeud_filename = "Final EEUD Outputs 2017 - 2023 12032025.xlsx"



# MAKE TABLE -------------------------------------------------------------------------

# read 
df = pl.read_excel(f"{input_location}/{eeud_filename}", engine='openpyxl', sheet_name = "Data")
# clean up the column names
eeud_df = rename_columns_to_pascal(df)

# process 

eeud_df = (eeud_df 
           .with_columns(pl.col("PeriodEndDate").dt.year().alias("Year"))           
           # label with unit variable 
           .with_columns(pl.lit("TJ").alias("Unit"))
           # value should not be string 
           .with_columns(pl.col("EnergyValue").cast(pl.Float64, strict = False).alias("Value"))
           # remove older columns we've transformed 
           .drop(["EnergyValue", "PeriodEndDate"])
           )

eeud_df.write_csv(f"{output_location}/eeud.csv")