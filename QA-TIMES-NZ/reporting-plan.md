# QA reporting integration plan

Status: proposed implementation plan.

## Tasks in order

**1: Recover v308 raw results and matching classifications**

Completed 24 November 2026: recovered all ten release scenarios and recorded the
explicitly approved use of current fuel classifications as a one-off legacy
adjustment. See [the recovery record](v308-recovery.md) for validation and artefacts.

Create `raw_results.parquet` from the archived v308 results for validation.
Do not rerun v308 post-processing: current labels and codes do not match that
release. Identify the archived results and renewable classifications in the
provenance of the recovered data and subsequent v308 summaries.

**2: Standardise annual `Period` types and preserve renewable metadata**

Correct annual `Period` types to integer in SOLVE post-processing before building
summaries. Preserve mixed period values in `raw_results.parquet` and support
existing releases with string years at the loading boundary. Whole-run metrics
such as the objective function do not require an annual period.

PREP's energy commodity metadata must retain the source `Renewable`
classification for generic, sectoral and distribution commodities, so SOLVE's
metadata snapshot supplies the classification without reading the live PREP tree.
Existing snapshots must be checked before calculating indicators; do not silently
substitute current classifications for archived inputs.

**3: Migrate analysis calculations into SOLVE summaries**

Move the existing analysis/chart-data calculations into a SOLVE reporting
submodule operating on postprocessed results. Write `summaries/` alongside
`labelled/`, including the renewable indicators, objective function and every
per-scenario dataset used by the QA demo. New per-scenario aggregations and
calculations belong here; QA calculates differences, tolerances and calibration
assessments. PNG rendering is not needed.

Summary outputs may evolve with the analyses: choose filenames, columns and
breakdowns as each calculation is migrated, without an upfront fixed catalogue
or common schema. Each reader validates the fields it uses. PUBLISH appends
matching summary datasets as it does labelled results and exports the prepared
tables for publication without repeating the calculations.

Zero-fill absent summary rows over the applicable model years and categories by
default, retaining explicit exceptions in the existing analysis scripts. Preserve
reviewed battery/demand-flex timeslice completion and the demo's energy-series
completion. This applies to absent rows, not existing null values, missing source
datasets, invalid mappings or undefined ratios.

Generate summaries within SOLVE post-processing before marking it completed.
Record their relative paths in `postprocessing.files` alongside raw and labelled
outputs. Invalidate completion before a rerun, and remove superseded summaries
only after all replacement writes succeed, before marking completion again.
A failed summary generation must leave the run ineligible for publication or QA.

Reproduce the existing CSV results using v308, independently of PNG rendering,
including units, labels, grouping and zero-filling. Bundle v308 summaries alongside
its labelled results without rerunning its post-processing. One-off v308 backfill
code need not become a maintained compatibility layer; record its inputs and
validation. Retain the old exports until the replacements are validated.

**4: Add QA input selection**

Select `RELEASE` plus release/scenario, or `SOLVE` plus case and optional exact
run timestamp, with resolved inputs shown explicitly. Resolve either source to
its result root and read the same relative `summaries/` dataset paths. QA must
compare a RELEASE baseline with a SOLVE candidate without publishing it first.
Test with synthetic release/run fixtures, including incomplete-run rejection.

**5: Integrate the QA report**

Build on the current demo's tables and charts, reading prepared summaries.
Provide a command such as `qa-times-nz generate_qa --main|--dev`, a tracked main
configuration and a generated, ignored developer configuration. Do not overwrite
an existing developer configuration when generating it.

QA owns input selection and validation, matching supplied year/category keys,
differences, tolerances, calibration assessments and report presentation. Category
completion and zero-filling happen entirely in SOLVE summary generation; remove
the demo's report-side completion. QA does not invent missing rows or zeroes,
including categories appearing only in the other selected run. Unmatched rows
remain visible with N/A comparisons. Write self-contained
HTML and comparison CSVs. If a chart's dataset is unavailable on both sides, show
"no data found"; if available on one side, display that side and N/A comparisons.
Incomplete runs, malformed data and invalid mappings remain input errors.

**6: Rebuild calibration as a report page**

Include calibration in this implementation, comparing model outputs with observed
emissions, demand and electricity data. Use the old code and reports to recover
reference sources and check definitions, then rebuild the assessments with
explicit years, units, boundaries, mappings and missing-data handling. Preserve
source evidence; do not carry over the old parser or assumptions automatically.

**7: Remove replaced code**

Delete the old analysis and calibration implementations after validating their
replacements and checking callers. Preserve historical reference data and move
retained one-off studies before removing their dependencies. Document QA as
housing automated result checks and one-off studies; use `QA-TIMES-NZ/studies/`
for the latter without migrating unrelated calculations as a prerequisite.

**8: Add QA linting to CI**

