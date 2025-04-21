"""
New Tech Data manipulation
new_tech_data.py

This scripts purpose is to build a table of data for the new electricity generating technology that is found in the MBIE GenStack data.
The data also contains some  offshore wind data from NREL and uses the learning curves obtained from the NREL ATB data to produce learning curves 
for the CAPEX and FOM of new solar, wind, and geothermal.

It also has data on the capacities, whether the plant has a fixed or earliest commissioning year or if it is able to be commissioned at any time. 

"""
################ Set up ################
import sys 
import pandas as pd
import numpy as np
import os 
import logging
import matplotlib.pyplot as plt

# set log level for message outputs 
logging.basicConfig(level=logging.INFO) 
pd.set_option('future.no_silent_downcasting', True)
#Getting Custom Libraries
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, "../..", "library"))
from filepaths import DATA_RAW, DATA_INTERMEDIATE
from dataprep import *
from new_tech_functions import *

#Loading the relevant csvs
genstack_file = pd.read_csv(f"{DATA_INTERMEDIATE}/stage_1_external_data/mbie/gen_stack.csv")
nrel_capex = pd.read_csv(f"{DATA_RAW}/external_data/NREL/CAPEX_Tech.csv")
nrel_fom = pd.read_csv(f"{DATA_RAW}/external_data/NREL/FOM_Tech.csv")
statsNZ_file = pd.read_csv(f"{DATA_RAW}/external_data/StatsNZ/Census_Total_dwelling_count_and_change_by_region_20132023.csv")
region_to_island = pd.read_csv(f"{DATA_RAW}/concordances/region_island_concordance.csv")
region_list = region_to_island['Region'].tolist()
new_tech = pd.read_csv(f"{DATA_RAW}/coded_assumptions/electricity_generation/new_tech.csv")
tracked_solar = pd.read_csv(f"{DATA_RAW}/coded_assumptions/electricity_generation/Tracked_solar_plants.csv")

# Setting the output loaction
output_location = f"{DATA_INTERMEDIATE}/stage_3_scenarios"
os.makedirs(output_location, exist_ok = True)

#Set base year
base_year = 2023
years_used = list(range(base_year, 2051))

#scenarios
scenarios = ['Advanced', 'Moderate', 'Conservative']
#region GENSTACK SORTING
#Sorting the GenStack info into what is set to be a fixed cost and what is set as a varied cost

#This splits out the reference scenario as the other MBIE scenarios (can be changed depending on which scenario is wanted)
reference_genstack = filter_df_by_one_column(genstack_file, "Scenario", "Reference")
#removing unwanted columns and assigning the type of commissioning year and merging the commissioning year columns into one
reference_genstack = reference_genstack[reference_genstack['Status'] != 'Current']
reference_genstack = assign_type(reference_genstack, "Fixed Commissioning Year", "Earliest Commissioning Year")
reference_genstack['Commissioning Year'] = reference_genstack['Fixed Commissioning Year'].fillna(0) + reference_genstack['Earliest Commissioning Year'].fillna(0)

#dropping the now unwanted columns
cols_to_drop = ['Scenario', 'Fixed Commissioning Year', 'Earliest Commissioning Year']
reference_genstack = reference_genstack.drop(columns=[col for col in cols_to_drop if col in reference_genstack.columns])

#Separating the plants we want at a fixed cost and those we dont, filters moves ones that we know should have a fixed cost
filters = {
    "Status" : ["Fully consented", "Under construction"],
    "Tech" : ["Wind", "Solar", "Geo"]
}

fixed_cost, varied_cost = filter_df_by_multiple_columns(reference_genstack, filters)
#Filtering so that we have only the tech with commisioning years later than 2030 or with no commisioning year in the varied costs
varied_cost, fixed_cost = filter_and_move_rows(varied_cost, fixed_cost, "Commissioning Year", threshold=2030)

# this filters out all of the things we want to keep in varied costs and moving ones we don't want into fixed costs
keep_values = ["Solar", "Wind", "Geo"]
varied_cost, fixed_cost = filter_by_column(varied_cost, "Tech", keep_values, fixed_cost)
#endregion
#region LEARNING CURVES
################ Applying learning curves to the MBIE solar, wind, and geothermal plants (CAPEX) ################

#Extracting the NREL CAPEX data for the technologies
filters = {
    "Technology": ["Land-Based Wind - Class 2 - Technology 1",
                  "Utility PV - Class 1", "Geothermal - Hydro / Flash"]}

nrel_capex, ex_nrel_capex = filter_df_by_multiple_columns(nrel_capex, filters)
nrel_capex = nrel_capex.reset_index()

#Removing unwanted columns before the calculations mainly just the data for years less than the base year

