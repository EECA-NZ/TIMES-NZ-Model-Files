"""
This module converts Data Centre input demand projection assumptions
 and compiles indices for all commodities and scenarios

A separate stage 4 module can extract these
 into the relevant demand scenario files

"""

import numpy as np
import pandas as pd
from prepare_times_nz.stage_0.stage_0_settings import BASE_YEAR
from prepare_times_nz.utilities.data_in_out import _save_data
from prepare_times_nz.utilities.filepaths import ASSUMPTIONS, STAGE_2_DATA, STAGE_3_DATA

# CONSTANTS
# file paths
PROJECTIONS_ASSUMPTIONS = ASSUMPTIONS / "demand_projections"
OUTPUT = STAGE_3_DATA / "demand_projections"
OUTPUT_CHECKS = OUTPUT / "checks"
# end year setting
END_YEAR = 2050


# HELPERS
def save_dc_proj_data(df, name, label):
    """save data wrapper"""
    label = "Saving datacentre demand projections (" + label + ")"
    _save_data(df, name, label, filepath=OUTPUT)


def save_dc_proj_check(df, name, label):
    """save checking data wrapper"""
    label = "Saving datacentre demand checks (" + label + ")"
    _save_data(df, name, label, filepath=OUTPUT_CHECKS)


def expand_years(df, base_year=BASE_YEAR, end_year=END_YEAR):
    """
    Adds a time index 't' to an existing dataframe that already contains a 'Year' column.
    If some years are missing within the base-end range, fills them in via reindexing.
    Also fills in Sector and SectorGroup for expanded years.
    """

    # Ensure Year column exists
    if "Year" not in df.columns:
        raise ValueError("Dataframe must already have a 'Year' column")

    # Create full year range for expansion
    all_years = pd.DataFrame({"Year": range(base_year, end_year + 1)})

    # Merge to ensure all years exist
    df = all_years.merge(df, on="Year", how="left")

    # Fill Sector and SectorGroup for expanded years
    df["Sector"] = df["Sector"].ffill()  # Updated line
    df["SectorGroup"] = df["SectorGroup"].ffill()  # Updated line

    # Add time index (t = 0 for base_year)
    df["t"] = df["Year"] - base_year

    return df


# FUNCTIONS


