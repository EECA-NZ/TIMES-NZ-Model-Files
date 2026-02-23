"""
This script currently contains miscellaneous functions

THese may need to be organised more clearly within the program, as there
is not a clear conceptual throughline.

It currently includes:

Directory manipulation functions:
    - clear_data_intermediate()
    - clear_output()

Data testing functions:
    - check_table_grain()

Data manipulation functions:
    - select_and_rename()

These should potentially be moved into their own specific scripts,
OR this might make more sense if we can move more functions to shared
scripts with clearer conceptual throughlines. TBD.

"""

import os
import shutil

from prepare_times_nz.utilities.filepaths import DATA_INTERMEDIATE, OUTPUT_LOCATION
from prepare_times_nz.utilities.logger_setup import logger


def clear_data_intermediate():
    """
    DELETES the folder defined as DATA_INTERMEDIATE
    """
    # Delete folder
    if os.path.exists(DATA_INTERMEDIATE):
        logger.debug("DATA_INTERMEDIATE = {%s}", DATA_INTERMEDIATE)
        shutil.rmtree(DATA_INTERMEDIATE)
    # and make fresh
    os.makedirs(DATA_INTERMEDIATE)


def clear_output():
    """
    DELETES the folder defined as OUTPUT_LOCATION
    """
    # Delete folder
    if os.path.exists(OUTPUT_LOCATION):
        logger.debug("OUTPUT_LOCATION = {%s}", OUTPUT_LOCATION)
        shutil.rmtree(OUTPUT_LOCATION)
    # and make fresh
    os.makedirs(OUTPUT_LOCATION)


# Some data manipulation functions


def select_and_rename(df, name_map):
    """
    Selects and renames columns in a DataFrame based on a provided mapping.

    Parameters:
    - df: The input DataFrame.
    - name_map: A dictionary:
        keys are the original column names and values are the new column names.

    Returns:
    - A DataFrame with selected and renamed columns.
    """
    # Select columns based on the mapping
    selected_df = df[list(name_map.keys())].copy()

    # Rename columns
    selected_df.rename(columns=name_map, inplace=True)

    return selected_df


# Some tests


def check_table_grain(df, grain_list):
    """
    Check the grain of a DataFrame against a list of expected grains.

    Parameters:
    - df: The input DataFrame.
    - grain_list: A list of column names
        These should uniquely identify the rows in the Dataframe.

    Returns:
    - A boolean indicating whether rows are uniquely idenfied by the grain_list
    """
    return df.duplicated(subset=grain_list).sum() == 0


def test_table_grain(df, grain_list):
    """
    A wrapper and logging output for check_table_grain

    Parameters:
    - df: The input DataFrame.
    - grain_list: A list of column names that should uniquely identify the rows in df.

    Outputs: logging information regarding the results of the test.

    """

    if check_table_grain(df, grain_list):
        logger.info(
            "Success: rows are uniquely identified using the following variables:"
        )
        for var in grain_list:
            logger.info(" - {%s}", var)

    else:
        logger.warning(
            "Please review! Rows are NOT uniquely identified using these variables:"
        )
        for var in grain_list:
            logger.info(" - {%s}", var)
