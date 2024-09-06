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

parser = argparse.ArgumentParser(description='Process VEDA data to create a human-readable schema')
parser.add_argument('version', type=str, help='The version number')
args = parser.parse_args()
os.environ['TIMES_NZ_VERSION'] = args.version

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'library'))

from constants import *
from helpers import *
from rulesets import *


#### CONSTANTS

fix_multiple_fout = True

zero_biofuel_emissions = False

group_columns = ['Scenario', 'Sector', 'Subsector', 'Technology', 'Enduse', 'Unit', 'Parameters', 'Fuel', 'Period', 'FuelGroup', 'Technology_Group']

SCENARIO_INPUT_FILES = {
    'Kea': f'../../TIMES-NZ-GAMS/scenarios/kea-v{VERSION_STR}/kea-v{VERSION_STR}.vd',
    'Tui': f'../../TIMES-NZ-GAMS/scenarios/tui-v{VERSION_STR}/tui-v{VERSION_STR}.vd'
}

needed_attributes = ['VAR_Cap', 'VAR_FIn', 'VAR_FOut']

non_emission_fuel = ['Electricity', 'Wood', 'Hydrogen', 'Hydro', 'Wind', 'Solar', 'Biogas']

commodity_units = {x[0]['Commodity']: x[2]['Unit'] for x in commodity_unit_rules}

process_sectors = {x[0]['Process']: x[2]['Sector'] for x in process_rules}

end_use_process_emission_types = {x: sector_emission_types[process_sectors[x]] for x in end_use_processes}




#### FUNCTIONS ####

def generate_schema_and_save_to(output_schema_filepath):

    # First approach: VD OUTPUT. This approach will only include technologies selected by TIMES.
    vd_df = read_and_concatenate(INPUT_VD_FILES)

    # Add and subtract columns
    vd_df = add_missing_columns(vd_df, OUT_COLS + SUP_COLS)
    logging.info(
        "Dropping columns: %s",
        [x for x in vd_df.columns if x not in OUT_COLS + SUP_COLS]
    )
    vd_df = vd_df[OUT_COLS + SUP_COLS]

    # Subset the rows and drop duplicates
    vd_df = vd_df[vd_df["Attribute"].isin(ATTRIBUTE_ROWS_TO_KEEP)]
    
    # Second approach: Read the 'Commodity Groups' CSV file. This approach would be preferred if the
    # Commodity Groups export from VEDA were complete. Unfortunately, it doesn't present the emissions
    cg_df = process_map_from_commodity_groups(ITEMS_LIST_COMMODITY_GROUPS_CSV)

    # Combine the two DataFrames and drop duplicates
    main_df = pd.concat([vd_df, cg_df]).drop_duplicates()

    # Populate the columns and augment with emissions rows according to the rulesets in the specified order
    for name, ruleset in SCHEMA_RULESETS:
        logging.info("Applying ruleset: %s", name)
        main_df = apply_rules(main_df, ruleset)

    main_df.Commodity = main_df.Commodity.fillna('-')

    # Drop emissions rows with non-emissions commodities
    indexes_to_drop = main_df[(main_df['Parameters'] == 'Emissions') & (~main_df['Commodity'].isin(
        ['INDCO2', 'COMCO2', 'AGRCO2', 'RESCO2', 'ELCCO2', 'TRACO2', 'TOTCO2']))
        ].index
    main_df.drop(indexes_to_drop, inplace=True)
    logging.info("Adding missing rows")
    main_df = pd.concat([main_df, MISSING_ROWS], ignore_index=True)
    main_df = main_df[OUT_COLS].drop_duplicates().dropna().sort_values(by=OUT_COLS)
    try:
        main_df.to_csv(OUTPUT_SCHEMA_FILEPATH, index=False)
    except PermissionError:
        logging.warning(
            "The file %s may be currently open in Excel. Did not write to file.",
            OUTPUT_SCHEMA_FILEPATH,
        )
        exit()
    logging.info("The files have been concatenated and saved to %s", output_schema_filepath)

#### MAIN ####

os.makedirs('../data/output', exist_ok=True)

generate_schema_and_save_to(OUTPUT_SCHEMA_FILEPATH)

raw_df = pd.DataFrame()

