import tomli
import sys 
import os 
import pandas as pd 
import logging

# set log level for message outputs 
logging.basicConfig(level=logging.INFO) # are we even using this? Because we probably should 

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, "../..", "library"))
from filepaths import PREP_LOCATION, DATA_INTERMEDIATE

from helpers import clear_output

from excel_writers import create_empty_workbook, dict_to_dataframe



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

workbooks_to_make = metadata["BookName"].unique()


# for each workbook we find in the metadata table: 
for workbook in workbooks_to_make: 

    # we find all the sheets 
    workbook_metadata = metadata[metadata["BookName"] == workbook]
    worksheets = workbook_metadata["SheetName"].unique()

    # and feed the book name and the sheetname into the creation function to give us the templates we need 

    create_empty_workbook(workbook, worksheets)


    for worksheet in worksheets: 

        worksheet_metadata = workbook_metadata[workbook_metadata["SheetName"] == worksheet]

        # we'll convert each row to a tuple and process from there 
        for x in worksheet_metadata.itertuples():
            print(f"BookName = {x.BookName}, Location = {x.DataLocation}, Tag = {x.VedaTag}")

            data_location = x.DataLocation
            table_name = x.TableName

            # we will need to make a rule that each table name in a toml must be distinct, I think
            # not the tag name of course, but the user-specified table names. These are not used by Veda but are for preprocessing IDs 

            print(f"Data can be found at {data_location}, and the table name is {table_name}")

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




            
    
            





        # now we're

        # now we go through each sheet and write everything from the metadata to the sheet 

        # the way we're going to do this is to treat every row in metadata as a new tag to write 
        # there can be double ups or all sorts - we're keeping some flexibility there 
        # if someone adds a new entry in a toml, it makes a new tag, no drama no ifs no buts


        # but we will work in aggregate groups of workbook/sheet     
        # because we need to just hit each sheet once then go down and add each tag 


        # so the structure goes like: for every combination of workbook/worksheet

        # we go through every row in the metadata and: 
            # a) find the df location (toml/csv)
                # - either read the toml and make the dict a df
                # - or read the csv 
            # b) add the tiny df logic to the two annoying tables 
            # c) read the tags and uc_sets if necessary 
            # d) write the table with the tags and iterate downwards 

            # I think this is actually pretty easy huh 






    

    

