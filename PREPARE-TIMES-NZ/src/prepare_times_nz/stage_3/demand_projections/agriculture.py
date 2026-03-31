"""
This module converts Agri, forest, fish input demand projection assumptions
 and compiles indices for all commodities and scenarios

A separate stage 4 module can extract these
 into the relevant demand scenario files

"""

from pathlib import Path

import pandas as pd
from prepare_times_nz.stage_0.stage_0_settings import BASE_YEAR
from prepare_times_nz.utilities.data_in_out import _save_data
from prepare_times_nz.utilities.filepaths import (
    ASSUMPTIONS,
    EXTERNAL_DATA,
    STAGE_2_DATA,
    STAGE_3_DATA,
)

# CONSTANTS
# file paths
PROJECTIONS_ASSUMPTIONS = ASSUMPTIONS / "demand_projections"
OUTPUT = STAGE_3_DATA / "demand_projections"
OUTPUT_CHECKS = OUTPUT / "checks"
# end year setting
END_YEAR = 2050
ASSUMPTIONS_FILE = PROJECTIONS_ASSUMPTIONS / "agriculture_demand_projections.csv"


# HELPERS
def save_agr_proj_data(df, name, label):
    """save data wrapper"""
    label = "Saving ag, forest, and fish demand projections (" + label + ")"
    _save_data(df, name, label, filepath=OUTPUT)


def save_agr_proj_check(df, name, label):
    """save checking data wrapper"""
    label = "Saving ag, forest, and fish demand checks (" + label + ")"
    _save_data(df, name, label, filepath=OUTPUT_CHECKS)


def normalise_optional_text(value):
    """Return stripped text or None for blanks/NaN-like values."""
    if pd.isna(value):
        return None
    text = str(value).strip()
    return text or None


def load_agriculture_projection_assumptions(assumptions_path=ASSUMPTIONS_FILE):
    """Load agriculture projection mappings and validate expected columns."""
    df = pd.read_csv(assumptions_path).copy()
    df = df[df["SectorGroup"] == "Agriculture, Forestry and Fishing"].copy()

    required_cols = {
        "SectorGroup",
        "Sector",
        "Scenario",
        "Method",
        "Workbook",
        "SheetName",
        "SourceCategory1",
        "SourceCategory2",
        "ConstantIndex",
        "Note",
    }
    missing_cols = required_cols.difference(df.columns)
    if missing_cols:
        raise ValueError(
            "Agriculture demand projection assumptions are missing columns: "
            + ", ".join(sorted(missing_cols))
        )

    df["Scenario"] = df["Scenario"].astype(str).str.strip().str.title()
    df["Method"] = df["Method"].astype(str).str.strip().str.title()
    df["Workbook"] = df["Workbook"].apply(normalise_optional_text)
    df["SheetName"] = df["SheetName"].apply(normalise_optional_text)
    df["SourceCategory1"] = df["SourceCategory1"].apply(normalise_optional_text)
    df["SourceCategory2"] = df["SourceCategory2"].apply(normalise_optional_text)
    df["ConstantIndex"] = pd.to_numeric(df["ConstantIndex"], errors="coerce")

    duplicates = df.duplicated(["SectorGroup", "Sector", "Scenario"], keep=False)
    if duplicates.any():
        duplicate_rows = df.loc[duplicates, ["SectorGroup", "Sector", "Scenario"]]
        raise ValueError(
            "Duplicate agriculture demand projection mappings found:\n"
            + duplicate_rows.to_string(index=False)
        )

    return df


def load_workbook_projection_sheet(workbook_path, sheet_name):
    """
    Load one ERP2 projection sheet.

    The workbook stores years as columns, with the first two columns acting as
    row identifiers for the projection categories.
    """
    df = pd.read_excel(workbook_path, sheet_name=sheet_name, header=5)
    first_two_cols = list(df.columns[:2])
    df = df.rename(
        columns={
            first_two_cols[0]: "SourceCategory1",
            first_two_cols[1]: "SourceCategory2",
        }
    )

    rename_map = {}
    for col in df.columns:
        if isinstance(col, float) and col.is_integer():
            rename_map[col] = int(col)
    df = df.rename(columns=rename_map)

    year_cols = [
        col
        for col in df.columns
        if isinstance(col, int) and BASE_YEAR <= col <= END_YEAR
    ]
    if not year_cols:
        raise ValueError(
            f"No year columns between {BASE_YEAR} and {END_YEAR} found in "
            f"{workbook_path} [{sheet_name}]"
        )

    return df[["SourceCategory1", "SourceCategory2"] + year_cols].copy()


