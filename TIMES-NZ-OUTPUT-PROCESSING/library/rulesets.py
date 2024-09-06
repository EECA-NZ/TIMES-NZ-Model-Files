"""
Defines rulesets used for data processing and transformation in the project. Each ruleset consists of rules that are
used to set values in the schema DataFrame based on conditions.

Each rule is a tuple containing a condition dictionary, a rule_type, and an actions dictionary.
* The condition dictionary contains key-value pairs that must match the DataFrame row.
* The rule_type - either 'inplace' or 'newrow' - specifies whether the rule should update the existing row or a copy of it.
* The actions dictionary contains key-value pairs to set in the schema DataFrame row.

Rulesets are defined as lists of tuples. When a ruleset is applied, rules are applied in order of specificity, from least
to most specific. A more specific rule's condition dictionary has a superset of the keys of a less specific one.

When a sequence of rulesets is applied, later rulesets can override the effects of earlier ones.

The rulesets are applied in a sequence determined by the RULESETS list (defined at the end of this module)
to ensure data consistency and completeness.
"""
import pandas as pd
from constants import *
from helpers import *


"""
Generate rulesets for 'Set' attributes and descriptions.
Here the 'Name' column in the CSV is used to match VD rows based
on the 'Commodity' column.
"""
commodity_set_rules = df_to_ruleset(
    df=pd.read_csv(ITEMS_LIST_COMMODITY_CSV),
    target_column_map={"Name": "Commodity"},
    parse_column="Set",
    separator="N/A", # Set looks like e.g. .NRG., no separator
    schema=["Set"],
    rule_type="inplace",
)

process_set_rules = df_to_ruleset(
    df=pd.read_csv(ITEMS_LIST_PROCESS_CSV),
    target_column_map={"Name": "Process"},
    parse_column="Set",
    separator="N/A", # Set looks like e.g. .NRG., no separator
    schema=["Set"],
    rule_type="inplace",
)

commodity_fuel_rules = df_to_ruleset(
    df=pd.read_csv(ITEMS_LIST_COMMODITY_CSV),
    target_column_map={"Name": "Commodity"},
    parse_column="Description",
    separator="-:-",
    schema=["Fuel", ""],
    rule_type="inplace",
)

commodity_enduse_rules = df_to_ruleset(
    df=pd.read_csv(ITEMS_LIST_COMMODITY_CSV),
    target_column_map={"Name": "Commodity"},
    parse_column="Description",
    separator="-:-",
    schema=["", "Enduse"],
    rule_type="inplace",
)

process_rules = df_to_ruleset(
    df=pd.read_csv(ITEMS_LIST_PROCESS_CSV),
    target_column_map={"Name": "Process"},
    parse_column="Description",
    separator="-:-",
    schema=["Sector", "Subsector", "Technology", ""],
    rule_type="inplace",
)

process_fuel_rules = df_to_ruleset(
    df=pd.read_csv(ITEMS_LIST_PROCESS_CSV),
    target_column_map={"Name": "Process"},
    parse_column="Description",
    separator="-:-",
    schema=["", "", "", "Fuel"],
    rule_type="inplace",
)


# Generate Enduse attributions for Processes based on their first output commodity
_cg_df = process_map_from_commodity_groups(ITEMS_LIST_COMMODITY_GROUPS_CSV)
process_enduse_df = apply_rules(_cg_df[_cg_df.Attribute=='VAR_FOut'], commodity_enduse_rules)[['Process', 'Enduse']].dropna()
# Take the first enduse for each process. This is a temporary solution until we have a better way to handle multiple enduses
# TODO: can we determine the 'main' enduse for each process, in terms of the way its capacity is defined?
process_enduse_df = process_enduse_df.groupby('Process').first().reset_index()
process_enduse_rules = df_to_ruleset(
    df=process_enduse_df,
    target_column_map={"Process": "Process"},
    parse_column="Enduse",
    separator="-:-",
    schema=["Enduse"],
    rule_type="inplace",
)
# Label process inputs with the process Enduse
process_input_enduse_rules = [(dict(condition, **{'Attribute': 'VAR_FIn'}), rule_type, updates)
    for condition, rule_type, updates in process_enduse_rules]
