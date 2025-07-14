# Libraries -------------------------------------------------------------------

import os
import tomllib

import pandas as pd
from prepare_times_nz.filepaths import (ASSUMPTIONS, DATA_RAW, STAGE_1_DATA,
                                        STAGE_2_DATA)
from prepare_times_nz.logger_setup import blue_text, h1, logger

# Constants ---------------------------------------------------------

base_year = 2023

# add these to an input file later
# note ballance is 9% cogen roughly, so we ignore that (and our total direct use and feedstock is only 90% of their demand)
# See

ballance_feedstock_share_assumption = 0.53
ballance_du_assumption = 0.38



logger.warning("Warning! There are several hardcoded assumptions in this script that should be added to an assumptions file")
logger.warning(f"Ballance feedstock share assumption: {round(ballance_feedstock_share_assumption*100,0)}%")
logger.warning(f"Ballance Direct Use share assumption: {round(ballance_du_assumption*100,0)}%")


# Filepaths -------------------------------------------------------------------------
output_location = f"{STAGE_2_DATA}/industry/preprocessing"
os.makedirs(output_location, exist_ok = True)

checks_location = f"{STAGE_2_DATA}/industry/checks/1_sector_alignment"
os.makedirs(checks_location, exist_ok = True)



# Get data ---------------------------------

# our process topology is hardcoded here
times_eeud_industry_categories = pd.read_csv(f"{DATA_RAW}/concordances/industry/times_eeud_industry_categories.csv")
# this maps processes to categories
# concordance = pd.read_csv(f"{DATA_RAW}/concordances/times_code_concordance/attribute_process_commodity_concordance.csv")
# demand data
gic_data = pd.read_csv(f"{STAGE_1_DATA}/gic/gic_production_consumption.csv")
eeud = pd.read_csv(f"{STAGE_1_DATA}/eeud/eeud.csv")

mbie_gas_non_energy =  pd.read_csv(f"{STAGE_1_DATA}/mbie/mbie_gas_non_energy.csv")

# assumptions
# chemical split codes
chemical_split_categories = pd.read_csv(f"{ASSUMPTIONS}/industry_demand/chemical_split_category_definitions.csv")
# coal use for nz steel is currently hardcoded as an assumption but we could(/should) replace this with MBIE coal data directly
nz_steel_coal_use = pd.read_csv(f"{ASSUMPTIONS}/industry_demand/nz_steel_coal_use.csv")

eeud_tech_adjustments_toml = f"{DATA_RAW}/concordances/industry/times_eeud_tech_renames.toml"


# Initial processing -----------------------

def summarise_gic_data(gic_data):
    # make years out of dates
    gic_data["Date"] = pd.to_datetime(gic_data["Date"])
    gic_data["Year"] = gic_data["Date"].dt.year


    # aggregate PJ per year and user
    group_vars = ["Year", "UserType", "Participant", "Unit"]
    gic_data = gic_data.groupby(group_vars)["Value"].sum().reset_index()

    # convert PJ
    gic_data["Value"] = gic_data["Value"]/1e3
    gic_data["Unit"] = "PJ"

    #backcast just one year to align with EEUD, which starts in 2017
    # this is quite dodgy but has very minimal use in TIMES at all so don't worry too much
    # if we don't do this then our chemical timeseries is very wrong, mostly used for checking historical trends
    # Note: the results are still quite weird looking and should not be relied on. I'm not sure what's happening here.
    gic_data_2017_fake = gic_data[gic_data["Year"] == 2018].copy()
    gic_data_2017_fake["Year"] = 2017
    gic_data = pd.concat([gic_data,gic_data_2017_fake])


    return gic_data

def parse_toml_file(file_path):
    with open(file_path, 'rb') as f:
        toml_data = tomllib.load(f)
    return toml_data

# creating a few additional supporting dataframes for other functions to use
eeud_tech_adjustments = parse_toml_file(eeud_tech_adjustments_toml)
gic_data = summarise_gic_data(gic_data)


# Functions --------------------

