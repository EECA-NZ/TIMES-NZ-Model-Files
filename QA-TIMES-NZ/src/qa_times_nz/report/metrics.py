"""Declare the prepared summary metrics shown on each report page."""

from types import MappingProxyType
from typing import Mapping, NamedTuple


class MetricSpec(NamedTuple):
    """A prepared dataset, its grouping column, expected unit and row filters."""

    key: str
    title: str
    dataset: str
    group: str | None
    unit: str
    filters: Mapping = MappingProxyType({})
    slices: bool = False


class Subheader(NamedTuple):
    """A heading shown in the page and its contents, above the metrics that follow."""

    title: str


PAGES = {
    "electricity": (
        "Electricity",
        [
            Subheader("Demand"),
            MetricSpec(
                "electricity-demand-total",
                "Total electricity demand",
                "electricity/electricity_demand",
                None,
                "TWh",
            ),
            MetricSpec(
                "electricity-demand-sector",
                "Electricity demand by sector",
                "electricity/electricity_demand_by_sector_group",
                "SectorGroup",
                "TWh",
            ),
            MetricSpec(
                "peak-demand",
                "Peak electricity demand",
                "electricity/peak_demand",
                None,
                "GW",
            ),
            Subheader("Generation"),
            MetricSpec(
                "electricity-generation-total",
                "Total electricity generation",
                "electricity/electricity_generation",
                None,
                "TWh",
            ),
            MetricSpec(
                "electricity-generation-type",
                "Electricity generation by type",
                "electricity/electricity_generation_by_technology_group",
                "TechnologyGroup",
                "TWh",
            ),
            MetricSpec(
                "thermal-generation-fuel",
                "Thermal generation fuel use by fuel",
                "electricity/thermal_generation_fuel_use",
                "Fuel",
                "PJ",
            ),
            MetricSpec(
                "generation-flows-2050",
                "Electricity generation by timeslice (2050)",
                "electricity/generation_flows",
                "Series",
                "GW",
                slices=True,
            ),
            Subheader("Batteries"),
            MetricSpec(
                "battery-capacity-type",
                "Battery capacity by type",
                "electricity/battery_capacity",
                "Technology",
                "GW",
            ),
            MetricSpec(
                "battery-flows-2050",
                "Battery flows by timeslice (2050)",
                "electricity/battery_flows",
                "Series",
                "GW",
                slices=True,
            ),
            Subheader("Grid"),
            MetricSpec(
                "grid-capacity-type",
                "Grid capacity by type",
                "electricity/grid_capacity",
                "Technology",
                "GW",
            ),
        ],
    ),
    "oil-and-gas": (
        "Oil and gas",
        [
            MetricSpec(
                "gas-demand-total",
                "Total final natural gas demand",
                "demand/energy_demand_by_fuel",
                None,
                "PJ",
                {"Fuel": "Natural gas"},
            ),
            MetricSpec(
                "gas-demand-sector",
                "Final natural gas demand by sector",
                "demand/energy_demand_by_fuel_and_sector_group",
                "SectorGroup",
                "PJ",
                {"Fuel": "Natural gas"},
            ),
            MetricSpec(
                "gas-supply-total",
                "Total natural gas supply, including LNG",
                "supply/natural_gas_supply",
                None,
                "PJ",
            ),
            MetricSpec(
                "gas-supply-source",
                "Natural gas supply by source",
                "supply/natural_gas_supply_by_source",
                "Supply source",
                "PJ",
            ),
            MetricSpec(
                "diesel-demand-total",
                "Total diesel demand",
                "demand/energy_demand_by_fuel",
                None,
                "PJ",
                {"Fuel": "Diesel"},
            ),
            MetricSpec(
                "diesel-demand-sector",
                "Diesel demand by sector",
                "demand/energy_demand_by_fuel_and_sector_group",
                "SectorGroup",
                "PJ",
                {"Fuel": "Diesel"},
            ),
            MetricSpec(
                "road-diesel-class",
                "Road diesel demand by vehicle class",
                "transport/road_transport_demand_by_fuel_and_vehicle_class",
                "Vehicle class",
                "PJ",
                {"Fuel": "Diesel"},
            ),
            MetricSpec(
                "petrol-demand-total",
                "Total petrol demand",
                "demand/energy_demand_by_fuel",
                None,
                "PJ",
                {"Fuel": "Petrol"},
            ),
            MetricSpec(
                "petrol-demand-sector",
                "Petrol demand by sector",
                "demand/energy_demand_by_fuel_and_sector_group",
                "SectorGroup",
                "PJ",
                {"Fuel": "Petrol"},
            ),
            MetricSpec(
                "road-petrol-class",
                "Road petrol demand by vehicle class",
                "transport/road_transport_demand_by_fuel_and_vehicle_class",
                "Vehicle class",
                "PJ",
                {"Fuel": "Petrol"},
            ),
        ],
    ),
    "renewables": (
        "Renewables",
        [
            MetricSpec(
                "renewable-generation-share",
                "Renewable share of electricity generation",
                "indicators/renewable_generation_share",
                None,
                "%",
                {"Unit": "%"},
            ),
            MetricSpec(
                "renewable-tfec-share",
                "Renewable share of total final energy consumption",
                "indicators/renewable_tfec_share",
                None,
                "%",
                {"Unit": "%"},
            ),
            MetricSpec(
                "biomass-demand-total",
                "Total biomass demand",
                "demand/woody_biomass_demand",
                None,
                "PJ",
            ),
            MetricSpec(
                "biomass-demand-sector",
                "Biomass demand by sector",
                "demand/woody_biomass_demand_by_sector_group",
                "SectorGroup",
                "PJ",
            ),
        ],
    ),
    "emissions": (
        "Emissions",
        [
            MetricSpec(
                "emissions-total",
                "Total emissions",
                "emissions/emissions",
                None,
                "Mt CO2e",
            ),
            MetricSpec(
                "emissions-sector",
                "Emissions by sector",
                "emissions/emissions_by_sector_group",
                "SectorGroup",
                "Mt CO2e",
            ),
        ],
    ),
}