# Label process capacities with the process Enduse
process_capacity_enduse_rules = [(dict(condition, **{'Attribute': 'VAR_Cap'}), rule_type, updates) 
    for condition, rule_type, updates in process_enduse_rules]
# Label process outputs with the commodity Enduse (where applicable)
commodity_enduse_rules = [(dict(condition, **{'Attribute': 'VAR_FOut'}), rule_type, updates)
    for condition, rule_type, updates in commodity_enduse_rules]

# Rules for assigning units to commodities based on the TIMES base.dd definitions
commodity_unit_rules = base_dd_commodity_unit_rules(
    filepath=BASE_DD_FILEPATH,
    rule_type="inplace",
    )

SUPPRESS_PROCESS_CAPACITY_RULES = [
    # If a VAR_Cap row has DisplayCapacity not equal to TRUE, remove it by setting Attribute to None
    ({"Attribute": "VAR_Cap", "DisplayCapacity": "-"}, "drop", {}),
]

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
]

# Predefined rules for setting the unit of capacity based on the sector
SECTOR_CAPACITY_RULES = [
    # Each tuple consists of a condition (e.g., {"Attribute": "VAR_Cap", "Sector": "Transport"}),
    # a ruletype (e.g. "inplace"),
    # and an action (e.g., {"Unit": "000 Vehicles"}).
    ({"Attribute": "VAR_Cap", "Sector": "Transport", "Subsector": "Road Transport"}, "inplace", {"Unit": "000 Vehicles"}),
    ({"Attribute": "VAR_Cap", "Sector": "Industry"}, "inplace", {"Unit": "GW"}),
    ({"Attribute": "VAR_Cap", "Sector": "Commercial"}, "inplace", {"Unit": "GW"}),
    ({"Attribute": "VAR_Cap", "Sector": "Agriculture"}, "inplace", {"Unit": "GW"}),
    ({"Attribute": "VAR_Cap", "Sector": "Residential"}, "inplace", {"Unit": "GW"}),
    ({"Attribute": "VAR_Cap", "Sector": "Electricity"}, "inplace", {"Unit": "GW"}),
    ({"Attribute": "VAR_Cap", "Sector": "Green Hydrogen"}, "inplace", {"Unit": "GW"}),
    ({"Attribute": "VAR_Cap", "Sector": "Primary Fuel Supply"}, "inplace", {"Unit": "GW"}),
]

# General parameter rules for processing data, including basic and specific categorizations
PARAMS_RULES = [
    # Basic Rules
    ({"Attribute": "VAR_Cap", "Unit": "000 Vehicles"}, "inplace", {"Parameters": "Number of Vehicles"}),
    ({"Attribute": "VAR_FIn", "Unit": "PJ"}, "inplace", {"Parameters": "Fuel Consumption"}),
    ({"Attribute": "VAR_FOut", "Unit": "Billion Vehicle Kilometres"}, "inplace", {"Parameters": "Distance Travelled"}),
    ({"Attribute": "VAR_Cap", "Unit": "GW"}, "inplace", {"Parameters": "Technology Capacity"}),
    ({"Attribute": "VAR_FOut", "Unit": "kt CO2"}, "inplace", {"Parameters": "Emissions"}),
    ({"Attribute": "VAR_FOut", "Unit": "PJ"}, "inplace", {"Parameters": "End Use Demand"}),
    # Specific Rules - Electricity Storage
    ({"Attribute": "VAR_FOut", "Unit": "PJ", "Sector": "Electricity", "Set": ".ELE.STG."}, "newrow", {"Attribute": "VAR_FIn", "Parameters": "Gross Electricity Storage"}),
    ({"Attribute": "VAR_FOut", "Unit": "PJ", "Sector": "Electricity", "Set": ".ELE.STG."}, "inplace", {"Parameters": "Grid Injection (from Storage)"}),
    # Specific Rules - Electricity Generation
    ({"Attribute": "VAR_FOut", "Unit": "PJ", "Sector": "Electricity", "Commodity": "ELC", "Set": ".ELE."}, "inplace", {"Parameters": "Electricity Generation"}),
    ({"Attribute": "VAR_FOut", "Unit": "PJ", "Sector": "Electricity", "Commodity": "ELCDD", "Set": ".ELE."}, "inplace", {"Parameters": "Electricity Generation"}),
    ({"Attribute": "VAR_FOut", "Unit": "PJ", "Sector": "Electricity", "Commodity": "ELC-MV", "Set": ".ELE."}, "inplace", {"Parameters": "Electricity Generation"}),
    # Specific Rules - Feedstock
    ({"Attribute": "VAR_FIn", "Unit": "PJ", "Enduse": "Feedstock"}, "inplace", {"Parameters": "Feedstock"}),
    ({"Attribute": "VAR_FOut", "Unit": "PJ", "Enduse": "Feedstock"}, "drop", {}),
]

