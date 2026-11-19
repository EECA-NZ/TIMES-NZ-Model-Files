"""Build demand-device reporting metadata from prepared model inputs."""

from __future__ import annotations

import pandas as pd

DEMAND_COLUMNS = [
    "ProcessGroup",
    "Process",
    "CommodityOut",
    "SectorGroup",
    "Sector",
    "EnduseGroup",
    "EndUse",
    "TechnologyGroup",
    "Technology",
    "Utilisation",
    "ClassificationSource",
    "ClassificationMethod",
]

_IDENTITY_COLUMNS = DEMAND_COLUMNS[2:10]
_OVERRIDE_COLUMNS = [
    "Process",
    *[column for column in _IDENTITY_COLUMNS if column != "Utilisation"],
]
_REQUIRED_DEMAND_COLUMNS = [
    "Process",
    "CommodityOut",
    "Sector",
    "EnduseGroup",
    "EndUse",
    "TechnologyGroup",
    "Technology",
]


def _require_columns(df: pd.DataFrame, columns: list[str], source: str) -> None:
    missing = sorted(set(columns).difference(df.columns))
    if missing:
        raise ValueError(f"{source} is missing columns: {', '.join(missing)}")


def _demand_rows(
    df: pd.DataFrame,
    sector_group: str,
    source: str,
    *,
    residential: bool = False,
) -> pd.DataFrame:
    """Select the shared demand reporting columns from one prepared table."""
    required = list(_REQUIRED_DEMAND_COLUMNS)
    if residential:
        required.append("DwellingType")
    _require_columns(df, required, source)

    rows = df[_REQUIRED_DEMAND_COLUMNS].copy()
    if residential:
        rows["Sector"] = df["DwellingType"] + " Dwelling"
    rows["ProcessGroup"] = "Demand"
    rows["SectorGroup"] = sector_group
    rows["Utilisation"] = pd.NA
    rows["ClassificationSource"] = source
    rows["ClassificationMethod"] = "Declared"
    return rows[DEMAND_COLUMNS]


def _transport_technology_labels(
    processes: pd.Series, technology_labels: pd.DataFrame
) -> pd.DataFrame:
    """Apply reporting-assumption labels to regular transport process codes."""
    _require_columns(
        technology_labels,
        ["Pattern", "Technology", "TechnologyGroup"],
        "transport technology labels",
    )
    if technology_labels["Pattern"].duplicated().any():
        raise ValueError("transport technology labels contains duplicate patterns")
    result = pd.DataFrame({"Process": processes.astype(str)})
    result["Technology"] = pd.NA
    result["TechnologyGroup"] = pd.NA
    for row in technology_labels.itertuples(index=False):
        pattern = str(row.Pattern)
        matches = result["Process"].str.contains(pattern, case=False, na=False)
        result.loc[matches, "Technology"] = row.Technology
        result.loc[matches, "TechnologyGroup"] = row.TechnologyGroup
    result["Utilisation"] = (
        result["Process"]
        .str.extract(r"_(LOW|MED|HIGH)$", expand=False)
        .map({"LOW": "Low", "MED": "Medium", "HIGH": "High"})
        .fillna("All")
    )
    unknown = result[result["Technology"].isna()]["Process"].tolist()
    if unknown:
        raise ValueError(
            "Transport reporting rule has no technology label for: "
            + ", ".join(sorted(unknown))
        )
    return result


def _transport_rows(
    base: pd.DataFrame,
    future: pd.DataFrame,
    commodity_labels: pd.DataFrame,
    technology_labels: pd.DataFrame,
) -> pd.DataFrame:
    """Build transport demand rows from prepared process parameters."""
    _require_columns(base, ["TechName", "Comm-Out"], "transport base parameters")
    _require_columns(future, ["TechName", "Comm-Out"], "transport future parameters")
    _require_columns(
        commodity_labels,
        ["CommodityOut", "Sector", "EnduseGroup", "EndUse"],
        "transport commodity labels",
    )

    processes = pd.concat(
        [
            base[["TechName", "Comm-Out"]],
            future[["TechName", "Comm-Out"]],
        ],
        ignore_index=True,
    ).drop_duplicates()
    processes = processes.rename(
        columns={"TechName": "Process", "Comm-Out": "CommodityOut"}
    )
    labels = _transport_technology_labels(processes["Process"], technology_labels)
    rows = processes.merge(labels, on="Process", how="left", validate="one_to_one")
    rows = rows.merge(
        commodity_labels,
        on="CommodityOut",
        how="left",
        validate="many_to_one",
    )
    missing = rows[rows[["Sector", "EnduseGroup", "EndUse"]].isna().any(axis=1)][
        "CommodityOut"
    ].unique()
    if len(missing):
        raise ValueError(
            "Transport reporting rule has no commodity label for: "
            + ", ".join(sorted(missing))
        )
    rows["ProcessGroup"] = "Demand"
    rows["SectorGroup"] = "Transport"
    rows["ClassificationSource"] = "transport reporting assumptions"
    rows["ClassificationMethod"] = "RuleGenerated"
    return rows[DEMAND_COLUMNS]


