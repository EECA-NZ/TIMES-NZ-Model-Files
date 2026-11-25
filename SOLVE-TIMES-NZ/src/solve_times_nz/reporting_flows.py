"""Battery and demand-flex publication tables, using recorded timeslice weights."""

from __future__ import annotations

import pandas as pd

SEASONS = {"SUM": "Summer", "FAL": "Autumn", "WIN": "Winter", "SPR": "Spring"}
DAYS = {"WK": "Weekday", "WE": "Weekend"}
HOURS = {"D": "Day", "P": "Peak", "N": "Night"}
# shortcut: legacy flow exports use 24 slices; extend these labels if the model changes.
TIMESLICES = [
    f"{season}-{day}-{hour}" for season in SEASONS for day in DAYS for hour in HOURS
]
FLEX_PROCESSES = {
    "DD-S_HEAT-FLEX": "RES-DD-ELC-HPSH-S_HEAT",
    "JD-S_HEAT-FLEX": "RES-JD-ELC-HPSH-S_HEAT",
    "DD-WH_LOW-FLEX": "RES-DD-ELC-HWATER_C-WH_LOW",
    "JD-WH_LOW-FLEX": "RES-JD-ELC-HWATER_C-WH_LOW",
    "DD-WH_LOW-SMART": "RES-DD-ELC-HWATER_C-WH_LOW",
    "JD-WH_LOW-SMART": "RES-JD-ELC-HWATER_C-WH_LOW",
}
NEGATIVE_FLOWS = {
    "battery charging",
    "demand flex input",
    "demand flex decrease",
    "demand flex down",
    "demand decrease",
    "demand reduction",
    "flexible demand decrease",
    "flexible demand down",
}


def equivalent_flex_input(flows: pd.DataFrame, raw: pd.DataFrame) -> pd.DataFrame:
    """Retain the existing residential flex-service to electricity-input conversion."""
    result = flows.copy()
    result["UnderlyingProcess"] = result.Process.str.upper().map(FLEX_PROCESSES)
    if result.UnderlyingProcess.isna().any():
        raise ValueError("Missing underlying process mapping for demand-flex rows")
    underlying = raw.loc[
        raw.Process.str.upper().isin(FLEX_PROCESSES.values())
        & raw.Attribute.isin(["VAR_FIn", "VAR_FOut"])
    ].copy()
    underlying["UnderlyingProcess"] = underlying.Process.str.upper()
    underlying["Period"] = pd.to_numeric(underlying.Period, errors="raise")
    if underlying.Period.isna().any() or underlying.Period.mod(1).ne(0).any():
        raise ValueError("Expected integer annual demand-flex periods")
    underlying["Period"] = underlying.Period.astype("int64")
    keys = ["Scenario", "UnderlyingProcess", "Period", "Region", "TimeSlice"]
    efficiencies = (
        underlying.groupby([*keys, "Attribute"], as_index=False)
        .PV.sum()
        .pivot(index=keys, columns="Attribute", values="PV")
        .reset_index()
    )
    if not {"VAR_FIn", "VAR_FOut"} <= set(efficiencies):
        raise ValueError(
            "Missing underlying input/output rows for demand-flex efficiency"
        )
    efficiencies["Efficiency"] = efficiencies.VAR_FOut / efficiencies.VAR_FIn
    result = result.merge(
        efficiencies[[*keys, "Efficiency"]], on=keys, how="left", validate="many_to_one"
    )
    if (
        result.Efficiency.isna().any()
        or not result.Efficiency.gt(0).all()
        or not result.Efficiency.lt(float("inf")).all()
    ):
        raise ValueError("Missing or invalid underlying demand-flex efficiency")
    result["Value"] /= result.Efficiency
    return result.drop(columns=["UnderlyingProcess", "Efficiency"])


def timeslice_view(
    data: pd.DataFrame, weights: pd.DataFrame, unit: str
) -> pd.DataFrame:
    """Sign, convert and complete flow groups over all 24 recorded model slices."""
    if not data.Unit.eq("PJ").all() or not data.Value.abs().lt(float("inf")).all():
        raise ValueError("Expected non-null flow values in PJ")
    if not data.TimeSlice.isin(TIMESLICES).all():
        raise ValueError("Unrecognised flow timeslice")
    data = data.copy()
    data.loc[data.Variable.str.lower().isin(NEGATIVE_FLOWS), "Value"] *= -1
    keys = ["Scenario", "Variable", "Technology", "Period", "TimeSlice"]
    data = data.groupby(keys, as_index=False).Value.sum()
    categories = data[
        ["Scenario", "Variable", "Technology", "Period"]
    ].drop_duplicates()
    grid = categories.merge(pd.DataFrame({"TimeSlice": TIMESLICES}), how="cross")
    result = (
        data.set_index(keys)
        .reindex(grid.set_index(keys).index, fill_value=0)
        .reset_index()
    )
    result = result.merge(
        weights[["TimeSlice", "YearFraction"]],
        on="TimeSlice",
        how="left",
        validate="many_to_one",
    )
    if (
        not result.YearFraction.gt(0).all()
        or not result.YearFraction.lt(float("inf")).all()
    ):
        raise ValueError("Missing or invalid recorded timeslice weights")
    result["Value"] *= 277.77777778
    if unit == "GW":
        result["Value"] /= result.YearFraction * 8760
    elif unit != "GWh":
        raise ValueError("Expected GW or GWh")
    result = result.drop(columns="YearFraction").assign(Unit=unit)
    parts = result.TimeSlice.str.split("-", expand=True)
    result[["SeasonCode", "DayTypeCode", "TimeOfDayCode"]] = parts
    result["Season"] = result.SeasonCode.map(SEASONS)
    result["DayType"] = result.DayTypeCode.map(DAYS)
    result["TimeOfDay"] = result.TimeOfDayCode.map(HOURS)
    result["TimeSliceDayTime"] = result.DayType + " " + result.TimeOfDay
    result["TimeSliceLongLabel"] = (
        result.Season + " / " + result.DayType + " / " + result.TimeOfDay
    )
    result["TimeSliceOrder"] = result.TimeSlice.map(TIMESLICES.index)
    return result.sort_values(["Scenario", "TimeSliceOrder"]).reset_index(drop=True)


def flow_summaries(
    tables: dict[str, pd.DataFrame], weights: pd.DataFrame
) -> dict[str, pd.DataFrame]:
    """Combine existing flow selections, retaining years and GW/GWh in columns."""
    result = {}
    for kind in ["battery", "demand_flex"]:
        data = tables[f"{kind}_flows.parquet"]
        if data.empty:
            continue
        if (
            data[["Scenario", "Variable", "Technology", "Period", "TimeSlice", "Value"]]
            .isna()
            .any()
            .any()
        ):
            raise ValueError(f"Missing {kind} flow keys or values")
        if kind == "demand_flex":
            data = equivalent_flex_input(data, tables["raw_results.parquet"])
        views = []
        for year in [2035, 2050]:
            selected = data.loc[data.Period.eq(year)]
            if selected.empty:
                continue
            for unit in ["GW", "GWh"]:
                views.append(timeslice_view(selected, weights, unit))
        if views:
            result[f"electricity/{kind}_flows"] = pd.concat(views, ignore_index=True)
    return result
