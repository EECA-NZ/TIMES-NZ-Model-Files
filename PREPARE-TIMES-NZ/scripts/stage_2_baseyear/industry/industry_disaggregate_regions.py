"""

This script takes the TIMES sector industrial demand outputs
and applies the sectoral and fuel regional share assumptions
to calculate regional shares

This is moderately complex: share assumptions are applied by
default per sector
However, natural gas and geothermal assumptions are also
applied to be 100% NI
This can lead to infeasibilities if we say that 60% of a sector
is SI, but all its process heat is natural gas - it doesn't add
up.

We can further apply overrides to specific sector/fuel combinations

The script takes all of these possibilities and ensure the
shares balance within the chosen category.

Effectively, depending on the category chosen (for example,
Technology)
we assume the share of that category within the sector is
balanced for each subsector between regions

For example: 70% Dairy NI means 70% Dairy boiler use is NI,
etc - so the fuels must balance for each of these.

Pay attention to the checking outputs. Various reports on the
results are generated, and infeasible results are possible
which may require adjustments to input assumptions.


The script follows these rules:

    * Sector-level default regional shares are applied first.
    * Fuel-level (and fuel-by-sector) overrides can force certain fuels to
      North Island (NI) or South Island (SI) shares (e.g., geothermal,
      natural-gas → 100 % NI).
    * The script rebalances any remaining fuels so the total per sector (and
      per grouping category) still matches the intended sector share.
    * Optional “tests” can be run to report infeasible or adjusted shares.

The output is written to STAGE_2_DATA/industry/preprocessing, with detailed
check files in STAGE_2_DATA/industry/checks/2_region_disaggregation.

Layout:
    - Imports
    - Constants / file paths
    - Helper functions
    - Calculation pipeline
    - Tests / reporting helpers
    - main()
    - "__main__" guard
"""

# --------------------------------------------------------------------------- #
# Imports
# --------------------------------------------------------------------------- #
import os

import pandas as pd
from prepare_times_nz.utilities.filepaths import ASSUMPTIONS, STAGE_2_DATA
from prepare_times_nz.utilities.logger_setup import blue_text, h2, logger

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #
# Toggle extra checks / verbose output
RUN_TESTS = False
if RUN_TESTS:
    logger.info("Including test outputs")
else:
    logger.info("Not running tests")

# Grouping column used when balancing shares.  Typical options: Technology,
# EndUse, etc.  Within each subsector, the NI/SI fuel shares will balance for
# each unique value in this column.
GROUP_USED = "Technology"
logger.info("Will calculate group shares using '%s'", GROUP_USED)

# --------------------------------------------------------------------------- #
# File-paths
# --------------------------------------------------------------------------- #
OUTPUT_LOCATION = f"{STAGE_2_DATA}/industry/preprocessing"
os.makedirs(OUTPUT_LOCATION, exist_ok=True)

CHECKS_LOCATION = f"{STAGE_2_DATA}/industry/checks/2_region_disaggregation"
os.makedirs(CHECKS_LOCATION, exist_ok=True)

# --------------------------------------------------------------------------- #
# Data – loaded at import so default arguments work unchanged
# --------------------------------------------------------------------------- #
baseyear_industry = pd.read_csv(
    f"{OUTPUT_LOCATION}/1_times_eeud_alignment_baseyear.csv"
)

# Assumption tables
regional_splits_by_sector = pd.read_csv(
    f"{ASSUMPTIONS}/industry_demand/regional_splits_by_sector.csv"
)
regional_splits_by_fuel = pd.read_csv(
    f"{ASSUMPTIONS}/industry_demand/regional_splits_by_fuel.csv"
)
regional_splits_by_sector_and_fuel = pd.read_csv(
    f"{ASSUMPTIONS}/industry_demand/regional_splits_by_sector_and_fuel.csv"
)


# --------------------------------------------------------------------------- #
# Helper functions
# --------------------------------------------------------------------------- #
def save_output(df: pd.DataFrame, name: str) -> None:
    """Save a DataFrame to the preprocessing output folder."""
    filename = f"{OUTPUT_LOCATION}/{name}"
    logger.info("Saving output:\n%s", blue_text(filename))
    df.to_csv(filename, index=False)


