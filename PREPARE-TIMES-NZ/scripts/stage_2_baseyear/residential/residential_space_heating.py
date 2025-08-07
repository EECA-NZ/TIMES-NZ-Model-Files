"""

Builds and applies a residential space‑heating disaggregation model
for EEUD data.

This module provides functions to:

  1. Load and clean StatsNZ census dwelling & heating data.
  2. Aggregate private dwelling types into standardized categories.
  3. Compute normalized heating‑technology shares by region.
  4. Merge in assumptions: floor area, heating efficiency, HDD.
  5. Build a space‑heating demand model to derive fuel demand shares.
  6. Distribute modelled shares against the EEUD residential space‑heating data.
  7. Split Gas/LPG demand between North and South Islands and by fuel.
  8. Saves final results to: residential_space_heating_disaggregation.csv

Constants at the top define filepaths and the base year.

Based on methodology found at:

https://www.sciencedirect.com/science/article/pii/S0378778825004451?ref=pdf_download&fr=RR-2&rr=9677b4c2bbe71c50

"""

import numpy as np
import pandas as pd
from prepare_times_nz.utilities.filepaths import (
    ASSUMPTIONS,
    CONCORDANCES,
    STAGE_1_DATA,
    STAGE_2_DATA,
)
from prepare_times_nz.utilities.logger_setup import blue_text, logger

# filepaths --------------------------------------------

RESIDENTIAL_ASSUMPTIONS = ASSUMPTIONS / "residential"
OUTPUT_LOCATION = STAGE_2_DATA / "residential"
CHECKS_LOCATION = OUTPUT_LOCATION / "checks"

# constants -----------------

BASE_YEAR = 2023
RUN_TESTS = False

# Data locations -----------------------------
EEUD_FILE = STAGE_1_DATA / "eeud/eeud.csv"
DWELLING_HEATING_FILE = STAGE_1_DATA / "statsnz/dwelling_heating.csv"

# Assumptions --------------------------------------------

HDD_ASSUMPTIONS = RESIDENTIAL_ASSUMPTIONS / "regional_hdd_assumptions.csv"
EFF_ASSUMPTIONS = RESIDENTIAL_ASSUMPTIONS / "heat_eff_assumptions.csv"
FLOOR_AREAS = RESIDENTIAL_ASSUMPTIONS / "floor_area_per_dwelling.csv"

# CONCORDANCES -----------------------------------------

REGION_ISLAND_CONCORDANCE = CONCORDANCES / "region_island_concordance.csv"


# Functions -----------------------------------------


def get_latest_census_year(df, base_year=BASE_YEAR, year_variable="CensusYear"):
    """
    Filters the census data according to the base year
    If the base year is not available in the census (ie base year 2024)
    Then we just return the latest data

    NOTE:
    This could also interpolate the underlying data,
    So we could have a base year between census years
    That use case seems extremely unlikely so that feature has not been built
    """

    census_years = df[year_variable].unique()
    latest_census = max(census_years)

    if base_year in census_years:
        # logger.info("Census data is available for the base year!")
        df = df[df[year_variable] == base_year]
    else:
        logger.info("The base year (%s) is not available in the census.", base_year)
        logger.info("Returning latest census data for %s", latest_census)
        df = df[df[year_variable] == latest_census]

    return df


