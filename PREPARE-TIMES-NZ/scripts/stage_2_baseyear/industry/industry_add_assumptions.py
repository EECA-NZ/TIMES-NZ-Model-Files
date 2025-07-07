"""

This script takes the TIMES sector industrial demand outputs and adds: 

AFA
Efficiency
Capital costs 
Lifetimes

Capacity estimates 

It's intended to run on the outputs of the regional disaggregation data, but could run on others

It then tidies the variables long ways after defining the topology, setting units etc.

This is the final output for the industrial sector base year, and includes all the categories etc (so we can make concordances out of this too)

"""
import sys 
import os 
import pandas as pd 
import numpy as np
import logging

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, "../../..", "library"))
from filepaths import STAGE_2_DATA, ASSUMPTIONS
from logger_setup import logger, h1, h2, blue_text
from deflator import deflate_data


# Constants -------

run_tests = False
CAP2ACT = 31.536
base_year = 2023
logger.warning("Alert! constants hardcoded in this script")

if run_tests:
    logger.info("Including test outputs")
else: 
    logger.info("Not running tests")

# Filepaths  --------------------

output_location = f"{STAGE_2_DATA}/industry/preprocessing"
os.makedirs(output_location, exist_ok = True)

checks_location = f"{STAGE_2_DATA}/industry/checks/3_parameter_assumptions"
os.makedirs(checks_location, exist_ok = True)

INDUSTRY_ASSUMPTIONS = f"{ASSUMPTIONS}/industry_demand"



# Get data -----------------------------------------------------

# need to input the regional shares data 
# think this would work with the original data too though
df = pd.read_csv(f"{output_location}/2_times_baseyear_regional_disaggregation.csv")

# get assumptions per tech
tech_lifetimes = pd.read_csv(f"{INDUSTRY_ASSUMPTIONS}/tech_lifetimes.csv")
tech_afa = pd.read_csv(f"{INDUSTRY_ASSUMPTIONS}/tech_afa.csv")

# per tech and fuel 
tech_fuel_efficiencies = pd.read_csv(f"{INDUSTRY_ASSUMPTIONS}/tech_fuel_efficiencies.csv")
tech_fuel_capex = pd.read_csv(f"{INDUSTRY_ASSUMPTIONS}/tech_fuel_capex.csv")




# Functions ----------------------------------------------------

def save_output(df, name):

    filename =f"{output_location}/{name}"
    logger.info(f"Saving output:\n{blue_text(filename)}")
    df.to_csv(filename, index = False)


def save_checks(df, name, label): 
    filename =f"{checks_location}/{name}"
    logger.info(f"Saving {label}:\n{blue_text(filename)}")
    df.to_csv(filename, index = False)



def check_missing_lifetimes(df):

    ### expecting the df to have a Life variable
    # will return all the technologies that don't have a life 
    # lol 

    df = df[df["Life"].isna()]
    missing_techs = df["Technology"].drop_duplicates() 
    missing_tech_count = len(missing_techs)


    if missing_tech_count > 0: 
        logger.warning(f"Warning: the following {missing_tech_count} technologies have no lifetimes")

        for tech in missing_techs:
            logger.warning(f"              {tech}")

        logger.warning(f"These will be given infinite lifetimes in the model and not retired!") 

    return df 

def add_lifetimes(df):

    df = pd.merge(df, tech_lifetimes, on = "Technology", how = "left")
    if run_tests:
        check_missing_lifetimes(df)

    df = df.drop("Note", axis = 1)
    
    return df 

def check_missing_efficiencies(df):

    missing_eff = df[df["Efficiency"].isna()]
    missing_eff = missing_eff[["Technology", "Fuel"]].drop_duplicates() 
    missing_eff_count = len(missing_eff)

    if missing_eff_count > 0: 
        logger.warning(f"Warning: the following {missing_eff_count} technologies have no efficiency listed")

        for index, row, in missing_eff.iterrows():
            logger.warning(f"        {row["Technology"]} - {row["Fuel"]}")        
        logger.warning(f"These will be given 100% efficiency in the model") 


    # also checking which ones we've explicitly set to 1 in the inputs just to make sure that makes sense 
    max_eff = df[df["Efficiency"] == 1 ]
    max_eff = max_eff[["Technology", "Fuel"]].drop_duplicates() 
    max_eff_count = len(max_eff)

    if max_eff_count > 0: 
        logger.warning(f"Warning: the following {missing_eff_count} technologies have had efficiency set to 100%:")

        for index, row, in max_eff.iterrows():
            logger.warning(f"        {row["Technology"]} - {row["Fuel"]}")        
        logger.warning(f"Maybe you intended this, but just worth reviewing") 


    return df 

