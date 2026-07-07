"""ETS price sensitivity reporting outputs."""

from pathlib import Path

import pandas as pd
from times_nz_internal_qa.utilities.filepaths import FINAL_DATA

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


def _get_objective_lookup(scenario_map=ETS_PRICE_SENSITIVITY_SCENARIOS):
    """Return objective values keyed by raw scenario code."""

    objective_df = pd.read_parquet(FINAL_DATA / "objective_function.parquet")
    objective_df = objective_df[objective_df["Scenario"].isin(scenario_map)].copy()
    objective_counts = objective_df.groupby("Scenario").size()
    duplicate_scenarios = objective_counts[objective_counts > 1]
    if not duplicate_scenarios.empty:
        scenarios = ", ".join(duplicate_scenarios.index.astype(str))
        raise ValueError(
            f"Expected one objective function value per scenario: {scenarios}"
        )
    return objective_df.set_index("Scenario")["Value"].to_dict()


def _objective_value(objectives, scenario_code):
    """Return an objective value, failing clearly if a required code is absent."""

    if scenario_code not in objectives:
        raise ValueError(f"Missing objective function value for {scenario_code}")
    return objectives[scenario_code]


def _format_nzdb(value):
    """Format an NZDb value for markdown tables."""

    if pd.isna(value):
        return ""
    return f"{value:,.3f}"


def _format_mionzd(value):
    """Format a Mio NZD value for markdown tables."""

    if pd.isna(value):
        return ""
    return f"{value:,.3f}"


def _markdown_table(headers, rows):
    """Render a simple GitHub-flavoured markdown table."""

    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(value) for value in row) + " |")
    return "\n".join(lines)


def create_objective_summary_table():
    """Create objective values for base and no-ETS scenarios."""

    objectives = _get_objective_lookup()
    rows = []
    for label, steady_code, shift_code in OBJECTIVE_SUMMARY_ROWS:
        rows.append(
            [
                label,
                _format_nzdb(_objective_value(objectives, steady_code)),
                _format_nzdb(_objective_value(objectives, shift_code)),
            ]
        )
    return _markdown_table(["Sensitivity", "Steady (NZDb)", "Shift (NZDb)"], rows)


def _get_total_carbon_cost_lookup(scenario_map=BASE_SCENARIOS):
    """Return total carbon costs keyed by raw scenario code."""

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
    return _markdown_table(["Scenario", "Total carbon cost (Mio NZD)"], rows)


def create_ets_price_sensitivity_markdown(
    output_file=SENSITIVITY_OUTPUT_DIR / "ets_price_sensitivity_summary.md",
):
    """Write a small markdown summary of ETS price sensitivity results."""

    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    content = "\n\n".join(
        [
            "# ETS Price Sensitivity Summary",
            "Objective values are reported in NZDb. Lower objective values are lower total system cost.",
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
