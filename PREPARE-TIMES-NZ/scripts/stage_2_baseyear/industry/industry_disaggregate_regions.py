"""

This script takes the TIMES sector industrial demand outputs and applies the sectoral and fuel regional share assumptions to calculate regional shares

This is moderately complex: share assumptions are applied by default per sector
However, natural gas and geothermal assumptions are also appplied to be 100% NI
This can lead to infeasibilities if we say that 60% of a sector is SI, but all its process heat is natural gas - it doesn't add up.

We can further apply overrides to specific sector/fuel combinations

The script takes all of these possibilities and ensure the shares balance within the chosen category.

Effectively, depending on the category chosen (for example, Technology)
we assume the share of that category within the sector is balanced for each subsector between regions

For example: 70% Dairy NI means 70% Dairy boiler use is NI, etc - so the fuels must balance for each of these.

Pay attention to the checking outputs. Various reports on the results are generated, and infeasible results are possible which may require adjustments to
input assumptions.


"""

import os

import pandas as pd
from prepare_times_nz.filepaths import ASSUMPTIONS, STAGE_2_DATA
from prepare_times_nz.logger_setup import blue_text, h2, logger, red_text

# Constants ---------------------------------------------------------

run_tests = False
if run_tests:
    logger.info("Including test outputs")
else:
    logger.info("Not running tests")

# This defines which groups we calculate the shares for. Within each subsector, the regional shares should match for each of these groups
# Note that sometimes this won't be feasible and we have to adjust some groups (eg if all the heating is natural gas it becomes all NI, no matter the sector share)
group_used = "Technology"
logger.info(f"Will calculate group shares using '{group_used}'")


# Filepaths  -----------------------------------------
output_location = f"{STAGE_2_DATA}/industry/preprocessing"
os.makedirs(output_location, exist_ok=True)

checks_location = f"{STAGE_2_DATA}/industry/checks/2_region_disaggregation"
os.makedirs(checks_location, exist_ok=True)


# Get data ---------------------------------------------------------

baseyear_industry = pd.read_csv(
    f"{output_location}/1_times_eeud_alignment_baseyear.csv"
)

# Assumptions

regional_splits_by_sector = pd.read_csv(
    f"{ASSUMPTIONS}/industry_demand/regional_splits_by_sector.csv"
)
regional_splits_by_fuel = pd.read_csv(
    f"{ASSUMPTIONS}/industry_demand/regional_splits_by_fuel.csv"
)
regional_splits_by_sector_and_fuel = pd.read_csv(
    f"{ASSUMPTIONS}/industry_demand/regional_splits_by_sector_and_fuel.csv"
)


# Functions -------------------------------------------------------------------


def save_output(df, name):

    filename = f"{output_location}/{name}"
    logger.info(f"Saving output:\n{blue_text(filename)}")
    df.to_csv(filename, index=False)


def save_checks(df, name, label):
    filename = f"{checks_location}/{name}"
    logger.info(f"Saving {label}:\n{blue_text(filename)}")
    df.to_csv(filename, index=False)


def get_usage_shares(df, group_used=group_used):
    """
    Return the share of fuel used per sector and use group
    """
    df = df.groupby(["Sector", group_used, "Fuel"])["Value"].sum().reset_index()
    df["TotalPerGroup"] = df.groupby(["Sector", group_used])["Value"].transform("sum")
    df["FuelShareOfGroup"] = df["Value"] / df["TotalPerGroup"]

    return df


def add_sector_default_shares(df):
    """
    Attach the default sector shares. These may be overwritten per fuel and are required to rebalance the disaggregation
    """
    sector_shares = regional_splits_by_sector[["Sector", "NI_Share"]].copy()
    sector_shares = sector_shares.rename(columns={"NI_Share": "NIShareSector"})

    df = pd.merge(df, sector_shares, on="Sector")
    return df


