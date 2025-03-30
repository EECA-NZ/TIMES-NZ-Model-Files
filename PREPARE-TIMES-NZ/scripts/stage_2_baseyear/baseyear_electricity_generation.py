
"""

Base Year Electricity Generation

This script's purpose is to build a base year electricity generation stock using various data sources.
The final output will go to data intermediate, and will be reformatted for Veda further down the pipeline. 

The intent is that we will have capacities, technologies, build years, and generation values for all existing assets in the base year.
This includes using EA and MBIE data for most official injecting plants, and making some assumptions about cogeneration and distributed plants.
The final figures (and some assumptions) are calibrated to MBIE data.

The script can make use of the vscode extention "Outline Map" to make the script more navigable by different regions. 
The code is broken down by #region/#endregion tags, which include a title and optional description


You can read full information about this script at `PREPARE-TIMES-NZ/docs/model_methodology/base_year_electricity.md`

"""


#############################################################################
#region SETUP
#############################################################################
# Here we are going to combine all the plants that will make up our base year 
import sys 
import os 
import pandas as pd 
import logging
import unicodedata
import numpy as np

# set log level for message outputs 
logging.basicConfig(level=logging.INFO) 

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, "../..", "library"))
from filepaths import DATA_RAW, DATA_INTERMEDIATE
CUSTOM_ELE_ASSUMPTIONS = f"{DATA_RAW}/coded_assumptions/electricity_generation"
CONCORDANCES = f"{DATA_RAW}/concordances"

# define and create intermediate location for base year data 
output_location = f"{DATA_INTERMEDIATE}/stage_2_baseyear"
os.makedirs(output_location, exist_ok = True)

# and for any testing outputs we might want to browse
check_location = f"{output_location}/checks"
os.makedirs(check_location, exist_ok = True)


# set parameters 
pd.set_option('display.float_format', '{:.6f}'.format)
show_checks = True
# later can read this in from the toml file to ensure easy updates 
base_year = 2023

#endregion
#############################################################################
#region HELPERFUNCTIONS 
#############################################################################

# we have one lonely function here.
# to do: refactor and functionalise more of this script? 
def assign_cogen(value):
    if value == "COG":
        return "CHP"
    else:
        return "ELE"
    
#endregion
#############################################################################
#region IMPORT load all data
#############################################################################

#MBIE
official_generation = pd.read_csv(f"{DATA_INTERMEDIATE}/stage_1_external_data/mbie/mbie_ele_generation_gwh.csv")
official_generation_no_cogen = pd.read_csv(f"{DATA_INTERMEDIATE}/stage_1_external_data/mbie/mbie_ele_only_generation.csv")
official_capacity = pd.read_csv(f"{DATA_INTERMEDIATE}/stage_1_external_data/mbie/mbie_generation_capacity.csv")
genstack = pd.read_csv(f"{DATA_INTERMEDIATE}/stage_1_external_data/mbie/gen_stack.csv")

#EMI 
emi_md = pd.read_parquet(f"{DATA_INTERMEDIATE}/stage_1_external_data/electricity_authority/emi_md.parquet", engine = "pyarrow")
emi_solar = pd.read_csv(f"{DATA_INTERMEDIATE}/stage_1_external_data/electricity_authority/emi_distributed_solar.csv")

# custom assumptions
eeca_fleet_data = pd.read_csv(f"{CUSTOM_ELE_ASSUMPTIONS}/GenerationFleet.csv")
custom_gen_data = pd.read_csv(f"{CUSTOM_ELE_ASSUMPTIONS}/CustomFleetGeneration.csv")
generic_plant_settings = pd.read_csv(f"{CUSTOM_ELE_ASSUMPTIONS}/GenericCurrentPlants.csv")
capacity_factors = pd.read_csv(f"{CUSTOM_ELE_ASSUMPTIONS}/CapacityFactors.csv")
technology_assumptions = pd.read_csv(f"{CUSTOM_ELE_ASSUMPTIONS}/TechnologyAssumptions.csv")

