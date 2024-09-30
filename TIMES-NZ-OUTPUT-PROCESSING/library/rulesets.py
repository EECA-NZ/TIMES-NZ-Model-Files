"""
Defines rulesets used for data processing and transformation
in the project. Each ruleset consists of rules that are used
to set values in the schema DataFrame based on conditions.

Each rule is a tuple containing a condition dictionary, a
rule_type, and an actions dictionary.
    * The condition dictionary contains key-value pairs that must
    match the DataFrame row.
    * The rule_type - either 'inplace' or 'newrow' - specifies
    whether the rule should update the existing row or a copy of it.
    * The actions dictionary contains key-value pairs to set in the
    schema DataFrame row.

Rulesets are defined as lists of tuples. When a ruleset is applied,
rules are applied in order of specificity, from least to most specific.
A more specific rule's condition dictionary has a superset of the keys
of a less specific one.

When a sequence of rulesets is applied, later rulesets can override the
effects of earlier ones.

The rulesets are applied in a sequence determined by the RULESETS list
(defined at the end of this module) to ensure data consistency and
completeness.
"""

import pandas as pd
import constants
import helpers



# Generate rulesets for 'Set' attributes and descriptions.
# Here the 'Name' column in the CSV is used to match VD rows based
# on the 'Commodity' column.

commodity_set_rules = helpers.df_to_ruleset(
    dataframe=pd.read_csv(constants.ITEMS_LIST_COMMODITY_CSV),
    target_column_map={"Name": "Commodity"},
    parse_column="Set",
    separator="N/A",  # Set looks like e.g. .NRG., no separator
    schema=["CommoditySet"],
    rule_type="inplace",
)

process_set_rules = helpers.df_to_ruleset(
    dataframe=pd.read_csv(constants.ITEMS_LIST_PROCESS_CSV),
    target_column_map={"Name": "Process"},
    parse_column="Set",
    separator="N/A",  # Set looks like e.g. .NRG., no separator
    schema=["ProcessSet"],
    rule_type="inplace",
    exclude_filter=lambda df: df["Name"].apply(helpers.is_trade_process),
)

commodity_fuel_rules = helpers.df_to_ruleset(
    dataframe=pd.read_csv(constants.ITEMS_LIST_COMMODITY_CSV),
    target_column_map={"Name": "Commodity"},
    parse_column="Description",
    separator="-:-",
    schema=["Fuel", ""],
    rule_type="inplace",
)

commodity_enduse_rules = helpers.df_to_ruleset(
    dataframe=pd.read_csv(constants.ITEMS_LIST_COMMODITY_CSV),
    target_column_map={"Name": "Commodity"},
    parse_column="Description",
    separator="-:-",
    schema=["", "Enduse"],
    rule_type="inplace",
)

process_rules = helpers.df_to_ruleset(
    dataframe=pd.read_csv(constants.ITEMS_LIST_PROCESS_CSV),
    target_column_map={"Name": "Process"},
    parse_column="Description",
    separator="-:-",
    schema=["Sector", "Subsector", "Technology", ""],
    rule_type="inplace",
    exclude_filter=lambda df: df["Name"].apply(
        lambda name: helpers.is_trade_process(name) or helpers.is_elc_exchange_process(name)
    ),
)

process_fuel_rules = helpers.df_to_ruleset(
    dataframe=pd.read_csv(constants.ITEMS_LIST_PROCESS_CSV),
    target_column_map={"Name": "Process"},
    parse_column="Description",
    separator="-:-",
    schema=["", "", "", "Fuel"],
    rule_type="inplace",
    exclude_filter=lambda df: df["Name"].apply(
        lambda name: helpers.is_trade_process(name) or helpers.is_elc_exchange_process(name)
    ),
)

