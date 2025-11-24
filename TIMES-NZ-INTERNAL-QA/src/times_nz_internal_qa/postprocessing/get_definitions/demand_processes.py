"""

Identify and map all demand processes

This is done by taking all the input data from data_intermediate
in PREPARE-TIMES-NZ, where everything is already categorised

(ie Processes aligned with EEUD-style defintions)

The current exception is Transport, which is not aligned in the same way as the others

Rather than refactoring that in PREPARE-TIMES-NZ (which would be ideal, longterm)

We patch that now with a few additional concordance maps in
    data_raw/concordances/transport

"""

# get data

import numpy as np
import pandas as pd
from times_nz_internal_qa.utilities.filepaths import (
    COMMODITY_CONCORDANCES,
    CONCORDANCE_PATCHES,
    PREP_STAGE_2,
    PREP_STAGE_4,
    PROCESS_CONCORDANCES,
)

TRANSPORT_CONCORDANCES = CONCORDANCE_PATCHES / "transport"
COMMERCIAL_CONCORDANCES = CONCORDANCE_PATCHES / "commercial"
AGRICULTURE_CONCORDANCES = CONCORDANCE_PATCHES / "agriculture"

# we basically want to form category files for all our attributes, processes, and commodities

# i want to break this down by process category. Unfortunately these aren't specified in the vd

# It would be best to get these

demand_process_categories = [
    "ProcessGroup",
    "Process",
    "CommodityOut",
    "SectorGroup",
    "Sector",
    "EnduseGroup",
    "EndUse",
    "TechnologyGroup",
    "Technology",
]


def get_industrial_demand_processes():
    """
    Industrial process mapping extracted from prep module staging data.
    Takes base year and new techs
    """

    # Base year

    df = pd.read_csv(PREP_STAGE_2 / "industry/baseyear_industry_demand.csv")
    # patch
    df["Process"] = np.where(
        df["Process"] == "UREA-NGA-REFRM-PH_HIGH",
        "UREA-NGA-BOILR-PH_HIGH",
        df["Process"],
    )
    df["Process"] = np.where(
        df["Process"] == "METH-NGA-REFRM-PH_HIGH",
        "METH-NGA-BOILR-PH_HIGH",
        df["Process"],
    )
    df["SectorGroup"] = "Industry"
    df["ProcessGroup"] = "Demand"
    df = df[demand_process_categories].drop_duplicates()

    # new techs
    df_new = pd.read_csv(
        PREP_STAGE_4 / "subres_ind/future_industry_process_definitions.csv"
    )
    df_new["SectorGroup"] = "Industry"
    df_new["ProcessGroup"] = "Demand"
    df_new = df_new[demand_process_categories].drop_duplicates()

    # combine and out
    df = pd.concat([df, df_new]).drop_duplicates()

    return df


def get_residential_demand_processes():
    """
    Residential process mapping extracted from prep module staging data.
    Here we additionally ensure that the sector is defined by the dwelling type
    (dwelling type is a key component of the process definition)
    """
    df = pd.read_csv(PREP_STAGE_2 / "residential/baseyear_residential_demand.csv")
    df["Sector"] = df["DwellingType"] + " Dwelling"
    df["SectorGroup"] = "Residential"
    df["ProcessGroup"] = "Demand"

    df = df[demand_process_categories].drop_duplicates()

    return df


def get_commercial_demand_processes():
    """
    Commercial process mapping extracted from prep module staging data.
    """
    df1 = pd.read_csv(PREP_STAGE_2 / "commercial/baseyear_commercial_demand.csv")
    df2 = pd.read_csv(COMMERCIAL_CONCORDANCES / "commercial_process_patch.csv")

    df = pd.concat([df1, df2], ignore_index=True)

    df["SectorGroup"] = "Commercial"
    df["ProcessGroup"] = "Demand"

    df = df[demand_process_categories].drop_duplicates()

    return df


def get_transport_demand_processes():
    """
    Transport process mapping extracted from prep module staging data.
    The transport module was developed differently so we have to do a bit more work

    Would be better to do some of this in stage 2 instead.

    We effectively take every process we can find and utilisation and technology names

    """
    # start with all parameters sent to main
    df_base = pd.read_csv(PREP_STAGE_4 / "base_year_tra/tra_process_parameters.csv")
    df_new = pd.read_csv(
        PREP_STAGE_4 / "subres_tra/future_transport_details_advanced_costcurve.csv"
    )

    df_base = df_base[["TechName", "Comm-In", "Comm-Out"]].drop_duplicates()
    df_new = df_new[["TechName", "Comm-In", "Comm-Out"]].drop_duplicates()

    df = pd.concat([df_base, df_new])

    process_concordances = pd.read_csv(TRANSPORT_CONCORDANCES / "processes.csv")
    commodity_concordances = pd.read_csv(TRANSPORT_CONCORDANCES / "commodities.csv")

    df = df.merge(process_concordances, on="TechName", how="left")
    df = df.merge(commodity_concordances, on="Comm-Out", how="left")

    df["ProcessGroup"] = "Demand"
    df["SectorGroup"] = "Transport"

    df = df.rename(columns={"TechName": "Process", "Comm-Out": "CommodityOut"})

    df = df[demand_process_categories]

    return df


def get_ag_demand_processes():
    """
    Ag process mapping extracted from prep module staging data.
    """
    df1 = pd.read_csv(
        PREP_STAGE_2 / "ag_forest_fish/baseyear_ag_forest_fish_demand.csv"
    )
    df2 = pd.read_csv(AGRICULTURE_CONCORDANCES / "agriculture_process_patch.csv")

    df = pd.concat([df1, df2], ignore_index=True)
    df["SectorGroup"] = "Agriculture, Forestry, and Fishing"
    df["ProcessGroup"] = "Demand"

    df = df[demand_process_categories].drop_duplicates()

    return df


def get_demand_commodities(df):
    """
    Use the demand process codes to also define all the demand commodities
    These should only exist in var_fout but good to clarify these
    """

    out = df.copy()

    out = out[["CommodityOut", "SectorGroup", "Sector", "EndUse"]].drop_duplicates()

    out["CommodityGroup"] = "Demand"
    out = out.rename(columns={"CommodityOut": "Commodity"})

    out = out[["CommodityGroup", "Commodity", "SectorGroup", "Sector", "EndUse"]]

    return out


def main():
    """
    Gather all the demand process concordances into a single file

    """

    df = pd.concat(
        [
            get_commercial_demand_processes(),
            get_transport_demand_processes(),
            get_residential_demand_processes(),
            get_industrial_demand_processes(),
            get_ag_demand_processes(),
        ]
    ).drop_duplicates()

    df.to_csv(PROCESS_CONCORDANCES / "demand.csv", index=False, encoding="utf-8-sig")

    # demand commodity definitions are based on this table
    demand = get_demand_commodities(df)
    demand.to_csv(
        COMMODITY_CONCORDANCES / "demand.csv", index=False, encoding="utf-8-sig"
    )


if __name__ == "__main__":
    main()
