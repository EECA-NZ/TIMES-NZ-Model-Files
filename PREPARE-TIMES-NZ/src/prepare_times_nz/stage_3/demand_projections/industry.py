"""
This module converts input demand projection assumptions
 and compiles indices for all commodities and scenarios

A separate stage 4 module can extract these
 into the relevant demand scenario files

This currently only covers industry demand!
Other sectors need to be added

"""

import numpy as np
import pandas as pd
from prepare_times_nz.stage_0.stage_0_settings import BASE_YEAR
from prepare_times_nz.utilities.data_in_out import _save_data
from prepare_times_nz.utilities.filepaths import ASSUMPTIONS, STAGE_2_DATA, STAGE_3_DATA

# CONSTANTS
# file paths
PROJECTIONS_ASSUMPTIONS = ASSUMPTIONS / "demand_projections"
OUTPUT = STAGE_3_DATA / "demand_projections"
OUTPUT_CHECKS = OUTPUT / "checks"
# end year setting
END_YEAR = 2050


# HELPERS
def save_ind_proj_data(df, name, label):
    """save data wrapper"""
    label = "Saving industrial demand projections (" + label + ")"
    _save_data(df, name, label, filepath=OUTPUT)


def save_ind_proj_check(df, name, label):
    """save checking data wrapper"""
    label = "Saving industrial demand checks (" + label + ")"
    _save_data(df, name, label, filepath=OUTPUT_CHECKS)


def expand_years(df, base_year=BASE_YEAR, end_year=END_YEAR):
    """
    Adds a full list of years to a dataframe,
    expanding according to the base year and an end year
    Assumes no "Year" variable in original dataframe.
    Peforms full expansion cross join

    Includes a variable "t" which indexes each year
    (starting from 0 as base year)
    """

    years_df = pd.DataFrame({"Year": range(base_year, end_year + 1)})
    years_df["t"] = years_df["Year"] - base_year
    df = df.merge(years_df, how="cross")

    return df


# FUNCTIONS


def get_industrial_growth_indices(transition_period):
    """
    Creates indices for all sectors labelled in the input assumptions
    Where each sector has growth rates specified for "Traditional" and "Transformation"
    Uses optional transition period for Transformation growth rates,
    which blends the growth rates together for the first X years
    This just smooths things out a little bit
    """
    df = pd.read_csv(PROJECTIONS_ASSUMPTIONS / "industry_demand_projections.csv")

    df = df[df["Method"] == "Assumption"]
    df = df[df["SectorGroup"] == "Industry"]

    # define group variables
    # should define the grain
    # currently, scenario isn't included in the grain
    # because "transformation" and "traditional" are separate columns
    # so if we wanted to expand the method we'd need to change this
    group_vars = ["SectorGroup", "Sector"]

    # expand years
    df = expand_years(df)

    # i dont love how this approach isn't very scalable to diff scenarios
    # but maybe it is fit for purpose
    df["delta"] = df["Traditional"] - df["Transformation"]

    # create indices for the vars with constant growth rates (simple)
    df["Traditional_Index"] = 1 * ((1 + df["Traditional"]) ** df["t"])
    df["Transformation_Index"] = 1 * ((1 + df["Transformation"]) ** df["t"])
    df = df.sort_values(group_vars + ["Year"])

    if transition_period:
        # Transition the transformation curves if transition period provided
        df["sigma"] = (df["delta"] / transition_period) * df["t"]
        # shifting (transitional) growth rates
        df["Transformation_Transition"] = np.where(
            df["t"] <= transition_period,
            df["Traditional"] - df["sigma"],
            df["Transformation"],
        )
        df["Transformation_Index"] = (
            (1 + df["Transformation_Transition"])
            .groupby([df[c] for c in group_vars])
            .cumprod()
            # base year 1 (fill value on nan, as this is the base year)
            # need to repeat group for this operation
            .groupby([df[c] for c in group_vars])
            .shift(1, fill_value=1.0)
        )

    # we just need the group, year, and each index
    # pivot on selected indices as variables
    indices = [
        "Traditional_Index",
        "Transformation_Index",
    ]
    index_vars = ["Sector", "Year"]
    df = df[index_vars + indices]
    df = df.melt(
        value_vars=indices, id_vars=index_vars, value_name="Index", var_name="Scenario"
    )

    # tidy the scenario names now
    df["Scenario"] = df["Scenario"].str.removesuffix("_Index")
    return df