def clean_census_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and standardize census heating data.

    This will:
      1. Rename raw census columns to more intuitive names.
      2. Drop rows for regions we don’t need.
      3. Strip the trailing " Region" suffix from Area names.

    Parameters
    ----------
    df : pandas.DataFrame
        Input must contain:
        - 'MainTypesOfHeatingUsed'
        - 'PrivateDwellingType'
        - 'Area'

    Returns
    -------
    pandas.DataFrame
        - 'MainTypesOfHeatingUsed' renamed to 'HeatingType'
        - 'PrivateDwellingType' renamed to 'DwellingType'
        - Rows where 'Area' is in REGIONS_TO_EXCLUDE removed
        - 'Area' values with a trailing " Region" suffix cleaned

    Raises
    ------
    KeyError
        If any of 'MainTypesOfHeatingUsed', 'PrivateDwellingType', or
        'Area' is missing from the input DataFrame.
    """

    required = {
        "MainTypesOfHeatingUsed",
        "PrivateDwellingType",
        "Area",
    }
    missing = required - set(df.columns)
    if missing:
        raise KeyError(f"Missing required column(s): {missing}")

    regions_to_exclude = [
        "Area Outside Region",  # ignore the Chathams
        "Total - New Zealand by regional council",
        "Total - New Zealand by health region/health district",
    ]

    # 1. Rename for clarity
    df = df.rename(
        columns={
            "MainTypesOfHeatingUsed": "HeatingType",
            "PrivateDwellingType": "DwellingType",
        }
    )

    # 2. Drop unwanted regions
    df = df.loc[~df["Area"].isin(regions_to_exclude)]

    # 3. Remove trailing " Region" from area names
    df["Area"] = df["Area"].str.replace(r" Region$", "", regex=True)

    return df


def aggregate_dwelling_types(
    df: pd.DataFrame,
    run_tests: bool = RUN_TESTS,
) -> pd.DataFrame:
    """
    Aggregate private dwelling types into higher‑level categories.

    Maps raw census dwelling labels into 'Detached', 'Joined', or 'Total',
    then sums 'Value' across all other dimensions. Optionally runs
    consistency tests against the original 'Total' rows.

    Parameters
    ----------
    df : pandas.DataFrame
        Must contain at least:
          - 'DwellingType': raw dwelling labels.
          - 'Value': numeric counts.
          - any other grouping columns (e.g. 'Area', 'CensusYear').
    run_tests : bool, default False
        If True, compares aggregated sums against original totals and
        logs warnings if discrepancies exceed tolerance.

    Returns
    -------
    pandas.DataFrame
        - 'DwellingType' in {'Detached','Joined'} (no 'Total' rows
          unless run_tests=True).
        - 'Value' summed by all other columns.

    Raises
    ------
    KeyError
        If 'DwellingType' or 'Value' missing from input.
    """

    required = {"DwellingType", "Value"}
    missing = required - set(df.columns)
    if missing:
        raise KeyError(f"Missing required column(s): {missing}")

    dwelling_type_mapping = {
        "Private dwelling not further defined": "Detached",
        "Other private dwelling": "Detached",
        "Separate house": "Detached",
        "Joined dwelling": "Joined",
        "Total - private dwelling type": "Total",
    }

    df = df.copy()
    df["DwellingType"] = df["DwellingType"].map(dwelling_type_mapping)

    # Sum 'Value' by all columns except itself to aggregate new dwellings
    group_cols = [col for col in df.columns if col != "Value"]
    df = df.groupby(group_cols, as_index=False)["Value"].sum()

    if run_tests:
        # Compare our aggregates to the original 'Total' rows
        df_totals = df.loc[df["DwellingType"] == "Total"]
        df_others = df.loc[df["DwellingType"] != "Total"]

        sum_cols = [
            col for col in df_others.columns if col not in ("Value", "DwellingType")
        ]
        test = (
            df_others.groupby(sum_cols, as_index=False)["Value"]
            .sum()
            .merge(
                df_totals.rename(columns={"Value": "Total"}),
                on=sum_cols,
                how="left",
            )
        )
        test["Delta"] = (test["Value"] - test["Total"]).abs()
        tolerance = 15
        errors = test.loc[test["Delta"] > tolerance]

        if not errors.empty:
            logger.warning("Some mismatches found in dwelling type aggregation")
            print(errors)
        else:
            logger.warning("Dwelling type aggregation successful")
    else:
        # Drop the 'Total' rows if not testing
        df = df.loc[df["DwellingType"] != "Total"]

    return df


def get_dwelling_heating_data(run_tests: bool = RUN_TESTS) -> pd.DataFrame:
    """
    Load and preprocess dwelling‑heating counts by region.

    This function performs the following steps:
      1. Reads raw dwelling‑heating data from DWELLING_HEATING_FILE.
      2. Filters rows to the BASE_YEAR census (or latest available).
      3. Cleans region names and heating labels.
      4. Aggregates dwelling types into 'Detached' and 'Joined',
         optionally running consistency checks.

    Parameters
    ----------
    run_tests : bool, default RUN_TESTS
        If True, the aggregation step logs warnings when
        summed counts diverge from original totals.

    Returns
    -------
    pd.DataFrame
        A DataFrame containing:
        - CensusYear
        - Area
        - DwellingType (one of 'Detached' or 'Joined')
        - HeatingType
        - Value (counts of dwellings)
    """
    # 1. Load raw CSV
    df = pd.read_csv(DWELLING_HEATING_FILE)

    # 2. Filter to the base or latest census year
    df = get_latest_census_year(df)

    # 3. Clean region names and rename columns
    df = clean_census_data(df)

    # 4. Aggregate dwelling types with optional tests
    df = aggregate_dwelling_types(df, run_tests)

    return df


def get_total_dwellings_per_region(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract total dwellings reporting any heating, per region.

    Filters to only those rows where the census recorded
    “total stated” heating, drops the now‑irrelevant
    HeatingType column, and renames the raw count into a more
    descriptive field.

    Parameters
    ----------
    df : pandas.DataFrame
        Input must contain 'HeatingType', 'Value', and any
        regional identifiers (e.g. 'Area', 'CensusYear').

    Returns
    -------
    pandas.DataFrame
        Subset with only rows where HeatingType equals
        TOTAL_HEATING_TYPE, 'HeatingType' removed, and 'Value'
        renamed to 'TotalDwellingsInRegion'.

    Raises
    ------
    KeyError
        If 'HeatingType' or 'Value' missing from the input.
    """
    required_cols = {"HeatingType", "Value"}
    missing = required_cols - set(df.columns)
    if missing:
        raise KeyError(f"Missing required column(s): {missing}")

    df = df[df["HeatingType"] == "Total stated - main types of heating used"]
    df = df.drop("HeatingType", axis=1)
    df = df.rename(columns={"Value": "TotalDwellingsInRegion"})

    return df


