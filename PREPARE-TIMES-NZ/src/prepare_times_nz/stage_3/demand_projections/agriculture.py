"""
This module converts Agri, forest, fish input demand projection assumptions
 and compiles indices for all commodities and scenarios

A separate stage 4 module can extract these
 into the relevant demand scenario files

"""

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
def save_agr_proj_data(df, name, label):
    """save data wrapper"""
    label = "Saving ag, forest, and fish demand projections (" + label + ")"
    _save_data(df, name, label, filepath=OUTPUT)


def save_agr_proj_check(df, name, label):
    """save checking data wrapper"""
    label = "Saving ag, forest, and fish demand checks (" + label + ")"
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


def get_agriculture_growth_indices():
    """
    Creates yearly indices for agriculture sectors (2023–2050):

    - ERP sectors: linearly interpolate provided indices between anchor years
    - Constant sectors: expanded 2023–2050 with index = 1.0

    Returns long format: [SectorGroup, Sector, Year, Scenario, Index]
    """
    df0 = pd.read_csv(PROJECTIONS_ASSUMPTIONS / "agriculture_demand_projections.csv")
    df0 = df0[df0["SectorGroup"] == "Agriculture, Forestry and Fishing"].copy()

    # normalise method labels
    df0["Method"] = df0["Method"].astype(str).str.strip().str.title()

    group_vars = ["SectorGroup", "Sector"]
    year_var = "Year"
    value_cols = ["Traditional", "Transformation"]

    # split
    df_erp = df0[df0["Method"] == "Erp"].copy()
    df_const = df0[df0["Method"] == "Constant"].copy()

    # --- ERP: expand to full 2023–2050 and interpolate between anchor years ---
    if not df_erp.empty:
        # keep only 2023..2050 points from CSV
        df_erp = df_erp[(df_erp[year_var] >= 2023) & (df_erp[year_var] <= 2050)]

        # full grid per (SectorGroup, Sector) × Year
        groups = df_erp[group_vars].drop_duplicates()
        years = pd.DataFrame({year_var: range(2023, 2051)})
        full_erp = groups.merge(years, how="cross")

        # attach known ERP points
        full_erp = full_erp.merge(
            df_erp[group_vars + [year_var] + value_cols],
            on=group_vars + [year_var],
            how="left",
        )

        # interpolate within each group for each scenario
        full_erp = full_erp.sort_values(group_vars + [year_var])
        for col in value_cols:
            full_erp[col] = full_erp.groupby(group_vars, group_keys=False)[col].apply(
                lambda s: s.interpolate(method="linear").ffill().bfill()
            )
    else:
        full_erp = pd.DataFrame()

    # --- Constant: full 2023–2050 with index 1.0 ---
    if not df_const.empty:
        groups_c = df_const[group_vars].drop_duplicates()
        years = pd.DataFrame({year_var: range(2023, 2051)})
        full_const = groups_c.merge(years, how="cross")
        for col in value_cols:
            full_const[col] = 1.0
    else:
        full_const = pd.DataFrame()

    # combine and reshape
    full = pd.concat([full_erp, full_const], ignore_index=True)
    full = full.sort_values(group_vars + [year_var])

    out = full.melt(
        id_vars=group_vars + [year_var],
        value_vars=value_cols,
        var_name="Scenario",
        value_name="Index",
    )
    return out


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
