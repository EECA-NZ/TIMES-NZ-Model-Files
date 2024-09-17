"""
Aim is to replicate the intended functionality of the inherited script 'New_Data_Processing.R'
"""

import os
import sys
import logging
import argparse
import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

try:
    parser = argparse.ArgumentParser(description='Process VEDA data to create a human-readable schema')
    parser.add_argument('version', type=str, help='The version number')
    args = parser.parse_args()
    version = args.version
except:
    version = '2.1.3'

try:
    current_dir = os.path.dirname(__file__)
except:
    current_dir = os.getcwd()

os.environ['TIMES_NZ_VERSION'] = version
sys.path.append(os.path.join(current_dir, '..', 'library'))
from constants import *
from helpers import *
from rulesetsnew import *


#### CONSTANTS
TOL = 1E-6

FIX_MULTIPLE_FOUT = True

ZERO_BIOFUEL_EMISSIONS = False

GROUP_COLUMNS = ['Scenario', 'Sector', 'Subsector', 'Technology', 'Enduse', 'Unit', 'Parameters', 'Fuel', 'Period', 'FuelGroup', 'Technology_Group']

SCENARIO_INPUT_FILES = {
    'Kea': f'../../TIMES-NZ-GAMS/scenarios/kea-v{VERSION_STR}/kea-v{VERSION_STR}.vd'
    #'Tui': f'../../TIMES-NZ-GAMS/scenarios/tui-v{VERSION_STR}/tui-v{VERSION_STR}.vd'
}

NEEDED_ATTRIBUTES = ['VAR_Cap', 'VAR_FIn', 'VAR_FOut']

NON_EMISSION_FUEL = ['Electricity', 'Wood', 'Hydrogen', 'Hydro', 'Wind', 'Solar', 'Biogas']

FOSSIL_FROM_RENEWABLE_FUEL_MAP = {'Drop-In Diesel': 'Diesel', 'Drop-In Jet': 'Jet Fuel', 'Biodiesel': 'Diesel'}

COMMODITY_UNITS = {x[0]['Commodity']: x[2]['Unit'] for x in commodity_unit_rules}

PROCESS_SECTORS = {x[0]['Process']: x[2]['Sector'] for x in process_rules}

END_USE_PROCESS_EMISSION_TYPES = {x: sector_emission_types[PROCESS_SECTORS[x]] for x in end_use_processes}


#### MAIN ####

os.makedirs('../data/output', exist_ok=True)

raw_df = pd.DataFrame()

# Read the VEDA Data (VD) files
for scen, path in SCENARIO_INPUT_FILES.items():
    if not os.path.exists(path):
        raise FileNotFoundError(f'File not found: {path}')
    scen_df = read_vd(path)
    scen_df = scen_df[(scen_df['Period'] != '2016') &
                      #(scen_df['Commodity'] != 'COseq') &
                      (scen_df['Period'] != '2020')]
    scen_df['Scenario'] = scen
    raw_df = pd.concat([raw_df, scen_df])

# Filtering and transformation
raw_df.rename(columns={'PV': 'Value'}, inplace=True)
raw_df = raw_df[raw_df['Attribute'].isin(NEEDED_ATTRIBUTES)]

all_tot_co2 = raw_df.loc[(raw_df.Attribute == 'VAR_FOut') & (raw_df.Commodity == 'TOTCO2')].Value.sum()
pos_tot_co2 = raw_df.loc[(raw_df.Attribute == 'VAR_FOut') & (raw_df.Commodity == 'TOTCO2') & (raw_df.Value > 0)].Value.sum()
sum_co2 = raw_df.loc[(raw_df.Attribute == 'VAR_FOut') & (raw_df.Commodity != 'TOTCO2') & raw_df.Commodity.str.contains('CO2')].Value.sum()

