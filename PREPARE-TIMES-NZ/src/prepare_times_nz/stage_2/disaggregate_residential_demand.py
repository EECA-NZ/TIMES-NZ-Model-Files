import numpy as np
import pandas as pd
from prepare_times_nz.utilities.filepaths import (
    ASSUMPTIONS,
    CONCORDANCES,
    STAGE_1_DATA,
    STAGE_2_DATA,
)
from prepare_times_nz.utilities.logger_setup import blue_text, logger

# Main filepaths --------------------------------------------

RESIDENTIAL_ASSUMPTIONS = ASSUMPTIONS / "residential"
OUTPUT_LOCATION = STAGE_2_DATA / "residential"
CHECKS_LOCATION = OUTPUT_LOCATION / "checks"

# constants -----------------

BASE_YEAR = 2023
RUN_TESTS = False

# Data locations -----------------------------

EEUD_FILE = STAGE_1_DATA / "eeud/eeud.csv"
DWELLING_HEATING_FILE = STAGE_1_DATA / "statsnz/dwelling_heating.csv"
POP_DWELLING = STAGE_1_DATA / "statsnz/population_by_dwelling.csv"

# Assumptions --------------------------------------------

HDD_ASSUMPTIONS = RESIDENTIAL_ASSUMPTIONS / "regional_hdd_assumptions.csv"
EFF_ASSUMPTIONS = RESIDENTIAL_ASSUMPTIONS / "eff_by_tech_and_fuel.csv"
CENSUS_EFF_ASSUMPTIONS = RESIDENTIAL_ASSUMPTIONS / "eff_for_census_heating_types.csv"
FLOOR_AREAS = RESIDENTIAL_ASSUMPTIONS / "floor_area_per_dwelling.csv"

# CONCORDANCES -----------------------------------------

ISLAND_FILE = CONCORDANCES / "region_island_concordance.csv"


# Helpers ----------------------------------


def save_output(df, name, dir=OUTPUT_LOCATION):
    """Save DataFrame output to the output location."""
    filename = f"{dir}/{name}"
    logger.info("Saving output:\n%s", blue_text(filename))
    df.to_csv(filename, index=False, encoding="utf-8-sig")


def save_checks(df, name, label, dir=CHECKS_LOCATION):
    """Save DataFrame checks to the checks location."""
    filename = f"{dir}/{name}"
    logger.info("Saving %s:\n%s", label, blue_text(filename))
    df.to_csv(filename, index=False, encoding="utf-8-sig")


# Population functions -----------------------------------------


def get_population_data(filepath=POP_DWELLING, base_year=BASE_YEAR):
    """Loads census pop/dwelling data
    Returns the df filtered to input baseyear

    IMPORTANT NOTE: this is not full dwelling/pop coverage
    So, we can use the shares of pop per dwelling type and region

    But we can't use the totals to imply total pop or dwellings

    It is best to instead apply these shares to actual pop/dwelling counts
    """

    df = pd.read_csv(filepath)
    df = df[df["CensusYear"] == base_year]

    return df


def clean_population_data(df):
    """
    Perform standard population cleaning and dwelling aggregation
    Input df of raw census data, output df

    Removes unnecessary regions
    Tidies region names
    Aggregates dwelling types to joined/detached
    """

    regions_to_exclude = [
        "Area Outside Region",  # ignore the Chathams
        "Total - New Zealand by regional council",
        "Total - New Zealand by health region/health district",
    ]

    dwelling_type_mapping = {
        "Other private dwelling": "Detached",
        "Private dwelling not further defined": "Detached",
        "Separate house": "Detached",
        "Joined dwelling": "Joined",
        "Total - private dwelling type": "Total",
    }

    df = df.copy()

    # Drop unwanted regions
    df = df.loc[~df["Area"].isin(regions_to_exclude)]

    # Remove trailing " Region" from area names
    df["Area"] = df["Area"].str.replace(r"\sRegion$", "", regex=True)

    # aggregate dwelling types
    df["DwellingType"] = df["DwellingType"].map(dwelling_type_mapping)
    group_cols = [col for col in df.columns if col != "Value"]
    df = df.groupby(group_cols, as_index=False)["Value"].sum()

    return df


