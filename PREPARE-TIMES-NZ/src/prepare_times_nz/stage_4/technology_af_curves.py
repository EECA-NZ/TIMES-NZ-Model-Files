"""
Generate timeslice-level AF curves for explicitly configured technologies.

Workflow:
1. Read a TOML file listing the fixed-AF groups we want to create.
2. For each group, find the electricity technologies in the chosen sector that
   serve the requested end use.
3. Pull the COM_FR shape from the explicitly listed COM_FR code.
4. Emit NCAP_AF rows for those technologies plus companion NCAP_AFA resets.


# NOTE:


"""

import tomllib
from pathlib import Path

import pandas as pd
from prepare_times_nz.stage_0.stage_0_settings import BASE_YEAR
from prepare_times_nz.utilities.data_in_out import _save_data
from prepare_times_nz.utilities.filepaths import ASSUMPTIONS, STAGE_2_DATA, STAGE_4_DATA

OUTPUT_LOCATION = Path(STAGE_4_DATA) / "scen_loadcurve"
OUTPUT_LOCATION.mkdir(parents=True, exist_ok=True)
YRFR_FILE = STAGE_2_DATA / "settings/load_curves/yrfr.csv"

AF_ATTRIBUTE = "NCAP_AF"
AFA_ATTRIBUTE = "NCAP_AFA"
BASE_AF_YEAR = BASE_YEAR + 1
BASE_AFA_VALUE = 1.0
FUTURE_DEFAULT_VALUE = 5.0
FUTURE_DEFAULT_YEAR = 0
LIMIT_TYPE = "FX"

AF_SELECTOR_FILE = ASSUMPTIONS / "load_curves/fixed_af_technologies.toml"

SECTOR_CONFIG = {
    "Residential": {
        "baseyear_file": STAGE_2_DATA / "residential/baseyear_residential_demand.csv",
        "curve_file": STAGE_4_DATA / "scen_com_fr/com_fr_residential.csv",
        "electricity_commodity": "RESELC",
        # which column in the baseyear file is used to denote sector type:
        "sector_column": "DwellingType",
        # which component of the process code gets a * for Veda wildcard:
        "code_component_to_wildcard": 3,
    },
    "Commercial": {
        "baseyear_file": STAGE_2_DATA / "commercial/baseyear_commercial_demand.csv",
        "curve_file": STAGE_4_DATA / "scen_com_fr/com_fr_commercial.csv",
        "electricity_commodity": "COMELC",
        "sector_column": "Sector",
        "code_component_to_wildcard": 2,
    },
}


def save_output(df: pd.DataFrame, name: str, label: str) -> None:
    """Stage-4 wrapper for saving generated AF inputs."""
    _save_data(df, name=name, label=label, filepath=OUTPUT_LOCATION)


def _clean_text(series: pd.Series) -> pd.Series:
    return series.astype("string").str.strip()


def load_af_selectors(filepath: Path = AF_SELECTOR_FILE) -> pd.DataFrame:
    """Load the fixed AF group definitions from TOML."""
    with open(filepath, "rb") as file:
        raw_config = tomllib.load(file)

    rows = []
    for group_name, group_config in raw_config.items():
        row = {"Name": group_name, **group_config}
        rows.append(row)

    df = pd.DataFrame(rows)

    required = {"Name", "SectorGroup", "Sector", "EndUse", "COM_FR", "PeakAvailability"}
    missing = required - set(df.columns)
    if missing:
        raise KeyError(f"AF selector file missing columns: {sorted(missing)}")

    for col in ["Name", "SectorGroup", "Sector", "EndUse", "COM_FR"]:
        df[col] = _clean_text(df[col])
    df["PeakAvailability"] = pd.to_numeric(df["PeakAvailability"], errors="raise")

    return df.drop_duplicates().reset_index(drop=True)


def load_baseyear_data(sector: str) -> pd.DataFrame:
    """Load the stage-2 baseyear table for the requested sector."""
    config = SECTOR_CONFIG[sector]
    df = pd.read_csv(config["baseyear_file"])

    for col in [
        "Sector",
        "SectorGroup",
        "DwellingType",
        "EndUse",
        "Process",
        "CommodityOut",
        "CommodityIn",
    ]:
        if col in df.columns:
            df[col] = _clean_text(df[col])

    df = df[df["Fuel"] == "Electricity"]

    return df


