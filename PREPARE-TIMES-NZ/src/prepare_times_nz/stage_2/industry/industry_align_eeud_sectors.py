"""
Align EEUD sectors for the TIMES-NZ industrial base year dataset.

This script processes industry sector data, applies assumptions, categorises,
and aligns the EEUD dataset for TIMES-NZ base year (2023). It outputs adjusted
data to the "data_intermediate/stage_2_baseyear/industry/preprocessing" and
writes various checks to the "checks" subdirectory.

Run directly:
    python -m prepare_times_nz.stages.industry.industry_align_eeud_sectors

or import the `main()` function from elsewhere in the pipeline or tests.
"""

import tomllib

import pandas as pd
from prepare_times_nz.stage_2.industry.common import (
    INDUSTRY_ASSUMPTIONS,
    INDUSTRY_CONCORDANCES,
    PREPRO_DF_NAME_STEP1,
    save_checks,
    save_preprocessing,
)
from prepare_times_nz.utilities.filepaths import STAGE_1_DATA
from prepare_times_nz.utilities.logger_setup import blue_text, logger

# ----------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------
BASE_YEAR = 2023
BALLANCE_FEEDSTOCK_SHARE_ASSUMPTION = 0.53
BALLANCE_DU_ASSUMPTION = 0.38

# ----------------------------------------------------------------------------
# Helper Functions
# ----------------------------------------------------------------------------


def parse_toml_file(file_path):
    """Read and parse a TOML file."""
    with open(file_path, "rb") as f:
        return tomllib.load(f)


# ----------------------------------------------------------------------------
# Data Loading
# ----------------------------------------------------------------------------


def load_data():
    """Load all necessary input data."""
    data = {
        "times_eeud_industry_categories": pd.read_csv(
            INDUSTRY_CONCORDANCES / "times_eeud_industry_categories.csv"
        ),
        "gic_data": pd.read_csv(STAGE_1_DATA / "gic/gic_production_consumption.csv"),
        "eeud": pd.read_csv(STAGE_1_DATA / "eeud/eeud.csv"),
        "mbie_gas_non_energy": pd.read_csv(
            STAGE_1_DATA / "mbie/mbie_gas_non_energy.csv"
        ),
        "chemical_split_categories": pd.read_csv(
            INDUSTRY_ASSUMPTIONS / "chemical_split_category_definitions.csv"
        ),
        "nz_steel_coal_use": pd.read_csv(
            INDUSTRY_ASSUMPTIONS / "nz_steel_coal_use.csv"
        ),
        "eeud_tech_adjustments": parse_toml_file(
            INDUSTRY_CONCORDANCES / "times_eeud_tech_renames.toml"
        ),
    }
    return data


# ----------------------------------------------------------------------------
# Processing Functions (fixed for explicit dependencies)
# ----------------------------------------------------------------------------


def summarise_gic_data(gic_data):
    """Summarise GIC data to yearly aggregates."""
    gic_data["Date"] = pd.to_datetime(gic_data["Date"])
    gic_data["Year"] = gic_data["Date"].dt.year
    group_vars = ["Year", "UserType", "Participant", "Unit"]
    gic_data = gic_data.groupby(group_vars)["Value"].sum().reset_index()
    gic_data["Value"] /= 1e3
    gic_data["Unit"] = "PJ"
    gic_2017_fake = gic_data[gic_data["Year"] == 2018].copy()
    gic_2017_fake["Year"] = 2017
    return pd.concat([gic_data, gic_2017_fake])


def get_methanex_gic_data(gic_data):
    """
    Get GIC data for Methanex participants.
    """
    methanex_participants = ["Methanex Motunui", "Methanex Waitara Valley"]
    df = gic_data[gic_data["Participant"].isin(methanex_participants)].copy()
    df["Participant"] = "Methanex"
    df = df.groupby(["Year"])["Value"].sum().reset_index()
    df = df.rename(columns={"Value": "Methanex Total"})
    return df


