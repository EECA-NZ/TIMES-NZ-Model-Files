# QA code review and cleanup plan

Reviewed: 23 November 2026. Status: recommendations; no runtime changes made.

This reviews the existing QA implementation separately from the
[reporting integration plan](reporting-plan.md). The recommendation is to retain
only the domain calculations and chart templates needed by agreed reports.
The inventory below identifies reusable material, not a commitment to preserve
or migrate every item. A wholesale rewrite is unnecessary.

## Scope preference

Keep this light touch. Build the first comparison with a small explicit
`RELEASE`/`SOLVE` source resolver, selected dataframe calculations and HTML/CSV
output. Follow the selection rules in the integration plan; make latest-run and
timestamp-pinning behaviour obvious to the human developer. Do not build an
abstraction framework to conceal those choices.

In the inventory, “keep” means useful to consider reusing if that report needs
it. It does not mean maintain an unused feature indefinitely. Remove confirmed
dead code after checking callers. Leave uncertain specialist code outside the
new report path until its usefulness is decided; do not spend effort repairing,
testing or migrating it in advance. Any shared code actually changed must still
have its retained callers handled completely.

## Inventory and recommended disposition

Paths below are relative to QA-TIMES-NZ; analysis modules live under
`src/qa_times_nz/analysis/`.

| Existing code or asset | Recommendation | Reason and required work |
| --- | --- | --- |
| `get_data.py`: electricity, emissions, battery and transport aggregations | Keep and adapt | Useful starting metrics. Separate file loading from dataframe calculations; accept explicit selected inputs and retain raw scenario IDs. Validate source units before relabelling or converting. |
| `get_data.py`: renewable electricity and TFEC shares | Keep, test before standard reporting | Already validates missing classifications and missing generation/fuel matches. Preserve plant-level keys, equal-efficiency assumption and international transport exclusions. Replace the live PREP classification dependency with a recorded source. |
| `get_data.py`: gas/biomass supply functions | Consolidate lightly | Three functions repeat primary-energy loading, filtering, grouping and small-value cleanup. Share that calculation while retaining readable named selections if callers need them. No general metric factory is needed. |
| `get_data.py`: filter helpers | Keep where used | Small and understandable. Replace default global scenario mapping with the report's explicit selection; avoid accepting display names as identity during calculation. |
| `analysis_demand.py` | Keep subject definitions; extract reusable calculations | Contains valuable sector/end-use selections, fuel groups, natural-gas sector classification and missing-fuel validation. Those definitions should feed tables and charts from the same calculated data. |
| `analysis_emissions.py`, `analysis_primary_energy.py`, `analysis_indicators.py` | Keep as thin chart callers | Already largely presentation over shared getters. Pass selected data explicitly and replace incidental display choices, such as excluding ERP2 inside the emissions chart, with an explicit comparison selection. |
| `analysis_transport.py` | Keep fleet charts; retire scratch maths from the standard workflow | `create_fleet_composition_chart()` is reusable. `quick_truck_maths()` is a hard-coded print calculation, not a result check; archive it only if its assumptions remain useful. Validate technology labels before mapping them. |
| `analysis_electricity_generation.py` | Keep annual and battery charts; separate diagnostics | Preserve generation/capacity views and peak-discharge logic. Move calculations out of rendering functions when needed by reports. Review unfinished diagnostics and live PREP reads before exposing them as checks. |
| `analysis_demand_flex_flows.py` | Keep as specialist analysis, migrate later | Equivalent-input conversion and missing-mapping checks are useful, but rely on archived scenario CSVs, fixed process mappings and global scenario selection. Use selected raw result artefacts if available; explicitly report unavailable legacy raw data. |
| `analysis_chart_helpers.py` | Keep plotting, palettes and export helpers; narrow responsibilities | Retain chart templates and PNG/CSV pairing. Move timeslice unit calculations out of chart styling, accept output directories explicitly, and pass scenario order from the comparison. |
| `sensitivity_*_charts.py` | Consolidate common plumbing | Both repeat scenario-map resolution, ordering, emissions/electricity aggregation and line plotting. Reuse shared calculations and chart routines; keep ETS and technology scenario selections distinct. |
| `sensitivity_demand_flex_reporting.py` | Keep specialist calculations; parameterize scenario roles | Objective differences, interaction effects and two-path technology valuation are useful. Replace constructed `family-v308` IDs with explicit selected scenario roles. Preserve subtraction signs and document what each comparison estimates. |
| `sensitivity_ets_price_reporting.py` | Keep objective/carbon-cost views; migrate reads | Reuse selected result loading. Verify carbon-cost units and interpretation across periods before presenting their sum as a comparable whole-run metric. |
| `analysis_reporting_helpers.py` | Keep validation and formatting | Existing objective uniqueness/missing-value checks are useful. Reuse objective calculations independently of output format; retain Markdown formatting only for callers that need it. |
| `create_analysis_charts.py` | Keep a simple entry point, adapt later | Existing subject orchestration is sufficient for batch chart export. A standard QA report should select its own required metrics instead of running every specialist chart and diagnostic. |
| `utilities/timeslices.py` | Keep, harden edge cases | Useful labels and order, but assumes the fixed 24-slice structure. Review the duplicated PUBLISH helper before changing either; avoid importing Explorer implementation details just to remove duplication. |
| `utilities/filepaths.py` | Reduce after caller migration | Retain stable module-relative locations for reference assets if needed. Retire `FINAL_DATA`, `SCENARIO_FILES` and live PREP paths when explicit artefact/reference inputs replace their callers. `ASSETS` and the `SCENARIO_MAP` alias have no Python callers found in QA. |
| `calibration_checks/calibration.py` | Replace from scratch after rethinking the checks | Retain historical calibration as a capability. Use old code and reports to inventory comparisons and source evidence, not as a migration target. Reassess mappings, boundaries and missingness explicitly. |
| `tests/test_analysis_reporting_helpers.py` | Keep and extend selectively | Three synthetic-data unit tests provide a useful pattern. Add tests for calculations being promoted into standard QA, rather than testing local result archives. |

