"""
Function factories for replicable server functions.
"""

from shiny import reactive, render, ui
from shinywidgets import render_plotly
from times_nz_internal_qa.app.helpers.charts import (
    build_grouped_bar,
    build_grouped_area,
    build_grouped_bar_timeslice,
    build_grouped_line,
    build_empty_figure,
)
from times_nz_internal_qa.app.helpers.data_processing import (
    get_agg_data,
    get_filter_options_from_data,
    make_chart_data,
    to_snake_case,
    write_polars_to_csv,
)
from times_nz_internal_qa.app.helpers.filters import (
    apply_filters,
    register_all_filters_and_clear,
)
from times_nz_internal_qa.utilities.value_mappings import remap_values


def register_download(outputs, out_id, filename, df_reactive):
    """
    Registers the download function to the server, ensuring correct IDs etc
    The reactive df is called and written to an IO, then yielded
    We ensure the namespace of the function matches the ID

    This is robust to some http problems which meant we could not use @outputs(id)
    """

    def handler():
        yield write_polars_to_csv(df_reactive())

    # match the route key
    handler.__name__ = out_id

    # apply decorators in code, not with @ syntax
    decorated = render.download(
        filename=filename,
        media_type="text/csv",
    )(handler)

    outputs(id=out_id)(decorated)


# pylint:disable = too-many-arguments, too-many-positional-arguments, too-many-locals
def register_server_functions_for_explorer(
    chart_parameters_dict: dict,
    df_function,
    scenarios,
    is_comparison,
    inputs,
    outputs,
    session,
):
    """

    Registers all reactive for a single chart within an explorer tab

    This includes the dynamic filters, the filtered data, the chart rendering,
    And the download button

    Most parameters are passed via dictionary and unpacked locally

    Saves rewriting the same reactives over and over.

    Note that only rendered functions, such as the chart and downloadable file,
    require ID setting

    """

    # unpack requirements from input dict

    filters = chart_parameters_dict["filters"]
    chart_id = chart_parameters_dict["chart_id"]
    base_cols = chart_parameters_dict["base_cols"]
    page_id = chart_parameters_dict["page_id"]
    sec_id = chart_parameters_dict["sec_id"]
    section_title = chart_parameters_dict["section_title"]

    # default to grouped bar if there's nothing in the dict
    chart_type = chart_parameters_dict.get("chart_type", "grouped_bar")

    # get reactive to return data following scenario selection
    @reactive.calc
    def _df():
        return df_function(scenarios())

    area_to_bar_id = f"{chart_id}_area_switch_bar"
    area_to_line_id = f"{chart_id}_area_switch_line"
    area_to_single_id = f"{chart_id}_area_switch_single"

    def _show_area_compare_modal():
        ui.modal_show(
            ui.modal(
                ui.tags.h3("Area charts are not available for scenario comparison"),
                ui.p(
                    "Stacked area charts are only supported for one scenario at a "
                    "time. Choose a different chart type, or switch back to a "
                    "single scenario."
                ),
                easy_close=True,
                footer=ui.div(
                    ui.input_action_button(area_to_bar_id, "Switch to Bar"),
                    ui.input_action_button(area_to_line_id, "Switch to Line"),
                    ui.input_action_button(
                        area_to_single_id, "Use One Scenario Only"
                    ),
                    ui.modal_button("Cancel"),
                    class_="d-flex gap-2 justify-content-end",
                ),
            )
        )

    @reactive.effect
    @reactive.event(inputs[area_to_bar_id])
    def _switch_area_to_bar():
        ui.update_radio_buttons(f"{chart_id}_chart_type", selected="bar")
        ui.modal_remove()

    @reactive.effect
    @reactive.event(inputs[area_to_line_id])
    def _switch_area_to_line():
        ui.update_radio_buttons(f"{chart_id}_chart_type", selected="line")
        ui.modal_remove()

    @reactive.effect
    @reactive.event(inputs[area_to_single_id])
    def _switch_area_to_single():
        ui.update_switch("compare_on", value=False)
        ui.update_radio_buttons(f"{chart_id}_chart_type", selected="area")
        ui.modal_remove()

    if chart_type != "timeslice":

        @reactive.effect
        @reactive.event(
            is_comparison,
            getattr(inputs, f"{chart_id}_chart_type"),
            getattr(inputs, f"{page_id}_nav"),
        )
        def _guard_area_compare_mode():
            if getattr(inputs, f"{page_id}_nav")() != sec_id:
                return

            compare_active = is_comparison()
            current_mode = getattr(inputs, f"{chart_id}_chart_type")()
            if compare_active and current_mode == "area":
                _show_area_compare_modal()

    # define filter options for this data based on input filter dict
    @reactive.calc
    def _filter_options():
        return get_filter_options_from_data(_df(), filters)

    # register all filter controls and clear button
    register_all_filters_and_clear(filters, _filter_options, inputs, outputs, session)

    # Apply filters to data dynamically and lazily
    @reactive.calc
    def _df_filtered():
        selected_group = getattr(inputs, f"{chart_id}_group")()
        group_vars = base_cols + [selected_group]
        df = get_agg_data(_df(), filters, inputs, group_vars)
        return df

    @reactive.calc
    def _df_chart_download():
        return apply_filters(_df(), filters, inputs)

    # Create chart data
    @reactive.calc
    def _chart_df():
        # touch the nav input so hidden panels still re-render after selection changes
        _ = getattr(inputs, f"{page_id}_nav")()
        selected_group = getattr(inputs, f"{chart_id}_group")()

        df_filtered = _df_filtered()

        # FIX #3 – prevent empty-data crash
        if df_filtered is None or df_filtered.height == 0:
            return None  # chart renderers will handle this

        return make_chart_data(
            df_filtered,
            base_cols,
            selected_group,
            remap_values("Scenario", scenarios()),
        )

    # DRAW CHARTS
    @outputs(id=f"{chart_id}_chart")
    @render_plotly
    def _chart_unified():
        params = _chart_df()

        # Early exit 1: no chart data at all
        if not params or params["pdf"].empty:
            return build_empty_figure("No data available")

        pdf = params["pdf"]

        # Early exit 2: no non-zero values = infeasible or meaningless for line charts
        if pdf["Value"].sum() == 0:
            return build_empty_figure("No meaningful values to plot")

        # Handle chart types
        if chart_type == "timeslice":
            chart = build_grouped_bar_timeslice(
                pdf=params["pdf"],
                unit=params["unit"],
                group_col=params["group_col"],
                scen_list=params["scen_list"],
            )

        else:
            mode = getattr(inputs, f"{chart_id}_chart_type")()

            if is_comparison() and mode == "area":
                return build_empty_figure(
                    "Area charts are not available when comparing scenarios"
                )

            if mode == "bar":
                chart = build_grouped_bar(**params)
            elif mode == "line":
                chart = build_grouped_line(**params)
            elif mode == "area":
                chart = build_grouped_area(**params)
            else:
                chart = build_empty_figure("No chart")

        chart.update_layout(autosize=True)
        return chart

    # Setup downloads
    chart_download_function_name = f"{chart_id}_chart_data_download"
    chart_download_filename = f"times_nz_{to_snake_case(section_title)}_chart_data.csv"
    register_download(
        outputs,
        chart_download_function_name,
        chart_download_filename,
        _df_chart_download,
    )

    unfiltered_download_function_name = f"{chart_id}_unfiltered_data_download"
    unfiltered_download_filename = (
        f"times_nz_{to_snake_case(section_title)}_unfiltered_data.csv"
    )
    register_download(
        outputs,
        unfiltered_download_function_name,
        unfiltered_download_filename,
        _df,
    )
