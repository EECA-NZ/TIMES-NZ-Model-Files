"""Build the standalone demo: python -m qa_times_nz.demo_report."""

import base64
import html
import io
import json
import math
import tomllib
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import matplotlib as mpl
import pandas as pd
from matplotlib.backends.backend_svg import FigureCanvasSVG
from matplotlib.figure import Figure

# EECA teal and purple from the existing QA chart palette.
SCENARIO_COLOURS = ["#447474", "#C346CE"]


def nz_timestamp(value):
    """Display a timezone-aware manifest timestamp in New Zealand local time."""
    timestamp = datetime.fromisoformat(value)
    if timestamp.tzinfo is None:
        raise ValueError("Expected a timestamp with a timezone")
    return timestamp.astimezone(ZoneInfo("Pacific/Auckland")).strftime(
        "%d %b %Y, %I:%M %p %Z"
    )


def electricity_demand(frame, groups=()):
    """Aggregate final electricity demand across sectors and regions, in TWh."""
    demand = frame.loc[
        frame["Variable"].eq("Energy demand") & frame["Fuel"].eq("Electricity")
    ].copy()
    return annual_energy(demand, groups)


def electricity_generation(frame):
    """Return generation by technology group and year, in TWh."""
    generation = frame.loc[frame["Variable"].eq("Electricity generation")].copy()
    if generation["TechnologyGroup"].isna().any():
        raise ValueError("Missing generation technology group")
    return annual_energy(generation, ["TechnologyGroup"])


def annual_energy(frame, groups=()):
    """Aggregate selected annual PJ records and convert to TWh."""
    result = annual_totals(frame, groups)
    result["Value"] /= 3.6
    return result


def annual_totals(frame, groups=(), unit="PJ"):
    """Validate and aggregate annual records without changing units."""
    if frame.empty or not frame["Unit"].eq(unit).all():
        raise ValueError(f"Expected non-empty data in {unit}")
    if groups and frame[list(groups)].isna().any().any():
        raise ValueError("Missing energy grouping values")
    periods = pd.to_numeric(frame["Period"], errors="raise")
    if periods.isna().any() or periods.mod(1).ne(0).any():
        raise ValueError("Expected integer annual periods")
    frame = frame.assign(Period=periods.astype(int))
    return frame.groupby([*groups, "Period"], as_index=False)["Value"].sum()


def natural_gas_demand(frame):
    """Return final natural gas demand by sector group in PJ."""
    return annual_totals(
        frame.loc[
            frame["Variable"].eq("Energy demand") & frame["Fuel"].eq("Natural gas")
        ],
        ["SectorGroup"],
    )


def natural_gas_supply(frame):
    """Return domestic natural gas and imported LNG supply in PJ."""
    supply = frame.loc[
        frame["Variable"].eq("Primary Energy Production")
        & frame["Fuel"].isin(["Natural gas", "LNG"])
    ].copy()
    supply["Supply source"] = supply["Fuel"].map(
        {"Natural gas": "Domestic natural gas", "LNG": "LNG imports"}
    )
    return annual_totals(supply, ["Supply source"])


def fuel_demand(frame, fuel):
    """Return final demand for one fuel by sector group in PJ."""
    return annual_totals(
        frame.loc[frame["Variable"].eq("Energy demand") & frame["Fuel"].eq(fuel)],
        ["SectorGroup"],
    )


def road_fuel_demand(frame, fuel):
    """Return road fuel demand by vehicle class in PJ, excluding other transport."""
    demand = frame.loc[
        frame["Variable"].eq("Energy demand")
        & frame["Fuel"].eq(fuel)
        & frame["SectorGroup"].eq("Transport")
        & frame["Sector"].eq("Road Transport")
    ].rename(columns={"EndUse": "Vehicle class"})
    return annual_totals(demand, ["Vehicle class"])


def biomass_demand(frame):
    """Return final woody biomass demand, including onsite residues, by sector in PJ."""
    return annual_totals(
        frame.loc[
            frame["Variable"].eq("Energy demand")
            & frame["Fuel"].isin(["Wood", "Wood residuals (onsite)"])
        ],
        ["SectorGroup"],
    )


