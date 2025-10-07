"""
Identifies and compiles descriptions of all distribution processes

A bit of a placeholder - we have identified them, but may want to adjust
their descriptions later, depending on reporting requirements.
"""

import pandas as pd
from times_nz_internal_qa.utilities.filepaths import (
    CONCORDANCE_PATCHES,
    PROCESS_CONCORDANCES,
)


def get_generic_distribution_processes():
    """
    Get definitions of distribution processes. Combine fuel and sector codes.
    """

    fuel_codes = pd.read_csv(CONCORDANCE_PATCHES / "code_mapping/fuel_codes.csv")
    sector_codes = pd.read_csv(CONCORDANCE_PATCHES / "code_mapping/sector_codes.csv")

    # cross join every combination of sector x fuel to label as the fuel
    df = fuel_codes.merge(sector_codes, how="cross")

    df["Process"] = "FTE_" + df["SectorCode"] + df["CommodityCode"]

    df = df[["Process", "Sector", "Commodity"]]
    df["ProcessGroup"] = "Distribution"

    # this will autogenerate every possible code
    # many of these won't exist (like wood for transport)
    # electricity is handled separately so we remove from this method
    # df = df[df["Commodity"] != "Electricity"]

    return df


def get_elc_distribution_processes():
    """
    quick manual descriptions of elc processes
    Might be better to put these in a concordance file
    """

    elc_dist_processes = [
        "G_ELC_A",
        "G_ELC_C",
        "G_ELC_I",
        "G_ELC_HV",
        "G_ELC_LV",
        "G_ELC_T_00",  # what is this???
        "G_ELC_R",
    ]

    df = pd.DataFrame()
    df["Process"] = elc_dist_processes
    df["Sector"] = "Electricity distribution"
    df["Commodity"] = "Electricity"
    df["ProcessGroup"] = "Distribution"

    return df


def get_ire_processes():
    """
    Manual loading of inter-regional exchange processes
    However we are shaping our main distribution file, this should match

    Not quite sure how best to deal with these right now, bit of a placeholder.

    """

    ire_patch = pd.read_csv(CONCORDANCE_PATCHES / "distribution/ire.csv")
    return ire_patch


def main():
    """script entrypoint"""

    df = pd.concat(
        [
            get_generic_distribution_processes(),
            get_elc_distribution_processes(),
            get_ire_processes(),
        ]
    )
    df.to_csv(PROCESS_CONCORDANCES / "distribution.csv", index=False)


if __name__ == "__main__":
    main()
