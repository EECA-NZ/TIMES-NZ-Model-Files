"""
Function factories for replicable server functions.
"""

from collections import OrderedDict

import polars as pl
from shiny import reactive, render
from shinywidgets import render_plotly
from times_nz_internal_qa.app.helpers.charts import (
    DEFAULT_LAYOUT_OPTIONS,
    TIMESLICE_LAYOUT_OPTIONS,
    build_empty_figure,
    build_grouped_area,
    build_grouped_bar,
    build_grouped_bar_timeslice,
    build_grouped_line,
)
from times_nz_internal_qa.app.helpers.data_processing import (
    TOTAL_GROUP_COLUMN,
    TOTAL_GROUP_OPTION,
    TOTAL_GROUP_VALUE,
    get_agg_data,
    get_filter_options_from_data,
    make_chart_data,
    make_table_data,
    to_snake_case,
    write_polars_to_csv,
)
from times_nz_internal_qa.app.helpers.filters import (
    register_all_filters_and_clear,
)
from times_nz_internal_qa.utilities.value_mappings import remap_values


def _selection_key(value):
    if value is None:
        return ()
    if isinstance(value, (list, tuple, set)):
        return tuple(sorted("" if v is None else str(v) for v in value))
    return ("",) if value == "" else (str(value),)


def _effective_group_column(selected_group):
    """Return the real or synthetic column used to build chart series."""
    if selected_group == TOTAL_GROUP_OPTION:
        return TOTAL_GROUP_COLUMN
    return selected_group


# pylint:disable = too-many-arguments
def _build_cached_chart_data(
    *,
    cache: OrderedDict,
    cache_key,
    df_filtered,
    base_cols,
    selected_group,
    scenarios,
    chart_type: str,
    cache_limit: int,
):
    if cache_key in cache:
        cache.move_to_end(cache_key)
        return cache[cache_key]

    if df_filtered is None or df_filtered.height == 0:
        cache[cache_key] = None
        return None

    chart_data = make_chart_data(
        df_filtered,
        base_cols,
        selected_group,
        scenarios,
        complete_missing_periods=chart_type != "timeslice",
    )
    cache[cache_key] = chart_data
    cache.move_to_end(cache_key)
    if len(cache) > cache_limit:
        cache.popitem(last=False)
    return chart_data


def _build_chart(params, chart_type, chart_id, inputs, is_comparison):
    chart = None

    if not params or params["pdf"].empty:
        chart = build_empty_figure("No data available")
    elif params["pdf"]["Value"].sum() == 0:
        chart = build_empty_figure("No meaningful values to plot")
    elif chart_type == "timeslice":
        chart = build_grouped_bar_timeslice(
            pdf=params["pdf"],
            unit=params["unit"],
            group_col=params["group_col"],
            scen_list=params["scen_list"],
        )
    else:
        mode = getattr(inputs, f"{chart_id}_chart_type")()
        if is_comparison() and mode == "area":
            chart = build_empty_figure(
                "Area charts are not available when comparing scenarios"
            )
        elif mode == "bar":
            chart = build_grouped_bar(**params)
        elif mode == "line":
            chart = build_grouped_line(**params)
        elif mode == "area":
            chart = build_grouped_area(**params)
        else:
            chart = build_empty_figure("No chart")

    return chart


def _register_explorer_downloads(
    outputs, chart_id, section_title, chart_df, raw_df, *, scenarios
):
    """
    Registers two separate downloads with IDs to give options in the dropdowns
    defines the data functions used to render, and a few components to
    define the filename based on current user settings
    """

    def download_filename(data_description):
        selected_scenarios = scenarios()
        main_scenario = selected_scenarios[0] if selected_scenarios else "scenario"
        comp_scenario = (
            f"and-{to_snake_case(selected_scenarios[1])}-"
            if len(selected_scenarios) == 2
            else ""
        )
        return (
            f"{to_snake_case(str(main_scenario))}-"
            f"{comp_scenario}"
            f"{to_snake_case(section_title)}-"
            f"{data_description}.csv"
        )

    chart_download_function_name = f"{chart_id}_chart_data_download"
    register_download(
        outputs,
        chart_download_function_name,
        lambda: download_filename("chart_data"),
        chart_df,
    )

    unfiltered_download_function_name = f"{chart_id}_unfiltered_data_download"
    register_download(
        outputs,
        unfiltered_download_function_name,
        lambda: download_filename("raw_data"),
        raw_df,
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
    chart_cache: OrderedDict[tuple, dict | None] = OrderedDict()
    chart_cache_limit = 24

    # get reactive to return data following scenario selection
    @reactive.calc
    def _df():
        return df_function(scenarios())

    @reactive.calc
    def _is_active_section():
        return getattr(inputs, f"{page_id}_nav")() == sec_id

    @reactive.calc
    def _chart_cache_key():
        selected_group = getattr(inputs, f"{chart_id}_group")()
        scenario_key = tuple(remap_values("Scenario", scenarios()))
        filter_key = tuple(
            (
                f["col"],
                _selection_key(
                    getattr(inputs, f'filter_{f["chart_id"]}_{f["id"]}_selected')()
                ),
            )
            for f in filters
        )
        return (chart_id, selected_group, scenario_key, filter_key)

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
        is_total = selected_group == TOTAL_GROUP_OPTION
        group_vars = base_cols if is_total else base_cols + [selected_group]
        df = get_agg_data(_df(), filters, inputs, group_vars)
        if is_total:
            df = df.with_columns(pl.lit(TOTAL_GROUP_VALUE).alias(TOTAL_GROUP_COLUMN))
        return df

    # Create chart data
    @reactive.calc
    def _chart_df():
        if not _is_active_section():
            return None

        selected_group = _effective_group_column(getattr(inputs, f"{chart_id}_group")())
        cache_key = _chart_cache_key()
        return _build_cached_chart_data(
            cache=chart_cache,
            cache_key=cache_key,
            df_filtered=_df_filtered(),
            base_cols=base_cols,
            selected_group=selected_group,
            scenarios=remap_values("Scenario", scenarios()),
            chart_type=chart_type,
            cache_limit=chart_cache_limit,
        )

    # DRAW CHARTS
    @outputs(id=f"{chart_id}_chart")
    @render_plotly
    def _chart_unified():
        if not _is_active_section():
            return build_empty_figure("")

        chart = _build_chart(_chart_df(), chart_type, chart_id, inputs, is_comparison)
        return chart

    @outputs(id=f"{chart_id}_table")
    @render.data_frame
    def _table_unified():
        if not _is_active_section():
            return None

        selected_group = _effective_group_column(getattr(inputs, f"{chart_id}_group")())
        table_df = make_table_data(_df_filtered(), selected_group)
        height = (
            TIMESLICE_LAYOUT_OPTIONS.height
            if chart_type == "timeslice"
            else DEFAULT_LAYOUT_OPTIONS.height
        )
        return render.DataGrid(
            table_df,
            width="100%",
            height=f"{height}px",
            summary=True,
            filters=False,
            editable=False,
            selection_mode="none",
            styles={"style": {"white-space": "nowrap"}},
        )

    _register_explorer_downloads(
        outputs,
        chart_id,
        section_title,
        # data function for the "filtered" download
        _df_filtered,
        # data function for the "unfiltered" download
        _df,
        scenarios=scenarios,
    )
