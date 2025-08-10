import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from prepare_times_nz.utilities.filepaths import ASSUMPTIONS, STAGE_1_DATA, STAGE_2_DATA
from prepare_times_nz.utilities.logger_setup import logger

# CONSTANTS -------------------------------------------------------


BASE_YEAR = 2023
# FILEPATHS -------------------------------------------------------

EA_DATA_DIR = STAGE_1_DATA / "electricity_authority"
LOAD_CURVE_ASSUMPTIONS = ASSUMPTIONS / "load_curves"
OUTPUT_LOCATION = STAGE_2_DATA / "settings/load_curves"
CHECKS_LOCATION = OUTPUT_LOCATION / "checks"

# INPUT DATA LOCATIONS -------------------------------------------------------
GXP_SHARES_FILE = LOAD_CURVE_ASSUMPTIONS / "gxp_shares.csv"
GXP_FILE = EA_DATA_DIR / "emi_gxp.parquet"
NODE_CONCORDANCE_FILE = EA_DATA_DIR / "emi_nsp_concordances.csv"


# FUNCTIONS ----------------------------------------------------------------------------


def aggregate_emi_by_timeslice(df):
    """
    Aggregates the EMI data to each hour per POC
    Note that TimeSlices have already been defined in pre-processing
    Based on Timeslice input assumption files
    """

    df["Year"] = df["Trading_Date"].dt.year.astype("int64")
    # aggregate to hourly per POC
    df = (
        df.groupby(
            ["Year", "TimeSlice", "POC", "Trading_Date", "Hour", "Unit_Measure"]
        )["Value"]
        .sum()
        .reset_index()
    )

    # ignore DST - this means the day where the clocks go back is slightly wrong
    # we could build more complex logic here
    # but it's not worth the detail for what we're doing
    df = df[df["Hour"] != 24]

    return df


def add_islands(df, nsp_file=NODE_CONCORDANCE_FILE):
    """
    Expects an input df with a POC Variable
    Then adds the Island from the NSP concordance file
    """

    nsp = pd.read_csv(nsp_file)
    nsp = nsp.rename(columns={"POC": "POCPrefix"})
    nsp = nsp[["POCPrefix", "Island"]]

    df["POCPrefix"] = df["POC"].astype(str).str[:3]
    df = pd.merge(df, nsp, on="POCPrefix", how="left")
    df = df.drop("POCPrefix", axis=1)
    return df


def get_summary_timeslices(df, by_island=True, nsp_file=NODE_CONCORDANCE_FILE):
    """
    Aggregates load data by timeslice and computes total GWh and average load (GW).

    If by_island is True, results are also grouped by island. Returns a DataFrame
    with total energy (GWh), hours in each timeslice, and average load in GW.
    """

    group_vars = ["Year", "TimeSlice", "Trading_Date", "Hour", "Unit_Measure"]
    agg_group_vars = ["Year", "TimeSlice", "Unit_Measure"]

    if by_island:
        # add the island variable to the data, extend our group definitions by island
        df = add_islands(df, nsp_file)
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

    # df["Unit_Measure"] = "GWh"
    # df["Value"] = df["Value"] / 1e6 # GWh conversion

    df = df.groupby(group_vars)["Value"].sum().reset_index()
    df["LoadCurve"] = df["Value"] / df.groupby(agg_group_vars)["Value"].transform("sum")

    # the value is just the sum of the sample POCs so not useful by itself.
    # remove to avoid confusion
    # we only want the curves
    df = df.drop(["Value", "Unit_Measure"], axis=1)

    return df


def get_residential_total_demand():
    """
    Load res elc demand from EEUD
    """

    eeud = pd.read_csv(f"{STAGE_1_DATA}/eeud/eeud.csv")

    eeud_res = eeud[eeud["SectorGroup"] == "Residential"]
    eeud_res = eeud_res[eeud_res["Fuel"] == "Electricity"]
    eeud_res = (
        eeud_res.groupby(["Year", "SectorGroup", "Unit"])["Value"].sum().reset_index()
    )
    # convert TJ to GWh
    TJ_TO_GWH = 1 / 3.6
    eeud_res["Unit"] = "GWh"
    eeud_res["Value"] = eeud_res["Value"] * TJ_TO_GWH

    return eeud_res


