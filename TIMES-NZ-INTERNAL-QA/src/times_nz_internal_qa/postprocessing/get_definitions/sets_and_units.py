"""
This script is designed to extract code definitions
    from PREPARE-TIMES-NZ

It assumes that that module has been run locally and
    data_intermediate populated

It then does the following:

a) Identifies every generated FI_Process table
    and allocates process groups and units to each process
b) The process groups are then handled separately:
    - DMD (Demand Devices) are formatted as per the EEUD.


"""

import tomllib

import pandas as pd
from times_nz_internal_qa.utilities.filepaths import (
    COMMODITY_CONCORDANCES,
    PREP_LOCATION,
    PREP_STAGE_0,
    PROCESS_CONCORDANCES,
)


def get_addresses_from_metadata(tag_type):
    """Extracts all datalocations and tablenames
      from config for a given tag type
    Only really useful for FI_Process or FI_Commodity types
    Returns as dict"""
    df = pd.read_csv(PREP_STAGE_0 / "config_metadata.csv")
    df = df[df["VedaTag"] == tag_type]
    # warn if some data was in the config
    df = df[["TableName", "DataLocation"]].drop_duplicates()
    return df.set_index(df.columns[0])[df.columns[1]].to_dict()


def convert_toml_data_to_df(data):
    """
    converts the input dict to a df, and expands inherited items
    Slightly convoluted just to do all the inheritances for different length lists
    This is because our potential toml inputs are very flexible.
    """
    lens = [len(v) if isinstance(v, list) else 1 for v in data.values()]
    n = max(lens)

    norm = {}
    for k, v in data.items():
        if isinstance(v, list):
            if len(v) == 1:
                norm[k] = v * n
            elif len(v) == n:
                norm[k] = v
            else:
                raise ValueError(f"{k} length {len(v)} != {n}")
        else:

            norm[k] = [v] * n

    return pd.DataFrame(norm)


def convert_table_columns_to_lower(df):
    """
    Convert all DataFrame column names to lowercase.
    """
    df.columns = [c.lower() for c in df.columns]
    return df


def get_all_process_tables():
    """
    Reads all process tables from metadata
    returns a dataframe of key declaration variables
    """

    address_dictionary = get_addresses_from_metadata("~FI_Process")

    process_dfs = []

    for table_name, address in address_dictionary.items():
        # standard read of csv inputs
        if ".csv" in address:
            # load process table
            df = pd.read_csv(PREP_LOCATION / address)
            # ensure everything inherited
            df = df.ffill()
            df = convert_table_columns_to_lower(df)
            process_dfs.append(df)
        elif ".toml" in address:
            # otherwise, read from toml (note diff location)
            toml_location = PREP_STAGE_0 / address
            with open(toml_location, "rb") as f:
                data = tomllib.load(f)
            # extract
            data = data[table_name]["Data"]
            # convert
            df = convert_toml_data_to_df(data)
            df = convert_table_columns_to_lower(df)
            # append to list
            process_dfs.append(df)

    # combine all and select only important values
    process_data = pd.concat(process_dfs, ignore_index=True)
    process_data = process_data[["techname", "sets", "tact", "tcap"]].drop_duplicates()

    return process_data


def get_all_commodity_tables():
    """
    Read all commodity tables from metadata
    returns a dataframe of key declaration variables
    """
    address_dictionary = get_addresses_from_metadata("~FI_Comm")

    commodity_dfs = []

    for table_name, address in address_dictionary.items():
        # standard read of csv inputs
        if ".csv" in address:
            # load process table
            df = pd.read_csv(PREP_LOCATION / address)
            # ensure everything inherited
            df = df.ffill()
            # standard cases
            df = convert_table_columns_to_lower(df)
            # join
            commodity_dfs.append(df)

        elif ".toml" in address:
            # otherwise, read from toml (note diff location)
            toml_location = PREP_STAGE_0 / address
            with open(toml_location, "rb") as f:
                data = tomllib.load(f)
            # extract
            data = data[table_name]["Data"]
            # convert
            df = convert_toml_data_to_df(data)
            df = convert_table_columns_to_lower(df)
            # append to list
            commodity_dfs.append(df)

    # combine all and select only important values
    commodity_data = pd.concat(commodity_dfs, ignore_index=True)
    commodity_data = commodity_data[["commname", "csets", "unit"]].drop_duplicates()

    return commodity_data


def save_unit_set_definitions():
    """
    A wrapper for identifying all sets and units
    for commodities and processes from the prep data
    Then saving these in this module
    """
    commodity_sets_and_units = get_all_commodity_tables()
    process_sets_and_units = get_all_process_tables()
    process_sets_and_units.to_csv(
        PROCESS_CONCORDANCES / "process_sets_and_units.csv", index=False
    )
    commodity_sets_and_units.to_csv(
        COMMODITY_CONCORDANCES / "commodity_sets_and_units.csv", index=False
    )


def main():
    """entrypoint"""
    save_unit_set_definitions()


if __name__ == "__main__":
    main()
