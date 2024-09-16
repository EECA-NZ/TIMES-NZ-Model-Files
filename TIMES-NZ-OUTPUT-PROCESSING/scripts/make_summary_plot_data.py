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

raw_df = pd.read_csv(f'../data/output/output_raw_df_v{VERSION_STR}.csv')
combined_df = pd.read_csv(f'../data/output/output_combined_df_v{VERSION_STR}.csv')

kea_emissions_df = raw_df[raw_df.Commodity.str.contains('CO2') & (raw_df.Period==2018) & (raw_df.Commodity != 'TOTCO2') & (raw_df.Scenario=='Kea')]
tui_emissions_df = raw_df[raw_df.Commodity.str.contains('CO2') & (raw_df.Period==2018) & (raw_df.Commodity != 'TOTCO2') & (raw_df.Scenario=='Tui')]
combined_df[(combined_df.Parameters=='Emissions') & (combined_df.Period==2018) & (combined_df.Scenario=='Kea')].Value.sum()


# Check emissions units consistent
emissions_units = combined_df[combined_df.Parameters=='Emissions'].Unit.unique()
assert(len(emissions_units)==1)


# All Energy Related Emissions - Kea: 29.4 MtCO2e-7.06 MtCO2e
all_energy_related_emissions = {}
for scenario in combined_df.Scenario.unique():
    all_energy_related_emissions[scenario] = combined_df[
        (combined_df.Scenario==scenario) &
        (combined_df.Parameters=='Emissions')
    ].groupby(['Scenario', 'Period']).Value.sum().reset_index()

# All Energy Related Cumulative Emissions - Kea: 29.4 MtCO2e-642 MtCO2e
all_energy_related_cumulative_emissions = {}
for scenario in all_energy_related_emissions:
    all_energy_related_cumulative_emissions[scenario] = all_energy_related_emissions[scenario].Value.cumsum()


# Electricity Generation from Solar - Kea: 0.635 PJ-31.3 MtCO2e (lower at end than tui)
electricity_generation_from_solar = {}
for scenario in combined_df.Scenario.unique():
    electricity_generation_from_solar[scenario] = combined_df[
        (combined_df.Scenario==scenario) &
        (combined_df.Fuel=='Solar') &
        (combined_df.Enduse=='Electricity Production')
    ].groupby(['Scenario', 'Period']).Value.sum().reset_index()


# Electrification (Percent) - Kea: 24.8%-59.3%
electrification_percentage = {}
total_energy_use = {}
total_electricity_use = {}
for scenario in combined_df.Scenario.unique():
    total_energy_use[scenario] = combined_df[
        (combined_df.Scenario==scenario)
    ].groupby(['Scenario', 'Period']).Value.sum().reset_index()
    total_electricity_use[scenario] = combined_df[
        (combined_df.Scenario==scenario) &
        (combined_df.Fuel == 'Electricity')
    ].groupby(['Scenario', 'Period']).Value.sum().reset_index()
    electrification_percentage[scenario] = 100 * \
        total_electricity_use[scenario].Value / \
    (total_energy_use[scenario].Value + total_electricity_use[scenario].Value)

# Industrial Emissions (MtCO2e) - Kea: 6.62 MtCO2e - 3.04 MtCO2e
industrial_emissions = {}
for scenario in combined_df.Scenario.unique():
    industrial_emissions[scenario] = combined_df[
        (combined_df.Scenario==scenario) &
        (combined_df.Parameters=='Emissions') &
        (combined_df.Sector=='Industry')
    ].groupby(['Scenario', 'Period']).Value.sum().reset_index()


# Renewable Electricity (Percent) - Kea: 84%-93.2% (lower at end than tui)
renewable_electricity_percentage = {}
renewable_electricity = {}
total_electricity = {}
for scenario in combined_df.Scenario.unique():
    renewable_electricity[scenario] = combined_df[
        (combined_df.Scenario==scenario) &
        (combined_df.Parameters=='Electricity Generation') &
        (combined_df.Fuel.isin(['Electricity', 'Hydro', 'Geothermal', 'Solar', 'Wind']))
    ].groupby(['Scenario', 'Period']).Value.sum()
    total_electricity[scenario] = combined_df[
        (combined_df.Scenario==scenario) &
        (combined_df.Parameters=='Electricity Generation')
    ].groupby(['Scenario', 'Period']).Value.sum()
    renewable_electricity_percentage[scenario] = 100 * renewable_electricity[scenario] / total_electricity[scenario]


# Renewable Energy (Percent) - Kea: 35%-82.7%
renewable_energy_percentage = {}
renewable_energy = {}
total_energy = {}
for scenario in combined_df.Scenario.unique():
    renewable_energy[scenario] = combined_df[
        (combined_df.Scenario==scenario) &
        (combined_df.Parameters.isin(['Electricity Generation', 'Fuel Consumption'])) &
        (combined_df.Fuel.isin(['Wood', 'Geothermal', 'Biogas', 'Drop-In Diesel', 'Hydro', 'Solar', 'Waste Incineration', 'Wind', 'Drop-In Jet', 'Biodiesel']))
    ]
    total_energy[scenario] = combined_df[
        (combined_df.Scenario==scenario) &
        (combined_df.Parameters.isin(['Electricity Generation', 'Fuel Consumption'])) &
        ~(combined_df.Fuel.isin(['Green Hydrogen', 'Electricity']))
    ]
    renewable_energy_percentage[scenario] = 100 * \
        renewable_energy[scenario].groupby(['Scenario', 'Period']).Value.sum() / \
        total_energy[scenario].groupby(['Scenario', 'Period']).Value.sum()

# Transport Emissions - Kea: 15.9%-2.16%



def base_year_energy_use(fuel):
    return total_energy[scenario][total_energy[scenario].Fuel==fuel].groupby('Period').Value.sum().loc[2018]

base_year_energy_use('LPG')
fuels = total_energy[scenario].Fuel.unique()
print(fuels)
for fuel in fuels:
    print(fuel, " : ", base_year_energy_use(fuel))