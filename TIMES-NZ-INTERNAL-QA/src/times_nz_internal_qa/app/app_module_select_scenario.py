"""
Server and UI functions for scenario selection
For now, the target is to just provide a main dropdown list,
    then a secondary, optional list for comparisons
"""

from shiny import reactive, render, ui
from times_nz_internal_qa.config import current_scenarios


# pylint:disable = unused-argument
def scenario_select_server(inputs, outputs, session):
    """Server processing for currently selected scenario(s)"""

    @reactive.calc
    def selected_scenario_a():
        return inputs.scenario_a()

    @render.ui
    def select_scenario_a_ui():
        opts = current_scenarios
        return ui.input_selectize("scenario_a", "Main scenario", choices=opts)

    @render.ui
    def select_scenario_b_ui():
        if not inputs.compare_on():
            return None  # hide when toggle is off
        # a = current selected main scenario
        a = inputs.scenario_a()
        opts = [s for s in current_scenarios if s != a] if a else current_scenarios
        return ui.input_selectize("scenario_b", "　", choices=opts)

    @reactive.calc
    def is_comparison():
        return inputs.compare_on()

    @reactive.calc
    def scenario_a():
        return inputs.scenario_a()

    @reactive.calc
    def scenario_b():
        b = inputs.scenario_b()
        if not b:
            return None
        return b

    # Reactives to return for other modules
    @reactive.calc
    def scenario_list():
        """List of selected scenarios (1 or 2)."""
        a = inputs.scenario_a()

        if is_comparison():
            b = inputs.scenario_b()
            # robustness check - never output the same scenario twice.
            # shouldn't really be possible, just a safeguard.
            if a == b:
                return [a]
            # we are comparing scenarios so put out both
            return [a] + [b]
        # we aren't comparing anything
        return [a]

    # return dict of reactives
    return {
        "is_comparison": is_comparison,
        "scenario_list": scenario_list,
    }
