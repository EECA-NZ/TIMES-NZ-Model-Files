import sys 
import os 
import pandas as pd 
import numpy as np
import logging

# set log level for message outputs 
logging.basicConfig(level=logging.INFO) # are we even using this? Because we probably should 

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, "../..", "library"))
from filepaths import DATA_INTERMEDIATE, DATA_RAW 
from helpers import test_table_grain, select_and_rename
from deflator import deflate_data



# define outputs for this script 
output_location = f"{DATA_INTERMEDIATE}/stage_4_veda_format/base_year_elc"
os.makedirs(output_location, exist_ok=True)

# parameters 

#so ideally we would have a library script that reads sthe data_intermediate config files and returns all the useful parameters, 
# including base year, but also whatever else we might need, that any script could load in.
base_year = 2023 
cap2act_pjgw = 31.536

############################################################################################
# Load Data 
############################################################################################

# Existing generation technologies 
existing_techs_df = pd.read_csv(f"{DATA_INTERMEDIATE}/stage_2_baseyear/base_year_electricity_supply.csv")
# should have done this before 
existing_techs_df.rename(columns = {"Process":"TechName"}, inplace = True)

# Distribution technologies (much simpler file) 
distribution_df = pd.read_csv(f"{DATA_RAW}/coded_assumptions/electricity_generation/DistributionAssumptions.csv")

############################################################################################
# PROCESS DEFINITION TABLE 
############################################################################################

# need to create the process definitions 
existing_techs_process_df = existing_techs_df[["TechName", "Region"]].drop_duplicates()

# add definitions for the model: 

# sets 
existing_techs_process_df["Sets"] = "ELE"
# activity unit defn
existing_techs_process_df["Tact"] = "PJ"
# cap unit defn
existing_techs_process_df["Tcap"] = "GW"
# timeslice level
existing_techs_process_df["Tslvl"] = "DAYNITE"


# reorder columns 
existing_techs_process_df = existing_techs_process_df[
    ["Sets",
     "Region",
     "TechName",
     "Tact",
     "Tcap"]]

# NOTE: Original version set the PrimaryCG to NRGO for the CHP plants. I am not sure if we need to do this so I won't for now but always an option 

existing_techs_process_df.to_csv(f"{output_location}/existing_tech_process_definitions.csv", index = False)

############################################################################################
# BASE YEAR DATA FILE
############################################################################################


# unit conversions

# this method should be generalised for other uses, I think 
def convert_units(df, conversion_map):    
    df = df.copy()
    # read through all the units we have and convert according to the provided map 
    for old_unit, (new_unit, factor) in conversion_map.items():
        mask = df['Unit'] == old_unit
        df.loc[mask, 'Value'] = df.loc[mask, 'Value'] * factor
        df.loc[mask, 'Unit'] = new_unit
    return df


generation_unit_map = {
    #old_unit: (new_unit_name, conversion_method).
    'MW': ('GW', 1/1000), # capacity
    'GWh': ('PJ', 0.0036), # generation
    'kWh': ('MWh', 1/1000),
    'MWh': ('GWh', 1/1000),
    '2023 NZD/MWh': ('2023 $m NZD/PJ', 0.27778), 
    '2023 NZD/kw': ('2023 $m NZD/GW', 1), 
    '2023 NZD/GJ' : ('2023 $m NZD/PJ', 1),

}
existing_techs_df = convert_units(existing_techs_df, generation_unit_map)

# NCAP_PASTI generation and existing stock treatment -----------------------------------------------------


existing_techs_capacity = existing_techs_df.copy()


existing_techs_capacity = existing_techs_capacity[existing_techs_capacity["Variable"] == "Capacity"]



# Define Attribute (NCAP_PASTI if we know the year, otherwise PRC_RESID)
def get_capacity_method_variable(df):
    year = df["YearCommissioned"]
    if pd.isna(year):
        return "PRC_RESID"
    else: 
        return "NCAP_PASTI"
    
existing_techs_capacity["Attribute"] = existing_techs_capacity.apply(get_capacity_method_variable, axis = 1)
# get years 
existing_techs_capacity = existing_techs_capacity.rename(columns = {"YearCommissioned":"Year"})
existing_techs_capacity["Year"] = existing_techs_capacity["Year"].fillna(base_year) # all null years should be PRC_RESID, so make these base year.
# Veda might do this anyway but best to be explicit

# rename and select columns 
existing_techs_capacity = existing_techs_capacity[["TechName", "Region", "Attribute", "Year", "Value"]]
# save
existing_techs_capacity.to_csv(f"{output_location}/existing_tech_capacity.csv", index = False, encoding = "utf-8-sig")


# pivot and rename ----------------------------------------------------------------------


# as a rule, we'll use the main names, not aliases (eg NCAP_PKCNT rather than Peak)

# define index variables - these define our table grain (as well as 'Variable')

