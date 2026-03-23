"""
All data preprocessing

Takes a standard input file and generates readable outputs

These are grouped by concept;

Energy demand
Electricity generation
etc (more to come)

"""

import numpy as np
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

BASE_YEAR = 2023
MAX_YEAR = 2050


def coerce_period_to_int(df):
    """
    Ensure Period is numeric and stored as nullable integer.
    Reports attributes where invalid years show up
    To do: list the attributes where this is acceptable
        and throw loud error if it happens to attributes that need a period
        currently judgement is required.
    """
    attributes_to_ignore = [
        # these attributes aren't relevant to "period" so should be NAs
        "Cost_Salv",
        "ObjZ",
        "Reg_irec",
        "Reg_obj",
        "Reg_wobj",
        "User_con",
    ]
    period_numeric = pd.to_numeric(df["Period"], errors="coerce")
    invalid_mask = (
        period_numeric.isna()
        & df["Period"].notna()
        & ~df["Attribute"].isin(attributes_to_ignore)
    )

    if invalid_mask.any():
        invalid_attributes = (
            df.loc[invalid_mask, "Attribute"]
            .dropna()
            .astype(str)
            .sort_values()
            .unique()
        )
        print("Note: the following attributes contain some invalid years.")
        print(
            "Please ensure these are not attributes that should have valid years for every entry:"
        )
        for atty in invalid_attributes:
            print("       -", atty)

    df = df.copy()
    df["Period"] = period_numeric.astype("Int64")
    return df


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
    df_all = coerce_period_to_int(df_all)
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
    # remove base year from timeslice data
    df = df[df["Period"] != BASE_YEAR]

    save_data(df, "generation_by_timeslice.csv")


def process_batteries(df):
    """
    Docstring for process_batteries

    :param df: Description
    """

    battery_processes = pd.read_csv(PROCESS_CONCORDANCES / "batteries.csv")

    df = df[df["Process"].isin(battery_processes["Process"])]
    df = df.merge(battery_processes, on="Process", how="left")

    df = df.rename(columns={"PV": "Value"})

    df_cap = df[df["Attribute"] == "VAR_Cap"].copy()
    df_cap["Variable"] = "Capacity"
    df_cap["Unit"] = "GW"

    battery_variables = [
        "Scenario",
        "TechnologyGroup",
        "Technology",
        "Region",
        "Period",
        "TimeSlice",
        "Vintage",
        "Variable",
        "Unit",
        "Value",
    ]
    df = pd.concat([df_cap])

    df = df.reset_index()

    df = df[battery_variables]
    save_data(df, "batteries.csv")


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
    df["Unit"] = "GW"

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

    # remove base year from timeslice data
    df = df[df["Period"] != BASE_YEAR]

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


def process_primary_energy(df):
    """
    Outputs of primary energy methods, either indigenous or imports
    Labels should include method (import/indigenous)

    This currently takes processes defined as "prduction" ie processes that produce
      primary energy categorised as MIN/IMP

    For primary energy with no restraints or costs on production
        (ie wind/solar/hydro/geo)
    Because we represent the costs of collection, rather than production,
        these won't be captured here

    If we wanted to capture these, the best approach would be to add explicit
        processes for production of those commodities then capture them labelled here.

    There's room for us to add the gaps of stuff we currently assume basically free
    We can accomplish that by just adding these as an output to a MIN process

    (wind/solar/geo/etc)
    """

    df = df[df["Attribute"] == "VAR_FOut"]

    prod_processes = pd.read_csv(PROCESS_CONCORDANCES / "production.csv")
    sets_units = pd.read_csv(PROCESS_CONCORDANCES / "process_sets_and_units.csv")
    sets_units = sets_units.rename(columns={"techname": "Process"})
    fuels = pd.read_csv(COMMODITY_CONCORDANCES / "energy.csv")

    # only energy outputs of identified production processes
    # including unit settings from inputs
    df = df.merge(prod_processes, on="Process", how="inner")
    df = df.merge(fuels, on="Commodity", how="inner")
    df = df.merge(sets_units, on="Process", how="inner")

    # some quick naming
    df["Variable"] = "Primary Energy Production"
    df = df.rename(
        columns={
            "tact": "Unit",
            "PV": "Value",
        }
    )

    prod_variables = [
        "Scenario",
        "Attribute",
        "Variable",
        "Imported",
        "Renewable",
        "FuelGroup",
        "Fuel",
        "FuelDetail",
        "Process",
        "Region",
        "Vintage",
        "TimeSlice",
        "Period",
        "Value",
        "Unit",
    ]

    df = df[prod_variables]

    save_data(df, "primary_energy.csv")