# Get mappings from fuel commodities to emissions commodities
emissions_dict = parse_emissions_factors(BASE_DD_FILEPATH)
emissions_rules = create_emissions_rules(emissions_dict)

SUPPRESS_VAR_FIn_RENEWABLES = [
    ({"Attribute": "VAR_FIn", "Sector": "Electricity", "Subsector": "Hydro"}, "drop", {}),
    ({"Attribute": "VAR_FIn", "Sector": "Electricity", "Subsector": "Solar"}, "drop", {}),
    ({"Attribute": "VAR_FIn", "Sector": "Electricity", "Subsector": "Wind"}, "drop", {}),
    ({"Attribute": "VAR_FIn", "Sector": "Electricity", "Subsector": "Geothermal"}, "drop", {}),
]

SCHEMA_RULESETS = [
        ("commodity_set_rules", commodity_set_rules),
        ("process_set_rules", process_set_rules),
        ("process_rules", process_rules),
        ("process_fuel_rules", process_fuel_rules),
        ("process_input_enduse_rules", process_input_enduse_rules),
        ("process_capacity_enduse_rules", process_capacity_enduse_rules),
        ("commodity_enduse_rules", commodity_enduse_rules),
        ("commodity_fuel_rules", commodity_fuel_rules),
        ("commodity_unit_rules", commodity_unit_rules),
        #("SUPPRESS_PROCESS_CAPACITY_RULES", SUPPRESS_PROCESS_CAPACITY_RULES),
        ("SUPPRESS_VAR_FIn_RENEWABLES", SUPPRESS_VAR_FIn_RENEWABLES),
        ("FUEL_TO_FUELGROUP_RULES", FUEL_TO_FUELGROUP_RULES),
        ("SECTOR_CAPACITY_RULES", SECTOR_CAPACITY_RULES),
        ("PARAMS_RULES", PARAMS_RULES),
        ("EMISSIONS_RULES", emissions_rules),
    ]

