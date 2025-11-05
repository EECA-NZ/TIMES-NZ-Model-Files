"""
All data preprocessing

Takes a standard input file and generates readable outputs

These are grouped by concept;

Energy demand
Electricity generation
etc (more to come)

"""

import pandas as pd
from times_nz_internal_qa.config import current_scenarios
from times_nz_internal_qa.utilities.filepaths import (
    COMMODITY_CONCORDANCES,
    CONCORDANCE_PATCHES,
    FINAL_DATA,
    PREP_STAGE_2,
    PROCESS_CONCORDANCES,
    SCENARIO_FILES,
)


def save_data(df, name, method="parquet"):
    """Save final outputs to <repo>/data (creates folder if missing)."""
    name = name.removesuffix(".csv").removesuffix(".parquet")
    FINAL_DATA.mkdir(parents=True, exist_ok=True)  # <-- ensure folder exists

    if method == "parquet":
        df.to_parquet(FINAL_DATA / f"{name}.parquet", engine="pyarrow")
    else:
        df.to_csv(FINAL_DATA / f"{name}.csv", index=False, encoding="utf-8-sig")


def load_scenario_results(scenarios):
    """
    Loads each scenario result file based on the input scenario list
    concatenates and returns a df
    """
    result_list = []
    for scenario in scenarios:
        df = pd.read_csv(SCENARIO_FILES / f"{scenario}.csv", low_memory=False)
        df["Scenario"] = scenario
        result_list.append(df)

    df_all = pd.concat(result_list)
    return df_all


def process_electricity_generation(df):
    """
    Identify all elec generation processes and output each with human readable labels

    Uses an input attribute list to identify the model results we want
    """

    # load data

    # get concordances
    processes = pd.read_csv(PROCESS_CONCORDANCES / "elec_generation.csv")
    fuels = pd.read_csv(COMMODITY_CONCORDANCES / "energy.csv")
    emissions = pd.read_csv(COMMODITY_CONCORDANCES / "emissions.csv")
    commodities = pd.concat([fuels, emissions])
    attributes = pd.read_csv(
        CONCORDANCE_PATCHES / "attributes/attributes_for_ele_gen.csv"
    )
    # ele specific labels for techs

    # filter to labelled processes only
    df = df[df["Process"].isin(processes["Process"].unique())]

    # filter to our specific attributes. These are defined in the input file
    df = df[df["Attribute"].isin(attributes["Attribute"].unique())]

    # add labels:
    df = df.merge(processes, on="Process", how="left")
    # commodity labels and groups
    df = df.merge(commodities, on="Commodity", how="left")
    # attributes, variables, units, based on commodity group
    df = df.merge(attributes, on=["Attribute", "CommodityGroup"], how="left")

    # rename
    df = df.rename(columns={"PV": "Value"})

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
    save_data(df, "elec_generation.csv")


def process_generation_by_timeslice(df):
    """
    Single preprocessing for timeslice generation
    Pulls yrfr and calculates average load in GW per slice

    Starts by matching the electricity method, then trims
    """
    yrfr = pd.read_csv(PREP_STAGE_2 / "settings/load_curves/yrfr.csv")
    processes = pd.read_csv(PROCESS_CONCORDANCES / "elec_generation.csv")
    fuels = pd.read_csv(COMMODITY_CONCORDANCES / "energy.csv")
    emissions = pd.read_csv(COMMODITY_CONCORDANCES / "emissions.csv")
    commodities = pd.concat([fuels, emissions])
    attributes = pd.read_csv(
        CONCORDANCE_PATCHES / "attributes/attributes_for_ele_gen.csv"
    )
    # ele specific labels for techs

    # filter to labelled processes only
    df = df[df["Process"].isin(processes["Process"].unique())]

    # filter to our specific attributes. These are defined in the input file
    df = df[df["Attribute"].isin(attributes["Attribute"].unique())]

    # add labels:
    df = df.merge(processes, on="Process", how="left")
    # commodity labels and groups
    df = df.merge(commodities, on="Commodity", how="left")
    # attributes, variables, units, based on commodity group
    df = df.merge(attributes, on=["Attribute", "CommodityGroup"], how="left")

    df = df[df["Variable"] == "Electricity generation"]

    # add year fractions

    df = df.merge(yrfr, on="TimeSlice", how="left")

    #

    # calculate average load (PV Unit is PJ)
    df["Hours"] = df["YRFR"] * 24 * 365
    df["GWh"] = df["PV"] * 277.777777778
    df["GW"] = df["GWh"] / df["Hours"]
    df["Variable"] = "Average output"
    df["Unit"] = "GW"
    df["Value"] = df["GW"]

    ele_variables = [
        "Scenario",
        "Attribute",
        "Process",
        "PlantName",
        "TechnologyGroup",
        "Technology",
        "Region",
        "Vintage",
        "TimeSlice",
        "Period",
        "Variable",
        "Value",
        "Unit",
    ]

    df = df[ele_variables]

    save_data(df, "generation_by_timeslice.csv")


