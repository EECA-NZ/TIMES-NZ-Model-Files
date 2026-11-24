"""Resolve inputs, compare prepared summaries and write the report and CSV."""

import pandas as pd

from qa_times_nz import report_inputs
from qa_times_nz.report.charts import detail_chart
from qa_times_nz.report.compare import period_comparison, read_metric
from qa_times_nz.report.metrics import PAGES
from qa_times_nz.report.render import render_report

OBJECTIVE_DATASET = "indicators/objective_function"


# pylint: disable-next=too-many-locals
def build_report(*, dev=False):
    """Validate inputs, then write the configured report and its comparison CSV."""
    inputs = report_inputs.resolve_inputs(dev=dev)
    tolerance = inputs["tolerance"]
    selected = [inputs[role] for role in ["baseline", "candidate"]]
    comparisons, charts, csv_tables = {}, {}, []
    for _, specs in PAGES.values():
        for spec in specs:
            frames = [
                read_metric(source, spec.dataset, spec.group, spec.unit, spec.filters)
                for source in selected
            ]
            compared = period_comparison(frames, spec.group, tolerance)
            comparisons[spec.key] = compared
            charts[spec.key] = detail_chart(frames, spec.group, spec.unit, tolerance)
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
    csv.to_csv(output / "comparisons.csv", index=False)
    path = output / "report.html"
    path.write_text(content, encoding="utf-8")
    return path
