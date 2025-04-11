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
from filepaths import DATA_RAW, DATA_INTERMEDIATE
from dataprep import *
#endregion

#region FILEPATHS
input_location = f"{DATA_INTERMEDIATE}/stage_1_external_data/electricity_authority"
timeslice_output_location = f"{DATA_INTERMEDIATE}/stage_1_external_data/TimeSlices"
time_configs = f"{DATA_RAW}/user_config"
os.makedirs(timeslice_output_location, exist_ok = True)

peak_periods = pd.read_csv(f"{time_configs}/peak_periods.csv")
yrfr = pd.read_csv(f"{time_configs}/year_fractions.csv")
timeslices = pd.read_csv(f"{time_configs}/TimeSlice_map.csv")
input_gxp_data = pd.read_parquet(f"{input_location}/emi_grid_export.parquet")
concordances = pd.read_csv(f"{input_location}/emi_nsp_concordances.csv")
res_baseline_data = pd.read_csv(f"{DATA_INTERMEDIATE}/stage_1_external_data/res_baseline/res_baseline_data.csv")
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

load_data_per_island.to_csv(f"{timeslice_output_location}/load_data.csv", index = False)

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
Peak = load_season_day[load_season_day['rank'] <= 3].drop(columns='rank').reset_index(drop=True)
#peaks in csv
Peak.to_csv(f"{timeslice_output_location}/peakperiods.csv", index = False)

national_load = national_load.groupby(['Season', 'Day_Type', 'Trading_Period'])['Value'].mean().reset_index()

nat_group_cols = ['Season', 'Day_Type']
national_load['rank'] = national_load.groupby(nat_group_cols)['Value'].rank(method='first', ascending=False)

# Filter top 2 ranked rows per group
National_Peak = national_load[national_load['rank'] <= 6].drop(columns='rank').reset_index(drop=True)

National_Peak.to_csv(f"{timeslice_output_location}/national_peakperiods.csv", index = False)
#endregion

#region PLOTS
# #not necessary for the actual code but does show the trends 
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

#region RESIDENTIAL DEMAND
# Want to work out COM_FR demand shares for the residential sector using the res baseline study
#extract NZ data
res_baseline_data = res_baseline_data[res_baseline_data['Region'] == 'NZ']

#merging any data that is duplicate entries
res_baseline_data = res_baseline_data.groupby(['Season', 'DayType', 'End Use Category', 'Year', 'Hour'])['Power'].sum().reset_index()

#Mapping for peak, day and night (this could be adjusted using the peaks we found from the EA load curve data if wanted)
peak_map = peak_periods.set_index('Time')['Time_Type'] 
res_baseline_data.insert(loc = 3, column = 'TimeType', value = res_baseline_data['Hour'].map(peak_map))

res_baseline_data = res_baseline_data.merge(timeslices, on=['Season', 'DayType', 'TimeType'], how='left')

#choosing year NOTE this will probably be changed later to include all years from 2023-40 but for now just 2023
# res_baseline_2023 = res_baseline_data[res_baseline_data['Year'] == 2023]

# res_baseline_2023 = res_baseline_2023.groupby(['TimeSlice','End Use Category', 'Year'])['Power'].sum().reset_index()

# #dividing by YRFR

# res_baseline_2023 = res_baseline_2023.merge(yrfr[['TimeSlice', 'AllRegions']], on = 'TimeSlice', how = 'left')

# res_baseline_2023['AdjustedPower'] = res_baseline_2023['Power']/ res_baseline_2023['AllRegions']

# #creating a copy so that we can find the total power use for each commodity for 2023
# total_com_use = res_baseline_2023.copy()
# total_com_use = total_com_use.groupby(['End Use Category', 'Year'])['AdjustedPower'].sum().reset_index()
# total_com_use = total_com_use.rename(columns = {'AdjustedPower': 'TotalPower'})

# #Merging so that we can find COM_FRs

# COM_FR_2023 = res_baseline_2023.merge(total_com_use[['End Use Category', 'TotalPower']], on = 'End Use Category', how = 'left')

# COM_FR_2023['COM_FR'] = COM_FR_2023['AdjustedPower'] / COM_FR_2023['TotalPower']
# COM_FR_2023 = COM_FR_2023[['TimeSlice', 'End Use Category', 'Year', 'COM_FR']].sort_values(by = ['End Use Category', 'TimeSlice'])


# COM_FR_2023.to_csv(f'{timeslice_output_location}/COM_FR.csv', index=False)

# Same thing but all the COM_FRs from 2023 to 2040
res_baseline = res_baseline_data[res_baseline_data['Year'] >= 2023]

res_baseline = res_baseline.groupby(['TimeSlice','End Use Category', 'Year'])['Power'].sum().reset_index()

#dividing by YRFR

res_baseline= res_baseline.merge(yrfr[['TimeSlice', 'AllRegions']], on = 'TimeSlice', how = 'left')
hours_per_year = 8760
res_baseline['AdjustedPower'] = res_baseline['Power'] * res_baseline['AllRegions'] * hours_per_year

#creating a copy so that we can find the total power use for each commodity for 2023
total_com_use = res_baseline.copy()
total_com_use = total_com_use.groupby(['End Use Category', 'Year'])['AdjustedPower'].sum().reset_index()
total_com_use = total_com_use.rename(columns = {'AdjustedPower': 'TotalPower'})

# Total_power = total_com_use.copy().groupby([''])
#Merging so that we can find COM_FRs

COM_FR = res_baseline.merge(total_com_use[['End Use Category', 'Year','TotalPower']], on = ['End Use Category', 'Year'], how = 'left')
COM_FR.to_csv(f'{timeslice_output_location}/COM_FR_ALL.csv', index=False)

COM_FR['COM_FR'] = COM_FR['AdjustedPower'] / COM_FR['TotalPower']
COM_FR = COM_FR[['TimeSlice', 'End Use Category', 'Year', 'COM_FR']].sort_values(by = ['End Use Category', 'Year','TimeSlice'])


COM_FR.to_csv(f'{timeslice_output_location}/COM_FR.csv', index=False)
#endregion

#region COM_FR vs YRFR
# want to compute COM_FR/YRFR and plot on a bar graph for each of the timeslices. can do for each commodity if needed

COM_FR_2023 = COM_FR[COM_FR['Year']==2023]

COM_FR_2023 = COM_FR_2023.merge(yrfr[['TimeSlice', 'AllRegions']], on = 'TimeSlice', how = 'left')

COM_FR_2023['COM_FRvsYRFR'] = COM_FR_2023['COM_FR'] / COM_FR_2023['AllRegions'] 

COM_FR_2023.to_csv(f'{timeslice_output_location}/COM_FRvsYRFR.csv', index=False)

#endregion