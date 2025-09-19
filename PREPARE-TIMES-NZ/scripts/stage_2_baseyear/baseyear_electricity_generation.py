"""
Base-year Electricity Generation builder for the TIMES-NZ preparation pipeline.

Full methodology description:
'docs/model_methodology/base_year_electricity.md'

The script:

1. Reads EA/MBIE/EECA and custom assumption sources.
2. Creates a 2023 base-year generation table with capacities, technologies,
   heat-rates, O&M, fuel delivery costs, etc.
3. Calibrates to MBIE totals and back-fills “generic” plants where needed.
4. Outputs a tidy long-format CSV plus calibration check files.

Run directly::

    python -m prepare_times_nz.stages.baseyear_electricity_generation
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from prepare_times_nz.utilities.data_cleaning import pascal_case, remove_diacritics
from prepare_times_nz.utilities.filepaths import (
    CONCORDANCES,
    DATA_RAW,
    STAGE_1_DATA,
    STAGE_2_DATA,
)
from prepare_times_nz.utilities.logger_setup import logger

# --------------------------------------------------------------------------- #
# Imports
# --------------------------------------------------------------------------- #


# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #
BASE_YEAR = 2023
SHOW_CHECKS = True

CUSTOM_ELE_ASSUMPTIONS = DATA_RAW / "coded_assumptions" / "electricity_generation"
OUTPUT_DIR = STAGE_2_DATA / "electricity"
CHECK_DIR = OUTPUT_DIR / "checks"


FUEL_CODES = CONCORDANCES / "electricity/fuel_codes.csv"

pd.set_option("display.float_format", lambda x: f"{x:.6f}")

# --------------------------------------------------------------------------- #
# Helper functions
# --------------------------------------------------------------------------- #


def assign_cogen(value: str) -> str:
    """Map EA 'COG' tech-code to 'CHP', else 'ELE'."""
    return "CHP" if value == "COG" else "ELE"


def add_output_commodity(df: pd.Series, tech_var="TechnologyCode") -> str:  # noqa: D401
    """
    TIMES output commodity code based on the Technology

    Solar gets 'ELCDD'; everything else is 'ELC'.

    Can adjust this as needed !
    """
    df["Comm-OUT"] = np.where(df[tech_var] == "SOL", "ELCDD", "ELC")
    return df


def add_input_commodity(df: pd.DataFrame):
    """
    TIMES input commodity code matching TIMES-2 mapping logic.
    Expects a "Fuel" variable like other sectors, with
    """
    conc = pd.read_csv(FUEL_CODES)
    df = df.merge(conc, on="Fuel", how="left")
    df["Fuel_TIMES"] = df["Fuel_TIMES"].fillna("UNDEFINED")
    # hve added Fuel_TIMES. specify electricity fuel:
    df["Comm-IN"] = "ELC" + df["Fuel_TIMES"]

    return df


def save_outputs(
    gen_df: pd.DataFrame,
    gen_cmp: pd.DataFrame,
    cap_cmp: pd.DataFrame,
    gen_generic: pd.DataFrame,
) -> None:
    """Persist main long-form CSV plus calibration check files."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    out_file = OUTPUT_DIR / "base_year_electricity_supply.csv"
    gen_df.to_csv(out_file, index=False, encoding="utf-8-sig")
    logger.info("Wrote base-year supply table to %s", out_file)

    gen_cmp.to_csv(CHECK_DIR / "check_ele_gen_calibration.csv", index=False)
    cap_cmp.to_csv(CHECK_DIR / "check_base_year_ele_cap_calibration.csv", index=False)
    gen_generic.to_csv(CHECK_DIR / "check_ele_gen_generated_generics.csv", index=False)


def print_checks(
    gen_cmp: pd.DataFrame, cap_cmp: pd.DataFrame, gen_generic: pd.DataFrame
) -> None:
    """Pretty-print calibration tables to stdout when SHOW_CHECKS is enabled."""
    if not SHOW_CHECKS:
        return
    print("GENERATION CHECKS:")
    print(gen_cmp)
    print("CAPACITY CHECKS:")
    print(cap_cmp)
    print("GENERIC PLANTS GENERATED:")
    print(gen_generic)


# --------------------------------------------------------------------------- #
# Main routine
# --------------------------------------------------------------------------- #