# Because the following hold, we can infer that the positive TOTCO2 values reflect the emissions and the negative TOTCO2 values reflect 
# the CO2 "sink" effects attributable to biofuels. We need to redistribute these to end-use processes.
assert(abs(pos_tot_co2 - sum_co2) < TOL)
assert(pos_tot_co2 >= all_tot_co2)

# Aggregate Value over all combinations of Region, Vintage, Timeslice, UserConstraint for the other columns.
main_df = raw_df.groupby(['Scenario', 'Attribute', 'Commodity', 'Process', 'Period']).sum(['Value']).reset_index()

# (See above): VAR_Fout TOTCO2 rows include negative and positive rows. The positive ones sum to the same total as the rest of the CO2 rows.
# For communication purposes (e.g. to show reduced emissions from end-use processes that burn blended fuels), the negative emissions
# rows need to be replaced with negative-emission contributions attributed to the downstream processes that use the blended fuels.
# We also drop the positive TOTCO2 rows, which duplicate the information contained in the rest of the CO2 rows.
# Get the index and use this to update the main_df instead of using the same condition twice:
totco2_rows_to_keep = main_df[(main_df['Commodity'] == 'TOTCO2') & (main_df.Value < 0)]
totco2_rows_to_drop = main_df[(main_df['Commodity'] == 'TOTCO2') & (main_df.Value >= 0)]
main_df.loc[totco2_rows_to_keep.index, 'Commodity'] = 'NEGCO2'
main_df.loc[totco2_rows_to_keep.index, 'Parameters'] = 'Emissions'
main_df = main_df[~main_df.index.isin(totco2_rows_to_drop.index)]

main_df = main_df[~main_df['Process'].apply(is_trade_process)]        # VAR_FIn and VAR_FOut rows match
main_df = main_df[~main_df['Process'].apply(is_elc_exchange_process)] # VAR_FIn and VAR_FOut rows match
main_df = main_df[~main_df['Process'].apply(is_elc_grid_processes)]


#main_df = main_df[~main_df['Process'].apply(is_import_process)]
#main_df = main_df[~main_df['Process'].apply(is_export_process)]
#save(main_df, f'../data/output/output_raw_df_v{VERSION_STR}.csv')

for name, ruleset in DIRECT_RULESETS:
    logging.info("Applying ruleset: %s", name)
    main_df = apply_rules(main_df, ruleset)

save(main_df, f'../data/output/main_df_v{VERSION_STR}.csv')

raw_nan_rows = main_df[main_df.isnull().any(axis=1)].copy()
raw_nan_rows.loc[:, 'NaN_Columns'] = raw_nan_rows.apply(lambda row: list(row[row.isna()].index), axis=1)
raw_nan_rows.loc[:, 'NaN_Columns'] = raw_nan_rows['NaN_Columns'].apply(lambda x: ', '.join(x))
unique_rows = raw_nan_rows[['Commodity', 'Process', 'NaN_Columns']].drop_duplicates()
raw_nan_rows.to_csv(f'../data/output/main_df_v{VERSION_STR}_nan_rows.csv', index=False)
unique_rows.to_csv(f'../data/output/main_df_v{VERSION_STR}_nan_row_summary.csv', index=False)

## Read other necessary files
schema_technology = pd.read_csv('../data/input/Schema_Technology.csv')
schema_technology['Technology'] = schema_technology['Technology'].str.strip()

emissions_rows_to_add = pd.DataFrame()
logging.info('Collect all "negative emissions" rows to attribute to end-use processes')
negative_emissions = main_df[
    (main_df['Attribute'] == "VAR_FOut") &
    (main_df['Commodity'].str.contains("CO2")) &
    (main_df['Value'] < 0)]
