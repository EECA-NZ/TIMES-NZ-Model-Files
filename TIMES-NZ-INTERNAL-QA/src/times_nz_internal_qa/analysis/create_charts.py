"""Create static chart outputs for internal TIMES-NZ QA analysis."""

# pylint: disable=too-many-lines
# pylint: disable=too-many-arguments,too-many-positional-arguments
# pylint: disable=too-many-locals,too-many-statements

from textwrap import fill

import pandas as pd
import times_nz_internal_qa.analysis.get_data as chart_data
from mizani.labels import comma_format, percent_format
from plotnine import (
    aes,
    facet_grid,
    facet_wrap,
    geom_area,
    geom_hline,
    geom_label,
    geom_line,
    ggplot,
    labs,
    scale_color_manual,
    scale_fill_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)

eeca_colours = {
    "emerald": "#41B496",
    "teal": "#447474",
    "navy": "#164057",
    "coral": "#ED6D63",
    "forest": "#3C4C49",
    "orange": "#E94E24",
}

chart_cols = [
    eeca_colours["navy"],
    eeca_colours["coral"],
    eeca_colours["teal"],
    eeca_colours["forest"],
    eeca_colours["emerald"],
    eeca_colours["orange"],
]

scenario_order = [
    "Steady",
    "Shift",
]


def decimal_tick_labels(values):
    """Return compact decimal labels for smaller chart values."""

    return [
        "" if pd.isna(value) else f"{value:.2f}".rstrip("0").rstrip(".")
        for value in values
    ]


def adaptive_tick_labels(values):
    """Return compact labels with more decimals for small axis ranges."""

    valid_values = [abs(value) for value in values if not pd.isna(value)]
    max_value = max(valid_values, default=0)

    if max_value >= 100:
        decimals = 0
    elif max_value >= 10:
        decimals = 1
    elif max_value >= 1:
        decimals = 2
    elif max_value >= 0.1:
        decimals = 3
    else:
        decimals = 4

    return [
        "" if pd.isna(value) else f"{value:,.{decimals}f}".rstrip("0").rstrip(".")
        for value in values
    ]


def get_scenario_facet_order(df):
    """Return preferred scenario order with any extras appended."""

    available_scenarios = df["Scenario"].dropna().unique().tolist()
    preferred_scenarios = [
        scenario for scenario in scenario_order if scenario in available_scenarios
    ]
    extra_scenarios = sorted(set(available_scenarios) - set(preferred_scenarios))
    return preferred_scenarios + extra_scenarios


def fill_missing_colours(values, colours):
    """Add fallback colours for any values not in a manual palette."""

    colours = colours.copy()
    missing_values = [value for value in values if value not in colours]
    for i, value in enumerate(missing_values):
        colours[value] = chart_cols[i % len(chart_cols)]
    return colours


