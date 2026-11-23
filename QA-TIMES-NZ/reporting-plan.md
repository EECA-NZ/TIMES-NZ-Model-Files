# QA reporting integration plan

Status: proposed implementation plan.

## Tasks in order

**1: Create `raw_results.parquet` for v308 to enable its use for validation**

Note: it is very important that we do not rerun v308 post processing, as the codes won't match and everything will break. 

**2: Migrate "analysis" code**

Move the existing analysis/chart data export capability into a new `SOLVE` reporting submodule for releases. 

 - *Requirements:* Operating on `SOLVE` postprocessing, and creating `summaries/` alongside `labelled/`. Preserve reviewed zero-filling behaviour. PNG rendering is not needed. `PUBLISH` ingests and appends these, as it does for labelled results. v308 summaries should be able to be created as well, but we don't need to maintain code that can do this exactly. This includes the existing indicators (such as renewable tfec shares). It should include all the datasets used by QA; a new QA dataset requires any aggregation/calc etc upstream (except for difference/tolerance calcs, which are done by the qa report). This includes surfacing the objective function. 
 - *Validation:* Inventory and reproduce the existing CSV results using the v308 release, independently of PNG rendering. These can be removed on successful validation. In any case, the summary chart data for v308 should be bundled alongside the v308 release. 

**3. Standardise `Period` datatypes.**

Correct annual `Period` types to integer in SOLVE post-processing, while continuing to accept existing releases with string years. This excludes  `raw_results.parquet`, which necessarily contains some strings in there. This should align with older postprocessing methods (`v308` postprocessed results use integers, although the app accepts either.)


**4: QA input selection methods**

Add QA input selection: from the source `PUBLISH` plus release/scenario, or `SOLVE` plus scenario and optional timestamp, with resolved inputs shown explicitly.

Resolve either source to its result root, then read the same relative `summaries/`
dataset paths. QA must be able to compare a RELEASE baseline with a SOLVE
candidate directly, without publishing the solve first. Verify this with synthetic
release/run fixtures, including rejection of an incomplete SOLVE run.

**5: Build QA metrics** 

We have a working demo already, which will be I am sure tweaked and expanded later as we go. But the bones are good. To-do; incorporate correctly into pipeline, ensure that the config is user-specific (ie not git-tracked) by having a "main" config that is git-tracked, and generating a "dev" config for developers to muck around with without messing with git. create a command like qa-times-nz generate_qa --main|--dev. extraordinarily minimal data handling here, everything else should exist. 

QA report handles: 
- Input selection and validation.
- Matching equivalent years/categories between scenarios.
- Differences, tolerances and calibration assessments.
- Tables, charts and report formatting.

In the case where one or either scenarios does not have the data for a requested QA chart, the chart must not fail but instead report that in some way: either "no data found" if both charts are missing, or only displaying one (with no differences) and N/A in the table if only found in one scenario. 

**5: Rebuild calibration metrics** 

as an extra page of the report

**7: Remove all old code**

ie; the analysis scripts are no longer needed and can be deleted. the calibration code is no longer needed and can be deleted. 

**8: add QA missing lint step**

its not in CI. everything else fine. 

**At some point: create QA-TIMES-NZ/studies for all one-off calculations**

This will be a grab-bag of all the random analysis scripts I have foolishly scattered across the repo, centralising and tidying these. The doco for `QA-TIMES-NZ` should describe it as housing "automated testing and one-off studies" of results so that the scope is clear. 



## Purpose and ownership

QA should produce repeatable reports comparing selected scenarios from existing
result artefacts, including legacy v308 results and current SOLVE outputs.

- SOLVE owns reading solver results, applying the run's reporting metadata, and
  writing raw and labelled Parquets.
- PUBLISH owns packaging selected outputs into named releases, including legacy
  imports, and serving the Explorer.
- QA owns metric calculations, comparisons, validation rules and reports.

QA should consume those artefacts directly. It should not maintain another copy
of cleaned results or repeat SOLVE's post-processing.

Keep the first implementation small: one explicit comparison definition, a
plain source resolver, a few agreed metric functions and an HTML/CSV writer.
The metric list below is a shortlist, not a requirement to implement everything.
Preserve the existing publication CSV functionality through the first task;
do not migrate old chart rendering or calibration implementations merely to keep them alive.
Reuse existing code only where it supports a chosen report. Remove clearly unused
code after checking callers; leave uncertain specialist work outside the new
workflow until its purpose is decided.

## Retiring legacy features