nrel_capex.columns = [convert_label(col) for col in nrel_capex.columns]
nrel_capex = nrel_capex.loc[:, [
    col for col in nrel_capex.columns
    if not isinstance(col, int) or col >= base_year
]]


nrel_capex_idx = nrel_capex.copy()
# Calculate the percentage indices for each scenario
nrel_capex_idx = divide_from_specific_column(nrel_capex, base_year, row_conditions = {})

#Renaming the Technology column to Tech to match with the MBIE dataframe
tech_map = {"Utility PV - Class 1": "Solar",
            "Land-Based Wind - Class 2 - Technology 1": "Wind",
            "Geothermal - Hydro / Flash": "Geo"
            }
nrel_capex_idx['Tech'] = nrel_capex_idx['Technology'].map(tech_map)

merged_nrel_capex = pd.merge(varied_cost,nrel_capex_idx, on = 'Tech', how = 'inner')
merged_nrel_capex['Connection Cost per kW'] = merged_nrel_capex['Connection cost (NZD $m)'] / merged_nrel_capex['Capacity (MW)']*1000



for col in years_used:
    merged_nrel_capex[col] = merged_nrel_capex['Capital cost (NZD/kW)'] * merged_nrel_capex[col] + merged_nrel_capex['Connection Cost per kW']
merged_nrel_capex['Variable'] = 'CAPEX'

################ Applying learning curves to the MBIE solar, wind, and geothermal plants (FOMs) ################
#Moving the wanted NREL FOM Solar, wind, and geothermal data into a separate frame
nrel_fom, ex_fom_curves = filter_df_by_multiple_columns(nrel_fom, filters)
nrel_fom = nrel_fom.reset_index()

nrel_fom.columns = [convert_label(col) for col in nrel_fom.columns]
nrel_fom = nrel_fom.loc[:, [
    col for col in nrel_fom.columns
    if not isinstance(col, int) or col >= base_year
]]

# Calculate the percentage indices for each scenario
nrel_fom_idx = divide_from_specific_column(nrel_fom, base_year, row_conditions = {})

#Renaming the Technology column to Tech to match with the MBIE dataframe
nrel_fom_idx['Tech'] = nrel_fom_idx['Technology'].map(tech_map)

merged_nrel_fom = pd.merge(varied_cost,nrel_fom_idx, on = 'Tech', how = 'inner')

for col in years_used:
    merged_nrel_fom[col] = merged_nrel_fom['Fixed operating costs (NZD/kW/year)'] * merged_nrel_fom[col]

merged_nrel_fom['Variable'] = 'FOM'
# #endregion

################ Varied cost plant capacities ################
varied_cost_capacity = varied_cost[['Plant', 'Status', 'TechName',
       'Substation', 'Region', 'Capacity (MW)', 'Type', 'Commissioning Year']].copy()

varied_cost_capacity = varied_cost_capacity.rename(columns = {'Capacity (MW)': 'Value'})
varied_cost_capacity['Unit'] = 'MW'
varied_cost_capacity['Year'] = varied_cost_capacity['Commissioning Year']

#Adding in the scenario names
new_varied_cap = duplicate_rows_with_new_column(varied_cost_capacity, 'Scenario', scenarios)
new_varied_cap['Variable'] = 'Capacity'

#region OFFSHORE WIND
################     Offshore wind (fixed and floating) ################
# First getting the data from the NREL csvs for CAPEX
filters_offshore = {
    "Technology": ["Offshore Wind - Class 1", "Offshore Wind - Class 8"]}

nrel_offshore_capex, ex_nrel_capex = filter_df_by_multiple_columns(ex_nrel_capex, filters_offshore)

#removing any data from years before the base year
nrel_offshore_capex.columns = [convert_label(col) for col in nrel_offshore_capex.columns]
nrel_offshore_capex = nrel_offshore_capex.loc[:, [
    col for col in nrel_offshore_capex.columns
    if not isinstance(col, int) or col >= base_year
]]

#As we want a base year of 2023 we want to adjust the NREL data which has a base year of 2022 for CPI of about 5% and convert from USD to NZD
CPI, COST_CONVERSION = 1.05, 0.62 # 5% CPI, USD to NZD
for col in years_used:
        nrel_offshore_capex[col] = nrel_offshore_capex[col].replace(r'[\$,]', '', regex=True).astype(float)
        nrel_offshore_capex[col] = nrel_offshore_capex[col] * CPI / COST_CONVERSION

nrel_offshore_capex['Variable'] = 'CAPEX'

# #Now to find the offshore FOMs, first the NREL data
nrel_offshore_fom, filtered_curves = filter_df_by_multiple_columns(nrel_fom, filters_offshore)


