"""
New Tech Data manipulation
new_tech_data.py

This scripts purpose is to build a table of data for the new electricity generating technology that is found in the MBIE GenStack data.
The data also contains some  offshore wind data from NREL and uses the learning curves obtained from the NREL ATB data to produce learning curves 
for the CAPEX and FOM of new solar, wind, and geothermal.

It also has data on the capacities, whether the plant has a fixed or earliest commissioning year or if it is able to be commissioned at any time. 

"""
# this is just so I can work out the MBIE gen stack data transformations before I put it into the calculation script whoop

import sys 
import pandas as pd
import numpy as np
import os 
import logging
import matplotlib.pyplot as plt


# set log level for message outputs 
logging.basicConfig(level=logging.INFO) 
#Getting Custom Libraries
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, "../..", "library"))
from filepaths import DATA_RAW, DATA_INTERMEDIATE
from dataprep import *

#Loading the relevant csvs
genstack_file = pd.read_csv(f"{DATA_INTERMEDIATE}/stage_1_external_data/mbie/gen_stack.csv")
NREL_CAPEX = pd.read_csv(f"{DATA_RAW}/external_data/NREL/CAPEX_Tech.csv")
NREL_FOM = pd.read_csv(f"{DATA_RAW}/external_data/NREL/FOM_Tech.csv")
statsNZ_file = pd.read_csv(f"{DATA_RAW}/external_data/StatsNZ/Census_Total_dwelling_count_and_change_by_region_20132023.csv")
region_to_island = pd.read_csv(f"{DATA_RAW}/concordances/region_island_concordance.csv")
region_list = region_to_island['Region'].tolist()

# Setting the output loaction
output_location = f"{DATA_INTERMEDIATE}/stage_3_scenarios"
os.makedirs(output_location, exist_ok = True)

# this splits out the reference scenario as the other MBIE scenarios as these are just scaled from the reference
Reference_Genstack = filter_csv_by_one_column(genstack_file, "Scenario", "Reference", output_filtered_file=None)

Reference_Genstack = remove_rows_by_column_value(Reference_Genstack, "Status", "Current")

Reference_Genstack = assign_type(Reference_Genstack, "Fixed Commissioning Year", "Earliest Commissioning Year")

Reference_Genstack['Commissioning Year'] = Reference_Genstack['Fixed Commissioning Year'].fillna(0) + Reference_Genstack['Earliest Commissioning Year'].fillna(0)

cols_to_drop = ['Fixed Commissioning Year', 'Earliest Commissioning Year']
Reference_Genstack = Reference_Genstack.drop(columns=[col for col in cols_to_drop if col in Reference_Genstack.columns])

#Separating the plants we want at a fixed cost and those we dont, (filters is the ones at fixed cost)
filters = {
    "Status" : ["Fully consented", "Under construction"],
    "Tech" : ["Wind", "Solar", "Geo"]
}

fixed_cost, varied_cost = filter_csv_by_multiple_columns(Reference_Genstack, filters, output_filtered_file=None, output_excluded_file=None)

#Here we are filtering so that we have only the tech with commisioning years later than 2030 or with no commisioning year in the varied costs
varied_cost, fixed_cost = filter_and_move_rows(varied_cost, fixed_cost, "Commissioning Year", threshold=2030)

# this filters out all of the things we want to keep in varied costs and moving ones we don't want into fixed costs
keep_values = ["Solar", "Wind", "Geo"]
varied_cost, fixed_cost = filter_by_column(varied_cost, "Tech", keep_values, fixed_cost)

#Then we want to apply the NREL learning curves to the according varied cost

#In TIMES2.0 they used the moderate data from NREL to model the Moderate scenario
filters_Moderate = {
    "Technology": ["Land-Based Wind - Class 2 - Technology 1",
                  "Utility PV - Class 1", "Geothermal - Hydro / Flash"],  
    "Scenario": "Moderate" 
}

Moderate_NREL_CAPEX, excluded_Moderate_curves = filter_csv_by_multiple_columns(NREL_CAPEX, filters_Moderate, output_filtered_file=None, output_excluded_file=None)


#For Conservative they used the conservative scenario (slower decrease in costs over time)
filters_Conservative = {
    "Technology": ["Land-Based Wind - Class 2 - Technology 1",
                  "Utility PV - Class 1", "Geothermal - Hydro / Flash"],  
    "Scenario": "Conservative" 
}