def save_output(df, name):

    filename =f"{output_location}/{name}"
    logger.info(f"Saving output:\n{blue_text(filename)}")
    df.to_csv(filename, index = False)


def save_checks(df, name, label):
    filename =f"{checks_location}/{name}"
    logger.info(f"Saving {label}:\n{blue_text(filename)}")
    df.to_csv(filename, index = False)


def get_methanex_gic_data(gic_data):

    # filter
    methanex_participants = ["Methanex Motunui",
                             "Methanex Waitara Valley"]
    df =  gic_data[gic_data["Participant"].isin(methanex_participants)].copy()

    # aggregate - we capture waitara valley and just add it in. THis is zero for recent years but helps us build a believable backseries.
    df["Participant"] = "Methanex"
    df = df.groupby(["Year"])["Value"].sum().reset_index()
    df = df.rename(columns = {"Value": "Methanex Total"})

    return df

def get_ballance_gic_data(gic_data):

    df = gic_data[gic_data["Participant"] == "Ballance"].copy()
    df = df[["Year", "Value"]]
    df = df.rename(columns = {"Value": "Ballance Total"})

    return df

def get_industry_pj(df):

    """
    industrial demand and convert to PJ (original data in TJ)

    """
    df = df[df["SectorGroup"] == "Industrial"].copy() # must copy to ensure we don't then mess with a view

    # convert PJ
    df["Unit"] = "PJ"
    df["Value"] = df["Value"]/1e3

    return df

def rename_eeud_techs(df, report = False):

    """
    Reads in a concordance table for tweaks we want to make to the EEUD names

    NOTE: we want to do this before aggregating (so if we combine categories they sum based on these )
    However we need to do it after our sector splits, so that we can use the sector split logic to define our rules


    """

    rules = eeud_tech_adjustments['rule']

    def apply_rules(df, rules, report = False):
        for rule in rules:
            cond = pd.Series([True] * len(df))
            if report:
                logger.info(f"Applying technology definition adjustment: {rule["Name"]}")
                logger.info(f"          Justification: {rule["Justification"]}")
            for col, val in rule['conditions'].items():
                if col not in df.columns:
                    logger.warning(f"Column '{col}' not found in DataFrame")
                if report:
                    logger.info(f"          Condition: '{col}' = '{val}'")
                cond &= df[col] == val
            for col, val in rule['updates'].items():
                if report:
                        logger.info(f"          Changing '{col}' to '{val}'")
                df.loc[cond, col] = val
        return df

    df = apply_rules(df, rules, report)



    return df

def define_tiwai(df):
    """
    Here we set hardcoded function rules to define Aluminium sector use
    This is quite straightforward, since it's just all the ele high temp furnace use at Tiwai.
    """

    df.loc[(
        (df["Sector"] == "Primary Metal and Metal Product Manufacturing") &
        (df["EndUse"]  == "High Temperature Heat (>300 C), Process Requirements") &
        (df["Technology"]  == "Electric Furnace")
        ),
        "Sector"
        ] = "Aluminium"

    return df

def define_nzsteel(df):

    """
    So we are assuming that other than Tiwai, all other primary metal and metal product manufacturing is Iron & Steel
    The EEUD definitions include Tiwai, NZSteel, and Pacific Steel only.
    So this does line up even if the original data also includes some non-ferrous processes.

    We do not include the fuel oil processes here, as these are not part of the NZSteel process
    So anything not captured by Iron/Steel or Tiwai will end up in "other" for the model

    """

    df.loc[(
        (df["Sector"] == "Primary Metal and Metal Product Manufacturing") &
        (df["Sector"]  != "Aluminium") &
        (df["Fuel"]  != "Fuel Oil")
        ),
        "Sector"
        ] = "Iron & Steel"

    return df

def get_current_subsectors(df):

    """
    can probably delete this later
    """

    df = df["Sector"].drop_duplicates()
    return df

