"""Residential, commercial, and industrial demand analysis charts."""

import times_nz_internal_qa.analysis.get_data as chart_data
from times_nz_internal_qa.analysis.analysis_chart_helpers import (
    PJ_TO_GWH,
    create_scenario_facet_chart,
    make_filename,
    save_chart_and_data,
    standardise_chart_data,
)

TOTAL_DEMAND_FUEL_PALETTE = [
    "#164057",
    "#ED6D63",
    "#3C4C49",
    "#447474",
    "#C346CE",
]


def create_residential_demand_chart():
    """Create residential demand area chart."""

    group_vars = [
        "Scenario",
        "Period",
        "Unit",
        "Fuel",
    ]

    res_df = chart_data.get_fuel_use_by_island_and_sector(sector_group="Residential")

    res_fuel_aggregation = {
        "Coal": "Other",
        "Diesel": "Diesel/Petrol",
        "Electricity": "Electricity",
        "LPG": "LPG",
        "Natural gas": "Natural gas",
        "Petrol": "Diesel/Petrol",
        "Solar": "Other",
        "Wood": "Woody biomass",
    }

    res_df["Fuel"] = res_df["Fuel"].map(res_fuel_aggregation)
    res_df = res_df.groupby(group_vars)["Value"].sum().reset_index()
    res_df = standardise_chart_data(res_df)

    p = create_scenario_facet_chart(res_df, "Residential demand", group_var="Fuel")

    save_chart_and_data(res_df, p, "residential_demand.png")


def create_commercial_demand_chart():
    """Create commercial demand area chart."""

    group_vars = ["Scenario", "Period", "Unit", "Fuel"]

    com_df = chart_data.get_fuel_use_by_island_and_sector(sector_group="Commercial")

    # fuels = com_df["Fuel"].unique()s
    # for fuel in fuels:
    # print(fuel)

    com_fuel_aggregation = {
        "Coal": "Other",
        "Diesel": "Diesel/Petrol",
        "Electricity": "Electricity",
        "LPG": "LPG",
        "Natural gas": "Natural gas",
        "Petrol": "Diesel/Petrol",
        "Solar": "Other",
        "Geothermal": "Other",
        "Biogas": "Biogas",
        "Biomethane": "Biomethane",
        "Wood": "Woody biomass",
    }

    com_df["Fuel"] = com_df["Fuel"].map(com_fuel_aggregation)
    com_df = com_df.groupby(group_vars)["Value"].sum().reset_index()

    com_df = standardise_chart_data(com_df)

    p = create_scenario_facet_chart(
        com_df, group_var="Fuel", chart_title="Commercial demand "
    )

    save_chart_and_data(com_df, p, "commercial_demand.png")


def create_industrial_demand_chart():
    """Create industrial demand area chart."""

    group_vars = ["Scenario", "Period", "Unit", "Fuel"]

    ind_df = chart_data.get_fuel_use_by_island_and_sector(
        sector_group="Industry",
    )

    # fuels = ind_df["Fuel"].unique()
    # for fuel in fuels:
    #     print(fuel)

    ind_fuel_aggregation = {
        "Coal": "Other",
        "Diesel": "Diesel/Petrol",
        "Electricity": "Electricity",
        "LPG": "LPG",
        "Natural gas": "Natural gas",
        "Petrol": "Diesel/Petrol",
        "Solar": "Other",
        "Geothermal": "Other",
        "Biogas": "Biogas",
        "Biomethane": "Biomethane",
        "Wood": "Woody biomass",
    }

    ind_df["Fuel"] = ind_df["Fuel"].map(ind_fuel_aggregation)
    ind_df = ind_df.groupby(group_vars)["Value"].sum().reset_index()

    ind_df = standardise_chart_data(ind_df)
    p = create_scenario_facet_chart(
        ind_df, group_var="Fuel", chart_title="Industrial demand "
    )

    save_chart_and_data(ind_df, p, "industrial_demand.png")