Add Black, isort and Pylint checks matching the other modules. QA tests already
run in CI; no separate test pipeline is needed.

**9: Rewrite the Sphinx documentation last**

After implementation and validation are complete, rewrite the Sphinx developer
guides to describe the finished SOLVE, PUBLISH and QA workflow, commands and
configuration. Leave this documentation rewrite until all other steps are done.

## Purpose and ownership

QA should produce repeatable reports comparing selected scenarios from existing
result artefacts, including legacy v308 results and current SOLVE outputs.

- SOLVE owns reading solver results, applying the run's reporting metadata, and
  writing raw, labelled and summary Parquets, including per-scenario metrics.
- PUBLISH owns packaging selected outputs into named releases, including legacy
  imports, and serving the Explorer.
- QA owns comparisons, calibration assessments, validation rules and reports.

QA should consume those artefacts directly. It should not maintain another copy
of cleaned results or repeat SOLVE's post-processing.

Keep the first implementation small: one explicit comparison definition, a
plain source resolver, summary readers and an HTML/CSV writer.
Use the existing demo and analysis exports to guide the summaries being migrated.
Preserve publication CSV functionality during migration. Rebuild calibration as
part of delivery; PNG generation is unnecessary.
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

Move per-scenario calculations from `analysis/get_data.py` and the demo into
SOLVE summaries, accepting loaded dataframes explicitly. Keep loading separate
from calculation so functions can be tested with fake data. Handle retained
callers when shared functions change. QA reads these values without repeating
aggregations or unit conversions. Summary shapes remain flexible; validate the
columns, units and unique keys needed by each consuming calculation.

Existing outputs to cover include:

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
not calculations owned by the QA report. Include them under `summaries/`, keeping
scenario identity, integer annual periods and units explicit. Their file and
column layout can follow the migrated analysis. Store shares as decimals from
0 to 1 with unit `Share`.

PUBLISH should preserve and batch the indicator summary datasets in each
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

Use `Renewable` from the run's recorded energy commodity metadata, not the live
PREP working tree. PREP must preserve this field for all energy commodity aliases.
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

SOLVE summaries zero-fill absent rows over applicable model years and categories
unless the existing analysis specifies an exception. QA compares those prepared
zeroes directly, with no report-side category completion or zero-filling. Match
the supplied keys and show unmatched rows with N/A comparisons, including when a
category occurs only in the other run. Keep unavailable source datasets, invalid
classifications and existing null values distinguishable from zero. Show unavailable chart data as
N/A, state the compared years and preserve coverage exceptions from each summary
rather than silently comparing only the intersection.

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

## Delivery verification

Follow the numbered tasks above; summary calculations belong in SOLVE throughout.

- Test period conversion and renewable metadata retention with synthetic inputs,
  including invalid annual periods and generic, sectoral and distribution aliases.
- Test migrated summary calculations with fake dataframes for grouping, units,
  zero-filling and any existing analysis exceptions. Outside pytest, compare v308
  summaries with the existing CSV results for the same scenarios and selections.
- Test summary failure and retry: completion stays invalid until all outputs are
  written, summary paths appear in the manifest, and successful reruns remove
  superseded summaries before marking completion.
- Verify PUBLISH batches the same relative `summaries/` paths without recalculating
  metrics. Publication CSVs consume these prepared tables and preserve provenance.
- Test QA release/run selection, timestamp pinning, old string-year compatibility,
  repeated scenario IDs in different runs, unavailable charts, zero baselines and
  share differences. Verify categories present in only one input remain unmatched
  with N/A comparisons, without inserting zeroes. Check incomplete runs and
  invalid data fail explicitly.
- Generate a Steady v308 versus Steady v309 HTML/CSV report using a SOLVE candidate,
  then repeat with that candidate packaged into a release. The summary values and
  differences must agree; only source provenance should differ. Independently
  verify selected totals against source Parquets outside pytest.
- Deliver the calibration page with synthetic tests for its mappings, units,
  years and missingness. Check selected real observations against their recorded
  reference sources outside pytest before retiring the old calibration code.
- Verify main/dev configuration behavior, offline HTML output and the documented
  command. Add QA linting to CI and remove replaced callers and dependencies only
  after the summary, comparison and calibration checks pass.

Keep pytest independent of local result archives. The completed workflow includes
SOLVE summaries, PUBLISH packaging/exports and QA comparison plus calibration.
A new dashboard, result database, source-provider framework and wholesale rewrite
of specialist studies are outside this scope.

## Publication boundary

PUBLISH consumes packaged summary tables and writes publication CSVs without
requiring PNG generation. It does not own summary calculations or select SOLVE
runs. QA's `RELEASE`/`SOLVE` choice applies to its comparison and calibration
report. QA's HTML/CSV products stay in QA; publication exports stay in PUBLISH.
No new shared package or generic reporting framework is needed.
