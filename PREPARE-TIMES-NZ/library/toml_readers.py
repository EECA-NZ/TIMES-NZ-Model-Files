import tomli  # For Python < 3.11, use the tomli package for reading
import copy
import os 

import pandas as pd 
# from filepaths import DATA_RAW, DATA_INTERMEDIATE, OUTPUT_LOCATION

def normalize_toml_data(toml_data):
    """
    Normalize TOML data by:
    1. Moving all entries except 'tagname' to a 'Data' subtable if 'Data' doesn't exist
    2. Setting 'tagname' to the table name if it's not specified
    
    Args:
        toml_data (dict): The parsed TOML data
        toml_filepath: the location of the toml to read 
        tempted 
        
    Returns:
        dict: Normalized TOML data
    """   
    

    normalized_data = copy.deepcopy(toml_data)

    # get the bookname here 
    book_name = normalized_data["BookName"]
    
    for table_name, table_content in normalized_data.items():


        # these are all the values with explicit meanings for each item 
        reserved_keys = [
            "SheetName",
            "TagName",            
            "DataLocation",
            "Data",
            "UCSets",
            "Description",


        ]

        # Ignore the bookname parameter - our items inherit this 
        if(table_name == "BookName"):
            continue 


        # If tagname is not specified, use the table name
        if 'TagName' not in table_content:
            table_content['TagName'] = table_name

        # IF sheetname is not specified, inherit the book name
        if 'SheetName' not in table_content:
            table_content['SheetName'] = book_name

        # Blank entries for uc_sets? could put this somewhere else too if we wanted
        if 'UCSets' not in table_content:
            table_content['UCSets'] = ""

        # Blank entries for uc_sets? could put this somewhere else too if we wanted
        if 'Description' not in table_content:
            table_content['Description'] = ""


        # Data processing 


        # we skip if no dictionary exists i can't remeber why 
        # is this fully covered by skipping BookName?       


        
        # Skip if not a dictionary (table)
        if not isinstance(table_content, dict):
           continue

        if 'DataLocation' in table_content: 
            # we write the data as just the location of the table provided by DataLocation, so this is already done 
            continue            
        
        elif "Data" in table_content:
            # we just keep it
            continue 

        else:              
            # This means there were no references to data tables or locations, 
            # so we assume the data is in the toml and just take all the other variables and make them a dictionary         

            # Create a Data subtable
            data_subtable = {}           
            
            
            # Move all entries except reserved keys to 'Data'
            keys_to_remove = []
            for key, value in table_content.items():
                if key not in reserved_keys:
                    data_subtable[key] = value
                    keys_to_remove.append(key)
            
            # Remove the moved keys from the original table
            for key in keys_to_remove:
                del table_content[key]
            
            # Add the Data subtable
            table_content['Data'] = data_subtable


        



        

    
    return normalized_data


def parse_toml_file(file_path):

    """
    Parse a TOML file and normalize its structure
    
    Args:
        file_path (str or Path): Path to the TOML file
        
    Returns:
        dict: Normalized TOML data
    """
    
    
    with open(file_path, 'rb') as f:
        toml_data = tomli.load(f)
    
    return normalize_toml_data(toml_data)


# toml_test = parse_toml_file(syssettings_toml)


# we want to use this to write a workbook now . 





# def normalise_all_tomls(config_location): 

    # config_location should be data_raw/stage_0_config/*toml 





def get_toml_files(folder_path):
    """Returns a list of all .toml files in the specified folder."""
    if not os.path.isdir(folder_path):
        print(f"Error: The folder '{folder_path}' does not exist.")
        return []
    
    return [f for f in os.listdir(folder_path) if f.endswith('.toml')]

# print(toml_test)





# df = dict_to_dataframe(test_data["Data"])
# tag = test_data["TagName"]


# create_empty_workbook("SysSettings", ["SysSettings"])
 #write_data(df, "SysSettings_test_automate", "SysSettings", tag = tag, uc_set = [], startrow = 6)

# want to extract all the sheets in the toml 


# couple extra categories for the toml::::: 



# BookName should be removed from the list of key value pairs 
# SheetName can be included within any given tag
# UCSets can be included within any given tag 
# DataLocation can be used to specify a csv to read instead of containing data within the toml itself 
# Description can be be used to add a note to the table which will be read into the config table 

# From here, we should be able to read in every toml in our config folder (raw_data/stage_0_config/*.toml)
# normalise these, and create data_intermediate/stage_0_config/toml_configs 
# which is effectively just a table listing all the tags we'll create - it WON'T create data but it will make labels for either the data location 
# or a note if the data itself is in the toml (like startyear or whatever - we can probably make user constraints in tomls too or something )


# WE USE THE INTERMEDIATE TABLE TO CREATE THE WORKBOOKS so don't worry about these yet. 

# raw_data/stage_0_config/*.toml
# raw_data/stage_0_config/concordances?????????
# raw_data/stage_1_macro_drivers
# raw_data/stage_2_energy