def create_industry_sector_demand_chart(subsector_list, name):
    """Create industry area chart for a specific list of subsectors."""

    group_vars = ["Scenario", "Period", "Unit", "Fuel"]

    ind_df = chart_data.get_fuel_use_by_island_and_sector(
        sector_group="Industry",
    )

    df = ind_df[ind_df["Sector"].isin(subsector_list)].copy()

    ind_fuel_aggregation = {
        "Coal": "Coal",
        "Diesel": "Diesel",
        "Electricity": "Electricity",
        "LPG": "LPG",
        "Natural gas": "Natural gas",
        "Petrol": "Petrol",
        "Solar": "Other",
        "Geothermal": "Other",
        "Biogas": "Biogas",
        "Biomethane": "Biogas",
        "Wood": "Woody biomass",
    }

    df["Fuel"] = df["Fuel"].map(ind_fuel_aggregation)
    df = df.groupby(group_vars)["Value"].sum().reset_index()

    filename = make_filename(name)
    df = standardise_chart_data(df)
    p = create_scenario_facet_chart(df, group_var="Fuel", chart_title=f"{name} demand")
    save_chart_and_data(df, p, f"demand_profile_{filename}.png")


def create_industry_use_demand_chart(enduse_list, name):
    """Create industry area chart for a specific list of end uses."""

    group_vars = ["Scenario", "Period", "Unit", "Fuel"]

    ind_df = chart_data.get_fuel_use_by_island_and_sector(
        end_use=enduse_list,
        sector_group="Industry",
    )
    df = ind_df.copy()

    ind_fuel_aggregation = {
        "Coal": "Coal",
        "Diesel": "Diesel",
        "Electricity": "Electricity",
        "LPG": "Other",
        "Natural gas": "Natural gas",
        "Petrol": "Petrol",
        "Solar": "Other",
        "Geothermal": "Other",
        "Biogas": "Biogas",
        "Biomethane": "Biogas",
        "Wood": "Woody biomass",
    }

    df["Fuel"] = df["Fuel"].map(ind_fuel_aggregation)
    df = df.groupby(group_vars)["Value"].sum().reset_index()

    filename = make_filename(name)
    df = standardise_chart_data(df)
    p = create_scenario_facet_chart(df, group_var="Fuel", chart_title=f"{name} demand")
    save_chart_and_data(df, p, f"demand_profile_{filename}.png")


def create_industry_demand_charts():
    """Write industrial demand charts."""

    create_industrial_demand_chart()
    create_industry_sector_demand_chart(["Dairy"], "Dairy")
    create_industry_sector_demand_chart(["Meat"], "Meat")
    create_industry_sector_demand_chart(["Methanol", "Urea"], "Methanex/Ballance")

    create_industry_use_demand_chart(
        enduse_list=[
            "High Temperature Heat (>300 C), Process Requirements",
            "Intermediate Heat (100-300 C), Process Requirements",
            "Low Temperature Heat (<100 C), Process Requirements",
        ],
        name="Industrial process heat",
    )


def create_electricity_demand_chart():
    """Create electricity demand area chart by sector group."""

    group_vars = ["Scenario", "Period", "Unit", "SectorGroup"]

    df = chart_data.get_fuel_use_by_island_and_sector()
    df = df[df["Fuel"] == "Electricity"].copy()
    df["SectorGroup"] = df["SectorGroup"].replace(
        {"Agriculture, Forestry, and Fishing": "Industry"}
    )
    df = df.groupby(group_vars)["Value"].sum().reset_index()
    df["Value"] = df["Value"] * PJ_TO_GWH / 1000
    df["Unit"] = "TWh"

    df = standardise_chart_data(df)
    p = create_scenario_facet_chart(
        df,
        group_var="SectorGroup",
        chart_title="Electricity demand by sector",
    )
    save_chart_and_data(df, p, "electricity_demand_by_sector_group.png")


def create_road_transport_demand_chart():
    """Create road transport energy demand area chart by fuel."""

    group_vars = ["Scenario", "Period", "Unit", "Fuel"]

    df = chart_data.get_times_data("transport_energy_demand.parquet")
    df = df[df["Variable"] == "Transport Energy Demand"].copy()

    road_transport_fuel_aggregation = {
        "Diesel": "Diesel",
        "Electricity": "Electricity",
        "LPG": "LPG",
        "Petrol": "Petrol",
    }

    df["Fuel"] = df["Fuel"].map(road_transport_fuel_aggregation).fillna("Other fuels")
    df = df.groupby(group_vars)["Value"].sum().reset_index()

    df = standardise_chart_data(df)
    p = create_scenario_facet_chart(
        df,
        group_var="Fuel",
        chart_title="Road transport demand",
    )
    save_chart_and_data(df, p, "road_transport_demand.png")