def process_energy_service_demand(df):
    """
    ESD methods, or the output of demand devices
    These should basically line up with our constraints so will be good to measure these
    We have to be quite careful with units both in processing and display
    Excludes Road Transport which is handled separately in process_transport_energy_service_demand
    """

    demand_processes = pd.read_csv(
        PROCESS_CONCORDANCES / "demand.csv"
    ).drop_duplicates()
    demand_commodities = pd.read_csv(COMMODITY_CONCORDANCES / "demand.csv")
    com_units = pd.read_csv(COMMODITY_CONCORDANCES / "commodity_sets_and_units.csv")

    # Exclude Road Transport sector processes (handled separately)
    demand_processes = demand_processes[
        ~(
            (demand_processes["SectorGroup"] == "Transport")
            & (demand_processes["Sector"] == "Road Transport")
        )
    ].copy()

    # get the output of all demand processes
    esd = df[df["Process"].isin(demand_processes["Process"].unique())].copy()
    esd = esd[esd["Commodity"].isin(demand_commodities["Commodity"].unique())]
    esd = esd[esd["Attribute"] == "VAR_FOut"]

    # include only demand commodity outputs
    # this should exclude the emissions but theoretically any other outputs
    # auxiliary production etc
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


def get_data_by_timeslice(filename):
    """
    Takes an existing file and converts it to load by timeslice
    Only works on PJ, and converts to GWh, then uses YRFR to convert to GW per hour
    """

    df = pd.read_parquet(FINAL_DATA / filename)

    df = df[df["Unit"] == "PJ"]

    yrfr = pd.read_csv(PREP_STAGE_2 / "settings/load_curves/yrfr.csv")

    # add year fractions
    df = df.merge(yrfr, on="TimeSlice", how="left")

    # do annuals too
    df["YRFR"] = np.where(df["TimeSlice"] == "ANNUAL", 1, df["YRFR"])

    # calculate average load (Value unit is PJ)
    df["Hours"] = df["YRFR"] * 24 * 365
    df["GWh"] = df["Value"] * 277.777777778
    df["GW"] = df["GWh"] / df["Hours"]
    df["Variable"] = "Average output"
    df["Unit"] = "GW"
    df["Value"] = df["GW"]

    # remove BY from this
    df = coerce_period_to_int(df)
    df = df[df["Period"] != BASE_YEAR]

    return df


def get_esd_by_timeslice():
    """Wrapper for energy service demand outputs by timeslice"""
    esd = get_data_by_timeslice("energy_service_demand.parquet")
    save_data(esd, "esd_by_timeslice.parquet")


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

    # for all-purpose emissions, we add extra labels to electricity generation
    for label in ["SectorGroup", "Sector", "EnduseGroup", "EndUse"]:
        ele_generation_concordance[label] = "Electricity generation"

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

    # add labels
    df_emissions["Unit"] = "kt CO2e"
    df_emissions = df_emissions.rename(columns={"PV": "Value"})
    df_emissions = df_emissions.merge(conc, on="Process", how="left")

    # remove international transport from emissions
    uses_to_remove = ["International Shipping", "International Aviation"]
    df_emissions = df_emissions[~df_emissions["EndUse"].isin(uses_to_remove)]

    save_data(df_emissions, "emissions.csv")


