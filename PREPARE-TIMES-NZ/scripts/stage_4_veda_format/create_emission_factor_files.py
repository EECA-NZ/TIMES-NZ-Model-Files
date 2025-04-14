"""
EECA's emission factors worksheet is already mostly compiled. We convert these into kt/PJ

"""
#######################################################################
#region LIBRARIES 
#######################################################################
import sys 
import os 
import polars as pl

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, "../..", "library"))
from filepaths import DATA_RAW, DATA_INTERMEDIATE
from helpers import select_and_rename

input_location = f"{DATA_RAW}/coded_assumptions/emission_factors"
stage_2_data_location = f"{DATA_INTERMEDIATE}/stage_2_baseyear"
output_location = f"{DATA_INTERMEDIATE}/stage_4_veda_format/emission_factors"
os.makedirs(output_location, exist_ok = True)


#endregion
#######################################################################
#region GET_DATA
#######################################################################

emission_factors_df = f"{input_location}/emission_factors.csv" 
emission_factors_df = pl.read_csv(emission_factors_df)

# calculate the kt/co2e for every fuel 
emission_factors_df = (
    emission_factors_df
    .with_columns((pl.col("EF kg CO2e/unit")/pl.col("CV MJ/Unit")).alias("kg/MJ"))
    .with_columns((pl.col("kg/MJ")*1e3).alias("kt CO2e/PJ"))
    )

# We also need the data from our full plant list 

plant_data = pl.read_csv(f"{stage_2_data_location}/base_year_electricity_supply.csv")
#endregion 

#######################################################################
#region ELECTRICITY_GENERATION
#######################################################################

# In future, once we have more emission factors in this script, we should maybe
# extract the full mapping to an external concordance file for raw input and greater visibility

elec_ef_mapping =  {
    "Coal - Sub-Bituminous" : "ELCCOA",
    "Natural Gas" : "ELCNGA",
    "Diesel" : "ELCOIL", # We call this oil but it's assumed all diesel (no fuel oil generation anymore)  (assumes 10ppt sulphur)
    "Biogas" : "ELCBIG",
    "Wood - Pellets" : "ELCWOD", # an argument for instead taking other wood types, or the mean of other wood types. They're all quite similar.
    }
# modify the table 
emission_factors_elc = (
    emission_factors_df
    # using the industrial EFs for electricity generation
    .filter(pl.col("Sector") == "Industrial")
    # taking the fuels specified in the mapping
    .filter(pl.col("Fuel").is_in(list(elec_ef_mapping.keys())))
    # and then renaming them based on the map 
    .with_columns(pl.col("Fuel").replace(elec_ef_mapping).alias("FuelCode"))  
    # add the TIMES CommName with a polars literal
    .with_columns(pl.lit("ELCCO2").alias("CommName"))  
    )

# select and rename 
emission_factors_elc_names = {
    "CommName" : "CommName",
    "FuelCode":"Fuel",     
    "kt CO2e/PJ" : "Value"
    }
emission_factors_elc = select_and_rename(emission_factors_elc,emission_factors_elc_names)

# pivot for TIMES format 
emission_factors_elc = (emission_factors_elc
                        .pivot(values = "Value",
                               index = "CommName", # the index is also our attribute name which Veda needs 
                               on = "Fuel"))

# save the file
emission_factors_elc.write_csv(f"{output_location}/emission_factors_elc_fuels.csv")


#endregion
########################################################################
#region GEOTHERMAL_EMISSION_FACTORS
#######################################################################

# Geothermal data from emission factors assumption file 
geothermal_df = (emission_factors_df.filter(pl.col("Fuel") == "Geothermal")                 )

# Extract median value for geothermal emissions factor as default value
default_geo_factor = (
    geothermal_df
    # Select median 
    .filter(pl.col("SectorDetail") == "Median")
    # extract the first value as a variable
    )["kt CO2e/PJ"].to_list()[0]

# select and rename the emission factors data so we can join it to our plant names 
geo_name_map = {
    "SectorDetail" : "CommName",
    "kt CO2e/PJ" : "Value",
    "SectorDetail" : "PlantName", # for joining the values to our main table 
}

geothermal_df = select_and_rename(geothermal_df, geo_name_map)

# Create the table from our main plant data and adding the above inputs. 
geo_plant_emission_factors = (
    # start with our list of geothermal plant names 
    plant_data 
    .filter(pl.col("FuelType") == "Geothermal")
    .select(["PlantName", "Process"])
    .unique()    
    .sort("PlantName") # Not necessary but makes me happy. 
    # These are our main plant names from the original genstack input at data_raw/coded_assumptions/electricity_generation/GenerationFleet.csv
    # They should match the appropriate plants in the raw emission factors assumption inputs. 
    .join(geothermal_df, on = "PlantName", how = "left")
    # If no factor is found, we use the default median factor
    .with_columns(pl.col("Value").fill_null(default_geo_factor))
    # Now we add the relevant variables for TIMES 
    # This sheet would need to be more complicated if we wanted different factors for different years. This is probably fine for now.
    .rename({"Process" : "TechName",
             "Value": "ENV_ACT~ELCCO2"})
    .select(["TechName","ENV_ACT~ELCCO2"])

)

# Save
geo_plant_emission_factors.write_csv(f"{output_location}/emission_factors_geo.csv")