def create_total_demand_by_fuel_chart():
    """Create total energy demand area chart by fuel."""

    group_vars = ["Scenario", "Period", "Unit", "Fuel"]

    df = chart_data.get_fuel_use_by_island_and_sector()

    total_fuel_aggregation = {
        "Biodiesel": "Other renewables",
        "Bioethanol": "Other renewables",
        "Biogas": "Other renewables",
        "Biomethane": "Other renewables",
        "Coal": "Coal",
        "Diesel": "Oil products",
        "Drop-in Diesel": "Other renewables",
        "Drop-in Jet fuel": "Other renewables",
        "Electricity": "Electricity",
        "Fuel oil": "Oil products",
        "Geothermal": "Other renewables",
        "Hydrogen": "Hydrogen",
        "Jet fuel": "Oil products",
        "LNG": "Natural gas",
        "LPG": "Oil products",
        "Municipal waste": "Other renewables",
        "Natural gas": "Natural gas",
        "Petrol": "Oil products",
        "Solar": "Other renewables",
        "Wood": "Other renewables",
        "Wood Pellet": "Other renewables",
        "Wood residuals (onsite)": "Other renewables",
        "Wood residuals (onsite industrial)": "Other renewables",
        "Wood waste": "Other renewables",
    }

    mapped_fuels = df["Fuel"].map(total_fuel_aggregation)
    if mapped_fuels.isna().any():
        missing_fuels = sorted(df.loc[mapped_fuels.isna(), "Fuel"].unique())
        raise ValueError(
            "Missing total demand fuel aggregation for: " + ", ".join(missing_fuels)
        )

    df["Fuel"] = mapped_fuels

    df = df.groupby(group_vars)["Value"].sum().reset_index()

    df = standardise_chart_data(df)
    p = create_scenario_facet_chart(
        df,
        group_var="Fuel",
        chart_title="Total energy demand by fuel",
        palette=TOTAL_DEMAND_FUEL_PALETTE,
    )
    save_chart_and_data(df, p, "total_demand_by_fuel.png")


def assign_detailed_natural_gas_sector(df):
    """Return demand data with natural gas use grouped into detailed sectors."""

    key_industry_sectors = [
        "Dairy",
        "Iron & Steel",
        "Methanol",
        "Urea",
    ]
    sector_group_labels = {
        "Agriculture, Forestry, and Fishing": "Agriculture, forestry, and fishing",
    }

    df = df.copy()
    df["DetailedSector"] = df["SectorGroup"].replace(sector_group_labels)

    industry_mask = df["SectorGroup"] == "Industry"
    key_industry_mask = industry_mask & df["Sector"].isin(key_industry_sectors)

    df.loc[industry_mask, "DetailedSector"] = "Other industry"
    df.loc[key_industry_mask, "DetailedSector"] = df.loc[key_industry_mask, "Sector"]

    return df


def create_natural_gas_demand_by_detailed_sector_chart():
    """Create natural gas demand area chart by detailed use sector."""

    group_vars = ["Scenario", "Period", "Unit", "Sector"]
    palette = [
        "#164057",
        "#ED6D63",
        "#3C4C49",
        "#447474",
        "#C346CE",
        "#41B496",
        "#E94E24",
        "#4184A8",
    ]

    df = chart_data.get_fuel_use_by_island_and_sector()
    df = df[df["Fuel"] == "Natural gas"].copy()
    df = assign_detailed_natural_gas_sector(df)
    df["Sector"] = df["DetailedSector"]
    df = df.groupby(group_vars)["Value"].sum().reset_index()

    df = standardise_chart_data(df)
    p = create_scenario_facet_chart(
        df,
        group_var="Sector",
        chart_title="Natural gas demand by detailed sector",
        palette=palette,
    )
    save_chart_and_data(
        df, p, "natural_gas_demand_by_detailed_sector.png", height=5, width=10
    )


def main():
    """Write all demand charts."""

    create_residential_demand_chart()
    create_commercial_demand_chart()
    create_industry_demand_charts()
    create_electricity_demand_chart()
    create_road_transport_demand_chart()
    create_total_demand_by_fuel_chart()
    create_natural_gas_demand_by_detailed_sector_chart()


if __name__ == "__main__":
    main()