def get_heating_shares(
    df: pd.DataFrame,
    run_tests: bool = RUN_TESTS,
) -> pd.DataFrame:
    """
    Compute normalized heating‑type shares per region and dwelling.
    Here we are taking the census "most common" heating types
    And assuming these represent shares of total heating
    The original data allowed for multiple entries per dwelling
    So this creates a slight distortion

    Steps:
      1. Exclude aggregate or non‑specific heating categories.
      2. For each (CensusYear, Area, DwellingType), sum Value to get Total
      3. Compute each row’s share: Value/Total
      4. Optionally test that shares sum to 1 (within tolerance) and log warnings.

    Parameters
    ----------
    df : pandas.DataFrame
        Input must contain columns:
          - 'CensusYear'
          - 'Area'
          - 'DwellingType'
          - 'HeatingType'
          - VALUE_COL
    run_tests : bool, default RUN_TESTS
        If True, validates that computed shares sum to 1 and logs if not.

    Returns
    -------
    pandas.DataFrame
        DataFrame with columns:
          - CensusYear, Area, DwellingType, HeatingType
          - SHARE_COL (normalized share of heating)
    Raises
    ------
    KeyError
        If any of the required columns are missing.
    """

    required = {
        "CensusYear",
        "Area",
        "DwellingType",
        "HeatingType",
        "Value",
    }
    missing = required - set(df.columns)
    if missing:
        raise KeyError(f"Missing required column(s): {missing}")

    heating_to_remove = [
        "Total stated - main types of heating used",
        "No heating used",
        "Other types of heating",
    ]

    df = df.copy()  # clarifying this is not a view

    df = df[~df["HeatingType"].isin(heating_to_remove)]

    df["Total"] = df.groupby(["CensusYear", "Area", "DwellingType"])["Value"].transform(
        "sum"
    )
    df["FuelHeatingShare"] = df["Value"] / df["Total"]

    # heating share should sum to 1 for every area and dwelling type

    if run_tests:
        test = df.copy()
        test["should_be_one"] = test.groupby(["CensusYear", "Area", "DwellingType"])[
            "FuelHeatingShare"
        ].transform("sum")
        test["should_be_one"] = round(test["should_be_one"], 6)  # float tolerance 6

        test = test[test["should_be_one"] != 1]

        if len(test) > 0:
            logger.warning("Something has gone wrong in the heatingshare calculations!")
            logger.warning(
                "The table grain is not expected by get_heating_shares_per_region()."
            )
            logger.warning("Please review")

    df = df.drop(["Value", "Total"], axis=1)

    return df


