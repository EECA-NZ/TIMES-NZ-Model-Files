"""
This script designs the driver allocation table

It gathers EVERY commodity and assigns these to groups based on the sector

Exceptions include the "new industries" which we'll ignore for now
But these will need their own method for com_proj (+50GWh a year)


Transport might need a specific method here too depending on the outputs we wanna use from MOT

but maybe it's all just fine

"""

import pandas as pd
from prepare_times_nz.stage_4.transport import (
    COMM_TO_VEHICLE as transport_commodity_map,
)
from prepare_times_nz.utilities.data_in_out import _save_data
from prepare_times_nz.utilities.filepaths import (
    ASSUMPTIONS,
    STAGE_2_DATA,
    STAGE_4_DATA,
)
from prepare_times_nz.utilities.logger_setup import logger

PROJECTION_ASSUMPTIONS = ASSUMPTIONS / "demand_projections"
OUTPUT_LOCATION = STAGE_4_DATA / "scen_demand"


# FUNCTIONS


def save_data(df, name, label):
    """Save data wrapper"""
    _save_data(df, name, label, filepath=OUTPUT_LOCATION)


def get_sd_comm(filepath, sector_group=None):
    """
    Get sector demand commodities.
    For a given baseyear data file, returns the sectorgroup, sector,
    and demand commodities
    """
    df = pd.read_csv(STAGE_2_DATA / filepath)

    # not well standardised !! couple of checks
    if "Island" in df.columns:
        df["Region"] = df["Island"]

    if "SectorGroup" not in df.columns:
        df["SectorGroup"] = sector_group

    out = df[["Region", "SectorGroup", "Sector", "CommodityOut"]].drop_duplicates()
    return out


def get_transport_demand_commodities():
    """
    Special treatment for transport sector, taking the commodity map
    If we refactor stage 2 for transport to align with others this
    treatment won't be required and it'll be a bit cleaner/
    more robust
    """
    # we just need the commodity map pulled from the s4 code
    keys = list(transport_commodity_map.keys())
    values = list(transport_commodity_map.values())

    df = pd.DataFrame({"CommodityOut": keys, "Sector": values})

    df["SectorGroup"] = "Transport"
    region_df = pd.DataFrame({"Region": ["NI", "SI"]})
    df = df.merge(region_df, how="cross")
    out = df[["SectorGroup", "Sector", "Region", "CommodityOut"]].drop_duplicates()
    return out


def get_all_demand_commodities():
    """
    Combine all base year commodities together to map
    Note that any commodities not used in the base year
    will need to be handled separately.
    This is very uncommon so it's okay.
    """

    df = pd.concat(
        [
            get_sd_comm("commercial/baseyear_commercial_demand.csv"),
            get_sd_comm("industry/baseyear_industry_demand.csv", "Industry"),
            get_sd_comm("residential/baseyear_residential_demand.csv"),
            get_sd_comm("ag_forest_fish/baseyear_ag_forest_fish_demand.csv"),
            get_transport_demand_commodities(),
        ]
    )
    df = df[["SectorGroup", "Sector", "Region", "CommodityOut"]]

    return df


def add_sector_indices(default_driver="Constant"):
    """
    Building on the list of all sector commodity maps
    Take the inputs from the sector assumptions
    and assigns these to all demand commodities

    returns a legible dataframe. We might want this at some point
    For now we just reshape for Veda
    """

    df = get_all_demand_commodities()
    demand_drivers = pd.read_csv(PROJECTION_ASSUMPTIONS / "sector_demand_drivers.csv")

    df = df.merge(demand_drivers, on=["SectorGroup", "Sector"], how="left")

    df = df.sort_values(["SectorGroup", "Sector"])

    # check failed joins
    test = df[df["SectorDriver"].isna()]
    if len(test) > 0:
        logger.warning(
            "Warning: The following sectors have no associated growth drivers."
        )
        logger.warning(
            "These will have growth set to '%s' in all scenarios", default_driver
        )
        test = test[["SectorGroup", "Sector"]].drop_duplicates()
        for i, row in test.iterrows():
            logger.warning("         %s: %s - %s", i, row["SectorGroup"], row["Sector"])

    df["SectorDriver"] = df["SectorDriver"].fillna(default_driver)
    return df


def format_allocations_for_veda(df):
    """
    Reshapes and labels allocations for Veda
    Basically select, order, rename
    """

    df = df.rename(
        columns={
            "SectorDriver": "Driver",
            "CommodityOut": "Demand",
        }
    )

    key_cols = ["Region", "Demand", "Driver"]
    df = df[key_cols]
    df = df.sort_values(key_cols)

    # not currently using calibration or sensitivity for anything:
    # could add this functionality later
    # placeholder ones for now
    df["Calibration"] = "Constant"
    df["Sensitivity"] = "Constant"

    return df


def main():
    """Entrypoint"""
    commodity_indices = add_sector_indices()
    df = format_allocations_for_veda(commodity_indices)
    save_data(df, "driver_allocations.csv", "Saving driver Allocations")


if __name__ == "__main__":
    main()
