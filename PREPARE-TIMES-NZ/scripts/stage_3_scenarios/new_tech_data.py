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
from functions_new_tech import *

# set log level for message outputs 
logging.basicConfig(level=logging.INFO) 

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, "../..", "library"))
from filepaths import DATA_RAW, DATA_INTERMEDIATE
MBIE = f"{DATA_RAW}/external_data/mbie"
NREL = f"{DATA_RAW}/external_data/NREL"


#Loading the MBIE genstack data
GenStack = pd.read_csv("MBIE_GenStack.csv")
#loading the CAPEX data
NREL_CAPEX = pd.read_csv(f"{NREL}/CAPEX_Tech.csv")
#Loading the FOM data from the NREL database
NREL_FOM = pd.read_csv("FOM_Tech.csv")


output_location = f"{DATA_INTERMEDIATE}/stage_3_scenarios"
os.makedirs(output_location, exist_ok = True)



# this splits out the reference scenario as the other MBIE scenarios as these are just scaled from the reference
Reference_Genstack = filter_csv_by_one_column(GenStack, "Scenario", "Reference", output_filtered_file=None)

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

#This merges all of th egeneric gas peakers into one entry
fixed_cost = merge_specific_group(fixed_cost, "Tech", "Plant", "Generic OCGT peaker", "GasPkr")



#Then we want to apply the NREL learning curves to the according varied cost spots


#In TIMES2.0 they used the moderate data from NREL to model the Tui scenario
filters_Tui = {
    "Technology": ["Land-Based Wind - Class 2 - Technology 1",
                  "Utility PV - Class 1", "Geothermal - Hydro / Flash"],  
    "Scenario": "Moderate" 
}

Tui_NREL_CAPEX, excluded_Tui_curves = filter_csv_by_multiple_columns(NREL_CAPEX, filters_Tui, output_filtered_file=None, output_excluded_file=None)


#For Kea they used the conservative scenario (slower decrease in costs over time)
filters_Kea = {
    "Technology": ["Land-Based Wind - Class 2 - Technology 1",
                  "Utility PV - Class 1", "Geothermal - Hydro / Flash"],  
    "Scenario": "Conservative" 
}

Kea_NREL_CAPEX, excluded_Kea_curves = filter_csv_by_multiple_columns(NREL_CAPEX, filters_Kea, output_filtered_file=None, output_excluded_file=None)


# removing the scenario and 2022 columns as these are not needed in calcs (want a base year of 2023 to match MBIE data) :)
columns_to_remove = ["Scenario", "2022"]
Tui_NREL_CAPEX = remove_columns(Tui_NREL_CAPEX, columns_to_remove)

Kea_NREL_CAPEX = remove_columns(Kea_NREL_CAPEX, columns_to_remove)


# Calculate the percentage indices

Tui_idx = divide_from_specific_column(Tui_NREL_CAPEX, base_column = "2023", row_conditions = {})

Kea_idx = divide_from_specific_column(Kea_NREL_CAPEX, base_column = "2023", row_conditions = {})


Tui_idx = Tui_idx.rename(columns={'Technology': 'Tech'})
Kea_idx = Kea_idx.rename(columns={'Technology': 'Tech'})


# gives you the indices of the rows that we want used for the mapping_dict 
solar_Tui = Tui_idx[Tui_idx["Tech"] == "Utility PV - Class 1"].index[0]
wind_Tui = Tui_idx[Tui_idx["Tech"] == "Land-Based Wind - Class 2 - Technology 1"].index[0]
geo_Tui = Tui_idx[Tui_idx["Tech"] == "Geothermal - Hydro / Flash"].index[0]
#set up to combine and multiply the two dataframes
selected_columns = ["Plant", "TechName", "Substation", "Region", "Status", "Type","Commissioning Year"]
multiply_column = "Capital cost (NZD/kW)"
option_column = "Tech"
mapping_dict_Tui = {
    "Solar" : solar_Tui,
    "Wind" : wind_Tui,
    "Geo" : geo_Tui
}

label_from_df2 = Tui_idx.columns.tolist()
constant_col1 = "Connection cost (NZD $m)"
constant_col2 = "Capacity (MW)"

Tui_idx = Tui_idx.apply(pd.to_numeric, errors="coerce")