# Generate Enduse attributions for Processes based on their first output commodity
_cg_df = helpers.process_map_from_commodity_groups(constants.ITEMS_LIST_COMMODITY_GROUPS_CSV)
process_enduse_df = helpers.apply_rules(
    _cg_df[_cg_df.Attribute == "VAR_FOut"], commodity_enduse_rules
)[["Process", "Enduse"]].dropna()
# Take the first enduse for each process. This is a temporary solution
# until we have a better way to handle multiple enduses
process_enduse_df = process_enduse_df.groupby("Process").first().reset_index()
process_enduse_rules = helpers.df_to_ruleset(
    dataframe=process_enduse_df,
    target_column_map={"Process": "Process"},
    parse_column="Enduse",
    separator="-:-",
    schema=["Enduse"],
    rule_type="inplace",
)
# Label process inputs with the process Enduse
process_input_enduse_rules = [
    (dict(condition, **{"Attribute": "VAR_FIn"}), rule_type, updates)
    for condition, rule_type, updates in process_enduse_rules
]
# Label process capacities with the process Enduse
process_capacity_enduse_rules = [
    (dict(condition, **{"Attribute": "VAR_Cap"}), rule_type, updates)
    for condition, rule_type, updates in process_enduse_rules
]
# Label process outputs with the commodity Enduse (where applicable)
commodity_enduse_rules = [
    (dict(condition, **{"Attribute": "VAR_FOut"}), rule_type, updates)
    for condition, rule_type, updates in commodity_enduse_rules
]

# Rules for assigning units to commodities based on the TIMES base.dd definitions
commodity_unit_rules = helpers.base_dd_commodity_unit_rules(
    filepath=constants.BASE_DD_FILEPATH,
    rule_type="inplace",
)

# Predefined rules for mapping fuels to their respective fuel groups
FUEL_TO_FUELGROUP_RULES = [
    # Each tuple consists of:
    # a condition (e.g., {"Fuel": "Electricity"}),
    # a ruletype (e.g. "inplace"),
    # and an action (e.g., {"FuelGroup": "Electricity"}).
    ({"Fuel": "Electricity"}, "inplace", {"FuelGroup": "Electricity"}),
    ({"Fuel": "Green Hydrogen"}, "inplace", {"FuelGroup": "Electricity"}),
    ({"Fuel": "Coal"}, "inplace", {"FuelGroup": "Fossil Fuels"}),
    ({"Fuel": "Diesel"}, "inplace", {"FuelGroup": "Fossil Fuels"}),
    ({"Fuel": "Fuel Oil"}, "inplace", {"FuelGroup": "Fossil Fuels"}),
    ({"Fuel": "Jet Fuel"}, "inplace", {"FuelGroup": "Fossil Fuels"}),
    ({"Fuel": "LPG"}, "inplace", {"FuelGroup": "Fossil Fuels"}),
    ({"Fuel": "Natural Gas"}, "inplace", {"FuelGroup": "Fossil Fuels"}),
    ({"Fuel": "Petrol"}, "inplace", {"FuelGroup": "Fossil Fuels"}),
    ({"Fuel": "Crude Oil"}, "inplace", {"FuelGroup": "Fossil Fuels"}),
    ({"Fuel": "Waste Oil"}, "inplace", {"FuelGroup": "Fossil Fuels"}),
    ({"Fuel": "Waste Incineration"}, "inplace", {"FuelGroup": "Fossil Fuels"}),
    ({"Fuel": "Biodiesel"}, "inplace", {"FuelGroup": "Renewables (direct use)"}),
    ({"Fuel": "Biogas"}, "inplace", {"FuelGroup": "Renewables (direct use)"}),
    ({"Fuel": "Drop-In Diesel"}, "inplace", {"FuelGroup": "Renewables (direct use)"}),
    ({"Fuel": "Drop-In Jet"}, "inplace", {"FuelGroup": "Renewables (direct use)"}),
    ({"Fuel": "Geothermal"}, "inplace", {"FuelGroup": "Renewables (direct use)"}),
    ({"Fuel": "Hydro"}, "inplace", {"FuelGroup": "Renewables (direct use)"}),
    ({"Fuel": "Solar"}, "inplace", {"FuelGroup": "Renewables (direct use)"}),
    ({"Fuel": "Wind"}, "inplace", {"FuelGroup": "Renewables (direct use)"}),
    ({"Fuel": "Wood"}, "inplace", {"FuelGroup": "Renewables (direct use)"}),
    ({"Fuel": "Other"}, "inplace", {"FuelGroup": "Other"}),
]


