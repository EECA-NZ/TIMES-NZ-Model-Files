"""Demand-flex sensitivity reporting outputs."""

from pathlib import Path

import pandas as pd
from times_nz_internal_qa.utilities.filepaths import FINAL_DATA

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

SENSITIVITY_OUTPUT_DIR = Path("analysis/sensitivity")

OBJECTIVE_SUMMARY_ROWS = [
    ("Base", "steady-v308", "shift-v308"),
    ("No demand flex", "steady-v308-nodf", "shift-v308-nodf"),
    ("No batteries", "steady-v308-nobatt", "shift-v308-nobatt"),
    ("No demand flex or batteries", "steady-v308-noflex", "shift-v308-noflex"),
]


def _resolve_scenario_map(
    scenarios=None, scenario_map=DEMAND_FLEX_SENSITIVITY_SCENARIOS
):
    """Return a code/name mapping from a dict, list of codes, or default."""

    if scenarios is None:
        return dict(scenario_map)

    if isinstance(scenarios, dict):
        return dict(scenarios)

    return {
        scenario_code: scenario_map.get(scenario_code, scenario_code)
        for scenario_code in scenarios
    }


def _sensitivity_scenario_order(scenario_map=DEMAND_FLEX_SENSITIVITY_SCENARIOS):
    """Return scenario display names in the order defined by the local mapping."""

    return list(dict.fromkeys(scenario_map.values()))


def _get_objective_lookup(scenario_map=DEMAND_FLEX_SENSITIVITY_SCENARIOS):
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


def _format_nzdb(value):
    """Format an NZDb value for markdown tables."""

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


def _objective_value(objectives, scenario_code):
    """Return an objective value, failing clearly if a required code is absent."""

    if scenario_code not in objectives:
        raise ValueError(f"Missing objective function value for {scenario_code}")
    return objectives[scenario_code]


def create_demand_flex_sensitivity_objective_functions(
    scenarios=None,
    scenario_map=DEMAND_FLEX_SENSITIVITY_SCENARIOS,
    output_file=SENSITIVITY_OUTPUT_DIR / "demand_flex_sensitivity_objective_functions.csv",
):
    """Write objective-function values for the selected sensitivity scenarios."""

    scenario_map = _resolve_scenario_map(scenarios, scenario_map)
    objective_df = pd.read_parquet(FINAL_DATA / "objective_function.parquet")
    objective_df = objective_df[objective_df["Scenario"].isin(scenario_map)].copy()
    found_scenarios = set(objective_df["Scenario"])
    missing_scenarios = sorted(set(scenario_map) - found_scenarios)
    if missing_scenarios:
        raise ValueError(
            "Missing objective function value for scenario(s): "
            + ", ".join(missing_scenarios)
        )

    objective_counts = objective_df.groupby("Scenario").size()
    duplicate_scenarios = objective_counts[objective_counts > 1]
    if not duplicate_scenarios.empty:
        scenarios = ", ".join(duplicate_scenarios.index.astype(str))
        raise ValueError(
            f"Expected one objective function value per scenario: {scenarios}"
        )

    objective_df["ScenarioCode"] = objective_df["Scenario"]
    objective_df["Scenario"] = objective_df["Scenario"].map(scenario_map)
    objective_df["Scenario"] = pd.Categorical(
        objective_df["Scenario"],
        categories=_sensitivity_scenario_order(scenario_map),
        ordered=True,
    )

    objective_variables = [
        "ScenarioCode",
        "Scenario",
        "Attribute",
        "Variable",
        "Unit",
        "Value",
    ]
    objective_df = objective_df[objective_variables].sort_values("Scenario")
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    objective_df.to_csv(output_file, index=False)
    return objective_df


def create_objective_summary_table():
    """Create objective values by sensitivity row and core scenario."""

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


def _technology_values_for_family(objectives, family):
    """Return implied technology values for one scenario family."""

    base = _objective_value(objectives, f"{family}-v308")
    flex = _objective_value(objectives, f"{family}-v308-nodf") - base
    batteries = _objective_value(objectives, f"{family}-v308-nobatt") - base
    combined = _objective_value(objectives, f"{family}-v308-noflex") - base
    interaction = combined - flex - batteries
    return {
        "Demand flex": flex,
        "Batteries": batteries,
        "Demand flex and batteries": combined,
        "Interaction effect": interaction,
    }


def create_technology_value_table():
    """Create implied values of demand flex, batteries, and their interaction."""

    objectives = _get_objective_lookup()
    steady_values = _technology_values_for_family(objectives, "steady")
    shift_values = _technology_values_for_family(objectives, "shift")

    rows = []
    for label in [
        "Demand flex",
        "Batteries",
        "Demand flex and batteries",
        "Interaction effect",
    ]:
        rows.append(
            [
                label,
                _format_nzdb(steady_values[label]),
                _format_nzdb(shift_values[label]),
            ]
        )

    return _markdown_table(["Value component", "Steady (NZDb)", "Shift (NZDb)"], rows)


