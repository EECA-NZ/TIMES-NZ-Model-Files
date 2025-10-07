"""
Data loading and quality check functions
"""

# Libraries

import re

import pandas as pd
from times_nz_internal_qa.utilities.filepaths import (
    COMMODITY_CONCORDANCES,
    PROCESS_CONCORDANCES,
    SCENARIO_FILES,
)

# Functions


def read_vd(filepath):
    """
    Reads a VD file, using column names extracted from the file's
    header with regex, skipping non-CSV formatted header lines.

    :param filepath: Path to the VD file.
    :param scen_label: Label for the 'scen' column for rows from this file.
    """
    dimensions_pattern = re.compile(r"\*\s*Dimensions-")

    # Determine the number of rows to skip and the column names
    with open(filepath, "r", encoding="utf-8") as file:
        columns = None
        skiprows = 0
        for line in file:
            if dimensions_pattern.search(line):
                columns_line = line.split("- ")[1].strip()
                columns = columns_line.split(";")
                continue
            if line.startswith('"'):
                break
            skiprows += 1

    # Read the CSV file with the determined column names and skiprows
    vd_df = pd.read_csv(
        filepath, skiprows=skiprows, names=columns, header=None, low_memory=False
    )
    return vd_df


def check_process_coverage(df):
    """
    Checks every process in model output results
    Ensures that they are identified in one of our process description files

    Simply prints results to console
    """

    # process codes

    demand_processes = pd.read_csv(PROCESS_CONCORDANCES / "demand.csv")
    elec_processes = pd.read_csv(PROCESS_CONCORDANCES / "elec_generation.csv")
    dist_processes = pd.read_csv(PROCESS_CONCORDANCES / "distribution.csv")
    dummy_processes = pd.read_csv(PROCESS_CONCORDANCES / "dummies.csv")
    production_processes = pd.read_csv(PROCESS_CONCORDANCES / "production.csv")

    # remove non-process data
    df = df[df["Process"] != "-"]
    # remove identified demand processes
    df = df[~df["Process"].isin(demand_processes["Process"].unique())]

    # remove identified elec processes
    df = df[~df["Process"].isin(elec_processes["Process"].unique())]

    # remove identified distribution processes
    df = df[~df["Process"].isin(dist_processes["Process"].unique())]

    # dummies
    df = df[~df["Process"].isin(dummy_processes["Process"].unique())]

    # production
    df = df[~df["Process"].isin(production_processes["Process"].unique())]

    if len(df) > 0:
        print("FAILURE: The following processes have no descriptions")
        df = df.sort_values("Process")
        remaining_processes = df["Process"].unique()
        for process in remaining_processes:
            print("    ", process)

    # print(df)


def check_commodity_coverage(df):
    """
    Checks every commodity in model output results
    Ensures that they are identified in one of our commodity description files

    Simply prints results to console
    """

    # commodity codes

    demand_commodities = pd.read_csv(COMMODITY_CONCORDANCES / "demand.csv")
    energy_commodities = pd.read_csv(COMMODITY_CONCORDANCES / "energy.csv")
    emission_commodities = pd.read_csv(COMMODITY_CONCORDANCES / "emissions.csv")
    currency_commodities = pd.read_csv(COMMODITY_CONCORDANCES / "currency.csv")

    # remove non-commodity data
    df = df[df["Commodity"] != "-"]
    # demand commodities
    df = df[~df["Commodity"].isin(demand_commodities["Commodity"].unique())]
    # energy commodities
    df = df[~df["Commodity"].isin(energy_commodities["Commodity"].unique())]
    # emissions
    df = df[~df["Commodity"].isin(emission_commodities["Commodity"].unique())]
    # currencies
    df = df[~df["Commodity"].isin(currency_commodities["Commodity"].unique())]

    if len(df) > 0:
        print("The following commodities have no descriptions!")
        df = df.sort_values("Commodity")
        remaining_commodities = df["Commodity"].unique()
        for comm in remaining_commodities:
            print("    ", comm)
    else:
        print("SUCCESS: Model data has full commodity code coverage")

    # print(demand_commodities)


def check_coverage(df):
    """
    Runs full process and commodity checks to console
    Everything the model outputs should be covered in our description files
    Or outputs will be wrong/misinterpreted
    """

    check_commodity_coverage(df)
    check_process_coverage(df)


def load_scenario_results(scenario_name):
    """
    Wraps a scenario loading method (read_vd)
    and checks commodity/process description coverage.

    returns the full dataframe.
    Note that it does not attempt to label the data.
    """

    scenario_file = SCENARIO_FILES / f"{scenario_name}.vd"

    df = read_vd(scenario_file)

    check_coverage(df)
    return df
