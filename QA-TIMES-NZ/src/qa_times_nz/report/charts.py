"""Draw comparison charts as offline SVG images."""

import base64
import html
import io
import math

import matplotlib as mpl
from matplotlib.backends.backend_svg import FigureCanvasSVG
from matplotlib.figure import Figure

from qa_times_nz.report.compare import different_period_spans

SCENARIO_COLOURS = ["#447474", "#C346CE"]


def draw_panel(axis, panel, value_label):
    """Draw scenario lines and over-tolerance bands from one comparison panel."""
    panel = panel.sort_values("Period")
    for column, colour in zip(["Value_baseline", "Value_candidate"], SCENARIO_COLOURS):
        axis.plot(
            panel["Period"], panel[column], color=colour, marker="o", markersize=3
        )
    for left, right in different_period_spans(panel):
        axis.axvspan(left, right, color="#ffb65c", alpha=0.2, linewidth=0)
    axis.set(xlabel="Year", ylabel=value_label)
    if not panel[["Value_baseline", "Value_candidate"]].lt(0).any().any():
        axis.set_ylim(bottom=0)
    axis.ticklabel_format(axis="x", style="plain", useOffset=False)
    axis.grid(color="#e5e5e5", linewidth=0.6)
    axis.set_axisbelow(True)


def chart_figure(compared, group, value_label):
    """Build static panels with consistent sizing and independent y scales."""
    categories = list(compared[group].unique()) if group else [None]
    columns = min(3, len(categories))
    rows = math.ceil(len(categories) / columns)
    figure = Figure(
        figsize=(11, rows * 2.8 + (rows - 1) * 0.4 + 0.8), dpi=100, layout="constrained"
    )
    axes = figure.subplots(rows, columns, squeeze=False).flat
    for axis, category in zip(axes, categories):
        panel = compared.loc[compared[group].eq(category)] if group else compared
        draw_panel(axis, panel, value_label)
        if group:
            axis.set_title(str(category), fontsize=10, wrap=True)
    for axis in list(figure.axes)[len(categories) :]:
        axis.remove()
    return figure


def detail_chart(compared, group, value_label):
    """Embed an offline SVG, preserving the colour assigned to each input role."""
    if compared.empty:
        return "<p>no data found</p>"
    message = "".join(
        f"<p>{role.title()} data unavailable; comparisons are N/A.</p>"
        for role in ["baseline", "candidate"]
        if compared[f"Value_{role}"].isna().all()
    )
    with mpl.rc_context({"font.size": 9, "svg.fonttype": "none"}):
        figure = chart_figure(compared, group, value_label)
        output = io.BytesIO()
        FigureCanvasSVG(figure).print_svg(output)
    encoded = base64.b64encode(output.getvalue()).decode("ascii")
    return (
        message + f'<img class="chart" alt="{html.escape(value_label)}" '
        f'src="data:image/svg+xml;base64,{encoded}">'
    )
