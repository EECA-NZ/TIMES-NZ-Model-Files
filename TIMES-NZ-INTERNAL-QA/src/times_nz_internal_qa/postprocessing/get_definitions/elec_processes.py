"""
Rules for all electricity generating processes

Outputs a concordance file for these



"""

import numpy as np

# get data
import pandas as pd
from times_nz_internal_qa.utilities.filepaths import (
    CONCORDANCE_PATCHES,
    PREP_STAGE_2,
    PREP_STAGE_3,
    PROCESS_CONCORDANCES,
)

# suggested labels:


# first read in the main one - we'll take some from this
PROCESS_GROUP = "Electricity generation"


def get_elc_base_processes():
    """
    Read all base year ele processes from staging prep data
    Return codes and categories
    """

    df = pd.read_csv(PREP_STAGE_2 / "electricity/base_year_electricity_supply.csv")
    df = df[["TechName", "PlantName", "Tech_TIMES"]].drop_duplicates()

    df = df.rename(columns={"TechName": "Process"})
    df["ProcessGroup"] = PROCESS_GROUP

    return df


def get_elc_genstack():
    """
    Read all genstack processes from staging prep data
    Return codes and categories
    """
    df = pd.read_csv(PREP_STAGE_3 / "electricity/genstack.csv")
    df = df[["TechName", "Plant", "Tech_TIMES"]].drop_duplicates()

    df = df.rename(columns={"TechName": "Process", "Plant": "PlantName"})
    df["ProcessGroup"] = PROCESS_GROUP

    return df


def get_elc_offshore():
    """
    Read all offshore processes from staging prep data
    Return codes and categories
    Unique to offshore wind: build human names for these plants based on tech and region
    """
    df = pd.read_csv(PREP_STAGE_3 / "electricity/offshore_wind.csv")

    df["PlantName"] = np.where(df["Tech_TIMES"] == "WindFixOff", "Fixed", "Floating")
    df["PlantName"] = "Offshore wind (" + df["PlantName"] + ") - " + df["Region"]

    df = df[["TechName", "PlantName", "Tech_TIMES"]].drop_duplicates()
    df = df.rename(columns={"TechName": "Process"})
    df["ProcessGroup"] = PROCESS_GROUP
    return df


def get_elc_dist_solar():
    """
    Read all dist solar processes from staging data
    Return codes and categories
    """
    df = pd.read_csv(PREP_STAGE_3 / "electricity/residential_solar.csv")
    df = df[["TechName", "Tech_TIMES"]].drop_duplicates()
    # weird patch
    df["TechName"] = df["TechName"].str.removesuffix("New")
    df = df.rename(columns={"TechName": "Process"})
    df["ProcessGroup"] = PROCESS_GROUP

    return df


def main():
    """
    Entry point. Simply reads all elc processes,
    Joins them all into a single table,
    Then writes the final output.
    """
    df = pd.concat(
        [
            get_elc_base_processes(),
            get_elc_genstack(),
            get_elc_offshore(),
            get_elc_dist_solar(),
        ]
    ).drop_duplicates()

    # if we failed to generate a plant name, we'll use the process as a backup
    df["PlantName"] = df["PlantName"].fillna(df["Process"])

    tech_codes = pd.read_csv(CONCORDANCE_PATCHES / "electricity/tech_codes.csv")
    df = df.merge(tech_codes, on="Tech_TIMES", how="left")

    # just some placeholders if we ever want to combine these with demand processes
    df["EnduseGroup"] = PROCESS_GROUP
    df["EndUse"] = PROCESS_GROUP
    df["SectorGroup"] = PROCESS_GROUP
    df["Sector"] = PROCESS_GROUP

    df = df[
        [
            "ProcessGroup",
            "Process",
            "PlantName",
            "TechnologyGroup",
            "Technology",
            "SectorGroup",
            "Sector",
            "EnduseGroup",
            "EndUse",
        ]
    ]

    df.to_csv(
        PROCESS_CONCORDANCES / "elec_generation.csv", index=False, encoding="utf-8-sig"
    )


if __name__ == "__main__":
    main()