def fuel_use_area_grid_chart(
    end_use,
    sector_group,
    scenario,
    facet_rows="Sector",
    facet_cols="Island",
    chart_title="Fuel use by island and sector",
    filename="Fuel use by island and sector.png",
    label_facets_above=False,
    exclude_sector=None,
):
    """
    Create and save a configurable small-multiple fuel-use area chart.

    end_use, sector_group, and scenario should be lists. Use an empty list or
    None to include all values for that filter.
    """

    df = chart_data.get_fuel_use_by_island_and_sector(
        end_use=end_use,
        sector_group=sector_group,
        scenario=scenario,
    )
    if df.empty:
        raise ValueError("No fuel-use data found for the supplied filters.")

    if exclude_sector is not None:
        df = df[~df["Sector"].isin(exclude_sector)].copy()
        if df.empty:
            raise ValueError("No fuel-use data left after excluding sectors.")

    df = df.groupby(
        ["Scenario", "Period", "Unit", "Island", "Sector", "Fuel"], as_index=False
    )["Value"].sum()
    df["Period"] = pd.to_numeric(df["Period"], errors="coerce")

    scenarios = get_scenario_facet_order(df)
    df["Scenario"] = pd.Categorical(
        df["Scenario"],
        categories=scenarios,
        ordered=True,
    )

    preferred_island_order = ["North Island", "South Island"]
    available_islands = df["Island"].dropna().unique().tolist()
    island_order = [
        island for island in preferred_island_order if island in available_islands
    ]
    island_order.extend(sorted(set(available_islands) - set(island_order)))
    df["Island"] = pd.Categorical(df["Island"], categories=island_order, ordered=True)

    sector_order = (
        df.groupby("Sector", observed=False)["Value"]
        .sum()
        .sort_values(ascending=False)
        .index.tolist()
    )
    df["Sector"] = pd.Categorical(df["Sector"], categories=sector_order, ordered=True)

    preferred_fuel_order = [
        "Coal",
        "Natural gas",
        "Fuel oil",
        "Diesel",
        "Petrol",
        "Jet fuel",
        "LPG",
        "Electricity",
        "Geothermal",
        "Solar",
        "Wood",
        "Wood residuals (onsite)",
        "Biogas",
        "Biomethane",
    ]
    available_fuels = df["Fuel"].dropna().unique().tolist()
    fuel_order = [fuel for fuel in preferred_fuel_order if fuel in available_fuels]
    fuel_order.extend(sorted(set(available_fuels) - set(fuel_order)))
    fuel_colours = {
        "Biogas": eeca_colours["emerald"],
        "Biomethane": "#73C6A5",
        "Coal": "grey",
        "Diesel": eeca_colours["orange"],
        "Electricity": eeca_colours["navy"],
        "Fuel oil": "#6E4F47",
        "Geothermal": "#A85E2E",
        "Jet fuel": eeca_colours["forest"],
        "LPG": "#C9A227",
        "Natural gas": eeca_colours["teal"],
        "Petrol": eeca_colours["coral"],
        "Solar": "#E9B949",
        "Wood": "#6F8F45",
        "Wood residuals (onsite)": "#8B6F47",
    }
    fuel_colours = fill_missing_colours(fuel_order, fuel_colours)
    df["Fuel"] = pd.Categorical(df["Fuel"], categories=fuel_order, ordered=True)

    periods = sorted(df["Period"].dropna().unique())
    full_index = pd.MultiIndex.from_product(
        [scenarios, periods, island_order, sector_order, fuel_order],
        names=["Scenario", "Period", "Island", "Sector", "Fuel"],
    )
    unit = df["Unit"].dropna().iloc[0] if not df["Unit"].dropna().empty else "PJ"
    df = (
        df.set_index(["Scenario", "Period", "Island", "Sector", "Fuel"])
        .reindex(full_index, fill_value=0)
        .reset_index()
    )
    df["Unit"] = unit
    df["Scenario"] = pd.Categorical(
        df["Scenario"],
        categories=scenarios,
        ordered=True,
    )
    df["Island"] = pd.Categorical(df["Island"], categories=island_order, ordered=True)
    df["Sector"] = pd.Categorical(df["Sector"], categories=sector_order, ordered=True)
    df["Fuel"] = pd.Categorical(df["Fuel"], categories=fuel_order, ordered=True)

    facet_values = {
        "Scenario": len(scenarios),
        "Island": len(island_order),
        "Sector": len(sector_order),
    }
    facet_vars = {"Scenario", "Island", "Sector"}
    row_vars = [facet_rows] if isinstance(facet_rows, str) else list(facet_rows)
    col_vars = [facet_cols] if isinstance(facet_cols, str) else list(facet_cols)
    unknown_facets = (set(row_vars) | set(col_vars)) - facet_vars
    if unknown_facets:
        raise ValueError(
            "Unknown facet variable(s): " + ", ".join(sorted(unknown_facets))
        )
    if len(scenarios) > 1 and "Scenario" not in row_vars + col_vars:
        row_vars = ["Scenario"] + row_vars

    row_count = 1
    for row_var in row_vars:
        row_count *= facet_values[row_var]
    col_count = 1
    for col_var in col_vars:
        col_count *= facet_values[col_var]

    width = max(8, 3.4 * col_count + 1.5)
    height = max(6, 1.15 * row_count + 2)

    if label_facets_above:
        wrapped_sector_labels = {
            sector: fill(str(sector), width=28) for sector in sector_order
        }
        facet_order = [
            f"{wrapped_sector_labels[sector]}\n{island}"
            for sector in sector_order
            for island in island_order
        ]
        df["FacetLabel"] = [
            f"{wrapped_sector_labels[str(sector)]}\n{island}"
            for sector, island in zip(
                df["Sector"].astype(str),
                df["Island"].astype(str),
            )
        ]
        df["FacetLabel"] = pd.Categorical(
            df["FacetLabel"],
            categories=facet_order,
            ordered=True,
        )
        facet = facet_wrap("~FacetLabel", ncol=col_count, scales="free_y")
    else:
        facet = facet_grid(rows=row_vars, cols=col_vars, scales="free_y")

    p = (
        ggplot(df, aes(x="Period", y="Value", fill="Fuel"))
        + geom_area()
        + facet
        + labs(
            title=chart_title,
            x="Year",
            y=unit,
            fill="Fuel",
        )
        + scale_x_continuous(breaks=[2025, 2030, 2035, 2040, 2045, 2050])
        + scale_y_continuous(limits=(0, None), labels=adaptive_tick_labels)
        + scale_fill_manual(values=fuel_colours, limits=fuel_order)
        + theme_minimal()
        + theme(legend_position="bottom")
    )

    p.save(
        f"analysis/{filename}",
        dpi=300,
        height=height,
        width=width,
        limitsize=False,
    )


