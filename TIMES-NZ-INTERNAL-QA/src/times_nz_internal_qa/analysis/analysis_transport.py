"""Transport analysis charts."""

import times_nz_internal_qa.analysis.get_data as chart_data
from times_nz_internal_qa.analysis.analysis_chart_helpers import (
    create_scenario_facet_chart,
    save_chart_and_data,
    standardise_chart_data,
)


def create_fleet_composition_chart(enduse_list, title, filename, facet_rows=None):
    """
    Area facet chart for transport fleet counts by technology, filtered for a
    specific end use.
    """

    fleet_df = chart_data.get_transport_capacity(enduse_list)
    fleet_df = standardise_chart_data(fleet_df)

    tech_rename_mapping = {
        "Battery Electric Vehicle": "BEV",
        "Hybrid Vehicle": "Hybrid",
        "Internal Combustion Engine": "ICE",
        "Plug-in Hybrid Vehicle": "PHEV",
    }

    fleet_df["TechnologyGroup"] = fleet_df["TechnologyGroup"].map(tech_rename_mapping)

    p = create_scenario_facet_chart(fleet_df, title, "TechnologyGroup", facet_rows)

    if facet_rows is None:
        fleet_df = fleet_df.drop("EndUse", axis=1)

    save_chart_and_data(fleet_df, p, filename)


def quick_truck_maths():
    """
    Short analysis script for rough heavy and medium truck fuel-cost comparison.
    """

    heavy_truck_high_util = 74_246
    med_truck_low_util = 12_047

    heavy_truck_ice_eff = 0.05
    heavy_truck_bev_eff = 0.2

    heavy_truck_ice_gj_demand = heavy_truck_high_util / heavy_truck_ice_eff / 1000
    heavy_truck_bev_gj_demand = heavy_truck_high_util / heavy_truck_bev_eff / 1000

    heavy_truck_bev_gj_demand = heavy_truck_bev_gj_demand * 1.1

    bev_fuel_costs = 62.82
    ice_fuel_costs = 39.74

    print(f"Heavy trukc bev uses {heavy_truck_bev_gj_demand} gj")
    print(f"Heavy trukc ice uses {heavy_truck_ice_gj_demand} gj")
    print(f"Heavy trukc bev costs {heavy_truck_bev_gj_demand*bev_fuel_costs} pa")
    print(f"Heavy trukc ice costs {heavy_truck_ice_gj_demand*ice_fuel_costs} pa")

    med_truck_ice_eff = 0.06
    med_truck_bev_eff = 0.3

    med_truck_bev_gj_demand = med_truck_low_util / med_truck_bev_eff / 1000
    med_truck_ice_gj_demand = med_truck_low_util / med_truck_ice_eff / 1000

    print(f"Medium Truck bev uses {med_truck_bev_gj_demand} gj")
    print(f"Medium Truck ice uses {med_truck_ice_gj_demand} gj")
    print(f"Medium Truck bev costs {med_truck_bev_gj_demand*bev_fuel_costs} pa")
    print(f"Medium Truck ice costs {med_truck_ice_gj_demand*ice_fuel_costs} pa")


def main():
    """Write all transport charts."""

    create_fleet_composition_chart(
        ["Light Passenger Vehicle"],
        "Light passenger fleet",
        "transport_lpv_capacity.png",
    )

    create_fleet_composition_chart(
        ["Light Commercial Vehicle"],
        "Light commercial fleet",
        "transport_lcv_capacity.png",
    )

    create_fleet_composition_chart(
        ["Light Truck", "Heavy Truck", "Medium Truck"],
        "Truck fleet",
        "transport_truck_capacity.png",
        "EndUse",
    )


if __name__ == "__main__":
    main()