# Read the VEDA Data (VD) files
for scen, path in SCENARIO_INPUT_FILES.items():
    if not os.path.exists(path):
        raise FileNotFoundError(f'File not found: {path}')
    scen_df = read_vd(path)
    scen_df = scen_df[(scen_df['Period'] != '2016') &
                      (scen_df['Commodity'] != 'COseq') &
                      (scen_df['Period'] != '2020')]
    scen_df['Scenario'] = scen
    raw_df = pd.concat([raw_df, scen_df])

# Filtering and transformation
raw_df.rename(columns={'PV': 'Value'}, inplace=True)
raw_df = raw_df[raw_df['Attribute'].isin(needed_attributes)]

# Aggregate Value over all combinations of Region, Vintage, Timeslice, UserConstraint for the other columns.
raw_df = raw_df.groupby(['Scenario', 'Attribute', 'Commodity', 'Process', 'Period']).sum(['Value']).reset_index()

# Read other necessary files
schema_all = pd.read_csv(OUTPUT_SCHEMA_FILEPATH)
schema_technology = pd.read_csv('../data/input/Schema_Technology.csv')
schema_technology['Technology'] = schema_technology['Technology'].str.strip()


# Drop MISSING_ROWS from schema_all before we begin
schema_all = pd.merge(schema_all,
                      MISSING_ROWS,
                      on=['Attribute', 'Process', 'Commodity', 'Sector', 'Subsector', 'Technology', 'Fuel', 'Enduse', 'Unit', 'Parameters', 'FuelGroup'],
                      how='outer', indicator=True)
schema_all = schema_all[schema_all['_merge'] == 'left_only'].drop(columns=['_merge'])


emissions_rows_to_add = pd.DataFrame()
emissions_rows_to_drop = pd.DataFrame()

# Collect all "negative emissions" rows to attribute to end-use processes
negative_emissions = raw_df[
    (raw_df['Attribute'] == "VAR_FOut") &
    (raw_df['Commodity'].str.contains("CO2")) &
    (raw_df['Value'] < 0)]
for index, row in negative_emissions.iterrows():
    # For each negative emission process, follow its outputs through to end uses
    trace_result = trace_commodities(row['Process'], row['Scenario'], row['Period'], raw_df, commodity_units)
    # Get the fractional attributions of the process output to end-use processes
    end_use_allocations = end_use_fractions(row['Process'], row['Scenario'], row['Period'], raw_df, commodity_units)
    # Proportionately attribute the 'neg-emissions' to the end-uses, in units of Mt CO₂/yr
    end_use_allocations['Value'] *= row['Value']
    # Label the Fuels used according to the neg-emission process and commodity produced
    end_use_allocations = apply_rules(end_use_allocations, RENEWABLE_FUEL_ALLOCATION_RULES)
    # Overwrite the commodity with the emission commodity for the sector
    end_use_allocations['Commodity'] = end_use_allocations['Process'].map(end_use_process_emission_types)
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
if zero_biofuel_emissions:
    emissions_rows_to_add_copy = emissions_rows_to_add.copy()
    emissions_rows_to_add_copy.Fuel = emissions_rows_to_add_copy.Fuel.map(
        {'Drop-In Diesel': 'Diesel', 'Drop-In Jet': 'Jet Fuel', 'Biodiesel': 'Diesel'}
    )
    emissions_rows_to_add_copy.FuelGroup = "Fossil Fuels"
    emissions_rows_to_add.Value = 0.0
    emissions_rows_to_add = pd.concat([emissions_rows_to_add, emissions_rows_to_add_copy])
emissions_rows_to_drop = pd.concat([emissions_rows_to_drop, negative_emissions])
# These rows are dropped on schema join.
assert(0 == len(pd.merge(emissions_rows_to_drop, schema_all, on=['Attribute', 'Process', 'Commodity'], how='inner')))


biodiesel_rows_to_add = pd.DataFrame()
# Allocate biodiesel to end-use processes
biodiesel = raw_df[(
    raw_df['Attribute'] == "VAR_FOut") &
    (raw_df['Commodity'] == "BDSL") &
    (~raw_df['Process'].apply(is_trade_process))
]
for index, row in biodiesel.iterrows():
    trace_result = trace_commodities(row['Process'], row['Scenario'], row['Period'], raw_df, commodity_units)
    trace_result = [x for x in trace_result if x[1]==row['Commodity']]
    end_use_allocations = end_use_fractions(row['Process'], row['Scenario'], row['Period'], raw_df, commodity_units, filter_to_commodities=['BDSL']).dropna()
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
diesel_rows_to_add['Fuel'] = 'Diesel'
diesel_rows_to_add['FuelGroup'] = 'Fossil Fuels'
biodiesel_rows_to_add = pd.concat([biodiesel_rows_to_add, diesel_rows_to_add])


