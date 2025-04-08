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

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, "../..", "library"))
from filepaths import DATA_INTERMEDIATE
#endregion

#region FILEPATHS
input_location = f"{DATA_INTERMEDIATE}/stage_1_external_data/electricity_authority"
output_location = f"{DATA_INTERMEDIATE}/stage_1_external_data/TimeSlices"

input_gxp_data = f"{input_location}/emi_md.parquet"
concordances = f"{input_location}/emi_nsp_concordances.csv"
#endregion

#region LOAD CURVES



#endregion