def emissions_by_sector(frame):
    """Return annual energy emissions by sector group in Mt CO2e."""
    result = annual_totals(frame, ["SectorGroup"], unit="kt CO2e")
    result["Value"] /= 1000
    return result


def objective_value(frame):
    """Require exactly one whole-run objective, already expressed in NZDb."""
    if len(frame) != 1 or frame.iloc[0]["Unit"] != "NZDb":
        raise ValueError("Expected one objective value in NZDb")
    value = float(frame.iloc[0]["Value"])
    if not pd.notna(value) or abs(value) == float("inf"):
        raise ValueError("Expected a finite objective value")
    return value


def within_tolerance(baseline, candidate, tolerance):
    """Compare finite values relative to baseline; zero matches only zero."""
    return (
        math.isfinite(baseline)
        and math.isfinite(candidate)
        and abs(candidate - baseline) <= abs(baseline) * tolerance
    )


def changed_periods(baseline, candidate, tolerance):
    """Count annual totals outside tolerance, including unmatched years."""
    totals = [frame.groupby("Period")["Value"].sum() for frame in (baseline, candidate)]
    compared = pd.concat(totals, axis=1, keys=["Baseline", "Candidate"])
    return sum(
        not within_tolerance(row.Baseline, row.Candidate, tolerance)
        for row in compared.itertuples()
    )


def different_period_spans(baseline, candidate, tolerance):
    """Yield differing periods bounded by midpoints to neighbouring periods."""
    periods = sorted(baseline.keys() | candidate.keys())
    for index, period in enumerate(periods):
        if within_tolerance(
            baseline.get(period, float("nan")),
            candidate.get(period, float("nan")),
            tolerance,
        ):
            continue
        left = (periods[index - 1] + period) / 2 if index else period
        right = (
            (period + periods[index + 1]) / 2 if index + 1 < len(periods) else period
        )
        if len(periods) == 1:
            left, right = period - 0.5, period + 0.5
        yield left, right


def draw_panel(axis, frames, value_label, tolerance):
    """Draw scenario lines and tolerance bands on one static panel."""
    for frame, colour in zip(frames, SCENARIO_COLOURS):
        frame = frame.sort_values("Period")
        axis.plot(frame["Period"], frame["Value"], color=colour)
    for left, right in different_period_spans(
        dict(zip(frames[0]["Period"], frames[0]["Value"])),
        dict(zip(frames[1]["Period"], frames[1]["Value"])),
        tolerance,
    ):
        axis.axvspan(left, right, color="#ffb65c", alpha=0.2, linewidth=0)
    axis.set(xlabel="Year", ylabel=value_label, ylim=(0, None))
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


def period_comparison(frames, group, tolerance):
    """Align chart values and calculate candidate-minus-baseline differences."""
    keys = ([group] if group else []) + ["Period"]
    compared = (
        frames[0][keys + ["Value"]]
        .merge(
            frames[1][keys + ["Value"]],
            on=keys,
            how="outer",
            suffixes=("_baseline", "_candidate"),
            validate="one_to_one",
        )
        .sort_values(keys)
    )
    compared["Difference"] = compared["Value_candidate"] - compared["Value_baseline"]
    compared["PercentDifference"] = (
        compared["Difference"]
        / compared["Value_baseline"].mask(compared["Value_baseline"].eq(0))
        * 100
    )
    compared["ExceedsTolerance"] = [
        not within_tolerance(row.Value_baseline, row.Value_candidate, tolerance)
        for row in compared.itertuples()
    ]
    return compared


