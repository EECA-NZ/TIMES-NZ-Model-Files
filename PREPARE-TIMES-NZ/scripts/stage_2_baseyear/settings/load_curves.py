"""
We have explicitly set our load curves to always peak at 6pm for every season.
This isn't perfect, but is quite close.

This script:

1) Creates base_year load curves using base year GXP data, mapping this to islands.
   These load curves will be applied to the total base year electricity demand for
   every sector.

   (This was the TIMES 2.0 method.)
   We are calibrating our load curves rather than representing each sector.
   I am not sure I like this approach, but oh well.

2) Identifies residential GXPs and uses 2023 residential GXP demand per timeslice.
   This is only for forming COM_FR for residential demand. We do NOT adjust these
   per island. We will maintain these residential shares.

Potential additional features (not yet implemented):

1) Load RBS data to distinguish residential load curves more fully.
   These should be based on the base year, but distinguish commodities per timeslice.

   This would allow for:
     a) Better representation of how reducing space heating demand affects peaks.
     b) Assessment of shape impact when changing demand by commodity
        (e.g. increased cooling).

   Since we don't currently project different residential commodities at different
   rates, b) is currently irrelevant—but a) is useful.

Outputs:

- base_year_load_curves (could also just generate curves by year and filter later)
- load_curves_residential
- yrfr

Potential checking outputs:

- base_year peak (by applying load curves to total demand)—
  this shows the 6GW peak load we're representing.
"""

# LIBRARIES -------------------------------------------------------

import pandas as pd
from prepare_times_nz.filepaths import ASSUMPTIONS, STAGE_1_DATA, STAGE_2_DATA
from prepare_times_nz.logger_setup import logger

# CONSTANTS -------------------------------------------------------


BASE_YEAR = 2023
# FILEPATHS -------------------------------------------------------

EA_DATA_DIR = STAGE_1_DATA / "electricity_authority"
LOAD_CURVE_ASSUMPTIONS = ASSUMPTIONS / "load_curves"
OUTPUT_LOCATION = STAGE_2_DATA / "residential/load_curves"
CHECKS_LOCATION = OUTPUT_LOCATION / "checks"

# INPUT DATA LOCATIONS -------------------------------------------------------
GXP_SHARES_FILE = LOAD_CURVE_ASSUMPTIONS / "gxp_shares.csv"
GXP_FILE = EA_DATA_DIR / "emi_gxp.parquet"
NODE_CONCORDANCE_FILE = EA_DATA_DIR / "emi_nsp_concordances.csv"


# FUNCTIONS ----------------------------------------------------------------------------


def aggregate_emi_by_timeslice():
    """
    Aggregates the EMI data to each hour per POC
    Note that TimeSlices have already been defined in pre-processing
    Based on Timeslice input assumption files
    """

    df = pd.read_parquet(GXP_FILE)
    df["Year"] = df["Trading_Date"].dt.year
    # aggregate to hourly per POC
    df = (
        df.groupby(
            ["Year", "TimeSlice", "POC", "Trading_Date", "Hour", "Unit_Measure"]
        )["Value"]
        .sum()
        .reset_index()
    )

    # ignore DST
    df = df[df["Hour"] != 24]

    return df


def add_islands(df):
    """
    Expects an input df with a POC Variable
    Then adds the Island from the NSP concordance file
    """

    nsp = pd.read_csv(NODE_CONCORDANCE_FILE)
    nsp = nsp.rename(columns={"POC": "POCPrefix"})
    nsp = nsp[["POCPrefix", "Island"]]

    df["POCPrefix"] = df["POC"].astype(str).str[:3]
    df = pd.merge(df, nsp, on="POCPrefix", how="left")
    df = df.drop("POCPrefix", axis=1)
    return df


def get_summary_timeslices(df, by_island=True):
    """
    Aggregates load data by timeslice and computes total GWh and average load (GW).

    If by_island is True, results are also grouped by island. Returns a DataFrame
    with total energy (GWh), hours in each timeslice, and average load in GW.
    """

    group_vars = ["Year", "TimeSlice", "Trading_Date", "Hour", "Unit_Measure"]
    agg_group_vars = ["Year", "TimeSlice", "Unit_Measure"]

    if by_island:
        # add the island variable to the data, extend our group definitions by island
        df = add_islands(df)
        group_vars += ["Island"]
        agg_group_vars += ["Island"]

    df = df.groupby(group_vars)["Value"].sum().reset_index()

    # now hour is the grain we can get hours per slice to test:
    df = (
        df.groupby(agg_group_vars)
        .agg(Value=("Value", "sum"), HoursInSlice=("Value", "size"))
        .reset_index()
    )

    # average loads
    df["Value"] = df["Value"] / 1e6
    df["Unit_Measure"] = "GWh"
    df["AverageLoadGW"] = df["Value"] / df["HoursInSlice"]

    return df