for index, row in negative_emissions.iterrows():
    # For each negative emission process, follow its outputs through to end uses
    trace_result = trace_commodities(row['Process'], row['Scenario'], row['Period'], main_df, COMMODITY_UNITS)
    # Get the fractional attributions of the process output to end-use processes
    end_use_allocations = end_use_fractions(row['Process'], row['Scenario'], row['Period'], main_df, COMMODITY_UNITS)
    # Proportionately attribute the 'neg-emissions' to the end-uses, in units of Mt CO₂/yr
    end_use_allocations['Value'] *= row['Value']
    # Label the Fuels used according to the neg-emission process and commodity produced
    end_use_allocations = apply_rules(end_use_allocations, RENEWABLE_FUEL_ALLOCATION_RULES)
    # Overwrite the commodity with the emission commodity for the sector
    end_use_allocations['Commodity'] = end_use_allocations['Process'].map(END_USE_PROCESS_EMISSION_TYPES)
    # Tidy up and add the new rows to emissions_rows_to_add
    end_use_allocations.dropna(inplace=True)
    end_use_allocations = add_missing_columns(end_use_allocations, OUT_COLS)
    emissions_rows_to_add = pd.concat([emissions_rows_to_add, end_use_allocations], ignore_index=True)
# Complete the dataframe using the usual rules, taking care not to overwrite the Fuel
for name, ruleset in SCHEMA_RULESETS + [('process_enduse_rules', process_enduse_rules)]:
    if name in ["commodity_fuel_rules", "process_fuel_rules"]:
        continue
    logging.info("Applying ruleset to 'negative emissions' rows: %s", name)
    emissions_rows_to_add = apply_rules(emissions_rows_to_add, ruleset)
# If desired, attribute the negative emissions to the fossil fuel instead, and create zero-emissions rows for the biofuel.
# The extra fossil negative-emissions rows for the fossil fuel will later combine and partly cancel the existing
# fossil fuel emissions on a subsequent .groupby().sum() operation.
if ZERO_BIOFUEL_EMISSIONS:
    fossil_emissions_rows_to_add = emissions_rows_to_add.copy()
    fossil_emissions_rows_to_add.Fuel = fossil_emissions_rows_to_add.Fuel.map(
        FOSSIL_FROM_RENEWABLE_FUEL_MAP
    )
    fossil_emissions_rows_to_add.FuelGroup = "Fossil Fuels"
    emissions_rows_to_add.Value = 0.0
    emissions_rows_to_add = pd.concat([emissions_rows_to_add, fossil_emissions_rows_to_add])
# Create a dataframe with positive emissions associated with the "negative emissions" rows so that total emissions are unaffected.
negated_negative_emissions = negative_emissions.copy()
negated_negative_emissions.Value = -negated_negative_emissions.Value
emissions_rows_to_add = pd.concat([emissions_rows_to_add, negated_negative_emissions])
assert(emissions_rows_to_add.Value.sum() < TOL)


logging.info('Allocate biodiesel to end-use processes')
biodiesel_rows_to_add = pd.DataFrame()
biodiesel_out = main_df[(
    main_df['Attribute'] == "VAR_FOut") &
    (main_df['Commodity'] == "BDSL") #&
    #(~main_df['Process'].apply(is_trade_process))
]
biodiesel_in = main_df[(
    main_df['Attribute'] == "VAR_FIn") &
    (main_df['Commodity'] == "BDSL") #&
    #(~main_df['Process'].apply(is_trade_process))
]
for index, row in biodiesel_out.iterrows():
    trace_result = trace_commodities(row['Process'], row['Scenario'], row['Period'], main_df, COMMODITY_UNITS)
    trace_result = [x for x in trace_result if x[1]==row['Commodity']]
    end_use_allocations = end_use_fractions(row['Process'], row['Scenario'], row['Period'], main_df, COMMODITY_UNITS, filter_to_commodities=['BDSL']).dropna()
    end_use_allocations['Value'] *= row['Value']
    end_use_allocations['Attribute'] = 'VAR_FIn'
    end_use_allocations['Commodity'] = 'BDSL'
    end_use_allocations = apply_rules(end_use_allocations, RENEWABLE_FUEL_ALLOCATION_RULES)
    end_use_allocations.dropna(inplace=True)
    biodiesel_rows_to_add = pd.concat([biodiesel_rows_to_add, end_use_allocations], ignore_index=True)
