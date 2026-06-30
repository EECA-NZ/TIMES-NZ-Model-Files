"""Residential, commercial, and industrial demand analysis charts."""

import times_nz_internal_qa.analysis.get_data as chart_data
from times_nz_internal_qa.analysis.analysis_chart_helpers import (
    create_scenario_facet_chart,
    make_filename,
    save_chart,
    standardise_chart_data,
)


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

    save_chart(p, "residential_demand.png")


def create_commercial_demand_chart():
    """Create commercial demand area chart."""

    group_vars = ["Scenario", "Period", "Unit", "Fuel"]

    com_df = chart_data.get_fuel_use_by_island_and_sector(sector_group="Commercial")

    fuels = com_df["Fuel"].unique()

    for fuel in fuels:
        print(fuel)

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

    save_chart(p, "commercial_demand.png")


def create_industrial_demand_chart():
    """Create industrial demand area chart."""

    group_vars = ["Scenario", "Period", "Unit", "Fuel"]

    ind_df = chart_data.get_fuel_use_by_island_and_sector(
        sector_group="Industry",
    )

    fuels = ind_df["Fuel"].unique()

    for fuel in fuels:
        print(fuel)

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

    save_chart(p, "industrial_demand.png")


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
    save_chart(p, f"demand_profile_{filename}.png")


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
    save_chart(p, f"demand_profile_{filename}.png")


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


def main():
    """Write all demand charts."""

    create_residential_demand_chart()
    create_commercial_demand_chart()
    create_industry_demand_charts()


if __name__ == "__main__":
    main()