The current QA-TIMES-NZ contains: 

 - scripts for compiling reporting summary data, intended for report charts via datawrapper elsewhere
 - a bunch of png generation according to the above
 - old methods for historical year calibration - comparing results to real data
 - old methods for comparing results to other scenarios 

| Capability | Intended destination |
|---|---|
| Reusable per-scenario summaries and renewable indicators | SOLVE post-processing; PUBLISH packages them |
| Standard scenario comparisons and historical calibration | QA reports |
| Bespoke sensitivity valuations, interactions and technology attribution | QA-TIMES-NZ/studies, with explicit scenario selection |
| PREPARE’s standalone analyses | Review and move into the same studies directory |
| External-model comparisons, such as other generation/emissions projections | added to QA report (?) - needs bespoke chart handling, not aligned with report comparisons|
| Old PNG rendering, palettes and plotting-only helpers | Retire once required CSV-producing calculations are extracted |
| Historical reference datasets and concordances | Preserve if used for calibration/external-model comparisons, else delete |


## Result sources and scenario selection

Make source selection explicit and visible in the report definition. Each input
has `source = "RELEASE"` or `source = "SOLVE"`, plus an optional display label.
These resolve to two existing layouts:

- A PUBLISH release: `release-manifest.json` and its processed-result root.
- A completed SOLVE run: `manifest.json` and its `postprocessed/` result root.

Both roots use `raw_results.parquet`, `labelled/` and, when produced,
`summaries/`. PUBLISH preserves dataset paths; its legacy importer moves flat
labelled datasets into `labelled/`. Metadata snapshots stay with SOLVE runs.
QA support for selecting SOLVE runs remains planned.

Reuse PUBLISH's release manifest validation and dataset lookup rather than
creating another release format. Declare the workspace dependency if QA imports
that code; do not depend on Explorer UI modules. For direct SOLVE inputs, check
the run and post-processing completion status before loading results.

Legacy v308 is already imported under `PUBLISH-TIMES-NZ/releases/v308`, so it
can use the same release-loading path as current results. No separate legacy
metric implementation is needed.

For two packaged scenarios:

```toml
[baseline]
source = "RELEASE"
release = "v308"
scenario = "steady-v308"
label = "Steady v308"

[candidate]
source = "RELEASE"
release = "v3.0.9-standard"
scenario = "steady-v3.0.9"
label = "Steady v309"
```

To compare the legacy baseline against an unpackaged solve, replace the candidate
with:

```toml
[candidate]
source = "SOLVE"
scenario = "steady"
# timestamp = "20261112T074405Z"  # Optional exact run timestamp.
label = "Steady development"
```

Resolve releases under `PUBLISH-TIMES-NZ/releases/` and solves under
`SOLVE-TIMES-NZ/build/solves/`. No configurable search paths or alternate layouts
are needed initially.

### Selection rules for the developer

| Source | Required fields | Optional fields | Selection |
| --- | --- | --- | --- |
| `RELEASE` | `release`, `scenario` | `label` | Exact named release and exact scenario ID from its manifest. |
| `SOLVE` | `scenario` (case name, e.g. `steady`) | `timestamp`, `label` | One completed, postprocessed run for that case. Read its versioned scenario ID from the run manifest. |

- Reject unknown source types and fields belonging to the other source type.
  Both sources use `scenario`: RELEASE selects a packaged scenario ID, while
  SOLVE selects a scenario by its case name. Use canonical identifiers from the
  manifests (`steady`, rather than the display label `Steady`); `label` remains
  optional presentation text.
- Without a timestamp, select the latest completed, postprocessed run for the
  case at the current workspace version, following PUBLISH's existing
  `bundle_definition.select_runs()` policy. Do not mix versions silently. Reuse
  that selector where practical rather than introducing another ranking policy.
- With a timestamp, select the exact case/run timestamp, including an older
  version if explicitly pinned. The timestamp means the UTC token in the run
  directory name, not its modification time or execution completion time. Match
  the case through its manifest and reject missing or ambiguous matches.
- An explicitly pinned incomplete run is an error; do not fall back to another
  run. For all selections, validate required outputs before calculating metrics.
- Print the resolved run directory, scenario ID and version before report
  generation and include them in the report's input section, along with source
  manifests and workspace version. Latest selection can change between reports;
  show the exact timestamp needed to pin the selected run for a later comparison.

Keep these rules together in one ordinary resolver function and document them
beside the example configuration. Avoid implicit global scenario maps, source
auto-detection, a selection UI or a generic source-provider framework.

Keep IDs throughout calculations and apply labels for presentation. Identify
baseline and candidate separately even if both refer to the same scenario ID
from different runs; never group them together by scenario ID alone.

## Period types and dataset compatibility

