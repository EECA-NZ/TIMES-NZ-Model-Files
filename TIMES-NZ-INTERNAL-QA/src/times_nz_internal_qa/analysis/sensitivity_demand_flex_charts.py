"""Demand-flex sensitivity analysis charts.

This module intentionally uses its own scenario code/name mapping instead of
the global current_scenarios config. Sensitivity scenarios are often temporary
or exploratory, so keeping that mapping local avoids changing the main app and
standard analysis outputs.
"""

from pathlib import Path

import times_nz_internal_qa.analysis.get_data as chart_data

# isort is clashing with pylint on what order these should go in, so disable pylint
# pylint:disable = wildcard-import, unused-wildcard-import, wrong-import-order, duplicate-code
from plotnine import *
from times_nz_internal_qa.analysis.analysis_chart_helpers import (
    PJ_TO_GWH,
    adaptive_tick_labels,
    chart_cols_line,
    save_chart_and_data,
    standardise_island_order,
    standardise_scenario_order,
)

DEMAND_FLEX_SENSITIVITY_SCENARIOS = {
    "steady-v308": "Steady",
    "steady-v308-noflex": "Steady (no DF or batteries)",
    "steady-v308-nodf": "Steady (Batteries, no DF)",
    "steady-v308-shiftdf": "Steady (Shift Flex)",
    "steady-v308-nobatt": "Steady (no batteries)",
    "shift-v308": "Shift",
    "shift-v308-noflex": "Shift (no DF or batteries)",
    "shift-v308-nodf": "Shift (Batteries, no DF)",
    "shift-v308-steadydf": "Shift (Steady Flex)",
    "shift-v308-nobatt": "Shift (no batteries)",
}

SHIFT_NO_DF_COMPARISON_SCENARIOS = {
    "shift-v308": "Shift",
    "shift-v308-nodf": "Shift (no DF)",
}

STEADY_TECHNOLOGY_COMPARISON_SCENARIOS = {
    "steady-v308": "Steady",
    "steady-v308-nobatt": "Steady (no batteries)",
    "steady-v308-nodf": "Steady (batteries, no DF)",
    "steady-v308-noflex": "Steady (no DF or batteries)",
}

SHIFT_TECHNOLOGY_COMPARISON_SCENARIOS = {
    "shift-v308": "Shift",
    "shift-v308-nobatt": "Shift (no batteries)",
    "shift-v308-nodf": "Shift (batteries, no DF)",
    "shift-v308-noflex": "Shift (no DF or batteries)",
}

SENSITIVITY_OUTPUT_DIR = Path("analysis/sensitivity")


def ensure_sensitivity_output_dir():
    """Create the sensitivity chart output folder if needed."""

    SENSITIVITY_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _resolve_scenario_map(scenarios=None, scenario_map=None):
    """Return a code/name mapping from a dict, list of codes, or default."""

    if scenario_map is None:
        scenario_map = DEMAND_FLEX_SENSITIVITY_SCENARIOS

    if scenarios is None:
        return dict(scenario_map)

    if isinstance(scenarios, dict):
        return dict(scenarios)

    return {
        scenario_code: scenario_map.get(scenario_code, scenario_code)
        for scenario_code in scenarios
    }


def _sensitivity_scenario_order(scenario_map=None):
    """Return scenario display names in the order defined by the local mapping."""

    if scenario_map is None:
        scenario_map = DEMAND_FLEX_SENSITIVITY_SCENARIOS

    return list(dict.fromkeys(scenario_map.values()))


def _standardise_sensitivity_chart_data(df, scenario_map=None):
    """Apply chart ordering using this module's local scenario names."""

    df = standardise_island_order(df)
    df = standardise_scenario_order(
        df, scenario_order=_sensitivity_scenario_order(scenario_map)
    )
    return df


def get_sensitivity_emissions(scenarios=None):
    """Return total emissions for the selected sensitivity scenarios."""

    scenario_map = _resolve_scenario_map(
        scenarios, scenario_map=SHIFT_NO_DF_COMPARISON_SCENARIOS
    )
    df = chart_data.get_times_data("emissions.parquet", scenario_map=scenario_map)
    df = df.groupby(["Scenario", "Period", "Unit"])["Value"].sum().reset_index()
    df["Value"] = df["Value"] / 1000
    df["Unit"] = "MT CO2e"
    return _standardise_sensitivity_chart_data(df, scenario_map=scenario_map)