def get_electric_technologies_for_enduse(
    sector_group: str, sector: str, end_use: str
) -> pd.DataFrame:
    """
    Return the electricity processes and demand commodities serving a configured
    SectorGroup/Sector/EndUse selection.
    """
    config = SECTOR_CONFIG[sector_group]
    df = load_baseyear_data(sector_group)
    sector_column = config["sector_column"]

    matches = df[
        (df["SectorGroup"] == sector_group)
        & (df[sector_column].str.casefold() == sector.casefold())
        & (df["EndUse"].str.casefold() == end_use.casefold())
    ][["Process", "CommodityOut"]].drop_duplicates()

    if matches.empty:
        raise ValueError(
            "No electricity technologies found for "
            f"SectorGroup={sector_group}, Sector={sector}, EndUse={end_use}"
        )

    return matches.sort_values(["Process", "CommodityOut"]).reset_index(drop=True)


def load_curve_rows_from_code(sector_group: str, com_fr_code: str) -> pd.DataFrame:
    """
    Load the COM_FR rows for the explicitly configured COM_FR code.
    """
    config = SECTOR_CONFIG[sector_group]
    df = pd.read_csv(config["curve_file"])
    df["Cset_CN"] = _clean_text(df["Cset_CN"])
    df["TimeSlice"] = _clean_text(df["TimeSlice"])

    out = df[df["Cset_CN"] == com_fr_code].copy()
    if out.empty:
        raise ValueError(
            f"No COM_FR rows found for Cset_CN='{com_fr_code}'\n"
            f"All {sector_group} COM_FR entries in '{AF_SELECTOR_FILE.name}' "
            f"must be found in '{config['curve_file'].name}'.\n"
            f"Your COM_FR structure may have changed. Please review."
        )
    return out


def transform_com_fr_to_af_curve(
    curve_by_timeslice: pd.DataFrame, peak_availability: float
) -> pd.DataFrame:
    """
    Convert COM_FR shares into timeslice AF values.

    Method:
    1. Divide COM_FR by YRFR to get relative average output per hour in each slice.
    2. Scale the resulting curve so its maximum value is 1.
    3. Apply PeakAvailability so the peak slice equals that value.
    """
    if not 0 < peak_availability <= 1:
        raise ValueError(
            f"PeakAvailability must be > 0 and <= 1, got {peak_availability}"
        )

    yrfr = pd.read_csv(YRFR_FILE)
    yrfr["TimeSlice"] = _clean_text(yrfr["TimeSlice"])
    yrfr["Hours"] = yrfr["YRFR"] * 8760

    out = curve_by_timeslice.merge(
        yrfr, on="TimeSlice", how="left", validate="one_to_one"
    )
    missing_yrfr = out[out["YRFR"].isna()]["TimeSlice"].tolist()
    if missing_yrfr:
        raise ValueError(
            "Missing YRFR values for timeslices: " + ", ".join(missing_yrfr)
        )

    out["RelativeUtilisation"] = out["AllRegions"] / out["YRFR"]
    peak_utilisation = out["RelativeUtilisation"].max()
    if peak_utilisation <= 0:
        raise ValueError("Peak relative utilisation must be positive")

    out["AllRegions"] = (
        out["RelativeUtilisation"] / peak_utilisation * peak_availability
    )

    return out[["TimeSlice", "AllRegions"]].copy()


def validate_curve_grain(df: pd.DataFrame) -> pd.DataFrame:
    """
    Validate that the selected COM_FR rows are already at one row per timeslice.

    We intentionally fail loudly if the source grain is not exact
    """
    counts = df.groupby("TimeSlice").size()
    bad_counts = counts[counts != 1]
    if not bad_counts.empty:
        details = ", ".join(
            f"{timeslice} ({count} rows)" for timeslice, count in bad_counts.items()
        )
        raise ValueError(
            "Expected exactly one COM_FR row per TimeSlice, but found: " f"{details}"
        )

    expected_timeslices = 24
    if len(df) != expected_timeslices:
        raise ValueError(
            "Expected a full 24-timeslice COM_FR curve, " f"but found {len(df)} rows"
        )

    out = (
        df[["TimeSlice", "NI"]]
        .rename(columns={"NI": "AllRegions"})
        .sort_values("TimeSlice")
        .reset_index(drop=True)
    )

    return out