Fix annual period types in SOLVE before building the new reporting path.
The raw `.vd` mixes year values with `-` and `NONE`, so pandas currently reads
the whole `Period` column as strings. That type survives filtering and is written
to annual labelled Parquets.

- Preserve original dimension values in `raw_results.parquet`.
- After selecting annual records, validate and cast `Period` to integer years
  before writing annual labelled datasets. Reject non-year or fractional values
  rather than silently coercing them to null or dropping records.
- Do not require an annual period for whole-run metrics such as the objective
  function. Check each dataset's meaning before applying a conversion.
- Cover the conversion with a small synthetic-data test, including invalid
  periods, and retain existing post-processing checks.

PUBLISH should preserve the resulting schemas. The Explorer already casts
`Period` to integers when loading, so it supports both existing string-year
artefacts and newly corrected outputs.

QA should also validate and normalize annual periods on loading to support
already-created releases. Read existing releases without rewriting them. Any
regenerated SOLVE outputs or release should be created and identified explicitly,
so a previous report's inputs remain traceable.

The v308 and v309 schemas have different auxiliary columns. Validate the columns
required by each metric rather than demanding identical full schemas. Verify
units and required classifications before aggregating; schema compatibility
alone does not establish equivalent metric definitions.

## Shared metrics and comparison behaviour

Adapt calculations from `analysis/get_data.py` only as chosen metrics need them,
accepting loaded dataframes explicitly. Keep loading separate from calculation
so functions can be tested with fake data. Avoid changing old shared interfaces
unless their callers are deliberately being migrated or retired.

Candidate metrics to select from with the human developer:

- Electricity generation totals and generation by fuel, in TWh.
- Energy emissions totals and emissions by sector, in Mt CO2e.
- Final energy demand totals and demand by fuel, in PJ, with exclusions stated.
- Primary energy supply totals and supply by fuel, in PJ.
- Objective function value, as a separate whole-run comparison in NZDb.

Document each metric's filters, grouping, units and exclusions. Compare objective
values only with an explicit understanding of cost, discounting and model-horizon
conventions across the selected runs.

### Reusable renewable-share indicators

Calculate renewable share of TFEC and renewable share of electricity generation
once per scenario/year in SOLVE post-processing. These are reusable indicators,
not calculations owned by the QA report. Write `postprocessed/summaries/indicators.parquet`
with `Scenario`, integer `Period`, `Variable`, `Value` and `Unit` columns. Store
shares as decimals from 0 to 1 with unit `Share`.

PUBLISH should gather the indicators into `summaries/indicators.parquet` in each
release. QA, the Explorer and publication exports should read these same values
rather than implement their own versions. Summary CSVs can export the indicators
without recalculating them.

Use the existing calculations in `analysis/get_data.py` as the starting point,
with synthetic-data tests before moving them:

- Renewable electricity generation share: calculate each plant's renewable
  input-fuel share and apply it to that plant's generation, then aggregate.
  Preserve scenario, year, process, region and vintage matching, mixed-fuel
  handling, and the assumption of equal conversion efficiency across fuels
  within a plant.
- Renewable TFEC share: combine direct renewable final energy use with final
  electricity consumption multiplied by the renewable electricity generation
  share. Preserve the current exclusion of international aviation and shipping
  from both numerator and denominator, and document that boundary explicitly.

Use fuel classifications recorded with the run, not the live PREP working tree.
Validate classification coverage and matching electricity/fuel-use records.
Report an undefined share for a zero denominator rather than silently returning
zero. Test mixed-fuel plants, exclusions, missing classifications, and zero totals.

Backfill the same indicator dataset for v308 using its matching results and
recorded classifications; identify those inputs in the provenance. Confirm
their availability alongside recovery of v308's raw results.

QA should display differences between shares in percentage points. Agree and
label whether the tolerance is relative percent or percentage points before
adding these to the report; do not silently reinterpret the demo's relative
5% tolerance. Add the indicators to QA only after their inputs and definitions
are reproducible.

### Comparison behaviour

Join annual metric results by metric, period, unit and any breakdown dimensions.
Report baseline and candidate values, candidate minus baseline, and percentage
change relative to the baseline. Use percentage-point changes for share metrics.
When the baseline is zero, mark percentage change as undefined and retain the
absolute difference.

Make missing scenarios, required datasets, years and classifications visible.
Distinguish a genuinely absent category from an explicitly reported zero; do not
blanket-fill unmatched comparison rows with zero. State the compared years and
show coverage gaps instead of silently comparing only their intersection.

