import tomli
import sys 
import os 
import pandas as pd 
import numpy as np
import logging

# set log level for message outputs 
logging.basicConfig(level=logging.INFO) # are we even using this? Because we probably should 

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, "../..", "library"))
from filepaths import PREP_LOCATION, DATA_INTERMEDIATE

from helpers import clear_output

from excel_writers import create_empty_workbook, dict_to_dataframe, strip_headers_from_tiny_df, write_data



metadata_location = f"{DATA_INTERMEDIATE}/stage_0_config/config_metadata.csv"

# GET THE METADATA 


metadata = pd.read_csv(metadata_location)


# wipe the output - we're going to fill it in! 

clear_output()

# note: later this will plug directly into the TIMES-NZ folder itself. So we would want to be pretty confident when doing that 
# for now we will paste into this output folder, and copy/paste as needed 



# print(metadata)


# ok so we should be able to use everything here. 
# First we get each unique combination of BookName and SheetName to run the entry book creation



# so i guess for each toml 

# are we saying each toml is its own book? that might be the structure we need to follow but we will see 

workbooks_to_make = metadata["WorkBookName"].unique()


# for each workbook we find in the metadata table: 
for workbook in workbooks_to_make: 

    # we find all the sheets 
    workbook_metadata = metadata[metadata["WorkBookName"] == workbook]
    worksheets = workbook_metadata["SheetName"].unique()

    # and feed the book name and the sheetname into the creation function to give us the templates we need 

    create_empty_workbook(workbook, worksheets)


    for worksheet in worksheets: 

        worksheet_metadata = workbook_metadata[workbook_metadata["SheetName"] == worksheet]

        startrow = 0

        # we'll convert each row to a tuple and process from there 
        for x in worksheet_metadata.itertuples():
            print(f"WorkBookName = {x.WorkBookName}, Location = {x.DataLocation}, Tag = {x.VedaTag}")

            data_location = x.DataLocation
            table_name = x.TableName
            tag_name = x.VedaTag
            uc_sets = x.UC_Sets




            # we will need to make a rule that each table name in a toml must be distinct, I think
            # not the tag name of course, but the user-specified table names. These are not used by Veda but are for preprocessing IDs 

            print(f"Data details: ")
            print(f"Data location: {data_location}")
            print(f"Table Name: {table_name}")
            print(f"Veda Taf: {tag_name}")
            print(f"UC Sets: {uc_sets}")


            if np.isnan(uc_sets):
                uc_sets = []

            

            # first, find the data 

            # we can also just load this once from the normalised toml file 

            # open the toml file             

            if data_location.endswith(".toml"): 
                # do toml things 
                # open the toml file (normalised and pull out the dict and make a dataframe
                toml_location = f"{DATA_INTERMEDIATE}/stage_0_config/{data_location}"
                with open(toml_location, 'rb') as f:
                    toml_data = tomli.load(f)
                df_dict = toml_data[table_name]["Data"]
                df = dict_to_dataframe(df_dict)                

            elif data_location.endswith(".csv"):
                # the csv versions could be in raw or intermediate, so we just start at the module root and work up 
                csv_location = f"{PREP_LOCATION}/{data_location}"
                 # think we have to ensure strings here but I am not 100% (maybe just on write???)
                 # to check the old methods just to make sure 
                df = pd.read_csv(csv_location, dtype = str)
            else: 
                logging.warning("I don't know how to interpret the data located at {data_location}")

            # do the tiny dfs - these are the only 2 I believe! 

            if (workbook == "SysSettings"                    
                    and table_name in ["StartYear", "ActivePDef"]):
                df = strip_headers_from_tiny_df(df)

            # we still need to set the row counts to make this work urgh 


            # write the table and iterate the start row 

            write_data(df,
                       book_name = workbook,
                       sheet_name = worksheet,
                       tag = tag_name, 
                       uc_set = uc_sets, 
                       startrow = startrow)
            

            df_row_count= len(df) + len(uc_sets)
            # add the dataframe rows to our start row index so we can keep going without overwriting
            # and additional rows for a healthy gap.            
            startrow += df_row_count + 3     
            

