"""Compare and draw one year of timeslice values as four seasonal panels."""

import matplotlib as mpl
import pandas as pd
from matplotlib.figure import Figure

from qa_times_nz import report_inputs
from qa_times_nz.report.charts import SCENARIO_COLOURS, embed_svg, unavailable_message
from qa_times_nz.report.compare import period_comparison

SLICE_YEAR = 2050
SEASONS = ["Summer", "Autumn", "Winter", "Spring"]
DETAIL = [
    "Variable",
    "Technology",
    "TimeSlice",
    "TimeSliceOrder",
    "Season",
    "TimeSliceDayTime",
]


def read_slice_metric(selected, dataset, unit):
    """Read the slice year as annual rows, each slice labelled in a 'Series' column.

    This lets the usual year comparison and table handle slices unchanged.
    """
    columns = ["Series", "Period", "Unit", "Value", *DETAIL]
    frame = report_inputs.load_summary(selected, f"summaries/{dataset}.csv")
    if frame is not None:
        required = {"Period", "Unit", "Value", "TimeSliceLongLabel", *DETAIL}
        if not required <= set(frame):
            raise ValueError(f"Missing slice fields in {dataset}")
        years = pd.to_numeric(frame.Period, errors="raise")
        frame = frame.loc[frame.Unit.eq(unit) & years.eq(SLICE_YEAR)].copy()
    if frame is None or frame.empty:
        empty = pd.DataFrame({column: pd.Series(dtype="object") for column in columns})
        return empty.astype({"Period": "int64", "Value": "float64"})
    frame["Period"] = SLICE_YEAR
    frame["TimeSliceOrder"] = pd.to_numeric(frame.TimeSliceOrder, errors="raise")
    frame["Series"] = (
        frame.Technology + ": " + frame.Variable + ", " + frame.TimeSliceLongLabel
    )
    if frame.duplicated("Series").any():
        raise ValueError(f"Duplicate timeslice rows in {dataset}")
    return frame[columns].reset_index(drop=True)


def slice_comparison(frames, tolerance):
    """Compare slices like years, then restore their labels in timeslice order."""
    compared = period_comparison(frames, "Series", tolerance)
    detail = pd.concat(frames).drop_duplicates("Series")[["Series", *DETAIL]]
    compared = compared.merge(detail, on="Series", validate="many_to_one")
    order = ["Technology", "Variable", "TimeSliceOrder"]
    return compared.sort_values(order).reset_index(drop=True)


def draw_season(axis, season, value_label):
    """Draw a baseline and candidate bar for each slice in one season."""
    slices = season.drop_duplicates("TimeSlice").sort_values("TimeSliceOrder")
    position = {name: index for index, name in enumerate(slices.TimeSlice)}
    x = season.TimeSlice.map(position)
    flagged = season.ExceedsTolerance.to_numpy(dtype=bool, na_value=False)
    for index in x[flagged].unique():
        axis.axvspan(index - 0.5, index + 0.5, color="#ffb65c", alpha=0.2, linewidth=0)
    for offset, column, colour in zip(
        [-0.2, 0.2], ["Value_baseline", "Value_candidate"], SCENARIO_COLOURS
    ):
        axis.bar(x + offset, season[column], width=0.4, color=colour)
    axis.set_xticks(
        range(len(slices)), slices.TimeSliceDayTime, rotation=30, ha="right"
    )
    axis.axhline(0, color="#888888", linewidth=0.6)
    axis.set_ylabel(value_label)
    axis.grid(axis="y", color="#e5e5e5", linewidth=0.6)
    axis.set_axisbelow(True)


def slice_chart(compared, value_label):
    """Embed one figure per technology, with a panel for each season."""
    if compared.empty:
        return "<p>no data found</p>"
    images = []
    with mpl.rc_context({"font.size": 9, "svg.fonttype": "none"}):
        for technology, panel in compared.groupby("Technology", sort=False):
            figure = Figure(figsize=(11, 6), dpi=100, layout="constrained")
            axes = figure.subplots(2, 2, sharey=True).flat
            for axis, season in zip(axes, SEASONS):
                draw_season(axis, panel.loc[panel.Season.eq(season)], value_label)
                axis.set_title(season, fontsize=10)
            figure.suptitle(technology, fontsize=11)
            images.append(embed_svg(figure, f"{technology} ({value_label})"))
    return unavailable_message(compared) + "".join(images)
