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

    # note that this duplication method is only needed
    # for comparing different model solar structures

    solar_dist_dupes = df[
        df["TechName"].isin(
            [
                "ELC_SolarDistBifacial_Com",
                "ELC_SolarDistBifacial_Ind",
                "ELC_SolarDistSmall_Res",
            ]
        )
    ].copy()
    solar_dist_dupes["TechName"] = solar_dist_dupes["TechName"].replace(
        {
            "ELC_SolarDistBifacial_Com": "ELC_SolarDist_Commercial",
            "ELC_SolarDistBifacial_Ind": "ELC_SolarDist_Industrial",
            "ELC_SolarDistSmall_Res": "ELC_SolarDist_Residential",
        }
    )
    # adjusting tech code to include solar dist
    solar_dist_dupes["Tech_TIMES"] = "SolarDist"
    df = pd.concat([df, solar_dist_dupes], ignore_index=True).drop_duplicates()

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

    solar_track_dupes = df[
        df["TechName"].str.startswith("ELC_SolarTrack_", na=False)
    ].copy()
    solar_track_dupes["TechName"] = solar_track_dupes["TechName"].str.replace(
        "ELC_SolarTrack_", "ELC_SolarFixed_", n=1, regex=False
    )
    solar_track_dupes["Tech_TIMES"] = "SolarFixed"
    df = pd.concat([df, solar_track_dupes], ignore_index=True).drop_duplicates()

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
        ]
    ).drop_duplicates()

    # if we failed to generate a plant name, we'll use the process as a backup
    df["PlantName"] = df["PlantName"].fillna(df["Process"])

    tech_codes = pd.read_csv(CONCORDANCE_PATCHES / "electricity/tech_codes.csv")
    df = df.merge(tech_codes, on="Tech_TIMES", how="left")

    # just some placeholders if we ever want to combine these with demand processes
    # df["EnduseGroup"] = PROCESS_GROUP
    # df["EndUse"] = PROCESS_GROUP
    # df["SectorGroup"] = PROCESS_GROUP
    # df["Sector"] = PROCESS_GROUP

    df = df[
        [
            "ProcessGroup",
            "Process",
            "PlantName",
            "TechnologyGroup",
            "Technology",
            # "SectorGroup",
            # "Sector",
            # "EnduseGroup",
            # "EndUse",
        ]
    ]

    df.to_csv(
        PROCESS_CONCORDANCES / "elec_generation.csv", index=False, encoding="utf-8-sig"
    )


if __name__ == "__main__":
    main()
