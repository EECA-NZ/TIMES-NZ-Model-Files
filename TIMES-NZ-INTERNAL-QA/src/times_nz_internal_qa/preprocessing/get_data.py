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


def test_coverage(df, result_type, scenario_name):
    """
    takes a df which has already been filtered to remove everything we found coverage for

    Simply outputs a test describing what's left (or success if there's nothing)
    type must be one of "Process" or "Commodity"
    """

    if result_type not in ["Process", "Commodity"]:
        print(
            f"Cannot test '{result_type}' coverage. Please enter 'Process' or 'Commodity'"
        )

    if len(df) > 0:
        # failure
        print(
            f"FAILURE: Could not find descriptions for '{result_type}' found in {scenario_name}:"
        )
        df = df.sort_values(result_type)
        uncovered_items = df[result_type].unique()
        for item in uncovered_items:
            print("    ", item)
    else:
        print(f"SUCCESS: Full coverage of each {result_type} in {scenario_name}")


def check_process_coverage(df, scenario_name):
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

    test_coverage(df, "Process", scenario_name=scenario_name)

    # print(df)


def check_commodity_coverage(df, scenario_name):
    """
    Checks every commodity in model output results
    Ensures that they are identified in one of our commodity description files

    Simply prints results to console
    Note: any failures might mean we need to tweak our description files
    Or add a whole new section, depending
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

    test_coverage(df, "Commodity", scenario_name=scenario_name)


def check_coverage(df, scenario_name):
    """
    Runs full process and commodity checks to console
    Everything the model outputs should be covered in our description files
    Or outputs will be wrong/misinterpreted
    """

    check_commodity_coverage(df, scenario_name=scenario_name)
    check_process_coverage(df, scenario_name=scenario_name)


def load_scenario_results(scenario_name):
    """
    Wraps a scenario loading method (read_vd)
    and checks commodity/process description coverage.

    returns the full dataframe.
    Note that it does not attempt to label the data.
    """

    scenario_file = SCENARIO_FILES / f"{scenario_name}.vd"

    df = read_vd(scenario_file)

    check_coverage(df, scenario_name)
    df["Scenario"] = scenario_name
    return df
