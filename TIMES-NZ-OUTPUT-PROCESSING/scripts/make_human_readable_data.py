"""
Aim is to replicate the intended functionality of the inherited script 'New_Data_Processing.R'
"""

import os
import sys
import logging
import argparse
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
import numpy as np
import pandas as pd

parser = argparse.ArgumentParser(description='Process VEDA data to create a human-readable schema')
parser.add_argument('version', type=str, help='The version number')
args = parser.parse_args()
os.environ['TIMES_NZ_VERSION'] = args.version

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'library'))

from constants import *
from rulesets import *
from helpers import *


#### CONSTANTS

fix_multiple_fout = True

zero_biofuel_emissions = False

group_columns = ['Scenario', 'Sector', 'Subsector', 'Technology', 'Enduse', 'Unit', 'Parameters', 'Fuel', 'Period', 'FuelGroup', 'Technology_Group']

RENEWABLE_FUEL_ALLOCATION_RULES = [
    ({"FuelSourceProcess": "SUP_BIGNGA", "Commodity": "NGA"}, "inplace", {"Fuel": "Biogas"}),
    ({"FuelSourceProcess": "SUP_H2NGA", "Commodity": "NGA"}, "inplace", {"Fuel": "Natural Gas From Green Hydrogen"}),
    ({"FuelSourceProcess": "CT_COILBDS", "Commodity": "BDSL"}, "inplace", {"Fuel": "Biodiesel"}),
    ({"FuelSourceProcess": "CT_CWODDID", "Commodity": "DID"}, "inplace", {"Fuel": "Drop-In Diesel"}),
    ({"FuelSourceProcess": "CT_CWODDID", "Commodity": "DIJ"}, "inplace", {"Fuel": "Drop-In Jet"}),
    ({"FuelSourceProcess": "IMPDIJ", "Commodity": "DIJ"}, "inplace", {"Fuel": "Drop-In Jet"}),
]

THOUSAND_VEHICLE_RULES = [
    ({"Sector": "Transport", "Subsector": "Road Transport",# "Technology": "Plug-In Hybrid Vehicle",
      "Unit": "000 Vehicles"}, "inplace", {"Unit": "Number of Vehicles (Thousands)"}),
]

SCENARIO_INPUT_FILES = {
    'Kea': f'../../TIMES-NZ-GAMS/scenarios/kea-v{VERSION_STR}/kea-v{VERSION_STR}.vd',
    'Tui': f'../../TIMES-NZ-GAMS/scenarios/tui-v{VERSION_STR}/tui-v{VERSION_STR}.vd'
}


needed_attributes = ['VAR_Cap', 'VAR_FIn', 'VAR_FOut']
non_emission_fuel = ['Electricity', 'Wood', 'Hydrogen', 'Hydro', 'Wind', 'Solar', 'Biogas']
commodity_map = process_map_from_commodity_groups(ITEMS_LIST_COMMODITY_GROUPS_CSV)
commodities_by_type = commodities_by_type_from_commodity_groups(ITEMS_LIST_COMMODITY_GROUPS_CSV)
end_use_commodities = commodities_by_type['DEMO']
end_use_processes = commodity_map[commodity_map.Commodity.isin(end_use_commodities)].Process.unique()
commodity_units = {x[0]['Commodity']: x[2]['Unit'] for x in commodity_unit_rules}
process_sectors = {x[0]['Process']: x[2]['Sector'] for x in process_rules}
sector_emission_types = {
    '': 'TOTCO2',
    'Industry': 'INDCO2',
    'Residential' : 'RESCO2',
    'Agriculture' : 'AGRCO2',
    'Electricity' : 'ELCCO2',
    'Transport' : 'TRACO2',
    'Green Hydrogen': 'TOTCO2',
    'Primary Fuel Supply': 'TOTCO2',
    'Commercial': 'COMCO2'
}
end_use_process_emission_types = {x: sector_emission_types[process_sectors[x]] for x in end_use_processes}


#### FUNCTIONS ####

def generate_schema():

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
    for name, ruleset in RULESETS:
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
    logging.info("The files have been concatenated and saved to %s", OUTPUT_SCHEMA_FILEPATH)