def add_assumptions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Join efficiency, floor‑area, and HDD assumptions into the model data.

    Performs three merges, pulling in:
      1. Heat efficiency assumptions (EFF_ASSUMPTIONS),
      2. Floor‑area per dwelling (FLOOR_AREAS),
      3. Heating degree days per region (HDD_ASSUMPTIONS).

    Parameters
    ----------
    df : pandas.DataFrame
        Input must contain:
          - 'DwellingType' (for floor area merge)
          - 'Area'        (for HDD merge)
          - any columns produced by earlier steps (e.g.
            'FuelHeatingShare', 'TotalDwellingsInRegion').

    Returns
    -------
    pandas.DataFrame
        Original rows plus these new columns:
          - 'EFF'       (heat efficiency)
          - 'FloorArea' (area to heat per dwelling)
          - 'HDD'       (degree‑day heating factor)

    Raises
    ------
    KeyError
        If 'DwellingType' or 'Area' is missing from the input DataFrame.
    """
    # validate required columns
    missing = {"DwellingType", "Area"} - set(df.columns)
    if missing:
        raise KeyError(f"Missing required column(s): {missing}")

    heat_eff_assumptions = pd.read_csv(EFF_ASSUMPTIONS)

    # efficiencies
    df = pd.merge(df, heat_eff_assumptions)
    df = df.drop("Note", axis=1)
    # floor areas

    floor_areas = pd.read_csv(FLOOR_AREAS)
    df = pd.merge(df, floor_areas, on="DwellingType", how="left")
    df = df.drop("Note", axis=1)
    # hdd
    # first, just select relevant fields
    hdd_data = pd.read_csv(HDD_ASSUMPTIONS)
    hdd_data = hdd_data[["Region", "HDD"]]
    hdd_data = hdd_data.rename(columns={"Region": "Area"})
    df = pd.merge(df, hdd_data, how="left")

    return df


def build_sh_model(df):
    """
    Use inputs to build space heating model.
    All model calculations are in this function

    Input: a dataframe with the necessary data/assumptions.
    Outputs a dataframe with the key new variable:
        FuelDemandShare

    FuelDemandShare is the share of tech/fuel demand for each region and dwelling type
    We can apply this directly to the EEUD to get the fuel demand disaggregation

    """
    # Total heat demand is a function of dwelling count * floor area * HDD
    # ie, each dwelling has a floor area to heat and some hdd to heat it by
    # the units here are very abstract
    df["ModelHeatDemand"] = df["TotalDwellingsInRegion"] * df["FloorArea"] * df["HDD"]

    # FuelHeatingShare is the share of fuel/tech as reported in the census
    # This is really a bit of a proxy from census data on "most common heating techs"
    # We treat this as the share of end use (ie heat demand not fuel demand)
    # Model heat demand is NOT per fuel
    # So we disaggregate the fuel demand as a function of:
    #   fuelheatingshare and
    #   reverse efficiency
    # the apply these shares to the modelled heat demand
    # This gives modelled fuel demand per heating category, dwellingtype, and region
    df["ModelHeatFuelInput"] = df["FuelHeatingShare"] / df["EFF"]
    df["ModelHeatFuelInput"] = df["ModelHeatFuelInput"] * df["ModelHeatDemand"]

    # we then just want to find the share of fuel demand (within each tech)
    # per region and dwelling type

    # First, aggregate up to define the grain (this should already be the grain?)
    df = (
        df.groupby(["CensusYear", "Area", "DwellingType", "Technology", "Fuel"])[
            "ModelHeatFuelInput"
        ]
        .sum()
        .reset_index()
    )
    # we create a total of these based on our EEUD grain
    df["TotalModelFuelInput"] = df.groupby(["CensusYear", "Technology", "Fuel"])[
        "ModelHeatFuelInput"
    ].transform("sum")

    # finally, the share of total fuel demand by area/dwellingtype
    # this is what we'll use to disaggregate the heating demand
    df["FuelDemandShare"] = df["ModelHeatFuelInput"] / df["TotalModelFuelInput"]

    return df


def get_eeud_space_heating_data():
    """
    Returns the EEUD residential space heating data
    for the selected base year.
    Aggregates Natural gas and LPG together,
    because we don't have this detail in the heat model
    so these fuels need to be disaggregated later
    """
    # get EEUD data for residential space heating

    eeud = pd.read_csv(EEUD_FILE)
    df = eeud[eeud["Sector"] == "Residential"]
    df = df[df["EndUse"] == "Low Temperature Heat (<100 C), Space Heating"]
    df = df[df["Year"] == BASE_YEAR]

    # aggregate EEUD LPG/natural gas together
    df.loc[df["Fuel"].isin(["Natural Gas", "LPG"]), "Fuel"] = "Gas/LPG"
    group_cols = [col for col in df.columns if col != "Value"]
    df = df.groupby(group_cols)["Value"].sum().reset_index()

    return df


def apply_sh_model_to_eeud(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply space‑heating model shares to EEUD residential demand data.

    This function merges precomputed fuel‑demand shares into the
    EEUD (Energy End‑Use Database) for residential space heating,
    then scales the raw EEUD values by those shares to produce a
    fully disaggregated demand breakdown by technology and fuel.

    Parameters
    ----------
    df : pandas.DataFrame
        Model output containing columns:
        - 'Technology'
        - 'Fuel'
        - 'FuelDemandShare'

    Returns
    -------
    pandas.DataFrame
        A DataFrame with the same schema as the EEUD residential space
        heating subset, but with its 'Value' column replaced by
        disaggregated demand

    """
    # get EEUD
    sh_eeud = get_eeud_space_heating_data()

    # join input to EEUD
    df = pd.merge(sh_eeud, df, on=["Technology", "Fuel"], how="left")

    # modify Values based on shares
    df["Value"] = df["Value"] * df["FuelDemandShare"]

    return df