# Suppress pylint warnings (big, but minimal-change refactor)
# pylint: disable=too-many-locals,too-many-statements
def main() -> None:
    """Entry-point wrapping the original procedural script."""
    # --------------------------------------------------------------------- #
    # Directory setup (import-safe)
    # --------------------------------------------------------------------- #
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    # --------------------------------------------------------------------- #
    # Load input data
    # --------------------------------------------------------------------- #
    official_generation = pd.read_csv(
        STAGE_1_DATA / "mbie" / "mbie_ele_generation_gwh.csv"
    )
    official_generation_no_cogen = pd.read_csv(
        STAGE_1_DATA / "mbie" / "mbie_ele_only_generation.csv"
    )
    official_capacity = pd.read_csv(
        STAGE_1_DATA / "mbie" / "mbie_generation_capacity.csv"
    )
    genstack = pd.read_csv(STAGE_1_DATA / "mbie" / "gen_stack.csv")

    emi_md = pd.read_parquet(
        STAGE_1_DATA / "electricity_authority" / "emi_md.parquet", engine="pyarrow"
    )
    emi_solar = pd.read_csv(
        STAGE_1_DATA / "electricity_authority" / "emi_distributed_solar.csv"
    )

    eeca_fleet_data = pd.read_csv(CUSTOM_ELE_ASSUMPTIONS / "GenerationFleet.csv")
    custom_gen_data = pd.read_csv(CUSTOM_ELE_ASSUMPTIONS / "CurrentPlantsCustom.csv")
    generic_plant_settings = pd.read_csv(
        CUSTOM_ELE_ASSUMPTIONS / "CurrentPlantsGeneric.csv"
    )
    capacity_factors = pd.read_csv(CUSTOM_ELE_ASSUMPTIONS / "CapacityFactors.csv")
    technology_assumptions = pd.read_csv(
        CUSTOM_ELE_ASSUMPTIONS / "TechnologyAssumptions.csv"
    )

    region_island_concordance = pd.read_csv(
        CONCORDANCES / "region_island_concordance.csv"
    )
    nsp_table = pd.read_csv(
        STAGE_1_DATA / "electricity_authority" / "emi_nsp_concordances.csv"
    )

    # --------------------------------------------------------------------- #
    # EMI processing
    # --------------------------------------------------------------------- #
    emi_md["Trading_Date"] = pd.to_datetime(emi_md["Trading_Date"])
    emi_md["Period"] = emi_md["Trading_Date"].dt.year
    emi_md = (
        emi_md.groupby(["Period", "Gen_Code", "Fuel_Code", "Tech_Code"])
        .sum("Value")
        .reset_index()
    )
    emi_md = emi_md[emi_md["Period"] == BASE_YEAR]
    emi_md["Value"] = emi_md["Value"] / 1e6  # kWh → GWh
    emi_md["Unit"] = "GWh"

    # --------------------------------------------------------------------- #
    # MBIE generation summary inc. CHP split
    # --------------------------------------------------------------------- #
    generation_summary = official_generation[
        official_generation["Year"] == BASE_YEAR
    ].copy()
    generation_summary = generation_summary[
        ["Year", "FuelType", "Unit", "Value"]
    ].rename(columns={"Value": "MBIE_Value"})

    ele_only = official_generation_no_cogen.copy()
    ele_only["FuelType"] = ele_only["FuelType"].replace("Solar PV", "Solar")
    ele_only = ele_only[ele_only["Year"] == BASE_YEAR][
        ["Year", "FuelType", "Value"]
    ].rename(columns={"Value": "ELE"})

    generation_summary = generation_summary.merge(
        ele_only, how="left", on=["Year", "FuelType"]
    )
    generation_summary["ELE"] = generation_summary["ELE"].fillna(0)
    generation_summary["CHP"] = (
        generation_summary["MBIE_Value"] - generation_summary["ELE"]
    )
    generation_summary = generation_summary.drop(columns="MBIE_Value").melt(
        id_vars=["Year", "Unit", "FuelType"],
        value_vars=["ELE", "CHP"],
        var_name="GenerationType",
        value_name="MBIE_Value",
    )
    generation_summary.loc[generation_summary["FuelType"] == "Oil", "FuelType"] = (
        "Diesel"
    )

    # --------------------------------------------------------------------- #
    # Build base plant list and add EMI generation
    # --------------------------------------------------------------------- #
    base_year_gen = eeca_fleet_data[
        [
            "PlantName",
            "EMI_Name",
            "TechnologyCode",
            "FuelType",
            "POC",
            "CapacityMW",
            "YearCommissioned",
            "GenerationMethod",
        ]
    ].copy()
    base_year_gen["GenerationType"] = base_year_gen["TechnologyCode"].apply(
        assign_cogen
    )

    poc_island = nsp_table[["POC", "Island"]].drop_duplicates()
    base_year_gen = base_year_gen.merge(poc_island, how="left", on="POC").rename(
        columns={"Island": "Region"}
    )

    emi_md_per_plant = emi_md[["Gen_Code", "Value"]].rename(
        columns={"Gen_Code": "EMI_Name", "Value": "EMI_Value"}
    )
    base_year_gen_emi = base_year_gen[base_year_gen["GenerationMethod"] == "EMI"].merge(
        emi_md_per_plant, how="left", on="EMI_Name"
    )
    base_year_gen_emi["CapacityShare"] = base_year_gen_emi[
        "CapacityMW"
    ] / base_year_gen_emi.groupby("EMI_Name")["CapacityMW"].transform("sum")
    base_year_gen_emi["EECA_Value"] = (
        base_year_gen_emi["EMI_Value"] * base_year_gen_emi["CapacityShare"]
    )
    base_year_gen_emi.drop(columns=["CapacityShare"], inplace=True)

    # --------------------------------------------------------------------- #
    # Capacity-factor & custom generation
    # --------------------------------------------------------------------- #
    base_year_gen_cfs = base_year_gen[
        base_year_gen["GenerationMethod"] == "Capacity Factor"
    ].merge(capacity_factors, on=["FuelType", "GenerationType", "TechnologyCode"])
    base_year_gen_cfs["EECA_Value"] = (
        base_year_gen_cfs["CapacityMW"] * 8.76 * base_year_gen_cfs["CapacityFactor"]
    )

    base_year_gen_custom = (
        base_year_gen[base_year_gen["GenerationMethod"] == "Custom"]
        .merge(
            custom_gen_data, how="left", on=["PlantName", "FuelType", "TechnologyCode"]
        )
        .drop(columns="Source")
    )

    # --------------------------------------------------------------------- #
    # Distributed solar
    # --------------------------------------------------------------------- #
    df_sol = emi_solar.copy()
    df_sol["Month"] = pd.to_datetime(df_sol["Month"])
    df_sol = df_sol[df_sol["Month"].dt.month == 12]
    df_sol["Year"] = df_sol["Month"].dt.year
    df_sol = df_sol.merge(region_island_concordance, on="Region", how="left")
    df_sol["PlantName"] = "DistributedSolar" + df_sol["Sector"]
    df_sol = (
        df_sol.groupby(["Year", "PlantName", "Island", "Sector"])[
            "capacity_installed_mw"
        ]
        .sum()
        .reset_index()
    )
    df_sol = df_sol[df_sol["Year"] == BASE_YEAR]
    df_sol["total_cap"] = df_sol.groupby("Year")["capacity_installed_mw"].transform(
        "sum"
    )
    df_sol["capacity_share"] = df_sol["capacity_installed_mw"] / df_sol["total_cap"]

    solar_total = official_generation[official_generation["FuelType"] == "Solar"][
        ["Year", "Value"]
    ].rename(columns={"Value": "TotalSolarGen"})
    df_sol = df_sol.merge(solar_total, on="Year", how="left")
    df_sol["EECA_Value"] = df_sol["capacity_share"] * df_sol["TotalSolarGen"]
    df_sol["CapacityFactor"] = df_sol["EECA_Value"] / (
        df_sol["capacity_installed_mw"] * 8.760
    )

    df_sol = df_sol.rename(
        columns={"capacity_installed_mw": "CapacityMW", "Island": "Region"}
    )[["PlantName", "CapacityMW", "EECA_Value", "Region", "CapacityFactor"]]
    df_sol["GenerationType"] = "ELE"
    df_sol["GenerationMethod"] = "Solar data from MBIE"
    df_sol["TechnologyCode"] = "SOL"
    df_sol["FuelType"] = "Solar"
    base_year_gen_dist_solar = df_sol

    # --------------------------------------------------------------------- #
    # Combine plant data gathered so far
    # --------------------------------------------------------------------- #
    base_year_gen = pd.concat(
        [
            base_year_gen_emi,
            base_year_gen_custom,
            base_year_gen_cfs,
            base_year_gen_dist_solar,
        ],
        ignore_index=True,
    )

    # --------------------------------------------------------------------- #
    # Calibrate by adding generic plants
    # --------------------------------------------------------------------- #
    base_year_summary = (
        base_year_gen.groupby(["FuelType", "GenerationType"])["EECA_Value"]
        .sum()
        .reset_index()
    )

    gen_comparison = generation_summary.merge(base_year_summary, how="left")
    gen_comparison["EECA_Value"] = gen_comparison["EECA_Value"].fillna(0)
    gen_comparison["Delta"] = (
        gen_comparison["MBIE_Value"] - gen_comparison["EECA_Value"]
    )

    generic_generation = gen_comparison.merge(
        generic_plant_settings, on=["FuelType", "GenerationType"], how="inner"
    ).merge(
        capacity_factors,
        on=["FuelType", "GenerationType", "TechnologyCode"],
        how="left",
    )

    generic_generation = generic_generation[
        [
            "PlantName",
            "FuelType",
            "GenerationType",
            "TechnologyCode",
            "Delta",
            "CapacityFactor",
        ]
    ].rename(columns={"Delta": "EECA_Value"})
    generic_generation = generic_generation[generic_generation["EECA_Value"] > 0]

    region_gen = (
        base_year_gen.groupby(["Region", "GenerationType", "FuelType"])["CapacityMW"]
        .sum()
        .reset_index()
    )
    region_gen["Total"] = region_gen.groupby(["FuelType", "GenerationType"])[
        "CapacityMW"
    ].transform("sum")
    region_gen["Share"] = region_gen["CapacityMW"] / region_gen["Total"]
    region_gen = region_gen[["FuelType", "GenerationType", "Region", "Share"]]

    generic_generation = generic_generation.merge(
        region_gen, on=["FuelType", "GenerationType"], how="left"
    )
    generic_generation["Share"] = generic_generation["Share"].fillna(1)
    generic_generation["Region"] = generic_generation["Region"].fillna("NI")
    generic_generation["EECA_Value"] *= generic_generation["Share"]
    generic_generation.drop(columns="Share", inplace=True)
    generic_generation["CapacityMW"] = (
        generic_generation["EECA_Value"] * 1000 / 8760
    ) / generic_generation["CapacityFactor"]
    generic_generation["GenerationMethod"] = "Generic"

    base_year_gen = pd.concat([base_year_gen, generic_generation], ignore_index=True)

    # --------------------------------------------------------------------- #
    # Capacity calibration
    # --------------------------------------------------------------------- #
    mbie_capacity = official_capacity[official_capacity["Year"] == BASE_YEAR].copy()
    mbie_capacity = mbie_capacity[
        mbie_capacity["Technology"] != "Other electricity generation"
    ]
    mbie_capacity["GenerationType"] = "ELE"
    mbie_capacity.loc[
        mbie_capacity["Technology"] == "Gas Cogen", ["GenerationType", "Technology"]
    ] = ["CHP", "Gas"]
    mbie_capacity.loc[
        mbie_capacity["Technology"] == "Other Cogen", ["GenerationType", "Technology"]
    ] = ["CHP", "Other"]
    mbie_capacity.replace({"Solar PV": "Solar", "Coal/Gas": "Coal"}, inplace=True)
    mbie_capacity = mbie_capacity[["Technology", "GenerationType", "Value"]].rename(
        columns={"Technology": "FuelType", "Value": "MBIE_Value"}
    )

    base_year_summary_cap = base_year_gen.copy()
    base_year_summary_cap = base_year_summary_cap[
        ~(
            (base_year_summary_cap["TechnologyCode"] == "RNK")
            & (base_year_summary_cap["FuelType"] == "Gas")
        )
    ]
    base_year_summary_cap.loc[
        (base_year_summary_cap["GenerationType"] == "CHP")
        & (base_year_summary_cap["FuelType"] != "Gas"),
        "FuelType",
    ] = "Other"
    base_year_summary_cap = (
        base_year_summary_cap.groupby(["FuelType", "GenerationType"])["CapacityMW"]
        .sum()
        .reset_index()
    ).rename(columns={"CapacityMW": "EECA_Value"})

    cap_comparison = mbie_capacity.merge(
        base_year_summary_cap, on=["FuelType", "GenerationType"], how="left"
    )
    cap_comparison["EECA_Value"] = cap_comparison["EECA_Value"].fillna(0)
    cap_comparison["Delta"] = (
        cap_comparison["EECA_Value"] - cap_comparison["MBIE_Value"]
    )

    # --------------------------------------------------------------------- #
    # Technical parameters & TIMES metadata
    # --------------------------------------------------------------------- #
    base_year_gen["CapacityFactor"] = base_year_gen["EECA_Value"] / (
        base_year_gen["CapacityMW"] * 8.760
    )
    base_year_gen = base_year_gen.merge(
        technology_assumptions, on="TechnologyCode", how="left"
    )

    base_year_gen.rename(
        columns={"CapacityFactor": "ImpliedCapacityFactor"}, inplace=True
    )
    base_year_gen = base_year_gen.merge(
        capacity_factors,
        on=["FuelType", "GenerationType", "TechnologyCode"],
        how="left",
    )

    # Genstack cost/heat-rate parameters (specific + generic) ----------------
    eeca_mbie_name = eeca_fleet_data[["PlantName", "FuelType", "MBIE_Name"]]
    base_year_gen = base_year_gen.merge(
        eeca_mbie_name, on=["PlantName", "FuelType"], how="left"
    )

    reference_genstack = genstack[genstack["Scenario"] == "Reference"]
    current_genstack = reference_genstack[reference_genstack["Status"] == "Current"]
    specific_parameters = current_genstack[
        [
            "Plant",
            "Heat Rate (GJ/GWh)",
            "Variable operating costs (NZD/MWh)",
            "Fixed operating costs (NZD/kW/year)",
            "Fuel delivery costs (NZD/GJ)",
        ]
    ].rename(
        columns={
            "Plant": "MBIE_Name",
            "Heat Rate (GJ/GWh)": "specific_heatrate_gj_gwh",
            "Variable operating costs (NZD/MWh)": "specific_varom_nzd_mwh",
            "Fixed operating costs (NZD/kW/year)": "specific_fixom_nzd_kw_year",
            "Fuel delivery costs (NZD/GJ)": "specific_fuel_delivery_costs_nzd_gj",
        }
    )
    base_year_gen = base_year_gen.merge(specific_parameters, on="MBIE_Name", how="left")

    genstack_avg_parameters = (
        reference_genstack.groupby("TechName")[
            [
                "Heat Rate (GJ/GWh)",
                "Variable operating costs (NZD/MWh)",
                "Fixed operating costs (NZD/kW/year)",
                "Fuel delivery costs (NZD/GJ)",
            ]
        ]
        .mean()
        .reset_index()
        .rename(
            columns={
                "Heat Rate (GJ/GWh)": "generic_heatrate_gj_gwh",
                "Variable operating costs (NZD/MWh)": "generic_varom_nzd_mwh",
                "Fixed operating costs (NZD/kW/year)": "generic_fixom_nzd_kw_year",
                "Fuel delivery costs (NZD/GJ)": "generic_fuel_delivery_costs_nzd_gj",
            }
        )
    )

    techs_to_fuels = pd.DataFrame(
        np.array(
            [
                ["Coal", "RNK", "Coal"],
                ["Gas", "RNK", "Gas"],
                ["Cogeneration, gas-fired", "COG", "Gas"],
                ["Cogeneration, other", "COG", "Wood"],
                ["Cogeneration, other", "COG", "Coal"],
                ["Cogeneration, other", "COG", "Biogas"],
                ["Geothermal", "GEO", "Geothermal"],
                ["Geothermal", "COG", "Geothermal"],
                ["Reciprocating Biogas engine", "BIG", "Biogas"],
                ["Combined cycle gas turbine", "CCGT", "Gas"],
                ["Open cycle gas turbine", "OCGT", "Gas"],
                ["Peaker, diesel-fired OCGT", "OCGT", "Diesel"],
                ["Peaker, diesel-fired OCGT", "DSL", "Diesel"],
                ["Solar", "SOL", "Solar"],
                ["Wind", "WIN", "Wind"],
                ["Hydro, schedulable", "HYD", "Hydro"],
                ["Hydro, run of river", "HYDRR", "Hydro"],
            ]
        ),
        columns=["TechName", "TechnologyCode", "FuelType"],
    )

    base_year_gen = base_year_gen.merge(
        techs_to_fuels, on=["FuelType", "TechnologyCode"], how="left"
    )
    base_year_gen = base_year_gen.merge(
        genstack_avg_parameters, on="TechName", how="left"
    )

    base_year_gen["HeatRate"] = base_year_gen["specific_heatrate_gj_gwh"].fillna(
        base_year_gen["generic_heatrate_gj_gwh"]
    )
    base_year_gen["VarOM"] = base_year_gen["specific_varom_nzd_mwh"].fillna(
        base_year_gen["generic_varom_nzd_mwh"]
    )
    base_year_gen["FixOM"] = base_year_gen["specific_fixom_nzd_kw_year"].fillna(
        base_year_gen["generic_fixom_nzd_kw_year"]
    )
    base_year_gen["FuelDelivCost"] = base_year_gen[
        "specific_fuel_delivery_costs_nzd_gj"
    ].fillna(base_year_gen["generic_fuel_delivery_costs_nzd_gj"])

    base_year_gen.drop(
        columns=[
            "generic_heatrate_gj_gwh",
            "generic_varom_nzd_mwh",
            "generic_fixom_nzd_kw_year",
            "generic_fuel_delivery_costs_nzd_gj",
            "specific_heatrate_gj_gwh",
            "specific_varom_nzd_mwh",
            "specific_fixom_nzd_kw_year",
            "specific_fuel_delivery_costs_nzd_gj",
            "TechName",
        ],
        inplace=True,
    )

    base_year_gen["FuelEfficiency"] = 3600 / base_year_gen["HeatRate"]

    # TIMES process names & commodities ------------------------------------
    base_year_gen["Process"] = (
        "ELC_"
        + base_year_gen["FuelType"]
        + "_"
        + base_year_gen["TechnologyCode"]
        + "_"
        + base_year_gen["PlantName"].apply(pascal_case).apply(remove_diacritics)
    )
    base_year_gen.loc[base_year_gen["TechnologyCode"] == "RNK", "Process"] = (
        "ELC_RNK_HuntlyUnits1-4"
    )

    base_year_gen = add_output_commodity(base_year_gen)
    # input commodity functin works on full df not per row
    base_year_gen["Fuel"] = base_year_gen["FuelType"]
    base_year_gen = add_input_commodity(base_year_gen)

    # --------------------------------------------------------------------- #
    # Tidy to long-format with units
    # --------------------------------------------------------------------- #
    variable_unit_map = {
        "Capacity": "MW",
        "Generation": "GWh",
        "CapacityFactor": "%",
        "VarOM": "2023 NZD/MWh",
        "FixOM": "2023 NZD/kw",
        "FuelDelivCost": "2023 NZD/GJ",
        "PlantLife": "Years",
        "PeakContribution": "%",
        "FuelEfficiency": "%",
    }

    base_year_gen = base_year_gen.rename(
        columns={"EECA_Value": "Generation", "CapacityMW": "Capacity"}
    )
    value_vars = list(variable_unit_map.keys())
    id_vars = [col for col in base_year_gen.columns if col not in value_vars]

    base_year_gen = base_year_gen.melt(
        id_vars=id_vars, value_vars=value_vars, var_name="Variable", value_name="Value"
    )
    base_year_gen["Unit"] = base_year_gen["Variable"].map(variable_unit_map)

    # --------------------------------------------------------------------- #
    # Output + checks
    # --------------------------------------------------------------------- #
    save_outputs(base_year_gen, gen_comparison, cap_comparison, generic_generation)
    print_checks(gen_comparison, cap_comparison, generic_generation)


# --------------------------------------------------------------------------- #
# Guard
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    main()
