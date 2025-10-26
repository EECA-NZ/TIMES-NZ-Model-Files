"""
Data formatting, server and ui functions for electricity generation data

"""

import io

import pandas as pd

# from functools import lru_cache
import polars as pl
from shiny import reactive, render
from shinywidgets import render_plotly
from times_nz_internal_qa.app.helpers.charts import (
    build_grouped_bar_better,
)
from times_nz_internal_qa.app.helpers.filters import (
    apply_filters,
    create_filter_dict,
    register_filter_from_factory,
)
from times_nz_internal_qa.app.helpers.ui_elements import make_explorer_page_ui
from times_nz_internal_qa.utilities.filepaths import FINAL_DATA

# CONSTANTS  ------------------------------------------------------------------------------


# TEMP

# ID_PREFIX is used to ensure some ui and server elements link correctly
ID_PREFIX = "elec"

# define base columns that we must always group by
ele_base_cols = [
    "Scenario",
    "Variable",
    "Period",
    "Unit",
]

# parameters to optionally group data by
# Note: we can add Fuel for the fuel inputs
ele_core_group_options = [
    "TechnologyGroup",
    "Technology",
    "Region",
    "PlantName",
]

# configure filter options
core_filters = [
    {"col": "TechnologyGroup", "label": "Technology Group"},
    {"col": "Technology"},
    {"col": "Region"},
    {"col": "PlantName", "label": "Plant"},
]

ele_gen_filters = create_filter_dict("ele_gen", core_filters)
ele_cap_filters = create_filter_dict("ele_cap", core_filters)
ele_use_filters = create_filter_dict("ele_use", core_filters + [{"col": "Fuel"}])

ele_all_group_options = ele_base_cols + ele_core_group_options + ["Fuel"]


# PROCESS DATA


# DATA PROCESSING FOR CHARTS

# THESE WILL MOVE TO SEPARATE FUNCTION


def show_df_size(df):
    """small helper function to print the mb size of a df"""

    size = df.estimated_size()
    print(round(size / 1e6, 3), "MB")


def complete_periods(
    df: pl.LazyFrame, period_list, category_cols=None, value_col="Value"
) -> pl.LazyFrame:
    """
    Fill in missing periods with explicit zero values for each category combination
    """
    # Create a DataFrame from the complete period list
    periods_lf = pl.DataFrame({"Period": period_list}).lazy()

    if category_cols:
        # Unique category combinations
        categories = df.select(category_cols).unique()

        # Cross join to create all combinations of Period × categories
        template = periods_lf.join(categories, how="cross")

        # Left join with original data
        result = template.join(df, on=["Period"] + category_cols, how="left")
    else:
        # Just merge periods with original data
        result = periods_lf.join(df, on="Period", how="left")

    # Fill missing values with 0 in the value column
    result = result.with_columns(pl.col(value_col).fill_null(0))

    return result


def read_data_pl(file_location, scenarios) -> pl.LazyFrame:
    """Minor tidying of the base input using Polars"""

    # eager read; for lazy, use pl.scan_parquet
    df = (
        pl.scan_parquet(file_location)
        .fill_null("-")
        .with_columns(pl.col("Period").cast(pl.Int64))
        # filter here? we reread when the scenario filter changes.
        # this keeps excess scenarios out of memory
        .filter(pl.col("Scenario").is_in(scenarios))
    )

    return df


def filter_df_for_variable_pl(df, variable) -> pl.LazyFrame:
    """
    Optionally, filter for a variable
    We may end up never using this if each table is filtered beforehand
    But it's here for now
    """
    return df.filter(pl.col("Variable") == variable)


def aggregate_by_group(df, group_vars):
    """
    Short hand for summing a value across groups
    Takes a list of cols to group by
    sums "Value" across these
    works on lazy or not lazy
    """
    return df.group_by(group_vars).agg(pl.col("Value").sum().alias("Value"))


