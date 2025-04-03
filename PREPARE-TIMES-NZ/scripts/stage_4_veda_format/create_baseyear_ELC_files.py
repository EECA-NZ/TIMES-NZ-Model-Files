import sys 
import os 
import pandas as pd 
import numpy as np
import logging

# set log level for message outputs 
logging.basicConfig(level=logging.INFO)

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
#region LOAD_DATA 
############################################################################################

# Existing generation technologies 
existing_techs_df = pd.read_csv(f"{DATA_INTERMEDIATE}/stage_2_baseyear/base_year_electricity_supply.csv")
# should have done this before 
existing_techs_df.rename(columns = {"Process":"TechName"}, inplace = True)

# Distribution technologies (much simpler file) 
distribution_df = pd.read_csv(f"{DATA_RAW}/coded_assumptions/electricity_generation/DistributionAssumptions.csv")


#endregion
############################################################################################
#region COMMODITY_DEFINITIONS
############################################################################################

# This section creates the tables for SECTOR_FUELS_ELC
# we have already defined ELC and ELCC02, and all the output commodities (like ELCDD etc) 
# so these are just the dummy commodites and processes for electricity input fuels. 
# we will basically just extract them all from the input commodities, so this list updates automatically.

# Commodity definitions -----------------------------------------------------

elc_input_commoditylist = existing_techs_df["Comm-IN"].unique()

elc_input_commodity_definitions = pd.DataFrame()
elc_input_commodity_definitions["CommName"] = elc_input_commoditylist 
elc_input_commodity_definitions["Csets"] = "NRG"
elc_input_commodity_definitions["Unit"] = "PJ"
elc_input_commodity_definitions["LimType"] = "FX"

# Dummy process parameters -----------------------------------------------------
# We also define the dummy processes that turn the regular commodity into the elc version 
# We'll start with the parameters (just in/out/100% efficiency)

elc_dummy_fuel_process_parameters = pd.DataFrame()
# take all the output commodities we need (inputs from the elc generation processes)
elc_dummy_fuel_process_parameters["Comm-Out"] = elc_input_commoditylist
# use these to create the inputs and the dummy process names 
elc_dummy_fuel_process_parameters["Comm-In"] = elc_dummy_fuel_process_parameters["Comm-Out"].str.removeprefix("ELC")
elc_dummy_fuel_process_parameters["TechName"] = "FTE_" + elc_dummy_fuel_process_parameters["Comm-Out"]

# The next steps are just making sure the columns roughly match the TIMES 2.0 version, but they might actually all be unnecessary.

# reorder these columns (not sure if this is needed)
elc_dummy_fuel_process_parameters = elc_dummy_fuel_process_parameters[["TechName","Comm-In", "Comm-Out"]]
# add a few more specs 
elc_dummy_fuel_process_parameters["EFF"] = 1 # 100% efficiency (could we just leave this blank?)
elc_dummy_fuel_process_parameters["Life"] = "100" # forever (could we just leave this blank?)

# NOTE: we are not using these for fuel delivery costs anymore, as these are done on a per-plant basis in the generation processes.

# Dummy process definitions -----------------------------------------------------
# Now we just provide the definitions for these processes in a separate table 

elc_dummy_fuel_process_definitions = pd.DataFrame()
elc_dummy_fuel_process_definitions["TechName"] = elc_dummy_fuel_process_parameters["TechName"]
elc_dummy_fuel_process_definitions["Sets"] = "PRE" # miscellaneous set
elc_dummy_fuel_process_definitions["Tact"] = "PJ" # activity unit (same as commodity)
elc_dummy_fuel_process_definitions["Tcap"] = "GW" # capacity unit (same as generation) (doesn't actually matter)

# Timeslice level for these was set to Daynite for FTE_ELCNGA - not sure why but we will keep this in place.

elc_dummy_fuel_process_definitions['Tslvl'] = np.where(
    elc_dummy_fuel_process_definitions['TechName'] == 'FTE_ELCNGA',
    'DAYNITE',
    None)
# Save --------------------------------------------------------