def comparison_accordion(frames, group, value_label, tolerance):
    """Render a native details element with grouped, highlighted comparison rows."""
    headers = ([group] if group else []) + [
        "Year",
        frames[0]["Input"].iloc[0],
        frames[1]["Input"].iloc[0],
        "Difference",
        "Difference (%)",
    ]
    rows = []
    for row in period_comparison(frames, group, tolerance).to_dict("records"):
        cells = ([str(row[group])] if group else []) + [str(row["Period"])]
        cells += [
            f"{row[key]:,.3f}" if pd.notna(row[key]) else "—"
            for key in ("Value_baseline", "Value_candidate", "Difference")
        ]
        cells.append(
            f"{row['PercentDifference']:+.2f}%"
            if pd.notna(row["PercentDifference"])
            else "—"
        )
        style = ' class="over-tolerance"' if row["ExceedsTolerance"] else ""
        rows.append(
            f"<tr{style}>"
            + "".join(f"<td>{html.escape(cell)}</td>" for cell in cells)
            + "</tr>"
        )
    heading = "".join(f'<th scope="col">{html.escape(label)}</th>' for label in headers)
    return (
        '<details><summary>View data and differences</summary><div class="table-scroll">'
        f"<table><caption>{html.escape(value_label)}</caption><thead><tr>{heading}</tr></thead>"
        f'<tbody>{"".join(rows)}</tbody></table></div></details>'
    )


def detail_chart(frames, group, value_label, tolerance):
    """Embed a standalone SVG image without external files or chart JavaScript."""
    with mpl.rc_context({"font.size": 9, "svg.fonttype": "none"}):
        figure = chart_figure(frames, group, value_label, tolerance)
        output = io.BytesIO()
        FigureCanvasSVG(figure).print_svg(output)
    encoded = base64.b64encode(output.getvalue()).decode("ascii")
    return (
        f'<img class="chart" alt="{html.escape(value_label)}" '
        f'src="data:image/svg+xml;base64,{encoded}">'
        + comparison_accordion(frames, group, value_label, tolerance)
    )


def load_oil_and_gas(demand, folder, filters, label):
    """Load fuel summaries using the already-selected release and scenario."""
    return {
        "diesel_demand": fuel_demand(demand, "Diesel").assign(Input=label),
        "road_diesel": road_fuel_demand(demand, "Diesel").assign(Input=label),
        "petrol_demand": fuel_demand(demand, "Petrol").assign(Input=label),
        "road_petrol": road_fuel_demand(demand, "Petrol").assign(Input=label),
        "gas_demand": natural_gas_demand(demand).assign(Input=label),
        "gas_supply": natural_gas_supply(
            pd.read_parquet(folder / "labelled/primary_energy.parquet", filters=filters)
        ).assign(Input=label),
    }


def load_scenario(selected, role):
    """Load and validate the datasets for one configured release scenario."""
    releases = Path(__file__).resolve().parents[3] / "PUBLISH-TIMES-NZ/releases"
    # shortcut: demo supports RELEASE only; add SOLVE when implementing the plan.
    if selected["source"] != "RELEASE":
        raise ValueError("This demo supports RELEASE inputs only")
    release = selected["release"]
    if Path(release).name != release or release in (".", ".."):
        raise ValueError("Expected a release directory name")
    folder = releases / release
    manifest = json.loads((folder / "release-manifest.json").read_text())
    # Read only the selected scenario from each dataset.
    scenario = selected["scenario"]
    if scenario not in {entry["id"] for entry in manifest["scenarios"]}:
        raise ValueError(f"Scenario {scenario} is absent from release {release}")
    label = selected.get("label", scenario)
    filters = [("Scenario", "=", scenario)]
    demand = pd.read_parquet(folder / "labelled/energy_demand.parquet", filters=filters)
    objective = pd.read_parquet(
        folder / "labelled/objective_function.parquet", filters=filters
    )
    curve = electricity_demand(demand)
    curve["Input"] = f"{role.title()}: {label}"
    sector_demand = electricity_demand(demand, ["SectorGroup"])
    sector_demand["Input"] = f"{role.title()}: {label}"
    generation = electricity_generation(
        pd.read_parquet(folder / "labelled/elec_generation.parquet", filters=filters)
    )
    generation["Input"] = f"{role.title()}: {label}"
    provenance = {
        "Input": role.title(),
        "Label": label,
        "Release": release,
        "Scenario": scenario,
        "Release created": nz_timestamp(manifest["created_at"]),
    }
    print(f"{role}: {folder} / {scenario}")
    return {
        **load_oil_and_gas(demand, folder, filters, f"{role.title()}: {label}"),
        "emissions": emissions_by_sector(
            pd.read_parquet(folder / "labelled/emissions.parquet", filters=filters)
        ).assign(Input=f"{role.title()}: {label}"),
        "biomass_demand": biomass_demand(demand).assign(
            Input=f"{role.title()}: {label}"
        ),
        "demand": curve,
        "sector_demand": sector_demand,
        "generation": generation,
        "objective": objective_value(objective),
        "input": provenance,
    }