Conservative_NREL_CAPEX, excluded_Conservative_curves = filter_csv_by_multiple_columns(NREL_CAPEX, filters_Conservative, output_filtered_file=None, output_excluded_file=None)

# removing the scenario and 2022 columns as these are not needed in calcs (want a base year of 2023 to match MBIE data) :)
columns_to_remove = ["Scenario", "2022"]
Moderate_NREL_CAPEX = remove_columns(Moderate_NREL_CAPEX, columns_to_remove)

Conservative_NREL_CAPEX = remove_columns(Conservative_NREL_CAPEX, columns_to_remove)

# Calculate the percentage indices

Moderate_idx = divide_from_specific_column(Moderate_NREL_CAPEX, base_column = "2023", row_conditions = {})

Conservative_idx = divide_from_specific_column(Conservative_NREL_CAPEX, base_column = "2023", row_conditions = {})

Moderate_idx = Moderate_idx.rename(columns={'Technology': 'Tech'})
Conservative_idx = Conservative_idx.rename(columns={'Technology': 'Tech'})

# gives you the indices of the rows that we want used for the mapping_dict 
solar_Moderate = Moderate_idx[Moderate_idx["Tech"] == "Utility PV - Class 1"].index[0]
wind_Moderate = Moderate_idx[Moderate_idx["Tech"] == "Land-Based Wind - Class 2 - Technology 1"].index[0]
geo_Moderate = Moderate_idx[Moderate_idx["Tech"] == "Geothermal - Hydro / Flash"].index[0]
#set up to combine and multiply the two dataframes
selected_columns = ["Plant", "TechName", "Substation", "Region", "Status", "Type","Commissioning Year"]
multiply_column = "Capital cost (NZD/kW)"
option_column = "Tech"
mapping_dict_Moderate = {
    "Solar" : solar_Moderate,
    "Wind" : wind_Moderate,
    "Geo" : geo_Moderate
}

label_from_df2 = Moderate_idx.columns.tolist()
constant_col1 = "Connection cost (NZD $m)"
constant_col2 = "Capacity (MW)"

Moderate_idx = Moderate_idx.apply(pd.to_numeric, errors="coerce")

Moderate_CAPEX = combine_and_multiply_by_row(varied_cost, Moderate_idx, selected_columns, multiply_column, option_column, mapping_dict_Moderate, label_from_df2, constant_col1, constant_col2)
Moderate_CAPEX = remove_columns(Moderate_CAPEX, "Tech") # for some reason it added an extra tech column that made no sense to me so this just gets rid of it, the calulcationss are correct now tho woooooooooo

# first just finding the indices of the rows we want to use
solar_Conservative = Conservative_idx[Conservative_idx["Tech"] == "Utility PV - Class 1"].index[0]
wind_Conservative = Conservative_idx[Conservative_idx["Tech"] == "Land-Based Wind - Class 2 - Technology 1"].index[0]
geo_Conservative = Conservative_idx[Conservative_idx["Tech"] == "Geothermal - Hydro / Flash"].index[0]
mapping_dict_Conservative = {
    "Solar" : solar_Conservative,
    "Wind" : wind_Conservative,
    "Geo" : geo_Conservative
}

Conservative_idx = Conservative_idx.apply(pd.to_numeric, errors="coerce")
Conservative_CAPEX = combine_and_multiply_by_row(varied_cost, Conservative_idx, selected_columns, multiply_column, option_column, mapping_dict_Conservative, label_from_df2, constant_col1, constant_col2)
Conservative_CAPEX = remove_columns(Conservative_CAPEX, "Tech") # for some reason it added an extra tech column that made no sense to me so this just gets rid of it, the calulcationss are correct now tho woooooooooo


### FOM time 
#Moving the wanted FOM data to it's own dataframe
Moderate_NREL_FOM, ex_FOM_Moderate_curves = filter_csv_by_multiple_columns(NREL_FOM, filters_Moderate, output_filtered_file=None, output_excluded_file=None)


Conservative_NREL_FOM, ex_FOM_Conservative_curves = filter_csv_by_multiple_columns(NREL_FOM, filters_Conservative, output_filtered_file=None, output_excluded_file=None)



# removing the scenario and 2022 columns as these are not needed in calcs :)

Moderate_NREL_FOM = remove_columns(Moderate_NREL_FOM, columns_to_remove)

Conservative_NREL_FOM = remove_columns(Conservative_NREL_FOM, columns_to_remove)

#Creating the percentage indices for FOMs
Moderate_FOM_idx = divide_from_specific_column(Moderate_NREL_FOM, base_column = "2023", row_conditions = {})

