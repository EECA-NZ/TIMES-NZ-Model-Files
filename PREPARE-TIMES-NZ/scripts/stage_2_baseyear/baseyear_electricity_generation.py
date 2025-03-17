
"""

Base Year Electricity Generation
base_year_generation.py

This script's purpose is to build a base year electricity generation stock using various data sources.
The final output will go to data intermediate, and will be reformatted for Veda further down the pipeline. 

The intent is that we will have capacities, technologies, build years, and generation values for all existing assets in the base year.
This includes using EA and MBIE data for most official injecting plants, and making some assumptions about cogeneration and distributed plants.
The final figures (and some assumptions) are calibrated to MBIE data.

The script can make use of the vscode extention "Outline Map" to make the script more navigable by different regions. 
The code is broken down by #region/#endregion tags, which include a title and optional description

"""


#############################################################################
#region libraries
#############################################################################
# Here we are going to combine all the plants that will make up our base year 
import sys 
import os 
import pandas as pd 
import logging

# set log level for message outputs 
logging.basicConfig(level=logging.INFO) 

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, "../..", "library"))
from filepaths import DATA_RAW, DATA_INTERMEDIATE
CUSTOM_ELE_ASSUMPTIONS = f"{DATA_RAW}/other"

# set parameters 
pd.set_option('display.float_format', '{:.6f}'.format)
# later can read this in from the toml file to ensure easy updates 
base_year = 2023

#endregion

#############################################################################
#region HELPERFUNCTIONS 
#############################################################################

def assign_cogen(value):
    if value == "COG":
        return "CHP"
    else:
        return "ELE"
    
#endregion

#############################################################################
#region IMPORT load all data
#############################################################################

# temp: rewrite the fleet data ensuring correct encoding
# fleet_data = pd.read_csv(f"{DATA_RAW}/other/GenerationFleet.csv")
# fleet_data.to_csv(f"{DATA_RAW}/other/GenerationFleet.csv", index = False, encoding = "utf-8-sig")

genstack_raw_df = pd.read_csv(f"{DATA_INTERMEDIATE}/stage_1_external_data/mbie/gen_stack.csv")
official_generation = pd.read_csv(f"{DATA_INTERMEDIATE}/stage_1_external_data/mbie/mbie_ele_generation_gwh.csv")
official_generation_no_cogen = pd.read_csv(f"{DATA_INTERMEDIATE}/stage_1_external_data/mbie/mbie_ele_only_generation.csv")
official_capacity = pd.read_csv(f"{DATA_INTERMEDIATE}/stage_1_external_data/mbie/mbie_generation_capacity.csv")
emi_md = pd.read_parquet(f"{DATA_INTERMEDIATE}/stage_1_external_data/electricity_authority/emi_md.parquet", engine = "pyarrow")
emi_fleet_data = pd.read_csv(f"{DATA_RAW}/external_data/electricity_authority/emi_fleet_data/20230601_DispatchedGenerationPlant.csv")

# custom data (including some assumptions)
eeca_fleet_data = pd.read_csv(f"{CUSTOM_ELE_ASSUMPTIONS}/GenerationFleet.csv")
custom_gen_data = pd.read_csv(f"{CUSTOM_ELE_ASSUMPTIONS}/CustomFleetGeneration.csv")
generic_plant_settings = pd.read_csv(f"{CUSTOM_ELE_ASSUMPTIONS}/GenericCurrentPlants.csv")
capacity_factors = pd.read_csv(f"{CUSTOM_ELE_ASSUMPTIONS}/CapacityFactors.csv")


# concordances
region_island_concordance = pd.read_csv(f"{DATA_RAW}/concordances/region_island_concordance.csv")

#endregion

#############################################################################
#region GENSTACK process MBIE genstack
#############################################################################

genstack_df = genstack_raw_df[genstack_raw_df["Scenario"] == "Reference"]
genstack_df = genstack_df[genstack_df["Status"] == "Current"]



# only specific variables 
genstack_df = genstack_df[["Plant", "PlantType",
                          "Tech", "TechName", "Substation", "Region", 
                          "Capacity (MW)", "Heat Rate (GJ/GWh)",                          
                          "Variable operating costs (NZD/MWh)", "Fixed operating costs (NZD/kW/year)"]]