Differences are descriptive by default. Add pass/fail checks only where a metric
has an agreed expectation and explicit absolute or relative tolerance. Keep
input validity failures distinguishable from tolerance failures.

## Reports and QA cleanup

Provide one command that reads a comparison definition and writes:

- A self-contained HTML report with input provenance, metric definitions, comparison tables
  and validation outcomes.
- A CSV containing the calculated values and differences for further analysis.

Reuse calculation/validation helpers where suitable; HTML does not require a
parallel Markdown renderer. Start with tables; add existing charts only when
they help interpret a metric. Embed any assets so the report can be shared and
opened offline.
Keep generated reports separate from source inputs and out of version control.

There is no commitment to migrate every chart or sensitivity report. If shared
code is changed, fix its retained callers or explicitly retire them in the same
change. Some sensitivity reports read `FINAL_DATA` directly, so changing
`get_times_data()` alone does not migrate those workflows.

Keep calibration checks and external comparison data separate from result-source
loading. Remove obsolete path constants, scripts and dependencies only after
checking their callers; preserve archived inputs until their use is understood.

## Delivery sequence and verification

The task list above sets the order. First reproduce the existing analysis/chart
CSV exports in PUBLISH's release-only reporting submodule. Compare the migrated
tables against legacy calculations for the same release and selections, including
units, labels, grouping and reviewed zero-filling; PNG generation is not required.
Keep exports separate from source Parquets and record the selected release/scenarios.
Then deliver the QA comparison:

1. Correct annual `Period` types in SOLVE, test the shared conversion and affected
   post-processing outputs, and verify compatibility with the Explorer loader.
2. Add explicit release/run selection and dataset validation in QA. Test scenario
   selection, old string-year compatibility and missing-input errors.
3. Agree the small initial metric set, then adapt those calculations and affected retained callers. Use small synthetic
   dataframes for aggregation, unit conversion, missing coverage and zero-baseline
   comparison tests; keep pytest independent of local result archives.
4. Generate the first Steady v308 versus Steady v309 HTML/CSV report, accepting
   either a release or an unpackaged solve as the candidate. Outside
   pytest, check it against the existing local releases and independently verify
   selected totals from their source Parquets.
5. Remove obsolete code made unnecessary by the chosen workflow, document the
   command and source-selection rules in the QA README, and add other metrics
   only when their purpose is agreed. Calibration and specialist sensitivities
   are optional follow-up work, not prerequisites for this report.

The first deliverable is the release-only publication CSV export capability;
the next is one reproducible two-scenario QA comparison using existing
artefacts. A new dashboard, result database, generic plugin framework and bulk
rewrite of old analysis scripts are outside this initial scope.

## Follow-up work and publication boundary

- Add QA's Black, isort and Pylint step to CI, matching the other modules. Local
  pre-commit linting, pre-push tests and CI tests/coverage already include QA;
  `.github/workflows/ci.yml` currently omits its lint step. Review coverage of
  retained scripts outside `src` when adding it. This can follow later.
- Recreate historical calibration checks in QA from scratch. Retain the ability
  to compare model outputs with observed emissions, demand and electricity data,
  but rethink boundaries, reference inputs, mappings, missingness and assessment
  years before defining the new checks. The existing calibration code and reports
  are evidence of past functionality, not the implementation to migrate. Preserve
  useful source evidence without carrying over its parser or assumptions by default.
- As the first task, put the existing publication-oriented CSV generation in a small `reporting` submodule within
  PUBLISH, rather than maintaining the old QA analysis/chart batch. The old
  `save_chart_and_data()` helper does write grouped chart data to CSV alongside
  PNGs, under `QA-TIMES-NZ/analysis/results/data_for_charts/`. Preserve the useful
  export capability for external charting, inventorying the existing tables
  before porting their transformations. CSV production must work independently
  of chart rendering. No active external-chart consumer was found in the repo.

PUBLISH reporting must consume releases only and record their provenance. It
must not select SOLVE runs or use a fallback to unpackaged results. QA's
`RELEASE`/`SOLVE` choice applies to QA reports only. The reviewed battery and
demand-flex timeslice completion treats missing rows as zero; preserve this
intended behaviour in those publication exports. This rule does not apply
automatically to other datasets or missing QA inputs.

QA owns calibration, validity checks and scenario differences; its
HTML/CSV outputs remain QA products. PUBLISH owns publication tables, labels and
exports for external charts. SOLVE continues to own labelled result production.
Existing PUBLISH full-results CSV downloads do not replace the old subject-specific
aggregations. Do not introduce a shared package or dependencies between QA and
publication formatting in anticipation of overlap; share a calculation only when
both workflows have a concrete need for the same definition.