# Predefined rules for setting the unit of capacity based on the sector
SECTOR_CAPACITY_RULES = [
    # Each tuple consists of a condition (e.g., {"Attribute": "VAR_Cap", "Sector": "Transport"}),
    # a ruletype (e.g. "inplace"),
    # and an action (e.g., {"Unit": "000 Vehicles"}).
    (
        {"Attribute": "VAR_Cap", "Sector": "Transport", "Subsector": "Road Transport"},
        "inplace",
        {"Unit": "000 Vehicles"},
    ),
    ({"Attribute": "VAR_Cap", "Sector": "Industry"}, "inplace", {"Unit": "GW"}),
    ({"Attribute": "VAR_Cap", "Sector": "Commercial"}, "inplace", {"Unit": "GW"}),
    ({"Attribute": "VAR_Cap", "Sector": "Agriculture"}, "inplace", {"Unit": "GW"}),
    ({"Attribute": "VAR_Cap", "Sector": "Residential"}, "inplace", {"Unit": "GW"}),
    ({"Attribute": "VAR_Cap", "Sector": "Electricity"}, "inplace", {"Unit": "GW"}),
    ({"Attribute": "VAR_Cap", "Sector": "Green Hydrogen"}, "inplace", {"Unit": "GW"}),
    (
        {"Attribute": "VAR_Cap", "Sector": "Primary Fuel Supply"},
        "inplace",
        {"Unit": "GW"},
    ),
]