# @lru_cache(maxsize=16)
def make_chart_pdf(lf, base_cols, group_col, scen_list, period_range=range(2023, 2051)):
    """
    A cached collection of a pandas df
    expected to go directly to plotly
    Assumes a lazy polars input

    lf is the lazy input frame
    We complete the bars by the completed period range to allow display

    returns the output and the unit as a separate item
    """

    all_group_cols = base_cols + [group_col]

    # complete periods
    lf = complete_periods(
        # this ensures that we have 0 entries for all years
        # if the data doesn't include those years.
        # forces x-axis consistency among our charts.
        lf,
        period_list=period_range,
        category_cols=[c for c in all_group_cols if c != "Period"],
    )

    # we might do other things here like adding totals, later

    # collect as pandas df
    pdf = lf.collect().to_pandas(use_pyarrow_extension_array=True)

    # unit defined in the data itself

    unit_list = pdf["Unit"].unique().tolist()
    # ensure only one (otherwise the chart is wrong)
    if len(unit_list) > 1:
        raise ValueError(f"Multiple units found in data: {unit_list}")

    # Normalise types and ordering

    # Normalize dtypes and ordering once
    period_order = [str(p) for p in period_range]
    pdf["Period"] = pd.Categorical(
        pdf["Period"].astype(str), categories=period_order, ordered=True
    )
    pdf[group_col] = pdf[group_col].astype(str)

    pdf["Scenario"] = pd.Categorical(
        pdf["Scenario"], categories=scen_list, ordered=True
    )

    # return the data and the unit separately

    unit = unit_list[0]

    return pdf, unit, period_range, group_col, scen_list


# ELECTRICITY SPECIFIC HANDLING


# @lru_cache(maxsize=4)
def get_ele_var_data(df, variable):
    """
    Return the unfiltered ele gen data for a specific base
    Won't rerun unless scenarios change. Holds in memory
    Caches results
    """

    df = filter_df_for_variable_pl(df, variable)

    return df.collect()


def get_agg_ele_data(df, filters, inputs, group_vars) -> pl.LazyFrame:
    """
    Polars filtering and grouping based on inputs
    This is the version for the chart.
    It's lazy - can collect later for chart or for data download
    """
    lf = df.lazy()

    # apply filters
    lf = apply_filters(lf, filters, inputs)
    # apply group
    lf = aggregate_by_group(lf, group_vars)

    return lf


