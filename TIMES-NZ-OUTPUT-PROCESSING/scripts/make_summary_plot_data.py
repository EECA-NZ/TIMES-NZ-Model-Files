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

INSIGHTCOLS = ['Title', 'Parameter', 'Scenario', 'Units', 2018, 2025, 2030, 2035, 2040, 2045, 2050, 2055, 2060]

clean_df = pd.read_csv(f'../data/output/output_clean_df_v{VERSION_STR}.csv')
clean_df['IsEnduse'] = (clean_df.ProcessSet=='.DMD.') | (clean_df.CommoditySet=='.DEM.')

assert clean_df[clean_df.Commodity.str.contains('CO2')].Parameters.unique().tolist() == ['Emissions'], "Emissions found not labelled as 'Emissions'"
assert clean_df[(clean_df.Parameters == 'Emissions') & (clean_df.Value!=0)].Commodity.str.contains('CO2').all(), "All Emissions rows should be CO2"

emissions_summary_rows = clean_df[clean_df.Parameters=='Emissions'].groupby(
    ['Scenario', 'Period']).Value.sum().reset_index().pivot(
        index='Scenario', columns='Period', values='Value'
    ).reset_index().rename_axis(None, axis=1)
emissions_summary_rows['Title'] = 'All energy related annual emissions'
emissions_summary_rows['Parameter'] = 'All Energy Related Annual Emissions'
emissions_summary_rows['Units'] = 'MtCO₂' #'MtCO<sub>2</sub>'
emissions_summary_rows = emissions_summary_rows[INSIGHTCOLS]

cumulative_emissions_summary_rows = emissions_summary_rows.copy()
year_columns = [col for col in cumulative_emissions_summary_rows.columns if isinstance(col, int)]
# Need to account for the fact that we don't have annual data so we need to multiply by the number of years which is 5
cumulative_emissions_summary_rows[year_columns] = cumulative_emissions_summary_rows[year_columns].cumsum(axis=1) * 5
cumulative_emissions_summary_rows['Title'] = 'All energy related cumulative emissions'
cumulative_emissions_summary_rows['Parameter'] = 'All Energy Related Cumulative Emissions'
cumulative_emissions_summary_rows = cumulative_emissions_summary_rows[INSIGHTCOLS]

electricity_generation_from_solar = clean_df[
    (clean_df.Fuel=='Solar') &
    (clean_df.Enduse=='Electricity Production') &
    (clean_df.Attribute=='VAR_FOut') &
    (clean_df.ProcessSet=='.ELE.')].groupby(
    ['Scenario', 'Period']).Value.sum().reset_index().pivot(
        index='Scenario', columns='Period', values='Value'
    ).reset_index().rename_axis(None, axis=1)
electricity_generation_from_solar['Title'] = 'Electricity generation from solar'
electricity_generation_from_solar['Parameter'] = 'Electricity Generation from Solar'
electricity_generation_from_solar['Units'] = 'PJ'
electricity_generation_from_solar = electricity_generation_from_solar[INSIGHTCOLS]

electricity_consumption = clean_df[(clean_df.Parameters=='Fuel Consumption') & clean_df.IsEnduse & (clean_df.Fuel=='Electricity')].groupby(['Scenario', 'Period']).Value.sum()
total_energy_consumption = clean_df[(clean_df.Parameters=='Fuel Consumption') & clean_df.IsEnduse].groupby(['Scenario', 'Period']).Value.sum()
electricity_consumption_percentage = electricity_consumption / total_energy_consumption * 100
electricity_consumption_percentage = electricity_consumption_percentage.reset_index().pivot(
    index='Scenario', columns='Period', values='Value'
).reset_index().rename_axis(None, axis=1)
electricity_consumption_percentage['Title'] = 'Electrification'
electricity_consumption_percentage['Parameter'] = 'Electrification'
electricity_consumption_percentage['Units'] = '%'
electricity_consumption_percentage = electricity_consumption_percentage[INSIGHTCOLS]

industry_emissions_summary_rows = clean_df[(clean_df.Parameters=='Emissions') & (clean_df.Sector=='Industry')].groupby(
    ['Scenario', 'Period']).Value.sum().reset_index().pivot(
        index='Scenario', columns='Period', values='Value'
    ).reset_index().rename_axis(None, axis=1)
