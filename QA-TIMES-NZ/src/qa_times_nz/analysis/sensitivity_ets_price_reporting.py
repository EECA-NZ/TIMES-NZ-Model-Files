"""ETS price sensitivity reporting outputs."""

from pathlib import Path

import pandas as pd

from qa_times_nz.analysis.analysis_reporting_helpers import (
    OBJECTIVE_SUMMARY_NOTE,
    build_objective_summary_table,
    get_objective_lookup,
    markdown_table,
)
from qa_times_nz.utilities.filepaths import FINAL_DATA

ETS_PRICE_SENSITIVITY_SCENARIOS = {
    "steady-v308": "Steady",
    "steady-v308-noets": "Steady (no ETS)",
    "steady-v308-shiftets": "Steady (Shift ETS)",
    "shift-v308": "Shift",
    "shift-v308-noets": "Shift (no ETS)",
    "shift-v308-steadyets": "Shift (Steady ETS)",
}

SENSITIVITY_OUTPUT_DIR = Path("analysis/sensitivity")

OBJECTIVE_SUMMARY_ROWS = [
    ("Base", "steady-v308", "shift-v308"),
    ("No ETS", "steady-v308-noets", "shift-v308-noets"),
]

BASE_SCENARIOS = {
    "steady-v308": "Steady",
    "shift-v308": "Shift",
}


def _get_objective_lookup(scenario_map=None):
    """Return objective values keyed by raw scenario code."""

    if scenario_map is None:
        scenario_map = ETS_PRICE_SENSITIVITY_SCENARIOS

    objective_df = pd.read_parquet(FINAL_DATA / "objective_function.parquet")
    return get_objective_lookup(objective_df, scenario_map)


def _format_mionzd(value):
    """Format a Mio NZD value for markdown tables."""

    if pd.isna(value):
        return ""
    return f"{value:,.3f}"


def create_objective_summary_table():
    """Create objective values for base and no-ETS scenarios."""

    return build_objective_summary_table(
        _get_objective_lookup(), OBJECTIVE_SUMMARY_ROWS
    )


def _get_total_carbon_cost_lookup(scenario_map=None):
    """Return total carbon costs keyed by raw scenario code."""

    if scenario_map is None:
        scenario_map = BASE_SCENARIOS

    carbon_costs = pd.read_parquet(FINAL_DATA / "carbon_costs.parquet")
    carbon_costs = carbon_costs[
        (carbon_costs["Scenario"].isin(scenario_map))
        & (carbon_costs["Variable"] == "Carbon cost")
    ].copy()
    return carbon_costs.groupby("Scenario")["Value"].sum().to_dict()


def create_base_carbon_cost_table():
    """Create total carbon-cost values for base Steady and Shift scenarios."""

    total_costs = _get_total_carbon_cost_lookup()
    rows = []
    for scenario_code, scenario_label in BASE_SCENARIOS.items():
        if scenario_code not in total_costs:
            raise ValueError(f"Missing carbon cost output for {scenario_code}")
        rows.append([scenario_label, _format_mionzd(total_costs[scenario_code])])
    return markdown_table(["Scenario", "Total carbon cost (Mio NZD)"], rows)


def create_ets_price_sensitivity_markdown(
    output_file=SENSITIVITY_OUTPUT_DIR / "ets_price_sensitivity_summary.md",
):
    """Write a small markdown summary of ETS price sensitivity results."""

    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    content = "\n\n".join(
        [
            "# ETS Price Sensitivity Summary",
            OBJECTIVE_SUMMARY_NOTE,
            "## Objective Functions",
            create_objective_summary_table(),
            "## Base Scenario Carbon Costs",
            create_base_carbon_cost_table(),
        ]
    )
    Path(output_file).write_text(content + "\n", encoding="utf-8")
    return output_file


def main():
    """Write ETS price sensitivity reporting outputs."""

    create_ets_price_sensitivity_markdown()


if __name__ == "__main__":
    main()