def add_times_categories(df):

    """
    Add the category concordance to the EEUD data, which maps EEUD to TIMES categories
    We can aggregate after this
    Note that we haven't done the urea/methanex/tiwai/alum splits yet
    """
    # just taking these labels ( adding copy() to remove slice warning )
    category_map = times_eeud_industry_categories[["EEUD", "TIMES"]]
    #
    category_map = category_map.rename(columns = {"EEUD" : "Sector",
                                                  "TIMES" : "TIMES_Sector"}
                                                  )

    # join the different labels
    df = pd.merge(df, category_map, on=  "Sector", how = "left")

    # if there is a successful join, we take the join, otherwise keep in place

    df["Sector"] = df["TIMES_Sector"].fillna(df["Sector"])



    return df

def aggregate_eeud(df):

    """
    1: Define EEUD categories according to:
    Sector | TechnologyGroup | Technology | EndUse | EndUseGroup | Fuel

    """

    # define groups and ensure no NAs in categories cos these confuse pandas
    group_cols = ["Year", "Sector", "TechnologyGroup", "Technology", "EndUse", "EnduseGroup", "Fuel", "Unit"]
    df[group_cols] = df[group_cols].fillna("NA")

    # group and aggregate
    df = df.groupby(group_cols)[["Value"]].sum().reset_index()

    return df

def add_nzsteel_feedstock(df, coal_feedstock_data = nz_steel_coal_use):

    df = df

    # get relevant columns
    coal_feedstock_data = coal_feedstock_data[["Year", "NZSteelUse"]].copy()
    # rename
    coal_feedstock_data.rename(columns = {"NZSteelUse" : "Value"}, inplace = True)
    # add descriptive variables (selecting from current dataframe)
    descriptive_variables = df.drop(["Year", "Value"], axis = 1)
    descriptive_variables = descriptive_variables[descriptive_variables["Sector"] == "Iron & Steel"]

    # rewrite the descriptive variables where needed

    descriptive_variables["Fuel"] = "Coal"
    descriptive_variables["FuelGroup"] = "Fossil Fuels"
    descriptive_variables["TechnologyGroup"] = "Feedstock"
    descriptive_variables["Technology"] = "Feedstock"
    descriptive_variables["EnduseGroup"] = "Feedstock"
    descriptive_variables["EndUse"] = "Feedstock"

    descriptive_variables = descriptive_variables.drop_duplicates()

    # add descriptive variables to coal data

    coal_feedstock_data["Sector"] = "Iron & Steel"
    coal_feedstock_data = pd.merge(coal_feedstock_data, descriptive_variables, on = "Sector")

    # append feedstock data to main dataframe

    df = pd.concat([df, coal_feedstock_data], ignore_index= True)





    return df