def total_fuel_use_by_island_chart(
    end_use,
    sector_group,
    scenario,
    chart_title="Total process heat fuel use by island",
    filename="Total process heat fuel use by island.png",
    exclude_sector=None,
):
    """Create and save a fuel-use area chart aggregated to island level."""

    df = chart_data.get_fuel_use_by_island_and_sector(
        end_use=end_use,
        sector_group=sector_group,
        scenario=scenario,
    )
    if df.empty:
        raise ValueError("No fuel-use data found for the supplied filters.")

    if exclude_sector is not None:
        df = df[~df["Sector"].isin(exclude_sector)].copy()
        if df.empty:
            raise ValueError("No fuel-use data left after excluding sectors.")

    df = df.groupby(["Scenario", "Period", "Unit", "Island", "Fuel"], as_index=False)[
        "Value"
    ].sum()
    df["Period"] = pd.to_numeric(df["Period"], errors="coerce")

    scenarios = get_scenario_facet_order(df)
    df["Scenario"] = pd.Categorical(
        df["Scenario"],
        categories=scenarios,
        ordered=True,
    )

    preferred_island_order = ["North Island", "South Island"]
    available_islands = df["Island"].dropna().unique().tolist()
    island_order = [
        island for island in preferred_island_order if island in available_islands
    ]
    island_order.extend(sorted(set(available_islands) - set(island_order)))
    df["Island"] = pd.Categorical(df["Island"], categories=island_order, ordered=True)

    preferred_fuel_order = [
        "Coal",
        "Natural gas",
        "Fuel oil",
        "Diesel",
        "Petrol",
        "Jet fuel",
        "LPG",
        "Electricity",
        "Geothermal",
        "Solar",
        "Wood",
        "Wood residuals (onsite)",
        "Biogas",
        "Biomethane",
    ]
    available_fuels = df["Fuel"].dropna().unique().tolist()
    fuel_order = [fuel for fuel in preferred_fuel_order if fuel in available_fuels]
    fuel_order.extend(sorted(set(available_fuels) - set(fuel_order)))
    fuel_colours = {
        "Biogas": eeca_colours["emerald"],
        "Biomethane": "#73C6A5",
        "Coal": "grey",
        "Diesel": eeca_colours["orange"],
        "Electricity": eeca_colours["navy"],
        "Fuel oil": "#6E4F47",
        "Geothermal": "#A85E2E",
        "Jet fuel": eeca_colours["forest"],
        "LPG": "#C9A227",
        "Natural gas": eeca_colours["teal"],
        "Petrol": eeca_colours["coral"],
        "Solar": "#E9B949",
        "Wood": "#6F8F45",
        "Wood residuals (onsite)": "#8B6F47",
    }
    fuel_colours = fill_missing_colours(fuel_order, fuel_colours)
    df["Fuel"] = pd.Categorical(df["Fuel"], categories=fuel_order, ordered=True)

    periods = sorted(df["Period"].dropna().unique())
    full_index = pd.MultiIndex.from_product(
        [scenarios, periods, island_order, fuel_order],
        names=["Scenario", "Period", "Island", "Fuel"],
    )
    unit = df["Unit"].dropna().iloc[0] if not df["Unit"].dropna().empty else "PJ"
    df = (
        df.set_index(["Scenario", "Period", "Island", "Fuel"])
        .reindex(full_index, fill_value=0)
        .reset_index()
    )
    df["Unit"] = unit
    df["Scenario"] = pd.Categorical(
        df["Scenario"],
        categories=scenarios,
        ordered=True,
    )
    df["Island"] = pd.Categorical(df["Island"], categories=island_order, ordered=True)
    df["Fuel"] = pd.Categorical(df["Fuel"], categories=fuel_order, ordered=True)

    if len(scenarios) > 1:
        facet = facet_grid(rows="Scenario", cols="Island", scales="free_y")
        height = 3.3 * len(scenarios) + 1.5
    else:
        facet = facet_wrap("~Island", ncol=len(island_order), scales="free_y")
        height = 4.6
    width = max(7, 3.4 * len(island_order) + 1.5)

    p = (
        ggplot(df, aes(x="Period", y="Value", fill="Fuel"))
        + geom_area()
        + facet
        + labs(
            title=chart_title,
            x="Year",
            y=unit,
            fill="Fuel",
        )
        + scale_x_continuous(breaks=[2025, 2030, 2035, 2040, 2045, 2050])
        + scale_y_continuous(limits=(0, None), labels=adaptive_tick_labels)
        + scale_fill_manual(values=fuel_colours, limits=fuel_order)
        + theme_minimal()
        + theme(legend_position="bottom")
    )

    p.save(
        f"analysis/{filename}",
        dpi=300,
        height=height,
        width=width,
        limitsize=False,
    )


