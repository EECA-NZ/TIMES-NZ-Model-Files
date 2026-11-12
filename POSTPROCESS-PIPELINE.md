# Post-processing pipeline implementation plan

## Decision

Make `SOLVE-TIMES-NZ` the owner of post-processing and of a versioned
parquet-results release. Keep `TIMES-NZ-INTERNAL-QA` in this repository for
the first phase, but change it to consume the release contract only. Move the
app to its internal repository only after that works in this repository.

The target dependency direction is:

```text
PREPARE-TIMES-NZ -> SOLVE-TIMES-NZ -> parquet release -> internal QA app
```

`PREPARE-TIMES-NZ` remains unaware of solver results and the app. The app
must not import model-repository Python packages or read preparation/solver
directories.

## Current state and migration boundary

`solve-times-nz solve` currently runs GAMS and GDX2VEDA, then writes VEDA
result files and a solver manifest to
`SOLVE-TIMES-NZ/build/solves/<case>-v<version>-<run-id>/`. The current QA
post-processor independently discovers VEDA files under a user's Windows
mount, imports a fixed scenario batch, reads PREPARE intermediate files and
local concordance patches, then writes ignored parquet files under
`TIMES-NZ-INTERNAL-QA/data/clean_results`.

Phase 1 keeps the VEDA result *format* and its existing parser. It removes the
QA-side VEDA discovery and makes post-processing consume the exact solver-run
directory. Replacing GDX2VEDA or the VEDA format is explicitly out of scope.

## Release contract

Each successful post-processing run writes a complete, immutable release below
its solver run:

```text
SOLVE-TIMES-NZ/build/solves/<run>/
  manifest.json
  *.vd, *.vde, *.vds, *.vdt
  postprocessed/
    release-manifest.json
    <current parquet output files>
```

Do not change the raw file locations or delete them. `postprocessed/` is only
publishable when all required files and validations succeed. A future artifact
copy/upload step may publish this directory elsewhere; `build/solves` itself
is generated and is not the durable release store.

`release-manifest.json` must contain:

- a contract/schema version;
- the source solver-run path and a reference to its manifest;
- case name, run identifier, source result files, and SHA-256 hashes;
- post-processing source revision/version and timestamp;
- the PREP reporting-manifest path and SHA-256 hash, including its declared
  preparation inputs and source-coverage results;
- scenarios represented in the release;
- every parquet filename, its SHA-256 hash, and its column names/types;
- successful validation/coverage results.

Use this manifest as the app's source of available scenarios and expected
files. Do not retain a separate hard-coded app scenario list as the source of
truth.

## Implementation phases

### 1. Publish a PREP reporting-metadata contract

Do not move the current definition builders unchanged. They reconstruct a
reporting taxonomy from scattered stage 2, 3, and 4 files; interpret generic
configuration metadata and TOML; infer transport labels from code names; and
apply QA-local patches. That makes `TIMES-NZ-INTERNAL-QA` the accidental owner
of model identity and creates a backwards flow when it copies concordances into
PREP documentation.

Instead, add a reproducibly generated PREP artifact directory, initially
`PREPARE-TIMES-NZ/data_intermediate/postprocessing_metadata/`. It is a defined
PREP output, not a manually maintained directory. Its manifest and tables are
the only PREP data post-processing may read.

The initial contract contains small CSVs organised by reporting domain, rather
than one sparse universal catalog:

- `process_units.csv`: process code and shared activity/capacity units;
- `demand_processes.csv`, `electricity_generation_processes.csv`,
  `primary_production_processes.csv`, `transformation_processes.csv`,
  `distribution_processes.csv`, `battery_processes.csv`, and
  `technical_processes.csv`: only the labels meaningful for each process
  domain;
- `energy_commodities.csv`, `demand_commodities.csv`,
  `emissions_commodities.csv`, and `currency_commodities.csv`: only the
  labels meaningful for each commodity domain;
- `timeslices.csv`: `TimeSlice`, `YearFraction`, explicit TIMES order, and
  required display fields;
- explicit exception catalogues where a model code cannot be described from
  normal preparation data; each exception must state its rationale and source;
- `reporting_manifest.json`: schema version, PREP revision/configuration
  identity, table schemas, table hashes, and source-coverage/validation
  results.

