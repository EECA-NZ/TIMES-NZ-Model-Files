"""
Helpers for applying commissioning-date adjustments to fixed-build plants.

The first steps are to:
1. identify plants in the stage-3 genstack output with fixed commissioning years
2. read any user assumptions about install months
3. default missing install months to July
4. translate install months into seasonal shares for the commissioning year
"""

from __future__ import annotations

import pandas as pd
from prepare_times_nz.utilities.data_in_out import _save_data
from prepare_times_nz.utilities.filepaths import ASSUMPTIONS, STAGE_3_DATA, STAGE_4_DATA

GENSTACK_FILE = STAGE_3_DATA / "electricity" / "genstack.csv"
FIXED_INSTALL_MONTHS_FILE = (
    ASSUMPTIONS / "electricity_generation" / "future_techs" / "FixedInstallMonths.csv"
)
RENEWABLE_AVAILABILITY_FILE = (
    STAGE_4_DATA / "scen_ren_af" / "renewable_availability.csv"
)
OUTPUT_LOCATION = STAGE_4_DATA / "scen_ren_af"
DEFAULT_INSTALL_MONTH = 7

month_season_map = {
    1: "SUM",
    2: "SUM",
    3: "FAL",
    4: "FAL",
    5: "FAL",
    6: "WIN",
    7: "WIN",
    8: "WIN",
    9: "SPR",
    10: "SPR",
    11: "SPR",
    12: "SUM",
}


def get_fixed_plant_dates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Return one row per fixed-build plant and commissioning year.

    The stage-3 genstack table contains many duplicate rows per plant because
    it is expanded by variable, year, and scenario. Step 1 filters to fixed
    commissioning plants and collapses that metadata to one row per plant.
    """

    required_columns = {
        "Plant",
        "TechName",
        "Tech_TIMES",
        "Island",
        "CommissioningType",
        "CommissioningYear",
    }
    missing_columns = required_columns.difference(df.columns)
    if missing_columns:
        missing_str = ", ".join(sorted(missing_columns))
        raise ValueError(
            f"Missing required columns for fixed plant dates: {missing_str}"
        )

    out = df[df["CommissioningType"] == "Fixed"].copy()
    out = out.loc[:, ["Plant", "TechName", "Tech_TIMES", "Island", "CommissioningYear"]]
    out = out.dropna(subset=["Plant", "TechName", "CommissioningYear"])
    out = out.rename(columns={"CommissioningYear": "Year"})
    out["Year"] = pd.to_numeric(out["Year"], errors="raise").astype(int)

    out = out.drop_duplicates().sort_values(["Year", "TechName"], ignore_index=True)
    return out


def read_fixed_plant_dates(filepath=GENSTACK_FILE) -> pd.DataFrame:
    """Read the stage-3 genstack file and return the fixed-build plant table."""

    df = pd.read_csv(filepath)
    return get_fixed_plant_dates(df)


def get_season_shares(month: int) -> dict[str, float]:
    """
    For a given install month, return the share of each season active in that year.

    Example:
    - month 1: all seasons are fully represented
    - month 6: winter and spring are fully represented, summer is 1/3, autumn is 0
    """

    if pd.isna(month):
        raise ValueError("Month cannot be null.")

    month = int(month)
    if month < 1 or month > 12:
        raise ValueError(f"Month must be between 1 and 12. Received: {month}")

    seasons = ["SUM", "FAL", "WIN", "SPR"]
    months_active = range(month, 13)

    shares = {}
    for season in seasons:
        season_months = [
            m
            for m, mapped_season in month_season_map.items()
            if mapped_season == season
        ]
        active_months = [m for m in months_active if month_season_map[m] == season]
        shares[season] = len(active_months) / len(season_months)

    return shares


def read_fixed_install_month_assumptions(
    filepath=FIXED_INSTALL_MONTHS_FILE,
) -> pd.DataFrame:
    """
    Read user assumptions for fixed-plant installation months.
    """

    df = pd.read_csv(filepath)
    required_columns = {"PlantName", "InstallMonth"}
    missing_columns = required_columns.difference(df.columns)
    if missing_columns:
        missing_str = ", ".join(sorted(missing_columns))
        raise ValueError(
            f"Missing required columns for fixed install month assumptions: {missing_str}"
        )

    out = df.loc[:, ["PlantName", "InstallMonth"]].copy()
    out["PlantName"] = out["PlantName"].astype(str).str.strip()
    out["PlantName"] = out["PlantName"].replace("", pd.NA)
    out["InstallMonth"] = pd.to_numeric(out["InstallMonth"], errors="coerce")
    out = out.dropna(subset=["PlantName"])
    out = out.drop_duplicates(subset=["PlantName"], keep="last")

    return out


def validate_fixed_install_month_names(
    fixed_plants: pd.DataFrame, install_months: pd.DataFrame
) -> None:
    """
    Ensure all assumption names correspond to known fixed-build plants.
    """

    valid_names = set(fixed_plants["Plant"])
    provided_names = set(install_months["PlantName"])
    unknown_names = sorted(provided_names.difference(valid_names))

    if unknown_names:
        unknown_str = ", ".join(unknown_names)
        raise ValueError(
            "Fixed install month assumptions include plants not found in the "
            f"existing fixed install list: {unknown_str}"
        )


def assign_install_months(
    fixed_plants: pd.DataFrame,
    install_months: pd.DataFrame,
    default_month: int = DEFAULT_INSTALL_MONTH,
) -> pd.DataFrame:
    """
    Join fixed plants to install-month assumptions and fill missing values.
    """

    validate_fixed_install_month_names(fixed_plants, install_months)

    out = fixed_plants.merge(
        install_months,
        left_on="Plant",
        right_on="PlantName",
        how="left",
    )
    out = out.drop(columns=["PlantName"])
    out["InstallMonth"] = out["InstallMonth"].fillna(default_month).astype(int)

    invalid_months = out.loc[
        ~out["InstallMonth"].between(1, 12), ["Plant", "InstallMonth"]
    ]
    if not invalid_months.empty:
        invalid_str = ", ".join(
            f"{row.Plant}={row.InstallMonth}" for row in invalid_months.itertuples()
        )
        raise ValueError(f"Install months must be between 1 and 12: {invalid_str}")

    return out


def create_renewable_availability_wildcard(tech_code: str) -> str:
    """
    Create the renewable-availability wildcard used in the Veda AF table.
    """

    wildcard = f"ELC_{tech_code}_*"

    if wildcard == "ELC_Geo_*":
        return "ELC_Geo_*, -ELC_GeoCHP_*"

    return wildcard


def add_renewable_availability_wildcards(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add the genstack tech code and matching renewable-availability wildcard.
    """

    out = df.copy()
    out["Pset_PN"] = out["Tech_TIMES"].map(create_renewable_availability_wildcard)
    return out