def test_average_loads():
    """
    This functions adds as a test
    to ensure our load shares for the base year look sensible
    Both our

    TBD !

    """

    residential_curve = pd.read_csv(OUTPUT_LOCATION / "residential_curves.csv")
    base_year_curve = pd.read_csv(OUTPUT_LOCATION / "base_year_load_curve.csv")
    yrfr = pd.read_csv(OUTPUT_LOCATION / "yrfr.csv")

    # does yrfr add 1?

    should_be_one = round(
        yrfr["YRFR"].sum(), 8
    )  # check this matches/exceeds GAMS/Veda tolerance
    if should_be_one != 1:
        logger.warning("YRFR does not add to 1! TIMES will fail")

    # national curves are the base year curve but sum across islands

    eeud_res = get_residential_total_demand()

    residential_curve = pd.merge(residential_curve, eeud_res)
    residential_curve = pd.merge(residential_curve, yrfr)
    residential_curve["Value"] = (
        residential_curve["LoadCurve"] * residential_curve["Value"]
    )

    residential_curve = residential_curve[["Year", "Unit", "TimeSlice", "Value"]]
    residential_curve["Sector"] = "Residential"

    base_year_curve = base_year_curve.rename(columns={"Unit_Measure": "Unit"})
    base_year_curve = (
        base_year_curve.groupby(["Year", "TimeSlice", "Unit"])["Value"]
        .sum()
        .reset_index()
    )
    base_year_curve["Sector"] = "Total"

    df = pd.concat([base_year_curve, residential_curve])

    # add hours for average load
    df = pd.merge(df, yrfr)
    df["Hours"] = df["YRFR"] * 8760

    df["AverageLoadGW"] = df["Value"] / df["Hours"]

    # Pivot so we have Total and Residential side-by-side per timeslice
    pivot_df = df.pivot(index="TimeSlice", columns="Sector", values="AverageLoadGW")

    # Calculate 'Other' as Total minus Residential
    pivot_df["Other"] = pivot_df["Total"] - pivot_df["Residential"]

    # Ensure the desired order
    order = [
        "FAL-WE-D",
        "FAL-WE-N",
        "FAL-WE-P",
        "FAL-WK-D",
        "FAL-WK-N",
        "FAL-WK-P",
        "SPR-WE-D",
        "SPR-WE-N",
        "SPR-WE-P",
        "SPR-WK-D",
        "SPR-WK-N",
        "SPR-WK-P",
        "SUM-WE-D",
        "SUM-WE-N",
        "SUM-WE-P",
        "SUM-WK-D",
        "SUM-WK-N",
        "SUM-WK-P",
        "WIN-WE-D",
        "WIN-WE-N",
        "WIN-WE-P",
        "WIN-WK-D",
        "WIN-WK-N",
        "WIN-WK-P",
    ]
    pivot_df = pivot_df.reindex(order)

    # Keep only Residential and Other for the stacked chart
    stack_df = pivot_df[["Residential", "Other"]]

    # Plot with nudged labels
    fig, ax = plt.subplots(figsize=(12, 6))
    stack_df.plot(
        kind="bar",
        stacked=True,
        width=0.8,
        color=["#1f77b4", "#ff7f0e"],
        ax=ax,
        fig=fig,
    )

    plt.ylabel("Average Load (GW)")
    plt.title("Average Load per TimeSlice (Residential vs Other)")
    plt.grid(axis="y", linestyle="--", alpha=0.7)
    plt.legend(title="Sector")

    # Nudge x-axis labels right so the END of label aligns with bar center
    ticks = np.arange(len(stack_df.index))
    ax.set_xticks(ticks + 0.05)  # adjust the shift amount as needed
    ax.set_xticklabels(stack_df.index, rotation=45, ha="right")

    plt.tight_layout()
    plt.savefig(f"{CHECKS_LOCATION}/average_load_timeslice.png", dpi=300)

    print(CHECKS_LOCATION)


def estimate_res_real_peak():
    """
    Analysis function. Not part of main workflow
    Intended to assess actual residential peaks by checking the peak of residential POC
    and applying that share of demand to total known res demand
    to estimate residential peak
    gets roughly 3GW in 2023 - seems a little low. To assess further.

    """

    df = pd.read_parquet(GXP_FILE)
    res_pocs = get_residential_pocs(threshold=0.90)

    df = df[df["POC"].isin(res_pocs)]
    df["Year"] = df["Trading_Date"].dt.year
    df = df[df["Year"] == 2023]

    df = df.groupby(["Trading_Date", "Trading_Period"])["Value"].sum().reset_index()
    df = df[df["Value"] != 0]

    df["Share"] = df["Value"] / df["Value"].sum()

    df["Year"] = 2023
    eeud_res = get_residential_total_demand()

    df = df.drop("Value", axis=1)

    df = pd.merge(df, eeud_res)

    df["Unit"] = "GWh"

    df["Value"] = df["Share"] * df["Value"]

    df["Unit"] = "GW"
    df["Value"] = df["Value"] * 2

    df = df.sort_values("Value", ascending=False)

    return df


def main():
    """
    Creates national electricity load curves for each island
    Creates residential load curves
    defines the year fractions for the base year

    Saves all data to staging
    """

    OUTPUT_LOCATION.mkdir(parents=True, exist_ok=True)
    CHECKS_LOCATION.mkdir(parents=True, exist_ok=True)
    raw_emi = pd.read_parquet(GXP_FILE)

    emi_timeslice = aggregate_emi_by_timeslice(raw_emi)
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