PREP owns model-derived reporting identity: what every process and commodity
means within its reporting domain. Post-processing owns only result
interpretation: which result attributes form demand, capacity, emissions, and
other published measures. The app owns presentation only.

Before writing these artifacts, freeze a baseline from the current QA pipeline
for representative cases: output schemas, row counts, unmatched model codes,
and representative values. Inventory every current concordance field used by
post-processing, calibration, analysis, and the app; the catalog schemas must
cover the required fields without expanding into a generic data dump.

Implement the PREP writers in its normal pipeline using the existing
script-I/O and dataframe-transformation boundary. Add schema, uniqueness,
referential-integrity, and coverage checks. In particular, fail on duplicate
keys within a domain, unintended overlap between incompatible process domains,
missing required labels/units, invalid timeslice fractions, or model codes not
represented by a declared entry, a tested deterministic naming rule, or a
deliberate exception. Do not edit
`data_intermediate` artifacts manually.

Move transport labels into transport preparation rather than inferring them
from `TechName` downstream. Similarly, emit electricity plant and technology
labels where those processes are prepared rather than reconstructing them from
multiple stage files. Retire a QA-side patch only when the equivalent PREP
artifact has baseline-parity coverage and an explicit provenance rule.

### 2. Extract a solver-owned post-processing package

Once the PREP contract is available, move the producer-only result reader,
transformations, validations, and release writer into
`SOLVE-TIMES-NZ/src/solve_times_nz/postprocessing/`. It must consume the
reporting-metadata directory and its manifest, not scattered PREP stages or
QA-local concordance paths.

Keep Shiny modules, `app.py`, assets, UI helpers, deployment files, and
app-specific tests in `TIMES-NZ-INTERNAL-QA`. Decide separately whether
calibration checks and analysis scripts are model QA consumers (keep here) or
app/research consumers (move later); do not leave either importing the old QA
producer package.

Replace physical assumptions such as `QA_LOCATION.parent / "PREPARE-TIMES-NZ"`
with solver-owned path resolution. The initial default can be the workspace
`PREPARE-TIMES-NZ` directory, but require clear errors for missing reporting
metadata and centralise that resolution in one place. Avoid a new configuration
framework.

Move the required dependencies (`numpy`, `pyarrow`, `polars`, and any retained
producer dependencies) from the QA project into `SOLVE-TIMES-NZ/pyproject.toml`.
Regenerate the workspace lockfile.

### 3. Process explicit solver results

Add a callable post-processing entry point that accepts:

- one completed solver-run directory;
- the preparation root; and
- an output directory, defaulting to `<solver-run>/postprocessed`.

It must read result files from that supplied directory only. Remove the
Windows-user lookup, VEDA directory scan, and latest-file selection from the
production path. Fail if the run manifest does not report a completed solver
run, result files are absent, or required preparation inputs are absent.

The existing code batches eight configured scenarios, while one solve produces
one case/run. Refactor transformations to process the scenarios present in the
provided result files and derive their identity from supplied run metadata.
Do not silently label a case as an old `current_scenarios` value.

### 4. Wire it into `solve-times-nz solve`

After `_copy_veda_results()` returns successfully, invoke the new
post-processing entry point with its returned result directory.

Preserve failure semantics:

| Condition | Solver-run result | Command result |
| --- | --- | --- |
| GAMS/GDX2VEDA fails | retained, `execution.status` records failure | non-zero |
| Solver succeeds, post-processing fails | retained raw results; manifest records `postprocessing: failed` | non-zero |
| Both succeed | raw results and complete `postprocessed/` release retained | success |

Post-processing must write to a temporary sibling directory and atomically
rename it to `postprocessed/` only after all outputs, checks and manifest
creation succeed. A failed or interrupted run must not look publishable.

Use the existing solver `manifest.json` as the parent provenance document.
Add a `postprocessing` section rather than overwriting `execution` or
duplicating solver provenance.

An explicit `postprocess` CLI subcommand is useful for retrying a completed
run after a code fix. It must use exactly the same implementation as the
automatic `solve` step.

### 5. Establish the app-consumer contract in place

Change the existing QA app's file-path/config layer to accept a release
directory containing `release-manifest.json` and parquet files. Initially it
may default to a local test release path, but no app module may import
`solve_times_nz`, read raw VEDA files, or reach into `PREPARE-TIMES-NZ`.