def get_ballance_gic_data(gic_data):
    """
    Get GIC data for Ballance participants.
    """
    df = gic_data[gic_data["Participant"] == "Ballance"].copy()
    df = df[["Year", "Value"]]
    df = df.rename(columns={"Value": "Ballance Total"})
    return df


def get_industry_pj(df):
    """
    Get industry data in PJ.
    """
    df = df[df["SectorGroup"] == "Industrial"].copy()
    df["Unit"] = "PJ"
    df["Value"] = df["Value"] / 1e3
    return df


def rename_eeud_techs(df, eeud_tech_adjustments, report=False):
    """
    Rename EEUD technologies based on the provided adjustments.
    """
    rules = eeud_tech_adjustments["rule"]

    def apply_rules(df, rules, report=False):
        for rule in rules:
            cond = pd.Series([True] * len(df))
            if report:
                logger.info(
                    "Applying technology definition adjustment: %s", rule["Name"]
                )
                logger.info("          Justification: %s", rule["Justification"])
            for col, val in rule["conditions"].items():
                if col not in df.columns:
                    logger.warning("Column '%s' not found in DataFrame", col)
                if report:
                    logger.info("          Condition: '%s' = '%s'", col, val)
                cond &= df[col] == val
            for col, val in rule["updates"].items():
                if report:
                    logger.info("          Changing '%s' to '%s'", col, val)
                df.loc[cond, col] = val
        return df

    df = apply_rules(df, rules, report)
    return df


def define_tiwai(df):
    """
    Here we set hardcoded function rules to define Aluminium sector use
    This is quite straightforward, since it's just all the ele high temp
    furnace use at Tiwai.
    """

    df.loc[
        (
            (df["Sector"] == "Primary Metal and Metal Product Manufacturing")
            & (df["EndUse"] == "High Temperature Heat (>300 C), Process Requirements")
            & (df["Technology"] == "Electric Furnace")
        ),
        "Sector",
    ] = "Aluminium"

    return df


def define_nzsteel(df):
    """
    So we are assuming that other than Tiwai, all other primary
    metal and metal product manufacturing is Iron & Steel
    The EEUD definitions include Tiwai, NZSteel, and Pacific Steel only.
    So this does line up even if the original data also includes
    some non-ferrous processes.

    We do not include the fuel oil processes here, as these are not
    part of the NZSteel process.
    So anything not captured by Iron/Steel or Tiwai will end up in
    "other" for the model

    """

    df.loc[
        (
            (df["Sector"] == "Primary Metal and Metal Product Manufacturing")
            & (df["Sector"] != "Aluminium")
            & (df["Fuel"] != "Fuel Oil")
        ),
        "Sector",
    ] = "Iron & Steel"

    return df


def add_times_categories(df, times_eeud_industry_categories):
    """
    Map EEUD sectors to TIMES sectors using the provided category definitions.
    """
    category_map = times_eeud_industry_categories[["EEUD", "TIMES"]]
    category_map = category_map.rename(
        columns={"EEUD": "Sector", "TIMES": "TIMES_Sector"}
    )
    df = pd.merge(df, category_map, on="Sector", how="left")
    df["Sector"] = df["TIMES_Sector"].fillna(df["Sector"])
    return df


def aggregate_eeud(df):
    """
    Aggregate EEUD data by relevant categories.
    """
    group_cols = [
        "Year",
        "Sector",
        "TechnologyGroup",
        "Technology",
        "EndUse",
        "EnduseGroup",
        "Fuel",
        "Unit",
    ]
    df[group_cols] = df[group_cols].fillna("NA")
    df = df.groupby(group_cols)[["Value"]].sum().reset_index()
    return df


