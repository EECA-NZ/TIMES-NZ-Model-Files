"""
Pulling/cleaning data from Stats NZ. Currently just CPI, which can be used to create a deflator function

"""
#######################################################################
#region LIBRARIES
#######################################################################
import os

import pandas as pd
from prepare_times_nz.filepaths import DATA_RAW, STAGE_1_DATA

#endregion
#######################################################################
#region FILEPATHS
#######################################################################
input_location = f"{DATA_RAW}/external_data/statsnz"
output_location = f"{STAGE_1_DATA}/statsnz"
os.makedirs(output_location, exist_ok = True)

# all file locations:
snz_cpi_file = f"{input_location}/cpi/cpi_infoshare.csv"

#endregion
#######################################################################
#region CPI
#######################################################################

# Load
cpi_df = pd.read_csv(snz_cpi_file, skiprows = 1) # skipping title row

# removing rows with no data (these are descriptive rows)
cpi_df = cpi_df[cpi_df["All groups"].notna()]
# renaming columns
cpi_df.columns = ["Period", "CPI_Index"]

# create year and quarter variables
cpi_df['Year'] = cpi_df['Period'].str[:4].astype(int)
cpi_df['Quarter'] = cpi_df['Period'].str[-1].astype(int)

# can remove a lot of ancient data
cpi_df = cpi_df[cpi_df["Year"] >= 1990] # removing data before 1990
# we are only creating annual indices, so we take Q4 for annual changes
cpi_df = cpi_df[cpi_df["Quarter"] == 4]

# take only needed columns
cpi_df  = cpi_df[["Year", "CPI_Index"]]

# save
cpi_df.to_csv(f"{output_location}/cpi.csv", index = False)

#endregion