MISSING_ROWS = pd.DataFrame([
    {'Attribute':  'VAR_FIn', 'Process': 'R_DDW-SH_MSHP-ELC',           'Commodity':   'RESELC', 'Sector': 'Residential', 'Subsector': 'Detached Dwellings',       'Technology':    'Heat Pump (Multi-Split)', 'Fuel':    'Electricity', 'Enduse':          'Space Cooling', 'Unit':     'PJ', 'Parameters': 'Fuel Consumption', 'FuelGroup': 'Electricity'},
    {'Attribute':  'VAR_FIn', 'Process':     'FTE-INDDSL_00',           'Commodity':      'DID', 'Sector':    'Industry', 'Subsector':             'Mining',       'Technology': 'Internal Combustion Engine', 'Fuel': 'Drop-In Diesel', 'Enduse':   'Motive Power, Mobile', 'Unit':     'PJ', 'Parameters': 'Fuel Consumption', 'FuelGroup': 'Renewables (direct use)'},
    {'Attribute':  'VAR_FIn', 'Process':     'FTE-INDDSL_00',           'Commodity':      'DID', 'Sector':    'Industry', 'Subsector':       'Construction',       'Technology': 'Internal Combustion Engine', 'Fuel': 'Drop-In Diesel', 'Enduse':   'Motive Power, Mobile', 'Unit':     'PJ', 'Parameters': 'Fuel Consumption', 'FuelGroup': 'Renewables (direct use)'},
    {'Attribute':  'VAR_FIn', 'Process':        'FTE_TRADSL',           'Commodity':     'BDSL', 'Sector':   'Transport', 'Subsector':               'Rail',       'Technology':                      'Train', 'Fuel':      'Biodiesel', 'Enduse':           'Freight Rail', 'Unit':     'PJ', 'Parameters': 'Fuel Consumption', 'FuelGroup': 'Renewables (direct use)'},
    {'Attribute':  'VAR_FIn', 'Process':        'FTE_TRADSL',           'Commodity':     'BDSL', 'Sector':   'Transport', 'Subsector':               'Rail',       'Technology':                      'Train', 'Fuel':      'Biodiesel', 'Enduse':         'Passenger Rail', 'Unit':     'PJ', 'Parameters': 'Fuel Consumption', 'FuelGroup': 'Renewables (direct use)'},
    {'Attribute':  'VAR_FIn', 'Process':        'FTE_TRADSL',           'Commodity':     'BDSL', 'Sector':   'Transport', 'Subsector':     'Road Transport',       'Technology': 'Internal Combustion Engine', 'Fuel':      'Biodiesel', 'Enduse':                    'Bus', 'Unit':     'PJ', 'Parameters': 'Fuel Consumption', 'FuelGroup': 'Renewables (direct use)'},
    {'Attribute':  'VAR_FIn', 'Process':        'FTE_TRADSL',           'Commodity':     'BDSL', 'Sector':   'Transport', 'Subsector':     'Road Transport',       'Technology': 'Internal Combustion Engine', 'Fuel':      'Biodiesel', 'Enduse':                'Car/SUV', 'Unit':     'PJ', 'Parameters': 'Fuel Consumption', 'FuelGroup': 'Renewables (direct use)'},
    {'Attribute':  'VAR_FIn', 'Process':        'FTE_TRADSL',           'Commodity':     'BDSL', 'Sector':   'Transport', 'Subsector':     'Road Transport',       'Technology': 'Internal Combustion Engine', 'Fuel':      'Biodiesel', 'Enduse':            'Heavy Truck', 'Unit':     'PJ', 'Parameters': 'Fuel Consumption', 'FuelGroup': 'Renewables (direct use)'},
    {'Attribute':  'VAR_FIn', 'Process':        'FTE_TRADSL',           'Commodity':     'BDSL', 'Sector':   'Transport', 'Subsector':     'Road Transport',       'Technology': 'Internal Combustion Engine', 'Fuel':      'Biodiesel', 'Enduse':           'Medium Truck', 'Unit':     'PJ', 'Parameters': 'Fuel Consumption', 'FuelGroup': 'Renewables (direct use)'},
    {'Attribute':  'VAR_FIn', 'Process':        'FTE_TRADSL',           'Commodity':     'BDSL', 'Sector':   'Transport', 'Subsector':     'Road Transport',       'Technology': 'Internal Combustion Engine', 'Fuel':      'Biodiesel', 'Enduse':                'Van/Ute', 'Unit':     'PJ', 'Parameters': 'Fuel Consumption', 'FuelGroup': 'Renewables (direct use)'},
    {'Attribute':  'VAR_FIn', 'Process':        'FTE_TRAJET',           'Commodity':      'DIJ', 'Sector':   'Transport', 'Subsector':           'Aviation',       'Technology':                      'Plane', 'Fuel':    'Drop-In Jet', 'Enduse':      'Domestic Aviation', 'Unit':     'PJ', 'Parameters': 'Fuel Consumption', 'FuelGroup': 'Renewables (direct use)'},
    {'Attribute':  'VAR_FIn', 'Process':        'FTE_TRAJET',           'Commodity':      'DIJ', 'Sector':   'Transport', 'Subsector':           'Aviation',       'Technology':                      'Plane', 'Fuel':    'Drop-In Jet', 'Enduse': 'International Aviation', 'Unit':     'PJ', 'Parameters': 'Fuel Consumption', 'FuelGroup': 'Renewables (direct use)'},
    {'Attribute': 'VAR_FOut', 'Process':        'CT_COILBDS',           'Commodity':   'TOTCO2', 'Sector':   'Transport', 'Subsector':               'Rail',       'Technology':                      'Train', 'Fuel':      'Biodiesel', 'Enduse':           'Freight Rail', 'Unit': 'kt CO2', 'Parameters':        'Emissions', 'FuelGroup': 'Renewables (direct use)'},
    {'Attribute': 'VAR_FOut', 'Process':        'CT_COILBDS',           'Commodity':   'TOTCO2', 'Sector':   'Transport', 'Subsector':               'Rail',       'Technology':                      'Train', 'Fuel':      'Biodiesel', 'Enduse':         'Passenger Rail', 'Unit': 'kt CO2', 'Parameters':        'Emissions', 'FuelGroup': 'Renewables (direct use)'},
    {'Attribute': 'VAR_FOut', 'Process':        'CT_COILBDS',           'Commodity':   'TOTCO2', 'Sector':   'Transport', 'Subsector':     'Road Transport',       'Technology': 'Internal Combustion Engine', 'Fuel':      'Biodiesel', 'Enduse':                    'Bus', 'Unit': 'kt CO2', 'Parameters':        'Emissions', 'FuelGroup': 'Renewables (direct use)'},
    {'Attribute': 'VAR_FOut', 'Process':        'CT_COILBDS',           'Commodity':   'TOTCO2', 'Sector':   'Transport', 'Subsector':     'Road Transport',       'Technology': 'Internal Combustion Engine', 'Fuel':      'Biodiesel', 'Enduse':                'Car/SUV', 'Unit': 'kt CO2', 'Parameters':        'Emissions', 'FuelGroup': 'Renewables (direct use)'},
    {'Attribute': 'VAR_FOut', 'Process':        'CT_COILBDS',           'Commodity':   'TOTCO2', 'Sector':   'Transport', 'Subsector':     'Road Transport',       'Technology': 'Internal Combustion Engine', 'Fuel':      'Biodiesel', 'Enduse':            'Heavy Truck', 'Unit': 'kt CO2', 'Parameters':        'Emissions', 'FuelGroup': 'Renewables (direct use)'},
    {'Attribute': 'VAR_FOut', 'Process':        'CT_COILBDS',           'Commodity':   'TOTCO2', 'Sector':   'Transport', 'Subsector':     'Road Transport',       'Technology': 'Internal Combustion Engine', 'Fuel':      'Biodiesel', 'Enduse':           'Medium Truck', 'Unit': 'kt CO2', 'Parameters':        'Emissions', 'FuelGroup': 'Renewables (direct use)'},
    {'Attribute': 'VAR_FOut', 'Process':        'CT_COILBDS',           'Commodity':   'TOTCO2', 'Sector':   'Transport', 'Subsector':     'Road Transport',       'Technology': 'Internal Combustion Engine', 'Fuel':      'Biodiesel', 'Enduse':                'Van/Ute', 'Unit': 'kt CO2', 'Parameters':        'Emissions', 'FuelGroup': 'Renewables (direct use)'},
    {'Attribute': 'VAR_FOut', 'Process':        'CT_CWODDID',           'Commodity':   'TOTCO2', 'Sector':    'Industry', 'Subsector':       'Construction',       'Technology': 'Internal Combustion Engine', 'Fuel': 'Drop-In Diesel', 'Enduse':   'Motive Power, Mobile', 'Unit': 'kt CO2', 'Parameters':        'Emissions', 'FuelGroup': 'Renewables (direct use)'},
    {'Attribute': 'VAR_FOut', 'Process':        'CT_CWODDID',           'Commodity':   'TOTCO2', 'Sector':    'Industry', 'Subsector':             'Mining',       'Technology': 'Internal Combustion Engine', 'Fuel': 'Drop-In Diesel', 'Enduse':   'Motive Power, Mobile', 'Unit': 'kt CO2', 'Parameters':        'Emissions', 'FuelGroup': 'Renewables (direct use)'},
    {'Attribute': 'VAR_FOut', 'Process':        'CT_CWODDID',           'Commodity':   'TOTCO2', 'Sector':   'Transport', 'Subsector':           'Aviation',       'Technology':                      'Plane', 'Fuel':    'Drop-In Jet', 'Enduse':      'Domestic Aviation', 'Unit': 'kt CO2', 'Parameters':        'Emissions', 'FuelGroup': 'Renewables (direct use)'},
    {'Attribute': 'VAR_FOut', 'Process':        'T_F_ISHIPP15',         'Commodity':   'TRACO2', 'Sector':   'Transport', 'Subsector':           'Shipping',       'Technology':                       'Ship', 'Fuel':       'Fuel Oil', 'Enduse': 'International Shipping', 'Unit': 'kt CO2', 'Parameters':        'Emissions', 'FuelGroup': 'Fossil Fuels'},
])