drop_in_diesel_rows_to_add = pd.DataFrame()
# Allocate drop-in diesel to end-use processes
drop_in_diesel = raw_df[
    (raw_df['Attribute'] == "VAR_FOut") &
    (raw_df['Commodity'] == "DID") &
    (~raw_df['Process'].apply(is_trade_process))
]
for index, row in drop_in_diesel.iterrows():
    trace_result = trace_commodities(row['Process'], row['Scenario'], row['Period'], raw_df, commodity_units)
    trace_result = [x for x in trace_result if x[1]==row['Commodity']]
    end_use_allocations = end_use_fractions(row['Process'], row['Scenario'], row['Period'], raw_df, commodity_units, filter_to_commodities=['DID']).dropna()
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
diesel_rows_to_add = drop_in_diesel_rows_to_add.copy()
diesel_rows_to_add['Value'] = -diesel_rows_to_add['Value']
diesel_rows_to_add['Fuel'] = 'Diesel'
diesel_rows_to_add['FuelGroup'] = 'Fossil Fuels'
drop_in_diesel_rows_to_add = pd.concat([drop_in_diesel_rows_to_add, diesel_rows_to_add])


drop_in_jet_rows_to_add = pd.DataFrame()
# Allocate drop-in jet fuel to end-use processes
drop_in_jet = raw_df[
    (raw_df['Attribute'] == "VAR_FOut") &
    (raw_df['Commodity'] == "DIJ") &
    (~raw_df['Process'].apply(is_trade_process))
]
for index, row in drop_in_jet.iterrows():
    trace_result = trace_commodities(row['Process'], row['Scenario'], row['Period'], raw_df, commodity_units)
    trace_result = [x for x in trace_result if x[1]==row['Commodity']]
    end_use_allocations = end_use_fractions(row['Process'], row['Scenario'], row['Period'], raw_df, commodity_units, filter_to_commodities=['DIJ'])
    
    ################################
    # Hack to match R
    domestic_jet_travel = process_output_flows('T_O_FuelJet', row['Scenario'], row['Period'], raw_df)['T_O_JET']
    internat_jet_travel = process_output_flows('T_O_FuelJet_Int', row['Scenario'], row['Period'], raw_df)['T_O_JET_Int']
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
jet_rows_to_add['Fuel'] = 'Jet Fuel'
jet_rows_to_add['FuelGroup'] = 'Fossil Fuels'
drop_in_jet_rows_to_add = pd.concat([drop_in_jet_rows_to_add, jet_rows_to_add])


# Bring together changes
rows_to_drop = emissions_rows_to_drop
rows_to_add = pd.concat([
    emissions_rows_to_add,
    biodiesel_rows_to_add,
    drop_in_diesel_rows_to_add,
    drop_in_jet_rows_to_add])


# Some checks
# Check that all rows to drop will be dropped on merging
assert(0 == len(pd.merge(rows_to_drop, schema_all, on=['Attribute', 'Process', 'Commodity'], how='inner')))
# All rows to add match rows to drop in terms of total value
tolerance = 1E-6
assert(abs(rows_to_drop.Value.sum() - rows_to_add.Value.sum()) < tolerance)
assert(abs(rows_to_drop[rows_to_drop.Commodity.str.contains('CO2')].Value.sum() - rows_to_add[rows_to_add.Commodity.str.contains('CO2')].Value.sum()) < tolerance)
assert(abs(rows_to_drop[rows_to_drop.Commodity.str.contains('BDSL')].Value.sum() - rows_to_add[rows_to_add.Commodity.str.contains('BDSL')].Value.sum()) < tolerance)
assert(abs(rows_to_drop[rows_to_drop.Commodity.str.contains('DIJ')].Value.sum() - rows_to_add[rows_to_add.Commodity.str.contains('DIJ')].Value.sum()) < tolerance)
assert(abs(rows_to_drop[rows_to_drop.Commodity.str.contains('DID')].Value.sum() - rows_to_add[rows_to_add.Commodity.str.contains('DID')].Value.sum()) < tolerance)