# Add regions (SI/NI)
genstack_df = genstack_df.merge(region_island_concordance, how = "left", on = "Region")

#endregion

#############################################################################
#region EMI process EMI_MD data
#############################################################################



# EMI_MD processing 
# we just want annual base year generation values for each plant, and some metadata to help us ensure we can match concordances properly.

# aggregate by year 
emi_md["Trading_Date"] = pd.to_datetime(emi_md["Trading_Date"])
emi_md["Period"] = emi_md["Trading_Date"].dt.year
emi_md = emi_md.groupby(["Period", "Gen_Code", "Fuel_Code", "Tech_Code"]).sum("Value").reset_index()

emi_md = emi_md[emi_md["Period"] == base_year]


# reminder from https://www.emi.ea.govt.nz/Wholesale/Datasets/Generation/Generation_MD that units are presented in kWh

# we can convert to gwh just to make this a little easier to work with for now. Might need to be PJ later. 
emi_md["Value"] = emi_md["Value"]/1e6
emi_md["Unit"] = "GWh"

# checks 
total_md_gen = emi_md.groupby("Period").sum("Value").reset_index()

total_md_gen = total_md_gen[total_md_gen["Period"] == base_year]
total_md_gen = total_md_gen.loc[0, "Value"]
print(f"Total MD Generation = {round(total_md_gen,2)}GWh")


#endregion 


#############################################################################
#region OFFICIAL_GENERATION Create summary official generation data 
#############################################################################


# we just want this by fuel and cogen split and can use it to guide base year generation

generation_summary = official_generation[official_generation["Year"] == base_year]
generation_summary = generation_summary[["Year", "FuelType", "Unit", "Value"]]
generation_summary = generation_summary.rename(columns = {"Value" : "MBIE_Value"})
                                                          


# add cogen split 
ele_only = official_generation_no_cogen
# official_generation_no_cogen = official_generation_no_cogen.rename(columns = {""}

# rename solar (Solar PV -> Solar)
ele_only["FuelType"] = ele_only["FuelType"].replace("Solar PV", "Solar")


ele_only = ele_only[ele_only["Year"] == base_year]
ele_only = ele_only[["Year", "FuelType", "Value"]]
ele_only = ele_only.rename(columns = {"Value":"ELE"})

# merge 
generation_summary = generation_summary.merge(ele_only, how = "left", on = ["Year", "FuelType"])

# failed joins mean 0 electricity only generation (ie all cogen)
generation_summary["ELE"] = generation_summary["ELE"].fillna(0)

# calculate cogeneration 
generation_summary["CHP"] = generation_summary["MBIE_Value"] - generation_summary["ELE"]

# we can now remove the total value and stack electricity and generation 
generation_summary = generation_summary.drop("MBIE_Value", axis = 1)


generation_summary = generation_summary.melt(
    id_vars = ["Year", "Unit", "FuelType"],
    value_vars = ["ELE", "CHP"],
    var_name = "GenerationType",
    value_name = "MBIE_Value"
)

generation_summary = generation_summary.rename(columns = {"Fuel":"FuelType"})
#endregion

#############################################################################
#region BASEGENERATION Create base list 
#############################################################################

# read our main data
base_year_gen = eeca_fleet_data[["PlantName", "EMI_Name","TechnologyCode", "FuelType", "CapacityMW","YearCommissioned","GenerationMethod"]]
# add the generation type
base_year_gen["GenerationType"] = base_year_gen["TechnologyCode"].apply(assign_cogen)


#endregion

#############################################################################
#region ADD_EMI add EMI MD generation to main list 
#############################################################################

# add emi figures where possible
emi_md_per_plant_by = emi_md[["Gen_Code", "Value"]]

# for the emi data, rename the Gen_Code to join on, and make the value explicitly from EMI
emi_md_per_plant_by = emi_md_per_plant_by.rename(
    columns = {"Gen_Code": "EMI_Name",
               "Value" : "EMI_Value"})