def wildcard_technology_codes(sector_group: str, technologies: list[str]) -> str:
    """
    Replace the technology component of a process code with "*".

    The position of the technology component is sector-specific, so this method
    uses an explicit token index from SECTOR_CONFIG rather than inferring it by
    comparing multiple base-year codes.
    """
    if not technologies:
        raise ValueError("Cannot wildcard an empty technology list")

    token_index = SECTOR_CONFIG[sector_group]["code_component_to_wildcard"]
    sample_code = sorted(set(technologies))[0]
    parts = sample_code.split("-")

    if token_index >= len(parts):
        raise ValueError(
            f"Technology token index {token_index} is out of range for code {sample_code}"
        )

    parts[token_index] = "*"
    return "-".join(parts)


def build_af_rows_for_group(
    output_code: str,
    curve_by_timeslice: pd.DataFrame,
    year: int = BASE_AF_YEAR,
    future_default_value: float = FUTURE_DEFAULT_VALUE,
    future_default_year: int = FUTURE_DEFAULT_YEAR,
) -> pd.DataFrame:
    """Build NCAP_AF rows for one wildcarded technology-group code."""
    base_rows = []
    future_rows = []

    tech_curve = curve_by_timeslice.copy()
    tech_curve["Attribute"] = AF_ATTRIBUTE
    tech_curve["Pset_PN"] = output_code
    tech_curve["Year"] = year
    tech_curve["LimType"] = LIMIT_TYPE
    base_rows.append(
        tech_curve[
            ["Attribute", "TimeSlice", "Pset_PN", "AllRegions", "Year", "LimType"]
        ]
    )

    future_curve = tech_curve.copy()
    future_curve["AllRegions"] = future_default_value
    future_curve["Year"] = future_default_year
    future_rows.append(future_curve)

    return pd.concat(base_rows + future_rows, ignore_index=True)


def build_afa_reset_rows(
    output_code: str,
    year: int = BASE_AF_YEAR,
    base_afa_value: float = BASE_AFA_VALUE,
    future_default_value: float = FUTURE_DEFAULT_VALUE,
    future_default_year: int = FUTURE_DEFAULT_YEAR,
) -> pd.DataFrame:
    """Build NCAP_AFA reset rows for one wildcarded technology-group code."""
    rows = [
        {
            "Attribute": AFA_ATTRIBUTE,
            "Pset_PN": output_code,
            "AllRegions": base_afa_value,
            "Year": year,
        },
        {
            "Attribute": AFA_ATTRIBUTE,
            "Pset_PN": output_code,
            "AllRegions": future_default_value,
            "Year": future_default_year,
        },
    ]

    return pd.DataFrame(rows)


def build_af_tables_for_selector(row) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build AF and AFA tables for one selector row."""
    sector_group = row.SectorGroup
    sector = row.Sector
    end_use = row.EndUse
    com_fr_code = row.COM_FR
    peak_availability = row.PeakAvailability

    if sector_group not in SECTOR_CONFIG:
        raise KeyError(f"Unsupported SectorGroup in AF selector file: {sector_group}")

    matches = get_electric_technologies_for_enduse(sector_group, sector, end_use)
    technologies = sorted(matches["Process"].unique().tolist())
    output_code = wildcard_technology_codes(sector_group, technologies)

    curve_rows = load_curve_rows_from_code(sector_group, com_fr_code)
    curve_by_timeslice = validate_curve_grain(curve_rows)
    af_curve = transform_com_fr_to_af_curve(curve_by_timeslice, peak_availability)

    af_df = build_af_rows_for_group(output_code, af_curve)
    afa_df = build_afa_reset_rows(output_code)

    return af_df, afa_df


def build_all_technology_af_curves() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Generate AF curves and AFA resets for all configured Sector/EndUse pairs."""
    selectors = load_af_selectors()

    af_frames = []
    afa_frames = []

    for row in selectors.itertuples(index=False):
        af_df, afa_df = build_af_tables_for_selector(row)
        af_frames.append(af_df)
        afa_frames.append(afa_df)

    af_df = (
        pd.concat(af_frames, ignore_index=True).drop_duplicates().reset_index(drop=True)
    )
    afa_df = (
        pd.concat(afa_frames, ignore_index=True)
        .drop_duplicates()
        .reset_index(drop=True)
    )

    return af_df, afa_df


def main() -> None:
    """Generate technology AF curves and companion AFA resets."""
    af_df, afa_df = build_all_technology_af_curves()

    save_output(af_df, "technology_af_curves.csv", "Technology NCAP_AF curves")
    save_output(afa_df, "technology_afa_resets.csv", "Technology NCAP_AFA resets")


if __name__ == "__main__":
    main()