Conservative_FOM_idx = divide_from_specific_column(Conservative_NREL_FOM, base_column = "2023", row_conditions = {})

#Prepping for combining and multiplying the NREL and MBIE dataframes
Moderate_FOM_idx = Moderate_FOM_idx.rename(columns={'Technology': 'Tech'})
Conservative_FOM_idx = Conservative_FOM_idx.rename(columns={'Technology': 'Tech'})

multiply_column_FOM = "Fixed operating costs (NZD/kW/year)"

Moderate_FOM_idx = Moderate_FOM_idx.apply(pd.to_numeric, errors="coerce")

Moderate_FOM = combine_and_multiply_FOM(varied_cost, Moderate_FOM_idx, selected_columns, multiply_column_FOM, option_column, mapping_dict_Moderate, label_from_df2, transform_func=None)
Moderate_FOM = remove_columns(Moderate_FOM, "Tech") # for some reason it added an extra tech column that made no sense to me so this just gets rid of it, the calulcationss are correct now tho woooooooooo

Conservative_FOM_idx = Conservative_FOM_idx.apply(pd.to_numeric, errors="coerce")

Conservative_FOM = combine_and_multiply_FOM(varied_cost, Conservative_FOM_idx, selected_columns, multiply_column_FOM, option_column, mapping_dict_Conservative, label_from_df2, transform_func=None)
Conservative_FOM = remove_columns(Conservative_FOM, "Tech") # for some reason it added an extra tech column that made no sense to me so this just gets rid of it, the calulcationss are correct now tho woooooooooo

###############     Offshore wind (fixed and floating) additions to table 
# First getting the data from the NREL csvs for CAPEX
filters_offshore_Moderate = {
    "Technology": ["Offshore Wind - Class 1", "Offshore Wind - Class 8"],  
    "Scenario": "Moderate" 
}

Moderate_offshore_CAPEX, excluded_Moderate_curves = filter_csv_by_multiple_columns(NREL_CAPEX, filters_offshore_Moderate, output_filtered_file=None, output_excluded_file=None)

filters_offshore_Conservative = {
    "Technology": ["Offshore Wind - Class 1", "Offshore Wind - Class 8"],  
    "Scenario": "Conservative" 
}

Conservative_offshore_CAPEX, excluded_Conservative_curves = filter_csv_by_multiple_columns(NREL_CAPEX, filters_offshore_Conservative, output_filtered_file=None, output_excluded_file=None)


#removing unwanted columns from the dataframes (columns_to_remove was defined earlier in the script)
Moderate_offshore_CAPEX = remove_columns(Moderate_offshore_CAPEX, columns_to_remove)
Conservative_offshore_CAPEX = remove_columns(Conservative_offshore_CAPEX, columns_to_remove)

CPI, cost_conversion = 1.05, 0.62 # 5% CPI, USD to NZD
Moderate_converted_CAPEX = clean_and_multiply(Moderate_offshore_CAPEX, CPI, cost_conversion)

Conservative_converted_CAPEX = clean_and_multiply(Conservative_offshore_CAPEX, CPI, cost_conversion)

#Now to find the offshore FOMs
Moderate_offshore_FOM, excluded_Moderate_curves = filter_csv_by_multiple_columns(NREL_FOM, filters_offshore_Moderate, output_filtered_file=None, output_excluded_file=None)
Conservative_offshore_FOM, excluded_Moderate_curves = filter_csv_by_multiple_columns(NREL_FOM, filters_offshore_Conservative, output_filtered_file=None, output_excluded_file=None)

#removing unwanted columns from the dataframes (columns_to_remove was defined earlier in the script)
Moderate_offshore_FOM = remove_columns(Moderate_offshore_FOM, columns_to_remove)
Conservative_offshore_FOM = remove_columns(Conservative_offshore_FOM, columns_to_remove)

#Final conversion from USD to NZD including CPI
Moderate_converted_FOM = clean_and_multiply(Moderate_offshore_FOM, CPI, cost_conversion)
Conservative_converted_FOM = clean_and_multiply(Conservative_offshore_FOM, CPI, cost_conversion)

#Want to add columns so that the data is easy to append into the main dataframe

status_offshore = ["Generic", "Generic"]
techname_offshore = ["Fixed Offshore Wind", "Floating Offshore Wind"]

Moderate_converted_CAPEX.insert(1, "Status", status_offshore)
Moderate_converted_CAPEX.insert(2,"TechName", techname_offshore)