def units_consistent(commodity_flow_dict):
     # Check if all units are the same
     return len(set([commodity_units[commodity] for commodity in commodity_flow_dict])) == 1

def trace_commodities(process, scenario, period, df, path=None, fraction=1):
    """
    Trace the output commodities of a process (e.g. Biodiesel blending) all the way through
    to end-use commodities (e.g. bus transportation) to determine what fraction of its output
    (e.g. blended diesel) ends up being used to provide each end-use commodity.
    """
    if path is None:
        path = []
    if len(path) > 100:
        logging.error("Path too long, likely a circular reference")
        logging.error(path)
        raise ValueError("Path too long, likely a circular reference")
    # Extend path with the current process
    current_path = path + [process]
    # Get output flows from the current process
    output_flows = process_output_flows(process, scenario, period, df)
    # This implementation assumes that everything has the same units
    assert(units_consistent(output_flows))
    # Calculate fractional flows for each output commodity
    output_fracs = flow_fractions(output_flows)
    # Resulting dictionary to keep track of the final fractional attributions
    result = {}
    for commodity in output_flows.keys():
        # Get the input flows for the commodity across different processes
        input_flows = commodity_input_flows(commodity, scenario, period, df)
        # If the commodity does not flow into any other processes, it is terminal
        if not input_flows:
            # Save the path and fraction up to this point
            result[tuple(current_path + [commodity])] = fraction * output_fracs[commodity]
        else:
            input_fracs = flow_fractions(input_flows)
            # Recursively trace downstream processes
            for downstream_process, input_fraction in input_fracs.items():
                ####    continue
                # Calculate new fraction as current fraction * fraction of this commodity's output used by the downstream process
                new_fraction = fraction * output_fracs[commodity] * input_fraction
                # Merge results from recursion
                result.update(trace_commodities(downstream_process, scenario, period, df, current_path + [commodity], new_fraction))
    return result

def end_use_fractions(process, scenario, period, df, filter_to_commodities=None):
    # Return a dictionary of emissions from end-use processes
    trace_result = trace_commodities(process, scenario, period, df)
    # Ensure the sum of all terminal fractions is approximately 1
    assert(abs(sum(trace_result.values()) - 1) < 1e-5)
    end_use_fractions = pd.DataFrame(
         [{'Scenario': scenario,
         'Attribute': 'VAR_FOut',
         'Commodity': None,
         'Process': process,
         'Period': period,
         'Value': None} for process in end_use_processes]
    )
    # Loop through the trace_result dictionary
    for key, value in trace_result.items():
        process_chain = key  # This is the tuple containing the process chain
        fuel_source_process = process_chain[0] # First entry which is the fuel source process
        process = process_chain[-2]  # Penultimate entry which is the process
        commodity = process_chain[1]  # Second entry which is the commodity
        end_use_fractions.loc[end_use_fractions['Process'] == process, 'Value'] = value
        end_use_fractions.loc[end_use_fractions['Process'] == process, 'Commodity'] = commodity
        end_use_fractions.loc[end_use_fractions['Process'] == process, 'FuelSourceProcess'] = fuel_source_process
    if filter_to_commodities is not None:
        end_use_fractions = end_use_fractions[(end_use_fractions['Commodity'].isin(filter_to_commodities)) | (end_use_fractions['Commodity'].isna())]
    end_use_fractions.Value = end_use_fractions.Value / end_use_fractions.Value.sum()
    return end_use_fractions