def process_transport_energy_demand(df):
    """
    Road transport sector-specific energy demand processing with utilization breakdown.

    Filters energy demand for Road Transport only and extracts utilization
    information (Low/Med/High) from process names to provide detailed breakdowns
    by vehicle type and utilization level.

    Key differences from process_energy_demand:
    - Filters only Road Transport sector
    - Extracts utilization level (LOW/MED/HIGH) from process identifiers
    - Maintains detailed vehicle technology information for each mode
    """

    demand_processes = pd.read_csv(
        PROCESS_CONCORDANCES / "demand.csv"
    ).drop_duplicates()
    energy_commodities = pd.read_csv(COMMODITY_CONCORDANCES / "energy.csv")

    # Filter for Road Transport sector only
    transport_processes = demand_processes[
        (demand_processes["SectorGroup"] == "Transport")
        & (demand_processes["Sector"] == "Road Transport")
    ].copy()

    # Get transport energy demand from the main dataframe
    df_transport = df[df["Process"].isin(transport_processes["Process"].unique())]
    df_transport = df_transport[df_transport["Attribute"] == "VAR_FIn"]

    df_transport = df_transport.merge(transport_processes, on="Process", how="left")
    df_transport = df_transport.merge(energy_commodities, on=["Commodity"], how="left")

    # Extract utilization level from process name (LOW, MED, HIGH)
    # Process names like T_P_CICEPET_LOW contain utilization info
    df_transport["Utilisation"] = df_transport["Process"].str.extract(
        r"(_LOW|_MED|_HIGH)$"
    )
    df_transport["Utilisation"] = (
        df_transport["Utilisation"].str.lstrip("_").fillna("UNSPECIFIED")
    )

    # Add labels
    df_transport["Variable"] = "Transport Energy Demand"
    df_transport["Unit"] = "PJ"
    df_transport["Value"] = df_transport["PV"]

    # Order and select output variables with utilization breakdown
    transport_energy_demand_variables = [
        "Scenario",
        "Attribute",
        "Variable",
        "Sector",
        "ProcessGroup",
        "Process",
        "Utilisation",
        "CommodityGroup",
        "Commodity",
        "Fuel",
        "Period",
        "Region",
        "Vintage",
        "TimeSlice",
        "EnduseGroup",
        "EndUse",
        "TechnologyGroup",
        "Technology",
        "Unit",
        "Value",
    ]

    df_transport = df_transport[transport_energy_demand_variables]

    save_data(df_transport, "transport_energy_demand.csv")


def process_transport_energy_service_demand(df):
    """
    Road transport sector-specific energy service demand processing with utilization breakdown.

    ESD (Energy Service Demand) methods for Road Transport only.
    Extracts utilization levels (Low/Med/High) to show how different vehicle
    utilization scenarios impact service demand.

    These outputs can be compared against transport demand constraints and show the
    breakdown by vehicle type and utilization level, essential for understanding
    technology deployment and modal choices.

    All values are in BVkm (Billion Vehicle Kilometers).
    """

    demand_processes = pd.read_csv(
        PROCESS_CONCORDANCES / "demand.csv"
    ).drop_duplicates()
    demand_commodities = pd.read_csv(COMMODITY_CONCORDANCES / "demand.csv")

    # Filter for Road Transport sector only
    transport_processes = demand_processes[
        (demand_processes["SectorGroup"] == "Transport")
        & (demand_processes["Sector"] == "Road Transport")
    ].copy()

    # Get the output of transport demand processes
    tesd = df[df["Process"].isin(transport_processes["Process"].unique())].copy()
    tesd = tesd[tesd["Commodity"].isin(demand_commodities["Commodity"].unique())]
    tesd = tesd[tesd["Attribute"] == "VAR_FOut"]

    # Include only demand commodity outputs
    tesd = tesd.merge(transport_processes, on="Process", how="left")

    # Extract utilization level from process name (LOW, MED, HIGH)
    tesd["Utilisation"] = tesd["Process"].str.extract(r"(_LOW|_MED|_HIGH)$")
    tesd["Utilisation"] = tesd["Utilisation"].str.lstrip("_").fillna("UNSPECIFIED")

    # Variable adjustments - set unit to BVkm for all transport ESD
    tesd["Unit"] = "BVkm"
    tesd["Variable"] = "Transport Energy Service Demand"
    tesd = tesd.rename(columns={"PV": "Value"})

    esd_transport_variables = [
        "Scenario",
        "Attribute",
        "Variable",
        "Sector",
        "ProcessGroup",
        "Process",
        "Utilisation",
        "Commodity",
        "Period",
        "Region",
        "Vintage",
        "TimeSlice",
        "EnduseGroup",
        "EndUse",
        "TechnologyGroup",
        "Technology",
        "Unit",
        "Value",
    ]

    tesd = tesd[esd_transport_variables]

    save_data(tesd, "transport_energy_service_demand.csv")