# concordances
region_island_concordance = pd.read_csv(f"{CONCORDANCES}/region_island_concordance.csv")
nsp_table = pd.read_csv(f"{DATA_INTERMEDIATE}/stage_1_external_data/electricity_authority/emi_nsp_concordances.csv")

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
# assuming all MBEI oil gen is diesel (we have no fuel oil generators anymore, nobody burns crude for ele gen, petrol out too I assume?)
generation_summary.loc[generation_summary["FuelType"] == "Oil", "FuelType"] = "Diesel"


#endregion
#############################################################################
#region BASEGENERATION Create base list 
#############################################################################

# read our main data
base_year_gen = eeca_fleet_data.copy()
base_year_gen = base_year_gen[["PlantName", "EMI_Name","TechnologyCode", "FuelType", "POC", "CapacityMW","YearCommissioned","GenerationMethod"]]
# add the generation type
base_year_gen["GenerationType"] = base_year_gen["TechnologyCode"].apply(assign_cogen)


# add the regions based on island 
# we will need to adjust this method if not using islands for regions 
poc_island_concordance = nsp_table.copy()
poc_island_concordance = poc_island_concordance[["POC", "Island"]].drop_duplicates()
base_year_gen = base_year_gen.merge(poc_island_concordance, how = "left", on = "POC")
base_year_gen.rename(columns = {"Island":"Region"}, inplace = True)



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



#  TODO: tidy variable selection to align with other methods 
base_year_gen_emi = base_year_gen_emi.rename(columns={"EMI_Value":"EECA_Value"})
base_year_gen_emi = base_year_gen_emi.drop("CapacityShare", axis = 1 )




# need the NSP table against the nodes I guess? 

#endregion
#############################################################################
#region ADD_CF_Defaults estimate generation for some plants 
# assumed capac
#############################################################################

# only apply to plants with Capacity Factor generation method settings
base_year_gen_cfs = base_year_gen[base_year_gen["GenerationMethod"] == "Capacity Factor"]

base_year_gen_cfs = base_year_gen_cfs.merge(capacity_factors, on = ["FuelType", "GenerationType", "TechnologyCode"])



base_year_gen_cfs["EECA_Value"] = (base_year_gen_cfs["CapacityMW"] * 8.76)*base_year_gen_cfs["CapacityFactor"]


#endregion
#############################################################################
#region ADD_CUSTOM add custom plants to list (just Huntly right now)
#############################################################################
# custom generation methods (just HLY right now)

base_year_gen_custom = base_year_gen[base_year_gen["GenerationMethod"] == "Custom"]

base_year_gen_custom = base_year_gen_custom.merge(custom_gen_data, how = "left", on = ["PlantName", "FuelType", "TechnologyCode"])

# tidy variables

base_year_gen_custom = base_year_gen_custom.drop("Source", axis = 1)


#endregion 
#############################################################################
#region ADD_SOLAR create generic distributed solar by island and sector 
#############################################################################

# start with the loaded emi_solar data 
df = emi_solar.copy()

# adjust date data and create a year variable.
df["Month"] = pd.to_datetime(df["Month"])
# we are only taking capacity at the end of the year 
df = df[df["Month"].dt.month == 12]
df["Year"] = df["Month"].dt.year

# add island concordances
df = df.merge(region_island_concordance, how = "left", on = "Region")
# generate distinct plant names for TIMES 
df["PlantName"] = "DistributedSolar"+ df["Sector"]

# aggregate across new region definitions 
df = df.groupby(["Year", "PlantName", "Island", "Sector"])["capacity_installed_mw"].sum().reset_index()

# only need base year 
df = df[df["Year"] == base_year]

# get capacity shares 
df["total_cap"] = df.groupby("Year").sum()["capacity_installed_mw"].sum()
df["capacity_share"] = df["capacity_installed_mw"]/df["total_cap"]

# add official solar generation for the year as a reference 
solar_generation = official_generation[official_generation["FuelType"] == "Solar"]
solar_generation = solar_generation[["Year", "Value"]]
solar_generation = solar_generation.rename(columns ={"Value":"TotalSolarGen"})

df = df.merge(solar_generation, how = "left", on = "Year")

# estimate generation 
df["EECA_Value"] = df["capacity_share"] * df["TotalSolarGen"]