# Join operations
clean_df = pd.concat(
    [pd.merge(raw_df[~raw_df.index.isin(rows_to_drop.index)], schema_all,
              on=['Attribute', 'Process', 'Commodity'],
              how='inner'),
     rows_to_add],
    ignore_index=True
)
clean_df = pd.merge(clean_df, schema_technology, on=['Technology'], how='left')

# Setting values based on conditions
logging.info("Value of emissions from non-emissions fuels before adjustment:")
logging.info(clean_df[(clean_df['Parameters'] == 'Emissions') & (clean_df['Fuel'].isin(non_emission_fuel))])
clean_df['Value'] = np.where((clean_df['Fuel'].isin(non_emission_fuel)) & (clean_df['Parameters'] == 'Emissions'), 0, clean_df['Value'])
logging.info("Value of emissions from non-emissions fuels after adjustment:")
logging.info(clean_df[(clean_df['Parameters'] == 'Emissions') & (clean_df['Fuel'].isin(non_emission_fuel))])
logging.warning("\nTODO: The approach inherited here could be improved. The schema has rows for each input fuel for processes that use multiple fuels.\n" \
       " On joining we get multiple rows with duplicated emissions for those processes, and we later set the non-emissions fuel emissions to zero.\n" \
       " This violates the principle that the dataframe should always be correct in between operations. Any forgotten process will lead to errors.\n" \
       " A nicer approach would be to have a single emissions row for each process, and procedurally attribute emissions to input energy flows.\n")
logging.info("process_input_flows('ELCTENGACHP00', 'Kea', '2018', raw_df): {}".format(process_input_flows('ELCTENGACHP00', 'Kea', '2018', raw_df)))
logging.info(raw_df[(raw_df.Process=='ELCTENGACHP00') & (raw_df.Scenario=='Kea') & (raw_df.Period=='2018')])
logging.info(schema_all[(schema_all.Process=='ELCTENGACHP00')])
logging.info(clean_df[(clean_df.Process=='ELCTENGACHP00') & (clean_df.Scenario=='Kea') & (clean_df.Period=='2018')])


# Reset the Electricity sector to 'Other'
clean_df['Sector'] = np.where(clean_df['Sector'] == 'Electricity', 'Other', clean_df['Sector'])

# Convert emissions to Mt CO2/yr
clean_df.loc[clean_df['Parameters'] == 'Emissions', 'Value'] /= 1000
clean_df.loc[clean_df['Parameters'] == 'Emissions', 'Unit'] = 'Mt CO<sub>2</sub>/yr' #'Mt CO₂/yr'

# Convert Annualised Capital Costs to Billion NZD
clean_df.loc[clean_df['Parameters'] == 'Annualised Capital Costs', 'Value'] /= 1000
clean_df.loc[clean_df['Parameters'] == 'Annualised Capital Costs', 'Unit'] = 'Billion NZD'

# Remove unwanted rows and group data
clean_df = clean_df[(clean_df['Parameters'] != 'Annualised Capital Costs') & (clean_df['Parameters'] != 'Technology Capacity')]
clean_df = clean_df.groupby(['Attribute', 'Process', 'Commodity'] + group_columns).agg(Value=('Value', 'sum')).reset_index()


combined_df = clean_df.copy()
# Find processes with multiple VAR_FOut rows (excluding emissions commodities) and split the VAR_FIn row across
# each of the end-uses obtained from the VAR_FOut rows, based on the ratio of VAR_FOut values
if fix_multiple_fout:

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
combined_df = combined_df.groupby(group_columns).agg(Value=('Value', 'sum')).reset_index()

all_periods = np.sort(combined_df['Period'].unique())
categories = [x for x in group_columns if x != 'Period']
combined_df = combined_df.groupby(categories).apply(add_missing_periods(all_periods)).reset_index(drop=True)

#combined_df = combined_df.groupby(group_columns).agg(Value=('Value', 'sum')).reset_index()
combined_df = apply_rules(combined_df, THOUSAND_VEHICLE_RULES)
combined_df = complete_expand_dim(combined_df, 'Scenario', {'Value': 0})

