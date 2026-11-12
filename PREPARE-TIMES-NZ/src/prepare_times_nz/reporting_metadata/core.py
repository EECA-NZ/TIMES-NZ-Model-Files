"""Build non-demand reporting metadata from prepared model declarations."""

from __future__ import annotations

import pandas as pd

TIMESLICE_LABELS = {
    "Season": {"SUM-": "Summer", "FAL-": "Autumn", "WIN-": "Winter", "SPR-": "Spring"},
    "Weekly": {"WK-": "Weekday", "WE-": "Weekend"},
    "DayNite": {"D": "Day", "N": "Night", "P": "Peak"},
}

CODE_COLUMNS = {
    "Process",
    "Commodity",
    "CommodityOut",
    "TimeSlice",
    "SeasonCode",
    "DayTypeCode",
    "DayNightCode",
    "techname",
    "commname",
    "sets",
    "csets",
}


def uppercase_codes(df: pd.DataFrame) -> pd.DataFrame:
    """Match reporting identifiers to xl2times' uppercase GAMS identifiers."""
    result = df.copy()
    # xl2times uppercases all string identifiers before writing the TIMES model.
    for column in CODE_COLUMNS.intersection(result.columns):
        result[column] = result[column].map(
            lambda value: value.upper() if isinstance(value, str) else value
        )
    return result


def _require_columns(df: pd.DataFrame, columns: list[str], source: str) -> None:
    missing = sorted(set(columns).difference(df.columns))
    if missing:
        raise ValueError(f"{source} is missing columns: {', '.join(missing)}")


def build_energy_commodities(
    fuels: pd.DataFrame, sectors: pd.DataFrame
) -> pd.DataFrame:
    """Label generic and sector-prefixed energy commodities."""
    _require_columns(fuels, ["CommodityCode", "Commodity"], "fuel labels")
    _require_columns(sectors, ["SectorCode"], "sector labels")
    generic = fuels[["CommodityCode", "Commodity"]]
    sectoral = fuels.merge(sectors[["SectorCode"]], how="cross")
    sectoral["CommodityCode"] = sectoral["SectorCode"] + sectoral["CommodityCode"]
    result = pd.concat([generic, sectoral[["CommodityCode", "Commodity"]]])
    result = result.rename(columns={"CommodityCode": "Commodity", "Commodity": "Fuel"})
    additions = pd.DataFrame(
        {
            "Commodity": ["ELCDD", "ELCHV", "NGADD", "BIMDD", "FSTKNGA", "FSTKCOA"],
            "Fuel": [
                "Electricity",
                "Electricity",
                "Natural gas",
                "Biomethane",
                "Natural gas",
                "Coal",
            ],
        }
    )
    result = pd.concat([result, additions], ignore_index=True).drop_duplicates()
    result["CommodityGroup"] = "Energy"
    return result.sort_values("Commodity", kind="stable").reset_index(drop=True)


def build_distribution_processes(
    fuels: pd.DataFrame, sectors: pd.DataFrame, extra: pd.DataFrame
) -> pd.DataFrame:
    """Label rule-generated distribution processes and declared exceptions."""
    _require_columns(fuels, ["CommodityCode", "Commodity"], "fuel labels")
    _require_columns(sectors, ["SectorCode", "Sector"], "sector labels")
    _require_columns(
        extra,
        ["Process", "Sector", "Commodity", "ProcessGroup"],
        "distribution exceptions",
    )
    generated = fuels.merge(sectors, how="cross")
    generated["Process"] = "FTE_" + generated["SectorCode"] + generated["CommodityCode"]
    generated = generated[["Process", "Sector", "Commodity"]]
    generated["ProcessGroup"] = "Distribution"
    return (
        pd.concat([generated, extra], ignore_index=True)
        .drop_duplicates()
        .sort_values("Process", kind="stable")
        .reset_index(drop=True)
    )


def build_declaration_units(
    tables: list[pd.DataFrame], columns: list[str]
) -> pd.DataFrame:
    """Extract the stable set and unit fields from declared VEDA tables."""
    if not tables:
        return pd.DataFrame(columns=columns)
    normalised = []
    for table in tables:
        table = table.copy()
        table.columns = [column.lower() for column in table.columns]
        _require_columns(table, columns, "declared VEDA table")
        normalised.append(table.ffill()[columns])
    return (
        pd.concat(normalised, ignore_index=True)
        .drop_duplicates()
        .sort_values(columns, kind="stable")
        .reset_index(drop=True)
    )


