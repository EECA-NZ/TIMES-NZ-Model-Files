"""
This script uses posts-processed TIMES-NZ data adn produces a table of summary results
for the key insights of the model. This table is then saved to a CSV file for use in
the visualisation.
"""

import os
import sys
import logging
import argparse
from pathlib import Path
import pandas as pd

current_dir = Path(__file__).resolve().parent
os.chdir(current_dir)
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'library'))

# pylint: disable=wrong-import-position, wildcard-import, import-error
from constants import *

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

parser = argparse.ArgumentParser(
    description='Process VEDA data to create a human-readable schema')
parser.add_argument('version', type=str, help='The version number')
args = parser.parse_args()
VERSION_STR = args.version.replace('.', '_')
INSIGHTCOLS = ['Title', 'Parameter', 'Scenario', 'Units',
               2018, 2025, 2030, 2035, 2040, 2045, 2050, 2055, 2060]

clean_df = pd.read_csv(f'../data/output/output_clean_df_v{VERSION_STR}.csv')
clean_df['IsEnduse'] = (clean_df.ProcessSet == '.DMD.') | (
    clean_df.CommoditySet == '.DEM.')

assert clean_df[
    clean_df.Commodity.str.contains('CO2')
].Parameters.unique().tolist() == ['Emissions'], "Emissions found not labelled as 'Emissions'"
assert clean_df[
    (clean_df.Parameters == 'Emissions') & (clean_df.Value != 0)
].Commodity.str.contains('CO2').all(), "All Emissions rows should be CO2"

# Annual emissions is higher in the base year than previously reported.
# Query: is this because some emissions were not previously included --
# or is it because we are including inappropriate emissions?
emissions_summary_rows = clean_df[clean_df.Parameters == 'Emissions'].groupby(
    ['Scenario', 'Period']).Value.sum().reset_index().pivot(
        index='Scenario', columns='Period', values='Value'
).reset_index().rename_axis(None, axis=1)
emissions_summary_rows['Title'] = 'All energy related annual emissions'
emissions_summary_rows['Parameter'] = 'All Energy Related Annual Emissions'
emissions_summary_rows['Units'] = 'MtCO₂'
emissions_summary_rows = emissions_summary_rows[INSIGHTCOLS]

# Cumulative emissions appear to be being calculated in a similar manner to previously.
cumulative_emissions_summary_rows = emissions_summary_rows.copy()
year_columns = [
    col for col in cumulative_emissions_summary_rows.columns if isinstance(col, int)]
year_columns = sorted(year_columns)
for col in year_columns:
    cumulative_emissions_summary_rows[col] = pd.to_numeric(
        cumulative_emissions_summary_rows[col], errors='coerce')
all_years = list(range(min(year_columns), max(year_columns) + 1))
cumulative_emissions_summary_rows = cumulative_emissions_summary_rows.reindex(
    columns=cumulative_emissions_summary_rows.columns.tolist() +
    [y for y in all_years if y not in year_columns]
)
numeric_cols = sorted(
    [col for col in cumulative_emissions_summary_rows.columns if isinstance(col, int)])
non_numeric_cols = sorted(
    [col for col in cumulative_emissions_summary_rows.columns if not isinstance(col, int)])
# Adjust order based on your requirement
sorted_cols = non_numeric_cols + numeric_cols
cumulative_emissions_summary_rows = cumulative_emissions_summary_rows[sorted_cols]
cumulative_emissions_summary_rows[numeric_cols] = \
    cumulative_emissions_summary_rows[numeric_cols].interpolate(method='linear', axis=1)
cumulative_emissions_summary_rows[numeric_cols] = \
    cumulative_emissions_summary_rows[numeric_cols].cumsum(axis=1)
cumulative_emissions_summary_rows['Title'] = 'All energy related cumulative emissions'
cumulative_emissions_summary_rows['Parameter'] = 'All Energy Related Cumulative Emissions'
cumulative_emissions_summary_rows = cumulative_emissions_summary_rows[INSIGHTCOLS]

# Similar order of magnitude, more consistent between scenarios,
# Kea has more solar generation than Tui, unlike previously. Looks more believable?
electricity_generation_from_solar = clean_df[
    (clean_df.Fuel == 'Solar') &
    (clean_df.Enduse == 'Electricity Production') &
    (clean_df.Attribute == 'VAR_FOut') &
    (clean_df.ProcessSet == '.ELE.')].groupby(
    ['Scenario', 'Period']).Value.sum().reset_index().pivot(
        index='Scenario', columns='Period', values='Value'
).reset_index().rename_axis(None, axis=1)
electricity_generation_from_solar['Title'] = 'Electricity generation from solar'
electricity_generation_from_solar['Parameter'] = 'Electricity Generation from Solar'
electricity_generation_from_solar['Units'] = 'PJ'
electricity_generation_from_solar = electricity_generation_from_solar[INSIGHTCOLS]