## Issues to address before reusing calculations

### Confirmed failures and incomplete functions

- `get_thermal_generation_fuel_use()` filters `TechnologyGroup`, but its upstream
  `get_elec_gen_fuel_use()` groups that column away. A synthetic input reproduces
  `KeyError('TechnologyGroup')`. No callers were found in QA; remove the unused
  helper or fix the aggregation grain if thermal reporting is required.
- `split_timeslices()` indexes split columns 1 and 2 before handling `ANNUAL`.
  An annual-only dataframe reproduces `KeyError(1)`. Cover annual-only and empty
  inputs when this helper is retained.
- `get_scenario_facet_order()` and `create_thermal_generation_charts()` are print
  stubs. No callers were found in QA; delete rather than treating them as working
  functionality.
- `test_battery_afs()` is a scratch diagnostic in a chart module, not a pytest
  check. Either finish it as an explicit battery diagnostic with tested
  calculations or remove it after checking whether its analysis is still needed.

### Behaviour that can hide comparison problems

- `get_times_data()` silently filters to a fixed v308 mapping and replaces IDs
  with labels. Missing selected scenarios can produce empty data, while repeated
  labels across versions can collapse distinct inputs during later aggregation.
- Annual string periods are not normalized by the common QA loader. Some chart
  paths cast them, while line-chart labelling performs `Period + 1`. Fix SOLVE's
  annual output type and validate older artefacts at QA's loading boundary.
- Calibration's `build_scenario_comparison()` derives scenarios from available
  model rows, left-joins from historical coverage and fills missing model values
  with zero. Entirely missing scenarios and model-only categories can disappear.
  Make requested coverage and missingness explicit before reusing this join.
- Calibration prints and excludes unmapped generation technologies, and industry
  fuel classification drops unmapped process codes. Preserve diagnostics, expose
  excluded coverage in reports, and decide which missing mappings block a metric.
- Some label mappings use `map()` without checking for unmapped values, and pandas
  grouping can drop null dimensions. Audit these selections as metrics migrate;
  do not assume their totals cover every original row.
- Area and timeslice charts add presentation zeroes. Keep that chart preparation
  separate from unrelated metric data. Battery and demand-flex exports intentionally
  complete missing timeslices with zero, as previously reviewed; preserve that
  behaviour rather than treating it as a defect or reopening the assumption.

## Calibration and reference assets

Keep `calibration_data/electricity.csv`, the GHG inventory workbook, and the
external-model CSVs/workbooks as reference evidence. Record their source,
vintage, units and preparation method. Existing README text is incomplete and
`analysis/readme.txt` still describes coupling to the old Explorer configuration.

Rebuild calibration from scratch after agreeing the new check definitions. The
old comparisons cover emissions, EEUD demand and electricity consumption/generation;
preserve that capability without assuming its exact categories or calculations
are the desired design. Inventory the source evidence and rethink assessment
years, units, boundaries, allocation rules, mapping completeness and missingness.
Do not port the custom ZIP/XML workbook parser by default. Choose the simplest
reader for the agreed reference format; verify any workbook layout, cached
formula values and totals independently of the new calculation tests.

`emissions.csv`, `emissions_concordance_2023.csv` and
`industry_emissions_diagnostic_concordance_2023.csv` have no references in the
current calibration script. Treat them as archive candidates, not automatic
deletions: establish whether they document historical preparation or support
manual analysis. Keep raw workbooks until their derived data can be explained.

`calibration_results.md` is a generated, tracked report with no result manifest
attached. Preserve it as a historical example, clearly identify its inputs if
recoverable, and write new reports to a separate generated-output location.

## Dependencies and output direction

### Publication CSVs belong in PUBLISH

Verified in code: `save_chart_and_data()` renders a PNG, then calls
`save_chart_data()` with the same filename stem and a `.csv` extension. The
latter writes `df.to_csv(index=False)` under
`analysis/results/data_for_charts/`. Subject and sensitivity chart modules call
this helper for demand, emissions, generation, supply, indicators, fleet and
battery/flex views. Thus the old code contains a useful chart-data export
capability, in addition to plotting.