def add_nzsteel_feedstock(df, nz_steel_coal_use):
    """
    Add NZ Steel feedstock data to the main DataFrame.
    """
    coal_feedstock_data = nz_steel_coal_use[["Year", "NZSteelUse"]].copy()
    coal_feedstock_data.rename(columns={"NZSteelUse": "Value"}, inplace=True)
    descriptive_variables = df.drop(["Year", "Value"], axis=1)
    descriptive_variables = descriptive_variables[
        descriptive_variables["Sector"] == "Iron & Steel"
    ]
    descriptive_variables["Fuel"] = "Coal"
    descriptive_variables["FuelGroup"] = "Fossil Fuels"
    descriptive_variables["TechnologyGroup"] = "Feedstock"
    descriptive_variables["Technology"] = "Feedstock"
    descriptive_variables["EnduseGroup"] = "Feedstock"
    descriptive_variables["EndUse"] = "Feedstock"
    descriptive_variables = descriptive_variables.drop_duplicates()
    coal_feedstock_data["Sector"] = "Iron & Steel"
    coal_feedstock_data = pd.merge(
        coal_feedstock_data, descriptive_variables, on="Sector"
    )
    df = pd.concat([df, coal_feedstock_data], ignore_index=True)
    return df


def create_chemical_nga_shares(
    df, gic_data, mbie_gas_non_energy, chemical_split_categories
):
    """
    Create shares of natural gas use for chemical processes.
    """
    input_data = df
    methanex_data = get_methanex_gic_data(gic_data)
    ballance_data = get_ballance_gic_data(gic_data)
    mbie_feedstock = mbie_gas_non_energy[["Year", "Value"]].rename(
        columns={"Value": "MBIE Feedstock"}
    )

    def get_eeud_chem_nga_use(
        df, tech, use="High Temperature Heat (>300 C), Process Requirements"
    ):
        df2 = df[
            (
                df["Sector"]
                == "Petroleum, Basic Chemical and Rubber Product Manufacturing"
            )
            & (df["Technology"] == tech)
            & (df["EndUse"] == use)
            & (df["Fuel"] == "Natural Gas")
        ]
        df2 = df2[["Year", "Value"]]
        df2 = df2.rename(columns={"Value": tech})
        return df2

    calcs = get_eeud_chem_nga_use(df, "Reformer")
    calcs = pd.merge(
        calcs,
        get_eeud_chem_nga_use(
            df, "Pump Systems (for Fluids, etc.)", use="Motive Power, Stationary"
        ),
    )
    calcs = pd.merge(calcs, get_eeud_chem_nga_use(df, "Boiler Systems"))
    calcs = pd.merge(calcs, get_eeud_chem_nga_use(df, "Furnace/Kiln"))
    calcs = pd.merge(calcs, ballance_data, on="Year")
    calcs = pd.merge(calcs, methanex_data, on="Year")
    calcs = pd.merge(calcs, mbie_feedstock, on="Year")
    calcs["Ballance Direct Use"] = calcs["Ballance Total"] * BALLANCE_DU_ASSUMPTION
    calcs["Ballance Feedstock"] = (
        calcs["Ballance Total"] * BALLANCE_FEEDSTOCK_SHARE_ASSUMPTION
    )
    calcs["Ballance Pumps"] = calcs["Pump Systems (for Fluids, etc.)"]
    calcs["Ballance Reforming"] = calcs["Ballance Direct Use"] - calcs["Ballance Pumps"]
    calcs["Methanex Feedstock"] = calcs["MBIE Feedstock"] - calcs["Ballance Feedstock"]
    calcs["Methanex Direct Use"] = calcs["Methanex Total"] - calcs["Methanex Feedstock"]
    calcs["Methanex Remaining DU"] = calcs["Methanex Direct Use"]

    def allocate_methanex_du(df, item_to_allocate):
        df[item_to_allocate] = df[[item_to_allocate, "Methanex Remaining DU"]].min(
            axis=1
        )
        df["Methanex Remaining DU"] = df["Methanex Remaining DU"] - df[item_to_allocate]
        return df

    calcs["Methanex Reforming"] = calcs["Reformer"] - calcs["Ballance Reforming"]
    calcs = allocate_methanex_du(calcs, "Methanex Reforming")
    calcs["Methanex Furnaces"] = calcs["Furnace/Kiln"]
    calcs = allocate_methanex_du(calcs, "Methanex Furnaces")
    calcs["Methanex Boilers"] = calcs["Boiler Systems"]
    calcs = allocate_methanex_du(calcs, "Methanex Boilers")
    calcs["Remaining Reforming"] = calcs["Reformer"] - (
        calcs["Ballance Reforming"] + calcs["Methanex Reforming"]
    )
    calcs["Remaining Boilers"] = calcs["Boiler Systems"] - calcs["Methanex Boilers"]
    calcs["Remaining Pumps"] = (
        calcs["Pump Systems (for Fluids, etc.)"] - calcs["Ballance Pumps"]
    )
    calcs["Methanex Total"] = (
        calcs["Methanex Feedstock"]
        + calcs["Methanex Boilers"]
        + calcs["Methanex Reforming"]
        + calcs["Methanex Furnaces"]
    )
    calcs["Methanex FS Share"] = calcs["Methanex Feedstock"] / calcs["Methanex Total"]

    save_checks(
        calcs,
        name="chemical_split_calculations.csv",
        label="detailed chemical split calculations and tests",
    )
    df2 = calcs[
        [
            "Year",
            "Methanex Feedstock",
            "Methanex Reforming",
            "Methanex Boilers",
            "Methanex Furnaces",
            "Ballance Feedstock",
            "Ballance Reforming",
            "Ballance Pumps",
        ]
    ]
    df2 = pd.melt(df2, id_vars="Year", var_name="Lookup", value_name="Value")
    df2 = pd.merge(df2, chemical_split_categories, on="Lookup", how="left")
    df2 = df2[input_data.columns]
    return df2