# only those plants we are doing EMI with 
base_year_gen_emi = base_year_gen[base_year_gen["GenerationMethod"] == "EMI"]
# add the emi data
base_year_gen_emi = base_year_gen_emi.merge(emi_md_per_plant_by, how = "left", on = "EMI_Name")
# for multiple plants per EMI node, get capacity shares for splitting the generation 
base_year_gen_emi["CapacityShare"] = base_year_gen_emi['CapacityMW'] / base_year_gen_emi.groupby('EMI_Name')['CapacityMW'].transform('sum')
base_year_gen_emi["EMI_Value"] = base_year_gen_emi["EMI_Value"] * base_year_gen_emi["CapacityShare"]




# TODO: tidy variable selection to align with other methods 
base_year_gen_emi = base_year_gen_emi.rename(columns={"EMI_Value":"EECA_Value"})
base_year_gen_emi = base_year_gen_emi.drop("CapacityShare", axis = 1 )
# TODO 

#endregion




#############################################################################
#region ADD_CF_Defaults estimate generation for some plants 
# assumed capac
#############################################################################

# only apply to plants with Capacity Factor generation method settings
base_year_gen_cfs = base_year_gen[base_year_gen["GenerationMethod"] == "Capacity Factor"]

base_year_gen_cfs = base_year_gen_cfs.merge(capacity_factors, on = ["FuelType", "GenerationType"])



base_year_gen_cfs["EECA_Value"] = (base_year_gen_cfs["CapacityMW"] * 8.76)*base_year_gen_cfs["CapacityFactor"]


#endregion
#############################################################################
#region ADD_CUSTOM add custom plants to list (just Huntly right now)
#############################################################################
# custom generation methods (just HLY right now)

base_year_gen_custom = base_year_gen[base_year_gen["GenerationMethod"] == "Custom"]

# adjust to remove the FuelType and EMI_Name (not needed for this)
base_year_gen_custom = base_year_gen_custom.drop(["FuelType", "TechnologyCode"], axis = 1 )

base_year_gen_custom = base_year_gen_custom.merge(custom_gen_data, how = "left", on = "PlantName")

# tidy variables

base_year_gen_custom = base_year_gen_custom.drop("Source", axis = 1)

#endregion 

#############################################################################
#region COMBINE combine all plant data together
#############################################################################

base_year_gen = pd.concat([base_year_gen_emi,
                           base_year_gen_custom,
                           base_year_gen_cfs], axis = 0)

#endregion

#################################################################
#region CALIBRATE_GEN calibrate generation 
# this is BEFORE adding generic plants
#################################################################



base_year_summary = base_year_gen.groupby(["FuelType", "GenerationType"])["EECA_Value"].sum().reset_index()
base_year_summary = base_year_summary.rename(columns = {"Fuel":"FuelType"})
# rename Diesel to Oil to match MBIE 
base_year_summary.loc[base_year_summary["FuelType"] == "Diesel", "FuelType"] = "Oil"





gen_comparison = generation_summary.merge(base_year_summary, how = "left")
gen_comparison["EECA_Value"] = gen_comparison["EECA_Value"].fillna(0)

gen_comparison["Delta"] = gen_comparison["MBIE_Value"] - gen_comparison["EECA_Value"]
gen_comparison = gen_comparison.sort_values(by = ["FuelType", "GenerationType"])

# add implied capacity factors (we can overwrite these later but useful to inspect) 

base_year_gen["CapacityFactor"] = base_year_gen["EECA_Value"]/(base_year_gen["CapacityMW"]*8.760)





#endregion

#############################################################################
#region ADD_GENERIC use calibrated data to create generic plants and fill gaps
# note: this will be based on the category settings found in GenericCurrentPlants.csv,
# so you can adjust those there
#############################################################################



# find deltas based on the generic plant settings by inner join on the calibrated data 



generic_generation = gen_comparison.merge(generic_plant_settings, on = ["FuelType", "GenerationType"], how = "inner")
# add capacity factors 
generic_generation = generic_generation.merge(capacity_factors, on = ["FuelType", "GenerationType"], how = "left")
# rearrange columns 
generic_generation = generic_generation[["PlantName", "FuelType","GenerationType", "Delta", "CapacityFactor"]]

