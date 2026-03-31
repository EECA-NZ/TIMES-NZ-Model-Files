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
DAY_TYPE_AXIS_LABELS = {
    "WK": "Week",
    "WE": "Wknd.",
}
TIME_OF_DAY_LABELS = {
    "D": "Day",
    "P": "Peak",
    "N": "Night",
}

TIMESLICE_ORDER = [
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
        out["DayType"] = out["DayTypeCode"].map(DAY_TYPE_LABELS).fillna(
            out["DayTypeCode"]
        )
        out["TimeOfDay"] = out["TimeOfDayCode"].map(TIME_OF_DAY_LABELS).fillna(
            out["TimeOfDayCode"]
        )
    else:
        out["Season"] = out["SeasonCode"]
        out["DayType"] = out["DayTypeCode"]
        out["TimeOfDay"] = out["TimeOfDayCode"]

    return out


def get_timeslice_axis_label(timeslice: str) -> str:
    """
    Return a compact axis label token for a raw TimeSlice code.
    """
    parts = str(timeslice).split("-")
    if len(parts) != 3:
        return str(timeslice)
    season_code, day_type_code, time_of_day_code = parts
    season = SEASON_LABELS.get(season_code, season_code)
    day_type = DAY_TYPE_AXIS_LABELS.get(day_type_code, day_type_code)
    time_of_day = TIME_OF_DAY_LABELS.get(time_of_day_code, time_of_day_code)
    return f"{season}|{day_type} {time_of_day}"


def get_timeslice_long_label(timeslice: str) -> str:
    """
    Return a fuller tooltip label for a raw TimeSlice code.
    """
    parts = str(timeslice).split("-")
    if len(parts) != 3:
        return str(timeslice)
    season_code, day_type_code, time_of_day_code = parts
    season = SEASON_LABELS.get(season_code, season_code)
    day_type = DAY_TYPE_LABELS.get(day_type_code, day_type_code)
    time_of_day = TIME_OF_DAY_LABELS.get(time_of_day_code, time_of_day_code)
    return f"{season} / {day_type} / {time_of_day}"


def add_timeslice_chart_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add compact display labels for timeslice charts without changing raw codes.
    """
    out = split_timeslices(df, make_nice_labels=True)
    out["TimeSliceLabel"] = out["TimeSlice"].map(get_timeslice_axis_label)
    out["TimeSliceLongLabel"] = out["TimeSlice"].map(get_timeslice_long_label)
    return out


def get_timeslice_label_order() -> list[str]:
    """
    Ordered list of compact two-line labels matching the desired timeslice sort.
    """
    return [get_timeslice_axis_label(timeslice) for timeslice in TIMESLICE_ORDER]
