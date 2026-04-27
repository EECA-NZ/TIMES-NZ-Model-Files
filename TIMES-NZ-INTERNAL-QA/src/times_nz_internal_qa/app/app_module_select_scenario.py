"""
Server and UI functions for scenario selection
For now, the target is to just provide a main dropdown list,
    then a secondary dropdown for optional comparisons
"""

from shiny import reactive, render, ui
from shiny.types import SilentException
from times_nz_internal_qa.config import current_scenarios
from times_nz_internal_qa.utilities.value_mappings import get_choice_labels

NO_COMPARISON = "__none__"


# pylint:disable = unused-argument
def scenario_select_server(inputs, outputs, session):
    """Server processing for currently selected scenario(s)"""

    @render.ui
    def select_scenario_a_ui():
        opts = get_choice_labels("Scenario", current_scenarios)
        return ui.div(
            ui.tags.h4("Main scenario:", class_="filter-section-title"),
            ui.input_selectize(
                "scenario_a",
                label=None,
                choices=opts,
                options={"plugins": ["auto_position"]},
            ),
            class_="scenario-selector-field",
        )

    @reactive.effect
    def update_scenario_b_options():
        a = inputs.scenario_a()
        scenario_options = (
            [s for s in current_scenarios if s != a] if a else current_scenarios
        )
        opts = {
            NO_COMPARISON: "None",
            **get_choice_labels("Scenario", scenario_options),
        }

        with reactive.isolate():
            try:
                current = inputs.scenario_b() or NO_COMPARISON
            except SilentException:
                current = NO_COMPARISON

        selected = current if current in opts else NO_COMPARISON
        ui.update_selectize("scenario_b", choices=opts, selected=selected)

    @reactive.calc
    def is_comparison():
        b = scenario_b()
        return b is not None and b != scenario_a()

    @reactive.calc
    def scenario_a():
        return inputs.scenario_a()

    @reactive.calc
    def scenario_b():
        b = inputs.scenario_b()
        if not b or b == NO_COMPARISON:
            return None
        return b

    # Reactives to return for other modules
    @reactive.calc
    def scenario_list():
        """List of selected scenarios (1 or 2)."""
        a = scenario_a()
        b = scenario_b()
        if b is not None and b != a:
            return [a, b]
        return [a]

    # return dict of reactives
    return {
        "is_comparison": is_comparison,
        "scenario_list": scenario_list,
    }