def objective_summary(baseline, candidate):
    """Render the whole-run objective comparison table."""
    difference = candidate - baseline
    percent = f"{difference / baseline * 100:+.2f}%" if baseline else "Undefined"
    return pd.DataFrame(
        [
            {
                "Baseline (NZDb)": f"{baseline:,.3f}",
                "Candidate (NZDb)": f"{candidate:,.3f}",
                "Change (NZDb)": f"{difference:+,.3f}",
                "Change (%)": percent,
            }
        ]
    ).to_html(index=False, border=0)


def fill_report_zeroes(scenarios):
    """Complete these energy series over selected model years and category unions."""
    periods = sorted(
        {year for scenario in scenarios for year in scenario["demand"]["Period"]}
    )
    for key, groups in {
        "demand": [],
        "sector_demand": ["SectorGroup"],
        "generation": ["TechnologyGroup"],
        "gas_demand": ["SectorGroup"],
        "gas_supply": ["Supply source"],
        "diesel_demand": ["SectorGroup"],
        "road_diesel": ["Vehicle class"],
        "petrol_demand": ["SectorGroup"],
        "road_petrol": ["Vehicle class"],
        "biomass_demand": ["SectorGroup"],
        "emissions": ["SectorGroup"],
    }.items():
        grid = pd.DataFrame({"Period": periods})
        if groups:
            categories = pd.concat(
                [scenario[key][groups] for scenario in scenarios]
            ).drop_duplicates()
            grid = grid.merge(categories, how="cross")
        index = grid.set_index(groups + ["Period"]).index
        for scenario in scenarios:
            frame = scenario[key]
            label = frame["Input"].iloc[0]
            # Only absent rows become zero; existing values are preserved.
            scenario[key] = (
                frame.set_index(groups + ["Period"])[["Value"]]
                .reindex(index, fill_value=0)
                .reset_index()
                .assign(Input=label)
            )


def metric_report(scenarios, tolerance):
    """Build metric totals and detail charts from the same selected series."""
    totals, charts = {}, {}
    for key, group, unit in [
        ("gas_demand", "SectorGroup", "PJ"),
        ("gas_supply", "Supply source", "PJ"),
        ("diesel_demand", "SectorGroup", "PJ"),
        ("petrol_demand", "SectorGroup", "PJ"),
        ("biomass_demand", "SectorGroup", "PJ"),
        ("emissions", "SectorGroup", "Mt CO₂e"),
    ]:
        frames = [scenario[key] for scenario in scenarios]
        totals[key] = [
            frame.groupby(["Input", "Period"], as_index=False)["Value"].sum()
            for frame in frames
        ]
        charts[key] = detail_chart(frames, group, unit, tolerance)
        charts[f"{key}_total"] = detail_chart(totals[key], None, unit, tolerance)
    for key in ("road_diesel", "road_petrol"):
        charts[key] = detail_chart(
            [scenario[key] for scenario in scenarios], "Vehicle class", "PJ", tolerance
        )
    return {"totals": totals, "charts": charts}