def split_chemicals_out(df, gic_data, mbie_gas_non_energy, chemical_split_categories):
    """
    Split chemical processes into their respective natural gas use categories.
    """
    new_sectors = create_chemical_nga_shares(
        df, gic_data, mbie_gas_non_energy, chemical_split_categories
    )
    df_to_remove = new_sectors.copy()
    df_to_remove["Sector"] = (
        "Petroleum, Basic Chemical and Rubber Product Manufacturing"
    )
    grouping_cols = [col for col in df_to_remove.columns if col != "Value"]
    df_to_remove = (
        df_to_remove.groupby(grouping_cols)["Value"]
        .sum()
        .reset_index()
        .rename(columns={"Value": "ValueToRemove"})
    )
    df = pd.merge(df, df_to_remove, how="left")
    df["ValueToRemove"] = df["ValueToRemove"].fillna(0)
    df["Value"] = df["Value"] - df["ValueToRemove"]
    df = df.drop("ValueToRemove", axis=1)
    df = pd.concat([df, new_sectors])
    return df


def filter_output_to_base_year(df):
    """
    Filter the DataFrame to only include data for the base year.
    """
    df = df[df["Year"] == BASE_YEAR]
    df = df.drop("Year", axis=1)
    return df


def create_default_groups_per_fuel(df):
    """

    Some items in the EEUD do not allocate the fuel use
    to a technology or end use. So we have some miscellaneous
    use in the "other" bucket which should be assigned to
    something. The approach is to create default use/tech
    groups per fuel which we can use when we're not sure.
    This method returns a dataframe of the most common uses
    per fuel per year  (agnostic to industry)
    """

    grouping_vars = [
        "TechnologyGroup",
        "Technology",
        "EndUse",
        "EnduseGroup",
        "Fuel",
    ]

    # we remove Aluminium, Methanex, and Ballance, as
    # these are large users but do not reflect the
    # rest of the sector very well
    # A reminder that the official names are
    # Methanol/Urea, not Methanex/Ballance. This
    # might be a problem since Ballance makes urea and
    df = df[~df["Sector"].isin(["Methanol", "Aluminium", "Urea"])]
    # we also remove the feedstock
    df = df[df["EndUse"] != "Feedstock"]
    # we also don't want the nulls obviously (looking for most
    # common non-null usage)
    df = df[df["Technology"] != "NA"]

    # aggregate per group and fuel and year
    df = df.groupby(grouping_vars)["Value"].sum().reset_index()

    # now take the max per fuel and year. First find the
    # corresponding index of max value per group
    idx = df.groupby(["Fuel"])["Value"].idxmax()
    # then use that index to filter
    df = df.loc[idx].reset_index()

    # Value no longer needed and also remove index
    df = df.drop(["Value", "index"], axis=1)

    # save this as well for reference)
    save_checks(
        df,
        name="default_fuel_uses.csv",
        label="default fuel uses",
    )
    return df