for name, ruleset in SCHEMA_RULESETS + [('process_enduse_rules', process_enduse_rules)]:
    if name in ["commodity_fuel_rules", "process_fuel_rules"]:
        continue
    logging.info("Applying ruleset to 'biodiesel' rows: %s", name)
    biodiesel_rows_to_add = apply_rules(biodiesel_rows_to_add, ruleset)
# Deallocate the same amount of diesel.
diesel_rows_to_add = biodiesel_rows_to_add.copy()
diesel_rows_to_add['Value'] = -diesel_rows_to_add['Value']
diesel_rows_to_add['Commodity'] = 'DSL'
diesel_rows_to_add['Fuel'] = 'Diesel'
diesel_rows_to_add['FuelGroup'] = 'Fossil Fuels'
biodiesel_rows_to_add = pd.concat([biodiesel_rows_to_add, diesel_rows_to_add])
biodiesel_rows_to_drop = biodiesel_in


logging.info('Allocate drop-in-diesel to end-use processes')
drop_in_diesel_rows_to_add = pd.DataFrame()
drop_in_diesel_out = main_df[
    (main_df['Attribute'] == "VAR_FOut") &
    (main_df['Commodity'] == "DID") #&
    #(~main_df['Process'].apply(is_trade_process))
]
drop_in_diesel_in = main_df[
    (main_df['Attribute'] == "VAR_FIn") &
    (main_df['Commodity'] == "DID") #&
    #(~main_df['Process'].apply(is_trade_process))
]
for index, row in drop_in_diesel_out.iterrows():
    trace_result = trace_commodities(row['Process'], row['Scenario'], row['Period'], main_df, COMMODITY_UNITS)
    trace_result = [x for x in trace_result if x[1]==row['Commodity']]
    end_use_allocations = end_use_fractions(row['Process'], row['Scenario'], row['Period'], main_df, COMMODITY_UNITS, filter_to_commodities=['DID']).dropna()
    end_use_allocations['Value'] *= row['Value']
    end_use_allocations['Attribute'] = 'VAR_FIn'
    end_use_allocations['Commodity'] = 'DID'
    end_use_allocations = apply_rules(end_use_allocations, RENEWABLE_FUEL_ALLOCATION_RULES)
    end_use_allocations.dropna(inplace=True)
    drop_in_diesel_rows_to_add = pd.concat([drop_in_diesel_rows_to_add, end_use_allocations], ignore_index=True)
for name, ruleset in SCHEMA_RULESETS + [('process_enduse_rules', process_enduse_rules)]:
    if name in ["commodity_fuel_rules", "process_fuel_rules"]:
        continue
    logging.info("Applying ruleset to 'drop-in diesel' rows: %s", name)
    drop_in_diesel_rows_to_add = apply_rules(drop_in_diesel_rows_to_add, ruleset)
# Deallocate the same amount of diesel.
diesel_rows_to_add = drop_in_diesel_rows_to_add.copy()
diesel_rows_to_add['Value'] = -diesel_rows_to_add['Value']
diesel_rows_to_add['Commodity'] = 'DSL'
diesel_rows_to_add['Fuel'] = 'Diesel'
diesel_rows_to_add['FuelGroup'] = 'Fossil Fuels'
drop_in_diesel_rows_to_add = pd.concat([drop_in_diesel_rows_to_add, diesel_rows_to_add])
drop_in_diesel_rows_to_drop = drop_in_diesel_in

