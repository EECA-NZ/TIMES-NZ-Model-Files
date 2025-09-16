"""
This module contains the functions required to read and parse our toml user configs

THe most important (and mildly complex) feature is the "normalize_toml_data" function,

which effectively defines and sets default rules for how tomls work to create
Veda workbooks.



"""

import copy
import os
import tomllib

from prepare_times_nz.utilities.logger_setup import logger


# this function is too complex and should be refactored
# pylint: disable = too-many-branches
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

    # create a copy to work with
    normalized_data = copy.deepcopy(toml_data)

    # get the bookname here
    book_name = normalized_data["WorkBookName"]

    # reserved_keys are all the values with explicit meanings for each item
    # Note that any other keys will be assumed to be data
    # and inserted into the Veda file accordingly
    reserved_keys = [
        "WorkBookName",
        "SheetName",
        "TagName",
        "DataLocation",
        "Data",
        "UCSets",
        "Description",
    ]

    for table_name, table_content in normalized_data.items():

        # Assess how to adjust each item, if necessary

        # Ignore the bookname parameter - our items inherit this
        if table_name == "WorkBookName":
            continue

        # If tagname is not specified, use the table name
        if "TagName" not in table_content:
            table_content["TagName"] = table_name

        # inherit the workbook name (but otherwise keep specific workbooks if needed)
        if "WorkBookName" not in table_content:
            table_content["WorkBookName"] = book_name

        # IF sheetname is not specified, inherit the book name
        if "SheetName" not in table_content:
            table_content["SheetName"] = book_name

        # Blank entries for uc_sets.
        if "UCSets" not in table_content:
            table_content["UCSets"] = ""

        # Blank entries for Description
        if "Description" not in table_content:
            table_content["Description"] = ""
            logger.warning("{%s} has no Description - please fix", table_name)

        # Data processing
        # We process specific data if it is captured in this table_name

        # Skip if not a dictionary (table)
        if not isinstance(table_content, dict):
            continue
        # IF table_name contains a data_location, then the data is just that location
        # so this is already done and we skip
        if "DataLocation" in table_content:
            continue

        # If "Data" has been specified clearly in the content, we just keep it as is
        if "Data" in table_content:
            continue

        # If there were no references to data tables or locations,
        # We assume the data is in the toml and just take all the non-key variables
        # and convert these to the data
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
        table_content["Data"] = data_subtable

    return normalized_data


def parse_toml_file(file_path):
    """
    Parse a TOML file and normalize its structure

    Args:
        file_path (str or Path): Path to the TOML file

    Returns:
        dict: Normalized TOML data
    """

    with open(file_path, "rb") as f:
        toml_data = tomllib.load(f)

    return normalize_toml_data(toml_data)


def get_toml_files(folder_path):
    """Returns a list of all .toml files in the specified folder."""
    if not os.path.isdir(folder_path):
        print(f"Error: The folder '{folder_path}' does not exist.")
        return []

    return [f for f in os.listdir(folder_path) if f.endswith(".toml")]