def get_cached_workbook_projection_sheet(mapping_row, sheet_cache, external_data_dir):
    """Return a cached ERP2 worksheet dataframe for the configured mapping row."""
    workbook_path = Path(external_data_dir) / mapping_row["Workbook"]
    cache_key = (str(workbook_path), mapping_row["SheetName"])
    if cache_key not in sheet_cache:
        sheet_cache[cache_key] = load_workbook_projection_sheet(
            workbook_path, mapping_row["SheetName"]
        )
    return sheet_cache[cache_key].copy()


def select_projection_match(df, mapping_row):
    """Select the single workbook row that matches the configured categories."""
    mask = pd.Series(True, index=df.index)
    for column in ["SourceCategory1", "SourceCategory2"]:
        value = mapping_row[column]
        if value is not None:
            mask &= df[column].astype(str).str.strip().eq(value)

    matches = df.loc[mask].copy()
    mapping_details = (
        f"{mapping_row['Sector']} / {mapping_row['Scenario']} "
        f"using [{mapping_row['SourceCategory1']!r}, {mapping_row['SourceCategory2']!r}] "
        f"in {mapping_row['Workbook']} [{mapping_row['SheetName']}]"
    )
    if matches.empty:
        raise ValueError(
            "No ERP2 workbook row matched agriculture projection mapping for "
            + mapping_details
        )
    if len(matches) > 1:
        raise ValueError(
            "Multiple ERP2 workbook rows matched agriculture projection mapping for "
            + mapping_details
        )
    return matches.iloc[0]


def build_projection_index_frame(match_row, mapping_row):
    """Convert a matched workbook row into a base-year index dataframe."""
    year_cols = [col for col in match_row.index if isinstance(col, int)]
    values = pd.to_numeric(match_row[year_cols], errors="coerce")
    if pd.isna(values.get(BASE_YEAR)) or values[BASE_YEAR] == 0:
        raise ValueError(
            "Cannot compute agriculture projection index because the base-year value "
            f"is missing or zero for {mapping_row['Sector']} / {mapping_row['Scenario']}"
        )

    out = pd.DataFrame({"Year": year_cols, "Index": values.values / values[BASE_YEAR]})
    out["SectorGroup"] = mapping_row["SectorGroup"]
    out["Sector"] = mapping_row["Sector"]
    out["Scenario"] = mapping_row["Scenario"]
    return out[["SectorGroup", "Sector", "Scenario", "Year", "Index"]]


def get_workbook_projection_indices(
    mapping_row, sheet_cache, external_data_dir=EXTERNAL_DATA
):
    """Read one configured ERP2 row and convert it to a base-year index series."""
    df = get_cached_workbook_projection_sheet(
        mapping_row, sheet_cache, external_data_dir
    )
    match_row = select_projection_match(df, mapping_row)
    return build_projection_index_frame(match_row, mapping_row)


def get_constant_projection_indices(mapping_row):
    """Create a flat constant projection series from configuration."""
    constant_index = mapping_row["ConstantIndex"]
    if pd.isna(constant_index):
        raise ValueError(
            f"ConstantIndex is required for constant agriculture mapping: {mapping_row['Sector']}"
        )

    out = pd.DataFrame({"Year": range(BASE_YEAR, END_YEAR + 1)})
    out["Index"] = float(constant_index)
    out["SectorGroup"] = mapping_row["SectorGroup"]
    out["Sector"] = mapping_row["Sector"]
    out["Scenario"] = mapping_row["Scenario"]

    return out[["SectorGroup", "Sector", "Scenario", "Year", "Index"]]


