# QA-TIMES-NZ

**Draft developer guide — proposed workflow, not yet implemented.**
The examples below describe the intended report configuration. There is no QA
report command yet; the initial metrics and command interface still need to be
agreed. Existing analysis scripts do not support this configuration.

QA-TIMES-NZ will compare high-level results from two selected scenarios and
produce a report that you can share with colleagues. Use it to review changes
between model versions, compare development runs, or check a candidate against
an agreed baseline.

SOLVE produces the result datasets. PUBLISH packages scenarios into releases.
QA reads those results directly and calculates comparisons; you will not need
to publish a release before checking a development solve.

## Choose the results to compare

A report definition is a small TOML file with a `baseline` and a `candidate`.
Each has a `source` and a `scenario`. Either input can come from a release or
from a completed local solve, independently of the other input.

| Field | `source = "RELEASE"` | `source = "SOLVE"` |
| --- | --- | --- |
| `scenario` | Required: exact scenario ID in the release manifest. | Required: scenario case name, such as `steady`. |
| `release` | Required: release directory name. | Omit. |
| `timestamp` | Omit. | Optional: exact UTC timestamp token from the run directory name. |
| `label` | Optional display name in the report. | Optional display name in the report. |

Use canonical identifiers, including their case. For example, `steady` is the
SOLVE case name; `Steady` is a display label. Release scenario IDs include the
version as recorded in their manifest, such as `steady-v308` or
`steady-v3.0.9`. Labels do not select results.

### Compare two releases

This example compares Steady v308 against Steady v309:

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

Releases are resolved under `PUBLISH-TIMES-NZ/releases/`. Check
`release-manifest.json` inside the release for the available scenario IDs.
QA will read its labelled Parquets and validate the requested scenario and
datasets. Legacy v308 results already use this release layout; they do not
need a separate QA mode.

### Compare a release with a development solve

Keep the baseline above and replace the candidate with:

```toml
[candidate]
source = "SOLVE"
scenario = "steady"
label = "Steady development"
```

Solves are resolved under `SOLVE-TIMES-NZ/build/solves/`. With no timestamp,
QA will select the most recently completed run for `steady` at the current
workspace version from the root `pyproject.toml`. Both execution and
post-processing must be marked complete in the run manifest.

“Most recent” means the manifest's `execution.completed_at`, following the
existing PUBLISH selection policy. Filesystem modification times and the time
post-processing was rerun do not determine selection. Failed and unfinished
runs are ineligible. Tied latest completion times are an error.

This is convenient while developing, but another solve can change what the
same definition selects. The report will show the exact selected run.

### Pin a particular solve

Add `timestamp` when you want a specific run:

```toml
[candidate]
source = "SOLVE"
scenario = "steady"
timestamp = "20261112T074405Z"
label = "Steady selected run"
```

Here the timestamp is the `20261112T074405Z` token in a directory such as
`steady-v3.0.9-20261112T074405Z`. It is not the execution completion timestamp.
The scenario is checked against the run manifest. A pinned run can be from an
older workspace version.

A missing, incomplete or ambiguous pinned run will stop report generation;
QA will not substitute another run. Latest selection also stops if no eligible
run exists at the current version. Missing required outputs are an error.

For two development solves, use `source = "SOLVE"` in both sections. Pin at
least the baseline so that a newer solve does not move the comparison target.

## Review and share the report

The intended workflow is:

1. Produce a completed SOLVE run or obtain an existing PUBLISH release locally.
2. Write the two input selections and choose the agreed report metrics.
3. Generate the report once the QA command is available. Check the printed
   resolved inputs before interpreting the results.
4. Review input coverage and validation messages, then the metric differences.
5. Share the HTML report and its CSV; keep the definition and source artefacts
   if you need to repeat the comparison.

The HTML will be self-contained, including any charts, so recipients can open
it offline without Python or the repository. The CSV will contain the same
calculated values for analysis in Excel or other tools. Output filenames and the
command syntax remain to be defined.