Tui_CAPEX = combine_and_multiply_by_row(varied_cost, Tui_idx, selected_columns, multiply_column, option_column, mapping_dict_Tui, label_from_df2, constant_col1, constant_col2)
Tui_CAPEX = remove_columns(Tui_CAPEX, "Tech") # for some reason it added an extra tech column that made no sense to me so this just gets rid of it, the calulcationss are correct now tho woooooooooo



# first just finding the indices of the rows we want to use
solar_Kea = Kea_idx[Kea_idx["Tech"] == "Utility PV - Class 1"].index[0]
wind_Kea = Kea_idx[Kea_idx["Tech"] == "Land-Based Wind - Class 2 - Technology 1"].index[0]
geo_Kea = Kea_idx[Kea_idx["Tech"] == "Geothermal - Hydro / Flash"].index[0]
mapping_dict_Kea = {
    "Solar" : solar_Kea,
    "Wind" : wind_Kea,
    "Geo" : geo_Kea
}

Kea_idx = Kea_idx.apply(pd.to_numeric, errors="coerce")
Kea_CAPEX = combine_and_multiply_by_row(varied_cost, Kea_idx, selected_columns, multiply_column, option_column, mapping_dict_Kea, label_from_df2, constant_col1, constant_col2)
Kea_CAPEX = remove_columns(Kea_CAPEX, "Tech") # for some reason it added an extra tech column that made no sense to me so this just gets rid of it, the calulcationss are correct now tho woooooooooo


### FOM time 


#Moving the wanted FOM data to it's own dataframe
Tui_NREL_FOM, ex_FOM_Tui_curves = filter_csv_by_multiple_columns(NREL_FOM, filters_Tui, output_filtered_file=None, output_excluded_file=None)


Kea_NREL_FOM, ex_FOM_Kea_curves = filter_csv_by_multiple_columns(NREL_FOM, filters_Kea, output_filtered_file=None, output_excluded_file=None)



# removing the scenario and 2022 columns as these are not needed in calcs :)

Tui_NREL_FOM = remove_columns(Tui_NREL_FOM, columns_to_remove)

Kea_NREL_FOM = remove_columns(Kea_NREL_FOM, columns_to_remove)

#Creating the percentage indices for FOMs
Tui_FOM_idx = divide_from_specific_column(Tui_NREL_FOM, base_column = "2023", row_conditions = {})

Kea_FOM_idx = divide_from_specific_column(Kea_NREL_FOM, base_column = "2023", row_conditions = {})

#Prepping for combining and multiplying the NREL and MBIE dataframes
Tui_FOM_idx = Tui_FOM_idx.rename(columns={'Technology': 'Tech'})
Kea_FOM_idx = Kea_FOM_idx.rename(columns={'Technology': 'Tech'})

multiply_column_FOM = "Fixed operating costs (NZD/kW/year)"

Tui_FOM_idx = Tui_FOM_idx.apply(pd.to_numeric, errors="coerce")

Tui_FOM = combine_and_multiply_FOM(varied_cost, Tui_FOM_idx, selected_columns, multiply_column_FOM, option_column, mapping_dict_Tui, label_from_df2, transform_func=None)
Tui_FOM = remove_columns(Tui_FOM, "Tech") # for some reason it added an extra tech column that made no sense to me so this just gets rid of it, the calulcationss are correct now tho woooooooooo

Kea_FOM_idx = Kea_FOM_idx.apply(pd.to_numeric, errors="coerce")

Kea_FOM = combine_and_multiply_FOM(varied_cost, Kea_FOM_idx, selected_columns, multiply_column_FOM, option_column, mapping_dict_Kea, label_from_df2, transform_func=None)
Kea_FOM = remove_columns(Kea_FOM, "Tech") # for some reason it added an extra tech column that made no sense to me so this just gets rid of it, the calulcationss are correct now tho woooooooooo

###############     Offshore wind (fixed and floating) additions to table 
# First getting the data from the NREL csvs for CAPEX
filters_offshore_Tui = {
    "Technology": ["Offshore Wind - Class 1", "Offshore Wind - Class 8"],  
    "Scenario": "Moderate" 
}

Tui_offshore_CAPEX, excluded_Tui_curves = filter_csv_by_multiple_columns(NREL_CAPEX, filters_offshore_Tui, output_filtered_file=None, output_excluded_file=None)