# take only necessary variables 
# implied capacity factors (should hit 12ish ) 
# Note slightly low implicit capacity factor. This will be at least in part due to some installations coming on late in the year 
# not least of all the lodestone plants, which came partially online in November and were a pretty big bump to capacity (NI Industrial category)

df["CapacityFactor"] = df["EECA_Value"]/(df["capacity_installed_mw"]*8.760)

# not cogen :)

# some renaming and readjusting of columns 
df = df.rename(columns = {
    "capacity_installed_mw":"CapacityMW",
    "Island":"Region"
    })
df = df[["PlantName", "CapacityMW", "EECA_Value", "Region", "CapacityFactor"]]

# and a few new columns for the main table 
df["GenerationType"] = "ELE"
df["GenerationMethod"] = "Solar data from MBIE"
df["TechnologyCode"] = "SOL"
df["FuelType"] = "Solar"
base_year_gen_dist_solar = df




#endregion
#############################################################################
#region COMBINE combine all plant data together
#############################################################################

base_year_gen = pd.concat([base_year_gen_emi,
                           base_year_gen_custom,
                           base_year_gen_cfs,
                           base_year_gen_dist_solar], axis = 0)

#endregion
#############################################################################
#region CALIBRATE_GEN calibrate generation 
# this is BEFORE adding generic plants
#################################################################



base_year_summary = base_year_gen.groupby(["FuelType", "GenerationType"])["EECA_Value"].sum().reset_index()
base_year_summary = base_year_summary.rename(columns = {"Fuel":"FuelType"})







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


generic_generation = generic_generation.merge(capacity_factors, on = ["FuelType", "GenerationType", "TechnologyCode"], how = "left")

# rearrange columns 
generic_generation = generic_generation[["PlantName", "FuelType","GenerationType","TechnologyCode", "Delta", "CapacityFactor"]]

generic_generation = generic_generation.rename(columns = {"Delta":"EECA_Value"})
# in some cases, we will overcount generation (not ideal) - in these cases, we obviously don't to add negative plants 
# so we remove all rows with negative deltas 
# this also means we will correctly represent categories where we have overcounted somehow, which might mean we need to review our 
# methods/assumptions for some areas 

# the missing generation (Delta) becomes our new value for these plants 
generic_generation = generic_generation[generic_generation["EECA_Value"] > 0]

# before we generate capacities, we need to distribute the generation by region (so each region gets a certain capacity/gen)
# we do this by using the same region distributions as the non-generic plants we have already found 

region_gen = base_year_gen.copy()
# aggregate capacities
region_gen = region_gen.groupby(["Region","GenerationType", "FuelType"])["CapacityMW"].sum().reset_index()
region_gen["Total"] = region_gen.groupby(["FuelType", "GenerationType"])["CapacityMW"].transform("sum")
region_gen["Share"] = region_gen["CapacityMW"]/region_gen["Total"]


region_gen = region_gen[["FuelType", "GenerationType", "Region", "Share"]]

generic_generation = generic_generation.merge(region_gen, how = "left", on = ["GenerationType", "FuelType"])

# if missing regions, we replace share with 1
generic_generation["Share"] = generic_generation["Share"].fillna(1)
# and region with NI 
generic_generation["Region"] = generic_generation["Region"].fillna("NI")
# can now adjust the values as needed 
generic_generation["EECA_Value"] = generic_generation["EECA_Value"] * generic_generation["Share"]
# and drop the shares 
generic_generation.drop("Share", axis = 1, inplace = True)


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
# assess differences
cap_comparison["EECA_Value"] = cap_comparison["EECA_Value"].fillna(0)
cap_comparison["Delta"] = (cap_comparison["EECA_Value"]-cap_comparison["MBIE_Value"])

#endregion 
#############################################################################
#region TECHNICAL_PARAMETERS # remaining technical parameters 
#############################################################################

# assumptions by technology (peak cont, plant life)
base_year_gen = base_year_gen.merge(technology_assumptions, how = "left", on = "TechnologyCode")

# capacity factors. Some of these are by assumption (either generic or capacityfactor settings), the rest are implied by capacity and output for the base year. 
# we don't want to limit AFA to base year implied cfs, so we will shuffle these away and add assumed capacity factors instead 

