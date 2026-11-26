"""Validate prepared rows and compare them without aggregating or completing them."""

import math

import pandas as pd

from qa_times_nz import report_inputs


# pylint: disable-next=too-many-arguments
def read_metric(selected, dataset, group, unit, filters, *, annual=True):
    """Validate and select supplied rows without aggregating or completing them."""
    relative = f"summaries/{dataset}.csv"
    frame = report_inputs.load_summary(selected, relative)
    keys = ([group] if group else []) + (["Period"] if annual else []) + ["Unit"]
    if frame is None:
        return pd.DataFrame(
            {
                key: pd.Series(dtype="int64" if key == "Period" else "object")
                for key in keys
            }
        ).assign(Value=pd.Series(dtype="float64"))
    required = {*keys, *filters, "Value"}
    if not required <= set(frame):
        raise ValueError(
            f"Missing metric fields in {relative}: {sorted(required - set(frame))}"
        )
    for column, value in filters.items():
        if frame[column].isna().any() or frame[column].eq("").any():
            raise ValueError(f"Missing {column} classification in {relative}")
        frame = frame.loc[frame[column].eq(value)]
    if not frame.Unit.eq(unit).all():
        raise ValueError(f"Expected {relative} in {unit}")
    if frame[keys].isna().any().any() or frame[keys].eq("").any().any():
        raise ValueError(f"Missing metric keys or classifications in {relative}")
    if annual:
        years = pd.to_numeric(frame.Period, errors="raise")
        if years.isna().any() or years.mod(1).ne(0).any():
            raise ValueError(f"Expected integer annual periods in {relative}")
        frame = frame.assign(Period=years.astype("int64"))
    elif not frame.empty and (len(frame) != 1 or frame.Value.isna().any()):
        raise ValueError("Expected one finite objective value in NZDb")
    if frame.duplicated(keys).any():
        raise ValueError(f"Duplicate metric keys in {relative}")
    return frame[[*keys, "Value"]].reset_index(drop=True)


def within_tolerance(baseline, candidate, tolerance):
    """Compare finite values relative to baseline; zero matches only zero."""
    return (
        math.isfinite(baseline)
        and math.isfinite(candidate)
        and abs(candidate - baseline) <= abs(baseline) * tolerance
    )


def period_comparison(frames, group, tolerance, *, annual=True):
    """Outer-join supplied keys; categories absent from a reported period count as zero."""
    keys = ([group] if group else []) + (["Period"] if annual else []) + ["Unit"]
    compared = (
        frames[0][[*keys, "Value"]]
        .merge(
            frames[1][[*keys, "Value"]],
            on=keys,
            how="outer",
            suffixes=("_baseline", "_candidate"),
            validate="one_to_one",
            indicator=True,
        )
        .sort_values(keys)
        .reset_index(drop=True)
    )
    if annual:
        # A row absent from a scenario that reports the period is a true zero;
        # an explicit null stays unknown.
        for side, absent, frame in (
            ("baseline", "right_only", frames[0]),
            ("candidate", "left_only", frames[1]),
        ):
            blank = compared["_merge"].eq(absent) & compared.Period.isin(frame.Period)
            compared.loc[blank, f"Value_{side}"] = 0.0
    compared = compared.drop(columns="_merge")
    compared["Difference"] = compared.Value_candidate - compared.Value_baseline
    compared["DifferenceUnit"] = compared.Unit.replace({"%": "percentage points"})
    compared["PercentDifference"] = (
        compared.Difference
        / compared.Value_baseline.mask(compared.Value_baseline.eq(0))
        * 100
    )
    compared["ExceedsTolerance"] = pd.array(
        [
            (
                not within_tolerance(row.Value_baseline, row.Value_candidate, tolerance)
                if annual
                and pd.notna(row.Value_baseline)
                and pd.notna(row.Value_candidate)
                else pd.NA
            )
            for row in compared.itertuples()
        ],
        dtype="boolean",
    )
    return compared


def different_period_spans(compared):
    """Yield periods over tolerance, bounded by midpoints to neighbouring periods."""
    periods = sorted(compared.Period)
    for index, period in enumerate(periods):
        if not compared.ExceedsTolerance[compared.Period.eq(period)].any():
            continue
        if len(periods) == 1:
            yield period - 0.5, period + 0.5
            continue
        left = (periods[index - 1] + period) / 2 if index else period
        right = (
            (period + periods[index + 1]) / 2 if index + 1 < len(periods) else period
        )
        yield left, right