def process_electricity_demand_by_timeslice(df):
    """
    Load full scenario data for `scenario_name`
    Identify all energy demand processes and output each with human readable labels
    For these we currently only extract energy demand, not capacity or output.
    """

    demand_processes = pd.read_csv(PROCESS_CONCORDANCES / "demand.csv")
    energy_commodities = pd.read_csv(COMMODITY_CONCORDANCES / "energy.csv")
    yrfr = pd.read_csv(PREP_STAGE_2 / "settings/load_curves/yrfr.csv")

    df = df[df["Process"].isin(demand_processes["Process"].unique())]

    df = df[df["Attribute"] == "VAR_FIn"]

    df = df.merge(demand_processes, on="Process", how="left")
    df = df.merge(energy_commodities, on=["Commodity"], how="left")

    # only electricity demand
    df = df[df["Fuel"] == "Electricity"]

    # add year fractions
    df = df.merge(yrfr, on="TimeSlice", how="left")

    # check annual timeslice methods

    test = df[df["TimeSlice"] == "ANNUAL"]

    if len(test) > 0:
        print("WARNING - these electricity processes are running on annual")
        annual_commodities = test["Process"].unique().tolist()
        for c in annual_commodities:
            print("          '", c, "'")

        raise ValueError("Process timeslices must not be annual")  #

    # calculate average load (PV Unit is PJ)
    df["Hours"] = df["YRFR"] * 24 * 365
    df["GWh"] = df["PV"] * 277.777777778
    df["GW"] = df["GWh"] / df["Hours"]
    df["Variable"] = "Average output"
    df["Unit"] = "GW"
    df["Value"] = df["GW"]

    # order and select output variables

    save_data(df, "electricity_demand_by_timeslice.csv")


def process_energy_demand(df):
    """
    Load full scenario data for `scenario_name`
    Identify all energy demand processes and output each with human readable labels
    For these we currently only extract energy demand, not capacity or output.
    """

    demand_processes = pd.read_csv(PROCESS_CONCORDANCES / "demand.csv")
    energy_commodities = pd.read_csv(COMMODITY_CONCORDANCES / "energy.csv")

    df = df[df["Process"].isin(demand_processes["Process"].unique())]

    df = df[df["Attribute"] == "VAR_FIn"]

    df = df.merge(demand_processes, on="Process", how="left")
    df = df.merge(energy_commodities, on=["Commodity"], how="left")

    # add labels (could also do this in an attributes concordance file, like with ele)
    df["Variable"] = "Energy demand"
    df["Unit"] = "PJ"
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
        # pylint:disable = duplicate-code
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

    save_data(df, "energy_demand.csv")