logging.info('Allocate drop-in-jet to end-use processes')
drop_in_jet_rows_to_add = pd.DataFrame()
drop_in_jet_out = main_df[
    (main_df['Attribute'] == "VAR_FOut") &
    (main_df['Commodity'] == "DIJ") #&
    #(~main_df['Process'].apply(is_trade_process))
]
drop_in_jet_in = main_df[
    (main_df['Attribute'] == "VAR_FIn") &
    (main_df['Commodity'] == "DIJ") #&
    #(~main_df['Process'].apply(is_trade_process))
]
for index, row in drop_in_jet_out.iterrows():
    trace_result = trace_commodities(row['Process'], row['Scenario'], row['Period'], main_df, COMMODITY_UNITS)
    trace_result = [x for x in trace_result if x[1]==row['Commodity']]
    end_use_allocations = end_use_fractions(row['Process'], row['Scenario'], row['Period'], main_df, COMMODITY_UNITS, filter_to_commodities=['DIJ'])
    ################################
    # Hack to match R
    domestic_jet_travel = process_output_flows('T_O_FuelJet', row['Scenario'], row['Period'], main_df)['T_O_JET']
    internat_jet_travel = process_output_flows('T_O_FuelJet_Int', row['Scenario'], row['Period'], main_df)['T_O_JET_Int']
    end_use_allocations.loc[end_use_allocations.Process=='T_O_FuelJet_Int','Value'] = internat_jet_travel / (internat_jet_travel + domestic_jet_travel)
    end_use_allocations.loc[end_use_allocations.Process=='T_O_FuelJet','Value'] = domestic_jet_travel / (internat_jet_travel + domestic_jet_travel)
    end_use_allocations.loc[end_use_allocations.Process=='T_O_FuelJet_Int','Commodity'] = 'DIJ'
    end_use_allocations.loc[end_use_allocations.Process=='T_O_FuelJet_Int','FuelSourceProcess'] = 'CT_CWODDID'
    ################################
    end_use_allocations.dropna(inplace=True)
    end_use_allocations['Value'] *= row['Value']
    end_use_allocations['Attribute'] = 'VAR_FIn'
    end_use_allocations['Commodity'] = 'DIJ'
    end_use_allocations = apply_rules(end_use_allocations, RENEWABLE_FUEL_ALLOCATION_RULES)
    drop_in_jet_rows_to_add = pd.concat([drop_in_jet_rows_to_add, end_use_allocations.dropna()], ignore_index=True)
for name, ruleset in SCHEMA_RULESETS + [('process_enduse_rules', process_enduse_rules)]:
    if name in ["commodity_fuel_rules", "process_fuel_rules"]:
        continue
    logging.info("Applying ruleset to 'drop-in jet' rows: %s", name)
    drop_in_jet_rows_to_add = apply_rules(drop_in_jet_rows_to_add, ruleset)
# Deallocate the same amount of jet fuel.
jet_rows_to_add = drop_in_jet_rows_to_add.copy()
jet_rows_to_add['Value'] = -jet_rows_to_add['Value']
jet_rows_to_add['Commodity'] = 'JET'
jet_rows_to_add['Fuel'] = 'Jet Fuel'
jet_rows_to_add['FuelGroup'] = 'Fossil Fuels'
drop_in_jet_rows_to_add = pd.concat([drop_in_jet_rows_to_add, jet_rows_to_add])
drop_in_jet_rows_to_drop = drop_in_jet_in

# Bring together changes
rows_to_add = pd.concat([
    emissions_rows_to_add,
    biodiesel_rows_to_add,
    drop_in_diesel_rows_to_add,
    drop_in_jet_rows_to_add])

rows_to_drop = pd.concat([
    biodiesel_rows_to_drop,
    drop_in_diesel_rows_to_drop,
    drop_in_jet_rows_to_drop])

