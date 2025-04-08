"""
This script is to find the load curves of the NI and SI and whole of NZ from the EA GXP data. The data from this will
then be used to produce more accurate time slices using what is already defined but changing the peak time to represent
the actual peak times a bit better than before.

Then want to find the load curves for industrial, commercial, and residential. (This is not happening just yet come back to me in a week)
"""

#region LIBRARIES
import sys 
import os 
import pandas as pd 
import numpy as np
import matplotlib.pyplot as plt

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, "../..", "library"))
from filepaths import DATA_INTERMEDIATE
from dataprep import *
#endregion

#region FILEPATHS
input_location = f"{DATA_INTERMEDIATE}/stage_1_external_data/electricity_authority"
Timeslice_output_location = f"{DATA_INTERMEDIATE}/stage_1_external_data/TimeSlices"
os.makedirs(Timeslice_output_location, exist_ok = True)

input_gxp_data = pd.read_parquet(f"{input_location}/emi_grid_export.parquet")
concordances = pd.read_csv(f"{input_location}/emi_nsp_concordances.csv")
#endregion

#region LOAD CURVES
concordances = concordances.rename(columns = {'POC' : 'GXP_prefix'})
#Determining which Island each GXP is on
input_gxp_data['GXP_prefix'] = input_gxp_data['POC'].str[:3]

# Select only 'prefix' and 'category' from the mapping DataFrame
concordance_subset = concordances[['GXP_prefix', 'Island']]

# Merge using the subset
input_gxp_data = input_gxp_data.merge(concordance_subset, on='GXP_prefix', how='left')

# Drop the 'prefix' column if no longer needed
input_gxp_data.drop(columns='GXP_prefix', inplace=True)

#Summing up per Island per day
load_data_per_island = input_gxp_data.groupby(['Island', 'Trading_Date', 'Trading_Period', 'Unit_Measure'])['Value'].sum().reset_index()


#determining if the Trading_Date is a weekday or weekend
load_data_per_island['Trading_Date'] = pd.to_datetime(load_data_per_island['Trading_Date'])
load_data_per_island['Day_Type'] = load_data_per_island['Trading_Date'].dt.weekday.map(lambda x: 'WE' if x >= 5 else 'WD')



#now adding in which season each trading date is in
conditions = [
    (load_data_per_island['Trading_Date'].dt.month.isin([12, 1, 2])),
    (load_data_per_island['Trading_Date'].dt.month.isin([3, 4, 5])),
    (load_data_per_island['Trading_Date'].dt.month.isin([6, 7, 8])),
    (load_data_per_island['Trading_Date'].dt.month.isin([9, 10, 11]))
]
choices = ['Summer', 'Autumn', 'Winter', 'Spring']

load_data_per_island['Season'] = np.select(conditions, choices, default='Unknown')

load_data_per_island.to_csv(f"{Timeslice_output_location}/load_data.csv", index = False)

#Grouping by season and day type 
load_season_day = load_data_per_island.groupby(['Island', 'Season', 'Day_Type','Trading_Period', 'Unit_Measure'])['Value'].mean().reset_index()
#Removing rows with a TP of 49 or 50 (IDK why EA has those since they don't exist)
load_season_day = load_season_day[~load_season_day['Trading_Period'].isin(['TP49', 'TP50'])]

national_load = load_season_day.copy() #Making a copy so can find the average load per season/day for all of NZ
load_curve_plots = load_season_day.copy()
group_cols = ['Island', 'Season', 'Day_Type']

# Get top 2 Value rows per group
# Rank values within each group (1 = highest)
load_season_day['rank'] = load_season_day.groupby(group_cols)['Value'].rank(method='first', ascending=False)

# Filter top 2 ranked rows per group
Peak = load_season_day[load_season_day['rank'] <= 2].drop(columns='rank').reset_index(drop=True)
#peaks in csv
Peak.to_csv(f"{Timeslice_output_location}/peakperiods.csv", index = False)

national_load = national_load.groupby(['Season', 'Day_Type', 'Trading_Period'])['Value'].mean().reset_index()

nat_group_cols = ['Season', 'Day_Type']
national_load['rank'] = national_load.groupby(nat_group_cols)['Value'].rank(method='first', ascending=False)

# Filter top 2 ranked rows per group
National_Peak = national_load[national_load['rank'] <= 2].drop(columns='rank').reset_index(drop=True)

National_Peak.to_csv(f"{Timeslice_output_location}/national_peakperiods.csv", index = False)
#endregion

#region PLOTS
#not necessary for the actual code but does show the trends 
# #making some plots
# load_curve_plots['slot'] = load_curve_plots['Trading_Period'].str.extract(r'(\d+)$').astype(int)

# # Create integer-keyed map: 1–48 → half-hour times
# half_hour_map = {
#     i: f"{(i - 1) // 2:02}:{'00' if i % 2 == 1 else '30'}"
#     for i in range(1, 49)
# }

# load_curve_plots['Time'] = load_curve_plots['slot'].map(half_hour_map)
# #Gonna try to plot all of the categories on top of each other
# load_curve_plots = load_curve_plots.sort_values(by = 'slot')
# load_curve_plots['Group'] = load_curve_plots[['Island', 'Season', 'Day_Type']].agg('-'.join, axis = 1)

# plt.figure()
# for label, group in load_curve_plots.groupby('Group'):
#     plt.plot(group['Time'], group['Value'], label=label)

# plt.legend()
# plt.xlabel('Time')
# plt.ylabel('Value')
# plt.title('Plot of all of the average load curves')
# plt.show()

# #plotting just NI winter weekday
# NI_load_curve_plots = load_curve_plots[(load_curve_plots["Island"] == 'NI') & (load_curve_plots['Day_Type'] == 'WD') & (load_curve_plots['Season'] == 'Winter')]
# NI_load_curve_plots.plot(x= 'Time', y = 'Value')
# plt.show()

#endregion