def render_report(scenarios, tolerance, config_path):
    """Render loaded comparison data as an offline HTML report."""
    curves = [scenario["demand"] for scenario in scenarios]
    generations = [scenario["generation"] for scenario in scenarios]
    sector_demands = [scenario["sector_demand"] for scenario in scenarios]
    inputs = [scenario["input"] for scenario in scenarios]
    generation_totals = [
        frame.groupby(["Input", "Period"], as_index=False)["Value"].sum()
        for frame in generations
    ]
    metrics = metric_report(scenarios, tolerance)
    changed_table = pd.DataFrame(
        [
            {
                "Metric": name,
                "Years where difference exceeds tolerance": (
                    f"{changed_periods(frames[0], frames[1], tolerance)} / "
                    f"{len(set(frames[0]['Period']) | set(frames[1]['Period']))}"
                ),
            }
            for name, frames in [
                ("Total electricity demand", curves),
                ("Total electricity generation", generation_totals),
                ("Total final natural gas demand", metrics["totals"]["gas_demand"]),
                ("Total diesel demand", metrics["totals"]["diesel_demand"]),
                ("Total petrol demand", metrics["totals"]["petrol_demand"]),
                ("Total biomass demand", metrics["totals"]["biomass_demand"]),
                ("Total emissions", metrics["totals"]["emissions"]),
                (
                    "Total natural gas supply (including LNG)",
                    metrics["totals"]["gas_supply"],
                ),
            ]
        ]
    ).to_html(index=False, border=0)
    charts = {}
    charts["generation_total"] = detail_chart(
        generation_totals, None, "Generation (TWh)", tolerance
    )
    charts["generation"] = detail_chart(
        generations, "TechnologyGroup", "Generation (TWh)", tolerance
    )
    charts["demand_total"] = detail_chart(
        curves, None, "Electricity demand (TWh)", tolerance
    )
    charts["demand"] = detail_chart(
        sector_demands, "SectorGroup", "Electricity demand (TWh)", tolerance
    )
    objective_table = objective_summary(
        scenarios[0]["objective"], scenarios[1]["objective"]
    )
    title = html.escape(f"{inputs[0]['Label']} vs {inputs[1]['Label']}")
    heading = " vs ".join(
        f'<span style="color:{colour}">{html.escape(selected["Label"])}</span>'
        for selected, colour in zip(inputs, SCENARIO_COLOURS)
    )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>TIMES-NZ · {title}</title><style>