def process_energy_service_demand(df):
    """
    ESD methods, or the output of demand devices
    These should basically line up with our constraints so will be good to measure these
    We have to be quite careful with units both in processing and display
    """

    demand_processes = pd.read_csv(PROCESS_CONCORDANCES / "demand.csv")
    demand_commodities = pd.read_csv(COMMODITY_CONCORDANCES / "demand.csv")
    com_units = pd.read_csv(COMMODITY_CONCORDANCES / "commodity_sets_and_units.csv")

    # get the output of all demand processes
    esd = df[df["Process"].isin(demand_processes["Process"].unique())].copy()
    esd = esd[esd["Attribute"] == "VAR_FOut"]

    # include only demand commodity outputs
    # this should exclude the emissions but theoretically any other outputs
    # auxiliary production etc
    esd = esd[esd["Commodity"].isin(demand_commodities["Commodity"].unique())]
    esd = esd.merge(demand_processes, on="Process", how="left")

    # we now need to identify the unit. We'll do this based on the commodity unit
    com_units = com_units[com_units["csets"] == "DEM"]
    com_units = com_units.rename(
        columns={
            "commname": "Commodity",
            "unit": "Unit",
        }
    )

    com_units = com_units[["Commodity", "Unit"]]
    # add this to main table
    esd = esd.merge(com_units, on="Commodity", how="left")

    # a few other var adjustments

    esd["Variable"] = "Energy service demand"
    esd = esd.rename(columns={"PV": "Value"})

    esd_variables = [
        "Scenario",
        "Attribute",
        "Variable",
        "ProcessGroup",
        "Process",
        "Commodity",
        "Period",
        "Region",
        "Vintage",
        "TimeSlice",
        # pylint:disable = duplicate-code
        "SectorGroup",
        "Sector",
        "EnduseGroup",
        "EndUse",
        "TechnologyGroup",
        "Technology",
        "Unit",
        "Value",
    ]
    esd = esd[esd_variables]
    save_data(esd, "energy_service_demand.csv")


def process_infeasible_data(df):
    """
    This is used for getting a better look at the autogenerated dummy processes
    """
    dummy_processes = pd.read_csv(PROCESS_CONCORDANCES / "dummies.csv")
    demand_commodities = pd.read_csv(COMMODITY_CONCORDANCES / "demand.csv")
    energy_commodities = pd.read_csv(COMMODITY_CONCORDANCES / "energy.csv")

    # only var_fout is relevant - act is also available but who cares
    # cost_act is available - might be worth something later

    df = df[df["Attribute"] == "VAR_FOut"].copy()
    df["Variable"] = "Production"
    df = df.merge(dummy_processes, on="Process", how="left")
    df = df.rename(columns={"PV": "Value"})

    # we do the demand and energy components separately
    df_dummy_demand = df[df["Process"] == "IMPDEMZ"]
    df_dummy_energy = df[df["Process"] == "IMPNRGZ"]

    # attys = df["Attribute"].unique()

    df_dummy_demand = df_dummy_demand.merge(
        demand_commodities, on="Commodity", how="left"
    )
    df_dummy_energy = df_dummy_energy.merge(
        energy_commodities, on="Commodity", how="left"
    )

    save_data(df_dummy_demand, "dummy_demand.csv")
    save_data(df_dummy_energy, "dummy_energy.csv")


def process_emissions(df):
    """
    All emissions outputs!
    """

    df_s = pd.read_csv(COMMODITY_CONCORDANCES / "emissions.csv")

    demand_concordance = pd.read_csv(PROCESS_CONCORDANCES / "demand.csv")
    ele_generation_concordance = pd.read_csv(
        PROCESS_CONCORDANCES / "elec_generation.csv"
    )
    production_concordance = pd.read_csv(PROCESS_CONCORDANCES / "production.csv")

    conc = pd.concat(
        [demand_concordance, ele_generation_concordance, production_concordance]
    )
    conc = conc.drop("CommodityOut", axis=1)

    # emission commodities
    df_emissions = df[df["Commodity"].isin(df_s["Commodity"])]
    # only outputs (not costs)
    df_emissions = df_emissions[df_emissions["Attribute"] == "VAR_FOut"]
    # remove TOTCO2 (not helpful)
    df_emissions = df_emissions[df_emissions["Commodity"] != "TOTCO2"]

    # some labels
    df_emissions["Unit"] = "kt CO2e"
    df_emissions = df_emissions.rename(columns={"PV": "Value"})
    df_emissions = df_emissions.merge(conc, on="Process", how="left")

    save_data(df_emissions, "emissions.csv")


def main():
    """
    Orchestrates processing for all relevant outputs.
    """
    print("Processing all scenario files...")
    df = load_scenario_results(current_scenarios)
    process_energy_service_demand(df)
    process_energy_demand(df)
    process_electricity_generation(df)
    process_infeasible_data(df)
    process_emissions(df)
    process_generation_by_timeslice(df)
    process_electricity_demand_by_timeslice(df)
    print("Done")


if __name__ == "__main__":

    main()