def electricity_generation_by_technology_chart(df):
    """Create and save faceted area charts of generation by technology."""

    if df.empty:
        raise ValueError("No electricity generation by technology group data found.")

    df = df.copy()
    df["Period"] = pd.to_numeric(df["Period"], errors="coerce")
    scenarios = get_scenario_facet_order(df)
    df["Scenario"] = pd.Categorical(
        df["Scenario"],
        categories=scenarios,
        ordered=True,
    )

    technology_order = sorted(df["TechnologyGroup"].dropna().unique().tolist())
    technology_colours = {
        "Geothermal": eeca_colours["coral"],
        "Hydro": eeca_colours["navy"],
        "Solar": eeca_colours["orange"],
        "Thermal": "grey",
        "Wind": eeca_colours["teal"],
    }
    technology_colours = fill_missing_colours(technology_order, technology_colours)
    df["TechnologyGroup"] = pd.Categorical(
        df["TechnologyGroup"],
        categories=technology_order,
        ordered=True,
    )

    periods = sorted(df["Period"].dropna().unique())
    full_index = pd.MultiIndex.from_product(
        [scenarios, periods, technology_order],
        names=["Scenario", "Period", "TechnologyGroup"],
    )
    df = (
        df.set_index(["Scenario", "Period", "TechnologyGroup"])
        .reindex(full_index, fill_value=0)
        .reset_index()
    )
    df["Scenario"] = pd.Categorical(
        df["Scenario"],
        categories=scenarios,
        ordered=True,
    )

    p = (
        ggplot(df, aes(x="Period", y="Value", fill="TechnologyGroup"))
        + geom_area()
        + facet_wrap("~Scenario", ncol=2)
        + labs(
            title="Electricity generation by technology",
            x="Year",
            y="TWh",
            fill="Technology",
        )
        + scale_x_continuous(breaks=[2025, 2030, 2035, 2040, 2045, 2050])
        + scale_y_continuous(limits=(0, None), labels=comma_format())
        + scale_fill_manual(values=technology_colours, limits=technology_order)
        + theme_minimal()
        + theme(legend_position="bottom")
    )

    p.save(
        "analysis/Electricity generation by technology.png",
        dpi=300,
        height=4.6,
        width=7,
    )


def thermal_generation_fuel_use_chart(df):
    """Create and save faceted area charts of fuel used by thermal plants."""

    if df.empty:
        raise ValueError("No thermal generation fuel-use data found.")

    df = df.copy()
    df["Period"] = pd.to_numeric(df["Period"], errors="coerce")
    scenarios = get_scenario_facet_order(df)
    df["Scenario"] = pd.Categorical(
        df["Scenario"],
        categories=scenarios,
        ordered=True,
    )

    fuel_order = sorted(df["Fuel"].dropna().unique().tolist())
    fuel_colours = {
        "Biogas": eeca_colours["emerald"],
        "Coal": "grey",
        "Diesel": eeca_colours["orange"],
        "Natural gas": eeca_colours["navy"],
        "Wood": eeca_colours["teal"],
    }
    fuel_colours = fill_missing_colours(fuel_order, fuel_colours)
    df["Fuel"] = pd.Categorical(
        df["Fuel"],
        categories=fuel_order,
        ordered=True,
    )

    periods = sorted(df["Period"].dropna().unique())
    full_index = pd.MultiIndex.from_product(
        [scenarios, periods, fuel_order],
        names=["Scenario", "Period", "Fuel"],
    )
    df = (
        df.set_index(["Scenario", "Period", "Fuel"])
        .reindex(full_index, fill_value=0)
        .reset_index()
    )
    df["Scenario"] = pd.Categorical(
        df["Scenario"],
        categories=scenarios,
        ordered=True,
    )

    p = (
        ggplot(df, aes(x="Period", y="Value", fill="Fuel"))
        + geom_area()
        + facet_wrap("~Scenario", ncol=2)
        + labs(
            title="Fuel used by thermal electricity generation",
            x="Year",
            y="PJ",
            fill="Fuel",
        )
        + scale_x_continuous(breaks=[2025, 2030, 2035, 2040, 2045, 2050])
        + scale_y_continuous(limits=(0, None), labels=comma_format())
        + scale_fill_manual(values=fuel_colours, limits=fuel_order)
        + theme_minimal()
        + theme(legend_position="bottom")
    )

    p.save(
        "analysis/Fuel used by thermal electricity generation.png",
        dpi=300,
        height=4.6,
        width=7,
    )