def save_checks(df: pd.DataFrame, name: str, label: str) -> None:
    """Save a DataFrame to the checks folder with a log message."""
    filename = f"{CHECKS_LOCATION}/{name}"
    logger.info("Saving %s:\n%s", label, blue_text(filename))
    df.to_csv(filename, index=False)


def get_usage_shares(df: pd.DataFrame, *, group_used: str = GROUP_USED) -> pd.DataFrame:
    """Return the share of each fuel within (Sector, group) total."""
    df = df.groupby(["Sector", group_used, "Fuel"])["Value"].sum().reset_index()
    df["TotalPerGroup"] = df.groupby(["Sector", group_used])["Value"].transform("sum")
    df["FuelShareOfGroup"] = df["Value"] / df["TotalPerGroup"]
    return df


def add_sector_default_shares(df: pd.DataFrame) -> pd.DataFrame:
    """Attach default NI shares at sector level."""
    sector_shares = regional_splits_by_sector[["Sector", "NI_Share"]].copy()
    sector_shares = sector_shares.rename(columns={"NI_Share": "NIShareSector"})
    return pd.merge(df, sector_shares, on="Sector")


def add_fuel_default_shares(df: pd.DataFrame) -> pd.DataFrame:
    """Attach default NI shares at fuel level (override candidate)."""
    fuel_shares = regional_splits_by_fuel[["Fuel", "NI_Share"]].copy()
    fuel_shares = fuel_shares.rename(columns={"NI_Share": "NIShareFuelOverride"})
    return pd.merge(df, fuel_shares, on="Fuel", how="left")


def add_fuel_sector_default_shares(df: pd.DataFrame) -> pd.DataFrame:
    """
    Attach fuel-by-sector overrides (highest priority).  If present, they
    replace the simple fuel override.
    """
    sector_fuel_shares = regional_splits_by_sector_and_fuel.rename(
        columns={"NI_Share": "NIShareSectorFuelOverride"}
    )
    df = pd.merge(df, sector_fuel_shares, on=["Sector", "Fuel"], how="left")

    # Overwrite more generic override where specific override exists
    df["NIShareFuelOverride"] = df["NIShareSectorFuelOverride"].fillna(
        df["NIShareFuelOverride"]
    )
    return df  # keeping extra columns for diagnostics


def define_override_shares(
    df: pd.DataFrame, *, group_used: str = GROUP_USED
) -> pd.DataFrame:
    """Calculate weighted overrides and flags."""
    df["WeightedOverride"] = df["FuelShareOfGroup"] * df["NIShareFuelOverride"]
    df["OverrideShareOfGroup"] = df.groupby(["Sector", group_used])[
        "WeightedOverride"
    ].transform("sum")
    df["UsesOverride"] = ~df["NIShareFuelOverride"].isna()
    return df


def calculate_override_adjustments(
    df: pd.DataFrame, *, group_used: str = GROUP_USED
) -> pd.DataFrame:
    """
    Adjust sector default shares upward where overrides force a higher NI share
    than originally assumed.
    """
    df["NIShareSectorAdjusted"] = df[["OverrideShareOfGroup", "NIShareSector"]].max(
        axis=1
    )

    # Remaining NI value to assign within this (Sector, group)
    df["LeftToAssignFuel"] = (
        df["NIShareSectorAdjusted"] - df["OverrideShareOfGroup"]
    ) * df["TotalPerGroup"]

    # Portion of each fuel still free to be assigned after overrides
    df["StillNeedsAssigning"] = df["Value"] - (
        df["Value"] * df["NIShareFuelOverride"].fillna(0)
    )

    # Protected fuels (with overrides) cannot receive further assignment
    df.loc[df["UsesOverride"], "StillNeedsAssigning"] = 0

    # Share of residual NI allocation each unprotected fuel receives
    df["StillNeedsAssigningShare"] = df["StillNeedsAssigning"] / df.groupby(
        ["Sector", group_used]
    )["StillNeedsAssigning"].transform("sum")
    df["StillNeedsAssigningShare"] = df["StillNeedsAssigningShare"].fillna(0)

    return df


