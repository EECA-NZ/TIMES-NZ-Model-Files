"""
Shared helpers for constructing TIMES timeslices.
"""

from __future__ import annotations

from functools import cache

import numpy as np
import pandas as pd
from prepare_times_nz.utilities.filepaths import DATA_RAW

TIME_OF_DAY_FILE = DATA_RAW / "user_config/settings/time_of_day_types.csv"


@cache
def get_hour_to_time_map() -> dict[int, str]:
    """
    Load the project hour-to-time-of-day mapping once per process.
    """
    time_of_day_types = pd.read_csv(TIME_OF_DAY_FILE)
    return dict(zip(time_of_day_types["Hour"], time_of_day_types["Time_Of_Day"]))


def convert_hour_to_timeofday(df: pd.DataFrame, hour_col: str = "Hour") -> pd.DataFrame:
    """
    Map integer hours to the project time-of-day categories.
    """
    df["Time_Of_Day"] = df[hour_col].map(get_hour_to_time_map())
    df["Time_Of_Day"] = df["Time_Of_Day"].fillna("N")
    return df


def convert_date_to_daytype(
    df: pd.DataFrame, date_col: str = "Trading_Date"
) -> pd.DataFrame:
    """
    Map dates to project weekday and weekend labels.
    """
    df[date_col] = pd.to_datetime(df[date_col])
    weekday = df[date_col].dt.weekday
    df["Day_Type"] = np.select(
        [weekday.isin([5, 6]), weekday.isin([0, 1, 2, 3, 4])],
        ["WE-", "WK-"],
        default="ERROR",
    )
    return df


def convert_date_to_season(
    df: pd.DataFrame, date_col: str = "Trading_Date"
) -> pd.DataFrame:
    """
    Map dates to the project season labels.
    """
    df[date_col] = pd.to_datetime(df[date_col])
    month = df[date_col].dt.month
    df["Season"] = np.select(
        [
            month.isin([12, 1, 2]),
            month.isin([3, 4, 5]),
            month.isin([6, 7, 8]),
            month.isin([9, 10, 11]),
        ],
        ["SUM-", "FAL-", "WIN-", "SPR-"],
        default="ERROR",
    )
    return df


def create_timeslices(
    df: pd.DataFrame, date_col: str = "Trading_Date", hour_col: str = "Hour"
) -> pd.DataFrame:
    """
    Add a TIMES-style `TimeSlice` column using the shared project mapping.
    """
    df = convert_hour_to_timeofday(df, hour_col=hour_col)
    df = convert_date_to_daytype(df, date_col)
    df = convert_date_to_season(df, date_col)
    df["TimeSlice"] = df["Season"] + df["Day_Type"] + df["Time_Of_Day"]
    df = df.drop(columns=["Season", "Day_Type", "Time_Of_Day"])
    return df