def get_population_shares(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate overall population shares by (Area, DwellingType).
    """
    required = {"Area", "DwellingType", "Value"}
    missing = required - set(df.columns)
    if missing:
        raise KeyError(f"Missing required column(s): {missing}")

    out = df.copy()

    total = out["Value"].sum()
    # Avoid divide-by-zero; will yield NaN shares if total == 0
    out["ShareOfPopulation"] = (
        out["Value"] / total if total != 0 else out["Value"] * float("nan")
    )

    return out[["Area", "DwellingType", "ShareOfPopulation"]]


def add_islands(df, island_file=ISLAND_FILE):
    """
    Reads in the island concordance file to attach islands to
    an in input df with a "Area" variable
    Renames the island concordance "Region" variable to "Area"
    Returns the df with "Island"
    """

    ri_df = pd.read_csv(island_file)
    ri_df = ri_df.rename(columns={"Region": "Area"})
    df = pd.merge(df, ri_df, on="Area", how="left", validate="many_to_one")

    # Validate merge result
    if "Island" not in df.columns:
        raise KeyError("Merge failed to produce 'Island' column")

    return df


# Space heating model functions ------------------------------------------------------


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


def get_dwelling_heating_data(
    run_tests: bool = RUN_TESTS, dwelling_heating_file=DWELLING_HEATING_FILE
) -> pd.DataFrame:
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
    df = pd.read_csv(dwelling_heating_file)

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
    save_checks(df, "fuel_heating_shares.csv", "Fuel heating shares")

    return df


def add_assumptions(
    df: pd.DataFrame,
    eff_assumptions=CENSUS_EFF_ASSUMPTIONS,
    floor_areas=FLOOR_AREAS,
    hdd_assumptions=HDD_ASSUMPTIONS,
) -> pd.DataFrame:
    """
    Join efficiency, floor‑area, and HDD assumptions into the model data.

    Performs three merges, pulling in:
      1. Heat efficiency assumptions (CENSUS_EFF_ASSUMPTIONS),
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
    # Validate required columns (include HeatingType, since we merge on it)
    required = {"DwellingType", "Area", "HeatingType"}
    missing = required - set(df.columns)
    if missing:
        raise KeyError(f"Missing required column(s): {missing}")

    df = df.copy()

    eff = pd.read_csv(eff_assumptions)
    fa = pd.read_csv(floor_areas)
    hdd = pd.read_csv(hdd_assumptions)[["Region", "HDD"]].rename(
        columns={"Region": "Area"}
    )

    # 1) Efficiencies: explicit many-to-one merge on HeatingType
    df = pd.merge(df, eff, on="HeatingType", how="left", validate="many_to_one")
    # Drop any Note-ish columns without failing if absent
    for col in ["Note", "Note_x", "Note_y"]:
        df = df.drop(columns=[col], errors="ignore")

    # 2) Floor areas: merge on aggregated dwelling labels ('Detached' / 'Joined')
    df = pd.merge(df, fa, on="DwellingType", how="left", validate="many_to_one")
    df = df.drop(columns=["Note"], errors="ignore")

    # 3) HDD:
    df = pd.merge(df, hdd, on="Area", how="left", validate="many_to_one")

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
    df = df.copy()
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

    # First, aggregate up to define the grain
    # In theory there should be only one census year in the data
    # but we will group by this just in case that filter changes
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
    # no longer needed
    df = df.drop(["CensusYear", "ModelHeatFuelInput", "TotalModelFuelInput"], axis=1)

    return df


def get_eeud_space_heating_data(eeud_file=EEUD_FILE, base_year=BASE_YEAR):
    """
    Returns the EEUD residential space heating data
    for the selected base year.
    Aggregates Natural gas and LPG together,
    because we don't have this detail in the heat model
    so these fuels need to be disaggregated later
    """
    # get EEUD data for residential space heating

    eeud = pd.read_csv(eeud_file)
    df = eeud[eeud["Sector"] == "Residential"]
    df = df[df["EndUse"] == "Low Temperature Heat (<100 C), Space Heating"]
    df = df[df["Year"] == base_year]

    # aggregate EEUD LPG/natural gas together
    df.loc[df["Fuel"].isin(["Natural Gas", "LPG"]), "Fuel"] = "Gas/LPG"
    group_cols = [col for col in df.columns if col != "Value"]
    df = df.groupby(group_cols)["Value"].sum().reset_index()

    return df


def check_join_grain(df1, df2, join_vars):
    """
    Assesses how well two dataframes can join together
    Checks the unique combination of each grain
    This is basically like a SQL minus test in both directions

    """

    df1_vars = df1[join_vars].drop_duplicates()
    df2_vars = df2[join_vars].drop_duplicates()

    only_in_df1 = df1_vars.merge(df2_vars, on=join_vars, how="left", indicator=True)
    only_in_df1 = only_in_df1[only_in_df1["_merge"] == "left_only"].drop(
        columns="_merge"
    )

    only_in_df2 = df2_vars.merge(df1_vars, on=join_vars, how="left", indicator=True)
    only_in_df2 = only_in_df2[only_in_df2["_merge"] == "left_only"].drop(
        columns="_merge"
    )

    if not (only_in_df1.empty and only_in_df2.empty):
        logger.warning("Grain mismatch found in join")

        if not only_in_df1.empty:
            print(only_in_df1)

        if not only_in_df2.empty:
            print(only_in_df2)


def apply_sh_model_to_eeud(
    df: pd.DataFrame, eeud_file=EEUD_FILE, base_year=BASE_YEAR
) -> pd.DataFrame:
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
    sh_eeud = get_eeud_space_heating_data(eeud_file=eeud_file, base_year=base_year)

    # assess joins
    join_vars = ["Technology", "Fuel"]

    check_join_grain(df, sh_eeud, join_vars)

    # join input to EEUD
    df = pd.merge(sh_eeud, df, on=join_vars, how="left")

    # modify Values based on shares
    df["Value"] = df["Value"] * df["FuelDemandShare"]

    # no longer needed
    df = df.drop("FuelDemandShare", axis=1)

    return df


def disaggregate_space_heating_demand(
    dwelling_heating_file=DWELLING_HEATING_FILE,
    hdd_assumptions=HDD_ASSUMPTIONS,
    eff_assumptions=CENSUS_EFF_ASSUMPTIONS,
    floor_areas=FLOOR_AREAS,
    eeud_file=EEUD_FILE,
    base_year=BASE_YEAR,
) -> pd.DataFrame:
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
    dwelling_heating_data_tidy = get_dwelling_heating_data(
        dwelling_heating_file=dwelling_heating_file
    )
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
    model_df = add_assumptions(
        model_df,
        eff_assumptions=eff_assumptions,
        floor_areas=floor_areas,
        hdd_assumptions=hdd_assumptions,
    )
    # Build model heat demand
    model_df = build_sh_model(model_df)
    # apply calculated shares to EEUD
    model_df = apply_sh_model_to_eeud(
        model_df, eeud_file=eeud_file, base_year=base_year
    )

    return model_df


def get_tech_island_split(
    model_df, technology, island_file=ISLAND_FILE
) -> pd.DataFrame:
    """
    Compute the North/South Island split for Gas/LPG burners.
    Works on the output of disaggregate_space_heating_demand()

    Steps
    -----
    1. Filter space heating model for Fuel == Natural Gas/LPG.
    4. Add Islands.
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

    df = model_df.copy()
    """
    # 1 Handle different fuel variables, depending on the model input
    # Convert all of these to Gas/LPG if needed and aggregate
    fuel_list = ["Natural Gas", "LPG", "Gas/LPG"]

    # 1. Filter model data to Gas/LPG use, and aggregate (we will redistinguish later)
    df = model_df.loc[model_df["Fuel"].isin(fuel_list)].copy()
    df["Fuel"] = "Gas/LPG"
    cols = [col for col in df.columns if col != "Value"]
    df = df.groupby(cols)["Value"].sum().reset_index()

    techs = df["Technology"].unique().tolist()

    if technology in techs:
        logger.info("%s found in dataframe", blue_text(technology))

    else:
        logger.warning("'%s' not found in input data!", blue_text(technology))
        logger.warning("This pipeline is about to break.")
        logger.warning("Available technologies are: ")
        for tech in techs:
            logger.warning("                 '%s'", tech)

    # 2. Filter model data to input tech if necessary
    df = df[df["Technology"] == technology]

    # 3. Merge in Island labels
    merged = add_islands(df, island_file=island_file)
    # 4. Compute totals and shares
    agg = merged.groupby("Island", as_index=False)["Value"].sum()
    total = agg["Value"].sum()
    agg["Share"] = agg["Value"] / total

    print(f"ISLAND SPLIT: {agg}")
    return agg


def get_lpg_gas_consumption_share_of_tech(
    eeud_file=EEUD_FILE,
    base_year=BASE_YEAR,
    technology="Burner (Direct Heat)",
) -> pd.DataFrame:
    """
    Compute the share of Natural Gas vs LPG for residential burners.

    Steps
    -----
    1. Read the EEUD CSV.
    2. Filter to:
       - Sector == "Residential"
       - EndUse == end_use
       - Year == BASE_YEAR
       - Fuel in Natural Gas, LPG
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
        If any of 'Sector', 'EndUse', 'Year', 'Fuel', 'Technology' or 'Value'
        is missing from the EEUD data.
    FileNotFoundError
        If EEUD_FILE cannot be read.
    """

    # Load EEUD data
    eeud = pd.read_csv(eeud_file)

    # Validate required columns
    required = {"Sector", "EndUse", "Year", "Fuel", "Technology", "Value"}
    missing = required - set(eeud.columns)
    if missing:
        raise KeyError(f"Missing required column(s): {missing}")

    # Filter to residential space heating and target fuels
    filtered = eeud.loc[
        (eeud["Sector"] == "Residential")
        & (eeud["Technology"] == technology)
        & (eeud["Year"] == base_year)
        & (eeud["Fuel"].isin(["Natural Gas", "LPG"]))
    ]

    # Aggregate total Value by Fuel
    agg = filtered.groupby(["Fuel"], as_index=False)["Value"].sum()

    # Compute share
    total = agg["Value"].sum()
    agg["Share"] = agg["Value"] / total

    return agg


def get_ni_lpg_share(fuel_split, island_split):
    """
    Estimate the share of LPG used in the North Island (NI) for direct heat burners.

    Takes the gas burners by fuel (from the EEUD)
    And the gas burners by island (from the space heating model)

    Assumptions:
    - The heating model does not distinguish gas from LPG.
    - All South Island (SI) gas burner demand is LPG.
    - All Natural Gas (NGA) is used in the NI.

    Steps:

    1. Ensure NI burner share can support the natural gas share.
        (if not, the space heat model is wrong)
    2. Calculate remaining LPG available to NI.
    3. Compute and return NI LPG share.
    """

    # 1. Validate feasibility of NI supporting all natural gas demand
    nat_gas_share = fuel_split.loc[fuel_split["Fuel"] == "Natural Gas", "Share"].iloc[0]
    ni_share = island_split.loc[island_split["Island"] == "NI", "Share"].iloc[0]

    if ni_share < nat_gas_share:
        logger.warning(
            "Natural gas share exceeds NI burner share — potential model issue."
        )
    else:
        logger.info("Natural gas share is feasible given NI burner demand.")

    # 2. Calculate total NI LPG use
    si_total_lpg = island_split.loc[island_split["Island"] == "SI", "Value"].iloc[0]
    total_lpg = fuel_split.loc[fuel_split["Fuel"] == "LPG", "Value"].iloc[0]
    ni_total_lpg = total_lpg - si_total_lpg

    # Validate total NI burner demand = NI NGA + NI LPG
    tolerance = 6
    total_nga = fuel_split.loc[fuel_split["Fuel"] == "Natural Gas", "Value"].iloc[0]
    total_ni = island_split.loc[island_split["Island"] == "NI", "Value"].iloc[0]
    error = abs(round((total_nga + ni_total_lpg) - total_ni, tolerance))

    if error != 0:
        logger.warning("Mismatch between NI demand and (NGA + LPG) supply.")
    else:
        logger.info("NI supply balances correctly between NGA and LPG.")

    # 3. Final LPG share for NI
    if total_ni == 0 or np.isclose(total_ni, 0.0):
        raise ZeroDivisionError(
            "NI total burner demand is zero; cannot compute LPG share."
        )
    ni_lpg_share = ni_total_lpg / total_ni
    return ni_lpg_share


def distribute_gas_for_tech(
    df, ni_lpg_share, technology="Burner (Direct Heat)", island_file=ISLAND_FILE
):
    """
    Takes the input space heating model,
    which aggregates gas burners among Gas/LPG
    operates on only 1 tech at a time.

    Uses island definition assumptions to split the Gas/LPG across islands:

    ie: No Natural Gas in the South Island
    """
    # add island tags
    df = add_islands(df, island_file=island_file)

    df_gas_lpg = df[(df["Fuel"] == "Gas/LPG") & (df["Technology"] == technology)]

    # Remove those rows from the main df
    df = df[~((df["Fuel"] == "Gas/LPG") & (df["Technology"] == technology))]

    # add the lpg shares
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


# disaggregate other demand by pop (and redistribute NGA) ------------------------


def get_residential_eeud(eeud_file=EEUD_FILE, base_year=BASE_YEAR):
    """Loads residential EEUD for the base year"""

    df = pd.read_csv(eeud_file)

    df = df[df["Sector"] == "Residential"]
    df = df[df["Year"] == base_year]

    return df


def get_disaggregated_end_use_by_pop(
    eeud, pop_shares, uses, eff_assumptions=EFF_ASSUMPTIONS
):
    """

    For the given end uses, converts consumption to demand via efficiency assumptions
    Then disaggregates demand to island and dwelling type based on population shares
    ensures that the natural gas is distributed among north island regions only
        (based on the region's share of NI demand )
    Calculates all other fuel's share of the original demand (minus natural gas)
    Distributes other fuels among the "Residual" demand for that end use
        (ie: demand unmet by natural gas)
    Converts back to fuel demand using the same efficient


    NOTE: the allocation is slightly complex. This is because we handle multiple natural gas technologies

    The simplest option is to throw an error for this. If the error is ever raised, then you'll need to handle the multiple techs somehow
    Couple of different options, but mostly you'll want to assign the original shares of the ng techs within that end group in the final allocation
    (Otherwise it will give ALL the natural gas to EACH natural gas technology)



    """

    eff = pd.read_csv(eff_assumptions)[["Technology", "Fuel", "EFF"]]

    df = eeud.copy()
    eeud_columns = df.columns.to_list()  # keep original EEUD schema

    # inputs for shares
    group_vars = ["EndUse", "Area", "DwellingType"]

    # filter - only base year residential specific uses
    df = df[df["EndUse"].isin(uses)]

    # Join additional parameters (pop share expansion and efficiencies)

    df = df.merge(eff, how="left", on=["Technology", "Fuel"])
    df = df.merge(pop_shares, how="cross")

    # Guard EFF=0. This means bad input data.

    mask = df["EFF"].isna() | (df["EFF"] == 0)
    if mask.any():
        bad_rows = df.loc[mask, ["Technology", "Fuel"]].drop_duplicates()
        logger.error(
            f"Zero or missing efficiency found for residential technologies!. Please complete the input sheet."
        )
        raise ValueError(
            f"Zero or missing efficiency found for: {bad_rows.to_dict(orient='records')}"
        )

    # Warning early if multiple techs. This case doesn't currently exist but needs robust testing if it does.
    ng = df[df["Fuel"].eq("Natural Gas")]
    viol = ng.groupby(["EndUse", "Area", "DwellingType"])["Technology"].nunique()
    if (viol > 1).any():
        logger.warning("Warning - multiple NG techs discovered")
        logger.warning(
            "This result should be handled, but please test that outputs aren't double-counting!"
        )

    # Step 1: demand by area/dwelling
    df["Demand"] = df["Value"] * df["EFF"]
    df["DemandPerAreaDwelling"] = df["Demand"] * df["ShareOfPopulation"]

    # Step 2: allocate natural gas to NI only, proportional to island pop shares
    df = add_islands(df)  # must create column "Island" with {"NI","SI"}

    df["IslandShareOfPop"] = df.groupby(["EndUse", "Fuel", "Island"])[
        "ShareOfPopulation"
    ].transform("sum")
    df["ShareOfIsland"] = df["ShareOfPopulation"] / df["IslandShareOfPop"]

    df["NaturalGasShare"] = np.where(df["Island"].eq("SI"), 0.0, df["ShareOfIsland"])

    # NG demand only on NG rows
    df["NaturalGasDemand_row"] = np.where(
        df["Fuel"].eq("Natural Gas"),
        df["NaturalGasShare"] * df["Demand"],
        0.0,
    )

    # Aggregate NG demand per (EndUse, Area, DwellingType), then merge back
    ng = (
        df.loc[df["Fuel"].eq("Natural Gas"), group_vars + ["NaturalGasDemand_row"]]
        .groupby(group_vars, as_index=False)["NaturalGasDemand_row"]
        .sum()
        .rename(columns={"NaturalGasDemand_row": "NaturalGasDemand"})
    )
    df = df.merge(ng, on=group_vars, how="left").fillna({"NaturalGasDemand": 0.0})

    # Step 3: residual allocation to non-gas fuels
    df["TotalDemandInArea"] = df.groupby(group_vars)["DemandPerAreaDwelling"].transform(
        "sum"
    )

    df["DemandPerAreaDwellingNoGas"] = np.where(
        df["Fuel"].eq("Natural Gas"), 0.0, df["DemandPerAreaDwelling"]
    )
    df["DemandPerAreaDwellingNoGasTotal"] = df.groupby(group_vars)[
        "DemandPerAreaDwellingNoGas"
    ].transform("sum")

    # Avoid divide by zero
    denom = df["DemandPerAreaDwellingNoGasTotal"].replace(0, np.nan)
    df["ShareOfResidual"] = df["DemandPerAreaDwellingNoGas"] / denom
    df["ShareOfResidual"] = df["ShareOfResidual"].fillna(0.0)

    df["Residual"] = df["TotalDemandInArea"] - df["NaturalGasDemand"]

    # Assign final demand per area/dwelling
    df["DemandIfOtherFuel"] = df["ShareOfResidual"] * df["Residual"]

    # NOTE: we've added functionality to apportion different natural gas techs,
    # because the simplest option will double count natural gas if there are multiple ng techs for a use
    # there actually isn't multiple techs in residential,
    # so this is defensive for if the input data ever gets more detailed

    ng_mask = df["Fuel"].eq("Natural Gas")
    ng = df.loc[
        ng_mask, group_vars + ["DemandPerAreaDwelling", "NaturalGasDemand"]
    ].copy()
    # weights within each group
    denom = (
        ng.groupby(group_vars)["DemandPerAreaDwelling"]
        .transform("sum")
        .replace(0, np.nan)
    )
    ng["w"] = ng["DemandPerAreaDwelling"] / denom

    # assign non-NG rows
    df.loc[~ng_mask, "DemandPerAreaDwelling"] = df.loc[~ng_mask, "DemandIfOtherFuel"]

    # split NG total across NG-tech rows (order-aligned via the slice)
    df.loc[ng_mask, "DemandPerAreaDwelling"] = (
        ng["w"].fillna(0).to_numpy() * ng["NaturalGasDemand"].to_numpy()
    )

    # Convert back to fuel consumption.
    df["Value"] = df["DemandPerAreaDwelling"] / df["EFF"]

    # Save entire (massive) dataframe of intermediate variables to checking output for possible inspections
    save_checks(
        df,
        "full_enduse_method_variables.csv",
        "All enduse disaggregation variables (no space heating)",
    )

    # Return EEUD shape plus geography
    out_cols = eeud_columns + ["Area", "DwellingType", "Island"]
    out = df[out_cols].copy()

    return out


# Checks


def ensure_totals_match(disag_demand, base_year=BASE_YEAR, eeud_file=EEUD_FILE):
    """Get original eeud demand for each tech/sector,
    compare to summed disaggregated demand

    Just ensure that totals match
    Can probably just move this as an automated check to main script

    """
    # GET EEUD
    eeud_res = pd.read_csv(eeud_file)

    eeud_res = eeud_res[eeud_res["Sector"] == "Residential"]
    eeud_res = eeud_res[eeud_res["Year"] == base_year]

    eeud_res = (
        eeud_res.groupby(["Year", "EndUse", "Technology", "Fuel"])["Value"]
        .sum()
        .reset_index()
    )
    eeud_res = eeud_res.rename(columns={"Value": "ORIGINAL"})
    # summarise disaggregated results
    disag_demand = (
        disag_demand.groupby(["Year", "EndUse", "Technology", "Fuel"])["Value"]
        .sum()
        .reset_index()
    )
    disag_demand = disag_demand.rename(columns={"Value": "DISAGGREGATED"})

    # compare
    test = pd.merge(eeud_res, disag_demand, how="left")

    test["DELTA"] = round(abs(test["DISAGGREGATED"] - test["ORIGINAL"]), 6)

    mask = test["DELTA"] != 0
    if mask.any():
        bad_rows = test[mask].drop_duplicates()
        logger.error(
            f"Disaggregated residential demand does not match totals! Please review"
        )
        raise ValueError(
            f"Disaggregation model has warped results for: {bad_rows.to_dict(orient='records')}"
        )


# Execute outputs -------------------------------------------


def get_residential_other_demand():
    """
    Executes all functions required for residential
    demand disaggregated by population and dwelling type

    Saves result to staging area
    """
    pop_dwelling = get_population_data()
    pop_dwelling = clean_population_data(pop_dwelling)
    shares = get_population_shares(pop_dwelling)
    save_checks(shares, "population_shares.csv", "Population shares")

    # get residential eeud
    eeud = get_residential_eeud(eeud_file=EEUD_FILE, base_year=BASE_YEAR)

    # identify all end uses except space heating
    all_uses = eeud["EndUse"].unique().tolist()
    uses = [u for u in all_uses if u != "Low Temperature Heat (<100 C), Space Heating"]
    #     uses = ["Low Temperature Heat (<100 C), Water Heating", "Intermediate Heat (100-300 C), Cooking"]

    df = get_disaggregated_end_use_by_pop(eeud=eeud, pop_shares=shares, uses=uses)

    return df


def get_residential_space_heating_demand():
    # Runs the mode

    model_df = disaggregate_space_heating_demand()
    # distribute the burner gas from model output
    burner_island_split = get_tech_island_split(
        model_df, technology="Burner (Direct Heat)", island_file=ISLAND_FILE
    )
    burner_fuel_split = get_lpg_gas_consumption_share_of_tech(
        eeud_file=EEUD_FILE, technology="Burner (Direct Heat)"
    )

    ni_lpg_share = get_ni_lpg_share(
        fuel_split=burner_fuel_split, island_split=burner_island_split
    )

    res_sh_df = distribute_gas_for_tech(
        model_df,
        ni_lpg_share,
        technology="Burner (Direct Heat)",
        island_file=ISLAND_FILE,
    )

    return res_sh_df


def main():
    """Script entry-point"""
    OUTPUT_LOCATION.mkdir(parents=True, exist_ok=True)
    CHECKS_LOCATION.mkdir(parents=True, exist_ok=True)
    residential_other_demand = get_residential_other_demand()
    residential_sh_demand = get_residential_space_heating_demand()

    residential_demand = pd.concat([residential_other_demand, residential_sh_demand])

    ensure_totals_match(residential_demand)

    save_output(residential_demand, "residential_demand_disaggregated.csv")


# Main safeguard
if __name__ == "__main__":
    main()