elc_input_commodity_definitions.to_csv(f"{output_location}/elc_input_commodity_definitions.csv", index = False, encoding = "utf-8-sig")  
elc_dummy_fuel_process_definitions.to_csv(f"{output_location}/elc_dummy_fuel_process_definitions.csv", index = False, encoding = "utf-8-sig")  
elc_dummy_fuel_process_parameters.to_csv(f"{output_location}/elc_dummy_fuel_process_parameters.csv", index = False, encoding = "utf-8-sig")  


#endregion
############################################################################################
#region PROCESS_DEFINITIONS
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


#endregion
############################################################################################
#region BASE_YEAR_DATA 
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
# no new build extrapolate forever (NOTE this means no new generics or dist solar - will need to tweak with new plants)
existing_techs_parameters["NCAP_BND~0"] = 5 
# cap2act required 
existing_techs_parameters["CAP2ACT"] = cap2act_pjgw
# loosen activity bound for future years (no extrapolation)
existing_techs_parameters["ACT_BND~0"] = 1
# save 
existing_techs_parameters.to_csv(f"{output_location}/existing_tech_parameters.csv", index = False)

#endregion
############################################################################################
#region DISTRIBUTION
############################################################################################

# First, inflate the costs to 2023 NZD.

# costs are in 2015 NZD (according to the input assumption) so we need to deflate these to 2023 NZD.
# we can use the deflator function in the library for this
distribution_df = deflate_data(distribution_df, base_year, ["INVCOST", "VAROM", "FIXOM"])


# We then create the needed tables by mapping existing columns to the required columns in Veda.

# Commodity Definitions ----------------------------
fi_comm_map = {
    #variable name in current data: desired variable name
    "CommoditySets": "CSets",
    "Comm-OUT": "CommName",
    "ActivityUnit": "Unit",
    "CommodityTimeSlice": "CTSLvl",
    "CommodityType": "CType"
}
distribution_commodities = select_and_rename(distribution_df,fi_comm_map)
# there will be multiple entries per region but we only need to define once 
distribution_commodities = distribution_commodities.drop_duplicates()


# Process Definitions ----------------------------
fi_process_map = {
    #variable name in current data: desired variable name
    "Sets": "Sets",
    "TechName": "TechName",
    "ActivityUnit": "Tact",
    "CapacityUnit": "Tcap",
    "TimeSlice": "TSlvl"
}
distribution_processes = select_and_rename(distribution_df,fi_process_map)
# there will be multiple entries per region but we only need to define once 
distribution_processes = distribution_processes.drop_duplicates()

# Process technical parameters ----------------------------
distribution_parameters_map = {
    
    "TechName": "TechName",
    "Comm-IN": "Comm-IN",
    "Comm-OUT": "Comm-OUT",
    "Region": "Region",
    
    "NCAP_PASTI~2015": "NCAP_PASTI~2015",
    "AF" : "AF", # why put this in if it's just 1? That's the default? 
    "CAP2ACT": "CAP2ACT", # can also replace this with the cap2act_pjgw variable but this is fine (stored in raw data)

    "INVCOST": "INVCOST",
    "VAROM": "VAROM",
    "FIXOM": "FIXOM",

    "Efficiency": "EFF",     
    "Life": "Life"
    }

distribution_parameters = select_and_rename(distribution_df, distribution_parameters_map)

# carry forward efficiency (not sure if this is needed, should carry forward by default in Veda)
distribution_parameters["EFF~0"] = 0 


# Test tables for duplicates ----------------------------
test_table_grain(distribution_commodities, ["CommName"])
test_table_grain(distribution_processes, ["TechName"])
test_table_grain(distribution_parameters, ["TechName", "Region"])

# Save -------
distribution_commodities.to_csv(f"{output_location}/distribution_commodities.csv", index = False, encoding = "utf-8-sig")     
distribution_processes.to_csv(f"{output_location}/distribution_processes.csv", index = False, encoding = "utf-8-sig")
distribution_parameters.to_csv(f"{output_location}/distribution_parameters.csv", index = False, encoding = "utf-8-sig")


#endregion