base_year_gen.rename(columns = {"CapacityFactor": "ImpliedCapacityFactor"}, inplace = True)
# now we can rejoin on the assumed CFs, as these will make our upper limits on availablity for TIMES 
base_year_gen = base_year_gen.merge(capacity_factors, how = "left", on = ["FuelType", "GenerationType", "TechnologyCode"])


# The rest of the parameters come from MBIE's genstack.
#  This section is ripe for refactor, as a lot of manual coding and mapping happens to tie everything togehter

# first, we'll extract a mapping of eeca plant names to MBIE plant names from our original manual file 
eeca_mbie_plantname_concordance = eeca_fleet_data[["PlantName", "FuelType", "MBIE_Name"]]
# we need to distinguish some of these by fueltype or huntly gets double counted 
base_year_gen = base_year_gen.merge(eeca_mbie_plantname_concordance, how = "left", on = ["PlantName", "FuelType"])

# now we can get all the additional cost parameters we want from the mbie genstack data by joining on the mbie name 
# additional parameters 
reference_genstack = genstack[genstack ["Scenario"] == "Reference"]
current_genstack = reference_genstack[reference_genstack["Status"] == "Current"]

# First, we apply specific values to specific plants where possible, by extracting these for each plant and joining 
# this is all we want from the main 
specific_parameters = current_genstack[[
    "Plant",
    "Heat Rate (GJ/GWh)",
    "Variable operating costs (NZD/MWh)",
    "Fixed operating costs (NZD/kW/year)",
    "Fuel delivery costs (NZD/GJ)",
    ]]

# rename plant for joining on 
specific_parameters = specific_parameters.rename(columns = {
    "Plant" : "MBIE_Name",
    "Heat Rate (GJ/GWh)": "specific_heatrate_gj_gwh",
    "Variable operating costs (NZD/MWh)": "specific_varom_nzd_mwh",
    "Fixed operating costs (NZD/kW/year)": "specific_fixom_nzd_kw_year",
    "Fuel delivery costs (NZD/GJ)": 'specific_fuel_delivery_costs_nzd_gj',
})


# add these 

base_year_gen = base_year_gen.merge(specific_parameters, how = "left", on = "MBIE_Name")


# we now make some generic additions for our missing plants 

# We'll pull these from the full reference list for better coverage

genstack_avg_parameters = reference_genstack.groupby(["TechName"])[[
    "Heat Rate (GJ/GWh)",    
    "Variable operating costs (NZD/MWh)",
    "Fixed operating costs (NZD/kW/year)",
    "Fuel delivery costs (NZD/GJ)",
    ]].mean().reset_index()



genstack_avg_parameters = genstack_avg_parameters.rename(columns = {
    "Heat Rate (GJ/GWh)": "generic_heatrate_gj_gwh",
    "Variable operating costs (NZD/MWh)": "generic_varom_nzd_mwh",
    "Fixed operating costs (NZD/kW/year)": "generic_fixom_nzd_kw_year",
    "Fuel delivery costs (NZD/GJ)": 'generic_fuel_delivery_costs_nzd_gj',
})

# here we're going to map the MBIE technames to our fuel/tech combos
# this mapping should possibly be moved to an assumptions input tbh but we'll do it here first. 