#removing any data from years before the base year
nrel_offshore_fom.columns = [convert_label(col) for col in nrel_offshore_fom.columns]
nrel_offshore_fom = nrel_offshore_fom.loc[:, [
    col for col in nrel_offshore_fom.columns
    if not isinstance(col, int) or col >= base_year
]]

#As we want a base year of 2023 we want to adjust the NREL data which has a base year of 2022 for CPI of about 5% and convert from USD to NZD
for col in years_used:
        nrel_offshore_fom[col] = nrel_offshore_fom[col].replace(r'[\$,]', '', regex=True).astype(float)
        nrel_offshore_fom[col] = nrel_offshore_fom[col] * CPI / COST_CONVERSION
nrel_offshore_fom['Variable'] = 'FOM'

nrel_offshore = pd.concat([nrel_offshore_capex, nrel_offshore_fom], ignore_index = True)
nrel_offshore.rename(columns = {'Technology': 'Plant'}, inplace = True)
#mapping technology to the status, tech, and region
map_offshore = new_tech[['Plant', 'TechName', 'Status', 'Region', 'Type', 'Commissioning Year']]

nrel_offshore = pd.merge(nrel_offshore, map_offshore, on = 'Plant', how ='inner')

offshore_capacity_filters = {'Plant': ["Offshore Wind - Class 1", "Offshore Wind - Class 8"]}
offshore_capacities, excluded = filter_df_by_multiple_columns(new_tech, offshore_capacity_filters) 

offshore_capacities = duplicate_rows_with_new_column(offshore_capacities, 'Scenario', scenarios)
# ################ Merging the varied costs and offshore wind data ################

#merging all of the variable data
merged_df = pd.concat([merged_nrel_capex, merged_nrel_fom, nrel_offshore], ignore_index = True)
unit_map = {
    'Capacity' : 'MW',
    'Heat Rate' : 'GJ/GWh',
    'VOC' : '$/MWh',
    'FOM' : '$/kW',
    'FDC' : '$/GJ',
    'CAPEX' : '$/kW'
}
merged_df['Unit'] = merged_df['Variable'].map(unit_map)
#Melting so that there is 1 data point per row
long_df = pd.melt(merged_df,
                  id_vars = ["Scenario", "Plant", "TechName", "Substation", "Region", "Status", "Type", "Commissioning Year", "Variable", "Unit"],
                  value_vars = years_used,
                  var_name = "Year",
                  value_name= "Value")
varied_df = pd.concat([long_df, new_varied_cap, offshore_capacities], ignore_index = True)

#endregion

#region FIXED COSTS
# ################ Fixed cost data ################

#As the total capital costs include the connection cost we can just divide by the capacity of the plant to find $/kW for CAPEX
fixed_cost["CAPEX"] = fixed_cost["Total Capital costs (NZD $m)"]/fixed_cost["Capacity (MW)"]*1000
fixed_cost = fixed_cost.drop(['Total Capital costs (NZD $m)'], axis=1)

#putting in Moderate/Conservative scenarios
scenarios = ['Advanced', 'Moderate', 'Conservative']
combined_fixed_cost = duplicate_rows_with_new_column(fixed_cost, 'Scenario',scenarios)

#renaming columns from MBIE data
combined_fixed_cost = combined_fixed_cost.rename(columns={
    'Capacity (MW)': 'Capacity',
    'Heat Rate (GJ/GWh)': 'Heat Rate',
    'Variable operating costs (NZD/MWh)': 'VOC',
    'Fixed operating costs (NZD/kW/year)': 'FOM',
    'Fuel delivery costs (NZD/GJ)': 'FDC'
})

melted_fixed_cost = pd.melt(combined_fixed_cost, 
                          id_vars = ["Scenario", "Plant", "TechName", "Substation", "Region", "Status", "Type", "Commissioning Year"],
                          value_vars = ['Capacity', 'Heat Rate',
                                        'VOC',
                                        'FOM', 'FDC',
                                        'CAPEX'],
                                        var_name = "Variable",
                                        value_name = "Value")


melted_fixed_cost['Unit'] = melted_fixed_cost['Variable'].map(unit_map).fillna('Other')

melted_fixed_cost['Year'] = melted_fixed_cost['Commissioning Year']
#endregion
#region DISTRIBUTED SOLAR
################ Rooftop distributed solar costs and capacities ################
#First for Capacities we have the statsNZ data fro the number of households per region and we assume that about 80% are suitable for rooftop solar and 
#we also assume a capacity of 9kW per roof. First we need to filter the csv for only 2023 and only the regions in nz.
dwelling_number = statsNZ_file[statsNZ_file['Census year'] == '2023']
dwelling_number = dwelling_number[~dwelling_number['Region'].isin(['North Island', 'South Island', 'Chatham Islands', 'New Zealand'])]