def get_final_adjusted_shares(df: pd.DataFrame) -> pd.DataFrame:
    """
    Combine override assignment and residual balancing to produce final NI/SI
    split per record.
    """
    df["NIValueAssigned"] = df["LeftToAssignFuel"] * df["StillNeedsAssigningShare"]
    df["NIValueOverride"] = df["NIShareFuelOverride"].fillna(0) * df["Value"]

    df["NIValue"] = df["NIValueAssigned"] + df["NIValueOverride"]
    df["SIValue"] = df["Value"] - df["NIValue"]
    return df


def summarise_shares(df: pd.DataFrame, *, group_used: str = GROUP_USED) -> pd.DataFrame:
    """Return a compact table with NIShare for merge onto main dataframe."""
    df = (
        df.groupby(["Sector", group_used, "Fuel"])[["Value", "NIValue"]]
        .sum()
        .reset_index()
    )
    df["NIShare"] = df["NIValue"] / df["Value"]

    # Replace NaNs (arise when Value == 0) by sector defaults for completeness
    df = add_sector_default_shares(df)
    df["NIShare"] = df["NIShare"].fillna(df["NIShareSector"])
    return df.drop(columns=["Value", "NIValue", "NIShareSector"])


def apply_shares_to_main_dataframe(
    df: pd.DataFrame,
    *,
    main_df: pd.DataFrame = baseyear_industry,
    tolerance: int = 8,
) -> pd.DataFrame:
    """
    Join calculated NIShare onto the main TIMES base-year dataframe and
    translate into NI / SI values (rounded for FP stability).
    """
    shares = summarise_shares(df)
    df = pd.merge(main_df, shares, on=["Sector", GROUP_USED, "Fuel"], how="left")

    df["NI"] = round(df["Value"] * df["NIShare"], tolerance)
    df["SI"] = abs(round(df["Value"] - df["NI"], tolerance))
    return df


def tidy_data(df: pd.DataFrame) -> pd.DataFrame:
    """Drop helper columns and pivot NI/SI into a Region column."""
    df = df.drop(["Value", "NIShare"], axis=1)

    cols_to_melt = ["NI", "SI"]
    id_cols = [col for col in df.columns if col not in cols_to_melt]
    df = df.melt(
        id_vars=id_cols, value_vars=cols_to_melt, var_name="Region", value_name="Value"
    )

    # Remove explicit zeros (e.g., SI natural gas if all NG assumed 100 % NI)
    return df[df["Value"] != 0]


# --------------------------------------------------------------------------- #
# Tests / Reporting helpers (unchanged except for quoting fix)
# --------------------------------------------------------------------------- #
def report_adjusted_weights(df: pd.DataFrame) -> pd.DataFrame:
    """Log and save any (Sector, group) where defaults were adjusted."""
    df = df[df["NIShareSectorAdjusted"] != df["NIShareSector"]]

    cols = [
        "Sector",
        GROUP_USED,
        "Fuel",
        "NIShareSector",
        "NIShareSectorAdjusted",
        "UsesOverride",
    ]
    save_checks(
        df[cols], "regional_share_adjustments.csv", "regional share adjustments made"
    )

    summary = df[
        ["Sector", GROUP_USED, "NIShareSector", "NIShareSectorAdjusted"]
    ].drop_duplicates()
    logger.warning(
        "The following items for each %s have had default shares adjusted "
        "so that fuel shares align with provided overrides:",
        GROUP_USED,
    )
    for _, row in summary.iterrows():
        sector = row["Sector"]
        group = row[GROUP_USED]
        original = round(row["NIShareSector"] * 100, 2)
        adjusted = round(row["NIShareSectorAdjusted"] * 100, 2)

        logger.warning(
            "      %s (%s): Share was adjusted from %s %% to %s %%",
            sector,
            group,
            original,
            adjusted,
        )
    return df