# pylint:disable = too-many-locals, unused-argument
def elec_server(inputs, outputs, session, selected_scens):
    """
    server functions for electricity
    """

    # base data - filtered for scenario. Lazy.
    @reactive.calc
    def base_df():
        d = read_data_pl(
            FINAL_DATA / "elec_generation.parquet", selected_scens["scenario_list"]()
        )
        d = aggregate_by_group(d, ele_all_group_options)
        return d

    # get each table for each chart
    @reactive.calc
    def ele_gen_df():
        return get_ele_var_data(base_df(), "Electricity generation")

    @reactive.calc
    def ele_cap_df():
        return get_ele_var_data(base_df(), "Electricity generation capacity")

    @reactive.calc
    def ele_use_df():
        return get_ele_var_data(base_df(), "Electricity fuel use")

    # REGISTER ALL FILTER FUNCTIONS FOR UI
    # Currently we do this once per chart
    for fs in ele_gen_filters:
        register_filter_from_factory(
            fs, ele_gen_df, ele_gen_filters, inputs, outputs, session
        )

    for fs in ele_cap_filters:
        register_filter_from_factory(
            fs, ele_cap_df, ele_cap_filters, inputs, outputs, session
        )

    for fs in ele_use_filters:
        register_filter_from_factory(
            fs, ele_use_df, ele_use_filters, inputs, outputs, session
        )

    # APPLY FILTERS TO DATA DYNAMICALLY AND LAZILY
    @reactive.calc
    def ele_cap_df_filtered():
        group_vars = ele_base_cols + [inputs.ele_cap_group()]
        df = get_agg_ele_data(ele_cap_df(), ele_cap_filters, inputs, group_vars)
        return df

    @reactive.calc
    def ele_use_df_filtered():
        group_vars = ele_base_cols + [inputs.ele_use_group()]
        df = get_agg_ele_data(ele_use_df(), ele_use_filters, inputs, group_vars)
        return df

    @reactive.calc
    def ele_gen_df_filtered():
        group_vars = ele_base_cols + [inputs.ele_gen_group()]
        df = get_agg_ele_data(ele_gen_df(), ele_gen_filters, inputs, group_vars)

        return df

    # CREATE CHART OUTPUTS (only ones that we're actually collecting)
    @reactive.calc
    def ele_gen_chart_df():
        pdf, unit, period_range, group_col, scen_list = make_chart_pdf(
            ele_gen_df_filtered(),
            ele_base_cols,
            inputs.ele_gen_group(),
            selected_scens["scenario_list"](),
        )
        print("I HAVE MADE GEN DATA")
        return pdf, unit, period_range, group_col, scen_list

    @reactive.calc
    def ele_cap_chart_df():
        pdf, unit, period_range, group_col, scen_list = make_chart_pdf(
            ele_cap_df_filtered(),
            ele_base_cols,
            inputs.ele_cap_group(),
            selected_scens["scenario_list"](),
        )
        print("I HAVE MADE CAP DATA")
        return pdf, unit, period_range, group_col, scen_list

    @reactive.calc
    def ele_use_chart_df():
        pdf, unit, period_range, group_col, scen_list = make_chart_pdf(
            ele_use_df_filtered(),
            ele_base_cols,
            inputs.ele_use_group(),
            selected_scens["scenario_list"](),
        )
        print("I HAVE MADE USE DATA")
        return pdf, unit, period_range, group_col, scen_list

    # CHARTS
    @render_plotly
    def ele_gen_chart():
        print("I AM BUILDING THE GEN CHART")
        pdf, unit, period_range, group_col, scen_list = ele_gen_chart_df()
        return build_grouped_bar_better(pdf, unit, period_range, group_col, scen_list)

    @render_plotly
    def ele_cap_chart():
        print("I AM BUILDING THE CAP CHART")
        pdf, unit, period_range, group_col, scen_list = ele_cap_chart_df()
        return build_grouped_bar_better(pdf, unit, period_range, group_col, scen_list)

    @render_plotly
    def ele_use_chart():
        print("I AM BUILDING THE USE CHART")
        pdf, unit, period_range, group_col, scen_list = ele_use_chart_df()
        return build_grouped_bar_better(pdf, unit, period_range, group_col, scen_list)

    # CSV downloads (not yet functionalised sorry)
    @render.download(filename="ele_gen_chart_data_download.csv", media_type="text/csv")
    def ele_gen_chart_data_download():
        buf = io.StringIO()
        ele_gen_df_filtered().collect().to_csv(buf, index=False)
        yield buf.getvalue()

    @render.download(filename="ele_use_chart_data_download.csv", media_type="text/csv")
    def ele_use_chart_data_download():
        buf = io.StringIO()
        ele_use_df_filtered().collect().to_csv(buf, index=False)
        yield buf.getvalue()

    @render.download(filename="ele_cap_chart_data_download.csv", media_type="text/csv")
    def ele_cap_chart_data_download():
        buf = io.StringIO()
        ele_cap_df_filtered().collect().to_csv(buf, index=False)
        yield buf.getvalue()


# UI ------------------------------------------------


sections = [
    (
        "elec-gen",
        "Electricity generation",
        "ele_gen_group",
        ele_core_group_options,
        ele_gen_filters,
        "ele_gen_chart",
    ),
    (
        "elec-use",
        "Fuel used for generation",
        "ele_use_group",
        ele_core_group_options + ["Fuel"],
        ele_use_filters,
        "ele_use_chart",
    ),
    (
        "elec-cap",
        "Generation capacity",
        "ele_cap_group",
        ele_core_group_options,
        ele_cap_filters,
        "ele_cap_chart",
    ),
]

elec_ui = make_explorer_page_ui(sections, ID_PREFIX)
