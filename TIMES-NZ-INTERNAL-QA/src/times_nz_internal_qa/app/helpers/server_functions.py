"""
Function factories for replicable server functions

Mostly because we were repeating methods a lot
"""

import altair as alt
import pandas as pd
from shiny import reactive, render
from shinywidgets import render_altair
from times_nz_internal_qa.app.helpers.charts import (
    build_grouped_bar,
    build_grouped_bar_timeslice,
    build_grouped_line,
)
from times_nz_internal_qa.app.helpers.data_processing import (
    get_agg_data,
    get_filter_options_from_data,
    make_chart_data,
    to_snake_case,
    write_polars_to_csv,
)
from times_nz_internal_qa.app.helpers.filters import (
    register_all_filters_and_clear,
)


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
    chart_parameters_dict: dict, df_function, scenarios, inputs, outputs, session
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
    section_title = chart_parameters_dict["section_title"]

    # default to grouped bar if there's nothing in the dict
    chart_type = chart_parameters_dict.get("chart_type", "grouped_bar")

    # get reactive to return data following scenario selection
    @reactive.calc
    def _df():
        return df_function(scenarios())

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

    # Create chart data
    @reactive.calc
    def _chart_df():
        # if using altair, must touch the nav input to ensure rerendering
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
            scenarios(),
        )

    toggle_mode = reactive.Value("bar")  # default

    @reactive.effect
    @reactive.event(getattr(inputs, f"{chart_id}_show_bar"))
    def _set_to_bar():
        toggle_mode.set("bar")

    @reactive.effect
    @reactive.event(getattr(inputs, f"{chart_id}_show_line"))
    def _set_to_line():
        toggle_mode.set("line")

    # DRAW CHARTS
    @outputs(id=f"{chart_id}_chart")
    @render_altair
    def _chart_unified():
        params = _chart_df()

        # Early exit 1: no chart data at all
        if not params or params["pdf"].empty:
            return alt.Chart(pd.DataFrame({"x": [], "y": []})).mark_text(
                text="No data available"
            )

        pdf = params["pdf"]

        # Early exit 2: no non-zero values → infeasible or meaningless for line charts
        if pdf["Value"].sum() == 0:
            return alt.Chart(pd.DataFrame({"x": [], "y": []})).mark_text(
                text="No meaningful values to plot"
            )

        # Handle chart types
        if chart_type == "timeslice":
            # unpack the params - we don't use period_range so just send everything else
            return build_grouped_bar_timeslice(
                pdf=params["pdf"],
                unit=params["unit"],
                group_col=params["group_col"],
                scen_list=params["scen_list"],
            )

        mode = toggle_mode()

        if mode == "bar":
            return build_grouped_bar(**params)

        if mode == "line":
            return build_grouped_line(**params)

        return alt.Chart(pd.DataFrame({"x": [], "y": []})).mark_text(text="No chart")

    # Setup downloads
    download_function_name = f"{chart_id}_chart_data_download"
    download_filename = f"times_nz_{to_snake_case(section_title)}.csv"
    register_download(outputs, download_function_name, download_filename, _df)