def disaggregate_space_heating_demand() -> pd.DataFrame:
    """
    Disaggregate residential space heating demand using census and EEUD data.

    This orchestrator function performs the following steps:
      1. Load and preprocess census dwelling/heating data.
      2. Compute normalized heating shares per region and dwelling.
      3. Extract total dwellings per region.
      4. Merge total dwellings with heating shares.
      5. Join in assumptions: fuel efficiencies, floor areas, HDD.
      6. Build the space‑heating model to compute FuelDemandShare.
      7. Apply those shares to the EEUD residential space heating data.

    Returns
    -------
    pandas.DataFrame
        Disaggregated residential space heating demand for the BASE_YEAR.
        Contains one row per combination of:
        (Year, Area, DwellingType, Technology, Fuel)
        with the 'Value' column equal to the disaggregated demand.

    Raises
    ------
    Any exceptions from the individual steps if required data
    or columns are missing (KeyError, FileNotFoundError, etc.).
    """

    # get dwelling/heating data
    dwelling_heating_data_tidy = get_dwelling_heating_data()
    # get heating shares
    heating_shares = get_heating_shares(dwelling_heating_data_tidy)
    # total dwellings from same dataset
    total_dwellings = get_total_dwellings_per_region(dwelling_heating_data_tidy)

    # Combine
    model_df = pd.merge(
        total_dwellings,
        heating_shares,
        on=["Area", "CensusYear", "DwellingType"],
        how="left",
    )

    # add assumptions (efficiency and floor area)
    model_df = add_assumptions(model_df)
    # Build model heat demand
    model_df = build_sh_model(model_df)
    # apply calculated shares to EEUD
    model_df = apply_sh_model_to_eeud(model_df)

    return model_df