body {{font:16px system-ui,sans-serif;color:#164057;background:#f3f6f6;margin:0}}
main {{max-width:1360px;margin:40px auto;padding:0 24px}}
.chart {{display:block;width:100%;height:auto}}
section {{background:white;padding:24px;margin:24px 0;border-radius:12px;overflow:auto}}
h1 {{font-size:32px;position:sticky;top:0;z-index:40;background:#f3f6f6;
margin:0;padding:12px 0;line-height:40px;height:64px;box-sizing:border-box}}
h2 {{margin-top:0}} p {{line-height:1.6}}
table {{width:100%;border-collapse:collapse;text-align:left;font-size:14px}}
th,td {{padding:12px;border-bottom:1px solid #e1e8e8}} th {{text-align:left}}
details {{margin-top:20px}}
summary {{cursor:pointer;font-weight:600;padding:12px 0}}
.table-scroll {{overflow:auto;max-height:480px}}
.table-scroll thead th {{position:sticky;top:0;background:white}}
caption {{text-align:left;padding:12px 0;font-weight:600}}
tr.over-tolerance {{background:#fff0dc}}
.tag {{color:#447474;font-weight:600;letter-spacing:.08em;font-size:12px}}
nav {{display:flex;gap:12px;margin:24px 0}}
nav a {{padding:12px 20px;border-radius:8px;color:#164057;text-decoration:none}}
nav a[aria-current="page"] {{background:#164057;color:white}}
nav a[aria-current="location"] {{background:#e6f0ee;color:#164057;
font-weight:600;border-radius:0;box-shadow:inset 3px 0 #447474}}
nav[aria-label="Report pages"] {{position:sticky;top:64px;z-index:30;
background:#f3f6f6;margin:0;padding:12px 0;height:68px;box-sizing:border-box}}
.section-page {{display:grid;grid-template-columns:336px minmax(0,1fr);gap:24px}}
.section-page[hidden] {{display:none}}
.page-content {{min-width:0}}
nav[aria-label$="sections"] {{position:sticky;top:148px;align-self:start;
flex-direction:column;background:white;margin:0;padding:16px;
border:1px solid #d5dede;border-radius:10px;gap:4px}}
nav[aria-label$="sections"] {{max-height:calc(100vh - 164px);overflow:auto;box-sizing:border-box}}
nav[aria-label$="sections"] strong {{padding:4px 8px 12px}}
nav[aria-label$="sections"] a {{padding:10px 8px}}
nav[aria-label$="sections"] a {{white-space:normal}}
nav a {{line-height:20px;white-space:nowrap}}
.report-section {{scroll-margin-top:132px}}
</style></head><body><main>
<div class="tag">TIMES-NZ / QUALITY ASSURANCE / DEMO</div>
<h1>{heading}</h1>
<nav aria-label="Report pages">
<a href="#summary" data-page="summary">Summary</a>
<a href="#electricity" data-page="electricity">Electricity</a>
<a href="#oil-and-gas" data-page="oil-and-gas">Oil and gas</a>
<a href="#renewables" data-page="renewables">Renewables</a>
<a href="#emissions" data-page="emissions">Emissions</a>
</nav>
<div id="summary" class="page">
<p>Difference tolerance: <strong style="font-size:1.5em">{tolerance:.0%}</strong>.
Differences greater than tolerance are highlighted.</p>
<section><h2>Objective function</h2>{objective_table}
</section>
<section><h2>Differences in key metrics</h2>{changed_table}</section>
<section><h2>Selected inputs</h2>
{pd.DataFrame(inputs).to_html(index=False, border=0)}
<p>Configuration: {html.escape(str(config_path))}</p>
</section></div>
<div id="electricity" class="page section-page" hidden>
<nav aria-label="Electricity sections">
<strong>Page contents</strong>
<a href="#electricity-demand-total">Total electricity demand</a>
<a href="#electricity-demand-sector">Electricity demand by sector</a>
<a href="#electricity-generation-total">Total electricity generation</a>
<a href="#electricity-generation-type">Electricity generation by type</a>
</nav>
<div class="page-content">
<section id="electricity-demand-total" class="report-section">
<h2>Total electricity demand</h2>{charts["demand_total"]}</section>
<section id="electricity-demand-sector" class="report-section">
<h2>Electricity demand by sector</h2>{charts["demand"]}</section>
<section id="electricity-generation-total" class="report-section">
<h2>Total electricity generation</h2>{charts["generation_total"]}</section>
<section id="electricity-generation-type" class="report-section">
<h2>Electricity generation by type</h2>{charts["generation"]}</section>
</div></div>
<div id="oil-and-gas" class="page section-page" hidden>
<nav aria-label="Oil and gas sections">
<strong>Page contents</strong>
<a href="#gas-demand-total">Total final natural gas demand</a>
<a href="#gas-demand-sector">Final natural gas demand by sector</a>
<a href="#gas-supply-total">Total natural gas supply, including LNG</a>
<a href="#gas-supply-source">Natural gas supply by source</a>
<a href="#diesel-demand-total">Total diesel demand</a>
<a href="#diesel-demand-sector">Diesel demand by sector</a>
<a href="#road-diesel-class">Road diesel demand by vehicle class</a>
<a href="#petrol-demand-total">Total petrol demand</a>
<a href="#petrol-demand-sector">Petrol demand by sector</a>
<a href="#road-petrol-class">Road petrol demand by vehicle class</a>
</nav>
<div class="page-content">
<section id="gas-demand-total" class="report-section">
<h2>Total final natural gas demand</h2>{metrics["charts"]["gas_demand_total"]}</section>
<section id="gas-demand-sector" class="report-section">
<h2>Final natural gas demand by sector</h2>{metrics["charts"]["gas_demand"]}</section>
<section id="gas-supply-total" class="report-section">
<h2>Total natural gas supply, including LNG</h2>{metrics["charts"]["gas_supply_total"]}</section>
<section id="gas-supply-source" class="report-section">
<h2>Natural gas supply by source</h2>{metrics["charts"]["gas_supply"]}</section>
<section id="diesel-demand-total" class="report-section">
<h2>Total diesel demand</h2>{metrics["charts"]["diesel_demand_total"]}</section>
<section id="diesel-demand-sector" class="report-section">
<h2>Diesel demand by sector</h2>{metrics["charts"]["diesel_demand"]}</section>
<section id="road-diesel-class" class="report-section">
<h2>Road diesel demand by vehicle class</h2>{metrics["charts"]["road_diesel"]}</section>
<section id="petrol-demand-total" class="report-section">
<h2>Total petrol demand</h2>{metrics["charts"]["petrol_demand_total"]}</section>
<section id="petrol-demand-sector" class="report-section">
<h2>Petrol demand by sector</h2>{metrics["charts"]["petrol_demand"]}</section>
<section id="road-petrol-class" class="report-section">
<h2>Road petrol demand by vehicle class</h2>{metrics["charts"]["road_petrol"]}</section>
</div></div>
<div id="renewables" class="page section-page" hidden>
<nav aria-label="Renewables sections">
<strong>Page contents</strong>
<a href="#biomass-demand-total">Total biomass demand</a>
<a href="#biomass-demand-sector">Biomass demand by sector</a>
</nav>
<div class="page-content">
<section id="biomass-demand-total" class="report-section">
<h2>Total biomass demand</h2>{metrics["charts"]["biomass_demand_total"]}</section>
<section id="biomass-demand-sector" class="report-section">
<h2>Biomass demand by sector</h2>{metrics["charts"]["biomass_demand"]}</section>
</div></div>
<div id="emissions" class="page section-page" hidden>
<nav aria-label="Emissions sections">
<strong>Page contents</strong>
<a href="#emissions-total">Total emissions</a>
<a href="#emissions-sector">Emissions by sector</a>
</nav>
<div class="page-content">
<section id="emissions-total" class="report-section">
<h2>Total emissions</h2>{metrics["charts"]["emissions_total"]}</section>
<section id="emissions-sector" class="report-section">
<h2>Emissions by sector</h2>{metrics["charts"]["emissions"]}</section>
</div></div></main><script>
function updateContents() {{
  const page = document.querySelector('.page:not([hidden])');
  const sections = Array.from(page.querySelectorAll('.report-section'));
  if (!sections.length) return;
  const current = sections.find(section => section.getBoundingClientRect().bottom > 132)
    || sections[sections.length - 1];
  page.querySelectorAll('nav a').forEach(link => {{
    if (link.hash === '#' + current.id) link.setAttribute('aria-current', 'location');
    else link.removeAttribute('aria-current');
  }});
}}
const sectionObserver = new IntersectionObserver(updateContents, {{
  rootMargin: '-132px 0px 0px 0px'
}});
function showPage() {{
  sectionObserver.disconnect();
  const requested = location.hash.slice(1);
  const target = document.getElementById(requested);
  const selected = target?.closest('.page')?.id || 'summary';
  document.querySelectorAll('.page').forEach(page => {{page.hidden = page.id !== selected;}});
  document.querySelectorAll('nav a[data-page]').forEach(link => {{
    if (link.dataset.page === selected) link.setAttribute('aria-current', 'page');
    else link.removeAttribute('aria-current');
  }});
  requestAnimationFrame(() => {{
    if (selected !== 'summary' && requested !== selected)
      document.getElementById(requested).scrollIntoView();
    updateContents();
    document.querySelectorAll('#' + selected + ' .report-section')
      .forEach(section => sectionObserver.observe(section));
  }});
}}
window.addEventListener('hashchange', showPage);
showPage();
</script></body></html>"""


def build_report(config_path, output_path):
    """Read two named release scenarios and write an offline HTML comparison."""
    config = tomllib.loads(config_path.read_text(encoding="utf-8"))
    tolerance = float(config["tolerance"])
    if not math.isfinite(tolerance) or tolerance < 0:
        raise ValueError("Tolerance must be finite and non-negative")
    scenarios = [
        load_scenario(config[role], role) for role in ("baseline", "candidate")
    ]
    fill_report_zeroes(scenarios)
    content = render_report(scenarios, tolerance, config_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    print(f"Report: {output_path.resolve()}")


def main():
    """Build the demo with its fixed config and output locations."""
    qa_root = Path(__file__).resolve().parents[2]
    build_report(qa_root / "demo-report.toml", qa_root / "QA-report.html")


if __name__ == "__main__":
    main()