def _demand_flex_technology_shapley_values(objectives):
    """Return two-path Shift demand-flex technology values."""

    comparisons = [
        (
            "Steady",
            "steady-v308",
            "steady-v308-shiftdf",
        ),
        (
            "Shift",
            "shift-v308-steadydf",
            "shift-v308",
        ),
    ]
    rows = []
    for label, steady_df_code, shift_df_code in comparisons:
        steady_df_objective = _objective_value(objectives, steady_df_code)
        shift_df_objective = _objective_value(objectives, shift_df_code)
        value = steady_df_objective - shift_df_objective
        rows.append(
            {
                "Base scenario": label,
                "Steady DF objective": steady_df_objective,
                "Shift DF objective": shift_df_objective,
                "Value": value,
            }
        )
    return rows


def _mean_shift_demand_flex_technology_value(objectives):
    """Return mean two-path value of Shift demand-flex technology."""

    values = [row["Value"] for row in _demand_flex_technology_shapley_values(objectives)]
    return sum(values) / len(values)


def create_demand_flex_technology_shapley_table():
    """Create a two-path Shapley-style value table for Shift demand-flex tech."""

    objectives = _get_objective_lookup()
    shapley_rows = _demand_flex_technology_shapley_values(objectives)
    rows = []
    for row in shapley_rows:
        rows.append(
            [
                row["Base scenario"],
                _format_nzdb(row["Steady DF objective"]),
                _format_nzdb(row["Shift DF objective"]),
                _format_nzdb(row["Value"]),
            ]
        )

    rows.append(
        [
            "Mean",
            "",
            "",
            _format_nzdb(_mean_shift_demand_flex_technology_value(objectives)),
        ]
    )
    return _markdown_table(
        [
            "Base scenario",
            "Steady DF objective (NZDb)",
            "Shift DF objective (NZDb)",
            "Implied value of Shift DF (NZDb)",
        ],
        rows,
    )


def create_shift_demand_flex_technology_share_text():
    """Return text comparing additional Shift combined value to technology value."""

    objectives = _get_objective_lookup()
    steady_values = _technology_values_for_family(objectives, "steady")
    shift_values = _technology_values_for_family(objectives, "shift")
    additional_shift_value = (
        shift_values["Demand flex and batteries"]
        - steady_values["Demand flex and batteries"]
    )
    technology_value = _mean_shift_demand_flex_technology_value(objectives)
    technology_share = technology_value / additional_shift_value

    return (
        "Additional Shift combined demand-flex and batteries value is "
        f"{_format_nzdb(additional_shift_value)} NZDb "
        "(Shift `noflex - base` value minus Steady `noflex - base` value). The mean "
        f"Shift demand-flex technology value is {_format_nzdb(technology_value)} NZDb, "
        f"implying {technology_share:.1%} of the additional Shift combined value."
    )


def create_demand_flex_sensitivity_markdown(
    output_file=SENSITIVITY_OUTPUT_DIR / "demand_flex_sensitivity_summary.md",
):
    """Write a small markdown summary of demand-flex sensitivity objectives."""

    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    content = "\n\n".join(
        [
            "# Demand Flex Sensitivity Summary",
            "Objective values are reported in NZDb. Lower objective values are lower total system cost.",
            "## Objective Functions",
            create_objective_summary_table(),
            "## Implied Technology Values",
            (
                "Values are calculated as the increase in objective value when an option is removed "
                "relative to the base scenario. The interaction effect is calculated as "
                "`combined value - demand flex value - batteries value`."
            ),
            create_technology_value_table(),
            "## Shift Demand-Flex Technology Decomposition",
            (
                "This table compares the objective value under Steady demand-flex "
                "technology and Shift demand-flex technology within each base scenario. "
                "The implied value is `Steady DF objective - Shift DF objective`; the "
                "mean is the two-path Shapley-style estimate of the value attributable "
                "to the improved Shift demand-flex technology."
            ),
            create_demand_flex_technology_shapley_table(),
            create_shift_demand_flex_technology_share_text(),
            (
                "Interpretation note: these values are marginal to the scenario definitions. "
                "A positive interaction effect means removing both options raises system cost "
                "by more than the sum of removing each option separately; a negative value means "
                "the combined removal is less costly than that simple sum. This is not a standalone "
                "market value for either technology."
            ),
        ]
    )
    Path(output_file).write_text(content + "\n", encoding="utf-8")
    return output_file


def main():
    """Write demand-flex sensitivity reporting outputs."""

    create_demand_flex_sensitivity_objective_functions()
    create_demand_flex_sensitivity_markdown()


if __name__ == "__main__":
    main()