techs_to_fuels = np.array([

    # Rankines - not sure why we bother making generic costs when we do these already. But we do. 
    ["Coal", "RNK", "Coal"],
    ["Gas", "RNK", "Gas"],
    # Cogen plants - natural gas 
    ["Cogeneration, gas-fired", "COG", "Gas"],
    # We apply "other" cogen to all the diff generic cogen plants we have 
    ["Cogeneration, other", "COG", "Wood"],
    ["Cogeneration, other", "COG", "Coal"],
    ["Cogeneration, other", "COG", "Biogas"],
    # we'll use geothermal for both ele and cogen geo
    ["Geothermal", "GEO", "Geothermal"],
    ["Geothermal", "COG", "Geothermal"],    
    # Using assumptions on maint costs for unadjusted future plants for the current biogas generation 
    ["Reciprocating Biogas engine", "BIG", "Biogas"],    
    # Gas turbines
    ["Combined cycle gas turbine", "CCGT", "Gas"],
    ["Open cycle gas turbine", "OCGT", "Gas"],
    ["Peaker, gas-fired OCGT", "", ""], #not currently used 
    # Diesel - we'll apply to our main and generic diesel plants: 
    ["Peaker, diesel-fired OCGT", "OCGT", "Diesel"],
    ["Peaker, diesel-fired OCGT", "DIE", "Diesel"],
    # Wind/solar/hydro - quite straightfowrad. we use the future RR OM costs for existing RR OM costs
    ["Solar", "SOL", "Solar"],
    ["Wind", "WIN", "Wind"],  
    ["Hydro, schedulable", "HYD", "Hydro"],
    ["Hydro, run of river", "HYDRR", "Hydro"],
    ])

techs_to_fuels = pd.DataFrame(techs_to_fuels, columns=['TechName', 'TechnologyCode', 'FuelType'])

# we can add these to our main table to get mbie_concordance values for generic costs 
base_year_gen = base_year_gen.merge(techs_to_fuels, how = "left", on = ["FuelType", "TechnologyCode"])
# now we can use these codes to add the generic parameters 
base_year_gen = base_year_gen.merge(genstack_avg_parameters, how = "left", on = "TechName")

# finally, we select either specific or generic factors for each plant, depending on what is available. 
base_year_gen["HeatRate"] = base_year_gen["specific_heatrate_gj_gwh"].fillna(base_year_gen["generic_heatrate_gj_gwh"])
base_year_gen["VarOM"] = base_year_gen["specific_varom_nzd_mwh"].fillna(base_year_gen["generic_varom_nzd_mwh"])
base_year_gen["FixOM"] = base_year_gen["specific_fixom_nzd_kw_year"].fillna(base_year_gen["generic_fixom_nzd_kw_year"])
base_year_gen["FuelDelivCost"] = base_year_gen["specific_fuel_delivery_costs_nzd_gj"].fillna(base_year_gen["generic_fuel_delivery_costs_nzd_gj"])


# remove all the unnecessary variables now 
base_year_gen = base_year_gen.drop([
    # intermediate variables 
    "generic_heatrate_gj_gwh",
    "generic_varom_nzd_mwh",
    "generic_fixom_nzd_kw_year",
    "generic_fuel_delivery_costs_nzd_gj",
    "specific_heatrate_gj_gwh",
    "specific_varom_nzd_mwh",
    "specific_fixom_nzd_kw_year",
    "specific_fuel_delivery_costs_nzd_gj",

    # linking name 
    "TechName"

], axis = 1)

# we will create efficiency as a function of heat rate 
# heat rate is the ratio between GJ in and GWH out - we'll simply normalise the units to find percentage efficiency:
base_year_gen["FuelEfficiency"] = 3600/base_year_gen["HeatRate"]




#endregion 
#############################################################################
#region TIMES_FEATURES # adding additional information for TIMES variables 
#############################################################################

# add the output techs (ELC for everything but solar I guess)
def add_output_commodity(df):
    if df["TechnologyCode"] == "SOL":
        return "ELCDD"
    else: 
        return "ELC"
    
# input techs 

def add_input_commodity(df):
    tech_based = ["SOL", "WIN", "HYD", "GEO"]
    
    if df["TechnologyCode"] in tech_based:
        in_com = df["TechnologyCode"]
    else:
        fuel_to_com = {
            "Wood": "WOD",
            "Gas": "NGA",
            "Coal": "COA",
            "Diesel": "OIL",
            "Biogas": "BIG",
            "Geothermal": "GEO",
            "Hydro": "HYD",
        }
        in_com = fuel_to_com.get(df["FuelType"], "UNDEFINED")

    return f"ELC{in_com}"

# for output commodities, we just adjust the solar output commodities to ELCDD rather than ELC
base_year_gen["Comm-OUT"] = base_year_gen.apply(add_output_commodity, axis = 1)

# for the rest, we align with TIMES 2.0 input commodity definitions
base_year_gen["Comm-IN"] = base_year_gen.apply(add_input_commodity, axis = 1)


