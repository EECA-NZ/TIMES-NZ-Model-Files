"""
Export committed documentation tables from generated solar availability factors.
"""

from __future__ import annotations

import csv

import pandas as pd
from prepare_times_nz.utilities.filepaths import PREP_LOCATION, STAGE_3_DATA

SOLAR_AF_FILE = (
    STAGE_3_DATA / "electricity/solar_af/timeslices/solar_availability_factors.csv"
)
HOURLY_FILE = STAGE_3_DATA / "electricity/solar_af/hourly/all_scenarios_hourly_long.csv"
DOC_TABLE_DIR = PREP_LOCATION / "docs/source/model_methodology/electricity/tables"

TECH_TABLE_FILES = {
    "SolarDistSmall": "solar_availability_dist.csv",
    "SolarDistBifacial": "solar_availability_dist_bifacial.csv",
    "SolarTrack": "solar_availability_utility_track.csv",
}

SEASON_LABELS = {
    "FAL": "Autumn",
    "SPR": "Spring",
    "SUM": "Summer",
    "WIN": "Winter",
}

DAY_TYPE_LABELS = {
    "WE": "Weekend",
    "WK": "Weekday",
}

TIME_OF_DAY_LABELS = {
    "D": "Day",
    "N": "Night",
    "P": "Peak",
}


def format_percent(value: float) -> str:
    """
    Format an availability factor as a percentage string.
    """
    return f"{value * 100:.1f}%"


def build_doc_table(
    tech: str, timeslice_df: pd.DataFrame, annual_df: pd.DataFrame
) -> list[list[str]]:
    """
    Convert generated timeslice outputs into the documentation-table layout.
    """
    tech_df = timeslice_df[timeslice_df["Tech_TIMES"] == tech].copy()
    tech_df[["SeasonCode", "DayTypeCode", "TimeOfDayCode"]] = tech_df[
        "TimeSlice"
    ].str.split("-", expand=True)

    rows = [["Season", "Day Type", "Time of Day", "North Island", "South Island"]]
    for _, row in tech_df.iterrows():
        rows.append(
            [
                SEASON_LABELS[row["SeasonCode"]],
                DAY_TYPE_LABELS[row["DayTypeCode"]],
                TIME_OF_DAY_LABELS[row["TimeOfDayCode"]],
                format_percent(row["NI"]),
                format_percent(row["SI"]),
            ]
        )

    annual = annual_df[annual_df["Tech_TIMES"] == tech].set_index("Island")
    rows.append(
        [
            "**Annual**",
            "",
            "",
            f"**{format_percent(annual.loc['NI', 'generation_kw_per_kw'])}**",
            f"**{format_percent(annual.loc['SI', 'generation_kw_per_kw'])}**",
        ]
    )
    return rows


def export_doc_tables():
    """
    Write the committed documentation CSV tables from the current solar outputs.
    """
    DOC_TABLE_DIR.mkdir(parents=True, exist_ok=True)

    timeslice_df = pd.read_csv(SOLAR_AF_FILE)
    annual_df = (
        pd.read_csv(HOURLY_FILE)
        .groupby(["Tech_TIMES", "Island"], as_index=False)["generation_kw_per_kw"]
        .mean()
    )

    for tech, filename in TECH_TABLE_FILES.items():
        rows = build_doc_table(tech, timeslice_df, annual_df)
        output_path = DOC_TABLE_DIR / filename
        with output_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle, lineterminator="\n")
            writer.writerows(rows)


if __name__ == "__main__":
    export_doc_tables()
