"""
This module builds a user constraint to ban coal demand
for specific end uses by 2037

It compiles the required uses and inputs based on end use categories

Saves a single veda file to ingest as a UC
"""

import pandas as pd
from prepare_times_nz.utilities.data_in_out import _save_data
from prepare_times_nz.utilities.filepaths import STAGE_2_DATA, STAGE_4_DATA

# CONSTANTS

# data locations
com_demand = pd.read_csv(STAGE_2_DATA / "commercial/baseyear_commercial_demand.csv")
res_demand = pd.read_csv(STAGE_2_DATA / "residential/baseyear_residential_demand.csv")
ind_demand = pd.read_csv(STAGE_2_DATA / "industry/baseyear_industry_demand.csv")
ag_demand = pd.read_csv(
    STAGE_2_DATA / "ag_forest_fish/baseyear_ag_forest_fish_demand.csv"
)

# output locations
OUTPUT_LOCATION = STAGE_4_DATA / "scen_coal_ban"


# FUNCTIONS


def get_commodity_list(sector, end_uses):
    """
    Docstring for get_commodity_list

    :param sector: Description
    """
    filepath = STAGE_2_DATA / f"{sector}/baseyear_{sector}_demand.csv"
    df = pd.read_csv(filepath)

    # just want in, out, and end use
    df = df[["CommodityIn", "CommodityOut", "EndUse"]].drop_duplicates()

    # filter only our specified uses to ban
    df = df[df["EndUse"].isin(end_uses)]
    # get the coal use (to specify the input commodity to ban )
    df = df[df["CommodityIn"].str.contains("COA")]

    # now just need input and output commodities

    df = df[["CommodityIn", "CommodityOut"]].drop_duplicates()

    return df


def get_all_commodities_to_ban():
    """
    Based on specific end uses, gets all demand commodities that use these
    And could use coal

    """
    end_uses = [
        "Intermediate Heat (100-300 C), Process Requirements",
        "Low Temperature Heat (<100 C), Process Requirements",
        "Low Temperature Heat (<100 C), Space Heating",
        "Low Temperature Heat (<100 C), Water Heating",
    ]
    # combine all sectors use of coal for these uses
    df = pd.concat(
        [
            get_commodity_list("commercial", end_uses),
            get_commodity_list("ag_forest_fish", end_uses),
            get_commodity_list("residential", end_uses),
            get_commodity_list("industry", end_uses),
        ]
    )

    return df


def create_ban_veda(df):
    """
    Compiles all input coal commodities and relevant outputs

    Sets demand 0 by 2037


    """
    # input params
    act_2037 = 0

    # inverting inupts for the UC.
    coa_2037 = (1 - act_2037) * -1
    other_2037 = act_2037

    # veda naming conventions from now on
    df = df.rename(columns={"CommodityIn": "PSet_CI", "CommodityOut": "PSet_CO"})

    # Standard parameters
    df["UC_N"] = "COAL-BAN-" + df["PSet_CO"]
    df["Year"] = "2025"
    df["LimType"] = "LO"
    df["UC_RHST"] = "0"
    df["UC_RHST~0"] = "5"

    # setup inverse version to add (limit for non-coal)
    df_inverse = df.copy()
    df_inverse["PSet_CI"] = "-" + df_inverse["PSet_CI"]

    # attach activity bounds
    df["UC_ACT~2037"] = coa_2037
    df_inverse["UC_ACT~2037"] = other_2037

    # combine data and sort
    df = pd.concat([df, df_inverse])
    df = df.sort_values(["UC_N", "PSet_CI"])

    return df


def main():
    """
    Entry point

    """
    df = get_all_commodities_to_ban()
    df = create_ban_veda(df)
    _save_data(df, "coal_ban_process_heat.csv", "NDGHG coal ban", OUTPUT_LOCATION)


if __name__ == "__main__":
    main()