def get_base_year_load_curves(df):
    """
    Filter input data to base year, then create the curves based on demand per slice
    """

    df = df[df["Year"] == BASE_YEAR].copy()

    df["LoadCurve"] = df["Value"] / df["Value"].sum()

    return df


def get_yrfr(df):
    """
    Takes the base year load curves df
    calculates the hours per timeslice and therefore the yrfr
    Ensures the total hours add to 8760 (or 8784)
    This means we've got our grain right

    Repeating some processing here unfortunately
    """

    df = get_base_year_load_curves(df)
    # calculate implied yrfr (should match the ones we already have)
    df["HoursInYear"] = df.groupby("Year")["HoursInSlice"].transform("sum")

    df["YRFR"] = df["HoursInSlice"] / df["HoursInYear"]
    # just make sure we haven't done anything silly
    hours_in_year = df["HoursInYear"].iloc[0]

    if hours_in_year != 8760:
        if hours_in_year == 8784:
            logger.warning(
                "The year has %s hours. Is the base year a leap year?", hours_in_year
            )
        else:
            logger.warning(
                "The year has an incorrect number of hours (%s). Please review",
                hours_in_year,
            )

    else:
        logger.info("The year has %s hours", hours_in_year)

    df = df[["TimeSlice", "YRFR"]].copy()

    return df


def get_residential_pocs(threshold=0.9):
    """
    Reads the raw data on ICP shares of each gxp.

    Returns a list of GXPs with residential shares above threshold

    Expects specific variable names in the GXP_SHARES_FILE:
        "Connection point"
        "Residential" (the share of residential ICPs at this POC)

    """

    df = pd.read_csv(GXP_SHARES_FILE)
    df = df[["Connection point", "Residential"]]
    df = df[df["Residential"] >= threshold]

    # we want to remove the prefixes and take only the first 7 chars of each code
    # this aligns with our gxp demand data

    df["Connection point"] = df["Connection point"].astype(str).str[:7]

    return df["Connection point"].tolist()


def get_residential_curves(df, with_islands=False):
    """

    Filter the main dataset by the residential pocs

    Also filter for all complete years of data!

    Create timeslice curves

    """
    residential_pocs = get_residential_pocs()
    df = df[df["Year"] == BASE_YEAR]
    df = df[df["POC"].isin(residential_pocs)]

    # add islands
    #
    group_vars = ["Year", "TimeSlice", "Unit_Measure"]
    agg_group_vars = ["Year", "Unit_Measure"]

    if with_islands:
        group_vars = group_vars + ["Island"]
        agg_group_vars = ["Year", "Unit_Measure"]
        df = add_islands(df)

    df = df.groupby(group_vars)["Value"].sum().reset_index()
    df["LoadCurve"] = df["Value"] / df.groupby(agg_group_vars)["Value"].transform("sum")

    return df


def test_average_loads():
    """
    This functions adds as a test
    to ensure our load shares for the base year look sensible
    Both our

    TBD !

    """


def main():
    """
    Creates national electricity load curves for each island
    Creates residential load curves
    defines the year fractions for the base year

    Saves all data to staging
    """
    OUTPUT_LOCATION.mkdir(parents=True, exist_ok=True)
    CHECKS_LOCATION.mkdir(parents=True, exist_ok=True)

    emi_timeslice = aggregate_emi_by_timeslice()
    timeslice_by_island = get_summary_timeslices(emi_timeslice, by_island=True)
    national_timeslices = get_summary_timeslices(emi_timeslice, by_island=False)

    # base year load curves (all sectors, per island)

    base_year_load_curve = get_base_year_load_curves(timeslice_by_island)
    base_year_load_curve.to_csv(
        OUTPUT_LOCATION / "base_year_load_curve.csv", index=False
    )

    # # calculate year fractions
    yrfr = get_yrfr(national_timeslices)
    yrfr.to_csv(OUTPUT_LOCATION / "yrfr.csv", index=False)

    residential_curves = get_residential_curves(emi_timeslice)
    residential_curves.to_csv(OUTPUT_LOCATION / "residential_curves.csv", index=False)


if __name__ == "__main__":
    main()