def create_chemical_nga_shares(df):

    # store the input data as a separate object for general use
    input_data = df

    """
    This function defines Methanex and Ballance demand allocated against the EEUD.
    It's an annoyingly complex method to try and align all the relevant data sources, hence the long list of calculations.
    The way this is setup allows us to define all the logic based on a range of inputs, so it's moderately straightforward to adjust the logic if we want.
    We can call our final variables whatever we want: these are then categorised properly according to the structure in assumptions/industry_demand/chemical_splits.csv
    Those are then compared to the relevant EEUD categories and removed from that sector in split_chemicals_out(), which wraps the output of this function.

    """

    # First, we prep the additional data (GIC consumption and mbie feedstock data)
    methanex_data = get_methanex_gic_data(gic_data)
    ballance_data = get_ballance_gic_data(gic_data)

    mbie_feedstock = mbie_gas_non_energy[["Year", "Value"]]
    mbie_feedstock = mbie_feedstock.rename(columns = {"Value": "MBIE Feedstock"})

    # we then make the skeleton of our output data, including some EEUD items that we can use for calculations. We don't want to overallocate demand to Methanex/Ballance, after all.

    def get_eeud_chem_nga_use(df, tech, use = "High Temperature Heat (>300 C), Process Requirements"):

        # return EEUD data from the petrochem sector for specific techs
        # we need to also specify the use, mostly to distinguish that we're only interested in the high temp furnaces (not the intermediate ones)
        # we'll default to only lookign at high temp process heat to save time and drama, but sometimes we want other stuff

        df = df[
        (df["Sector"] == "Petroleum, Basic Chemical and Rubber Product Manufacturing") &
        (df["Technology"] == tech) &
        (df["EndUse"] == use) &
        (df["Fuel"] == "Natural Gas")
        ]
        df = df[["Year", "Value"]]
        df = df.rename(columns = {"Value" : tech})
        return df

    calcs = get_eeud_chem_nga_use(df, "Reformer")
    calcs = pd.merge(calcs, get_eeud_chem_nga_use(df, "Pump Systems (for Fluids, etc.)", use = "Motive Power, Stationary"))
    calcs = pd.merge(calcs, get_eeud_chem_nga_use(df, "Boiler Systems"))
    calcs = pd.merge(calcs, get_eeud_chem_nga_use(df, "Furnace/Kiln"))



    # add ballance and mbie data
    calcs = pd.merge(calcs, ballance_data, on = "Year")
    calcs = pd.merge(calcs, methanex_data, on = "Year")
    calcs = pd.merge(calcs, mbie_feedstock, on = "Year")

    # Ballance estimates - DU and FS components. These don't add to 100, because we're ignoring the cogen demand shares.
    calcs["Ballance Direct Use"] = calcs["Ballance Total"] * ballance_du_assumption
    calcs["Ballance Feedstock"] = calcs["Ballance Total"] * ballance_feedstock_share_assumption

    # assume all the pumps are just Ballance compressors.
    calcs["Ballance Pumps"] = calcs["Pump Systems (for Fluids, etc.)"]
    # Rest of Ballance DU is reforming
    calcs["Ballance Reforming"] = calcs["Ballance Direct Use"] - calcs["Ballance Pumps"]

    # Methanex estimates
    # Methanex feedstock is jsut total feedstock minus Ballance Feedstock
    calcs["Methanex Feedstock"] = calcs["MBIE Feedstock"] - calcs["Ballance Feedstock"]
    # Methanex has no cogen, so DU is just total minus FS
    calcs["Methanex Direct Use"] = calcs["Methanex Total"] - calcs["Methanex Feedstock"]

    # We now need to go through and find demand in the EEUD to allocate to Methanex without overallocating.
    # First, we define a system where we check how much Methanex DU is left to allocate, so that we never go over that when extracting demand from other areas.
    calcs["Methanex Remaining DU"] = calcs["Methanex Direct Use"]

    # We then define a function that checks this remaining DU, checks an item we provide, allocates as much of the DU as it can (but no more), and then resets how much is left to allocate
    def allocate_methanex_du(df, item_to_allocate):
        # we don't want to go over the total DU remaining, so set the item to allocate to the minimum of itself and the remaining DU
        df[item_to_allocate] = df[[item_to_allocate, "Methanex Remaining DU"]].min(axis=1)
        # reset the remaining direct use
        df["Methanex Remaining DU"] = df["Methanex Remaining DU"] - df[item_to_allocate]

        return df

    # First, we apply this to the remaining reforming demand
    calcs["Methanex Reforming"] = calcs["Reformer"] - calcs["Ballance Reforming"]
    calcs = allocate_methanex_du(calcs, "Methanex Reforming")

    # If any Methanex direct use left, we take from the EEUD Furnaces
    calcs["Methanex Furnaces"] = calcs["Furnace/Kiln"]
    calcs = allocate_methanex_du(calcs, "Methanex Furnaces")

    # And repeat for the boilers if anything left still.
    calcs["Methanex Boilers"] = calcs["Boiler Systems"]
    calcs = allocate_methanex_du(calcs, "Methanex Boilers")

    # Tests - these just populate the output file to check
    calcs["Remaining Reforming"] = calcs["Reformer"] - (calcs["Ballance Reforming"] + calcs["Methanex Reforming"])
    calcs["Remaining Boilers"] = calcs["Boiler Systems"] - calcs["Methanex Boilers"]
    calcs["Remaining Pumps"] = calcs["Pump Systems (for Fluids, etc.)"] - calcs["Ballance Pumps"]
    calcs["Methanex Total"] = calcs["Methanex Feedstock"] + calcs["Methanex Boilers"] + calcs["Methanex Reforming"] + calcs["Methanex Furnaces"]
    calcs["Methanex FS Share"] = calcs["Methanex Feedstock"] / calcs["Methanex Total"]


    save_checks(calcs,
                name = "chemical_split_calculations.csv",
                label = "detailed chemical split calculations and tests")

    # reshape the data to our new version. These should be all the variables we've defined to match in our input category file
    # note they can be (and are) renamed/recategorised based on our custom rules later -
    # For now, they must lookup against original EEUD tech/use names in chemical_split_categories
    # I am a little uncomfortable with this hardcoding - perhaps it should instead read the input file lookups? That might save some drama later
    df = calcs[["Year",
                "Methanex Feedstock",
                "Methanex Reforming",
                "Methanex Boilers",
                "Methanex Furnaces",
                "Ballance Feedstock",
                "Ballance Reforming",
                "Ballance Pumps"
    ]]

    df = pd.melt(df, id_vars = "Year", var_name = "Lookup", value_name = "Value")

    # and add the EEUD structure variables for each technology.
    # these have been precategorised in the chemical_split_categories assumptions data
    df = pd.merge(df, chemical_split_categories, on = "Lookup", how = "left")

    # finally, make sure our order is correct by setting the same cols and order as input data
    df = df[input_data.columns]

    return df