def add_fuel_default_shares(df):
    """
    Attach the default fuel shares
    """
    sector_shares = regional_splits_by_fuel[["Fuel", "NI_Share"]].copy()
    sector_shares = sector_shares.rename(columns={"NI_Share": "NIShareFuelOverride"})

    df = pd.merge(df, sector_shares, on="Fuel", how="left")
    return df


def add_fuel_sector_default_shares(df):
    """
    Attach the fuel_sector shares
    these should replace the NIShareFuelOverride if the join succeeds - effectively a specific override
    """
    sector_fuel_shares = regional_splits_by_sector_and_fuel
    sector_fuel_shares = sector_fuel_shares.rename(
        columns={"NI_Share": "NIShareSectorFuelOverride"}
    )

    df = pd.merge(df, sector_fuel_shares, on=["Sector", "Fuel"], how="left")

    # Overwriting
    df["NIShareFuelOverride"] = df["NIShareSectorFuelOverride"].fillna(
        df["NIShareFuelOverride"]
    )
    # remove the junk field ? Let's keep it just for fun and see what breaks
    # hopefully nothing
    return df


def define_override_shares(df, group_used=group_used):
    # We first use the default shares to assign default fuels
    df["WeightedOverride"] = df["FuelShareOfGroup"] * df["NIShareFuelOverride"]
    # we then get the total of these to find the currently assigned fuel for each group
    df["OverrideShareOfGroup"] = df.groupby(["Sector", group_used])[
        "WeightedOverride"
    ].transform("sum")
    # Add boolean for checking if a fuel uses an override or not
    df["UsesOverride"] = ~df["NIShareFuelOverride"].isna()

    return df


def calculate_override_adjustments(df, group_used=group_used):

    # We want to adjust the shares for some groups if the override shares don't match (like meat rendering is more in NI or whatever)
    # If the NI override share is too high for a group we just adjust it up
    # This comes out in the reporting if tests are enabled

    df["NIShareSectorAdjusted"] = df[["OverrideShareOfGroup", "NIShareSector"]].max(
        axis=1
    )
    # use the override share in each group to calculate the fuel left to assign to the group from the fuels with no override
    df["LeftToAssignFuel"] = (
        df["NIShareSectorAdjusted"] - df["OverrideShareOfGroup"]
    ) * df["TotalPerGroup"]

    # For the fuels not directly assigned by override, we calculate the share of the total mix of fuel not assigned within a group
    # First get the value of the fuels that aren't overriden
    df["StillNeedsAssigning"] = df["Value"] - (
        df["Value"] * df["NIShareFuelOverride"].fillna(0)
    )
    # If the fuel uses an override, we do not allow any extra to be distributed so set their remaining assignment requirements to 0
    # Most of our overrides do this anyway so this is just defensive programming
    df.loc[df["UsesOverride"], "StillNeedsAssigning"] = 0

    # for the available fuel that could go in either region, we take the weights of the fuels without overrides
    df["StillNeedsAssigningShare"] = df["StillNeedsAssigning"] / df.groupby(
        ["Sector", group_used]
    )["StillNeedsAssigning"].transform("sum")
    # it's possible for the divisor to be 0 so this will come out null. We just make it 0 because nothing to assign in that case
    df["StillNeedsAssigningShare"] = df["StillNeedsAssigningShare"].fillna(0)

    return df


def get_final_adjusted_shares(df):

    # We then use this share to distribute the remaining share of unassigned fuels (considering the sector default compared to the total override share) among the remaining unassigned fuels
    # This step is important: there should be some fuel remaining to assign after the overrides, otherwise our default values might be wrong
    #
    df["NIValueAssigned"] = df["LeftToAssignFuel"] * df["StillNeedsAssigningShare"]
    # This can be added to the override values (which are 0 if no override was specified)
    df["NIValueOverride"] = df["NIShareFuelOverride"].fillna(0) * df["Value"]

    df["NIValue"] = df["NIValueAssigned"] + df["NIValueOverride"]
    df["SIValue"] = df["Value"] - df["NIValue"]

    return df