def expand_projection_indices(df):
    """Expand projection rows to a full annual series and interpolate missing years."""
    group_vars = ["SectorGroup", "Sector", "Scenario"]
    years = pd.DataFrame({"Year": range(BASE_YEAR, END_YEAR + 1)})
    groups = df[group_vars].drop_duplicates()

    full = groups.merge(years, how="cross")
    full = full.merge(df, on=group_vars + ["Year"], how="left")
    full = full.sort_values(group_vars + ["Year"])
    full["Index"] = full.groupby(group_vars, group_keys=False)["Index"].apply(
        lambda s: s.interpolate(method="linear").ffill().bfill()
    )

    return full[group_vars + ["Year", "Index"]]


# FUNCTIONS
def get_agriculture_growth_indices(
    assumptions_path=ASSUMPTIONS_FILE, external_data_dir=EXTERNAL_DATA
):
    """
    Build agriculture demand indices from a mapping config.

    Each row in the assumptions CSV maps a TIMES-NZ sector/scenario either to:
    - a workbook row in the ERP2 detailed results workbook, or
    - a constant index for sectors that remain flat
    """
    mappings = load_agriculture_projection_assumptions(assumptions_path)
    sheet_cache = {}
    projection_parts = []

    for _, mapping_row in mappings.iterrows():
        method = mapping_row["Method"]
        if method == "Workbook":
            projection_parts.append(
                get_workbook_projection_indices(
                    mapping_row,
                    sheet_cache=sheet_cache,
                    external_data_dir=external_data_dir,
                )
            )
        elif method == "Constant":
            projection_parts.append(get_constant_projection_indices(mapping_row))
        else:
            raise ValueError(
                f"Unsupported agriculture demand projection method: {method}"
            )

    combined = pd.concat(projection_parts, ignore_index=True)
    duplicates = combined.duplicated(
        ["SectorGroup", "Sector", "Scenario", "Year"], keep=False
    )
    if duplicates.any():
        duplicate_rows = combined.loc[
            duplicates, ["SectorGroup", "Sector", "Scenario", "Year"]
        ]
        raise ValueError(
            "Duplicate agriculture demand projection rows found after compilation:\n"
            + duplicate_rows.to_string(index=False)
        )

    return expand_projection_indices(combined)


def get_agriculture_baseyear_demand(var):
    """
    Pull base year commodity outputs by sector
    Get total base year service demand and energy demand
    Include sector, tech, and enduse labels

    variable must be one of InputEnergy, OutputEnergy
    """
    if var not in ["OutputEnergy", "InputEnergy"]:
        raise ValueError(
            f"Invalid variable '{var}'. Must be 'InputEnergy' or 'OutputEnergy'."
        )

    df = pd.read_csv(STAGE_2_DATA / "ag_forest_fish/baseyear_ag_forest_fish_demand.csv")
    df = df[df["Variable"] == var]
    df = (
        df.groupby(
            [
                "Sector",
                "CommodityOut",
                "Island",
                "Technology",
                "EndUse",
                "Variable",
                "Unit",
            ]
        )["Value"]
        .sum()
        .reset_index()
    )
    return df


def get_energy_demand_projections(energy_type):
    """
    Combine base year demand (input or output) and growth indices
    Create forward projections based on these
    Note that Output energy is required for the model
    InputEnergy is sometimes useful for communication purposes
    """

    index = get_agriculture_growth_indices()
    base_year = get_agriculture_baseyear_demand(energy_type)
    df = base_year.merge(index, on="Sector", how="left")
    df["Value"] = df["Value"] * df["Index"]

    return df


def main():
    """Script entrypoint"""
    df_input_energy = get_energy_demand_projections("InputEnergy")
    df_output_energy = get_energy_demand_projections("OutputEnergy")
    save_agr_proj_check(df_input_energy, "agriculture_input.csv", "Input energy")
    save_agr_proj_check(df_output_energy, "agriculture_output.csv", "Output energy")

    # the above is extra detail for reporting. The model just needs indices:

    df_index = get_agriculture_growth_indices()
    save_agr_proj_data(
        df_index, "agriculture_demand_index.csv", "Agriculture demand index"
    )


if __name__ == "__main__":
    main()
