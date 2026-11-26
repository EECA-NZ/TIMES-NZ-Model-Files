"""Prepare per-scenario report tables from already labelled result dataframes."""

from __future__ import annotations

import pandas as pd

from solve_times_nz.reporting_flows import flow_summaries

PJ_TO_TWH = 277.77777778 / 1000


def _annual_periods(periods: pd.Series) -> pd.Series:
    """Validate annual years before casting; raw periods may contain other tokens."""
    years = pd.to_numeric(periods, errors="raise")
    if years.isna().any() or years.mod(1).ne(0).any():
        raise ValueError("Expected integer annual periods")
    return years.astype("int64")


def aggregate(data: pd.DataFrame, groups=()) -> pd.DataFrame:
    """Sum valid annual values, retaining raw scenario IDs and units."""
    keys = ["Scenario", "Period", "Unit", *groups]
    data = data.assign(Period=_annual_periods(data["Period"]))
    if data[[*keys, "Value"]].isna().any().any():
        raise ValueError(f"Missing summary values or classifications: {keys}")
    if not data["Value"].abs().lt(float("inf")).all():
        raise ValueError("Expected finite summary values")
    return data.groupby(keys, as_index=False, observed=True)["Value"].sum()


def select(data: pd.DataFrame, variable: str, unit: str) -> pd.DataFrame:
    """Select one labelled measure and verify its input unit."""
    result = data.loc[data["Variable"].eq(variable)].copy()
    if not result["Unit"].eq(unit).all():
        raise ValueError(f"Expected {variable} in {unit}")
    return result


def complete(data: pd.DataFrame, years: pd.DataFrame) -> pd.DataFrame:
    """Complete absent annual rows; preserve existing nulls and category combinations."""
    if data.empty:
        return data
    categories = [
        column for column in data if column not in {"Scenario", "Period", "Value"}
    ]
    keys = ["Scenario", "Period", *categories]
    index = (
        years.merge(data[categories].drop_duplicates(), how="cross")
        .set_index(keys)
        .index
    )
    values = data.set_index(keys)
    if not values.index.is_unique or len(values.index.difference(index)):
        raise ValueError("Duplicate summary keys or periods outside the model years")
    return values.reindex(index, fill_value=0).reset_index()[data.columns]


def mapped(data: pd.DataFrame, column: str, labels: dict[str, str]) -> pd.DataFrame:
    """Apply an explicit reporting classification without dropping unknown values."""
    result = data.copy()
    result[column] = result[column].map(labels)
    if result[column].isna().any():
        missing = data.loc[result[column].isna(), column].drop_duplicates().tolist()
        raise ValueError(f"Missing {column} summary classification: {missing}")
    return result