def expand_fixed_plants_to_season_shares(df: pd.DataFrame) -> pd.DataFrame:
    """
    Expand one row per plant to one row per plant-season share.
    """

    rows = []
    for row in df.itertuples():
        season_shares = get_season_shares(row.InstallMonth)
        for season, share in season_shares.items():
            rows.append(
                {
                    "TechName": row.TechName,
                    "TechCode": row.Tech_TIMES,
                    "Pset_PN": row.Pset_PN,
                    "Year": row.Year,
                    "Region": row.Island,
                    "Season": season,
                    "Share": share,
                }
            )

    out = pd.DataFrame(rows)
    out = out.sort_values(["Year", "Region", "TechName", "Season"], ignore_index=True)
    return out


def get_fixed_plant_season_shares(
    genstack_filepath=GENSTACK_FILE,
    assumptions_filepath=FIXED_INSTALL_MONTHS_FILE,
    default_month: int = DEFAULT_INSTALL_MONTH,
) -> pd.DataFrame:
    """
    Build the season-share table for all fixed-build plants.

    Output columns:
    - TechName
    - Year
    - Region
    - Season
    - Share
    """

    fixed_plants = read_fixed_plant_dates(genstack_filepath)
    install_months = read_fixed_install_month_assumptions(assumptions_filepath)
    fixed_plants = assign_install_months(
        fixed_plants, install_months, default_month=default_month
    )
    fixed_plants = add_renewable_availability_wildcards(fixed_plants)

    return expand_fixed_plants_to_season_shares(fixed_plants)


def read_renewable_availability(filepath=RENEWABLE_AVAILABILITY_FILE) -> pd.DataFrame:
    """
    Read the existing stage-4 Veda renewable availability output.

    This is the table that fixed-plant seasonal adjustments will eventually
    update after a plant-to-availability mapping is applied.
    """

    df = pd.read_csv(filepath)
    required_columns = {
        "TimeSlice",
        "LimType",
        "Attribute",
        "NI",
        "SI",
        "Pset_PN",
        "Year",
    }
    missing_columns = required_columns.difference(df.columns)
    if missing_columns:
        missing_str = ", ".join(sorted(missing_columns))
        raise ValueError(
            "Missing required columns for renewable availability data: "
            f"{missing_str}"
        )

    return df


