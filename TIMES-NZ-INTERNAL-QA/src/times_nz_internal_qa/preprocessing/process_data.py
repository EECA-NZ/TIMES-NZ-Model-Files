"""
All data preprocessing

Takes a standard input file and generates readable outputs

These are grouped by concept;

Energy demand
Electricity generation
etc (more to come)

"""

import pandas as pd
from times_nz_internal_qa.preprocessing.get_data import load_scenario_results
from times_nz_internal_qa.utilities.filepaths import (
    COMMODITY_CONCORDANCES,
    CONCORDANCES,
    FINAL_DATA,
    PROCESS_CONCORDANCES,
)

SCENARIO_NAME = "times-nz_v300_trad"


def process_electricity_generation(scenario_name):
    """
    Load full scenario data for `scenario_name`
    Identify all elec generation processes and output each with human readable labels

    Uses an input attribute

    """

    # load data
    df = load_scenario_results(scenario_name)

    # get concordances
    processes = pd.read_csv(PROCESS_CONCORDANCES / "elec_generation.csv")
    fuels = pd.read_csv(COMMODITY_CONCORDANCES / "energy.csv")
    emissions = pd.read_csv(COMMODITY_CONCORDANCES / "emissions.csv")
    commodities = pd.concat([fuels, emissions])
    attributes = pd.read_csv(CONCORDANCES / "attributes/attributes_for_ele_gen.csv")
    # ele specific labels for techs
    tech_codes = pd.read_csv(CONCORDANCES / "electricity/tech_codes.csv")

    # filter to labelled processes only
    df = df[df["Process"].isin(processes["Process"].unique())]

    # filter to our specific attributes. These are defined in the input file
    df = df[df["Attribute"].isin(attributes["Attribute"].unique())]

    # add labels:

    # process/tech labels
    df = df.merge(processes, on="Process", how="left")
    # commodity labels and groups
    df = df.merge(commodities, on="Commodity", how="left")
    # attributes, variables, units, based on commodity group
    df = df.merge(attributes, on=["Attribute", "CommodityGroup"], how="left")
    # names for our tech codes
    df = df.merge(tech_codes, on="Tech_TIMES", how="left")

    # rename
    df = df.rename(columns={"PV": "Value"})
    # label with scenario name
    df["Scenario"] = SCENARIO_NAME

    # sort and select variables

    ele_variables = [
        "Scenario",
        "Attribute",
        "Variable",
        "ProcessGroup",
        "Process",
        "PlantName",
        "TechnologyGroup",
        "Technology",
        "CommodityGroup",
        "Commodity",
        "Fuel",
        "Region",
        "Vintage",
        "TimeSlice",
        "Period",
        "Value",
        "Unit",
    ]

    df = df[ele_variables]

    # save
    df.to_csv(FINAL_DATA / "elec_generation.csv", index=False, encoding="utf-8-sig")


def process_energy_demand(scenario_name):
    """
    Load full scenario data for `scenario_name`
    Identify all energy demand processes and output each with human readable labels
    For these we currently only extract energy demand, not capacity or output.
    """

    df = load_scenario_results(scenario_name=scenario_name)

    demand_processes = pd.read_csv(PROCESS_CONCORDANCES / "demand.csv")
    energy_commodities = pd.read_csv(COMMODITY_CONCORDANCES / "energy.csv")

    df = df[df["Process"].isin(demand_processes["Process"].unique())]

    df = df[df["Attribute"] == "VAR_FIn"]

    df = df.merge(demand_processes, on="Process", how="left")
    df = df.merge(energy_commodities, on=["Commodity"], how="left")

    # add labels (could also do this in an attributes concordance file, like with ele)
    df["Variable"] = "Energy demand"
    df["Unit"] = "PJ"
    df["Scenario"] = scenario_name
    df["Value"] = df["PV"]

    # order and select output variables

    energy_demand_variables = [
        "Scenario",
        "Attribute",
        "Variable",
        "ProcessGroup",
        "Process",
        "CommodityGroup",
        "Commodity",
        "Fuel",
        "Period",
        "Region",
        "Vintage",
        "TimeSlice",
        "SectorGroup",
        "Sector",
        "EnduseGroup",
        "EndUse",
        "TechnologyGroup",
        "Technology",
        "Unit",
        "Value",
    ]

    df = df[energy_demand_variables]

    df.to_csv(FINAL_DATA / "energy_demand.csv", index=False, encoding="utf-8-sig")


# print(demand_processes)


def main():
    """
    Orchestrates processing for all relevant outputs.
    """
    process_energy_demand(SCENARIO_NAME)
    process_electricity_generation(SCENARIO_NAME)


if __name__ == "__main__":
    main()