# Generate Process Name for each asset  
    
def to_pascal_case(s):
    return ''.join(word.capitalize() for word in s.split())


def remove_diacritics(input_str):
    # Normalize the string to decompose characters into base characters and diacritical marks
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    # Filter out all combining characters (diacritical marks)
    return ''.join(char for char in nfkd_form if not unicodedata.combining(char))


def clean_generic_process_names(df):
    # If the name is generic, then we don't want the extra bits currerntly added to "PlantName"
    if df["GenerationMethod"] == "Generic":
        return "Generic"
    else:
        return df["Process"]

# generate names for each process. First just capitalise the main name 
base_year_gen["Process"] = base_year_gen["PlantName"].apply(to_pascal_case)
# going to remove macrons because these will probably cause trouble when applied to GAMS code 
base_year_gen["Process"] = base_year_gen["Process"].apply(remove_diacritics)
# in cases where we made generic names, we just remove the extra bits 
base_year_gen["Process"] = base_year_gen.apply(clean_generic_process_names, axis = 1)
# now add some useful features to the process name and ensure distinct
base_year_gen["Process"] = "ELC_" + base_year_gen["FuelType"] + "_" + base_year_gen["TechnologyCode"] + "_" + base_year_gen["Process"]


# this doesn't work for Huntly - creates multiple processes which is not what we want
# Will manually change this for now but might want a better process for dual fuel processes 
# We don't actually have the information in the file for which plants take multifuel (as separate processes) and which don't (and are single processes with multiple inputs)
# need to think about a better approach for this maybe 

base_year_gen.loc[base_year_gen["TechnologyCode"] == "RNK", "Process"] = "ELC_RNK_HuntlyUnits1-4"




#endregion 
#############################################################################
#region TIDYDATA # tidy data principles on output, including long form and unit documentation
#############################################################################

base_year_gen = base_year_gen.rename(
    columns = {"EECA_Value":"Generation",
               "CapacityMW":"Capacity",
               })


# For our technical/cost variables, we pivot longer and and assign units
variable_unit_map = {
    'Capacity': 'MW',
    'Generation': 'GWh',
    'CapacityFactor': '%',
    'VarOM': '2023 NZD/MWh',
    'FixOM': '2023 NZD/kw',
    "FuelDelivCost" : '2023 NZD/GJ',
    'PlantLife': 'Years',
    'PeakContribution': '%',
    "FuelEfficiency": '%',

}

#extract the variable names - we pivot all these 
value_vars = list(variable_unit_map.keys())

# id variables is everything else that can remain in the table
id_vars = [col for col in base_year_gen.columns if col not in value_vars]

# pivot (or 'melt')
base_year_gen = base_year_gen.melt(id_vars = id_vars, 
                                   value_vars = value_vars, 
                                   var_name = "Variable",
                                   value_name = "Value")

# assign units 
base_year_gen["Unit"] = base_year_gen["Variable"].map(variable_unit_map)

 

#endregion 
#############################################################################
#region OUTPUT # finalise the variables we want and add to data_intermediate 
#############################################################################

output_name = "base_year_electricity_supply.csv"

print(f"Saving {output_name} to data_intermediate")

base_year_gen.to_csv(f"{output_location}/{output_name}", index = False, encoding = "utf-8-sig")

#endregion 
#############################################################################
#region CHECKS 
#############################################################################

if(show_checks):
    print("GENERATION CHECKS:")
    print(gen_comparison)
    print("CAPACITY CHECKS:")
    print(cap_comparison)
    print("GENERIC PLANTS GENERATED:")
    print(generic_generation)
    # extra gas checks 
    gas_test = base_year_gen[base_year_gen["FuelType"] == "Gas"]
    # print("Extra gas checks:")
    # print(gas_test)



gen_comparison.to_csv(f"{check_location}/check_ele_gen_calibration.csv", index = False)
cap_comparison.to_csv(f"{check_location}/check_base_year_ele_cap_calibration.csv", index = False)
generic_generation.to_csv(f"{check_location}/check_ele_gen_generated_generics.csv", index = False)



#endregion