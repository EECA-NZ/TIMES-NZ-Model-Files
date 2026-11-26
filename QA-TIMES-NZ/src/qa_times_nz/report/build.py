"""Resolve inputs, compare prepared summaries and write the report and CSV."""

import re

import pandas as pd

from qa_times_nz import report_inputs
from qa_times_nz.report.charts import detail_chart
from qa_times_nz.report.compare import period_comparison, read_metric
from qa_times_nz.report.metrics import PAGES
from qa_times_nz.report.render import render_report
from qa_times_nz.report.slices import read_slice_metric, slice_chart, slice_comparison

OBJECTIVE_DATASET = "indicators/objective_function"


def comparisons_path(report_path):
    """CSV path that sits beside, and is named after, the HTML report."""
    return report_path.with_name(f"{report_path.stem} comparisons.csv")


# pylint: disable-next=too-many-locals
def build_report(*, dev=False):
    """Validate inputs, then write the configured report and its comparison CSV."""
    inputs = report_inputs.resolve_inputs(dev=dev)
    tolerance = inputs["tolerance"]
    selected_roles = ["baseline", "candidate"]
    selected = [inputs[role] for role in selected_roles]
    comparisons, charts, csv_tables = {}, {}, []
    for _, specs in PAGES.values():
        for spec in specs:
            if spec.slices:
                frames = [
                    read_slice_metric(source, spec.dataset, spec.unit)
                    for source in selected
                ]
                compared = slice_comparison(frames, tolerance)
                chart = slice_chart(compared, spec.unit)
            else:
                frames = [
                    read_metric(
                        source, spec.dataset, spec.group, spec.unit, spec.filters
                    )
                    for source in selected
                ]
                compared = period_comparison(frames, spec.group, tolerance)
                chart = detail_chart(compared, spec.group, spec.unit)
            comparisons[spec.key] = compared
            charts[spec.key] = chart
            csv_tables.append(
                compared.assign(
                    Metric=spec.key, Dataset=f"summaries/{spec.dataset}.csv"
                )
            )
    objective = [
        read_metric(source, OBJECTIVE_DATASET, None, "NZDb", {}, annual=False)
        for source in selected
    ]
    comparisons["objective_function"] = period_comparison(
        objective, None, tolerance, annual=False
    )
    csv_tables.append(
        comparisons["objective_function"].assign(
            Metric="objective_function",
            Dataset=f"summaries/{OBJECTIVE_DATASET}.csv",
        )
    )
    content = render_report(inputs, comparisons, charts, tolerance)
    csv = pd.concat(csv_tables, ignore_index=True).assign(
        BaselineScenario=inputs["baseline"]["scenario"],
        CandidateScenario=inputs["candidate"]["scenario"],
    )
    csv["Period"] = csv.Period.astype("Int64")
    output = report_inputs.REPOSITORY_ROOT / "QA-TIMES-NZ" / "build"
    output.mkdir(parents=True, exist_ok=True)
    labels = [
        re.sub(r"[^\w .()+-]", "_", inputs[role]["label"]) for role in selected_roles
    ]
    path = output / f"TIMES-QA-{labels[0]} vs {labels[1]}.html"
    csv.to_csv(comparisons_path(path), index=False)
    path.write_text(content, encoding="utf-8")
    return path