def add_efficiencies(df, eff_data = tech_fuel_efficiencies):
    # remove notes and things     
    eff_data = eff_data[["Technology", "Fuel", "Efficiency"]]

    df = pd.merge(df, eff_data, on = ["Technology", "Fuel"] , how = "left")
    if run_tests:
         check_missing_efficiencies(df)    


    # set default as 1 explicitly (Veda will do this anyway but just makes it clearer)

    df["Efficiency"] = df["Efficiency"].fillna(1)

    return df 

def add_capex(df, capex_data = tech_fuel_capex):

    capex_data = capex_data[["Technology", "Fuel", "PriceBaseYear", "CAPEX"]].copy()

    # rebase 
    capex_data = deflate_data(capex_data, base_year = base_year, variables_to_deflate=["CAPEX"])
    df = pd.merge(df, capex_data, on = ["Technology", "Fuel"] , how = "left")

    if run_tests: 
        check_missing_capex(df)   

    return df 

def check_missing_capex(df):


    df = df[df["CAPEX"].isna()]

    missing_capex = df[["Technology", "Fuel"]].drop_duplicates() 
    missing_capex_count = len(missing_capex)


    if missing_capex_count > 0: 
        logger.warning(f"Warning: the following {missing_capex_count} processes have no capital cost listed")

        for index, row, in missing_capex.iterrows():
            logger.warning(f"        {row["Technology"]} - {row["Fuel"]}")

        logger.warning(f"These will require no capital investment in the model, so if more can be purchased they will be free") 

def add_afa(df, afa_data = tech_afa):

     afa_data = afa_data[["Technology", "AFA"]]
     df = pd.merge(df, afa_data, on = ["Technology"], how = "left")

     if run_tests:
         check_missing_afa(df)         

     return df 

def check_missing_afa(df):

    df = df[df["AFA"].isna()]

    missing_afa = df[["Technology", "Fuel"]].drop_duplicates() 
    missing_afa_count = len(missing_afa)


    if missing_afa_count > 0: 
        logger.warning(f"Warning: the following {missing_afa_count} processes have no availability factor listed")

        for index, row, in missing_afa.iterrows():
            logger.warning(f"        {row["Technology"]} - {row["Fuel"]}")

        logger.warning(f"This will lead to issues: please check the tech_afa.csv input file and ensure you have full tech coverage") 

def estimate_capacity(df): 

    """
    Capacity (as a function of output) is estimated according to the input fuel demand, the efficiency of the output, and the avaialability factor

    For example, if we have 3PJ going in with 80% efficiency and 50% AFA, then the output is 3PJ * 80% (2.4PJ) 
    the capacity required for 2.4PJ output is output/CAP2ACT, or output/31.536 (when output is PJ and capacity is GW)
    THen, because avaialbility is only 50%, we just divide by AFA (or doubling in this case)
    so the final equation for cap is 

    (inputPJ * efficiency)/(CAP2ACT*EFF)

    We keep the inputPJ*EFF in the data as "OutputEnergy" - this defines our activity bound later 

    """

    # output energy (relevant later, as this sets the base year activity bounds)
    df["InputEnergy"] = df["Value"]
    df["OutputEnergy"] = df["InputEnergy"] * df["Efficiency"]

    # Required capacity
    df["Capacity"] = df["OutputEnergy"] / CAP2ACT
    # Modify for availability
    df["Capacity"] = df["Capacity"] / df["AFA"]

    return df 
    
def tidy_data(df):

    """Here we just consistently set all our variables long with values and unit columns to make the thing self documenting"""

    df = df.drop(["Value", "Unit", "PriceBaseYear"], axis = 1)

    # we pivot the value columns. First define these with units. Everything else will stay in the data unpivoted    
    value_units = {
        "Life": "Years",
        "Efficiency": "%",        
        "CAPEX": f"{base_year} NZD/kW",
        "AFA": "%",
        "InputEnergy": "PJ",
        "OutputEnergy": "PJ",
        "Capacity": "GW"
        }   
    # extract variable names 
    value_cols = list(value_units.keys())    
    
    # id columns are everything else 
    id_cols = [col for col in df.columns if col not in value_cols]
    df = df.melt(id_vars = id_cols, value_vars = value_cols, var_name = "Variable", value_name = "Value")
    # add the units we designated 
    df["Unit"] = df["Variable"].map(value_units)

    return df 


# Execute


h2("Adding technology lifetimes")
df = add_lifetimes(df)

h2("Adding efficiency per fuel and technology")
df = add_efficiencies(df)

h2("Adding capital costs")
df = add_capex(df)

h2("Adding tech availabilities")
df = add_afa(df)

h2("Estimating capacity")
df = estimate_capacity(df)

h2("Cleaning up")
df = tidy_data(df)

# Save 
save_output(df, "3_times_baseyear_with_assumptions.csv")




 