# Here we find the EAexcel files and create data_intermediate/stage_1_external_data/electricity_authority/*
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

#endregion

#region FILEPATHS
input_location = f"{DATA_RAW}/external_data/electricity_authority"
output_location = f"{DATA_INTERMEDIATE}/stage_1_external_data/electricity_authority"
os.makedirs(output_location, exist_ok = True)

# all file locations: 

emi_md_folder = f"{input_location}/emi_md" # we'll take everything in this directory
emi_fleet_file = f"{input_location}/emi_fleet_data/20230601_DispatchedGenerationPlant.csv"
emi_nsp_table = f"{input_location}/emi_nsp_table/20250308_NetworkSupplyPointsTable.csv"
emi_distributed_solar_directory = f"{input_location}/emi_distributed_solar"

#endregion


#region MD_Generation 


emi_md_files = glob.glob(os.path.join(emi_md_folder, "*.csv"))

md_dfframes = []
for file in emi_md_files:
    print(f"Reading from {file}")
    df = pd.read_csv(file)
    md_dfframes.append(df)
    
md_df  = pd.concat(md_dfframes, ignore_index=True)

trading_period_vars = [col for col in md_df.columns if col.startswith("TP")]

md_df = pd.melt(
    md_df, 
    id_vars = md_df.columns.difference(trading_period_vars),
    value_vars = trading_period_vars,
    var_name = "Trading_Period",
    value_name = "Value"
)
# saving as parquet because these files are huge 
md_df.to_parquet(f"{output_location}/emi_md.parquet", engine = "pyarrow")

#endregion 



#region DISTRIBUTED_SOLAR

#to do: replace manual website download process.

# These files are from https://www.emi.ea.govt.nz/Retail/Reports/GUEHMT as per readme.txt in the folder 


def read_solar_file(sector):

    filename = f"solar_{sector.lower()}.csv"

    print(f"Reading {sector} solar data...")

    df = pd.read_csv(f"{emi_distributed_solar_directory}/{filename}", skiprows = 12)
    df["Sector"] = sector
    return df 

# read and combine



solar_df = pd.concat([
    read_solar_file("Residential"),
    read_solar_file("Commercial"),
    read_solar_file("Industrial"),

])

# NOTE will need to not drop Fuel Type if we want to distinguish by battery at some point! 
solar_df = solar_df.drop(["Region ID", "Capacity", "Fuel type"], axis = 1)


solar_df = solar_df.rename(columns = {
    "Avg. capacity installed (kW)" : "avg_cap_kw",
    "Avg. capacity - new installations (kW)" : "avg_cap_new_kw",
    "ICP count - new installations" : "icp_count_new",
    "ICP uptake rate (%)" : "icp_uptake_proportion",
    "Total capacity installed (MW)" : "capacity_installed_mw",    
    "ICP count" : "icp_count",

    "Region name" : "Region",
    "Month end" : "Month",

    })

# make percentage clearer 
solar_df["icp_uptake_proportion"] = solar_df["icp_uptake_proportion"]/100
# wonder if this date object will save correctly in csv form 
solar_df["Month"] = pd.to_datetime(solar_df["Month"], dayfirst = True)

# save
solar_df.to_csv(f"{output_location}/emi_distributed_solar.csv", index = False)

#endregion


#region NSP_CONCORDANCE

df = pd.read_csv(emi_nsp_table)


df = df[df["Current flag"] == 1]
# create a simple POC code using first three letters 
df["POC"] = df["POC code"].str[:3]

# take just the different area concordances and remove dupes
df = df[["POC",
         "Network reporting region",
         "Zone",
         "Island",
         ]].drop_duplicates()
# save 
nsp_data = df
nsp_data.to_csv(f"{output_location}/emi_nsp_concordances.csv", index = False)


#endregion 