# General parameter rules for processing data, including basic and specific categorizations
PARAMS_RULES_NEW = [
    # Basic Rules
    (
        {"Attribute": "VAR_Cap", "Unit": "000 Vehicles"},
        "inplace",
        {"Parameters": "Number of Vehicles"},
    ),
    (
        {"Attribute": "VAR_FIn", "Unit": "PJ", "ProcessSet": ".DMD."},
        "inplace",
        {"Parameters": "Fuel Consumption"},
    ),
    (
        {"Attribute": "VAR_FIn", "Unit": "PJ", "ProcessSet": ".ELE."},
        "inplace",
        {"Parameters": "Fuel Consumption"},
    ),
    (
        {"Attribute": "VAR_FOut", "Unit": "Billion Vehicle Kilometres"},
        "inplace",
        {"Parameters": "Distance Travelled"},
    ),
    (
        {"Attribute": "VAR_Cap", "Unit": "GW"},
        "inplace",
        {"Parameters": "Technology Capacity"},
    ),
    (
        {"Attribute": "VAR_FOut", "Unit": "kt CO2"},
        "inplace",
        {"Parameters": "Emissions"},
    ),
    (
        {
            "Attribute": "VAR_FOut",
            "Unit": "PJ",
            "ProcessSet": ".DMD.",
            "CommoditySet": ".DEM.",
        },
        "inplace",
        {"Parameters": "End Use Demand"},
    ),
    # Specific Rules - Electricity Storage
    (
        {
            "Attribute": "VAR_FIn",
            "Unit": "PJ",
            "Sector": "Electricity",
            "ProcessSet": ".ELE.STG.",
        },
        "inplace",
        {"Parameters": "Gross Electricity Storage"},
    ),
    (
        {
            "Attribute": "VAR_FOut",
            "Unit": "PJ",
            "Sector": "Electricity",
            "ProcessSet": ".ELE.STG.",
        },
        "inplace",
        {"Parameters": "Grid Injection (from Storage)"},
    ),
    # Specific Rules - Hydrogen Production
    (
        {
            "Attribute": "VAR_FOut",
            "Unit": "PJ",
            "Sector": "Green Hydrogen",
            "Commodity": "H2C",
            "ProcessSet": ".PRE.",
        },
        "inplace",
        {"Parameters": "Hydrogen Production", "Fuel": "Electricity"},
    ),
    (
        {
            "Attribute": "VAR_FOut",
            "Unit": "PJ",
            "Sector": "Green Hydrogen",
            "Commodity": "H2D",
            "ProcessSet": ".PRE.",
        },
        "inplace",
        {"Parameters": "Hydrogen Production", "Fuel": "Electricity"},
    ),
    (
        {
            "Attribute": "VAR_FOut",
            "Unit": "PJ",
            "Sector": "Primary Fuel Supply",
            "Subsector": "Hydrogen",
            "Commodity": "H2C",
            "ProcessSet": ".PRE.",
        },
        "inplace",
        {"Parameters": "Hydrogen Production", "Fuel": "Natural Gas"},
    ),
    (
        {
            "Attribute": "VAR_FOut",
            "Unit": "PJ",
            "Sector": "Primary Fuel Supply",
            "Subsector": "Hydrogen",
            "Commodity": "H2D",
            "ProcessSet": ".PRE.",
        },
        "inplace",
        {"Parameters": "Hydrogen Production", "Fuel": "Natural Gas"},
    ),
    # Specific Rules - Electricity Generation
    (
        {
            "Attribute": "VAR_FOut",
            "Unit": "PJ",
            "Sector": "Electricity",
            "Commodity": "ELC",
            "ProcessSet": ".ELE.",
        },
        "inplace",
        {"Parameters": "Electricity Generation"},
    ),
    (
        {
            "Attribute": "VAR_FOut",
            "Unit": "PJ",
            "Sector": "Electricity",
            "Commodity": "ELCDD",
            "ProcessSet": ".ELE.",
        },
        "inplace",
        {"Parameters": "Electricity Generation"},
    ),
    (
        {
            "Attribute": "VAR_FOut",
            "Unit": "PJ",
            "Sector": "Electricity",
            "Commodity": "ELC-MV",
            "ProcessSet": ".ELE.",
        },
        "inplace",
        {"Parameters": "Electricity Generation"},
    ),
    # Specific Rules - Feedstock
    (
        {"Attribute": "VAR_FIn", "Unit": "PJ", "Enduse": "Feedstock"},
        "inplace",
        {"Parameters": "Feedstock"},
    ),
    ({"Attribute": "VAR_FOut", "Unit": "PJ", "Enduse": "Feedstock"}, "drop", {}),
]

# Get mappings from fuel commodities to emissions commodities
emissions_dict = helpers.parse_emissions_factors(constants.BASE_DD_FILEPATH)
emissions_rules = helpers.create_emissions_rules(emissions_dict)

SUPPRESS_VAR_FIn_RENEWABLES = [
    (
        {"Attribute": "VAR_FIn", "Sector": "Electricity", "Subsector": "Hydro"},
        "drop",
        {},
    ),
    (
        {"Attribute": "VAR_FIn", "Sector": "Electricity", "Subsector": "Solar"},
        "drop",
        {},
    ),
    (
        {"Attribute": "VAR_FIn", "Sector": "Electricity", "Subsector": "Wind"},
        "drop",
        {},
    ),
    (
        {"Attribute": "VAR_FIn", "Sector": "Electricity", "Subsector": "Geothermal"},
        "drop",
        {},
    ),
]

THOUSAND_VEHICLE_RULES = [
    (
        {
            "Sector": "Transport",
            "Subsector": "Road Transport",  # "Technology": "Plug-In Hybrid Vehicle",
            "Unit": "000 Vehicles",
        },
        "inplace",
        {"Unit": "Number of Vehicles (Thousands)"},
    ),
]