combined_df = combined_df.sort_values(by=group_columns)
combined_df = apply_rules(combined_df, ALWAYS_PRESENT_EMISSIONS_RULES)
combined_df = combined_df.groupby(group_columns).agg(Value=('Value', 'sum')).reset_index()

# Sanity checks
grouped_negative_emissions = negative_emissions.groupby(['Scenario', 'Period']).Value.sum()
for (scenario, period), value in grouped_negative_emissions.items():
    if zero_biofuel_emissions:
        logging.info("skip check")
        break
    negative_emissions_in_dataframe = combined_df[
        (combined_df.Scenario==scenario) &
        (combined_df.Period==period) &
        (combined_df.Fuel.isin(['Biodiesel', 'Drop-In Jet', 'Drop-In Diesel'])) &
        (combined_df.Parameters=='Emissions')].Value.sum() * 1000
    assert(abs(negative_emissions_in_dataframe - value) < 1E-6)
    logging.info(f"Check output matches negative emissions for Scenario: {scenario}, Period: {period}, Summed Value: {value:.2f}: OK")

grouped_biodiesel_production = biodiesel.groupby(['Scenario', 'Period']).Value.sum()
for (scenario, period), value in grouped_biodiesel_production.items():
    biodiesel_in_dataframe = combined_df[
        (combined_df.Scenario==scenario) &
        (combined_df.Period==period) &
        (combined_df.Fuel=='Biodiesel') &
        (combined_df.Parameters=='Fuel Consumption')].Value.sum()
    assert(abs(biodiesel_in_dataframe - value) < 1E-6)
    logging.info(f"Check output matches biodiesel production for Scenario: {scenario}, Period: {period}, Summed Value: {value:.2f}: OK")

grouped_drop_in_diesel_production = drop_in_diesel.groupby(['Scenario', 'Period']).Value.sum()
for (scenario, period), value in grouped_drop_in_diesel_production.items():
    drop_in_diesel_in_dataframe = combined_df[
        (combined_df.Scenario==scenario) &
        (combined_df.Period==period) &
        (combined_df.Fuel=='Drop-In Diesel') &
        (combined_df.Parameters=='Fuel Consumption')].Value.sum()
    assert(abs(drop_in_diesel_in_dataframe - value) < 1E-6)
    logging.info(f"Check output matches drop-in diesel production for Scenario: {scenario}, Period: {period}, Summed Value: {value:.2f}: OK")

grouped_drop_in_jet_production = drop_in_jet.groupby(['Scenario', 'Period']).Value.sum()
for (scenario, period), value in grouped_drop_in_jet_production.items():
    drop_in_jet_in_dataframe = combined_df[
        (combined_df.Scenario==scenario) &
        (combined_df.Period==period) &
        (combined_df.Fuel=='Drop-In Jet') &
        (combined_df.Parameters=='Fuel Consumption')].Value.sum()
    assert(abs(drop_in_jet_in_dataframe - value) < 1E-6)
    logging.info(f"Check output matches drop-in jet production for Scenario: {scenario}, Period: {period}, Summed Value: {value:.2f}: OK")

total_emissions = raw_df[raw_df.Commodity=='TOTCO2'].groupby(['Scenario', 'Period']).Value.sum()
for (scenario, period), value in total_emissions.items():
    emissions_in_dataframe = combined_df[
        (combined_df.Scenario==scenario) &
        (combined_df.Period==period) &
        (combined_df.Parameters=='Emissions')].Value.sum() * 1000
    if abs(emissions_in_dataframe - value) > 1E-6 and emissions_in_dataframe < value:
        logging.info(f"WARNING: emissions in output for Scenario: {scenario}, Period: {period} ({emissions_in_dataframe:.2f}) is missing some TOTCO2 emissions in raw TIMES output: ({value:.2f})")

logging.info(raw_df[raw_df.Commodity.str.contains('TOTCO2')].groupby(['Scenario', 'Period']).Value.sum()*2)
logging.info(raw_df[raw_df.Commodity.str.contains('CO2')].groupby(['Scenario', 'Period']).Value.sum())

save(combined_df, f'../data/output/output_combined_df_v{VERSION_STR}.csv')
logging.info(f"The combined DataFrame has been saved to ../data/output/output_combined_df_v{VERSION_STR}.csv")