def get_sensitivity_electricity_demand(scenarios=None):
    """Return total annual electricity demand for selected sensitivity scenarios."""

    scenario_map = _resolve_scenario_map(
        scenarios, scenario_map=SHIFT_NO_DF_COMPARISON_SCENARIOS
    )
    df = chart_data.get_times_data("energy_demand.parquet", scenario_map=scenario_map)
    df = df[df["Variable"] == "Energy demand"].copy()
    df = df[df["Fuel"] == "Electricity"].copy()
    df = df.groupby(["Scenario", "Period", "Unit"])["Value"].sum().reset_index()
    df["Value"] = df["Value"] * PJ_TO_GWH / 1000
    df["Unit"] = "TWh"
    return _standardise_sensitivity_chart_data(df, scenario_map=scenario_map)


def _create_sensitivity_line_chart(df, title, filename):
    """Create a sensitivity line chart with scenarios as colour series."""

    ensure_sensitivity_output_dir()
    label_year = 2050 if 2050 in set(df["Period"]) else df["Period"].max()
    label_df = df[df["Period"] == label_year].copy()
    label_df["EndpointLabel"] = adaptive_tick_labels(label_df["Value"])
    x_min = df["Period"].min()
    x_max = df["Period"].max()

    p = (
        ggplot(df, aes(x="Period", y="Value", colour="Scenario"))
        + geom_line(size=1)
        + geom_point(size=1.7)
        + geom_text(
            label_df,
            aes(label="EndpointLabel"),
            nudge_x=0.7,
            ha="left",
            va="center",
            size=8,
            show_legend=False,
        )
        + labs(
            title=title,
            x="",
            y=df["Unit"].iloc[0],
            colour="Scenario",
        )
        + scale_x_continuous(limits=(x_min, x_max + 3))
        + scale_y_continuous(labels=adaptive_tick_labels)
        + scale_colour_manual(values=chart_cols_line, na_value="#7F7F7F")
        + theme_minimal()
        + theme(
            legend_position="bottom",
            panel_grid_minor_x=element_blank(),
        )
    )

    save_chart_and_data(df, p, f"sensitivity/{filename}", height=4.5, width=7)
    return p


def create_shift_technology_emissions_chart(scenarios=None):
    """Create emissions chart for Shift technology sensitivity scenarios."""

    if scenarios is None:
        scenarios = SHIFT_TECHNOLOGY_COMPARISON_SCENARIOS

    df = get_sensitivity_emissions(scenarios=scenarios)
    return _create_sensitivity_line_chart(
        df,
        "Emissions sensitivity: Shift technologies",
        "shift_technology_emissions.png",
    )


def create_shift_technology_electricity_demand_chart(scenarios=None):
    """Create electricity demand chart for Shift technology sensitivity scenarios."""

    if scenarios is None:
        scenarios = SHIFT_TECHNOLOGY_COMPARISON_SCENARIOS

    df = get_sensitivity_electricity_demand(scenarios=scenarios)
    return _create_sensitivity_line_chart(
        df,
        "Electricity demand sensitivity: Shift technologies",
        "shift_technology_electricity_demand.png",
    )


def create_steady_technology_emissions_chart(scenarios=None):
    """Create emissions chart for Steady technology sensitivity scenarios."""

    if scenarios is None:
        scenarios = STEADY_TECHNOLOGY_COMPARISON_SCENARIOS
    df = get_sensitivity_emissions(scenarios=scenarios)
    return _create_sensitivity_line_chart(
        df,
        "Emissions sensitivity: Steady technologies",
        "steady_technology_emissions.png",
    )


def create_steady_technology_electricity_demand_chart(scenarios=None):
    """Create electricity demand chart for Steady technology sensitivity scenarios."""

    if scenarios is None:
        scenarios = STEADY_TECHNOLOGY_COMPARISON_SCENARIOS
    df = get_sensitivity_electricity_demand(scenarios=scenarios)
    return _create_sensitivity_line_chart(
        df,
        "Electricity demand sensitivity: Steady technologies",
        "steady_technology_electricity_demand.png",
    )


def main():
    """Write demand-flex sensitivity charts."""

    ensure_sensitivity_output_dir()
    create_shift_technology_emissions_chart()
    create_shift_technology_electricity_demand_chart()
    create_steady_technology_emissions_chart()
    create_steady_technology_electricity_demand_chart()


if __name__ == "__main__":
    main()