Conservative_converted_CAPEX.insert(1, "Status", status_offshore)
Conservative_converted_CAPEX.insert(2,"TechName", techname_offshore)

Moderate_converted_FOM.insert(1, "Status", status_offshore)
Moderate_converted_FOM.insert(2,"TechName", techname_offshore)

Conservative_converted_FOM.insert(1, "Status", status_offshore)
Conservative_converted_FOM.insert(2,"TechName", techname_offshore)

#Just relabeling to match the main Data Frames
Moderate_converted_CAPEX = Moderate_converted_CAPEX.rename(columns={'Technology': 'Plant'})
Conservative_converted_CAPEX = Conservative_converted_CAPEX.rename(columns={'Technology': 'Plant'})
Moderate_converted_FOM = Moderate_converted_FOM.rename(columns={'Technology': 'Plant'})
Conservative_converted_FOM = Conservative_converted_FOM.rename(columns={'Technology': 'Plant'})


labels = ['Taranaki', 'Waikato', 'Southland']

# List of original DataFrames
original_dfs = [Moderate_converted_CAPEX, Conservative_converted_CAPEX, Moderate_converted_FOM, Conservative_converted_FOM]

new_columns = {
    'Type': 'Earliest Year',
    'Commissioning Year': '2035'
}

# Add columns to each DataFrame in the list
for df in original_dfs:
    for col_name, value in new_columns.items():
        df[col_name] = value

# Store the result for each original DataFrame
merged_copies = []

for i, df in enumerate(original_dfs):
    copies = []
    for label in labels:
        temp = df.copy()
        temp['Region'] = label
        copies.append(temp)
    merged_df = pd.concat(copies, ignore_index=True)
    merged_copies.append(merged_df)

#appending these frames into the main ones

Moderate_CAPEX = pd.concat([Moderate_CAPEX, merged_copies[0]], ignore_index = True)
Conservative_CAPEX = pd.concat([Conservative_CAPEX, merged_copies[1]], ignore_index = True)
Moderate_FOM = pd.concat([Moderate_FOM, merged_copies[2]], ignore_index = True)
Conservative_FOM = pd.concat([Conservative_FOM, merged_copies[3]], ignore_index = True)

#Adding in needed info for the final data frame
Moderate_CAPEX[["Scenario", "Variable", "Unit"]] = ["Moderate", "CAPEX", "$/kW"]
Conservative_CAPEX[["Scenario", "Variable", "Unit"]] = ["Conservative", "CAPEX", "$/kW"]
Moderate_FOM[["Scenario", "Variable", "Unit"]] = ["Moderate", "FOM", "$/kW"]
Conservative_FOM[["Scenario", "Variable", "Unit"]] = ["Conservative", "FOM", "$/kW"]

#merging all of the variable data
merged_df = pd.concat([Moderate_CAPEX, Conservative_CAPEX, Moderate_FOM, Conservative_FOM], ignore_index = True)

#moving some of the columns
moves = [("Scenario", 0), ("Variable", 8),("Unit", 9)]
merged_df = move_columns(merged_df, moves)

years_used = ['2023', '2024','2025', '2026', '2027', '2028', '2029', '2030', '2031', '2032', '2033','2034', '2035', '2036', '2037',
                                 '2038', '2039', '2040', '2041', '2042','2043', '2044', '2045', '2046', '2047', '2048', '2049', '2050']
#Melting so that there is 1 data point per row
long_df = pd.melt(merged_df,
                  id_vars = ["Scenario", "Plant", "TechName", "Substation", "Region", "Status", "Type", "Commissioning Year", "Variable", "Unit"],
                  value_vars = years_used,
                                 var_name = "Year",
                                 value_name= "Value")

 
#Adding in the data from fixed_costs

fixed_cost["CAPEX"] = fixed_cost["Total Capital costs (NZD $m)"]/fixed_cost["Capacity (MW)"]*1000
fixed_cost = fixed_cost.drop(['Total Capital costs (NZD $m)', 'Scenario'], axis=1)

#putting in Moderate/Conservative scenarios
Moderate_fixed_cost = fixed_cost.copy()
Conservative_fixed_cost = fixed_cost.copy()
Moderate_fixed_cost['Scenario'] = "Moderate"
Conservative_fixed_cost['Scenario'] = 'Conservative'
new_fixed_cost = pd.concat([Moderate_fixed_cost, Conservative_fixed_cost], ignore_index = True)

