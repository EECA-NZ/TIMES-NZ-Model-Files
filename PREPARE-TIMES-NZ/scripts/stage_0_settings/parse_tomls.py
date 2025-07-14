# this script:
# 1) reads in all the config toml files,
# 2) normalises them (which makes the default settings explicit),
# 3) saves these,
# 4) and also writes a descriptive metadata file for them

# It writes everything into data_intermediate, which is designed to be wiped on runs and reruns and not tracked by git.


import logging
import os

import pandas as pd
import tomli_w

# set log level for message outputs
logging.basicConfig(level=logging.INFO)

from prepare_times_nz.filepaths import DATA_INTERMEDIATE, DATA_RAW
from prepare_times_nz.helpers import clear_data_intermediate
from prepare_times_nz.toml_readers import normalize_toml_data, parse_toml_file

# clear data_intermediate - this will need removing later because this toml parse method will probably come quite late? or maybe it's the first thing. Not sure
# Definitely don't want to delete all the processed data in any case.

clear_data_intermediate()


# Define locations for this file, and spin up the folder if needed
raw_data_location = f"{DATA_RAW}/user_config"
output_location = f"{DATA_INTERMEDIATE}/stage_0_config"
os.makedirs(f"{output_location}", exist_ok=True)


# STEP ONE: Get all the tomls

#


def list_toml_files(folder_path):
    """Returns a list of all .toml files in the specified folder."""
    if not os.path.isdir(folder_path):
        print(f"Error: The folder '{folder_path}' does not exist.")
        return []

    return [f for f in os.listdir(folder_path) if f.endswith(".toml")]


# Identify all the tomls we will be writing
toml_list = list_toml_files(raw_data_location)

# NOTE: we will later need to consider how we handle nested folders here, for subRES and Scenario files
# honestly we might even want to just allow much more flexibility - do a toml .glob to get everything, and then let the config files themselves
# specify how these should translate to excel versions

# and actually maybe add a little archive so we can swap different scenarios in and out as needed (and obviously not extract from this one )

# make an empty dataframe to start filling
metadata_df = pd.DataFrame()

for toml_name in toml_list:

    # first we normalise the data then write the file for later
    raw_toml_location = f"{raw_data_location}/{toml_name}"
    toml_normalised = parse_toml_file(raw_toml_location)

    # write the file out for later
    file_path = f"{output_location}/{toml_name}"
    with open(file_path, "wb") as f:
        tomli_w.dump(toml_normalised, f)

    # extract the book name to use through the rest of this approach
    book_name = toml_normalised["WorkBookName"]
    # don't need this anymore
    del toml_normalised["WorkBookName"]

    # Now we go through the dictionary for this toml file and write the key items to the metadata dataframe

    for name, item in toml_normalised.items():

        # We label the data's location as the original toml file if it was directly in the file
        # Otherwise keep the original location

        # Later we will extract dicts from the normalised toml file then convert these to dfs to insert into the excel files
        if "DataLocation" in item:
            data_location = item["DataLocation"]
        else:
            # otherwise we use the address of the toml file
            data_location = toml_name

        df = pd.DataFrame(
            {
                "WorkBookName": [book_name],
                "TableName": [name],
                "SheetName": [item["SheetName"]],
                "VedaTag": [f"~{item['TagName']}"],
                "UC_Sets": [item["UCSets"]],
                "DataLocation": [data_location],
                "Description": [item["Description"]],
            }
        )
        # df = pd.DataFrame({"something_is here": [toml_normalised[x]]})
        metadata_df = pd.concat([metadata_df, df], ignore_index=True)

        # we write this out so that everyone can use it


# Finally, save the metadata

metadata_df.to_csv(f"{output_location}/config_metadata.csv", index=False)