# Electrification is lower than previously reported.
# Query: was it previously contaminated by double-counting due to energy transformation
# e.g. Natural Gas -> Electricity?
electricity_consumption = clean_df[
    (clean_df.Parameters == 'Fuel Consumption') &
    clean_df.IsEnduse &
    (clean_df.Fuel == 'Electricity')
    ].groupby(['Scenario', 'Period']).Value.sum()
total_energy_consumption = clean_df[
    (clean_df.Parameters == 'Fuel Consumption') &
     clean_df.IsEnduse
     ].groupby(['Scenario', 'Period']).Value.sum()
electricity_consumption_percentage = electricity_consumption / \
    total_energy_consumption * 100
electricity_consumption_percentage = electricity_consumption_percentage.reset_index().pivot(
    index='Scenario', columns='Period', values='Value'
).reset_index().rename_axis(None, axis=1)
electricity_consumption_percentage['Title'] = 'Electrification'
electricity_consumption_percentage['Parameter'] = 'Electrification'
electricity_consumption_percentage['Units'] = '%'
electricity_consumption_percentage = electricity_consumption_percentage[INSIGHTCOLS]

# The numbers have changed slightly but this looks very similar to previously reported data.
industry_emissions_summary_rows = clean_df[
        (clean_df.Parameters == 'Emissions') &
        (clean_df.Sector == 'Industry')
    ].groupby(['Scenario', 'Period']).Value.sum().reset_index().pivot(
        index='Scenario', columns='Period', values='Value'
    ).reset_index().rename_axis(None, axis=1)
industry_emissions_summary_rows['Title'] = 'Industrial Emissions'
industry_emissions_summary_rows['Parameter'] = 'Industrial Emissions'
industry_emissions_summary_rows['Units'] = 'MtCO₂'
industry_emissions_summary_rows = industry_emissions_summary_rows[INSIGHTCOLS]

# The numbers have changed slightly but this looks very similar to previously reported data.
assert clean_df[
        clean_df.Parameters == 'Electricity Generation'
    ].FuelGroup.unique().tolist() == ['Renewables (direct use)', 'Fossil Fuels'], \
    'Electricity Generation found outside of expected FuelGroups'
renewable_electricity_generation = clean_df[(clean_df.Parameters == 'Electricity Generation') & (
    clean_df.FuelGroup == 'Renewables (direct use)')].groupby(['Scenario', 'Period']).Value.sum()
total_electricity_generation = clean_df[(clean_df.Parameters == 'Electricity Generation')].groupby([
    'Scenario', 'Period']).Value.sum()
renewable_electricity_percentage = renewable_electricity_generation / \
    total_electricity_generation * 100
renewable_electricity_percentage = renewable_electricity_percentage.reset_index().pivot(
    index='Scenario', columns='Period', values='Value'
).reset_index().rename_axis(None, axis=1)
renewable_electricity_percentage['Title'] = 'Renewable Electricity'
renewable_electricity_percentage['Parameter'] = 'Renewable Electricity'
renewable_electricity_percentage['Units'] = '%'
renewable_electricity_percentage = renewable_electricity_percentage[INSIGHTCOLS]

# Renewable energy enduse is lower than previously reported.
# Query: is this because we are using a different definition of renewable energy enduse?
direct_renewable_enduse = clean_df[
        (clean_df.Parameters == 'Fuel Consumption') &
        clean_df.IsEnduse &
        (clean_df.FuelGroup == 'Renewables (direct use)')
    ].groupby(['Scenario', 'Period']).Value.sum()
electricity_enduse = clean_df[
        (clean_df.Parameters == 'Fuel Consumption') &
        clean_df.IsEnduse &
        (clean_df.Fuel == 'Electricity')
    ].groupby(['Scenario', 'Period']).Value.sum()
renewable_electricity_enduse = electricity_enduse * \
    renewable_electricity_generation / total_electricity_generation
total_enduse = clean_df[(clean_df.Parameters == 'Fuel Consumption')
                        & clean_df.IsEnduse].groupby(['Scenario', 'Period']).Value.sum()
renewable_energy_enduse_percentage = (
    direct_renewable_enduse + renewable_electricity_enduse) / total_enduse * 100
# Lower than the percentages previously reported.
# Did they use renewable fuel use instead of renewable electricity use? (E.g. Geothermal.)
renewable_energy_enduse_percentage = renewable_energy_enduse_percentage.reset_index().pivot(
    index='Scenario', columns='Period', values='Value'
).reset_index().rename_axis(None, axis=1)
renewable_energy_enduse_percentage['Title'] = 'Renewable Energy'
renewable_energy_enduse_percentage['Parameter'] = 'Renewable Energy'
renewable_energy_enduse_percentage['Units'] = '%'
renewable_energy_enduse_percentage = renewable_energy_enduse_percentage[INSIGHTCOLS]

# The numbers have changed slightly but this looks very similar to previously reported data.
transport_emissions_summary_rows = clean_df[
    (clean_df.Parameters == 'Emissions') &
    (clean_df.Sector == 'Transport')].groupby(
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

summary.to_csv(
    '../../TIMES-NZ-VISUALISATION/data/key_insight.csv', index=False)