def battery_capacity_by_technology_group_chart(df):
    """Create and save faceted area charts of battery capacity by technology group."""

    if df.empty:
        raise ValueError("No battery capacity data found.")

    df = df.copy()
    df["Period"] = pd.to_numeric(df["Period"], errors="coerce")
    scenarios = get_scenario_facet_order(df)
    df["Scenario"] = pd.Categorical(
        df["Scenario"],
        categories=scenarios,
        ordered=True,
    )

    preferred_technology_order = [
        "Utility-scale battery",
        "Distributed battery",
    ]
    available_technologies = df["TechnologyGroup"].dropna().unique().tolist()
    technology_order = [
        technology
        for technology in preferred_technology_order
        if technology in available_technologies
    ]
    technology_order.extend(sorted(set(available_technologies) - set(technology_order)))
    technology_colours = {
        "Utility-scale battery": eeca_colours["navy"],
        "Distributed battery": eeca_colours["emerald"],
    }
    technology_colours = fill_missing_colours(technology_order, technology_colours)
    df["TechnologyGroup"] = pd.Categorical(
        df["TechnologyGroup"],
        categories=technology_order,
        ordered=True,
    )

    periods = sorted(df["Period"].dropna().unique())
    full_index = pd.MultiIndex.from_product(
        [scenarios, periods, technology_order],
        names=["Scenario", "Period", "TechnologyGroup"],
    )
    df = (
        df.set_index(["Scenario", "Period", "TechnologyGroup"])
        .reindex(full_index, fill_value=0)
        .reset_index()
    )
    df["Scenario"] = pd.Categorical(
        df["Scenario"],
        categories=scenarios,
        ordered=True,
    )

    p = (
        ggplot(df, aes(x="Period", y="Value", fill="TechnologyGroup"))
        + geom_area()
        + facet_wrap("~Scenario", ncol=2)
        + labs(
            title="Battery capacity by technology group",
            x="Year",
            y="GW",
            fill="Battery type",
        )
        + scale_x_continuous(breaks=[2025, 2030, 2035, 2040, 2045, 2050])
        + scale_y_continuous(limits=(0, None), labels=decimal_tick_labels)
        + scale_fill_manual(values=technology_colours, limits=technology_order)
        + theme_minimal()
        + theme(legend_position="bottom")
    )

    p.save(
        "analysis/Battery capacity by technology group.png",
        dpi=300,
        height=4.6,
        width=7,
    )


def lpv_transport_capacity_chart(df):
    """Create and save faceted area charts of LPV capacity by technology group."""

    if df.empty:
        raise ValueError("No light passenger vehicle transport capacity data found.")

    df = df.copy()
    df["Period"] = pd.to_numeric(df["Period"], errors="coerce")
    scenarios = get_scenario_facet_order(df)
    df["Scenario"] = pd.Categorical(
        df["Scenario"],
        categories=scenarios,
        ordered=True,
    )

    technology_label_map = {
        "Battery Electric Vehicle": "BEV",
        "Hybrid Vehicle": "Hybrid",
        "Internal Combustion Engine": "ICE",
        "Plug-in Hybrid Vehicle": "PHEV",
    }
    df["TechnologyType"] = (
        df["TechnologyGroup"].map(technology_label_map).fillna(df["TechnologyGroup"])
    )

    preferred_technology_order = [
        "ICE",
        "Hybrid",
        "PHEV",
        "BEV",
    ]
    available_technologies = df["TechnologyType"].dropna().unique().tolist()
    technology_order = [
        technology
        for technology in preferred_technology_order
        if technology in available_technologies
    ]
    technology_order.extend(sorted(set(available_technologies) - set(technology_order)))
    technology_colours = {
        "ICE": "grey",
        "Hybrid": eeca_colours["teal"],
        "PHEV": eeca_colours["emerald"],
        "BEV": eeca_colours["navy"],
    }
    technology_colours = fill_missing_colours(technology_order, technology_colours)
    df["TechnologyType"] = pd.Categorical(
        df["TechnologyType"],
        categories=technology_order,
        ordered=True,
    )

    periods = sorted(df["Period"].dropna().unique())
    full_index = pd.MultiIndex.from_product(
        [scenarios, periods, technology_order],
        names=["Scenario", "Period", "TechnologyType"],
    )
    df = (
        df.set_index(["Scenario", "Period", "TechnologyType"])
        .reindex(full_index, fill_value=0)
        .reset_index()
    )
    df["Scenario"] = pd.Categorical(
        df["Scenario"],
        categories=scenarios,
        ordered=True,
    )

    p = (
        ggplot(df, aes(x="Period", y="Value", fill="TechnologyType"))
        + geom_area()
        + facet_wrap("~Scenario", ncol=2)
        + labs(
            title="Light passenger vehicle capacity by technology",
            x="Year",
            y="Thousand vehicles",
            fill="Technology",
        )
        + scale_x_continuous(breaks=[2025, 2030, 2035, 2040, 2045, 2050])
        + scale_y_continuous(limits=(0, None), labels=comma_format())
        + scale_fill_manual(values=technology_colours, limits=technology_order)
        + theme_minimal()
        + theme(legend_position="bottom")
    )

    p.save(
        "analysis/Light passenger vehicle capacity by technology.png",
        dpi=300,
        height=4.6,
        width=7,
    )