# Some checks
# All rows to add match rows to drop in terms of total value
assert(abs(rows_to_add.Value.sum()) < TOL)
assert(abs(rows_to_add[rows_to_add.Commodity.str.contains('CO2')].Value.sum()) < TOL)
assert(abs(rows_to_add[rows_to_add.Commodity=='DIJ'].Value.sum() + rows_to_add[rows_to_add.Commodity=='JET'].Value.sum()) < TOL)
assert(abs(rows_to_add[rows_to_add.Commodity=='BDSL'].Value.sum() + rows_to_add[rows_to_add.Commodity=='DID'].Value.sum() + rows_to_add[rows_to_add.Commodity=='DSL'].Value.sum()) < TOL)

## Join operations
clean_df = pd.concat(
    [main_df[~main_df.index.isin(rows_to_drop.index)],
     rows_to_add],
    ignore_index=True
)
clean_df = pd.merge(clean_df, schema_technology, on=['Technology'], how='left')

# Setting values based on conditions
fossil_fuels = ['Petrol', 'Diesel', 'Fuel Oil', 'Coal', 'Natural Gas',
       'LPG', 'Coal Lignite', 'Jet Fuel', 'Crude Oil (imported)',
       'Crude Oil', 'Crude Oil (domestic)', 'Oil wastes', 'Other fuels from refinery']
processes_to_fix = clean_df[(clean_df['Fuel'].isin(NON_EMISSION_FUEL)) & (clean_df['Parameters'] == 'Emissions')].Process.unique()

for process in processes_to_fix:
    # Identify the non-emission fuel to be replaced
    process_clean_fuel = clean_df.loc[
        (clean_df['Fuel'].isin(NON_EMISSION_FUEL)) & 
        (clean_df['Parameters'] == 'Emissions') & 
        (clean_df['Process'] == process), 'Fuel'].unique()[0]
    # Identify all fuels used in the process
    process_all_fuels = clean_df.loc[clean_df['Process'] == process, 'Fuel'].unique()
    # Ensure that at least one of the fuels is a fossil fuel
    assert any(fuel in fossil_fuels for fuel in process_all_fuels), "No fossil fuel found in the process."
    # Find the fossil fuel used in the process
    process_fossil_fuel = next((fuel for fuel in process_all_fuels if fuel in fossil_fuels), None)
    indices_to_update = (clean_df['Fuel'] == process_clean_fuel) & \
                        (clean_df['Parameters'] == 'Emissions') & \
                        (clean_df['Process'] == process)    
    clean_df.loc[indices_to_update, 'Fuel'] = process_fossil_fuel
    clean_df.loc[indices_to_update, 'FuelGroup'] = 'Fossil Fuels'

# Reset the Electricity sector to 'Other'
clean_df['Sector'] = np.where(clean_df['Sector'] == 'Electricity', 'Other', clean_df['Sector'])

# Convert emissions to Mt CO2/yr
clean_df.loc[clean_df['Parameters'] == 'Emissions', 'Value'] /= 1000
clean_df.loc[clean_df['Parameters'] == 'Emissions', 'Unit'] = 'Mt CO<sub>2</sub>/yr' #'Mt CO₂/yr'

# Remove unwanted rows and group data
clean_df = clean_df[(clean_df['Parameters'] != 'Annualised Capital Costs') & (clean_df['Parameters'] != 'Technology Capacity')]

clean_df = clean_df.drop(columns=['FuelSourceProcess'])
nan_rows = clean_df[clean_df.isnull().any(axis=1)]
nan_rows.to_csv('../data/output/nan_rows.csv', index=False)

clean_df_filled = clean_df.fillna('Unknown')
combined_df = clean_df_filled.groupby(['Attribute', 'Process', 'Commodity'] + GROUP_COLUMNS).agg(Value=('Value', 'sum')).reset_index()