industry_emissions_summary_rows['Title'] = 'Industrial Emissions'
industry_emissions_summary_rows['Parameter'] = 'Industrial Emissions'
industry_emissions_summary_rows['Units'] = 'MtCO₂'
industry_emissions_summary_rows = industry_emissions_summary_rows[INSIGHTCOLS]


assert clean_df[clean_df.Parameters=='Electricity Generation'].FuelGroup.unique().tolist() == ['Renewables (direct use)', 'Fossil Fuels'], 'Electricity Generation found outside of expected FuelGroups'
renewable_electricity_generation = clean_df[(clean_df.Parameters=='Electricity Generation') & (clean_df.FuelGroup=='Renewables (direct use)')].groupby(['Scenario', 'Period']).Value.sum()
total_electricity_generation = clean_df[(clean_df.Parameters=='Electricity Generation')].groupby(['Scenario', 'Period']).Value.sum()
renewable_electricity_percentage = renewable_electricity_generation / total_electricity_generation * 100
renewable_electricity_percentage = renewable_electricity_percentage.reset_index().pivot(
    index='Scenario', columns='Period', values='Value'
).reset_index().rename_axis(None, axis=1)
renewable_electricity_percentage['Title'] = 'Renewable Electricity'
renewable_electricity_percentage['Parameter'] = 'Renewable Electricity'
renewable_electricity_percentage['Units'] = '%'
renewable_electricity_percentage = renewable_electricity_percentage[INSIGHTCOLS]

direct_renewable_enduse = clean_df[(clean_df.Parameters=='Fuel Consumption') & clean_df.IsEnduse & (clean_df.FuelGroup=='Renewables (direct use)')].groupby(['Scenario', 'Period']).Value.sum()
electricity_enduse = clean_df[(clean_df.Parameters=='Fuel Consumption') & clean_df.IsEnduse & (clean_df.Fuel=='Electricity')].groupby(['Scenario', 'Period']).Value.sum()
renewable_electricity_enduse = electricity_enduse * renewable_electricity_generation / total_electricity_generation
total_enduse = clean_df[(clean_df.Parameters=='Fuel Consumption') & clean_df.IsEnduse].groupby(['Scenario', 'Period']).Value.sum()
renewable_energy_enduse_percentage = (direct_renewable_enduse + renewable_electricity_enduse) / total_enduse * 100
renewable_energy_enduse_percentage = renewable_energy_enduse_percentage.reset_index().pivot(
    index='Scenario', columns='Period', values='Value'
).reset_index().rename_axis(None, axis=1)
renewable_energy_enduse_percentage['Title'] = 'Renewable Energy'
renewable_energy_enduse_percentage['Parameter'] = 'Renewable Energy'
renewable_energy_enduse_percentage['Units'] = '%'
renewable_energy_enduse_percentage = renewable_energy_enduse_percentage[INSIGHTCOLS]

transport_emissions_summary_rows = clean_df[(clean_df.Parameters=='Emissions') & (clean_df.Sector=='Transport')].groupby(
    ['Scenario', 'Period']).Value.sum().reset_index().pivot(
        index='Scenario', columns='Period', values='Value'
    ).reset_index().rename_axis(None, axis=1)
transport_emissions_summary_rows['Title'] = 'Transport Emissions'
transport_emissions_summary_rows['Parameter'] = 'Transport Emissions'
transport_emissions_summary_rows['Units'] = 'MtCO₂'
transport_emissions_summary_rows = transport_emissions_summary_rows[INSIGHTCOLS]

summary = pd.concat(
    [emissions_summary_rows,
     cumulative_emissions_summary_rows,
     electricity_generation_from_solar,
     transport_emissions_summary_rows,
     industry_emissions_summary_rows,
     renewable_electricity_percentage,
     renewable_energy_enduse_percentage,
     electricity_consumption_percentage], ignore_index=True).replace('Tui', 'Tūī')

print(summary)

summary.to_csv(f'..\..\TIMES-NZ-VISUALISATION\data\key_insight.csv', index=False)