The report will identify baseline and candidate, selected scenario IDs, exact
run/release locations, workspace version and source manifest information. When
latest selection was used, it will show the timestamp needed to pin that run.
The same scenario ID can occur in two different runs; the report must keep the
two inputs separate.

A timestamp identifies a local run; it does not give colleagues access to its
files. Share the source artefacts as well when they need to reproduce the report.
Do not edit generated Parquets to make a comparison work.

## Interpret the comparisons

The first report will contain a small agreed set of metrics. Candidates include
electricity generation, energy emissions, final energy demand, primary energy
supply and whole-run objective value. This is not a committed metric catalogue.

Annual comparison tables will show baseline and candidate values, units,
candidate minus baseline, and percentage change relative to baseline. Percentage
change is undefined when the baseline is zero; the absolute difference remains
available. Share metrics use percentage-point changes. Objective value is a
whole-run metric and requires compatible cost, discounting and horizon
conventions.

SOLVE summaries zero-fill absent rows over applicable model years and categories,
preserving exceptions specified by the existing analyses. QA compares those
prepared zeroes. Missing source datasets, invalid classifications and existing
nulls remain distinguishable from zero. Check years, exclusions and grouping
before interpreting totals across versions. Additional columns do not themselves
make a metric incomparable.

Differences are descriptive unless an explicit expectation and tolerance have
been agreed. A large change can be intentional. A small change does not establish
that inputs, mappings or coverage are correct. Input validity failures and
metric tolerance failures will be reported separately.

## Implement or extend a metric

Keep source selection visible in one ordinary resolver. It should validate the
two source types and their fields, resolve the manifests and required datasets,
and return the selected input to the calculations. Reuse existing PUBLISH
release validation and latest-run selection where practical; avoid depending on
Explorer UI modules.

Write per-scenario metric calculations in SOLVE as small functions accepting
dataframes, with file loading and writing separate. Summary filenames and shapes
can evolve with the analyses; each reader validates the fields it uses. State
units, filters, grouping and exclusions. QA reads prepared summaries and calculates
comparisons and calibration assessments, using the same values for HTML, CSV
and charts. PUBLISH batches summaries and exports prepared publication tables.

Annual labelled SOLVE outputs should have integer `Period` values. This requires
an upstream post-processing change: raw `.vd` periods also contain `-` and
`NONE`, which currently cause string years to propagate. Preserve raw dimension
values in `raw_results.parquet`, and validate/cast periods after selecting annual
records. QA should also accept and validate integer year strings from existing
artefacts. Reject fractional or non-year values in annual metrics. Whole-run
metrics need not have an annual period.

Avoid relying on the current PREP working tree for a historical report's
classifications or timeslice weights. Use recorded reference inputs. Renewable
share metrics need this resolved before becoming standard report metrics.

Test new calculations and selection rules with small synthetic inputs, including
missing coverage and invalid periods. Use the root uv environment. Keep tests
independent of local releases; verify selected real totals separately against
source Parquets when introducing the report.

Reuse old QA functions where the report needs them. Historical calibration is
included as a report page and will be redesigned from the recorded source
evidence. Old code and reports document prior checks rather than prescribe the
replacement. Specialist sensitivities remain separate studies.

The old chart batch also exports CSVs of its supplied chart data. Migrate those
calculations into SOLVE summaries after correcting annual periods and preserving
renewable classifications in the metadata snapshot. PUBLISH exports the prepared
tables from releases without PNG rendering or repeating calculations. Preserve
existing export definitions and zero-filling. QA retains CSVs supporting its own
comparisons and calibration. Retire old code after validating its replacement.

## Related developer documentation

- [SOLVE post-processing](../solve_times_nz/postprocessing.md)
- [PUBLISH releases](../publish_times_nz/index.md)

The implementation plan remains in the `QA-TIMES-NZ` root as `reporting-plan.md`.
