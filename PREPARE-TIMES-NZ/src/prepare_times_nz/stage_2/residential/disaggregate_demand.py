"""
Other residential non space-heating demand is disaggregated by
population, and growth is keyed to population

Population data is from census 2023
The population data is disaggregated by dwelling type from census.
This means it's incomplete (not everyone answered dwelling type)
So we should only use the shares, not treat these as regional ERP

"""

import numpy as np
import pandas as pd
from prepare_times_nz.stage_2.residential.common import (
    BASE_YEAR,
    PREPRO_DF_NAME_STEP1,
    PREPRO_DF_NAME_STEP2,
    PREPROCESSING_DIR,
    RESIDENTIAL_ASSUMPTIONS,
    add_islands,
    get_population_shares,
    save_checks,
    save_preprocessing,
)
from prepare_times_nz.utilities.filepaths import STAGE_1_DATA
from prepare_times_nz.utilities.logger_setup import logger

# Data locations -----------------------------

EEUD_FILE = STAGE_1_DATA / "eeud/eeud.csv"
DWELLING_HEATING_FILE = STAGE_1_DATA / "statsnz/dwelling_heating.csv"
POP_DWELLING = STAGE_1_DATA / "statsnz/population_by_dwelling.csv"

# Assumptions --------------------------------------------

HDD_ASSUMPTIONS = RESIDENTIAL_ASSUMPTIONS / "regional_hdd_assumptions.csv"
EFF_ASSUMPTIONS = RESIDENTIAL_ASSUMPTIONS / "eff_by_tech_and_fuel.csv"
CENSUS_EFF_ASSUMPTIONS = RESIDENTIAL_ASSUMPTIONS / "eff_for_census_heating_types.csv"
FLOOR_AREAS = RESIDENTIAL_ASSUMPTIONS / "floor_area_per_dwelling.csv"

# disaggregate other demand by pop (and redistribute NGA) ------------------------


def get_residential_eeud(eeud_file=EEUD_FILE, base_year=BASE_YEAR):
    """Loads residential EEUD for the base year"""

    df = pd.read_csv(eeud_file)

    df = df[df["Sector"] == "Residential"]
    df = df[df["Year"] == base_year]

    return df


# It would be ideal to break this function up a bit
# pylint: disable = too-many-locals
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
    Converts back to fuel demand using the same efficiency rating


    NOTE: the allocation is slightly complex.

    This is because we handle multiple natural gas technologies.
    Currently, there is only one natural gas tech per end use.
    If there are more, then a naive implementation of the current method
        will double count

    We have therefore added a way of apportioning these,
        which is very defensive
        (covering an edge case that doesn't exist yet)

    If it comes up, the script flags a warning to check the outputs of these
    If anything goes wrong and stuff gets double-counted, the final check will fail


    """

    eff = pd.read_csv(eff_assumptions)[["Technology", "Fuel", "Efficiency"]]

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

    mask = df["Efficiency"].isna() | (df["Efficiency"] == 0)
    if mask.any():
        bad_rows = df.loc[mask, ["Technology", "Fuel"]].drop_duplicates()
        logger.error("Zero or missing efficiency found for residential technologies!")
        logger.error("Please complete the input sheet.")

        raise ValueError(
            f"Zero or missing efficiency found for: {bad_rows.to_dict(orient='records')}"
        )

    # Warning early if multiple techs.
    # This case doesn't currently exist but needs robust testing if it does.
    ng = df[df["Fuel"].eq("Natural Gas")]
    viol = ng.groupby(["EndUse", "Area", "DwellingType"])["Technology"].nunique()
    if (viol > 1).any():
        logger.warning("Warning - multiple NG techs discovered")
        logger.warning(
            "This result should be handled, but please test that outputs aren't double-counting!"
        )

    # Step 1: demand by area/dwelling
    df["Demand"] = df["Value"] * df["Efficiency"]
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
    df["Value"] = df["DemandPerAreaDwelling"] / df["Efficiency"]

    # Save entire (massive) dataframe of intermediate variables to checking output
    # this just allows extra inspection if desired
    save_checks(
        df,
        "full_enduse_method_variables.csv",
        "All enduse disaggregation variables (no space heating)",
    )

    # Return EEUD shape plus geography
    out_cols = eeud_columns + ["Area", "DwellingType", "Island"]
    out = df[out_cols].copy()

    return out


def get_residential_other_demand():
    """
    Executes all functions required for residential
    demand disaggregated by population and dwelling type

    Saves result to staging area
    """

    shares = get_population_shares()
    save_checks(shares, "population_shares.csv", "Population shares")

    # get residential eeud
    eeud = get_residential_eeud(eeud_file=EEUD_FILE, base_year=BASE_YEAR)

    # identify all end uses except space heating
    all_uses = eeud["EndUse"].unique().tolist()
    uses = [u for u in all_uses if u != "Low Temperature Heat (<100 C), Space Heating"]

    df = get_disaggregated_end_use_by_pop(eeud=eeud, pop_shares=shares, uses=uses)

    return df


def aggregate_regions_to_islands(df):
    """
    "Area" includes region, but TIMES just needs islands.
    The data already has an "Island" variable so this function
    just aggregates everything out by removing "Area"
    """
    group_cols = [col for col in df.columns if col not in ["Area", "Value"]]
    df = df.groupby(group_cols)["Value"].sum().reset_index()
    return df


# Execute outputs -------------------------------------------


def main():
    """Script entry-point"""
    # calculate disaggregated other demand
    residential_other_demand = get_residential_other_demand()
    # combine with space heating from preprocessing step1
    sh_df = pd.read_csv(PREPROCESSING_DIR / PREPRO_DF_NAME_STEP1)
    df_region = pd.concat([sh_df, residential_other_demand])

    df_island = aggregate_regions_to_islands(df_region)

    save_checks(
        df_region, "residential_demand_per_region.csv", "residential demand per region"
    )
    save_preprocessing(
        df_island,
        PREPRO_DF_NAME_STEP2,
        "disaggregated residential demand",
    )


# Main safeguard
if __name__ == "__main__":
    main()