def complete_expand_dim(df, expand_dim, fill_value_dict):
    original_column_order = df.columns
    # This implementation assumes no NaN values in the starting DataFrame
    assert not df.isnull().values.any(), "DataFrame contains NaN values"
    # Get all columns except the one to expand
    defcols = [expand_dim] + list(fill_value_dict.keys()) # defined columns
    columns = [x for x in df.columns if x not in defcols] # derived from data
    # Form a DataFrame with all combinations of the unique values of the other dimensions
    _df = df.copy().drop(columns=defcols).drop_duplicates()
    _df['key'] = 1
    # Get all unique values for the expansion dimension
    # Create a DataFrame with all expand_dim values and the same key
    expand_values = df[expand_dim].unique()
    expand_df = pd.DataFrame({expand_dim: expand_values, 'key': 1})
    # Combine the unique values of the expand_dim with the original DataFrame using the key
    # This creates a DataFrame where each row of the original is repeated for each unique value of the expand_dim
    df_expanded = pd.merge(_df, expand_df, on='key').drop(columns='key')
    # Merge the expanded DataFrame with the original DataFrame to fill in the missing values
    df_full = pd.merge(df_expanded, df, on=columns + [expand_dim], how='left')
    # for each column in fill_value_dict, fill in the missing values with the specified default
    for (col, fill_value) in fill_value_dict.items():
        df_full[col] = df_full[col].fillna(fill_value)
    return df_full[original_column_order]


#### MAIN ####

os.makedirs('../data/output', exist_ok=True)

generate_schema()

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
schema_all = pd.read_csv(f'../data/output/output_schema_df_v{VERSION_STR}.csv')
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
    trace_result = trace_commodities(row['Process'], row['Scenario'], row['Period'], raw_df)
    # Get the fractional attributions of the process output to end-use processes
    end_use_allocations = end_use_fractions(row['Process'], row['Scenario'], row['Period'], raw_df)
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
for name, ruleset in RULESETS + [('process_enduse_rules', process_enduse_rules)]:
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
    trace_result = trace_commodities(row['Process'], row['Scenario'], row['Period'], raw_df)
    trace_result = [x for x in trace_result if x[1]==row['Commodity']]
    end_use_allocations = end_use_fractions(row['Process'], row['Scenario'], row['Period'], raw_df, filter_to_commodities=['BDSL']).dropna()
    end_use_allocations['Value'] *= row['Value']
    end_use_allocations['Attribute'] = 'VAR_FIn'
    end_use_allocations['Commodity'] = 'BDSL'
    end_use_allocations = apply_rules(end_use_allocations, RENEWABLE_FUEL_ALLOCATION_RULES)
    end_use_allocations.dropna(inplace=True)
    biodiesel_rows_to_add = pd.concat([biodiesel_rows_to_add, end_use_allocations], ignore_index=True)
for name, ruleset in RULESETS + [('process_enduse_rules', process_enduse_rules)]:
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
    trace_result = trace_commodities(row['Process'], row['Scenario'], row['Period'], raw_df)
    trace_result = [x for x in trace_result if x[1]==row['Commodity']]
    end_use_allocations = end_use_fractions(row['Process'], row['Scenario'], row['Period'], raw_df, filter_to_commodities=['DID']).dropna()
    end_use_allocations['Value'] *= row['Value']
    end_use_allocations['Attribute'] = 'VAR_FIn'
    end_use_allocations['Commodity'] = 'DID'
    end_use_allocations = apply_rules(end_use_allocations, RENEWABLE_FUEL_ALLOCATION_RULES)
    end_use_allocations.dropna(inplace=True)
    drop_in_diesel_rows_to_add = pd.concat([drop_in_diesel_rows_to_add, end_use_allocations], ignore_index=True)
for name, ruleset in RULESETS + [('process_enduse_rules', process_enduse_rules)]:
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
    trace_result = trace_commodities(row['Process'], row['Scenario'], row['Period'], raw_df)
    trace_result = [x for x in trace_result if x[1]==row['Commodity']]
    end_use_allocations = end_use_fractions(row['Process'], row['Scenario'], row['Period'], raw_df, filter_to_commodities=['DIJ'])
    
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
for name, ruleset in RULESETS + [('process_enduse_rules', process_enduse_rules)]:
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
output_df = combined_df.groupby(group_columns).agg(Value=('Value', 'sum')).reset_index()

all_periods = np.sort(combined_df['Period'].unique())
categories = [x for x in group_columns if x != 'Period']
complete_df = combined_df.groupby(categories).apply(add_missing_periods(all_periods)).reset_index(drop=True)

complete_df = complete_df.groupby(group_columns).agg(Value=('Value', 'sum')).reset_index()
complete_df = apply_rules(complete_df, THOUSAND_VEHICLE_RULES)
complete_df = complete_expand_dim(complete_df, 'Scenario', {'Value': 0})
complete_df = complete_df.sort_values(by=group_columns)