def renewable_shares(
    generation: pd.DataFrame, demand: pd.DataFrame, fuels: pd.DataFrame
) -> dict[str, pd.DataFrame]:
    """Allocate mixed-fuel generation by input share, then calculate renewable TFEC."""
    if not {"Fuel", "Renewable"} <= set(fuels):
        raise ValueError(
            "Recorded energy commodity metadata is missing Renewable classifications"
        )
    if (
        not generation.Value.abs().lt(float("inf")).all()
        or not demand.Value.abs().lt(float("inf")).all()
    ):
        raise ValueError("Missing or non-finite values in renewable-share inputs")
    classifications = fuels[["Fuel", "Renewable"]].drop_duplicates()
    if (
        classifications["Renewable"].isna().any()
        or not classifications["Renewable"]
        .isin(["Renewable", "Non-renewable", "Electricity"])
        .all()
    ):
        raise ValueError("Missing or unknown renewable fuel classification")
    plant_keys = ["Scenario", "Period", "Process", "Region", "Vintage"]
    inputs = select(generation, "Electricity fuel use", "PJ").drop(
        columns="Renewable", errors="ignore"
    )
    inputs = inputs.merge(
        classifications, on="Fuel", how="left", validate="many_to_one"
    )
    if inputs["Renewable"].isna().any():
        raise ValueError("Missing renewable fuel classification for electricity inputs")
    inputs["RenewableInput"] = inputs["Value"].where(
        inputs["Renewable"].eq("Renewable"), 0
    )
    shares = inputs.groupby(plant_keys, dropna=False, as_index=False).agg(
        TotalInput=("Value", "sum"), RenewableInput=("RenewableInput", "sum")
    )
    shares["RenewableShare"] = shares["RenewableInput"].div(
        shares["TotalInput"].where(shares["TotalInput"].ne(0))
    )
    output = select(generation, "Electricity generation", "PJ").merge(
        shares[[*plant_keys, "RenewableShare"]],
        on=plant_keys,
        how="left",
        validate="many_to_one",
    )
    if (output["RenewableShare"].isna() & output["Value"].ne(0)).any():
        raise ValueError("Missing fuel-use renewable share for electricity generation")
    # Multi-fuel plants use the existing equal-conversion-efficiency assumption.
    output["RenewableValue"] = output["Value"] * output["RenewableShare"].fillna(0)
    electricity = output.groupby(["Scenario", "Period"], as_index=False).agg(
        Total=("Value", "sum"), Renewable=("RenewableValue", "sum")
    )
    electricity["Value"] = electricity["Renewable"].div(
        electricity["Total"].where(electricity["Total"].ne(0))
    )
    electricity["Unit"] = "Share"
    electricity = electricity[["Scenario", "Period", "Unit", "Value"]]
    final = demand.loc[
        ~demand["EndUse"].isin(["International Aviation", "International Shipping"])
    ].drop(columns="Renewable", errors="ignore")
    final = final.merge(classifications, on="Fuel", how="left", validate="many_to_one")
    if final["Renewable"].isna().any():
        raise ValueError(
            "Missing renewable fuel classification for final energy demand"
        )
    final = final.merge(
        electricity[["Scenario", "Period", "Value"]].rename(
            columns={"Value": "ElectricityShare"}
        ),
        on=["Scenario", "Period"],
        how="left",
        validate="many_to_one",
    )
    if (
        final["Renewable"].eq("Electricity")
        & final["ElectricityShare"].isna()
        & final["Value"].ne(0)
    ).any():
        raise ValueError(
            "Missing renewable electricity share for final electricity demand"
        )
    final["RenewableShare"] = final["Renewable"].eq("Renewable").astype(float)
    electric = final["Renewable"].eq("Electricity")
    final.loc[electric, "RenewableShare"] = final.loc[electric, "ElectricityShare"]
    final["RenewableValue"] = final["Value"] * final["RenewableShare"].fillna(0)
    tfec = final.groupby(["Scenario", "Period"], as_index=False).agg(
        Total=("Value", "sum"), Renewable=("RenewableValue", "sum")
    )
    tfec["Value"] = tfec["Renewable"].div(tfec["Total"].where(tfec["Total"].ne(0)))
    tfec["Unit"] = "Share"
    return {
        "indicators/renewable_generation_share": electricity,
        "indicators/renewable_tfec_share": tfec[
            ["Scenario", "Period", "Unit", "Value"]
        ],
    }


def demand_summaries(
    demand: pd.DataFrame, road: pd.DataFrame
) -> dict[str, pd.DataFrame]:
    """Prepare reusable demand totals and breakdowns, retaining distinct groupings."""
    electricity = demand.loc[demand["Fuel"].eq("Electricity")]
    result = {
        "electricity/electricity_demand": aggregate(electricity).assign(
            Value=lambda df: df.Value / 3.6, Unit="TWh"
        ),
        "electricity/electricity_demand_by_sector_group": aggregate(
            electricity, ["SectorGroup"]
        ).assign(Value=lambda df: df.Value / 3.6, Unit="TWh"),
        "demand/energy_demand_by_fuel_and_sector_group": aggregate(
            demand, ["Fuel", "SectorGroup"]
        ),
        "demand/woody_biomass_demand_by_sector_group": aggregate(
            demand.loc[demand.Fuel.isin(["Wood", "Wood residuals (onsite)"])],
            ["SectorGroup"],
        ),
    }
    vehicles = demand.loc[
        demand.SectorGroup.eq("Transport") & demand.Sector.eq("Road Transport")
    ].rename(columns={"EndUse": "Vehicle class"})
    result["transport/road_transport_demand_by_fuel_and_vehicle_class"] = aggregate(
        vehicles, ["Fuel", "Vehicle class"]
    )
    result.update(publication_demand_summaries(demand, road))
    return result