def build_timeslices(
    time_slices: dict[str, list[str]], yrfr: pd.DataFrame
) -> pd.DataFrame:
    """Build ordered, human-readable TIMES timeslices from PREP declarations."""
    levels = ["Season", "Weekly", "DayNite"]
    for level in levels:
        if level not in time_slices:
            raise ValueError(f"TimeSlices is missing {level}")
        unknown = set(time_slices[level]).difference(TIMESLICE_LABELS[level])
        if unknown:
            raise ValueError(
                f"No clean {level} label for: {', '.join(sorted(unknown))}"
            )
    _require_columns(yrfr, ["TimeSlice", "YRFR"], "year fractions")
    rows = []
    for season in time_slices["Season"]:
        for weekly in time_slices["Weekly"]:
            for day_nite in time_slices["DayNite"]:
                rows.append(
                    {
                        "TimeSlice": season + weekly + day_nite,
                        "SeasonCode": season,
                        "Season": TIMESLICE_LABELS["Season"][season],
                        "DayTypeCode": weekly,
                        "DayType": TIMESLICE_LABELS["Weekly"][weekly],
                        "DayNightCode": day_nite,
                        "DayNight": TIMESLICE_LABELS["DayNite"][day_nite],
                    }
                )
    result = pd.DataFrame(rows)
    if yrfr["TimeSlice"].duplicated().any():
        raise ValueError("year fractions contains duplicate timeslices")
    result = result.merge(yrfr, on="TimeSlice", how="left", validate="one_to_one")
    missing = result.loc[result["YRFR"].isna(), "TimeSlice"].tolist()
    if missing:
        raise ValueError("Missing year fractions for: " + ", ".join(missing))
    unexpected = set(yrfr["TimeSlice"]).difference(result["TimeSlice"])
    if unexpected:
        raise ValueError(
            "Year fractions contain undeclared timeslices: "
            + ", ".join(sorted(unexpected))
        )
    result["TimesliceOrder"] = range(1, len(result) + 1)
    result["TimeSliceLabel"] = result[["Season", "DayType", "DayNight"]].agg(
        " — ".join, axis=1
    )
    result = result.rename(columns={"YRFR": "YearFraction"})
    annual = pd.DataFrame(
        [
            {
                "TimeSlice": "ANNUAL",
                "TimesliceOrder": 0,
                "TimeSliceLabel": "Annual",
                "YearFraction": 1.0,
            }
        ]
    )
    return pd.concat([annual, result], ignore_index=True)[
        [
            "TimeSlice",
            "TimesliceOrder",
            "SeasonCode",
            "Season",
            "DayTypeCode",
            "DayType",
            "DayNightCode",
            "DayNight",
            "TimeSliceLabel",
            "YearFraction",
        ]
    ]


def build_electricity_generation_processes(
    base: pd.DataFrame,
    genstack: pd.DataFrame,
    offshore: pd.DataFrame,
    technology_labels: pd.DataFrame,
) -> pd.DataFrame:
    """Attach stable report labels to PREP electricity-generation declarations."""
    _require_columns(base, ["TechName", "PlantName", "Tech_TIMES"], "base electricity")
    _require_columns(genstack, ["TechName", "Plant", "Tech_TIMES"], "genstack")
    _require_columns(offshore, ["TechName", "Region", "Tech_TIMES"], "offshore wind")
    _require_columns(
        technology_labels,
        ["Tech_TIMES", "Technology", "TechnologyGroup"],
        "electricity technology labels",
    )
    if technology_labels["Tech_TIMES"].duplicated().any():
        raise ValueError("electricity technology labels contains duplicate Tech_TIMES")
    base_rows = base[["TechName", "PlantName", "Tech_TIMES"]].rename(
        columns={"TechName": "Process"}
    )
    stack_rows = genstack[["TechName", "Plant", "Tech_TIMES"]].rename(
        columns={"TechName": "Process", "Plant": "PlantName"}
    )
    offshore_rows = offshore[["TechName", "Region", "Tech_TIMES"]].copy()
    offshore_rows["PlantName"] = (
        "Offshore wind ("
        + offshore_rows["Tech_TIMES"]
        .map({"WindFixOff": "Fixed", "WindFloatOff": "Floating"})
        .fillna(offshore_rows["Tech_TIMES"])
        + ") - "
        + offshore_rows["Region"]
    )
    offshore_rows = offshore_rows.rename(columns={"TechName": "Process"})[
        ["Process", "PlantName", "Tech_TIMES"]
    ]
    result = pd.concat(
        [base_rows, stack_rows, offshore_rows], ignore_index=True
    ).drop_duplicates()
    result["PlantName"] = result["PlantName"].fillna(result["Process"])
    result = result.merge(
        technology_labels, on="Tech_TIMES", how="left", validate="many_to_one"
    )
    unknown = result.loc[result["Technology"].isna(), "Tech_TIMES"].unique()
    if len(unknown):
        raise ValueError(
            "No electricity technology label for: " + ", ".join(sorted(unknown))
        )
    result["ProcessGroup"] = "Electricity generation"
    for column in ["SectorGroup", "Sector", "EnduseGroup", "EndUse"]:
        result[column] = "Electricity generation"
    return (
        result[
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
        .sort_values("Process", kind="stable")
        .reset_index(drop=True)
    )