# pylint: disable=too-many-locals
def get_datacentre_growth_indices(base_year=2023):
    """
    Creates yearly indices for Data Centres where capacities are specified at
    2023, 2030, 2035 for Traditional & Transformation.
      - Linear 2023→2030 and 2030→2035
      - Flat after 2035
      - Index(year) = cap(year) / cap(year-1); Index(2023) = 1
    Returns long format: [SectorGroup, Sector, Year, Scenario, Index]
    """

    # --- Load & filter ---
    df0 = pd.read_csv(PROJECTIONS_ASSUMPTIONS / "datacentre_demand_projections.csv")
    df0 = df0[(df0["Method"] == "Forecasting") & (df0["SectorGroup"] == "Commercial")]

    group_vars = ["SectorGroup", "Sector"]
    year_var = "Year"
    value_cols = ["Traditional", "Transformation"]

    # Sanity: we need anchor years present per group
    anchors_needed = {2023, 2030, 2035}
    have_anchors = (
        df0[df0[year_var].isin(anchors_needed)]
        .groupby(group_vars)[year_var]
        .apply(set)
        .reset_index(name="have")
    )
    missing = have_anchors[have_anchors["have"].apply(lambda s: s < anchors_needed)]
    if not missing.empty:
        # Give a helpful error if any group lacks an anchor
        missing_groups = missing[group_vars].to_dict(orient="records")
        raise ValueError(
            f"Missing required anchor years {sorted(anchors_needed)} "
            f"for some groups: {missing_groups}"
        )

    # --- Build full grid: all groups × all years ---
    all_groups = df0[group_vars].drop_duplicates()
    years = pd.DataFrame({year_var: range(2023, 2051)})
    full = all_groups.merge(years, how="cross")

    # Bring in original data (may only exist at anchor years initially)
    full = full.merge(
        df0[group_vars + [year_var] + value_cols],
        on=group_vars + [year_var],
        how="left",
    )

    # --- Collect anchors per group for each column and merge back ---
    # anchors_wide[col_2023, col_2030, col_2035] per group
    anchors = (
        df0[df0[year_var].isin([2023, 2030, 2035])]
        .set_index(group_vars + [year_var])[value_cols]
        .unstack(year_var)  # columns like ('Traditional', 2023) etc.
    )
    # Flatten the MultiIndex columns to e.g. Traditional_2023, Transformation_2030, etc.
    anchors.columns = [f"{c}_{y}" for c, y in anchors.columns]
    full = full.merge(anchors.reset_index(), on=group_vars, how="left")

    # --- Piecewise capacity fill ---
    y = full[year_var].to_numpy()

    for col in value_cols:
        c23 = full[f"{col}_2023"].to_numpy()
        c30 = full[f"{col}_2030"].to_numpy()
        c35 = full[f"{col}_2035"].to_numpy()

        r1 = (c30 - c23) / (2030 - 2023)  # 7 years
        r2 = (c35 - c30) / (2035 - 2030)  # 5 years

        cap = np.select(
            [
                y <= 2023,
                (y > 2023) & (y <= 2030),
                (y > 2030) & (y <= 2035),
                y > 2035,
            ],
            [
                c23,
                c23 + r1 * (y - 2023),
                c30 + r2 * (y - 2030),
                c35,  # flat tail
            ],
        )

        # write filled capacity back
        full[col] = cap

    # --- Base-year-relative indices per group ---
    full = full.sort_values(group_vars + [year_var])

    # Get base-year capacities per group for both scenarios in one merge
    base_caps = full[full[year_var] == base_year][group_vars + value_cols].rename(
        columns={c: f"{c}_base" for c in value_cols}
    )
    full = full.merge(base_caps, on=group_vars, how="left")

    for col in value_cols:
        idx_col = f"{col}_Index"
        base_col = f"{col}_base"

        # Index(y) = cap(y) / cap(base_year)
        # Safe divide: if base is 0 -> NaN (or choose a policy you prefer)
        full[idx_col] = np.where(
            full[base_col].astype(float) != 0.0,
            (full[col].astype(float) / full[base_col].astype(float)),
            np.nan,
        )

        # Enforce index = 1.0 at and before base year
        full.loc[full[year_var] <= base_year, idx_col] = 1.0

    # (optional) tidy up helper columns
    full = full.drop(columns=[f"{c}_base" for c in value_cols])

    # --- Long format output ---
    out = full.melt(
        id_vars=group_vars + [year_var],
        value_vars=[f"{c}_Index" for c in value_cols],
        var_name="Scenario",
        value_name="Index",
    )
    out["Scenario"] = out["Scenario"].str.replace("_Index$", "", regex=True)

    return out


def get_datacentre_baseyear_demand(var):
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

    df = pd.read_csv(STAGE_2_DATA / "commercial/baseyear_commercial_demand.csv")
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

    index = get_datacentre_growth_indices()
    base_year = get_datacentre_baseyear_demand(energy_type)
    df = base_year.merge(index, on="Sector", how="left")
    df["Value"] = df["Value"] * df["Index"]

    return df


def main():
    """Script entrypoint"""
    df_input_energy = get_energy_demand_projections("InputEnergy")
    df_output_energy = get_energy_demand_projections("OutputEnergy")
    save_dc_proj_check(df_input_energy, "datacentre_input.csv", "Input energy")
    save_dc_proj_check(df_output_energy, "datacentre_output.csv", "Output energy")

    # the above is extra detail for reporting. The model just needs indices:

    df_index = get_datacentre_growth_indices()
    save_dc_proj_data(
        df_index, "datacentre_demand_index.csv", "Datacentre demand index"
    )


if __name__ == "__main__":
    main()
