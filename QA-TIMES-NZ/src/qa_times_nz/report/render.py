"""Assemble the self-contained HTML report from compared metrics and charts."""

import html
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

from qa_times_nz.report.charts import SCENARIO_COLOURS
from qa_times_nz.report.metrics import PAGES

ASSETS = Path(__file__).parent / "assets"


def nz_timestamp(value):
    """Display a timezone-aware manifest timestamp in New Zealand local time."""
    timestamp = datetime.fromisoformat(value)
    if timestamp.tzinfo is None:
        raise ValueError("Expected a timestamp with a timezone")
    return timestamp.astimezone(ZoneInfo("Pacific/Auckland")).strftime(
        "%d %b %Y, %I:%M %p %Z"
    )


def comparison_table(compared, group, value_label, labels, *, annual=True):
    """Render supplied values and differences, highlighting assessed failures."""
    if compared.empty:
        return ""
    headers = ([group] if group else []) + (["Year"] if annual else [])
    difference_label = (
        "Difference (percentage points)" if value_label == "%" else "Difference"
    )
    headers += [
        *labels,
        difference_label,
        "Relative difference (%)",
    ]
    rows = []
    for row in compared.to_dict("records"):
        cells = ([str(row[group])] if group else []) + (
            [str(row["Period"])] if annual else []
        )
        cells += [
            f"{row[key]:,.3f}" if pd.notna(row[key]) else "N/A"
            for key in ["Value_baseline", "Value_candidate", "Difference"]
        ]
        cells += [
            (
                f"{row['PercentDifference']:+.2f}%"
                if pd.notna(row["PercentDifference"])
                else "N/A"
            ),
        ]
        exceeds = row["ExceedsTolerance"]
        style = ' class="over-tolerance"' if pd.notna(exceeds) and exceeds else ""
        rows.append(
            f"<tr{style}>"
            + "".join(f"<td>{html.escape(cell)}</td>" for cell in cells)
            + "</tr>"
        )
    heading = "".join(f'<th scope="col">{html.escape(label)}</th>' for label in headers)
    caption = f"<caption>{html.escape(value_label)}</caption>" if value_label else ""
    return (
        '<div class="table-scroll">'
        f"<table>{caption}<thead><tr>{heading}</tr></thead>"
        f'<tbody>{"".join(rows)}</tbody></table></div>'
    )


def comparison_accordion(compared, group, value_label, labels, *, annual=True):
    """Keep chart data expandable while sharing the objective table's formatting."""
    table = comparison_table(compared, group, value_label, labels, annual=annual)
    return (
        f"<details><summary>View data and differences</summary>{table}</details>"
        if table
        else ""
    )


def input_provenance(selected, role):
    """Show the resolved identity and execution/release time, without guessing versions."""
    manifest = selected["manifest"]
    created = (
        manifest["created_at"]
        if selected["source"] == "RELEASE"
        else manifest["execution"]["completed_at"]
    )
    if not isinstance(created, str):
        raise ValueError(f"Expected a source timestamp: {selected['manifest_path']}")
    return {
        "Input": role.title(),
        "Label": selected["label"],
        "Source": selected["source"],
        "Release/run": (
            selected["result_root"].name
            if selected["source"] == "RELEASE"
            else selected["result_root"].parent.name
        ),
        "Scenario": selected["scenario"],
        "Release created / solve completed (NZ)": nz_timestamp(created),
    }


# pylint: disable-next=too-many-locals
def render_report(inputs, comparisons, charts, tolerance):
    """Use the existing five-page layout with explicit data coverage and provenance."""
    labels = [
        f"{role.title()}: {inputs[role]['label']}" for role in ["baseline", "candidate"]
    ]
    title = html.escape(
        f"{inputs['baseline']['label']} vs {inputs['candidate']['label']}"
    )
    heading = " vs ".join(
        f'<span style="color:{colour}">{html.escape(inputs[role]["label"])}</span>'
        for role, colour in zip(["baseline", "candidate"], SCENARIO_COLOURS)
    )
    navigation = '<a href="#summary" data-page="summary">Summary</a>'
    pages, summaries = [], []
    for page, (page_title, specs) in PAGES.items():
        navigation += f'<a href="#{page}" data-page="{page}">{page_title}</a>'
        links, sections = [], []
        for spec in specs:
            name = spec.title
            links.append(f'<a href="#{spec.key}">{html.escape(name)}</a>')
            sections.append(
                f'<section id="{spec.key}" class="report-section">'
                f"<h2>{html.escape(name)}</h2>"
                f"{charts[spec.key]}"
                f"{comparison_accordion(comparisons[spec.key], spec.group, spec.unit, labels)}"
                "</section>"
            )
            if spec.group is None:
                compared = comparisons[spec.key]
                assessed = compared.ExceedsTolerance.notna().sum()
                summaries.append(
                    {
                        "Metric": name,
                        "Years outside tolerance": (
                            f"{int(compared.ExceedsTolerance.sum())} / {int(assessed)}"
                            if assessed
                            else "N/A"
                        ),
                        "_fraction": compared.ExceedsTolerance.mean(),
                    }
                )
        pages.append(
            f'<div id="{page}" class="page section-page" hidden>'
            f'<nav aria-label="{page_title} sections"><strong>Page contents</strong>'
            f'{"".join(links)}</nav><div class="page-content">'
            f'{"".join(sections)}</div></div>'
        )
    selected_inputs = pd.DataFrame(
        [input_provenance(inputs[role], role) for role in ["baseline", "candidate"]]
    ).to_html(index=False, border=0)
    objective = comparisons["objective_function"]
    objective_table = (
        comparison_table(objective, None, "", labels, annual=False)
        if not objective.empty
        else "<p>no data found</p>"
    )
    summary_table = (
        pd.DataFrame(summaries)
        .sort_values("_fraction", ascending=False, kind="stable", na_position="last")
        .drop(columns="_fraction")
        .to_html(index=False, border=0)
    )
    style = (ASSETS / "report.css").read_text(encoding="utf-8")
    script = (ASSETS / "report.js").read_text(encoding="utf-8")
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>TIMES-NZ · {title}</title><style>{style}</style></head><body><main>
<div class="tag">TIMES-NZ / QUALITY ASSURANCE</div><h1>{heading}</h1>
<nav aria-label="Report pages">{navigation}</nav>
<div id="summary" class="page">
<p>Relative difference tolerance: <strong>{tolerance:.2%}</strong>.
Differences outside tolerance are highlighted.
</p>
<section><h2>Selected inputs</h2>{selected_inputs}
<h3>Objective function (NZDb)</h3>{objective_table}</section>
<section><h2>Differences in key metrics</h2>
{summary_table}</section>
</div>
{"".join(pages)}</main><script>{script}</script></body></html>"""