def split_chemicals_out(df):

    """

    This function subtracts the specific chemical sectors from the original dataframe, then adds the specific sectors to the main data

    It then re-sorts everything (not necessary just tidy) and performs a series of validations which are then added to the check outputs

    The calculations and assumptions are compiled separately in `create_chemical_nga_shares()`
    This function just slots them into place in the workflow


    """

    # create new splits
    new_sectors = create_chemical_nga_shares(df)


    # first, we need to remove everything from the current sector. We'll aggregate the new data then subtract the values for the main category
    # df_to_remove = create_chemical_nga_shares(df)
    df_to_remove = new_sectors.copy()
    df_to_remove["Sector"] = "Petroleum, Basic Chemical and Rubber Product Manufacturing"
    # aggregate the whole thing
    grouping_cols = [col for col in df_to_remove.columns if col != "Value"]
    df_to_remove = df_to_remove.groupby(grouping_cols)["Value"].sum().reset_index().rename(columns={"Value": "ValueToRemove"})


    # we join on the same technologies then remove our specific sectors from the main sector

    # this only works because we categorised our sectors precisely in the input assumptions, so pay attention to that file if this ever causes problems
    df = pd.merge(df, df_to_remove, how = "left")
    df["ValueToRemove"] = df["ValueToRemove"].fillna(0)
    df["Value"] = df["Value"] - df["ValueToRemove"]
    df = df.drop("ValueToRemove", axis = 1)


    # now we can add the new sectors as a concatenation


    df = pd.concat([df, new_sectors])



    return df

def filter_output_to_base_year(df):

    df  = df[df["Year"] == base_year]
    df = df.drop("Year", axis = 1)
    return df

