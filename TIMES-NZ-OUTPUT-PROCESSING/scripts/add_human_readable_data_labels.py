"""
The aim of this script is to replicate the intended functionality of the inherited script 'New_Data_Processing.R',
with previously manual steps automated. The script reads in the VEDA data files, applies a series of rules to clean
and transform the data, and then outputs an aggregated and labelled version of the data.

Usage: python add_human_readable_data_labels.py <version>
"""

import os
import sys
import logging
import argparse
import numpy as np
import pandas as pd
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

parser = argparse.ArgumentParser(description='Process VEDA data to create a human-readable schema')
parser.add_argument('version', type=str, help='The version number')
args = parser.parse_args()
version = args.version

current_dir = Path(__file__).resolve().parent
os.environ['TIMES_NZ_VERSION'] = version
sys.path.append(os.path.join(current_dir, '..', 'library'))

from constants import *
from helpers import *
from rulesets import *


#### MAIN ####

os.chdir(current_dir)

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
# the CO2 "sink" effects attributable to biofuels. To simplify communication, we proportionately redistribute these to the end-use processes.
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

# Label the data
for name, ruleset in DIRECT_RULESETS:
    logging.info("Applying ruleset: %s", name)
    main_df = apply_rules(main_df, ruleset)

## Read other necessary files
schema_technology = pd.read_csv('../../TIMES-NZ-VISUALISATION/data/schema_technology.csv')
schema_technology['Technology'] = schema_technology['Technology'].str.strip()

#### CLEANING
logging.info('Collect all "negative emissions" rows to attribute to end-use processes')
negative_emissions = main_df[(main_df['Attribute'] == "VAR_FOut") &
                             (main_df['Commodity'].str.contains("CO2")) &
                             (main_df['Value'] < 0)]
emissions_rows_to_add = allocate_to_enduse_processes(negative_emissions, main_df, commodity_units)
emissions_rows_to_add = apply_rulesets(emissions_rows_to_add, emissions_rulesets, subset_name = 'negative emissions')
# Create a dataframe with positive emissions associated with the "negative emissions" rows so that total emissions are unaffected.
emissions_rows_to_add = pd.concat([emissions_rows_to_add,
                                   negated_rows(negative_emissions, [])], ignore_index=True)
assert(emissions_rows_to_add.Value.sum() < TOL)

logging.info('Allocate biodiesel to end-use processes')
biodiesel_out = main_df[(main_df['Attribute'] == "VAR_FOut") &
                        (main_df['Commodity'] == "BDSL") &
                        (~main_df['Process'].apply(is_trade_process))]
biodiesel_rows_to_add = allocate_to_enduse_processes(biodiesel_out, main_df, commodity_units, filter_to_commodities=['BDSL'])
biodiesel_rows_to_add = apply_rulesets(biodiesel_rows_to_add, biodiesel_rulesets, subset_name = 'biodiesel')
biodiesel_rows_to_add = pd.concat([biodiesel_rows_to_add,
                                   negated_rows(biodiesel_rows_to_add, make_diesel_rules)], ignore_index=True)

logging.info('Allocate drop-in-diesel to end-use processes')
drop_in_diesel_out = main_df[(main_df['Attribute'] == "VAR_FOut") &
                             (main_df['Commodity'] == "DID") &
                             (~main_df['Process'].apply(is_trade_process))]
drop_in_diesel_rows_to_add = allocate_to_enduse_processes(drop_in_diesel_out, main_df, commodity_units, filter_to_commodities=['DID'])
drop_in_diesel_rows_to_add = apply_rulesets(drop_in_diesel_rows_to_add, drop_in_diesel_rulesets, subset_name = 'drop-in diesel')
drop_in_diesel_rows_to_add = pd.concat([drop_in_diesel_rows_to_add,
                                        negated_rows(drop_in_diesel_rows_to_add, make_diesel_rules)], ignore_index=True)

logging.info('Allocate drop-in-jet to end-use processes')
drop_in_jet_out = main_df[(main_df['Attribute'] == "VAR_FOut") &
                          (main_df['Commodity'] == "DIJ") &
                          (~main_df['Process'].apply(is_trade_process))]
drop_in_jet_domestic_rows_to_add = allocate_to_enduse_processes(drop_in_jet_out, main_df, commodity_units, filter_to_commodities=['DIJ'])
drop_in_jet_domestic_rows_to_add = apply_rulesets(drop_in_jet_domestic_rows_to_add, drop_in_jet_rulesets, subset_name = 'drop-in jet')
drop_in_jet_rows_to_add = spread_to_all_aviation(drop_in_jet_domestic_rows_to_add, main_df)
drop_in_jet_rows_to_add = pd.concat([drop_in_jet_rows_to_add,
                                     negated_rows(drop_in_jet_rows_to_add, make_jet_rules)], ignore_index=True)

# Bring together changes
rows_to_add = pd.concat([emissions_rows_to_add, biodiesel_rows_to_add, drop_in_diesel_rows_to_add, drop_in_jet_rows_to_add])

# Sanity checks - all added rows balance in terms of total value
assert(abs(rows_to_add.Value.sum()) < TOL)
assert(abs(rows_to_add[rows_to_add.Commodity.str.contains('CO2')].Value.sum()) < TOL)
assert(abs(rows_to_add[rows_to_add.Commodity=='DIJ'].Value.sum() +
           rows_to_add[rows_to_add.Commodity=='JET'].Value.sum()) < TOL)