def publication_demand_summaries(
    demand: pd.DataFrame, road: pd.DataFrame
) -> dict[str, pd.DataFrame]:
    """Retain the publication fuel mappings and sector selections."""
    result = {}
    island = demand.assign(
        Island=demand.Region.replace({"NI": "North Island", "SI": "South Island"})
    )
    island = aggregate(island, ["Island", "SectorGroup", "Sector", "Fuel"])
    island.loc[island.Value.abs().lt(1e-6), "Value"] = 0
    result["demand/fuel_use_by_island_and_sector"] = island
    total_fuels = {
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
        "Black Pellet": "Other renewables",
        "Wood residuals (onsite)": "Other renewables",
        "Wood residuals (onsite industrial)": "Other renewables",
        "Wood waste": "Other renewables",
        "Agricultural waste": "Other renewables",
        "Animal manure": "Other renewables",
    }
    result["demand/total_demand_by_fuel"] = aggregate(
        mapped(island, "Fuel", total_fuels), ["Fuel"]
    )
    sector_fuels = {
        "Coal": "Other",
        "Diesel": "Diesel/Petrol",
        "Electricity": "Electricity",
        "LPG": "LPG",
        "Natural gas": "Natural gas",
        "Petrol": "Diesel/Petrol",
        "Solar": "Other",
        "Wood": "Woody biomass",
        "Geothermal": "Other",
        "Biogas": "Biogas",
        "Biomethane": "Biomethane",
        "Fuel oil": "Other",
        "Wood residuals (onsite)": "Woody biomass",
    }
    for sector in ["Residential", "Commercial", "Industry"]:
        selected = island.loc[island.SectorGroup.eq(sector)]
        labels = sector_fuels.copy()
        # Preserve the archived publication groupings; QA retains detailed fuels.
        if sector in {"Commercial", "Industry"}:
            labels.update({"LPG": "Other", "Biogas": "Other"})
        if sector == "Industry":
            labels["Coal"] = "Coal"
            # These two fuels were omitted by the legacy industrial profile maps.
            selected = selected.loc[
                ~selected.Fuel.isin(["Fuel oil", "Wood residuals (onsite)"])
            ]
        result[
            f"demand/{sector.lower() if sector != 'Industry' else 'industrial'}_demand"
        ] = aggregate(mapped(selected, "Fuel", labels), ["Fuel"])
    detailed_fuels = {
        **sector_fuels,
        "Coal": "Coal",
        "Diesel": "Diesel",
        "Petrol": "Petrol",
        "Biomethane": "Biogas",
    }
    industry = island.loc[
        island.SectorGroup.eq("Industry")
        & ~island.Fuel.isin(["Fuel oil", "Wood residuals (onsite)"])
    ]
    for name, sectors in {
        "dairy": ["Dairy"],
        "meat": ["Meat"],
        "methanexballance": ["Methanol", "Urea"],
    }.items():
        result[f"demand/demand_profile_{name}"] = aggregate(
            mapped(industry.loc[industry.Sector.isin(sectors)], "Fuel", detailed_fuels),
            ["Fuel"],
        )
    heat = demand.loc[
        demand.SectorGroup.eq("Industry")
        & ~demand.Fuel.isin(["Fuel oil", "Wood residuals (onsite)"])
        & demand.EndUse.isin(
            [
                "High Temperature Heat (>300 C), Process Requirements",
                "Intermediate Heat (100-300 C), Process Requirements",
                "Low Temperature Heat (<100 C), Process Requirements",
            ]
        )
    ]
    heat = aggregate(heat, ["Region", "Sector", "Fuel"])
    heat.loc[heat.Value.abs().lt(1e-6), "Value"] = 0
    result["demand/demand_profile_industrial_process_heat"] = aggregate(
        mapped(heat, "Fuel", {**detailed_fuels, "LPG": "Other"}), ["Fuel"]
    )
    result["electricity/electricity_demand_by_sector_group_combined_industry"] = (
        aggregate(
            island.loc[island.Fuel.eq("Electricity")].assign(
                SectorGroup=lambda df: df.SectorGroup.replace(
                    {"Agriculture, Forestry, and Fishing": "Industry"}
                )
            ),
            ["SectorGroup"],
        ).assign(Value=lambda df: df.Value * PJ_TO_TWH, Unit="TWh")
    )
    road = road.assign(
        Fuel=road.Fuel.where(
            road.Fuel.isin(["Diesel", "Electricity", "LPG", "Petrol"]), "Other fuels"
        )
    )
    result["transport/road_transport_demand"] = aggregate(road, ["Fuel"])
    gas = island.loc[island.Fuel.eq("Natural gas")].copy()
    gas["DetailedSector"] = gas.SectorGroup.replace(
        {"Agriculture, Forestry, and Fishing": "Agriculture, forestry, and fishing"}
    )
    gas.loc[gas.SectorGroup.eq("Industry"), "DetailedSector"] = "Other industry"
    gas["DetailedSector"] = gas.Sector.where(
        gas.SectorGroup.eq("Industry")
        & gas.Sector.isin(["Dairy", "Iron & Steel", "Methanol", "Urea"]),
        gas.DetailedSector,
    )
    result["demand/natural_gas_demand_by_detailed_sector"] = aggregate(
        gas.assign(Sector=gas.DetailedSector), ["Sector"]
    )
    return result


