"""
Ui builders to share between modules
"""

from shiny import ui
from shinywidgets import output_widget
from times_nz_internal_qa.app.helpers.filters import (
    filter_output_ui_list,
)


# pylint:disable = too-many-positional-arguments, too-many-arguments, duplicate-code
def section_block(parameters):
    """
    UI generation for all explorer charts

    parameters are loaded from a dict
    """

    chart_id = parameters["chart_id"]
    title = parameters["section_title"]
    group_options = parameters["group_options"]
    filters = parameters["filters"]

    # generate additional
    sec_id = chart_id.replace("_", "-")  # kebab case for web
    group_input_id = chart_id + "_group"

    # first, the control panel
    chart_control_panel = ui.div(
        # FILTERS
        ui.div(
            ui.tags.h4("Filter:", class_="filter-section-title"),
            ui.input_action_button(
                f"{chart_id}_chart_clear_filters",
                None,  # no text
                icon=ui.tags.i(class_="fa fa-times"),  # font-awesome "X"
                class_="btn btn-sm clear-filters",
                title="Clear all filters",  # hover text
            ),
            class_="filter-header",
        ),
        *filter_output_ui_list(filters),
        # class defn
        class_="chart-control-panel",
    )

    chart_header = ui.div(
        ui.tags.h3(title, id=sec_id),
        ui.div(
            ui.tags.h4("Grouped by:", class_="filter-section-title"),
            ui.input_select(group_input_id, label=None, choices=group_options),
            class_="chart-group",
        ),
        ui.download_button(
            f"{chart_id}_chart_data_download",
            ui.tags.span(ui.tags.i(class_="fa fa-download"), " Download chart data"),
            class_="btn",
        ),
        class_="chart-header",
    )
    # chart UI
    chart_with_title = ui.div(
        chart_header, output_widget(f"{chart_id}_chart"), class_="chart-with-title"
    )

    return ui.div(
        ui.layout_columns(
            chart_control_panel,
            chart_with_title,
            col_widths=(2, 10),
        ),
        class_="chart-section",
    )


def make_explorer_page_ui(sections, id_prefix):
    """
    Creates the explorer page, including navbar, composed of sections
    Each section is a dictionary of input params, and sections is a list of these dicts

    """

    choices = {s["sec_id"]: s["section_title"] for s in sections}
    first_sec_id = sections[0]["sec_id"]

    main = ui.div(
        *[
            ui.panel_conditional(
                f'input.{id_prefix}_nav == "{s["sec_id"]}"',
                section_block(s),
            )
            for s in sections
        ],
        class_="panel-viewport",
    )

    # only open the side bar if it's useful (ie if we have multiple charts)
    if len(choices) > 1:
        nav_open_status = "open"
    else:
        nav_open_status = "closed"

    out_ui = ui.page_fluid(
        ui.layout_sidebar(
            ui.sidebar(
                ui.div(
                    ui.input_radio_buttons(
                        f"{id_prefix}_nav", None, choices=choices, selected=first_sec_id
                    ),
                    class_="nav-cards",
                ),
                open=nav_open_status,
            ),
            main,
        )
    )

    return out_ui


def tab_title(label: str, btn_id: str):
    """Small helper to add an info button to section headers"""
    return ui.tags.span(
        label,
        ui.input_action_button(
            btn_id,
            ui.tags.i(class_="fa fa-question-circle"),
            class_="info-btn",
            title="About this tab",
        ),
    )