assert(abs(rows_to_add[rows_to_add.Commodity=='BDSL'].Value.sum() +
           rows_to_add[rows_to_add.Commodity=='DID'].Value.sum() +
           rows_to_add[rows_to_add.Commodity=='DSL'].Value.sum()) < TOL)

# Same checks, grouped by scenario and year
assert(abs((rows_to_add.groupby(['Scenario', 'Period']).Value.sum().sum())) < TOL)
assert((rows_to_add[rows_to_add.Commodity.str.contains('CO2')].groupby(['Scenario', 'Period']).Value.sum().fillna(0).abs().max()) < TOL)
assert((rows_to_add[rows_to_add.Commodity=='DIJ'].groupby(['Scenario', 'Period']).Value.sum() +
        rows_to_add[rows_to_add.Commodity=='JET'].groupby(['Scenario', 'Period']).Value.sum()).fillna(0).abs().max() < TOL)
assert((rows_to_add[rows_to_add.Commodity=='BDSL'].groupby(['Scenario', 'Period']).Value.sum() +
        rows_to_add[rows_to_add.Commodity=='DID'].groupby(['Scenario', 'Period']).Value.sum() +
        rows_to_add[rows_to_add.Commodity=='DSL'].groupby(['Scenario', 'Period']).Value.sum()).fillna(0).abs().max() < TOL)

## Join operations
clean_df = pd.concat([main_df, rows_to_add], ignore_index=True)
clean_df = fixup_emissions_attributed_to_emitting_fuels(clean_df)

# Join with schema_technology to get the sector for each technology, first checking that no technologies are missing
check_missing_tech(clean_df, schema_technology)
logging.info("Checked that no end-use or electricity-generation technologies are missing from schema_technology.csv - OK")
clean_df = pd.merge(clean_df, schema_technology, on=['Technology'], how='left')

# Relabel the Electricity sector and all missing values as 'Other'
clean_df['Sector'] = np.where(clean_df['Sector'] == 'Electricity', 'Other', clean_df['Sector'])
clean_df = clean_df.fillna('Other')

# Convert emissions to Mt CO2/yr
clean_df.loc[clean_df['Parameters'] == 'Emissions', 'Value'] /= 1000
clean_df.loc[clean_df['Parameters'] == 'Emissions', 'Unit'] = 'Mt CO<sub>2</sub>/yr' #'Mt CO₂/yr'

# Remove unwanted rows and group data
clean_df = clean_df[(clean_df['Parameters'] != 'Annualised Capital Costs') & (clean_df['Parameters'] != 'Technology Capacity')]
clean_df = clean_df.groupby(['Attribute', 'Process', 'Commodity'] + GROUP_COLUMNS).agg(Value=('Value', 'sum')).reset_index()

# Find processes with multiple VAR_FOut rows (excluding emissions commodities) and split the VAR_FIn row across
# each of the end-uses obtained from the VAR_FOut rows, based on the ratio of VAR_FOut values
clean_df = fix_multiple_fout(clean_df)

# Write the clean data to a CSV file
all_periods = np.sort(clean_df['Period'].unique())
categories = [x for x in GROUP_COLUMNS if x != 'Period']
clean_df = clean_df.groupby(categories).apply(add_missing_periods(all_periods)).reset_index(drop=True)
clean_df = apply_rules(clean_df, THOUSAND_VEHICLE_RULES)
clean_df = complete_expand_dim(clean_df, 'Scenario', {'Value': 0})
clean_df = clean_df.sort_values(by=GROUP_COLUMNS)
clean_df = apply_rules(clean_df, ALWAYS_PRESENT_EMISSIONS_RULES)

check_enduse_rows(clean_df)
logging.info("Checked there are no missing values in end-use rows - Check OK")

check_electricity_fuel_consumption(clean_df)
logging.info("Checked electricity fuel consumption is only from electricity generation processes - Check OK")

logging.info("Check the data meets expectations")
sanity_check(negative_emissions, clean_df, {'Fuel': ['Biodiesel', 'Drop-In Jet', 'Drop-In Diesel'], 'Parameters': 'Emissions'}, TOL, factor=1000, name='negative emissions')
sanity_check(raw_df[raw_df.Commodity == 'TOTCO2'], clean_df, {'Parameters': 'Emissions'}, TOL, factor=1000, name='total emissions')
sanity_check(biodiesel_out, clean_df, {'Fuel': 'Biodiesel', 'Parameters': 'Fuel Consumption'}, TOL, name='biodiesel')
sanity_check(drop_in_diesel_out, clean_df, {'Fuel': 'Drop-In Diesel', 'Parameters': 'Fuel Consumption'}, TOL, name='drop-in diesel')
sanity_check(drop_in_jet_out, clean_df, {'Fuel': 'Drop-In Jet', 'Parameters': 'Fuel Consumption'}, TOL, name='drop-in jet')

save(raw_df, f'../data/output/output_raw_df_v{VERSION_STR}.csv')
logging.info(f"The raw DataFrame has been saved to ../data/output/output_raw_df_v{VERSION_STR}.csv")

save(main_df, f'../data/output/output_main_df_v{VERSION_STR}.csv')
logging.info(f"The main DataFrame has been saved to ../data/output/output_main_df_v{VERSION_STR}.csv")

save(clean_df, f'../data/output/output_clean_df_v{VERSION_STR}.csv')
logging.info(f"The cleaned DataFrame has been saved to ../data/output/output_vis_subset_df_v{VERSION_STR}.csv")