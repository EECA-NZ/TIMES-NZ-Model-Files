"""Draw comparison charts as offline SVG images."""

import base64
import html
import io
import math

import matplotlib as mpl
import pandas as pd
from matplotlib.backends.backend_svg import FigureCanvasSVG
from matplotlib.figure import Figure

from qa_times_nz.report.compare import different_period_spans

SCENARIO_COLOURS = ["#447474", "#C346CE"]


def draw_panel(axis, frames, value_label, tolerance):
    """Draw scenario lines and tolerance bands on one static panel."""
    for frame, colour in zip(frames, SCENARIO_COLOURS):
        frame = frame.sort_values("Period")
        axis.plot(
            frame["Period"], frame["Value"], color=colour, marker="o", markersize=3
        )
    for left, right in different_period_spans(
        dict(zip(frames[0]["Period"], frames[0]["Value"])),
        dict(zip(frames[1]["Period"], frames[1]["Value"])),
        tolerance,
    ):
        axis.axvspan(left, right, color="#ffb65c", alpha=0.2, linewidth=0)
    axis.set(xlabel="Year", ylabel=value_label)
    if not any(frame.Value.lt(0).any() for frame in frames):
        axis.set_ylim(bottom=0)
    axis.ticklabel_format(axis="x", style="plain", useOffset=False)
    axis.grid(color="#e5e5e5", linewidth=0.6)
    axis.set_axisbelow(True)


def chart_figure(frames, group, value_label, tolerance):
    """Build static panels with consistent sizing and independent y scales."""
    categories = list(pd.concat(frames)[group].unique()) if group else [None]
    columns = min(3, len(categories))
    rows = math.ceil(len(categories) / columns)
    figure = Figure(
        figsize=(11, rows * 2.8 + (rows - 1) * 0.4 + 0.8), dpi=100, layout="constrained"
    )
    axes = figure.subplots(rows, columns, squeeze=False).flat
    for axis, category in zip(axes, categories):
        selected = (
            [frame.loc[frame[group].eq(category)] for frame in frames]
            if group
            else frames
        )
        draw_panel(axis, selected, value_label, tolerance)
        if group:
            axis.set_title(str(category), fontsize=10, wrap=True)
    for axis in list(figure.axes)[len(categories) :]:
        axis.remove()
    return figure


def detail_chart(frames, group, value_label, tolerance):
    """Embed an offline SVG, preserving the colour assigned to each input role."""
    if all(frame.empty for frame in frames):
        return "<p>no data found</p>"
    message = "".join(
        f"<p>{role.title()} data unavailable; comparisons are N/A.</p>"
        for role, frame in zip(["baseline", "candidate"], frames)
        if frame.empty
    )
    with mpl.rc_context({"font.size": 9, "svg.fonttype": "none"}):
        figure = chart_figure(frames, group, value_label, tolerance)
        output = io.BytesIO()
        FigureCanvasSVG(figure).print_svg(output)
    encoded = base64.b64encode(output.getvalue()).decode("ascii")
    return (
        message + f'<img class="chart" alt="{html.escape(value_label)}" '
        f'src="data:image/svg+xml;base64,{encoded}">'
    )
