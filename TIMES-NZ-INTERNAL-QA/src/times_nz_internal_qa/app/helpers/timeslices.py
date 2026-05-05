"""
Helpers for parsing, ordering, and labelling TIMES-NZ timeslices.
"""

from __future__ import annotations

import pandas as pd

SEASON_ORDER = ["SUM", "FAL", "WIN", "SPR"]
DAY_TYPE_ORDER = ["WK", "WE"]
TIME_OF_DAY_ORDER = ["D", "P", "N"]

SEASON_LABELS = {
    "SUM": "Summer",
    "FAL": "Autumn",
    "WIN": "Winter",
    "SPR": "Spring",
}
DAY_TYPE_LABELS = {
    "WK": "Weekday",
    "WE": "Weekend",
}
TIME_OF_DAY_LABELS = {
    "D": "Day",
    "P": "Peak",
    "N": "Night",
}

TIMESLICE_ORDER = ["ANNUAL"] + [
    f"{season}-{day_type}-{time_of_day}"
    for season in SEASON_ORDER
    for day_type in DAY_TYPE_ORDER
    for time_of_day in TIME_OF_DAY_ORDER
]


def split_timeslices(df: pd.DataFrame, make_nice_labels: bool = True) -> pd.DataFrame:
    """
    Split TimeSlice into Season, DayType, and TimeOfDay columns.
    """
    out = df.copy()

    parts = out["TimeSlice"].astype(str).str.split("-", expand=True)
    out["SeasonCode"] = parts[0]
    out["DayTypeCode"] = parts[1]
    out["TimeOfDayCode"] = parts[2]

    if make_nice_labels:
        out["Season"] = out["SeasonCode"].map(SEASON_LABELS).fillna(out["SeasonCode"])
        out["DayType"] = (
            out["DayTypeCode"].map(DAY_TYPE_LABELS).fillna(out["DayTypeCode"])
        )
        out["TimeOfDay"] = (
            out["TimeOfDayCode"].map(TIME_OF_DAY_LABELS).fillna(out["TimeOfDayCode"])
        )
    else:
        out["Season"] = out["SeasonCode"]
        out["DayType"] = out["DayTypeCode"]
        out["TimeOfDay"] = out["TimeOfDayCode"]

    annual_mask = out["TimeSlice"].astype(str).eq("ANNUAL")
    out.loc[annual_mask, "Season"] = "Annual"
    out.loc[annual_mask, "DayType"] = ""
    out.loc[annual_mask, "TimeOfDay"] = ""

    return out


def get_timeslice_day_time_label(timeslice: str) -> str:
    """
    Return a combined DayType/TimeOfDay label for a raw TimeSlice code.
    """
    if str(timeslice) == "ANNUAL":
        return ""

    _, day_type_code, time_of_day_code = str(timeslice).split("-")
    day_type = DAY_TYPE_LABELS.get(day_type_code, day_type_code)
    time_of_day = TIME_OF_DAY_LABELS.get(time_of_day_code, time_of_day_code)
    return f"{day_type} {time_of_day}"


def get_timeslice_long_label(timeslice: str) -> str:
    """
    Return a fuller tooltip label for a raw TimeSlice code.
    """
    if str(timeslice) == "ANNUAL":
        return "Annual"

    season_code, day_type_code, time_of_day_code = str(timeslice).split("-")
    season = SEASON_LABELS.get(season_code, season_code)
    day_type = DAY_TYPE_LABELS.get(day_type_code, day_type_code)
    time_of_day = TIME_OF_DAY_LABELS.get(time_of_day_code, time_of_day_code)
    return f"{season} / {day_type} / {time_of_day}"


def add_timeslice_chart_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add display labels for timeslice charts without changing raw codes.
    """
    out = split_timeslices(df, make_nice_labels=True)
    out["TimeSliceDayTime"] = out["TimeSlice"].map(get_timeslice_day_time_label)
    out["TimeSliceLongLabel"] = out["TimeSlice"].map(get_timeslice_long_label)
    return out