# Find processes with multiple VAR_FOut rows (excluding emissions commodities) and split the VAR_FIn row across
# each of the end-uses obtained from the VAR_FOut rows, based on the ratio of VAR_FOut values
if FIX_MULTIPLE_FOUT:

    filtered_df = combined_df[(combined_df['Attribute'] == 'VAR_FOut') & (~combined_df['Commodity'].str.contains('CO2'))]
    multi_fout = filtered_df.groupby(['Scenario', 'Process', 'Period']).filter(lambda x: len(x) > 1)
    unique_scenario_process_periods = multi_fout[['Scenario', 'Process', 'Period']].drop_duplicates()

    for _, row in unique_scenario_process_periods.iterrows():
        scen = row['Scenario']
        process = row['Process']
        period = row['Period']
        logging.info(f"Processing Scenario: {scen}, Process: {process}, Period: {period}")
        
        # Filter relevant rows for the current process and period
        relevant_rows = combined_df[(combined_df['Scenario'] == scen) & (combined_df['Process'] == process) & (combined_df['Period'] == period)]
        fin_row = relevant_rows[relevant_rows['Attribute'] == 'VAR_FIn']
        assert(len(fin_row) == 1)  # There should only be one VAR_FIn row - currently not handling multiple VAR_FIn rows
        fout_rows = relevant_rows[relevant_rows['Attribute'] == 'VAR_FOut']

        if not fin_row.empty:
            total_output = fout_rows['Value'].sum()
            ratios = fout_rows['Value'] / total_output
            
            # Create new VAR_FIn rows by multiplying the original Value with each ratio
            new_fin_rows = fin_row.copy().loc[fin_row.index.repeat(len(fout_rows))].reset_index(drop=True)
            new_fin_rows['Value'] = fin_row['Value'].values[0] * ratios.values
            new_fin_rows['Enduse'] = fout_rows['Enduse'].values
            
            # Replace the original VAR_FIn row with the new rows in the DataFrame
            combined_df = combined_df.drop(fin_row.index)  # Remove original VAR_FIn row
            combined_df = pd.concat([combined_df, new_fin_rows], ignore_index=True)


# Write the clean data to a CSV file
combined_df = combined_df.groupby(GROUP_COLUMNS).agg(Value=('Value', 'sum')).reset_index()

all_periods = np.sort(combined_df['Period'].unique())
categories = [x for x in GROUP_COLUMNS if x != 'Period']
combined_df = combined_df.groupby(categories).apply(add_missing_periods(all_periods)).reset_index(drop=True)

#combined_df = combined_df.groupby(GROUP_COLUMNS).agg(Value=('Value', 'sum')).reset_index()
combined_df = apply_rules(combined_df, THOUSAND_VEHICLE_RULES)
combined_df = complete_expand_dim(combined_df, 'Scenario', {'Value': 0})

combined_df = combined_df.sort_values(by=GROUP_COLUMNS)
combined_df = apply_rules(combined_df, ALWAYS_PRESENT_EMISSIONS_RULES)
combined_df = combined_df.groupby(GROUP_COLUMNS).agg(Value=('Value', 'sum')).reset_index()

sanity_check(negative_emissions, combined_df, {'Fuel': ['Biodiesel', 'Drop-In Jet', 'Drop-In Diesel'], 'Parameters': 'Emissions'}, TOL, factor=1000)

sanity_check(raw_df[raw_df.Commodity == 'TOTCO2'], combined_df, {'Parameters': 'Emissions'}, TOL, factor=1000)

sanity_check(biodiesel_out, combined_df, {'Fuel': 'Biodiesel', 'Parameters': 'Fuel Consumption'}, TOL)

sanity_check(drop_in_diesel_out, combined_df, {'Fuel': 'Drop-In Diesel', 'Parameters': 'Fuel Consumption'}, TOL)

sanity_check(drop_in_jet_out, combined_df, {'Fuel': 'Drop-In Jet', 'Parameters': 'Fuel Consumption'}, TOL)

save(combined_df, f'../data/output/output_combined_df_v{VERSION_STR}.csv')
logging.info(f"The combined DataFrame has been saved to ../data/output/output_combined_df_v{VERSION_STR}.csv")