def report_aggregate_subsector_shares(df: pd.DataFrame) -> None:
    """
    Compare adjusted sector-level NI shares with the original defaults.
    """
    shares = df.groupby("Sector")[["Value", "NIValue", "SIValue"]].sum().reset_index()
    shares["AdjustedShare"] = shares["NIValue"] / shares["Value"]

    default_shares = regional_splits_by_sector[["Sector", "NI_Share"]].rename(
        columns={"NI_Share": "DefaultShare"}
    )
    shares = pd.merge(shares, default_shares, on="Sector")
    shares["ShareDifference"] = abs(shares["DefaultShare"] - shares["AdjustedShare"])

    differing = shares[shares["ShareDifference"] > 1e-4]
    if not differing.empty:
        logger.warning("The following sector share adjustments have been made:")
        for _, row in differing.iterrows():
            default_pct = round(row["DefaultShare"] * 100, 0)
            adjusted_pct = round(row["AdjustedShare"] * 100, 3)
            logger.warning(
                "      %s: Share was adjusted from %s %% to %s %%",
                row["Sector"],
                default_pct,
                adjusted_pct,
            )

    save_checks(
        shares[["Sector", "DefaultShare", "AdjustedShare"]],
        "sector_share_adjustments.csv",
        "sector share adjustments",
    )


def report_sector_fuel_shares_feasible(df: pd.DataFrame) -> None:
    """Check all calculated NI shares are within [0, 1]."""
    logger.info("Testing North Island fuel shares are feasible:")
    error_counter = 0

    for sector in df["Sector"]:
        df_sector = df[df["Sector"] == sector]
        for _, row in df_sector.iterrows():
            for fuel, val in row["Share"].items():
                if pd.notna(val):
                    val_round = round(val, 6)
                    val_str = f"{round(val * 100, 2)}%"
                    if (val_round > 1) or (val_round < 0):
                        error_counter += 1
                        logger.warning(
                            "             %s use of %s is "
                            "{red_text('IMPOSSIBLE')} at {red_text(%s)}!",
                            fuel,
                            sector,
                            val_str,
                        )
    if error_counter == 0:
        logger.info("             All values are feasible :)")


def report_sector_fuel_shares(df: pd.DataFrame) -> None:
    """Pivot NI shares by (Sector, Fuel) for inspection and save to checks."""
    shares = (
        df.groupby(["Sector", "Fuel"])[["Value", "NIValue", "SIValue"]]
        .sum()
        .reset_index()
    )
    shares["Share"] = shares["NIValue"] / shares["Value"]
    shares["Share"] = shares["Share"].fillna(0)

    pivot = pd.pivot(
        shares[["Sector", "Fuel", "Share"]], index="Sector", columns="Fuel"
    )
    report_sector_fuel_shares_feasible(pivot)

    save_checks(pivot.reset_index(), "fuel_sector_shares.csv", "fuel sector shares")

    logger.info("Fuel and Sector North Island share results:")
    printable = (pivot * 100).round(2).astype(str).replace("nan", "")
    printable["Sector"] = printable.index
    print(printable)


# --------------------------------------------------------------------------- #
# Calculation orchestration
# --------------------------------------------------------------------------- #
def calculate_shares(df: pd.DataFrame) -> pd.DataFrame:
    """
    Pipeline to compute final NI/SI disaggregation:
        1. Aggregate original usage for share weights.
        2. Attach sector defaults and fuel overrides.
        3. Re-balance remaining fuels.
        4. Optionally run diagnostic reports.
        5. Merge shares onto main dataframe and tidy result.
    """
    df_calc = (
        df.pipe(get_usage_shares)
        .pipe(add_sector_default_shares)
        .pipe(add_fuel_default_shares)
        .pipe(add_fuel_sector_default_shares)
        .pipe(define_override_shares)
        .pipe(calculate_override_adjustments)
        .pipe(get_final_adjusted_shares)
    )

    if RUN_TESTS:
        h2("Testing industrial demand shares")
        report_adjusted_weights(df_calc)
        report_aggregate_subsector_shares(df_calc)
        report_sector_fuel_shares(df_calc)

    save_checks(
        df_calc,
        "full_industrial_share_calculations.csv",
        "all regional share calculations",
    )

    result = df_calc.pipe(apply_shares_to_main_dataframe).pipe(tidy_data)
    return result


# --------------------------------------------------------------------------- #
# main()
# --------------------------------------------------------------------------- #
def main() -> None:
    """
    Entry point for script execution.  Calculates regional split and saves the
    primary output CSV.
    """
    logger.info("Starting regional disaggregation for industrial demand.")
    df_out = calculate_shares(baseyear_industry)
    save_output(df_out, "2_times_baseyear_regional_disaggregation.csv")
    logger.info("Regional disaggregation complete.")


# --------------------------------------------------------------------------- #
# "__main__" guard
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    main()