def get_industry_baseyear_demand(var):
    """
    We want to pull base year commodity outputs by sector
    Get total base year service demand and energy demand
    Include sector, tech, and enduse labels
    Note that industrial commodities are also often keyed by tech
    (boiler PH != furnace PH)
    So we need each of these to identify all commodities

    variable must be one of InputEnergy, OutputEnergy
    """
    if var not in ["OutputEnergy", "InputEnergy"]:
        raise ValueError(
            f"Invalid variable '{var}'. Must be 'InputEnergy' or 'OutputEnergy'."
        )

    df = pd.read_csv(STAGE_2_DATA / "industry/baseyear_industry_demand.csv")
    df = df[df["Variable"] == var]
    df = (
        df.groupby(
            [
                "Sector",
                "CommodityOut",
                "Region",
                "Technology",
                "EndUse",
                "Variable",
                "Unit",
            ]
        )["Value"]
        .sum()
        .reset_index()
    )
    return df


def get_new_industries_demand(ni_share=0.3):
    """
    Read assumptions for new industries demand
    """

    df = pd.read_csv(PROJECTIONS_ASSUMPTIONS / "industry_demand_projections.csv")

    df = df[df["Method"] == "New Industries"]
    df = df[df["SectorGroup"] == "Industry"]

    # only relevant
    df = df[["Sector", "Traditional", "Transformation"]]
    # melt
    df = df.melt(
        id_vars=["Sector"],
        value_vars=["Traditional", "Transformation"],
        value_name="Value",
        var_name="Scenario",
    )
    # convert PJ
    df["Value"] = df["Value"] * 0.0036
    # expand years
    df = expand_years(df)
    # linear extension of initial input assumption
    df["Value"] = df["Value"] * df["t"]

    # if 0, not needed for model. best to remove to keep clean
    df = df[df["Value"] > 0]

    key_vars = ["Sector", "Scenario", "Year"]

    #
    df = df[key_vars + ["Value"]]

    # island splits
    df["NI"] = df["Value"] * ni_share
    df["SI"] = df["Value"] * (1 - ni_share)
    df = df.drop("Value", axis=1)
    df = df.melt(
        id_vars=key_vars, value_vars=["NI", "SI"], var_name="Region", value_name="Value"
    )

    # add labels
    print(df)
    return df


def get_energy_demand_projections(energy_type, ts=5, new_industries=False):
    """
    Combine base year demand (input or output) and growth indices
    Create forward projections based on these
    Note that Output energy is required for the model
    InputEnergy is sometimes useful for communication purposes
    """

    index = get_industrial_growth_indices(ts)
    base_year = get_industry_baseyear_demand(energy_type)
    df = base_year.merge(index, on="Sector", how="left")
    df["Value"] = df["Value"] * df["Index"]

    if new_industries:
        # add new tech commodity. We might need to adjust this later.
        # no point doing this without the subres, so ignored by default
        newtechs = get_new_industries_demand()

        df = pd.concat([df, newtechs])
        # just fill these in for now
        df["Variable"] = energy_type
        df["Unit"] = "PJ"
        for col in ["CommodityOut", "Technology", "EndUse"]:
            # overwrite these with "New Industries" for now
            df[col] = np.where(
                df["Sector"] == "New Industries", "New Industries", df[col]
            )
    return df


def main():
    """Script entrypoint"""
    df_input_energy = get_energy_demand_projections("InputEnergy")
    df_output_energy = get_energy_demand_projections("OutputEnergy")
    save_ind_proj_check(df_input_energy, "industrial_input.csv", "Input energy")
    save_ind_proj_check(df_output_energy, "industrial_output.csv", "Output energy")

    # the above is extra detail for reporting. The model just needs indices:

    df_index = get_industrial_growth_indices(5)
    save_ind_proj_data(
        df_index, "industrial_demand_index.csv", "Industrial demand index"
    )


if __name__ == "__main__":
    main()
