# QA-TIMES-NZ


This module contains internal analysis tools. The legacy Explorer has been
removed; the Explorer now lives in `PUBLISH-TIMES-NZ`. `SOLVE-TIMES-NZ` owns
result post-processing.

Analysis scripts still use the old data paths and require archived inputs to run.
Updating them to read PUBLISH releases is deferred.

## QA report

From the repository root:

```bash
uv run qa-times-nz generate_qa
```

This writes `build/report.html` and `build/comparisons.csv`
inside `QA-TIMES-NZ/`. The HTML contains embedded SVG charts, expandable data
tables and selected input identities; it can be shared and
opened offline. The CSV keeps exact prepared values, canonical scenario IDs,
candidate-minus-baseline differences, percentage changes and
nullable tolerance assessments.

The report retains the former demo's Summary, Electricity, Oil and gas,
Renewables and Emissions pages. It reads prepared summary totals and breakdowns
without aggregating, converting units or filling absent rows. Only matching
year/category/unit keys are compared. Unmatched rows and existing undefined
values remain N/A and are unassessed for tolerance. Percentage change is undefined
for a zero baseline; absolute differences and tolerance checks still apply.
Objective differences are descriptive, with no tolerance assessment.

Charts with no data on either side show "no data found". When data exists on one
side, that side remains visible and comparisons show N/A. Invalid data and
incomplete runs are input errors. Charts and tables show units. Demand and
emissions boundaries are documented in `summary-migration.md`.
Renewable generation and TFEC shares use the same relative tolerance as the other
annual metrics. For example, a baseline of 63% and candidate of 76% differ by
13 percentage points and 20.63% relative, exceeding a 5% tolerance. The report
reads prepared `%` rows, shows absolute differences in percentage points and
identifies their units in the CSV's `DifferenceUnit` column. Calibration is step 6.

For a separate developer comparison:

```bash
uv run qa-times-nz init-dev-config
# Edit QA-TIMES-NZ/report_config_dev.toml.
uv run qa-times-nz generate_qa --dev
```

Initialisation copies the validated main configuration and refuses to overwrite
an existing developer file. Main and developer runs write to the same output
files, replacing the previous build. Configurations and generated output
locations are fixed; developer configuration and all generated reports are
Git-ignored.

## QA report inputs

`report_config.toml` selects one baseline and one candidate. Either role can use
either source, independently:

```toml
tolerance = 0.05

[baseline]
source = "RELEASE"
release = "v308"
scenario = "steady-v308"
label = "Steady v308"

[candidate]
source = "SOLVE"
scenario = "steady"
# timestamp = "20261124T010531Z"
label = "Steady development"
```

The tolerance is a finite, non-negative fraction: `0.05` means 5% relative for
the current checks. Selectors reject unknown fields and fields belonging to the
other source type. Labels are optional presentation text; calculations retain
scenario IDs and separate baseline/candidate roles.

RELEASE selects the exact release directory and a scenario ID declared in its
manifest under `PUBLISH-TIMES-NZ/releases/`. SOLVE selects a case through its
manifest under `SOLVE-TIMES-NZ/build/solves/`. Without a timestamp it uses PUBLISH's
latest-completed-run policy at the current workspace version, ranked by execution
completion time. A timestamp pins the UTC token in the run directory name,
including an older version if explicitly selected. Missing or ambiguous pins,
incomplete pinned runs and tied latest runs are errors. A failed pin never falls
back to another run. SOLVE runs must have both completion statuses, all declared
output files and prepared summary CSVs; missing outputs are errors even when a
run says it completed.

The main configuration is the default. `--dev` explicitly selects
`report_config_dev.toml`; a missing requested file is an error with instructions
to initialise it. The Python input interface is also available:

```python
from qa_times_nz.report_inputs import load_summary, resolve_inputs

inputs = resolve_inputs()  # Use resolve_inputs(dev=True) for the developer file.
dataset = "summaries/electricity/electricity_generation.csv"
baseline = load_summary(inputs["baseline"], dataset)
candidate = load_summary(inputs["candidate"], dataset)
```

Resolution prints the exact result roots, scenario IDs, versions and run
timestamps. Result roots, manifests, manifest paths, model versions and pin
timestamps remain internal for loading, validation and diagnostics. The report
shows the input roles, labels, source types, release/run names, scenario IDs
and release/solve completion times, without duplicating the
internal fields or embedding full manifests.

Both sources read the same relative `summaries/<subject>/<table>.csv` paths using
PUBLISH's CSV reader. Reads filter the selected scenario, preserve recorded
values and undefined values, and do not complete categories or years. A missing
optional dataset or no rows for the selected scenario returns `None`. Malformed
data, undeclared scenario IDs and a declared file that disappears are errors.
SOLVE reads only outputs registered by its post-processing manifest. Report
readers additionally validate the required fields, units, classifications and
unique keys. The standalone demo implementation and configuration have been
removed after migrating their retained presentation and comparison checks.

## Solver result bundles

`SOLVE-TIMES-NZ` now writes labelled parquet outputs for every completed model
run. Build and solve a case with:

```bash
uv run --directory SOLVE-TIMES-NZ solve-times-nz solve steady
```

The run directory under `SOLVE-TIMES-NZ/build/solves/` contains the raw `.vd`,
`raw_results.parquet`, the labelled output parquets, and the PREP metadata used
for that run. PUBLISH combines selected run outputs into named releases.

## Explorer deployment

For deployment payloads and deployment instructions, see the internal TIMES-NZ Explorer deployment runbook.