new_fixed_cost = new_fixed_cost.rename(columns={
    'Capacity (MW)': 'Capacity',
    'Heat Rate (GJ/GWh)': 'Heat Rate',
    'Variable operating costs (NZD/MWh)': 'VOC',
    'Fixed operating costs (NZD/kW/year)': 'FOM',
    'Fuel delivery costs (NZD/GJ)': 'FDC'
})

long_fixed_cost = pd.melt(new_fixed_cost, 
                          id_vars = ["Scenario", "Plant", "TechName", "Substation", "Region", "Status", "Type", "Commissioning Year"],
                          value_vars = ['Capacity', 'Heat Rate',
                                        'VOC',
                                        'FOM', 'FDC',
                                        'CAPEX'],
                                        var_name = "Variable",
                                        value_name = "Value")

#For the unit column (All of this is from the MBIE data)
label_map = {
    'Capacity' : 'MW',
    'Heat Rate' : 'GJ/GWh',
    'VOC' : '$/MWh',
    'FOM' : '$/kW',
    'FDC' : '$/GJ',
    'CAPEX' : '$/kW'
}
long_fixed_cost['Unit'] = long_fixed_cost['Variable'].map(label_map).fillna('Other')

long_fixed_cost['Year'] = long_fixed_cost['Commissioning Year']
#Replaces all 0 values with 2023 as base year
long_fixed_cost['Year'] = long_fixed_cost['Year'].replace(0,2023)
long_fixed_cost = move_columns(long_fixed_cost, [('Unit', 9), ("Year", 10)])

# Adding in the Capacities of each of the varied cost plants
varied_cost_capacity = varied_cost[['Plant', 'Status', 'TechName',
       'Substation', 'Region', 'Capacity (MW)', 'Type', 'Commissioning Year']].copy()

varied_cost_capacity = varied_cost_capacity.rename(columns = {'Capacity (MW)': 'Value'})
varied_cost_capacity['Unit'] = 'MW'
varied_cost_capacity['Year'] = varied_cost_capacity['Commissioning Year']
#Replaces all 0 values with 2023 as a default year
varied_cost_capacity['Year'] = varied_cost_capacity['Year'].replace(0,2023)

#Adding in the scenario names
scenarios = ['Moderate', 'Conservative']
new_varied_cap = duplicate_rows_with_new_column(varied_cost_capacity, 'Scenario', scenarios)
new_varied_cap['Variable'] = 'Capacity'

#reordering the columns to match other frames
new_varied_cap = new_varied_cap[['Scenario', 'Plant', 'TechName', 'Substation', 'Region', 'Status',
                                   'Type', 'Commissioning Year', 'Variable', 'Unit', 'Year', 'Value']]

#Adding in rooftop solar costs/capacities
#first for Capacities we have the statsNZ data fro the number of households per region and we assume that about 80% are suitable for rooftop solar and 
#we also assume a capacity of 9kW per roof. First we need to filter the csv for only 2023 and only the regions in nz.
Dwelling_number = statsNZ_file[statsNZ_file['Census year'] == '2023']
Dwelling_number = Dwelling_number[~Dwelling_number['Region'].isin(['North Island', 'South Island', 'Chatham Islands', 'New Zealand'])]

#removing columns that are not needed
Res_Solar_Cap = Dwelling_number[['Region', 'Value']].copy()
# Want to then multiply the number of houses by 0.8 (80%) and by 9kW to find regional capacities and divide by 1000kW/MW
Res_Solar_Cap['Value'] =  Res_Solar_Cap['Value'] * 0.8 * 9/1000
Res_Solar_Cap[['Variable', 'Year', 'Plant']] = ['Capacity', 2023, 'Generic Residential Distributed Solar']
Res_Solar_Cap = duplicate_rows_with_new_column(Res_Solar_Cap, 'Scenario', scenarios)

# Now we want to bring in the cost curves for CAPEX and FOMs, First CAPEX.
sol_CAPEX, sol_FOM = 2200, 30

NREL_ResSol_CAPEX = NREL_CAPEX[(NREL_CAPEX['Technology'] == 'Residential PV - Class 1') & (NREL_CAPEX['Scenario'].isin(['Moderate', 'Conservative']))]
NREL_ResSol_CAPEX =NREL_ResSol_CAPEX.drop(columns = ['2022'])
ResSol_CAPEX_PI = divide_from_specific_column(NREL_ResSol_CAPEX, base_column = "2023", row_conditions = {})