# we also include the capacity data in the index, as this is treated separately. 
index_variables =  ["TechName",
                    "Comm-IN",
                    "Comm-OUT",                    
                    "Region"] 

# Note: we are removing unit here. The units won't go in the output (as are defined by TIMES elsewhere)
# but should potentially be documented more clearly somewhere 
existing_techs_parameters = existing_techs_df.copy()
existing_techs_parameters = existing_techs_parameters[index_variables + ["Variable", "Value"]]

# we can remove capacity as dealt with separately 
existing_techs_parameters = existing_techs_parameters[existing_techs_parameters["Variable"] != "Capacity"]


# NOTE! It would be possible and potentially preferable to feed these as long tables with an Attribute and Unit variable
# pivot out 
existing_techs_parameters = existing_techs_parameters.pivot_table(index = index_variables, columns = "Variable", values = "Value").reset_index()

# rename our variables for Veda 

existing_techs_parameters.rename(columns = {    
    "CapacityFactor" : "AFA",
    "FuelDelivCost": "FLO_DELIV",
    "Generation": f"ACT_BND~FX~{base_year}",
    "PeakContribution": "NCAP_PKCNT",
    "PlantLife": "NCAP_TLIFE",
    "VarOM": "ACTCOST",
    "FixOM":"NCAP_FOM",
    "FuelEfficiency" : "EFF"
    }, inplace = True)


# ADDITIONAL PARAMETERS -----------------------------------


# no new build 
existing_techs_parameters["NCAP_BND"] = 0 
# no new build extrapolate forever 
existing_techs_parameters["NCAP_BND~0"] = 5 
# cap2act required 
existing_techs_parameters["CAP2ACT"] = cap2act_pjgw
# loosen activity bound for future years 
existing_techs_parameters["ACT_BND~0"] = 1
# save 
existing_techs_parameters.to_csv(f"{output_location}/existing_tech_parameters.csv", index = False)


############################################################################################
# Distribution 
############################################################################################

# First, inflate the costs to 2023 NZD.

# costs are in 2015 NZD (according to the input assumption) so we need to deflate these to 2023 NZD.
# we can use the deflator function in the library for this

distribution_df = deflate_data(distribution_df, base_year, ["INVCOST", "VAROM", "FIXOM"])

# Now we can define the map of columns we want from the distribution assumptions, and what each of these should be called, here: 
fi_comm_map = {
    #variable name in current data: desired variable nam
    "CommoditySets": "CSets",
    "Comm-OUT": "CommName",
    "ActivityUnit": "Unit",
    "CommodityTimeSlice": "CTSLvl",
    "CommodityType": "CType"
}

fi_process_map = {
    #variable name in current data: desired variable nam
    "Sets": "Sets",
    "TechName": "TechName",
    "ActivityUnit": "Tact",
    "CapacityUnit": "Tcap",
    "TimeSlice": "TSlvl"
}

distribution_parameters_map = {
    
    "TechName": "TechName",
    "Comm-IN": "Comm-IN",
    "Comm-OUT": "Comm-OUT",
    "Region": "Region",
    
    "NCAP_PASTI~2015": "NCAP_PASTI~2015",
    "AF" : "AF", # why put this in if it's just 1? That's the default? 
    "CAP2ACT": "CAP2ACT", # can also replace this with the cap2act_pjgw variable but this is fine 

    "INVCOST": "INVCOST",
    "VAROM": "VAROM",
    "FIXOM": "FIXOM",

    "Efficiency": "EFF",     
    "Life": "Life"
    }


# create tables 

# Commodity Definitions 

distribution_commodities = select_and_rename(distribution_df,fi_comm_map)
# there will be multiple entries per region but we only need to define once 
distribution_commodities = distribution_commodities.drop_duplicates()


# Process Definitions 
distribution_processes = select_and_rename(distribution_df,fi_process_map)
# there will be multiple entries per region but we only need to define once 
distribution_processes = distribution_processes.drop_duplicates()

# Process technical parameters 
distribution_parameters = select_and_rename(distribution_df, distribution_parameters_map)

# carry forward efficiency (not sure if this is needed, should carry forward by default )
distribution_parameters["EFF~0"] = 0 






print(distribution_parameters)


test_table_grain(distribution_commodities, ["CommName"])
test_table_grain(distribution_processes, ["TechName"])
test_table_grain(distribution_parameters, ["TechName", "Region"])



# Save all these as stage 4 files ready for direct Veda ingestion 

distribution_commodities.to_csv(f"{output_location}/distribution_commodities.csv", index = False, encoding = "utf-8-sig")     
distribution_processes.to_csv(f"{output_location}/distribution_processes.csv", index = False, encoding = "utf-8-sig")
distribution_parameters.to_csv(f"{output_location}/distribution_parameters.csv", index = False, encoding = "utf-8-sig")