# the missing generation (Delta) becomes our new value for these plants 
generic_generation = generic_generation.rename(columns = {"Delta":"EECA_Value"})

# use the generation and capacityfactor to reverse engineer an assumed capacity 

generic_generation["CapacityMW"] = (generic_generation["EECA_Value"]*1000/8760)/generic_generation["CapacityFactor"]

generic_generation["GenerationMethod"] = "Generic"

# add these plants to the main table 


base_year_gen = pd.concat([base_year_gen,generic_generation])






#endregion


#############################################################################
#region RECALIBRATE_GEN testing new calibration
#############################################################################


base_year_summary = base_year_gen.groupby(["FuelType", "GenerationType"])["EECA_Value"].sum().reset_index()

# rename Diesel to Oil to match MBIE 
base_year_summary.loc[base_year_summary["FuelType"] == "Diesel", "FuelType"] = "Oil"




gen_comparison = generation_summary.merge(base_year_summary, how = "left")
gen_comparison["EECA_Value"] = gen_comparison["EECA_Value"].fillna(0)

gen_comparison["Delta"] = gen_comparison["MBIE_Value"] - gen_comparison["EECA_Value"]
gen_comparison = gen_comparison.sort_values(by = ["FuelType", "GenerationType"])


#endregion


#############################################################################
#region CALIBRATE_CAP test capacity
#############################################################################
# test 
# process mbie capacity 
# base year 
mbie_capacity = official_capacity[official_capacity["Year"] == base_year]
# remove "other"
mbie_capacity = mbie_capacity[mbie_capacity["Technology"] != "Other electricity generation"]
# add generation types and ensure cogen treated correctly 
mbie_capacity["GenerationType"] = "ELE"

mbie_capacity.loc[mbie_capacity["Technology"] == "Gas Cogen", "GenerationType"] = "CHP"
mbie_capacity.loc[mbie_capacity["Technology"] == "Other Cogen", "GenerationType"] = "CHP"

mbie_capacity.loc[mbie_capacity["Technology"] == "Gas Cogen", "Technology"] = "Gas"
mbie_capacity.loc[mbie_capacity["Technology"] == "Other Cogen", "Technology"] = "Other"

# rename a few things 
mbie_capacity.loc[mbie_capacity["Technology"] == "Solar PV", "Technology"] = "Solar"
mbie_capacity.loc[mbie_capacity["Technology"] == "Coal/Gas", "Technology"] = "Coal" # Rankine treatment might need to change but whatever

# trim columns and rename

mbie_capacity = mbie_capacity[["Technology", "GenerationType", "Value"]]

mbie_capacity = mbie_capacity.rename(columns = {
    "Value" : "MBIE_Value",
    "Technology" : "FuelType",
    })
    

# todo 

# remove the gas rankine to avoid double counting it (we just call it coal, whatever)
base_year_summary_cap = base_year_gen[~((base_year_gen["TechnologyCode"] == "RNK") & (base_year_gen["FuelType"] == "Gas"))]

# convert wood CHP to other (not quite accurate but works here) 
base_year_summary_cap.loc[(base_year_summary_cap["GenerationType"] == "CHP") & (base_year_summary_cap["FuelType"] != "Gas"),
                          "FuelType"] = "Other"

# can aggregate now 
base_year_summary_cap = base_year_summary_cap.groupby(["FuelType", "GenerationType"])["CapacityMW"].sum().reset_index()

# rename 
base_year_summary_cap.rename(columns = {"CapacityMW":"EECA_Value"}, inplace=True)






cap_comparison = pd.merge(mbie_capacity,
                          base_year_summary_cap, 
                          how = "left",
                          on = ["FuelType", "GenerationType"])

# cap_comparison["EECA_Value"


cap_comparison["EECA_Value"] = cap_comparison["EECA_Value"].fillna(0)
cap_comparison["Delta"] = (cap_comparison["EECA_Value"]/cap_comparison["MBIE_Value"]-1)*100

#endregion 

###########################################
#region CHECKS 
###########################################

print(cap_comparison)

#endregion