The CSV is the dataframe supplied by each caller, not necessarily a pristine
metric table: timeslice callers can include display columns, signed flows,
equivalent-input conversions and completed zero rows. Battery/demand-flex zero
completion was reviewed when written and is intended export behaviour. Standard area-chart
boundary rows are added inside chart preparation rather than to the supplied
export dataframe. Audit each required export's semantics rather than treating
all files as interchangeable clean results. CSV writing currently follows PNG
rendering, so chart failure prevents that export too.

No active external-chart consumer or upload integration was found by searching
the repository for `data_for_charts` and Datawrapper references. The code proves
the exports exist, but does not establish which were used for publication or
which shapes the current external charting method requires.

Plan: first move the existing publication CSV generation into a small PUBLISH
`reporting` submodule for releases, independently runnable without chart generation.
Inventory and reproduce existing tables, labels, units and shapes, including the
reviewed battery/demand-flex zero completion. Accept named releases and selected
scenarios only; never resolve SOLVE runs in this publication path. New QA reports
retain their separate RELEASE/SOLVE selection.
PUBLISH already exports full-result CSVs through `utilities/output_packaging.py`
and Explorer downloads, but those are not equivalent to subject-specific chart
aggregations. Reuse suitable existing export code without importing UI modules.
Do not move the whole old QA chart stack or retain PNG rendering as a dependency.

QA's own comparison/calibration CSVs remain in QA. Publication data exports belong
in PUBLISH. The inventory's chart/analysis reuse recommendations are subject to
this boundary and do not imply keeping those workflows inside QA.

The current Python code uses pandas, NumPy and Plotnine. Plotnine is declared
only in the root development group, so QA's installed runtime dependencies do not
describe its chart requirements. Declare it in QA if these chart paths remain.

No Python usage was found in QA for `doit`, `plotly`, `polars`, `pygments`,
`python-dotenv`, `seaborn`, `shiny`, `shinywidgets` or `vega`. Review removal after
choosing the report renderer and checking external entry points. Keep the Parquet
engine dependency. Do not add a second dataframe implementation for this cleanup.

For the proposed shareable report, prefer self-contained HTML plus CSV, with
optional existing static charts embedded in the HTML. Plotly is an option if
interaction is useful, not a requirement to rewrite existing Plotnine charts.
Existing Markdown sensitivity reports can stay available during migration.
The integration plan specifies HTML and CSV for the first deliverable.

## Smallest practical migration

First reproduce existing analysis/chart CSV results in the release-only PUBLISH
reporting submodule. Verify against old calculations for the same release and
selections before removing the corresponding QA implementations. Then:

1. Add explicit RELEASE/SOLVE input selection and annual-period validation for
   the new report. Do not update every old `FINAL_DATA` reader as a prerequisite.
   Keep any affected retained commands usable or document their retirement.
2. Extract only the shared metrics needed by the first comparison. Test unit
   conversions, aggregation grain, missing classifications, missing scenarios,
   period alignment and zero-baseline differences with fake dataframes.
3. Generate HTML and CSV from those calculated results. Reuse chart export and
   objective validation, keep presentation zeroes out of comparison data, and
   attach provenance and coverage diagnostics.
4. In a separate follow-up, design and write calibration from scratch using
   explicit model and historical inputs. Review the old mappings and Rankine
   allocation as prior methods, not requirements to preserve unchanged.
5. Only if needed, consolidate sensitivity plumbing and migrate specialist
   battery/flex workflows. Replace their live PREP and archived scenario CSV
   dependencies when migrating them. Remove stubs, unused paths and dependencies
   after checking callers; defer work on code whose future use is undecided.

Changes can reach loaders, subject charts, both sensitivity report/chart pairs,
calibration, output paths, scenario definitions, QA dependency declarations and
README instructions. CI already includes `QA-TIMES-NZ/tests`; no separate test
pipeline is needed. Add QA's missing CI Black/isort/Pylint step later, matching
other modules, and review full-module coverage of any retained scripts outside
`src`. Local changed-file linting already includes QA; its pre-push Pylint target
currently covers `src/qa_times_nz` only. Avoid changes to PUBLISH UI or SOLVE's classification logic
as incidental cleanup. Never delete historical reference data as part of moving
generated reports.

## Verification and limits of this review

Inspected QA source, tests, dependency declarations, reference-file inventory,
entry points and CI test inclusion, with targeted checks against PUBLISH's
timeslice helper. Ran `uv run pytest QA-TIMES-NZ/tests -q`: **3 passed**.
Reproduced the thermal-fuel and annual-only timeslice failures with synthetic
dataframes, without changing source files.

Did not run the full chart/calibration workflows, audit the numerical accuracy
of archived reference workbooks, or verify every historical mapping against its
original publication. The existing passing tests cover objective-report helpers,
not the full analysis calculations. Preserve those assumptions until targeted
tests and an artefact-based manual comparison support changing them.
