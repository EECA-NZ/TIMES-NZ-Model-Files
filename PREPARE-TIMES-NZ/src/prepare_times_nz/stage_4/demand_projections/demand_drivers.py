"""
Loads growth indices and maps these to the correct names

# Industry growth indices
# Population
# GDP

# Other TBD (likely MOT VFEM, maybe some land use projections, that sort of thing)

# Everything is compiled into a single table per scenario
"""

import pandas as pd
from prepare_times_nz.stage_0.stage_0_settings import BASE_YEAR
from prepare_times_nz.stage_3.demand_projections.population_projections import (
    get_national_population_growth_index,
)
from prepare_times_nz.utilities.data_in_out import _save_data
from prepare_times_nz.utilities.filepaths import (
    CONCORDANCES,
    DATA_RAW,
    STAGE_3_DATA,
    STAGE_4_DATA,
)
from prepare_times_nz.utilities.logger_setup import logger

# CONSTANTS -----------------------------------------------------------

DEMAND_PROJECTIONS = STAGE_3_DATA / "demand_projections"
OUTPUT_LOCATION = STAGE_4_DATA / "scen_demand"
MBIE_RAW = DATA_RAW / "external_data/mbie"

EDGS = MBIE_RAW / "electricity-demand-generation-scenarios-2024-assumptions.xlsx"

# FUNCTIONS ----------------------------------------


def get_industry_indexes():
    """
    Veda-ready industry demand indices
    We build codenames for these: note that these
    should also be added to the config inputs for
        the driver allocation table

    We build everything up together in a single
        table before splitting by scenarios
    """

    df = pd.read_csv(DEMAND_PROJECTIONS / "industrial_demand_index.csv")

    conc = pd.read_csv(CONCORDANCES / "industry/sector_codes.csv")

    df = df.merge(conc, on="Sector", how="left")

    # in theory, it's not possible to mismatch here. but we check anyway

    test = df[df["Sector_TIMES"].isna()]

    if len(test) > 0:
        sectors = test["Sector"].unique().tolist()
        logger.warning("ALERT: FAILED SECTOR JOIN")
        logger.warning("This shouldn't be possible so something has gone wrong")
        logger.warning("Please review the following sectors:")
        for sector in sectors:
            logger.warning("           %s", sector)

    # create demand growth code for each sector
    df["Driver"] = "IND_" + df["Sector_TIMES"] + "_DMD"
    df["Region"] = "AllRegions"

    df = df[["Region", "Driver", "Scenario", "Year", "Index"]]

    return df


def get_population_index():
    """
    To generate population growth indices
    We use a function previously built
    And assign SNZ scenarios to our scenarios
    As a reminder, the possibilities are:

     - '5th percentile'
     - '10th percentile'
     - '25th percentile'
     - '50th percentile (median)'
     - '75th percentile'
     - '90th percentile'
     - '95th percentile'

    With the demand projections a little easier now,
      we could probably upgrade to subnational projections later

    Currently we just use median for both
    """

    # define traditional
    trad_index = get_national_population_growth_index("50th percentile (median)")
    trad_index["Scenario"] = "Traditional"

    # define transformation
    trans_index = get_national_population_growth_index("50th percentile (median)")
    trans_index["Scenario"] = "Transformation"

    # combine
    df = pd.concat([trad_index, trans_index])

    # shape for veda (rename and select)

    df["Region"] = "AllRegions"  # national pop means same growth on both islands
    df["Driver"] = "POP"

    df = df[["Region", "Driver", "Scenario", "Year", "Index"]]
    return df


def get_gdp_index():
    """
    Standard GDP indices for each scenario
    Data pulled from EDGS and based to BASE_YEAR
    """

    df = pd.read_excel(EDGS, sheet_name="GDP")

    df = df.rename(columns={"Scenario": "MBIEScenario", "TimePeriod": "Year"})

    # only reference for our purposes
    # df = df[df["Scenario"] == "Reference"]

    # index to base year
    df = df[df["Year"] >= BASE_YEAR]
    base_value = df[df["Year"] == BASE_YEAR]["Value"].iloc[0]
    df["Index"] = df["Value"] / base_value

    # expand by our scenarios
    scenario_map = pd.DataFrame(
        {
            "Scenario": ["Traditional", "Transformation"],
            # Select which MBIE scenario we are using for ours here
            "MBIEScenario": ["Reference", "Reference"],
        }
    )
    # arrange to our scens
    df = df.merge(scenario_map, on="MBIEScenario", how="left")
    df = df[~df["Scenario"].isna()]

    # select/rename

    df["Region"] = "AllRegions"
    df["Driver"] = "GDP"

    df = df[["Region", "Driver", "Scenario", "Year", "Index"]]

    return df


def get_all_demand_indices():
    """
    We want every possible index in the same table
    grouped by scenario

    This combines GDP, POP, our industry demand scenarios
    and potentially others later into one category
    """

    ind = get_industry_indexes()
    pop = get_population_index()
    gdp = get_gdp_index()

    df = pd.concat([ind, gdp, pop])

    return df


def make_demand_drivers(df, scenario):
    """
    Filters the drivers to a scenario,
    Reshapes for Veda,
    and saves a scenario file for ingestion
    """

    # filter to scenario
    df = df[df["Scenario"] == scenario]
    # remove scenario col
    df = df.drop("Scenario", axis=1)

    # pivot out. First do this weird thing to the year vars
    df["Year"] = r"\~" + df["Year"].astype(str)
    # pivot
    df = df.pivot(
        index=["Region", "Driver"], columns="Year", values="Index"
    ).reset_index()
    # forward fill columns, just so everything is covered
    df = df.ffill(axis=1)

    # expand regions

    df_all_regions = df[df["Region"] == "AllRegions"]
    df_region_detail = df[df["Region"] != "AllRegions"]
    # need to make these explicit
    df_all_regions_explicit = pd.concat(
        [
            df_all_regions.assign(Region="NI"),
            df_all_regions.assign(Region="SI"),
        ]
    ).reset_index(drop=True)

    df_out = pd.concat(
        [
            # join back any indices with specific region detail already
            df_all_regions_explicit,
            df_region_detail,
        ]
    ).reset_index(drop=True)

    # save

    _save_data(
        df_out,
        f"demand_drivers_{scenario}.csv",
        f"Demand Drivers ({scenario})",
        filepath=OUTPUT_LOCATION,
    )

    return df


def main():
    """Script entrypoint"""

    indices = get_all_demand_indices()

    make_demand_drivers(indices, "Traditional")
    make_demand_drivers(indices, "Transformation")


if __name__ == "__main__":

    main()