ResSol_CAPEX = ResSol_CAPEX_PI.copy()
#making sure all number columns are numeric to do calcs
for col in ResSol_CAPEX.columns:
    try:
        ResSol_CAPEX[col] = pd.to_numeric(ResSol_CAPEX[col])
    except ValueError:
        pass # Skip columns that can't be converted
numeric_cols = ResSol_CAPEX.select_dtypes(include='number').columns
#applying curve
ResSol_CAPEX[numeric_cols] = ResSol_CAPEX[numeric_cols] * sol_CAPEX
ResSol_CAPEX['Variable'] = 'CAPEX'

#Same thing but for FOMs
NREL_ResSol_FOM = NREL_FOM[(NREL_FOM['Technology'] == 'Residential PV - Class 1') & (NREL_FOM['Scenario'].isin(['Moderate', 'Conservative']))]
NREL_ResSol_FOM =NREL_ResSol_FOM.drop(columns = ['2022'])
ResSol_FOM_PI = divide_from_specific_column(NREL_ResSol_CAPEX, base_column = "2023", row_conditions = {})

ResSol_FOM = ResSol_FOM_PI.copy()
#making sure all number columns are numeric to do calcs
for col in ResSol_FOM.columns:
    try:
        ResSol_FOM[col] = pd.to_numeric(ResSol_FOM[col])
    except ValueError:
        pass # Skip columns that can't be converted
numeric_cols = ResSol_FOM.select_dtypes(include='number').columns
#applying curve
ResSol_FOM[numeric_cols] = ResSol_FOM[numeric_cols] * sol_FOM
ResSol_FOM['Variable'] = 'FOM'

ResSol_costs = pd.concat([ResSol_CAPEX, ResSol_FOM], ignore_index = True)

ResSol_costs = pd.melt(ResSol_costs.copy(),
                       id_vars = ['Scenario', 'Technology', 'Variable'],
                       value_vars = years_used,
                       var_name = 'Year',
                       value_name = 'Value')

ResSol_costs.rename(columns={'Technology': 'Plant'}, inplace=True)
ResSol_costs['Plant'] = 'Generic Residential Distributed Solar'


ResSol_costs = duplicate_rows_with_new_column(ResSol_costs, 'Region', region_list)

ResSol_data = pd.concat([ResSol_costs, Res_Solar_Cap], ignore_index = True)
ResSol_data['Unit'] = ResSol_data['Variable'].map(label_map).fillna('Other')
ResSol_data[['TechName', 'Type', 'Commissioning Year', 'Substation', 'Status']] = ['Residential Distributed Solar', 'Any Year', np.nan, np.nan, 'Generic']

final_data = pd.concat([long_df, new_varied_cap, long_fixed_cost, ResSol_data], ignore_index = True)

#replacing 0's with NaN
final_data = final_data.replace(0, np.nan)

#Removes all the unwanted data points as these points occur before the earliest commissioning year
final_data = conditional_row_filter(final_data, 'Type', 'Earliest Year', 'Commissioning Year', 'Year')

#Adding in the Capacities for the offshore wind
final_data = duplicate_and_modify_rows_two_conditions(final_data,'TechName', ['Floating Offshore Wind', 'Fixed Offshore Wind'],
                                                    'Variable', 'CAPEX', 'Variable', 'Capacity', 'Unit', 'MW', 'Value')

#These values are from NIR NZ offshore wind
value_map_fixed = {'Taranaki': 3800, 'Waikato': 3000, 'Southland': 1000}
final_data = assign_value_with_multiple_conditions(final_data, 'TechName', 'Fixed Offshore Wind', 'Variable', 'Capacity',
                                                    'Region', 'Value', value_map_fixed)

value_map_floating = {'Taranaki': 1900, 'Waikato': 1000}
final_data = assign_value_with_multiple_conditions(final_data, 'TechName', 'Floating Offshore Wind', 'Variable', 'Capacity',
                                                    'Region', 'Value', value_map_floating)
#As we assume no floating offshore wind in Southland we want to remove those rows
final_data = final_data[~((final_data['TechName'] == 'Floating Offshore Wind') & (final_data['Region'] == 'Southland'))]

island_mapping = dict(zip(region_to_island['Region'], region_to_island['Island']))
final_data.insert(4, 'Island', final_data['Region'].map(island_mapping).fillna('Other'))

output_name = "new_tech_data.csv"

print(f"Saving {output_name} to data_intermediate")

final_data.to_csv(f"{output_location}/{output_name}", index = False, encoding = "utf-8-sig")