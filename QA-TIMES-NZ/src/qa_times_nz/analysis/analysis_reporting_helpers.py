"""Shared formatting and validation for sensitivity reports."""

import pandas as pd

OBJECTIVE_SUMMARY_NOTE = (
    "Objective values are reported in NZDb. "
    "Lower objective values are lower total system cost."
)


def get_objective_lookup(objective_df, scenario_map):
    """Return objective values keyed by raw scenario code."""

    objective_df = objective_df[objective_df["Scenario"].isin(scenario_map)].copy()
    validate_unique_objectives(objective_df)
    return objective_df.set_index("Scenario")["Value"].to_dict()


def validate_unique_objectives(objective_df):
    """Require one objective value for each scenario present in the data."""

    objective_counts = objective_df.groupby("Scenario").size()
    duplicate_scenarios = objective_counts[objective_counts > 1]
    if not duplicate_scenarios.empty:
        scenarios = ", ".join(duplicate_scenarios.index.astype(str))
        raise ValueError(
            f"Expected one objective function value per scenario: {scenarios}"
        )


def format_nzdb(value):
    """Format an NZDb value for markdown tables."""

    if pd.isna(value):
        return ""
    return f"{value:,.3f}"


def markdown_table(headers, rows):
    """Render a simple GitHub-flavoured markdown table."""

    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(value) for value in row) + " |")
    return "\n".join(lines)


def objective_value(objectives, scenario_code):
    """Return an objective value, failing clearly if a required code is absent."""

    if scenario_code not in objectives:
        raise ValueError(f"Missing objective function value for {scenario_code}")
    return objectives[scenario_code]


def build_objective_summary_table(objectives, summary_rows):
    """Create objective values by sensitivity row and core scenario."""

    rows = []
    for label, steady_code, shift_code in summary_rows:
        rows.append(
            [
                label,
                format_nzdb(objective_value(objectives, steady_code)),
                format_nzdb(objective_value(objectives, shift_code)),
            ]
        )
    return markdown_table(["Sensitivity", "Steady (NZDb)", "Shift (NZDb)"], rows)