DIRECT_RULESETS = [
    ("commodity_set_rules", commodity_set_rules),
    ("process_set_rules", process_set_rules),
    ("process_rules", process_rules),
    ("process_fuel_rules", process_fuel_rules),
    ("process_enduse_rules", process_enduse_rules),  # Need these to label the emissions
    ("process_input_enduse_rules", process_input_enduse_rules),
    ("process_capacity_enduse_rules", process_capacity_enduse_rules),
    ("commodity_enduse_rules", commodity_enduse_rules),
    ("commodity_fuel_rules", commodity_fuel_rules),
    ("commodity_unit_rules", commodity_unit_rules),
    ("FUEL_TO_FUELGROUP_RULES", FUEL_TO_FUELGROUP_RULES),
    ("SECTOR_CAPACITY_RULES", SECTOR_CAPACITY_RULES),
    ("PARAMS_RULES", PARAMS_RULES_NEW),
    ("THOUSAND_VEHICLE_RULES", THOUSAND_VEHICLE_RULES),
]

#### The following rulesets are used to tweak the data after the initial processing

ALWAYS_PRESENT_EMISSIONS_RULES = [
    (
        {"Parameters": "End Use Demand"},
        "newrow",
        {"Parameters": "Emissions", "Unit": "Mt CO<sub>2</sub>/yr", "Value": 0},
    ),
    (
        {"Parameters": "Fuel Consumption"},
        "newrow",
        {"Parameters": "Emissions", "Unit": "Mt CO<sub>2</sub>/yr", "Value": 0},
    ),
    (
        {"Parameters": "Feedstock"},
        "newrow",
        {"Parameters": "Emissions", "Unit": "Mt CO<sub>2</sub>/yr", "Value": 0},
    ),
    (
        {"Parameters": "Grid Injection (from Storage)"},
        "newrow",
        {"Parameters": "Emissions", "Unit": "Mt CO<sub>2</sub>/yr", "Value": 0},
    ),
    (
        {"Parameters": "Gross Electricity Storage"},
        "newrow",
        {"Parameters": "Emissions", "Unit": "Mt CO<sub>2</sub>/yr", "Value": 0},
    ),
    (
        {"Parameters": "Electricity Generation"},
        "newrow",
        {"Parameters": "Emissions", "Unit": "Mt CO<sub>2</sub>/yr", "Value": 0},
    ),
    (
        {"Parameters": "Distance Travelled"},
        "newrow",
        {"Parameters": "Emissions", "Unit": "Mt CO<sub>2</sub>/yr", "Value": 0},
    ),
    (
        {"Parameters": "Number of Vehicles"},
        "newrow",
        {"Parameters": "Emissions", "Unit": "Mt CO<sub>2</sub>/yr", "Value": 0},
    ),
]

RENEWABLE_FUEL_ALLOCATION_RULES = [
    (
        {"FuelSourceProcess": "SUP_BIGNGA", "Commodity": "NGA"},
        "inplace",
        {"Fuel": "Biogas"},
    ),
    (
        {"FuelSourceProcess": "SUP_H2NGA", "Commodity": "NGA"},
        "inplace",
        {"Fuel": "Natural Gas From Green Hydrogen"},
    ),
    (
        {"FuelSourceProcess": "CT_COILBDS", "Commodity": "BDSL"},
        "inplace",
        {"Fuel": "Biodiesel"},
    ),
    (
        {"FuelSourceProcess": "CT_CWODDID", "Commodity": "DID"},
        "inplace",
        {"Fuel": "Drop-In Diesel"},
    ),
    (
        {"FuelSourceProcess": "CT_CWODDID", "Commodity": "DIJ"},
        "inplace",
        {"Fuel": "Drop-In Jet"},
    ),
    (
        {"FuelSourceProcess": "IMPDIJ", "Commodity": "DIJ"},
        "inplace",
        {"Fuel": "Drop-In Jet"},
    ),
]


#### Rulesets for use in postprocessing e.g. reallocating fuels and emissions

commodity_units = {x[0]["Commodity"]: x[2]["Unit"] for x in commodity_unit_rules}

process_sectors = {x[0]["Process"]: x[2]["Sector"] for x in process_rules}

