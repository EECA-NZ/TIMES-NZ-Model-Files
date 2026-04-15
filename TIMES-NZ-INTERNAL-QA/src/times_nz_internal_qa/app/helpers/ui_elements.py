"""
Ui builders to share between modules
"""

from shiny import ui
from shinywidgets import output_widget
from times_nz_internal_qa.app.helpers.charts import TIMESLICE_OUTPUT_HEIGHT
from times_nz_internal_qa.app.helpers.filters import (
    filter_output_ui_list,
    identifier_to_title_case,
)


def chart_download_dropdown(chart_id):
    """Download menu shared by explorer charts."""
    menu_button_id = f"{chart_id}_download_menu_btn"

    return ui.div(
        ui.tags.button(
            ui.tags.i(class_="fa fa-download"),
            " Download data ",
            type="button",
            id=menu_button_id,
            class_="btn chart-download-btn dropdown-toggle",
            **{"data-bs-toggle": "dropdown", "aria-expanded": "false"},
        ),
        ui.tags.ul(
            ui.tags.li(
                ui.download_link(
                    f"{chart_id}_chart_data_download",
                    "Download chart data",
                    class_="dropdown-item",
                )
            ),
            ui.tags.li(
                ui.download_link(
                    f"{chart_id}_unfiltered_data_download",
                    "Download unfiltered data",
                    class_="dropdown-item",
                )
            ),
            class_="dropdown-menu dropdown-menu-end",
            **{"aria-labelledby": menu_button_id},
        ),
        class_="btn-group chart-download-group",
    )


def chart_output_height(parameters):
    """Return a fixed output height so widget wrappers don't enter fill layout."""
    if parameters.get("chart_type") == "timeslice":
        return TIMESLICE_OUTPUT_HEIGHT
    return "560px"


def tab_page_info_icon(btn_id: str):
    """Clickable help icon shown beside the page-level section selector."""
    return ui.input_action_button(
        btn_id,
        ui.TagList(
            ui.tags.i(class_="fa fa-question-circle"),
            " About this tab",
        ),
        class_="btn tab-page-info-btn",
        title="About this tab",
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
    if isinstance(group_options, list):
        group_options = {
            option: identifier_to_title_case(option) for option in group_options
        }
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
                label="Clear",  # None = no text
                icon=ui.tags.i(class_="fa fa-times"),  # font-awesome eraser
                class_="btn btn-sm clear-filters",
                title="Clear all filters",  # hover text
            ),
            class_="filter-header",
        ),
        *filter_output_ui_list(filters),
        # class defn
        class_="chart-control-panel",
    )

    # Build toggle block only when charts support it
    toggle_block = None
    if parameters.get("chart_type") != "timeslice":
        toggle_block = ui.div(
            ui.tags.h4("Chart type:", class_="filter-section-title"),
            ui.div(
                ui.input_radio_buttons(
                    f"{chart_id}_chart_type",
                    label=None,
                    choices={"bar": "Bar", "line": "Line", "area": "Area"},
                    selected="bar",
                    inline=True,
                    width="auto",
                ),
                class_="chart-toggle-bar",
            ),
            class_="chart-toggle-header",
        )

    chart_header = ui.div(
        # Line 1: title on its own
        ui.tags.h3(title, id=sec_id, class_="chart-title"),
        # Line 2: left (group + toggles) and right (download)
        ui.div(
            ui.div(
                # left block: group selector + toggle buttons
                ui.div(
                    ui.tags.h4("Grouped by:", class_="filter-section-title"),
                    ui.input_selectize(
                        group_input_id,
                        label=None,
                        multiple=False,
                        choices=group_options,
                        options={"plugins": ["auto_position"]},
                    ),
                    class_="chart-header-group",
                ),
                toggle_block,
                class_="chart-header-left",
            ),
            # right block: download dropdown
            chart_download_dropdown(chart_id),
            class_="chart-header-row",
        ),
        class_="chart-header",
    )

    chart_columns = ui.layout_columns(
        ui.div(
            output_widget(f"{chart_id}_chart", height=chart_output_height(parameters)),
            class_="chart-container chart-body-card",
        ),
        col_widths=(12,),
        class_="chart-single",
    )

    chart_with_title = ui.div(
        ui.div(chart_header, class_="chart-header-card"),
        chart_columns,  # <-- the selected layout
        class_="chart-with-title",
    )

    return ui.div(
        ui.layout_columns(
            chart_control_panel,
            chart_with_title,
            col_widths=(3, 9),
        ),
        class_="chart-section",
    )


def make_explorer_page_ui(sections, id_prefix, page_info_button_id=None):
    """
    Creates the explorer page, including a 'second tier' horizontal navbar
    for subsections. Each section is a dictionary of input params, and
    sections are a list of these dicts.
    """

    # Map sec_id -> label
    choices = {s["sec_id"]: s["section_title"] for s in sections}
    first_sec_id = sections[0]["sec_id"]

    # The main content area: only one section visible at a time
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

    # Horizontal second-level nav bar
    nav_bar = ui.div(
        ui.div(
            ui.input_radio_buttons(
                f"{id_prefix}_nav",
                None,
                choices=choices,
                selected=first_sec_id,
                inline=True,  # <- makes choices render horizontally
            ),
            class_="secondary-nav-bar nav-cards",
        ),
        tab_page_info_icon(page_info_button_id) if page_info_button_id else None,
        class_="tab-page-toolbar",
    )

    out_ui = ui.page_fluid(
        # [horizontal nav bar]
        nav_bar,
        # [section content (which itself can have a sidebar+main)]
        main,
    )

    return out_ui