filters_offshore_Kea = {
    "Technology": ["Offshore Wind - Class 1", "Offshore Wind - Class 8"],  
    "Scenario": "Conservative" 
}

Kea_offshore_CAPEX, excluded_Kea_curves = filter_csv_by_multiple_columns(NREL_CAPEX, filters_offshore_Kea, output_filtered_file=None, output_excluded_file=None)


#removing unwanted columns from the dataframes (columns_to_remove was defined earlier in the script)
Tui_offshore_CAPEX = remove_columns(Tui_offshore_CAPEX, columns_to_remove)
Kea_offshore_CAPEX = remove_columns(Kea_offshore_CAPEX, columns_to_remove)

CPI = 1.05 # 5% CPI
cost_conversion = 0.62 #USD to NZD
Tui_converted_CAPEX = clean_and_multiply(Tui_offshore_CAPEX, CPI, cost_conversion)

Kea_converted_CAPEX = clean_and_multiply(Kea_offshore_CAPEX, CPI, cost_conversion)

#Now to find the offshore FOMs
Tui_offshore_FOM, excluded_Tui_curves = filter_csv_by_multiple_columns(NREL_FOM, filters_offshore_Tui, output_filtered_file=None, output_excluded_file=None)
Kea_offshore_FOM, excluded_Tui_curves = filter_csv_by_multiple_columns(NREL_FOM, filters_offshore_Kea, output_filtered_file=None, output_excluded_file=None)

#removing unwanted columns from the dataframes (columns_to_remove was defined earlier in the script)
Tui_offshore_FOM = remove_columns(Tui_offshore_FOM, columns_to_remove)
Kea_offshore_FOM = remove_columns(Kea_offshore_FOM, columns_to_remove)

#Final conversion from USD to NZD including CPI
Tui_converted_FOM = clean_and_multiply(Tui_offshore_FOM, CPI, cost_conversion)
Kea_converted_FOM = clean_and_multiply(Kea_offshore_FOM, CPI, cost_conversion)

#Want to add columns so that the data is easy to append into the main dataframe

status_offshore = ["Generic", "Generic"]
techname_offshore = ["Fixed Offshore Wind", "Floating Offshore Wind"]

Tui_converted_CAPEX.insert(1, "Status", status_offshore)
Tui_converted_CAPEX.insert(2,"TechName", techname_offshore)

Kea_converted_CAPEX.insert(1, "Status", status_offshore)
Kea_converted_CAPEX.insert(2,"TechName", techname_offshore)

Tui_converted_FOM.insert(1, "Status", status_offshore)
Tui_converted_FOM.insert(2,"TechName", techname_offshore)

Kea_converted_FOM.insert(1, "Status", status_offshore)
Kea_converted_FOM.insert(2,"TechName", techname_offshore)

#Just relabeling to match the main Data Frames
Tui_converted_CAPEX = Tui_converted_CAPEX.rename(columns={'Technology': 'Plant'})
Kea_converted_CAPEX = Kea_converted_CAPEX.rename(columns={'Technology': 'Plant'})
Tui_converted_FOM = Tui_converted_FOM.rename(columns={'Technology': 'Plant'})
Kea_converted_FOM = Kea_converted_FOM.rename(columns={'Technology': 'Plant'})


labels = ['Taranaki', 'Waikato', 'Southland']

# List of original DataFrames
original_dfs = [Tui_converted_CAPEX, Kea_converted_CAPEX, Tui_converted_FOM, Kea_converted_FOM]

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

Tui_CAPEX = pd.concat([Tui_CAPEX, merged_copies[0]], ignore_index = True)
Kea_CAPEX = pd.concat([Kea_CAPEX, merged_copies[1]], ignore_index = True)
Tui_FOM = pd.concat([Tui_FOM, merged_copies[2]], ignore_index = True)
Kea_FOM = pd.concat([Kea_FOM, merged_copies[3]], ignore_index = True)

#Adding in needed info for the final data frame
Tui_CAPEX[["Scenario", "Variable", "Unit"]] = ["Tui", "CAPEX", "$/kW"]
Kea_CAPEX[["Scenario", "Variable", "Unit"]] = ["Kea", "CAPEX", "$/kW"]
Tui_FOM[["Scenario", "Variable", "Unit"]] = ["Tui", "FOM", "$/kW"]
Kea_FOM[["Scenario", "Variable", "Unit"]] = ["Kea", "FOM", "$/kW"]