def summarise_shares(df, group_used=group_used):
    """We've made a lot of data and variables but we just need the value and the NIValue right now"""

    df = (
        df.groupby(["Sector", group_used, "Fuel"])[["Value", "NIValue"]]
        .sum()
        .reset_index()
    )
    df["NIShare"] = df["NIValue"] / df["Value"]

    # annoyingly, some values are 0 in the EEUD which breaks our NIShare calc and puts missing values in
    # we replace these broken NIShares with defaults - since values are 0 it doesn't matter but good for completeness
    df = add_sector_default_shares(df)
    df["NIShare"] = df["NIShare"].fillna(df["NIShareSector"])
    df = df.drop(["Value", "NIValue", "NIShareSector"], axis=1)

    return df


def apply_shares_to_main_dataframe(df, main=baseyear_industry, tolerance=8):

    shares = summarise_shares(df)

    df = pd.merge(main, shares, on=["Sector", group_used, "Fuel"], how="left")

    # we deal with some floating point drama by rounding and ensuring positive values (was getting -0 a lot which was annoying)

    df["NI"] = round(df["Value"] * df["NIShare"], tolerance)
    df["SI"] = abs(round(df["Value"] - df["NI"], tolerance))

    return df


def tidy_data(df):

    # we remove the original value and share variables and pivot out a region variable for value
    df = df.drop(["Value", "NIShare"], axis=1)

    cols_to_melt = ["NI", "SI"]
    id_cols = [col for col in df.columns if col not in cols_to_melt]
    df = df.melt(
        id_vars=id_cols, value_vars=cols_to_melt, var_name="Region", value_name="Value"
    )

    # this will expand out a lot of 0s, like value 0 for SI natural gas use etc
    # rather than then implying these might exist (they do not) we just delete them for clarity
    df = df[df["Value"] != 0]

    return df


# Define tests ------------------------------------------------------------------


def report_adjusted_weights(df):
    """
    We take the output of calculate shares and report any where we have had to mess with our defaults to make the overrides work
    """
    # Values where we note an adjustment was required
    df = df[df["NIShareSectorAdjusted"] != df["NIShareSector"]]

    df = df[
        [
            "Sector",
            group_used,
            "Fuel",
            "NIShareSector",
            "NIShareSectorAdjusted",
            "UsesOverride",
        ]
    ].drop_duplicates()

    logger.warning(
        f"The following items for each {group_used} have had default shares adjusted so that fuel shares align with provided overrides:"
    )

    summary = df = df[
        ["Sector", group_used, "NIShareSector", "NIShareSectorAdjusted"]
    ].drop_duplicates()
    for index, row in summary.iterrows():
        # logger.info(row)
        logger.warning(
            f"      {row['Sector']} ({row[group_used]}): Share was adjusted from {round(row['NIShareSector']*100,2)}% to {round(row['NIShareSectorAdjusted']*100,2)}% "
        )

    save_checks(df, "regional_share_adjustments.csv", "regional share adjustments made")

    # Save output to checks

    return df


def report_aggregate_subsector_shares(df):
    """

    This function takes the output and tests the new regional shares for each subsector
    If any have been adjusted to meet feasibility, there might be differences from the original assumptions

    """

    # Calculate the new shares
    df = df.groupby("Sector")[["Value", "NIValue", "SIValue"]].sum()
    df["AdjustedShare"] = df["NIValue"] / df["Value"]

    # Compare to default sector shares
    default_shares = regional_splits_by_sector[["Sector", "NI_Share"]].copy()
    default_shares = default_shares.rename(columns={"NI_Share": "DefaultShare"})
    df = pd.merge(df, default_shares, on="Sector")

    df = df[["Sector", "DefaultShare", "AdjustedShare"]]

    # get the output if any adjustments were made
    df["ShareDifference"] = abs(df["DefaultShare"] - df["AdjustedShare"])
    df_test = df[df["ShareDifference"] > 1e-4]

    # if there's any results of adjustments made, we output the results to log
    if not df_test.empty:
        logger.warning("The following sector share adjustments have been made:")
        for index, row in df_test.iterrows():
            logger.warning(
                f"      {row['Sector']}: Share was adjusted from {round(row['DefaultShare']*100,0)}% to {round(row['AdjustedShare']*100,3)}% "
            )

    # Save results
    save_checks(df, "sector_share_adjustments.csv", "sector share adjustments")