def get_burner_island_split() -> pd.DataFrame:
    """
    Compute the North/South Island split for Gas/LPG burners.

    Steps
    -----
    1. Load region–island concordance from REGION_ISLAND_CONCORDANCE.
    2. Run disaggregate_space_heating_demand() to get full model output.
    3. Filter for Fuel == Natural Gas/LPG.
    4. Merge island labels on 'Area'.
    5. Sum 'Value' by 'Island' and compute share.

    Returns
    -------
    pandas.DataFrame
        A DataFrame with columns:
        - Island : str, 'NI' or 'SI'
        - Value  : float, total Gas/LPG demand for that island
        - Share  : float, fraction of total Gas/LPG demand

    Raises
    ------
    KeyError
        If required columns ('Area', 'Fuel', 'Value', 'Island') are missing
        after the merge.

    """
    # 1. Load concordance
    ri_df = pd.read_csv(REGION_ISLAND_CONCORDANCE)
    ri_df = ri_df.rename(columns={"Region": "Area"})

    # 2. Get full disaggregated demand
    model_df = disaggregate_space_heating_demand()

    # 3. Filter to Gas/LPG burners
    try:
        gas_df = model_df.loc[model_df["Fuel"] == "Gas/LPG"].copy()
    except KeyError as e:
        raise KeyError(f"Missing expected column in model output: {e}") from e

    # 4. Merge in Island labels
    merged = pd.merge(gas_df, ri_df, on="Area", how="left", validate="many_to_one")

    # Validate merge result
    if "Island" not in merged.columns:
        raise KeyError("Merge failed to produce 'Island' column")

    # 5. Compute totals and shares
    agg = merged.groupby("Island", as_index=False)["Value"].sum()
    total = agg["Value"].sum()
    agg["Share"] = agg["Value"] / total

    return agg


def get_burner_fuel_split() -> pd.DataFrame:
    """
    Compute the share of Natural Gas vs LPG for residential burners.

    Steps
    -----
    1. Read the EEUD CSV.
    2. Filter to:
       - Sector == RES_SECTOR
       - EndUse == SPACE_HEATING_ENDUSE
       - Year == BASE_YEAR
       - Fuel in TARGET_FUELS
    3. Sum 'Value' by 'Fuel'.
    4. Compute each fuel’s fraction of the total.

    Returns
    -------
    pandas.DataFrame
        Columns:
        - Fuel : str, either "Natural Gas" or "LPG"
        - Value : float, total EEUD value for that fuel
        - Share : float, Value divided by the sum of both fuels

    Raises
    ------
    KeyError
        If any of 'Sector', 'EndUse', 'Year', 'Fuel', or 'Value'
        is missing from the EEUD data.
    FileNotFoundError
        If EEUD_FILE cannot be read.
    """

    # Load EEUD data
    eeud = pd.read_csv(EEUD_FILE)

    # Validate required columns
    required = {"Sector", "EndUse", "Year", "Fuel", "Value"}
    missing = required - set(eeud.columns)
    if missing:
        raise KeyError(f"Missing required column(s): {missing}")

    # Filter to residential space heating and target fuels
    filtered = eeud.loc[
        (eeud["Sector"] == "Residential")
        & (eeud["EndUse"] == "Low Temperature Heat (<100 C), Space Heating")
        & (eeud["Year"] == BASE_YEAR)
        & (eeud["Fuel"].isin(["Natural Gas", "LPG"]))
    ]

    # Aggregate total Value by Fuel
    agg = filtered.groupby("Fuel", as_index=False)["Value"].sum()

    # Compute share
    total = agg["Value"].sum()
    agg["Share"] = agg["Value"] / total

    return agg