#### The following rulesets are used to tweak the data after the initial processing

ALWAYS_PRESENT_EMISSIONS_RULES = [
    ({"Parameters": "End Use Demand"}, "newrow", {'Parameters': 'Emissions', 'Unit': 'Mt CO<sub>2</sub>/yr', 'Value': 0}),
    ({"Parameters": "Fuel Consumption"}, "newrow", {'Parameters': 'Emissions', 'Unit': 'Mt CO<sub>2</sub>/yr', 'Value': 0}),
    ({'Parameters': 'Feedstock'}, 'newrow', {'Parameters': 'Emissions', 'Unit': 'Mt CO<sub>2</sub>/yr', 'Value': 0}),
    ({'Parameters': 'Grid Injection (from Storage)'}, 'newrow', {'Parameters': 'Emissions', 'Unit': 'Mt CO<sub>2</sub>/yr', 'Value': 0}),
    ({'Parameters': 'Gross Electricity Storage'}, 'newrow', {'Parameters': 'Emissions', 'Unit': 'Mt CO<sub>2</sub>/yr', 'Value': 0}),
    ({'Parameters': 'Electricity Generation'}, 'newrow', {'Parameters': 'Emissions', 'Unit': 'Mt CO<sub>2</sub>/yr', 'Value': 0}),
    ({'Parameters': 'Distance Travelled'}, 'newrow', {'Parameters': 'Emissions', 'Unit': 'Mt CO<sub>2</sub>/yr', 'Value': 0}),
    ({'Parameters': 'Number of Vehicles'}, 'newrow', {'Parameters': 'Emissions', 'Unit': 'Mt CO<sub>2</sub>/yr', 'Value': 0})
]

