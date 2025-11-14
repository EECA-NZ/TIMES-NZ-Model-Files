"""
In-app data processing methods
These are designed to efficiently build lazy pipelines from raw data
And bundle things into charts using as little memory and as fast as possible

THis should NOT be considered post-processing, as it doesn't do any labelling or anything like that

These are effectively chart aggregation functions, intended to be used dynamically in the app


"""

import io

import pandas as pd
import polars as pl
from times_nz_internal_qa.app.helpers.filters import apply_filters


def show_df_size(df):
    """small helper function to print the mb size of a df"""
    # just used in performance testing
    size = df.estimated_size()
    print(round(size / 1e6, 3), "MB")


def ensure_lazy(x) -> pl.LazyFrame:
    """forces an input to be lazy
    Intended to make frame consistency a bit
        easier to manage when we're swapping types a lot
    """
    if isinstance(x, pl.LazyFrame):
        return x
    if isinstance(x, pl.DataFrame):
        return x.lazy()
    raise TypeError(f"Expected LazyFrame or DataFrame, got {type(x)}")


def complete_periods(
    df: pl.LazyFrame, period_list, category_cols=None, value_col="Value"
) -> pl.LazyFrame:
    """
    Fill in missing periods with explicit zero values for each category combination
    This is the best way to ensure the years are explicit even if we don't use all years
    We probably will for the final ones, though, making this obsolete

    Whatever comes in, everything is forced to be lazy for consistency
    """
    # Create a DataFrame from the complete period list
    periods_lf = pl.DataFrame({"Period": period_list})

    # always lazy
    periods_lf = ensure_lazy(periods_lf)
    df = ensure_lazy(df)

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
    """
    Minor tidying of the base input using Polars
    Include scenario filtering, and lazy output
    """

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


def filter_df_for_variable(
    df: pl.LazyFrame, variable, collect=False
) -> pl.LazyFrame | pl.DataFrame:
    """
    Wrapper: filter for a variable
    Optionally, we can collect the lazyframe now
    We may end up never using this if each table is filtered beforehand
    But it's here for now
    """
    df = df.filter(pl.col("Variable") == variable)

    if collect:
        return df.collect()
    return df


def aggregate_by_group(df: pl.LazyFrame | pl.DataFrame, group_vars: list):
    """
    Short hand for summing a value across groups
    Takes a list of cols to group by
    sums "Value" across these
    works on lazy or not lazy
    """

    df = df.group_by(group_vars).agg(pl.col("Value").sum().alias("Value"))
    # in order
    df = df.select(group_vars + ["Value"])
    # sort
    df = df.sort(group_vars)
    return df


def get_filter_options_from_data(df: pl.DataFrame, filters: dict):
    """
    Returns a dict of possible filter options as a polars df
    Based on the input filter settings dict
    """
    # identify all filter columns
    cols = [d["col"] for d in filters]
    # take only those values in the dataframe
    out = df.select(cols).drop_nulls().unique()
    return out


# @lru_cache(maxsize=16)
def make_chart_data(
    lf: pl.LazyFrame, base_cols, group_col, scen_list, period_range=range(2023, 2051)
) -> dict:
    """
    A cached collection of a pandas df expected to go directly to plotly
    Assumes a lazy polars input lf and various parameter inputs

    We complete the bars by the completed period range to allow display on bars

    Includes several additional parameters for the chart inputs.
    Outputs everything as a dict.
    """
    # combine full list of group columns
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
        print(pdf)
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

    # identify unit
    unit = unit_list[0] if unit_list else None

    # return all components for the chart as a dict
    return {
        "pdf": pdf,
        "unit": unit,
        "period_range": period_range,
        "group_col": group_col,
        "scen_list": scen_list,
    }


def write_polars_to_csv(df):
    """
    We need to encode the buffer with utf-bom
    so that our generated downloads include macrons properly
    """
    # df = df.sort(["Scenario", "Variable", "Period"])
    # make a buffer
    t = io.StringIO()
    # write data to it
    df.write_csv(t)
    # encode utf-8 BOM, including the data
    return b"\xef\xbb\xbf" + t.getvalue().encode("utf-8")


def get_agg_data(
    lf,
    filters,
    inputs,
    group_vars,
):
    """
    Polars filtering and grouping based on user inputs

    This is designed to create data for the chart
    It's lazy - can collect later for chart or for data download


    """
    # apply filters
    lf = apply_filters(lf, filters, inputs)
    # apply group
    lf = aggregate_by_group(lf, group_vars)

    return lf


def to_snake_case(s):
    """
    Return s as snake_case.
    """
    parts = s.replace("-", " ").replace("_", " ").split()
    return "_".join(p.lower() for p in parts)