def emissions_by_sector_group_chart(df):
    """Create and save faceted area charts of emissions by sector group."""

    if df.empty:
        raise ValueError("No emissions by sector group data found.")

    df = df.copy()
    df["Period"] = pd.to_numeric(df["Period"], errors="coerce")
    scenarios = get_scenario_facet_order(df)
    df["Scenario"] = pd.Categorical(
        df["Scenario"],
        categories=scenarios,
        ordered=True,
    )

    preferred_sector_order = [
        "Transport",
        "Industry",
        "Electricity generation",
        "Residential",
        "Commercial",
        "Agriculture, Forestry, and Fishing",
        "Fugitive emissions",
    ]
    available_sectors = df["SectorGroup"].dropna().unique().tolist()
    sector_order = [
        sector for sector in preferred_sector_order if sector in available_sectors
    ]
    sector_order.extend(sorted(set(available_sectors) - set(sector_order)))
    sector_colours = {
        "Transport": eeca_colours["navy"],
        "Industry": eeca_colours["forest"],
        "Electricity generation": eeca_colours["orange"],
        "Residential": eeca_colours["teal"],
        "Commercial": eeca_colours["coral"],
        "Agriculture, Forestry, and Fishing": eeca_colours["emerald"],
        "Fugitive emissions": "grey",
    }
    sector_colours = fill_missing_colours(sector_order, sector_colours)
    df["SectorGroup"] = pd.Categorical(
        df["SectorGroup"],
        categories=sector_order,
        ordered=True,
    )

    periods = sorted(df["Period"].dropna().unique())
    full_index = pd.MultiIndex.from_product(
        [scenarios, periods, sector_order],
        names=["Scenario", "Period", "SectorGroup"],
    )
    df = (
        df.set_index(["Scenario", "Period", "SectorGroup"])
        .reindex(full_index, fill_value=0)
        .reset_index()
    )
    df["Scenario"] = pd.Categorical(
        df["Scenario"],
        categories=scenarios,
        ordered=True,
    )

    p = (
        ggplot(df, aes(x="Period", y="Value", fill="SectorGroup"))
        + geom_area()
        + facet_wrap("~Scenario", ncol=2)
        + labs(
            title="Energy emissions by sector group",
            x="Year",
            y="MT CO2e",
            fill="Sector group",
        )
        + scale_x_continuous(breaks=[2025, 2030, 2035, 2040, 2045, 2050])
        + scale_y_continuous(limits=(0, None), labels=comma_format())
        + scale_fill_manual(values=sector_colours, limits=sector_order)
        + theme_minimal()
        + theme(legend_position="bottom")
    )

    p.save(
        "analysis/Energy emissions by sector group.png",
        dpi=300,
        height=4.6,
        width=7,
    )