end_use_process_emission_types = {
    x: helpers.sector_emission_types[process_sectors[x]] for x in helpers.end_use_processes
}

emissions_commodity_rules = [
    ({"Process": key}, "inplace", {"Commodity": value})
    for (key, value) in end_use_process_emission_types.items()
]

var_fout_to_var_fin = [({"Attribute": "VAR_FOut"}, "inplace", {"Attribute": "VAR_FIn"})]

make_biodiesel_rules = [
    ({}, "inplace", {"Commodity": "BDSL"}),
    ({}, "inplace", {"Fuel": "Biodiesel"}),
    ({}, "inplace", {"FuelGroup": "Renewables (direct use)"}),
    ({}, "inplace", {"Parameters": "Fuel Consumption"}),
]

make_did_rules = [
    ({}, "inplace", {"Commodity": "DID"}),
    ({}, "inplace", {"Fuel": "Drop-In Diesel"}),
    ({}, "inplace", {"FuelGroup": "Renewables (direct use)"}),
    ({}, "inplace", {"Parameters": "Fuel Consumption"}),
]

make_dij_rules = [
    ({}, "inplace", {"Commodity": "DIJ"}),
    ({}, "inplace", {"Fuel": "Drop-In Jet"}),
    ({}, "inplace", {"FuelGroup": "Renewables (direct use)"}),
    ({}, "inplace", {"Parameters": "Fuel Consumption"}),
]

make_diesel_rules = [
    ({}, "inplace", {"Commodity": "DSL"}),
    ({}, "inplace", {"Fuel": "Diesel"}),
    ({}, "inplace", {"FuelGroup": "Fossil Fuels"}),
    ({}, "inplace", {"Parameters": "Fuel Consumption"}),
]

make_jet_rules = [
    ({}, "inplace", {"Commodity": "JET"}),
    ({}, "inplace", {"Fuel": "Jet Fuel"}),
    ({}, "inplace", {"FuelGroup": "Fossil Fuels"}),
    ({}, "inplace", {"Parameters": "Fuel Consumption"}),
]

emissions_rulesets = [
    ("RENEWABLE_FUEL_ALLOCATION_RULES", RENEWABLE_FUEL_ALLOCATION_RULES),
    ("emissions_commodity_rules", emissions_commodity_rules),
] + [
    x
    for x in DIRECT_RULESETS + [("process_enduse_rules", process_enduse_rules)]
    if not (x[0] in ["commodity_fuel_rules", "process_fuel_rules"])
]

biodiesel_rulesets = [
    ("var_fout_to_var_fin", var_fout_to_var_fin),
    ("set_commodity_to_BDSL", make_biodiesel_rules),
    ("RENEWABLE_FUEL_ALLOCATION_RULES", RENEWABLE_FUEL_ALLOCATION_RULES),
] + [
    x
    for x in DIRECT_RULESETS + [("process_enduse_rules", process_enduse_rules)]
    if not (x[0] in ["commodity_fuel_rules", "process_fuel_rules"])
]

drop_in_diesel_rulesets = [
    ("var_fout_to_var_fin", var_fout_to_var_fin),
    ("set_commodity_to_DID", make_did_rules),
    ("RENEWABLE_FUEL_ALLOCATION_RULES", RENEWABLE_FUEL_ALLOCATION_RULES),
] + [
    x
    for x in DIRECT_RULESETS + [("process_enduse_rules", process_enduse_rules)]
    if not (x[0] in ["commodity_fuel_rules", "process_fuel_rules"])
]

drop_in_jet_rulesets = [
    ("var_fout_to_var_fin", var_fout_to_var_fin),
    ("set_commodity_to_JET", make_dij_rules),
    ("RENEWABLE_FUEL_ALLOCATION_RULES", RENEWABLE_FUEL_ALLOCATION_RULES),
] + [
    x
    for x in DIRECT_RULESETS + [("process_enduse_rules", process_enduse_rules)]
    if not (x[0] in ["commodity_fuel_rules", "process_fuel_rules"])
]