# Sanity checks
grouped_negative_emissions = negative_emissions.groupby(['Scenario', 'Period']).Value.sum()
for (scenario, period), value in grouped_negative_emissions.items():
    if zero_biofuel_emissions:
        logging.info("skip check")
        break
    negative_emissions_in_dataframe = complete_df[
        (complete_df.Scenario==scenario) &
        (complete_df.Period==period) &
        (complete_df.Fuel.isin(['Biodiesel', 'Drop-In Jet', 'Drop-In Diesel'])) &
        (complete_df.Parameters=='Emissions')].Value.sum() * 1000
    assert(abs(negative_emissions_in_dataframe - value) < 1E-6)
    logging.info(f"Check output matches negative emissions for Scenario: {scenario}, Period: {period}, Summed Value: {value:.2f}: OK")

grouped_biodiesel_production = biodiesel.groupby(['Scenario', 'Period']).Value.sum()
for (scenario, period), value in grouped_biodiesel_production.items():
    biodiesel_in_dataframe = complete_df[
        (complete_df.Scenario==scenario) &
        (complete_df.Period==period) &
        (complete_df.Fuel=='Biodiesel') &
        (complete_df.Parameters=='Fuel Consumption')].Value.sum()
    assert(abs(biodiesel_in_dataframe - value) < 1E-6)
    logging.info(f"Check output matches biodiesel production for Scenario: {scenario}, Period: {period}, Summed Value: {value:.2f}: OK")

grouped_drop_in_diesel_production = drop_in_diesel.groupby(['Scenario', 'Period']).Value.sum()
for (scenario, period), value in grouped_drop_in_diesel_production.items():
    drop_in_diesel_in_dataframe = complete_df[
        (complete_df.Scenario==scenario) &
        (complete_df.Period==period) &
        (complete_df.Fuel=='Drop-In Diesel') &
        (complete_df.Parameters=='Fuel Consumption')].Value.sum()
    assert(abs(drop_in_diesel_in_dataframe - value) < 1E-6)
    logging.info(f"Check output matches drop-in diesel production for Scenario: {scenario}, Period: {period}, Summed Value: {value:.2f}: OK")

grouped_drop_in_jet_production = drop_in_jet.groupby(['Scenario', 'Period']).Value.sum()
for (scenario, period), value in grouped_drop_in_jet_production.items():
    drop_in_jet_in_dataframe = complete_df[
        (complete_df.Scenario==scenario) &
        (complete_df.Period==period) &
        (complete_df.Fuel=='Drop-In Jet') &
        (complete_df.Parameters=='Fuel Consumption')].Value.sum()
    assert(abs(drop_in_jet_in_dataframe - value) < 1E-6)
    logging.info(f"Check output matches drop-in jet production for Scenario: {scenario}, Period: {period}, Summed Value: {value:.2f}: OK")

total_emissions = raw_df[raw_df.Commodity=='TOTCO2'].groupby(['Scenario', 'Period']).Value.sum()
for (scenario, period), value in total_emissions.items():
    emissions_in_dataframe = complete_df[
        (complete_df.Scenario==scenario) &
        (complete_df.Period==period) &
        (complete_df.Parameters=='Emissions')].Value.sum() * 1000
    if abs(emissions_in_dataframe - value) > 1E-6 and emissions_in_dataframe < value:
        logging.info(f"WARNING: emissions in output for Scenario: {scenario}, Period: {period} ({emissions_in_dataframe:.2f}) is missing some TOTCO2 emissions in raw TIMES output: ({value:.2f})")

logging.info(raw_df[raw_df.Commodity.str.contains('TOTCO2')].groupby(['Scenario', 'Period']).Value.sum()*2)
logging.info(raw_df[raw_df.Commodity.str.contains('CO2')].groupby(['Scenario', 'Period']).Value.sum())

save(complete_df, f'../data/output/output_combined_df_v{VERSION_STR}.csv')
logging.info(f"The combined DataFrame has been saved to ../data/output/output_combined_df_v{VERSION_STR}.csv")