def process_heat_chart(df):
    """Create and save faceted area charts for industrial process heat demand."""

    if df.empty:
        raise ValueError("No process heat data found.")

    df = df.copy()
    df["Period"] = pd.to_numeric(df["Period"], errors="coerce")
    scenarios = get_scenario_facet_order(df)
    df["Scenario"] = pd.Categorical(
        df["Scenario"],
        categories=scenarios,
        ordered=True,
    )

    # keep a fixed fuel order so stacking/order is stable
    fuel_order = [
        "Biogas",
        "Biomass",
        "Coal",
        "Electricity",
        "Natural gas",
        "Other",
    ]
    df["Fuel"] = pd.Categorical(df["Fuel"], categories=fuel_order, ordered=True)

    # aggregate first, if needed
    df = df.groupby(["Scenario", "Period", "Fuel"], as_index=False, observed=False)[
        "Value"
    ].sum()

    # complete all Period x Fuel combinations and fill missing with zero
    periods = sorted(df["Period"].dropna().unique())
    full_index = pd.MultiIndex.from_product(
        [scenarios, periods, fuel_order], names=["Scenario", "Period", "Fuel"]
    )

    df = (
        df.set_index(["Scenario", "Period", "Fuel"])
        .reindex(full_index, fill_value=0)
        .reset_index()
    )
    df["Scenario"] = pd.Categorical(
        df["Scenario"],
        categories=scenarios,
        ordered=True,
    )

    ph_cols = [
        eeca_colours["navy"],
        eeca_colours["teal"],
        eeca_colours["forest"],
        eeca_colours["emerald"],
        eeca_colours["orange"],
        "grey",
    ]

    p = (
        ggplot(df, aes(x="Period", y="Value", fill="Fuel", group="Fuel"))
        + geom_area()
        + facet_wrap("~Scenario", ncol=2)
        + labs(
            title="Industrial process heat demand",
            x="Year",
            y="PJ",
            fill="Fuel",
        )
        + scale_x_continuous(breaks=[2025, 2030, 2035, 2040, 2045, 2050])
        + scale_y_continuous(limits=(0, None), labels=comma_format())
        + scale_fill_manual(values=ph_cols, limits=fuel_order)
        + theme_minimal()
        + theme(legend_position="bottom")
    )

    p.save("analysis/Industrial process heat demand.png", dpi=300, height=4.6, width=7)


def make_chart(
    df,
    unit,
    chart_title,
    value_label=None,
    y_labels=None,
    y_limits=(0, None),
    min_gap=2,
    width=4,
    height=3,
    hline_y=None,
):
    """Create and save a labelled scenario line chart for the supplied data."""

    if value_label is None:

        def default_value_label(value):
            return f"{value:,.1f} {unit}"

        value_label = default_value_label
    if y_labels is None:
        y_labels = comma_format()

    scenario_sequence = df["Scenario"].drop_duplicates().tolist()
    palette = {
        scenario: chart_cols[i % len(chart_cols)]
        for i, scenario in enumerate(scenario_sequence)
    }

    df_last = df.sort_values("Period").groupby("Scenario", as_index=False).tail(1)

    df_last["label"] = df_last["Scenario"] + ": " + df_last["Value"].map(value_label)

    df_last = df_last.sort_values("Value").copy()
    df_last["y_adjusted"] = df_last["Value"]

    for i in range(1, len(df_last)):
        prev = df_last.iloc[i - 1]["y_adjusted"]
        curr = df_last.iloc[i]["y_adjusted"]

        if curr - prev < min_gap:
            df_last.iloc[i, df_last.columns.get_loc("y_adjusted")] = prev + min_gap

    p = ggplot(df, aes(x="Period", y="Value", color="Scenario"))
    if hline_y is not None:
        p = p + geom_hline(
            yintercept=hline_y,
            linetype="dotted",
            color="grey",
            size=0.8,
        )

    p = (
        p
        + geom_line(size=1)
        + geom_label(
            data=df_last,
            mapping=aes(x="Period", y="y_adjusted", label="label", fill="Scenario"),
            colour="white",
            ha="left",
            nudge_x=0.5,
            size=8,
        )
        + labs(title=chart_title, x="Year", y=unit)
        + scale_x_continuous(
            breaks=[2025, 2030, 2035, 2040, 2045, 2050], limits=(2023, 2065)
        )
        + scale_y_continuous(limits=y_limits, labels=y_labels)
        + theme_minimal()
        + theme(legend_position="none")
        + scale_color_manual(values=palette, na_value="grey")
        + scale_fill_manual(values=palette, na_value="grey")
    )

    p.save(f"analysis/{chart_title}.png", dpi=300, height=height, width=width)


def chart_elec_gen(df):
    """Create and save the electricity generation line chart."""

    df_last = df.sort_values("Period").groupby("Scenario", as_index=False).tail(1)

    df_last["label"] = (
        df_last["Scenario"] + ": " + df_last["Value"].map(lambda v: f"{v:,.1f}") + "TWh"
    )

    p = (
        ggplot(df, aes(x="Period", y="Value", color="Scenario"))
        + geom_line(size=1)
        + geom_label(
            data=df_last,
            mapping=aes(x="Period", y="Value", label="label", fill="Scenario"),
            colour="white",
            ha="left",
            nudge_x=0.5,
            size=8,
        )
        + labs(title="Electricity generation", x="Year", y="TWh")
        + scale_x_continuous(
            breaks=[2025, 2030, 2035, 2040, 2045, 2050], limits=(2023, 2060)
        )
        + scale_y_continuous(limits=(0, None), labels=comma_format())
        + theme_minimal()
        + theme(legend_position="none")
        + scale_color_manual(values=eeca_colours, na_value="grey")
        + scale_fill_manual(values=eeca_colours, na_value="grey")
    )

    p.save("analysis/elec.png", dpi=300, height=3, width=4)