def create_default_groups_per_fuel(df):
    """

    Some items in the EEUD do not allocate the fuel use to a technology or end use.
    So we have some miscellaneous use in the "other" bucket which should be assigned to something.
    The approach is to create default use/tech groups per fuel which we can use when we're not sure.
    This method returns a dataframe of the most common uses per fuel per year  (agnostic to industry)
    """

    grouping_vars = [
        "TechnologyGroup",
        "Technology",
        "EndUse",
        "EnduseGroup",
        "Fuel",
    ]

    # we remove Aluminium, Methanex, and Ballance, as these are large users but do not reflect the rest of the sector very well
    # A reminder that the official names are Methanol/Urea, not Methanex/Ballance. This might be a problem since Ballance makes urea and
    df = df[~df["Sector"].isin(["Methanol", "Aluminium", "Urea"]) ]
    # we also remove the feedstock
    df = df[df["EndUse"] != "Feedstock"]
    # we also don't want the nulls obviously (looking for most common non-null usage)
    df = df[df["Technology"] != "NA"]


    # aggregate per group and fuel and year
    df = df.groupby(grouping_vars)["Value"].sum().reset_index()

    # now take the max per fuel and year. First find the corresponding index of max value per group
    idx = df.groupby(["Fuel"])["Value"].idxmax()
    # then use that index to filter
    df = df.loc[idx].reset_index()

    # Value no longer needed and also remove index
    df = df.drop(["Value", "index"], axis = 1)

    # save this as well for reference
    save_checks(df,
                name = "default_fuel_uses.csv",
                label = "default fuel uses")

    return df

def apply_default_fuel_uses(df):

    # create the defaults
    default_df = create_default_groups_per_fuel(df)



    # set the categories we're filling in
    cols_to_fill = [
        "TechnologyGroup",
        "Technology",
        "EnduseGroup",
        "EndUse",
        ]

    # we have two dfs with the same names for our categories. For clarity we rename our default categories before we join
    for col in default_df.columns:
        if col in cols_to_fill:
            default_df = default_df.rename(columns = {col: f"{col}Default"})

    # add default categories to main dataset (by fuel)
    df = pd.merge(df, default_df, on = "Fuel", how = "left")

    # replace NAs (note these are string 'NA's from the assumptions sheet!)
    for col in cols_to_fill:
        # define default
        default_col = f"{col}Default"
        # fill in from default
        df[col] = df[col].where(df[col] != "NA", df[default_col])
        # drop default column
        df = df.drop(default_col, axis = 1)

    # finally, we would reaggregate the table (adding our default uses to existing data on that use)
    # maybe should define the groups a little smarter but here we are
    df = df.groupby(["Year", "Sector",
                     "TechnologyGroup", "Technology",
                     "EnduseGroup", "EndUse",
                     "Fuel", "Unit"])["Value"].sum().reset_index()

    return df

# Checking functions -----------------

def check_sector_demand_shares(df, year = base_year):

    # first remove feedstock
    df = df[df["EndUse"] != "Feedstock"]

    # just pick one year (default to base year )

    df = df[df["Year"] == year]

    # aggregate by sectors

    df = df.groupby(["Sector"])[["Value"]].sum().reset_index()
    df["Total Demand"] = df["Value"].sum()
    df["Share of Industrial demand"] = df["Value"]/df["Value"].sum()

    save_checks(df, name = f"industry_demand_shares_{year}.csv", label = f"industry demand shares in {year}")

# Run stuff ------------------

# Define
def create_times_industry_timeseries():

    # This functiono is a wrapper for everything required to create the full adjusted TIMES industrial demand timeseries
    df = get_industry_pj(eeud)
    df = define_tiwai(df)
    df = define_nzsteel(df)
    df = split_chemicals_out(df)
    df = add_times_categories(df)
    # add NZSTeel feedstock here. Currently this uses a hardcoded input sheet which we should replace with MBIE coal data if possible
    df = add_nzsteel_feedstock(df)
    # Rename some techs using the rules provided in times_eeud_tech_renames.toml
    df = rename_eeud_techs(df)
    df = aggregate_eeud(df)
    df = apply_default_fuel_uses(df)

    return df

# Execute
df = create_times_industry_timeseries()

# checks - must do these before filtering the year (so we can check previous years)
check_sector_demand_shares(df)
check_sector_demand_shares(df, year = 2018)

# Filter for baseyear
#
df_baseyear = filter_output_to_base_year(df)

# Save outputs
save_checks(df, "times_eeud_alignment_timeseries.csv", "full timeseries EEUD data")
save_output(df_baseyear, "1_times_eeud_alignment_baseyear.csv")