#merging all of the variable data
merged_df = pd.concat([Tui_CAPEX, Kea_CAPEX, Tui_FOM, Kea_FOM], ignore_index = True)

#moving some of the columns
moves = [("Scenario", 0), ("Variable", 8),("Unit", 9)]
merged_df = move_columns(merged_df, moves)

#Melting so that there is 1 data point per row
long_df = pd.melt(merged_df,
                  id_vars = ["Scenario", "Plant", "TechName", "Substation", "Region", "Status", "Type", "Commissioning Year", "Variable", "Unit"],
                  value_vars = ['2023', '2024','2025', '2026', '2027', '2028', '2029', '2030', '2031', '2032', '2033','2034', '2035', '2036', '2037',
                                 '2038', '2039', '2040', '2041', '2042','2043', '2044', '2045', '2046', '2047', '2048', '2049', '2050'],
                                 var_name = "Year",
                                 value_name= "Value")

 
#Adding in the data from fixed_costs

fixed_cost["CAPEX"] = fixed_cost["Total Capital costs (NZD $m)"]/fixed_cost["Capacity (MW)"]*1000
fixed_cost = fixed_cost.drop(['Total Capital costs (NZD $m)', 'Scenario'], axis=1)

#putting in Tui/Kea scenarios
Tui_fixed_cost = fixed_cost.copy()
Kea_fixed_cost = fixed_cost.copy()
Tui_fixed_cost['Scenario'] = "Tui"
Kea_fixed_cost['Scenario'] = 'Kea'
new_fixed_cost = pd.concat([Tui_fixed_cost, Kea_fixed_cost], ignore_index = True)

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
    'CAPEX' : '$'
}
long_fixed_cost['Unit'] = long_fixed_cost['Variable'].map(label_map).fillna('Other')

long_fixed_cost['Year'] = long_fixed_cost['Commissioning Year']
#Replaces all 0 values with 2023 as base year
long_fixed_cost['Year'] = long_fixed_cost['Year'].replace(0,2023)
long_fixed_cost = move_columns(long_fixed_cost, [('Unit', 9), ("Year", 10)])

# Adding in the Capacities of each of the 
varied_cost_capacity = varied_cost[['Plant', 'Status', 'TechName',
       'Substation', 'Region', 'Capacity (MW)', 'Type', 'Commissioning Year']].copy()

varied_cost_capacity =varied_cost_capacity.rename(columns = {'Capacity (MW)': 'Value'})
varied_cost_capacity['Unit'] = 'MW'
varied_cost_capacity['Year'] = varied_cost_capacity['Commissioning Year']
#Replaces all 0 values with 2023 as a default year
varied_cost_capacity['Year'] = varied_cost_capacity['Year'].replace(0,2023)

#Adding in the scenario names
Tui_varied_cap = varied_cost_capacity.copy()
Kea_varied_cap = varied_cost_capacity.copy()
Tui_varied_cap['Scenario'] = "Tui"
Kea_varied_cap['Scenario'] = 'Kea'
new_varied_cap = pd.concat([Tui_varied_cap, Kea_varied_cap], ignore_index = True)
new_varied_cap['Variable'] = 'Capacity'

#reordering the columns to match other frames
new_varied_cap = new_varied_cap[['Scenario', 'Plant', 'TechName', 'Substation', 'Region', 'Status',
                                   'Type', 'Commissioning Year', 'Variable', 'Unit', 'Year', 'Value']]

final_data = pd.concat([long_df, new_varied_cap, long_fixed_cost], ignore_index = True)

#replacing 0's with NaN
final_data = final_data.replace(0, np.nan)

#Removes all the unwanted data points as these points occur before the earliest commissioning year
final_data = conditional_row_filter(final_data, 'Type', 'Earliest Year', 'Commissioning Year', 'Year')

#Adding in the Capacities for the offshore wind
final_data = duplicate_and_modify_rows_two_conditions(final_data,'TechName', ['Floating Offshore Wind', 'Fixed Offshore Wind'],
                                                    'Variable', 'CAPEX', 'Variable', 'Capacity', 'Unit', 'MW', 'Value')


output_name = "new_tech_data.csv"

print(f"Saving {output_name} to data_intermediate")

final_data.to_csv(f"{output_location}/{output_name}", index = False, encoding = "utf-8-sig")