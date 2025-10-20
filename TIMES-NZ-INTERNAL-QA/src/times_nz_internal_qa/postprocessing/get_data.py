"""
Data loading and quality check functions
"""

# Libraries

import re
from pathlib import Path

import pandas as pd
from times_nz_internal_qa.app.config import current_scenarios
from times_nz_internal_qa.utilities.filepaths import (
    COMMODITY_CONCORDANCES,
    PROCESS_CONCORDANCES,
    SCENARIO_FILES,
)

# Functions - coverage checks ------------------------------


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


# DATA LOADING


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


def find_veda_working_directory(base_dir=None):
    """
    Locate the VEDA working directory by scanning for a folder named "GAMS_WrkTIMES"
    under any directory whose name contains "veda" (case-insensitive).

    The search is one level deep for "*veda*" under `base_dir`, then recursive within
    each match for "GAMS_WrkTIMES". Useful on WSL where Windows drives are mounted
    at `/mnt/c/Users/...`.

    Args:
        base_dir (pathlib.Path | str | None): Directory to start from. Defaults to
            Path("/mnt/c/Users") if None.

    Returns:
        pathlib.Path | None: Full path to the first "GAMS_WrkTIMES" found, or None
        if not found. Prints a message on success/failure.

    Example:
        >>> find_veda_working_directory()
        PosixPath('/mnt/c/Users/SearleL/Veda/GAMS_WrkTIMES')

    Notes:
        - Match for "veda" is case-insensitive.
        - Stops at the first match; adjust if you need all matches.
        - On native Windows, pass a Windows path (e.g., r'C:\\Users') instead of /mnt paths.
    """
    if base_dir is None:
        base_dir = Path("/mnt/c/Users")
    for dir_path in base_dir.iterdir():
        if dir_path.is_dir() and "veda" in dir_path.name.lower():
            for sub_dir_path in dir_path.rglob("GAMS_WrkTIMES"):
                if sub_dir_path.is_dir():
                    print("VEDA working directory found:", sub_dir_path)
                    return sub_dir_path
    print(f"VEDA working directory not found under {base_dir}.")
    return None


def get_latest_scenario_vd_name(wd: Path, scenario: str):
    """
    Returns the latest name of the input vd file.

    Just returns the string name.
    wd/scenario contains files like:
      <scenario>_0810.vd, <scenario>_1010.vd
    Returns (latest_path, all_matches_sorted).

    Example usage:
    latest, all_vd = get_latest_scenario_from_veda(
        Path("/mnt/c/Users/SearleL/Veda/GAMS_WrkTIMES"),
        "traditional-v3_0_0")

    print("latest:", latest)

    """
    folder = Path(wd) / scenario
    pat = re.compile(rf"^{re.escape(scenario)}_(\d{{4}})\.vd$", re.IGNORECASE)

    matches = []
    for f in folder.iterdir():
        if f.is_file():
            m = pat.match(f.name)
            if m:
                code = int(m.group(1))  # e.g. 0810 -> 810 -> fine for ordering
                matches.append((code, f.stat().st_mtime, f))
    if not matches:
        return None, []
    matches.sort(key=lambda t: (t[0], t[1]))  # by date code, then mtime
    latest_file = matches[-1][2]
    return latest_file


def get_results_from_veda(scenario, veda_base_dir):
    """
    Takes the scenario name and looks in the appropriate folder
    Also assumes Veda is stored under your windows mount username

    Saves the compressed raw results to this directory
    """
    veda_base_dir = Path(veda_base_dir)

    veda_wd = find_veda_working_directory(veda_base_dir)
    latest_scenario_results = get_latest_scenario_vd_name(veda_wd, scenario)
    df = read_vd(latest_scenario_results)
    check_coverage(df, scenario)

    df.to_csv(SCENARIO_FILES / f"{scenario}.csv", index=False)
    print(f"Saved results from '{scenario}' to {SCENARIO_FILES}")

    return df


def main():
    """
    Entry point
    currently using my username to speed this up (sorry)
    swap for your user name, or better yet, automate find_veda_working_directory() better
    might need adjusting depending on the setup anyway
    note that trawling windows files from linux can be very slow
    so would need to be a bit careful about how to approach
    """

    print("WARNING: Using hardcoded (not portable) Veda location")
    for scenario in current_scenarios:
        get_results_from_veda(scenario, "/mnt/c/Users/weerasa")


if __name__ == "__main__":
    main()
