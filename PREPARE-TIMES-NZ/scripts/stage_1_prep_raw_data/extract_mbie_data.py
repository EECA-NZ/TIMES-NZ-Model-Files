# Here we find the mbie excel files and create data_intermediate/stage_1_external_data/mbie/*
# this will include any edgs assumptions we want to use and any official figures we want 
# We also do some tidying/standardising here


# Potential to-do: something from the oil/gas forecasts, maybe balance tables, primary production, that sort of thing. 

# LIBRARIES -------------------------------------------------------------------------

import sys 
import os 
import pandas as pd 

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, "../..", "library"))
from filepaths import DATA_RAW, DATA_INTERMEDIATE

# FILEPATHS -------------------------------------------------------------------------
input_location = f"{DATA_RAW}/external_data/mbie"
output_location = f"{DATA_INTERMEDIATE}/stage_1_external_data/mbie"
os.makedirs(output_location, exist_ok = True)


#############################################################################
#region EDGS
#############################################################################

def get_edgs_assumptions(SheetName):
    edgs_location = f"{input_location}/electricity-demand-generation-scenarios-2024-assumptions.xlsx"
    df = pd.read_excel(edgs_location, sheet_name=SheetName)
    return df 
# save
get_edgs_assumptions("Generation Stack").to_csv(f"{output_location}/gen_stack.csv", index=False)
#endregion

#############################################################################
#region ELE GENERATION
#############################################################################

def get_mbie_electricity(SheetName, rowstart,rowend, category_name, unit, variable_name):
    ele_location = f"{input_location}/electricity.xlsx"
    df = pd.read_excel(ele_location, sheet_name = SheetName, skiprows = 8)
    # each range must come with the years, which are now the column names
    # we then just supply the row range for whichever specific table we want.     
    df = df.iloc[rowstart:rowend]
    # remove this unneccessary column
    df = df.drop("Annual % change", axis = 1)
    # relabel the category year 
    df = df.rename(columns={'Calendar year': category_name})
    # remove the footnote numbers from the categories
    df[category_name] = df[category_name].str.replace(r'\d+$', '', regex=True)
    # self-documenting table variables
    df["Unit"] = unit
    df["Variable"] = variable_name
    # pivot 
    df = pd.melt(df, 
             id_vars = ["Fuel", "Unit", "Variable"],
             var_name = "Year",
             value_name = "Value"
             )
    df = df.rename(columns = {"Fuel":"FuelType"})
    return df 

# Generation (PJ/GWh - sticking with GWh for now but everything in TIMES will be PJ)
df = get_mbie_electricity("2 - Annual GWh", 
                          2,12, # row start/end
                          category_name = "Fuel",
                          unit = "GWh",
                          variable_name = "Annual net electricity generation")
df.to_csv(f"{output_location}/mbie_ele_generation_gwh.csv", index=False)


df = get_mbie_electricity("4 - Annual PJ", 
                          2,12, # row start/end
                          category_name = "Fuel",
                          unit = "PJ",
                          variable_name = "Annual net electricity generation")
# save
df.to_csv(f"{output_location}/mbie_ele_generation_pj.csv", index=False)

#endregion

#############################################################################
#region ELE ONLY
#############################################################################
ele_only_gen = pd.read_excel(
    f"{DATA_RAW}/external_data/mbie/electricity.xlsx",
    sheet_name = "6 - Fuel type (GWh)",
    usecols = "B:K", skiprows = 5, nrows = 51)


# ensure year label correct 
ele_only_gen = ele_only_gen.rename(columns = {"Unnamed: 1":  "Year"})
# remove junk rows 
ele_only_gen = ele_only_gen[~ele_only_gen["Year"].isna()]
# remove provisional label
ele_only_gen = ele_only_gen.drop(["Unnamed: 2"], axis = 1)

# tidy column names 
ele_only_gen = ele_only_gen.rename(
    columns = {"Oil1": "Oil",
               "Geo- thermal": "Geothermal"}
    )
# sensible shape 
ele_only_gen = ele_only_gen.melt(
    id_vars = "Year",
    var_name = "Fuel",
    value_name = "Value"
    )
# label 
ele_only_gen["Unit"] = "GWh"
ele_only_gen["Variable"] = "Electricity generation (no cogen)"
ele_only_gen = ele_only_gen.rename(columns = {"Fuel":"FuelType"})
# years as integers 
ele_only_gen["Year"] = ele_only_gen["Year"].astype(int)


# save
ele_only_gen.to_csv(f"{output_location}/mbie_ele_only_generation.csv", index=False)
#endregion

#############################################################################
#region ELE CAPACITY
#############################################################################


official_capacity = pd.read_excel(
    f"{DATA_RAW}/external_data/mbie/electricity.xlsx",
    sheet_name = "7 - Plant type (MW)",
    usecols = "B:P", skiprows = 5, nrows = 50)


# clean up 

# ensure year label correct 
official_capacity = official_capacity.rename(columns = {"Unnamed: 1":  "Year"})
# remove junk rows 
official_capacity = official_capacity[~official_capacity["Year"].isna()]

# remove junk columns (subtotals, totals)
official_capacity = official_capacity.drop(["Sub-total", "Sub-total.1", "Unnamed: 15"], axis = 1)

# sensible categories

official_capacity = official_capacity.rename(
    columns = {"Gas3": "Gas Cogen",
               "Other4": "Other Cogen",
               "Other Thermal2": "Other electricity generation"}
    )

# sensible shape 


official_capacity = official_capacity.melt(
    id_vars = "Year",
    var_name = "Technology",
    value_name = "Value"

)

# missing means 0 in this case 
official_capacity["Value"] = official_capacity["Value"].fillna(0)
# label 
official_capacity["Unit"] = "MW"
official_capacity["Variable"] = "Electricity generation capacity at end year"
# years as integers 
official_capacity["Year"] = official_capacity["Year"].astype(int)
# save 
official_capacity.to_csv(f"{output_location}/mbie_generation_capacity.csv", index=False)


#endregion






