def supply_summaries(supply: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Group existing gas and biomass supply views without changing PJ units."""
    result = {"supply/primary_energy_by_fuel": aggregate(supply, ["Fuel"])}
    for name, labels in {
        "primary_energy_lng_natural_gas_supply": {
            "Natural gas": "Domestic natural gas",
            "LNG": "LNG imports",
        },
        "primary_energy_lng_natural_gas_biogas_supply": {
            "Natural gas": "Domestic natural gas",
            "LNG": "LNG imports",
            "Biogas": "Biogas",
        },
        "primary_energy_biomass_biogas_supply": {
            "Biogas": "Biogas",
            "Wood": "Biomass",
            "Wood residuals (onsite)": "Biomass",
        },
    }.items():
        frame = supply.loc[supply.Fuel.isin(labels)].copy()
        frame["SupplySource"] = frame.Fuel.map(labels)
        frame = aggregate(frame, ["SupplySource"])
        if name == "primary_energy_lng_natural_gas_supply":
            result["supply/natural_gas_supply_by_source"] = frame.rename(
                columns={"SupplySource": "Supply source"}
            )
        frame.loc[frame.Value.abs().lt(1e-6), "Value"] = 0
        result[f"supply/{name}"] = frame
    return result


def _grid_capacity(table: pd.DataFrame) -> pd.DataFrame:
    """Sum grid capacity across islands, counting the HVDC link once (NI rows)."""
    grid = select(table, "Capacity", "GW")
    grid = grid.loc[grid.Technology.ne("HVDC link") | grid.Region.eq("NI")]
    return aggregate(grid, ["Technology"])


def _peak_demand(table: pd.DataFrame) -> pd.DataFrame:
    """Find the national electricity demand slice with the highest average GW."""
    slices = aggregate(select(table, "Average output", "GW"), ["TimeSlice"])
    peak = slices.loc[slices.groupby(["Scenario", "Period"]).Value.idxmax()]
    return peak[["Scenario", "Period", "Unit", "TimeSlice", "Value"]]


def build_summaries(
    tables: dict[str, pd.DataFrame], fuels: pd.DataFrame, timeslices: pd.DataFrame
) -> dict[str, pd.DataFrame]:
    """Build flexible named summary tables; all I/O belongs to the caller."""
    tables = {
        name: (
            frame.assign(Period=_annual_periods(frame["Period"]))
            if name != "raw_results.parquet" and "Period" in frame
            else frame
        )
        for name, frame in tables.items()
    }
    demand = select(tables["energy_demand.parquet"], "Energy demand", "PJ")
    generation = tables["elec_generation.parquet"]
    output = select(generation, "Electricity generation", "PJ")
    emissions = tables["emissions.parquet"].copy()
    if not emissions.Unit.eq("kt CO2e").all():
        raise ValueError("Expected emissions in kt CO2e")
    result = demand_summaries(
        demand,
        select(
            tables["transport_energy_demand.parquet"], "Transport Energy Demand", "PJ"
        ),
    )
    result.update(
        supply_summaries(
            select(tables["primary_energy.parquet"], "Primary Energy Production", "PJ")
        )
    )
    result["electricity/electricity_generation_by_technology_group"] = aggregate(
        output, ["TechnologyGroup"]
    ).assign(Value=lambda df: df.Value / 3.6, Unit="TWh")
    result["electricity/electricity_generation"] = aggregate(output).assign(
        Value=lambda df: df.Value / 3.6, Unit="TWh"
    )
    result["electricity/thermal_generation_fuel_use"] = aggregate(
        select(generation, "Electricity fuel use", "PJ").loc[
            lambda df: df.TechnologyGroup.eq("Thermal")
        ],
        ["Fuel"],
    )
    result["emissions/emissions"] = aggregate(emissions).assign(
        Value=lambda df: df.Value / 1000, Unit="Mt CO2e"
    )
    result["emissions/emissions_by_sector_group"] = aggregate(
        emissions, ["SectorGroup"]
    ).assign(Value=lambda df: df.Value / 1000, Unit="Mt CO2e")
    result["emissions/emissions_by_broad_sector_group"] = aggregate(
        emissions.assign(
            SectorGroup=emissions.SectorGroup.where(
                emissions.SectorGroup.isin(
                    ["Electricity generation", "Industry", "Transport"]
                ),
                "Other",
            )
        ),
        ["SectorGroup"],
    ).assign(Value=lambda df: df.Value / 1000, Unit="Mt CO2e")
    result["electricity/battery_capacity"] = aggregate(
        select(tables["batteries.parquet"], "Capacity", "GW"), ["Technology"]
    )
    result["electricity/grid_capacity"] = _grid_capacity(
        tables["grid_capacity.parquet"]
    )
    fleet = select(
        tables["transport_capacity.parquet"], "Transport Capacity", "000vehicles"
    )
    fleet = aggregate(
        fleet.loc[
            fleet.EndUse.isin(
                [
                    "Light Passenger Vehicle",
                    "Light Commercial Vehicle",
                    "Light Truck",
                    "Medium Truck",
                    "Heavy Truck",
                ]
            )
        ],
        ["TechnologyGroup", "EndUse"],
    )
    fleet.loc[fleet.Value.abs().lt(1e-6), "Value"] = 0
    result["transport/transport_capacity"] = mapped(
        fleet,
        "TechnologyGroup",
        {
            "Battery Electric Vehicle": "BEV",
            "Hybrid Vehicle": "Hybrid",
            "Internal Combustion Engine": "ICE",
            "Plug-in Hybrid Vehicle": "PHEV",
        },
    ).assign(Unit="Thousand vehicles")
    years = demand[["Scenario", "Period"]].drop_duplicates()
    result = {name: complete(frame, years) for name, frame in result.items()}
    # Added after completion: slices exist only for modelled years, so a
    # zero-filled base year would be a false zero peak.
    result["electricity/peak_demand"] = _peak_demand(
        tables["electricity_demand_by_timeslice.parquet"]
    )
    for name, frame in renewable_shares(generation, demand, fuels).items():
        result[name] = pd.concat(
            [frame, frame.assign(Value=lambda df: df.Value * 100, Unit="%")],
            ignore_index=True,
        )
    for name, source, groups in [
        (
            "demand/energy_demand_by_fuel",
            "demand/energy_demand_by_fuel_and_sector_group",
            ["Fuel"],
        ),
        ("supply/natural_gas_supply", "supply/natural_gas_supply_by_source", []),
        (
            "demand/woody_biomass_demand",
            "demand/woody_biomass_demand_by_sector_group",
            [],
        ),
    ]:
        result[name] = aggregate(result[source], groups)
    objectives = tables["objective_function.parquet"]
    if (
        objectives.Scenario.duplicated().any()
        or not objectives.Unit.eq("NZDb").all()
        or set(objectives.Scenario) != set(demand.Scenario)
    ):
        raise ValueError("Expected one NZDb objective per scenario")
    if (
        objectives.Value.isna().any()
        or not objectives.Value.abs().lt(float("inf")).all()
    ):
        raise ValueError("Expected finite objective values")
    result["indicators/objective_function"] = objectives[
        ["Scenario", "Variable", "Unit", "Value"]
    ].copy()
    result.update(flow_summaries(tables, timeslices))
    return {f"{name}.csv": frame for name, frame in result.items() if not frame.empty}