def main():
    """Build the analysis datasets and save the chart outputs."""

    df_elc = chart_data.get_elec_gen(compare_other_models=False)
    df_ems = chart_data.get_emissions(compare_other_models=False)
    df_ems_by_sector = chart_data.get_emissions_by_sector_group()
    df_elc_by_tech = chart_data.get_elec_gen(
        compare_other_models=False,
        groupby_cols="TechnologyGroup",
    )
    df_thermal_fuel_use = chart_data.get_thermal_generation_fuel_use()
    df_battery_capacity = chart_data.get_battery_capacity()
    df_lpv_transport_capacity = chart_data.get_lpv_transport_capacity()
    df_ren_elc = chart_data.get_renewable_electricity_share().rename(
        columns={"RenewableShareOfElectricity": "Value"}
    )
    df_ren_tfec = chart_data.get_renewable_tfec().rename(
        columns={"RenewableShareOfTFEC": "Value"}
    )

    df_pht = chart_data.get_process_heat()

    process_heat_chart(df_pht)

    # Use empty lists to include all values for that filter.
    fuel_use_grid_end_use = [
        "Low Temperature Heat (<100 C), Process Requirements",
        "Intermediate Heat (100-300 C), Process Requirements",
        "High Temperature Heat (>300 C), Process Requirements",
        "Intermediate Heat (100-300 C), Cooking",
    ]
    fuel_use_grid_sector_group = [
        "Agriculture, Forestry, and Fishing",
        "Commercial",
        "Industry",
    ]
    fuel_use_grid_scenario = ["Steady"]
    fuel_use_grid_exclude_sector = [
        "Aluminium",
        "Iron & Steel",
        "Methanol",
        "Urea",
    ]
    space_heating_grid_end_use = [
        "Low Temperature Heat (<100 C), Space Heating",
    ]
    space_heating_grid_sector_group = [
        "Agriculture, Forestry, and Fishing",
        "Commercial",
        "Industry",
    ]

    make_chart(df_elc, "TWh", "Electricity generation")
    make_chart(df_ems, "MT CO2e", "Energy emissions")
    emissions_by_sector_group_chart(df_ems_by_sector)
    electricity_generation_by_technology_chart(df_elc_by_tech)
    thermal_generation_fuel_use_chart(df_thermal_fuel_use)
    battery_capacity_by_technology_group_chart(df_battery_capacity)
    lpv_transport_capacity_chart(df_lpv_transport_capacity)
    fuel_use_area_grid_chart(
        end_use=fuel_use_grid_end_use,
        sector_group=fuel_use_grid_sector_group,
        scenario=fuel_use_grid_scenario,
        facet_rows="Sector",
        facet_cols="Island",
        chart_title="Process heat fuel use by island and sector",
        filename="Process heat fuel use by island and sector.png",
        label_facets_above=True,
        exclude_sector=fuel_use_grid_exclude_sector,
    )
    total_fuel_use_by_island_chart(
        end_use=fuel_use_grid_end_use,
        sector_group=fuel_use_grid_sector_group,
        scenario=fuel_use_grid_scenario,
        exclude_sector=fuel_use_grid_exclude_sector,
    )
    fuel_use_area_grid_chart(
        end_use=space_heating_grid_end_use,
        sector_group=space_heating_grid_sector_group,
        scenario=fuel_use_grid_scenario,
        facet_rows="Sector",
        facet_cols="Island",
        chart_title="Space heating fuel use by island and sector",
        filename="Space heating fuel use by island and sector.png",
        label_facets_above=True,
        exclude_sector=fuel_use_grid_exclude_sector,
    )
    total_fuel_use_by_island_chart(
        end_use=space_heating_grid_end_use,
        sector_group=space_heating_grid_sector_group,
        scenario=fuel_use_grid_scenario,
        chart_title="Total space heating fuel use by island",
        filename="Total space heating fuel use by island.png",
        exclude_sector=fuel_use_grid_exclude_sector,
    )
    make_chart(
        df_ren_elc,
        "%",
        "Renewable share of electricity generation",
        value_label=lambda v: f"{v:.1%}",
        y_labels=percent_format(),
        y_limits=(None, 1),
        min_gap=0.02,
        width=6,
        hline_y=1,
    )
    make_chart(
        df_ren_tfec,
        "%",
        "Renewable share of TFEC",
        value_label=lambda v: f"{v:.1%}",
        y_labels=percent_format(),
        y_limits=(0, 1),
        min_gap=0.02,
        width=6,
    )


if __name__ == "__main__":
    main()