def process_transport_capacity(df):
    """
    Road transport sector-specific capacity processing with utilization breakdown.

    Processes transport capacity (VAR_CAP) for Road Transport only.
    Extracts utilization levels (Low/Med/High) from process names to show how
    different vehicle utilization scenarios affect fleet capacity requirements.

    Essential for understanding technology deployment trajectories and vehicle
    fleet composition evolution across different utilization scenarios.
    """

    demand_processes = pd.read_csv(
        PROCESS_CONCORDANCES / "demand.csv"
    ).drop_duplicates()

    # Filter for Road Transport sector only
    transport_processes = demand_processes[
        (demand_processes["SectorGroup"] == "Transport")
        & (demand_processes["Sector"] == "Road Transport")
    ].copy()

    # Get transport capacity data
    tcap = df[df["Process"].isin(transport_processes["Process"].unique())].copy()
    tcap = tcap[tcap["Attribute"] == "VAR_Cap"]

    # Include only transport processes with labels
    tcap = tcap.merge(transport_processes, on="Process", how="left")

    # Extract utilization level from process name (LOW, MED, HIGH)
    tcap["Utilisation"] = tcap["Process"].str.extract(r"(_LOW|_MED|_HIGH)$")
    tcap["Utilisation"] = tcap["Utilisation"].str.lstrip("_").fillna("UNSPECIFIED")

    # Variable adjustments
    tcap["Variable"] = "Transport Capacity"
    tcap["Unit"] = "000vehicles"
    tcap = tcap.rename(columns={"PV": "Value"})

    transport_capacity_variables = [
        "Scenario",
        "Attribute",
        "Variable",
        "Sector",
        "ProcessGroup",
        "Process",
        "Utilisation",
        "Period",
        "Region",
        "Vintage",
        "TimeSlice",
        "EnduseGroup",
        "EndUse",
        "TechnologyGroup",
        "Technology",
        "Unit",
        "Value",
    ]

    tcap = tcap[transport_capacity_variables]

    save_data(tcap, "transport_capacity.csv")


def check_df(df):
    """scratch function"""

    df = df.copy()

    df = df[df["Attribute"] == "VAR_FOut"]
    df = df[df["Commodity"] == "ELC"]
    df = df[df["Period"] == 2023]

    df = df.groupby(["Period", "Scenario"])["PV"].sum().reset_index()
    print(df)


def main():
    """
    Orchestrates processing for all relevant outputs.
    """
    print("Processing all scenario files...")
    df = load_scenario_results(current_scenarios)

    df = df[(df["Period"] <= MAX_YEAR).fillna(False)]

    process_primary_energy(df)
    process_energy_service_demand(df)
    process_energy_demand(df)
    process_electricity_generation(df)
    process_infeasible_data(df)
    process_emissions(df)
    process_generation_by_timeslice(df)
    process_electricity_demand_by_timeslice(df)

    process_batteries(df)

    process_transport_energy_demand(df)
    process_transport_energy_service_demand(df)
    process_transport_capacity(df)

    get_esd_by_timeslice()


if __name__ == "__main__":

    main()