def extract_season_from_timeslice(timeslice: str) -> str:
    """
    Convert a TIMES timeslice label like ``WIN-WK-P`` to ``WIN``.
    """

    if pd.isna(timeslice):
        raise ValueError("TimeSlice cannot be null when deriving Season.")

    season = str(timeslice).strip()[:3]
    valid_seasons = {"SUM", "FAL", "WIN", "SPR"}
    if season not in valid_seasons:
        raise ValueError(f"Unrecognised season in TimeSlice: {timeslice}")

    return season


def prepare_renewable_availability_for_join(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add a season key and keep only explicit renewable-availability years.
    """

    out = df.copy()
    # remove interps
    out = out[out["Year"] > 0].copy()
    # define seasons
    out["Season"] = out["TimeSlice"].map(extract_season_from_timeslice)
    # remove the year
    out = out.drop("Year", axis=1)
    return out


def validate_fixed_plant_wildcards_against_renewable_availability(
    fixed_plants: pd.DataFrame, renewable_availability: pd.DataFrame
) -> None:
    """
    Ensure generated plant wildcards exist in the renewable availability table.
    """

    available_wildcards = set(renewable_availability["Pset_PN"].dropna().unique())
    fixed_wildcards = set(fixed_plants["Pset_PN"].dropna().unique())
    missing_wildcards = sorted(fixed_wildcards.difference(available_wildcards))

    if missing_wildcards:
        missing_str = ", ".join(missing_wildcards)
        raise ValueError(
            "Generated fixed-plant wildcards not found in renewable availability "
            f"data: {missing_str}"
        )


def join_fixed_plants_to_renewable_availability(
    fixed_plants: pd.DataFrame, renewable_availability: pd.DataFrame
) -> pd.DataFrame:
    """
    Join fixed-plant season shares to renewable availability by wildcard and season.
    """

    renewable_availability = prepare_renewable_availability_for_join(
        renewable_availability
    )

    out = fixed_plants.merge(
        renewable_availability,
        on=["Pset_PN", "Season"],
        how="left",
        validate="many_to_many",
    )

    missing_matches = out.loc[
        out["TimeSlice"].isna(), ["TechName", "Pset_PN", "Season"]
    ].drop_duplicates()
    if not missing_matches.empty:
        missing_str = ", ".join(
            f"{row.TechName} ({row.Pset_PN}, {row.Season})"
            for row in missing_matches.itertuples()
        )
        raise ValueError(
            "Fixed plant season rows could not be matched to renewable "
            f"availability data: {missing_str}"
        )

    return out.sort_values(
        ["Year", "Region", "TechName", "Season", "TimeSlice"], ignore_index=True
    )


def format_fixed_plant_adjustment_output(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert joined renewable rows into the downstream fixed-plant output shape.
    """

    out = df.copy()
    out["Value"] = pd.NA
    out.loc[out["Region"] == "NI", "Value"] = out.loc[out["Region"] == "NI", "NI"]
    out.loc[out["Region"] == "SI", "Value"] = out.loc[out["Region"] == "SI", "SI"]
    invalid_regions = out.loc[
        out["Value"].isna(), ["TechName", "Region"]
    ].drop_duplicates()

    out["Value"] = out["Value"] * out["Share"]
    if not invalid_regions.empty:
        invalid_str = ", ".join(
            f"{row.TechName} ({row.Region})" for row in invalid_regions.itertuples()
        )
        raise ValueError(
            "Fixed plant rows include unsupported regions for renewable "
            f"availability values: {invalid_str}"
        )

    out = out.drop(columns=["NI", "SI", "Pset_PN", "TechCode", "Season", "Share"])

    out = out.rename(columns={"TechName": "PSet_PN"})

    return out.sort_values(
        ["Year", "Region", "PSet_PN", "TimeSlice"], ignore_index=True
    )


def main() -> pd.DataFrame:
    """Convenience wrapper for interactive use."""

    fixed_plants = get_fixed_plant_season_shares()
    renewable_availability = read_renewable_availability()
    validate_fixed_plant_wildcards_against_renewable_availability(
        fixed_plants, renewable_availability
    )
    joined = join_fixed_plants_to_renewable_availability(
        fixed_plants, renewable_availability
    )
    out = format_fixed_plant_adjustment_output(joined)
    _save_data(
        out,
        "renewable_availability_fixed_adjustments.csv",
        "Renewable availability fixed adjustments",
        OUTPUT_LOCATION,
    )
    return out


if __name__ == "__main__":
    print(main())