#Copying the frame
res_solar_cap = dwelling_number[['Region', 'Value']].copy()

# Want to then multiply the number of useful household roofs of 80% and by 9kW to find regional capacities and divide by 1000kW/MW
suitable_houses = new_tech.loc[(new_tech['TechName'] == 'Residential dist solar') & (new_tech['Variable'] == 'Suitable houses'), 'Value'].iloc[0]/100# percentage of suitable houses
solar_cap = new_tech.loc[(new_tech['TechName'] == 'Residential dist solar') & (new_tech['Variable'] == 'Capacity'), 'Value'].iloc[0]#solar capacity per house

res_solar_cap['Value'] =  res_solar_cap['Value'] * suitable_houses * solar_cap
res_solar_cap[['Variable', 'Year', 'Plant']] = ['Capacity', base_year, 'Generic Residential Distributed Solar']
res_solar_cap = duplicate_rows_with_new_column(res_solar_cap, 'Scenario', scenarios)

nrel_ressol_capex = ex_nrel_capex[(ex_nrel_capex['Technology'] == 'Residential PV - Class 1')]
nrel_ressol_capex.insert(0, 'Variable', 'CAPEX')
nrel_ressol_fom = ex_fom_curves[(ex_fom_curves['Technology'] == 'Residential PV - Class 1')]
nrel_ressol_fom.insert(0, 'Variable', 'FOM')

nrel_ressol = pd.concat([nrel_ressol_capex, nrel_ressol_fom], ignore_index= True)
nrel_ressol.columns = [convert_label(col) for col in nrel_ressol.columns]
nrel_ressol = nrel_ressol.loc[:, [
    col for col in nrel_ressol.columns
    if not isinstance(col, int) or col >= base_year
]]


nrel_ressol_idx = divide_from_specific_column(nrel_ressol, base_year, row_conditions = {})
nrel_ressol_idx.rename(columns={'Technology': 'Plant'}, inplace=True)
ressol_costs = nrel_ressol_idx.merge(new_tech, on = ['Plant', 'Variable'], how = 'inner')

for col in years_used:
      ressol_costs[col] = ressol_costs[col] * ressol_costs['Value']
ressol_costs = ressol_costs.drop('Value', axis=1)

ressol_costs = pd.melt(ressol_costs.copy(),
                       id_vars = ['Plant','Scenario', 'Variable', 'Unit'],
                       value_vars = years_used,
                       var_name = 'Year',
                       value_name = 'Value')


ressol_costs['Plant'] = 'Generic Residential Distributed Solar'
ressol_costs = duplicate_rows_with_new_column(ressol_costs, 'Region', region_list)

ressol_data = pd.concat([ressol_costs, res_solar_cap], ignore_index = True)
ressol_data['Unit'] = ressol_data['Variable'].map(unit_map).fillna('Other')
ressol_data[['TechName', 'Type', 'Commissioning Year', 'Substation', 'Status']] = ['Residential Distributed Solar', 'Any Year', np.nan, np.nan, 'Generic']
#endregion
#region FINAL DF
################ Getting the final dataframe ################
final_data = pd.concat([varied_df, melted_fixed_cost, ressol_data], ignore_index = True)

#replacing 0's with NaN
final_data = final_data.replace(0, np.nan).infer_objects(copy=False)

#Removes all the unwanted data points as these points occur before the earliest commissioning year
final_data = conditional_row_filter(final_data, 'Type', 'Earliest Year', 'Commissioning Year', 'Year')

#Adding in the Capacities for the offshore wind
final_data = duplicate_and_modify_rows_two_conditions(final_data,'TechName', ['Floating Offshore Wind', 'Fixed Offshore Wind'],
                                                    'Variable', 'CAPEX', 'Variable', 'Capacity', 'Unit', 'MW', 'Value')

#Putting all regions into NI and SI 
island_mapping = dict(zip(region_to_island['Region'], region_to_island['Island']))
final_data.insert(4, 'Island', final_data['Region'].map(island_mapping).fillna('Other'))

#Tracked solar
 
final_data.loc[final_data['Plant'].isin(tracked_solar['Plant']), 'TechName'] = 'Tracked Solar'

final_data['Year'] = final_data['Year'].replace(np.nan,base_year)
output_name = "new_tech_data.csv"

print(f"Saving {output_name} to data_intermediate")

final_data.to_csv(f"{output_location}/{output_name}", index = False, encoding = "utf-8-sig")
#endregion