def report_sector_fuel_shares_feasible(df):
    """
    All this function does is print to console if any of the sector fuel shares aren't between 0 and 1
    It does some silly formatting and things too
    Can be repurposed as a unit test
    """

    logger.info(f"Testing North Island fuel shares are feasible:")

    error_counter = 0

    for sector in df["Sector"]:
        df_sector = df[df["Sector"] == sector]
        fuels = df_sector["Share"]

        for index, row in df_sector.iterrows():
            for fuel in fuels:
                val = row["Share"][fuel]
                val_str = f"{round(val*100,2)}%"
                # some floating point errors were causing false flags, quick tolerance adjustment
                val = round(val, 6)
                if pd.notna(val):
                    if (val > 1) | (val < 0):
                        error_counter += 1
                        val_str = red_text(val_str)
                        logger.warning(
                            f"             {sector} use of {fuel} is {red_text("IMPOSSIBLE")} at {val_str}!"
                        )  # this is very dramatic

    if error_counter == 0:
        logger.info("             All values are feasible :)")


def report_sector_fuel_shares(df):

    # Calculate the new shares by fuel
    df = (
        df.groupby(["Sector", "Fuel"])[["Value", "NIValue", "SIValue"]]
        .sum()
        .reset_index()
    )
    df["Share"] = df["NIValue"] / df["Value"]
    df["Share"] = df["Share"].fillna(0)
    df = df[["Sector", "Fuel", "Share"]].copy()
    df = pd.pivot(df, index="Sector", columns="Fuel").reset_index()

    # Test feasibility and output to console
    report_sector_fuel_shares_feasible(df)

    # Save results
    save_checks(df, "fuel_sector_shares.csv", "fuel sector shares")

    # Output share table to console
    logger.info("Fuel and Sector North Island share results:")
    sector_col = df["Sector"]
    print_df = (df * 100).round(2).astype(str).replace("nan", "")
    print_df["Sector"] = sector_col

    # this sends to console which is a useful quick check when you're working on this but can be ignored for main workflow
    print(print_df)


# Calculate -------------------------------------------------------------------


def calculate_shares(df):
    """
    Here we assign the regional share assumptions for sectors and each fuel (and its possible to add fuelXsector overrides)
    We then use the default sector assumptions, assign the fuel share overrides, then distribute the rest so that the totals add to the sector shares where possible
    We do this per group, so that the share of each group follows the sector assumptions once including overrides
    This group is currently set to Technology, but we could do it with end use or anything else we wanted
    """

    df = get_usage_shares(df)
    df = add_sector_default_shares(df)
    df = add_fuel_default_shares(df)
    df = add_fuel_sector_default_shares(df)

    df = define_override_shares(df)
    df = calculate_override_adjustments(df)
    df = get_final_adjusted_shares(df)

    # Run tests if we want
    if run_tests:
        h2("Testing industrial demand shares")
        report_adjusted_weights(df)
        report_aggregate_subsector_shares(df)
        report_sector_fuel_shares(df)

    # save this intermediary output to checks folder
    save_checks(
        df, "full_industrial_share_calculations.csv", "all regional share calculations"
    )

    # summarise the results and add the shares to the main dataframe
    df = apply_shares_to_main_dataframe(df)
    df = tidy_data(df)

    return df


# Execute ----------------------
df = calculate_shares(baseyear_industry)
# save
save_output(df, "2_times_baseyear_regional_disaggregation.csv")