def _apply_overrides(
    rows: pd.DataFrame, overrides: pd.DataFrame, source: str
) -> pd.DataFrame:
    """Replace complete reporting identities for documented exceptional processes."""
    if overrides.empty:
        return rows
    _require_columns(overrides, _OVERRIDE_COLUMNS, source)
    replacements = overrides[_OVERRIDE_COLUMNS].copy()
    replacements["ProcessGroup"] = "Demand"
    replacements["Utilisation"] = pd.NA
    replacements["ClassificationSource"] = source
    replacements["ClassificationMethod"] = "Exception"
    replacements = replacements[DEMAND_COLUMNS]
    return pd.concat([rows, replacements], ignore_index=True).drop_duplicates(
        subset="Process", keep="last"
    )


def _deduplicate(rows: pd.DataFrame) -> pd.DataFrame:
    """Reject one process receiving multiple reporting identities."""
    identity_columns = [column for column in _IDENTITY_COLUMNS if column != "Process"]
    duplicated = rows[rows.duplicated("Process", keep=False)]
    conflicts = []
    for process, group in duplicated.groupby("Process", sort=False):
        if any(group[column].nunique(dropna=False) > 1 for column in identity_columns):
            conflicts.append(process)
    if conflicts:
        raise ValueError(
            "Demand reporting has conflicting identities for: "
            + ", ".join(sorted(conflicts))
        )
    return (
        rows.drop_duplicates(subset="Process", keep="first")
        .sort_values("Process", kind="stable")
        .reset_index(drop=True)
    )


def build_industry_processes(
    base: pd.DataFrame, future: pd.DataFrame, overrides: pd.DataFrame
) -> pd.DataFrame:
    """Build industry demand-device reporting rows."""
    industry = pd.concat(
        [
            _demand_rows(base, "Industry", "industry base year"),
            _demand_rows(future, "Industry", "industry future"),
        ],
        ignore_index=True,
    )
    return _apply_overrides(industry, overrides, "industry overrides")


def build_residential_processes(residential: pd.DataFrame) -> pd.DataFrame:
    """Build residential demand-device reporting rows."""
    return _demand_rows(
        residential,
        "Residential",
        "residential base year",
        residential=True,
    )


def build_commercial_processes(
    base: pd.DataFrame, future: pd.DataFrame, overrides: pd.DataFrame
) -> pd.DataFrame:
    """Build commercial demand-device reporting rows."""

    commercial = pd.concat(
        [
            _demand_rows(base, "Commercial", "commercial base year"),
            _demand_rows(future, "Commercial", "commercial future"),
        ],
        ignore_index=True,
    )
    return _apply_overrides(commercial, overrides, "commercial overrides")


def build_agriculture_processes(
    base: pd.DataFrame, future: pd.DataFrame
) -> pd.DataFrame:
    """Build agriculture, forestry and fishing demand-device reporting rows."""
    sector_group = "Agriculture, Forestry, and Fishing"
    return pd.concat(
        [
            _demand_rows(base, sector_group, "agriculture base year"),
            _demand_rows(future, sector_group, "agriculture future"),
        ],
        ignore_index=True,
    )


def build_transport_processes(
    base: pd.DataFrame,
    future: pd.DataFrame,
    commodity_labels: pd.DataFrame,
    technology_labels: pd.DataFrame,
) -> pd.DataFrame:
    """Build transport demand-device reporting rows."""
    return _transport_rows(base, future, commodity_labels, technology_labels)


def combine_demand_processes(sector_processes: list[pd.DataFrame]) -> pd.DataFrame:
    """Combine sector reporting rows into the complete demand-device catalog."""
    if not sector_processes:
        raise ValueError("At least one demand sector table is required")
    return _deduplicate(pd.concat(sector_processes, ignore_index=True))


def build_demand_commodities(processes: pd.DataFrame) -> pd.DataFrame:
    """Derive demand commodity labels from the completed demand-process catalog."""
    _require_columns(processes, DEMAND_COLUMNS, "demand processes")
    columns = ["CommodityOut", "SectorGroup", "Sector", "EndUse"]
    commodities = (
        processes[columns]
        .drop_duplicates()
        .rename(columns={"CommodityOut": "Commodity"})
    )
    commodities.insert(0, "CommodityGroup", "Demand")
    return commodities.sort_values("Commodity", kind="stable").reset_index(drop=True)