def apply_default_fuel_uses(df):
    """
    Apply default fuel uses to the DataFrame.
    """

    # create the defaults
    default_df = create_default_groups_per_fuel(df)

    # set the categories we're filling in
    cols_to_fill = [
        "TechnologyGroup",
        "Technology",
        "EnduseGroup",
        "EndUse",
    ]

    # we have two dfs with the same names for our
    # categories. For clarity we rename our default
    # categories before we join
    for col in default_df.columns:
        if col in cols_to_fill:
            default_df = default_df.rename(columns={col: f"{col}Default"})

    # add default categories to main dataset (by fuel)
    df = pd.merge(df, default_df, on="Fuel", how="left")

    # replace NAs (note these are string 'NA's from the assumptions sheet!)
    for col in cols_to_fill:
        # define default
        default_col = f"{col}Default"
        # fill in from default
        df[col] = df[col].where(df[col] != "NA", df[default_col])
        # drop default column
        df = df.drop(default_col, axis=1)

    # finally, we would reaggregate the table (adding
    # our default uses to existing data on that use)
    # maybe should define the groups a little smarter
    # but here we are
    df = (
        df.groupby(
            [
                "Year",
                "Sector",
                "TechnologyGroup",
                "Technology",
                "EnduseGroup",
                "EndUse",
                "Fuel",
                "Unit",
            ]
        )["Value"]
        .sum()
        .reset_index()
    )

    return df


def check_sector_demand_shares(df, year=BASE_YEAR):
    """
    Check the demand shares for each sector in the specified year.
    """
    df = df[df["EndUse"] != "Feedstock"]
    df = df[df["Year"] == year]
    df = df.groupby(["Sector"])[["Value"]].sum().reset_index()
    df["Total Demand"] = df["Value"].sum()
    df["Share of Industrial demand"] = df["Value"] / df["Value"].sum()

    save_checks(
        df,
        name=f"industry_demand_shares_{year}.csv",
        label=f"industry demand shares in {year}",
    )


# ----------------------------------------------------------------------------
# Main execution flow
# ----------------------------------------------------------------------------


def main():
    """
    Main execution function for the script.
    """
    logger.warning("Several hardcoded assumptions need to move to assumptions file")
    logger.warning(
        "Ballance feedstock assumption: %s",
        blue_text(f"{BALLANCE_FEEDSTOCK_SHARE_ASSUMPTION:.0%}"),
    )
    logger.warning(
        "Ballance DU assumption: %s", blue_text(f"{BALLANCE_DU_ASSUMPTION:.0%}")
    )
    data = load_data()
    gic_data = summarise_gic_data(data["gic_data"])
    df = get_industry_pj(data["eeud"])
    df = define_tiwai(df)
    df = define_nzsteel(df)
    df = split_chemicals_out(
        df, gic_data, data["mbie_gas_non_energy"], data["chemical_split_categories"]
    )
    df = add_times_categories(df, data["times_eeud_industry_categories"])
    # add NZSTeel feedstock here. Currently this uses a hardcoded input
    # sheet which we should replace with MBIE coal data if possible
    df = add_nzsteel_feedstock(df, data["nz_steel_coal_use"])
    # Rename some techs using the rules provided in times_eeud_tech_renames.toml
    df = rename_eeud_techs(df, data["eeud_tech_adjustments"])
    df = aggregate_eeud(df)
    df = apply_default_fuel_uses(df)
    # checks - must do these before filtering the year (so we can check previous years)
    check_sector_demand_shares(df)
    check_sector_demand_shares(df, year=2018)
    df_baseyear = filter_output_to_base_year(df)
    # Save outputs
    save_checks(
        df,
        "times_eeud_alignment_timeseries.csv",
        "full EEUD timeseries",
    )
    save_preprocessing(
        df_baseyear, PREPRO_DF_NAME_STEP1, "eeud and TIMES sector alignments"
    )


if __name__ == "__main__":
    main()
