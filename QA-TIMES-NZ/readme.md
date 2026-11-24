# QA-TIMES-NZ


This module contains internal analysis tools. The legacy Explorer has been
removed; the Explorer now lives in `PUBLISH-TIMES-NZ`. `SOLVE-TIMES-NZ` owns
result post-processing.

Analysis scripts still use the old data paths and require archived inputs to run.
Updating them to read PUBLISH releases is deferred.

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

The main configuration is the default. `report_config_dev.toml` in this directory
is Git-ignored; `dev=True` explicitly selects it, and a missing requested file is
an error. This step does not create the developer configuration. The report
command, its `--dev` option and developer-config generation belong to step 5.

For now, use the Python interface from the repository root:

```python
from qa_times_nz.report_inputs import load_summary, resolve_inputs

inputs = resolve_inputs()  # Use resolve_inputs(dev=True) for the developer file.
dataset = "summaries/electricity/electricity_generation.csv"
baseline = load_summary(inputs["baseline"], dataset)
candidate = load_summary(inputs["candidate"], dataset)
```

Resolution prints the exact result roots, scenario IDs, versions and run
timestamps. Each resolved input retains its source manifest, manifest path,
workspace version and display label for report provenance. Legacy release model
versions are left unrecorded if absent from the release definition; the release
name and scenario IDs remain available in its manifest.

Both sources read the same relative `summaries/<subject>/<table>.csv` paths using
PUBLISH's CSV reader. Reads filter the selected scenario, preserve recorded
values and undefined values, and do not complete categories or years. A missing
optional dataset or no rows for the selected scenario returns `None`. Malformed
data, undeclared scenario IDs and a declared file that disappears are errors.
SOLVE reads only outputs registered by its post-processing manifest. Each report
reader must additionally validate the columns, keys, units and mappings it uses;
report comparisons and rendering remain step 5.

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