def get_ni_lpg_share():
    """
    Estimate the share of LPG used in the North Island (NI) for direct heat burners.

    Assumptions:
    - The heating model does not distinguish gas from LPG.
    - All South Island (SI) burner demand is LPG.
    - All Natural Gas (NGA) is used in the NI.

    Steps:
    1. Get the burner fuel split (Natural Gas vs LPG) from EEUD.
    2. Get the NI/SI burner demand split from model data.
    3. Ensure NI burner share can support the natural gas share.
    4. Calculate remaining LPG available to NI.
    5. Compute and return NI LPG share.
    """

    # 1. get fuel shares of burner demand  from EEUD
    burner_fuel_split = get_burner_fuel_split()

    # 2. Get island shares of burner demand from SH model
    burner_island_split = get_burner_island_split()

    # 3. Validate feasibility of NI supporting all natural gas demand
    nat_gas_share = burner_fuel_split.loc[
        burner_fuel_split["Fuel"] == "Natural Gas", "Share"
    ].iloc[0]
    ni_share = burner_island_split.loc[
        burner_island_split["Island"] == "NI", "Share"
    ].iloc[0]

    if ni_share < nat_gas_share:
        logger.warning(
            "Natural gas share exceeds NI burner share — potential model issue."
        )
    else:
        logger.info("Natural gas share is feasible given NI burner demand.")

    # 4. Calculate total NI LPG use
    si_total_lpg = burner_island_split.loc[
        burner_island_split["Island"] == "SI", "Value"
    ].iloc[0]
    total_lpg = burner_fuel_split.loc[burner_fuel_split["Fuel"] == "LPG", "Value"].iloc[
        0
    ]
    ni_total_lpg = total_lpg - si_total_lpg

    # Validate total NI burner demand = NI NGA + NI LPG
    tolerance = 6
    total_nga = burner_fuel_split.loc[
        burner_fuel_split["Fuel"] == "Natural Gas", "Value"
    ].iloc[0]
    total_ni = burner_island_split.loc[
        burner_island_split["Island"] == "NI", "Value"
    ].iloc[0]
    error = abs(round((total_nga + ni_total_lpg) - total_ni, tolerance))

    if error != 0:
        logger.warning("Mismatch between NI demand and (NGA + LPG) supply.")
    else:
        logger.info("NI supply balances correctly between NGA and LPG.")

    # 5. Final LPG share for NI
    ni_lpg_share = ni_total_lpg / total_ni
    return ni_lpg_share


def distribute_burner_gas(df):
    """
    Takes the input space heating model,
    which aggregates gas burners among Gas/LPG

    Uses island definition assumptions to split the Gas/LPG across islands:

    ie: No Natural Gas in the South Island
    """
    # get region island concordance
    ri_concordance = pd.read_csv(REGION_ISLAND_CONCORDANCE)
    ri_concordance = ri_concordance.rename(columns={"Region": "Area"})

    # add island tags
    df = pd.merge(df, ri_concordance, on="Area", how="left")
    # separate out the gas/lpg
    df_gas_lpg = df[df["Fuel"] == "Gas/LPG"]
    # remove from main
    df = df[df["Fuel"] != "Gas/LPG"]

    # add the lpg shares
    ni_lpg_share = get_ni_lpg_share()
    df_gas_lpg["LPGShare"] = np.where(df_gas_lpg["Island"] == "SI", 1, ni_lpg_share)

    # create lpg data
    df_lpg = df_gas_lpg.copy()

    df_lpg["Fuel"] = "LPG"
    df_lpg["Value"] = df_lpg["Value"] * df_lpg["LPGShare"]
    df_lpg = df_lpg.drop("LPGShare", axis=1)

    # create gas data (inverse of LPG)

    df_gas = df_gas_lpg.copy()
    df_gas["Fuel"] = "Natural Gas"
    df_gas["Value"] = df_gas["Value"] * (1 - df_gas["LPGShare"])
    df_gas = df_gas.drop("LPGShare", axis=1)

    # add the new data back to main dataframe

    df = pd.concat([df, df_gas, df_lpg])

    return df


def main():
    """Main entry point. Creates output directories and saves
    space heating data"""
    # create dirs
    OUTPUT_LOCATION.mkdir(parents=True, exist_ok=True)
    CHECKS_LOCATION.mkdir(parents=True, exist_ok=True)

    # run model
    res_sh_df = disaggregate_space_heating_demand()
    # distribute the burner gas
    res_sh_df = distribute_burner_gas(res_sh_df)

    # save
    output_file = OUTPUT_LOCATION / "residential_space_heating_disaggregation.csv"
    logger.info("Saving space heating results to %s", blue_text(output_file))
    res_sh_df.to_csv(output_file, index=False, encoding="utf-8-sig")


# Execute
if __name__ == "__main__":
    main()
