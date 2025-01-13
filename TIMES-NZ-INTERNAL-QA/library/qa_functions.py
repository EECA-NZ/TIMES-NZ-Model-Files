
"""
These functions perform structural and minus tests on the selected scenarios 
They will import some retrieval functions (and qa_runs have been defined in config)

Note that get_data_structure, remove_time_periods, and minus_test_structure are not currently called
May or may not use these as we build up the tests
"""


import pandas as pd
from config import qa_runs
from qa_data_retrieval import get_veda_data, get_veda_data_no_concordance, add_concordance_to_vd




def get_data_structure(attribute):
    # the point of this is to return the dataframe with no numbers in it so we can test structure changes     
    df = get_veda_data_no_concordance(attribute)
    # remove PV and ensure grain holds 
    current_count = len(df)    
    df_no_pv = df.drop("PV", axis = 1).drop_duplicates()
    new_count = len(df_no_pv) 
    if current_count != new_count:
        print(f"Error: '{attribute}' data has {current_count} rows")
        print(f"However, it has {new_count} rows after removing PV and collapsing")
        print(f"Mismatched counts imply rows are not uniquely defined in Veda output!! Help!!")

    return df_no_pv

def remove_time_periods(df):

    periods_to_remove = ["Period", "TimeSlice", "Vintage"]
    for period in periods_to_remove:
        df = df.drop(period, axis = 1).drop_duplicates()

    return df

def minus_test_structure(attribute, run_a, run_b, max_rows = 100): 

    df = get_data_structure(attribute) 
    # drop times to remove noise 
    df = remove_time_periods(df) 

    # get separate tables     
    df_a = df[df["Scenario"] == run_a].drop("Scenario", axis = 1)
    df_b = df[df["Scenario"] == run_b].drop("Scenario", axis = 1)  

    # minus 
    a_minus_b = (    
        df_a
        .merge(df_b, how='left', indicator=True)
        .query('_merge == "left_only"')
        .drop('_merge', axis=1)
        )
    
    # assess result 
    if len(a_minus_b) > 0: 
       print(f"The following structures are defined in '{run_a}' but not '{run_b}'")
       a_minus_b = add_concordance_to_vd(a_minus_b)
       pd.set_option('display.max_rows', max_rows)
       return a_minus_b
    else: 
        print(f"All CAP, ATT, and PROC combinations in '{run_b}' are also found in '{run_a}'")    

 
def get_minus_test_df(df_a, df_b):

    a_minus_b = (    
        df_a
        .merge(df_b, how='left', indicator=True)
        .query('_merge == "left_only"')
        .drop('_merge', axis=1)
        )
    return(a_minus_b)

def check_minus_test(df, run_a, run_b, variable):    
    
    df_a = df[df["Scenario"] == run_a].drop("Scenario", axis = 1)
    df_b = df[df["Scenario"] == run_b].drop("Scenario", axis = 1)

    a_minus_b = get_minus_test_df(df_a,df_b)

    output_string = ""

    if len(a_minus_b) == 0:
        output_string += f"All instances of '{variable}' in '{run_a}' are also in '{run_b}'\n"

    else: 
        failed_categories = a_minus_b[variable]      

        output_string = (f"The following instances of '{variable}' in '{run_a}' are not in `{run_b}`:\n")
        for category in failed_categories:
            output_string += f" - {category}\n"


    return output_string

        
            
        

def check_category_mismatch(attribute, variable, run_a, run_b):    

    # output_string = f"{attribute}: checking {variable} matches\n"
    output_string = ""
    # get the atty data 
    df = get_veda_data_no_concordance(attribute)
    # identify unique values of variable
    df = df[[variable, "Scenario"]].drop_duplicates()

    output_string += f"{check_minus_test(df, run_a, run_b, variable)}\n{check_minus_test(df, run_b, run_a, variable)}\n"
    


    return output_string


    
    

    
def check_all_category_mismatches(run_a, run_b):

    attributes_to_check = ["VAR_FIn", "VAR_FOut", "VAR_CAP"]
    variables_to_check = ["Process", "Commodity"]

    output_string = ""


    for attribute in attributes_to_check:
        for variable in variables_to_check:
            output_string += check_category_mismatch(attribute, variable, run_a, run_b)

    
    return output_string

    


def get_delta_data(attribute, runs = qa_runs):
    """
    METHOD


    We want to test any data changes given the grain of attribute, process, commodity, period, and region.
    Put another way, we want to hold those things constant between tables (so trim both to match) and then assess which ones have had values change

    We will assess only if numbers change within these grains 
    We won't capture if numbers changed because the structures of these changed (eg a process was renamed),
    because that testing is done elsewhere.

    This means the aggregated output of these might be the same at a Period level!
    However we will capture if eg; some demand has shifted in its timeslice.
    It is better to assess that here, rather than chalking it up to a category change in our category change testing.
    Timeslice or vintage changes can be a bit overwhelming/noisy

    """   

    # Setup 

    run_a = runs[0]
    run_b = runs[1]

    constant_variables = ["Attribute", "Commodity", "Process", "Period", "Region"]

    # get data 
    df = get_veda_data(attribute)

    # get all unique combinations for each scenario
    # first, aggregate the main table by the constant variables and scenario 
    agg_table = (df
                 .groupby(constant_variables + ["Scenario"])
                 .sum("PV").reset_index()
    )

    # pivot to make comparisons between each scenario
    # retain all other variables in pivot
    index_cols = [col for col in agg_table.columns if col not in ["PV", "Scenario"]]
    # pivot
    delta_test = agg_table.pivot(    
        index = index_cols,
        columns = "Scenario",
        values = "PV"
    ).fillna(0).reset_index()

    # Create delta
    delta_test["Delta"] = delta_test[run_a] - delta_test[run_b]
    # tolerance within 0.1% change
    # i thought i would need to mess around with the way it handles 0s but it seems to work fine 
    delta_test["Delta_Proc"] = delta_test[run_b] / delta_test[run_a] - 1
    delta_test =  delta_test[(abs(delta_test["Delta_Proc"]) > 0.001 )] 


    # add concordance back. This is now a table where there has been some change between scenarios in the matching data 
    delta_test = add_concordance_to_vd(delta_test)

    changed_grain = delta_test.groupby(["Attribute", "Process", "Commodity"]).size().reset_index(name = "Count").drop("Count", axis = 1 )


    # Now, the data we want is just the full (original) dataset,
    # but filtered to where any combination of att/proc/comm has seen any change in any of our other variables
    # this merge inner joins on the att/proc/comm variables, so is intended only as a filter
    df = df.merge(changed_grain)

    # We replace all our string values with missing
    # This is only intended to capture basically all the missing concordance inputs,
    # just because the nans tend to break downstream functions
    # We explicitly exclude PV cos this is an object and would convert it to a string otherwise (bad)
    string_columns = df.select_dtypes(include=['object']).columns
    string_columns = [col for col in string_columns if col != 'PV']
    # Replace NaN with "Missing" in those columns    
    df[string_columns] = df[string_columns].fillna('Missing')

    return df
    