Load the available scenarios from the release manifest. Validate required
files, checksums, and app-required columns at startup, producing a clear
operator error rather than an exception later in a reactive.

For the first working release, produce all current parquet outputs, including
those not shown in a primary UI tab. The current download endpoint packages
every parquet file and calibration/analysis scripts consume additional outputs.

### 6. Support comparisons deliberately

A solver run represents one case, whereas the current app compares multiple
scenarios in combined parquet files. Do not reintroduce a hidden fixed batch.

#### Solver batches and QA batches are separate

Add a solver-owned batch command (for example,
`solve-times-nz batch <batch-config>`) only after the per-case pipeline works.
Its configuration selects case definitions to build, solve, and
post-process. It is an operational orchestration input, not an app-release
definition. Each member must run through exactly the same per-case pipeline as
`solve-times-nz solve <case>` and produce its own immutable release.

The solver-batch manifest records each requested case, its resulting solver-run
directory, per-case release location, and status. A failed member leaves its
raw and successful per-case artifacts intact and makes the solver batch
incomplete; it must not discard successful members. Start sequentially until
the Windows/GAMS executor is demonstrated safe for parallel solves.

A QA/app batch is a separate, consumer-facing manifest that selects compatible
per-case releases, assigns display labels/order, and declares the permitted
comparisons. An assembly command may accept a completed solver-batch manifest
as a convenient input selector, but it must validate each selected release
instead of assuming all solver-batch members are comparable.

Choose and implement one explicit app-release composition policy before moving
the app:

1. The app accepts a manifest listing multiple per-run releases and combines
   them at read time; or
2. A solver-owned assembly/publish command accepts selected completed runs and
   creates one multi-scenario app release.

The recommended initial policy is option 2. It keeps per-run releases
immutable, makes cross-scenario comparison a deliberate selection, and can
reject runs with incompatible model/preparation/post-processing versions.

### 7. Move the app only after the contract is proven

Once the app can run against a release produced by `solve-times-nz solve` (and
the selected comparison release), lift and shift the remaining
`TIMES-NZ-INTERNAL-QA` app into the internal repository. Move its assets,
deployment configuration, requirements, app-only helpers, and tests together.

Then remove the QA workspace member, root dependency, pre-commit module entry,
and documentation references from this repository. Keep post-processing and
its tests here.

## Required checks

Add small fixture-driven tests; do not depend on local VEDA, GAMS, or generated
PREPARE data in pytest.

- A PREP reporting-artifact test using small source dataframes: schema,
  uniqueness, required-label, timeslice, exception, and model-code coverage
  checks; plus a baseline-parity comparison before retiring each old QA patch.
- A post-processing unit test using synthetic VEDA-shaped rows and synthetic
  reporting-metadata inputs, asserting expected parquet rows and types.
- A release-contract test asserting required files, manifest metadata, hashes,
  scenario identity, and required app columns.
- A `solve` orchestration test using the existing injectable process runner:
  successful solver results invoke post-processing with the copied result
  directory; a post-processing error retains raw results and returns failure.
- An app-consumer test using a minimal valid release fixture, plus a clear
  failure test for a missing/incompatible manifest/file/column.
- One end-to-end manual acceptance run on a real completed solve before
  deleting QA-side processing code: compare parquet row counts, schemas, and
  representative values against the existing output for the same scenarios.

## Completion criteria

- `solve-times-nz solve <case>` retains raw result files and either creates a
  complete contract-valid parquet release or exits non-zero with no publishable
  partial release.
- Every release is traceable to exact solver, preparation, and post-processing
  inputs.
- PREP owns a contract-valid reporting-metadata artifact, including documented
  deterministic lookup rules where appropriate; post-processing has no direct
  reads of scattered PREP stage directories or QA-side concordances.
- The existing app starts and supports its intended comparisons using only a
  release artifact.
- No code in the app imports the producer package or reads PREPARE/SOLVE/ raw
  VEDA paths.
- The app can be moved to a separate repository without changing the release
  contract.

## Explicit non-goals

- Replacing GDX2VEDA or changing the raw result format.
- Redesigning visualisations, release storage, authentication, or deployment.
- Generalising arbitrary external preparation locations beyond the one explicit
  preparation-root input.
- Migrating calibration and analysis scripts until their ownership is decided.