RENEWABLE_FUEL_ALLOCATION_RULES = [
    ({"FuelSourceProcess": "SUP_BIGNGA", "Commodity": "NGA"}, "inplace", {"Fuel": "Biogas"}),
    ({"FuelSourceProcess": "SUP_H2NGA", "Commodity": "NGA"}, "inplace", {"Fuel": "Natural Gas From Green Hydrogen"}),
    ({"FuelSourceProcess": "CT_COILBDS", "Commodity": "BDSL"}, "inplace", {"Fuel": "Biodiesel"}),
    ({"FuelSourceProcess": "CT_CWODDID", "Commodity": "DID"}, "inplace", {"Fuel": "Drop-In Diesel"}),
    ({"FuelSourceProcess": "CT_CWODDID", "Commodity": "DIJ"}, "inplace", {"Fuel": "Drop-In Jet"}),
    ({"FuelSourceProcess": "IMPDIJ", "Commodity": "DIJ"}, "inplace", {"Fuel": "Drop-In Jet"}),
]

THOUSAND_VEHICLE_RULES = [
    ({"Sector": "Transport", "Subsector": "Road Transport",# "Technology": "Plug-In Hybrid Vehicle",
      "Unit": "000 Vehicles"}, "inplace", {"Unit": "Number of Vehicles (Thousands)"}),
]