# Publish and QA restructuring plan

## Decision

Create two workspace modules with deliberately different responsibilities:

- `PUBLISH-TIMES-NZ` turns completed solver output into named release
  artefacts.  It owns the Explorer and its standard charts.
- `QA-TIMES-NZ` is the renamed remainder of `TIMES-NZ-INTERNAL-QA` after the
  Explorer is extracted.  It retains technical analysis and non-published
  reporting, which consume PUBLISH release artefacts; it does not include the
  current calibration code.

`SOLVE-TIMES-NZ` remains the owner of one immutable model run and its
`postprocessed/` output.  `PREPARE-TIMES-NZ` remains the owner of input
preparation and reporting metadata generation.

```text
PREPARE + SOLVE ──> PUBLISH release artefact ──> Explorer / QA analysis
```

This separates release production from technical checking without requiring
QA to know how a model run was built.  QA may produce reports, charts, or
other material for internal use, but it must not produce an artefact on which
PUBLISH, the Explorer, or another workflow relies.

## Current and legacy result paths

`TIMES-NZ-INTERNAL-QA/data/clean_results/` is the legacy Explorer data
location.  The former legacy postprocessor populated it with labelled,
scenario-batched parquets for the app.  That postprocessor is no longer the
active path; the existing v308 parquets remain as an untracked legacy result
set and are the input to a one-time imported v308 release.

The active `SOLVE-TIMES-NZ` postprocessor now writes the same family of
labelled topic parquets into one completed run's
`build/solves/<run>/postprocessed/` directory, alongside that run's raw
results and metadata snapshot.  Each new run normally supplies one scenario.

PUBLISH must not reproduce either postprocessor's calculations.  It validates
and combines the already-labelled per-run files into a named release, while a
legacy v308 import validates and adopts the existing multi-scenario files.
This is the only intended transformation between solver post-processing and
the Explorer release.

## Scope and non-goals

This change reaches the following current surfaces:

| Surface | Change needed |
| --- | --- |
| Root workspace | Add `PUBLISH-TIMES-NZ`; rename the `times-nz-internal-qa` workspace member/source to `qa-times-nz`. |
| Current Explorer | Move `app/`, app helpers, Explorer utilities, assets, deployment entry point, requirements export instructions, and associated tests to `PUBLISH-TIMES-NZ`, excluding the developer view. |
| Current QA | Rename the remainder of `TIMES-NZ-INTERNAL-QA` to `QA-TIMES-NZ` and its Python package to `qa_times_nz`; retain technical analysis and non-published reports, and make their common loader read one or more explicitly selected PUBLISH releases. |
| Data access | Replace the hard-coded `FINAL_DATA` path and static v308 scenario list with a selected release-artifact path and manifest-driven scenarios. |
| Calibration | Remove the current calibration script and its data/results from the migration. A future calibration rebuild is a separate project. |
| Documentation and CI | Update root README, module READMEs, deployment commands, uv workspace/package names, and import paths. |

Non-goals for this restructure:

- Do not change solver post-processing calculations to reproduce v308.
- Do not commit parquet files to a module repository.
- Do not redesign individual charts, add a generic reporting framework, or
  make QA reports public.
- Do not build new release reports in this change.  A comparison report and
  any HTML/PDF rendering are follow-up work.
- Remove the Explorer developer view rather than publishing its dummy or
  capacity datasets. Future internal inspection belongs in `QA-TIMES-NZ`.
- Do not migrate, preserve, or replace the current calibration report.  Its
  replacement will be designed after the release workflow is working.
- Do not delete current modules or deployment configurations until their
  replacements have passed the migration checks below.

## Release artefact contract

`PUBLISH-TIMES-NZ/releases/` is the initial release root. It is Git-ignored
and holds complete, named local release artefacts, including labelled and raw
parquets plus any future artefacts placed in the bundle. It is the canonical
local source for the Explorer and QA during development. A future external
artefact store can copy or mirror these unchanged release directories without
changing their format; store authentication, retention, and transfer mechanics
are outside this plan.

A release is not the same thing as an rsconnect deployment payload. This PR
uses a complete named release to wire the app. A later deployment may copy or
mount a compatible, deliberately trimmed Explorer payload for performance,
while retaining the complete release elsewhere. That optimisation is not
designed or implemented here.

Each published release has this logical layout:

```text
<release-name>/
  bundle.json
  labelled/
    elec_generation.parquet
    energy_demand.parquet
    ...
  raw/
    raw_results.parquet              # optional for legacy releases
```

The published layout is deliberately **scenario-batched by dataset**: one
`labelled/<dataset>.parquet` contains rows for every scenario in that release,
identified by its `Scenario` column.  This is the layout the existing Explorer
and chart code already expects.  It is independent of how an input arrived:

- legacy v308 inputs already contain multiple scenarios in each topic parquet;
- each new solver `postprocessed/` directory normally contains one scenario;
- the release builder appends the same named topic parquet from each selected
  new run to create the one scenario-batched published parquet.

For example, assembling a release from new `steady` and `shift` runs writes
one `labelled/energy_demand.parquet` with both `Scenario` values, not separate
per-scenario files.  A legacy v308 import validates and adopts its existing
multi-scenario topic parquets into this same canonical layout.  Consumers
always filter the `Scenario` column; they never infer scenario identity from
the directory or filename.

Every Parquet below a release directory is part of that release. PUBLISH does
not maintain a list of permitted filenames, schemas, or a raw-results flag in
the manifest. For each matching labelled source filename, PUBLISH reads the
file from every selected new run, validates its `Scenario` values,
concatenates the rows, and writes one new compressed Parquet in the staged
release. This is deliberately a data-copying operation; Parquet files cannot
be safely combined by concatenating their bytes. A legacy multi-scenario file
already has the target layout, so PUBLISH validates then copies it into the
release without rewriting it. `raw_results.parquet`, when present, follows the
same row-concatenate-and-write rule under `raw/`.

`bundle.json` is the stable contract.  It must include:

- release format version and release name;
- all scenario IDs and display labels;
- source run identities, or a legacy source identity;
- creation time.

It must also identify whether the release is built from selected solver runs
or is an imported legacy result set. An imported v308 release records its
legacy source; it must not claim source run identities it does not have.

The release does not include PREP metadata snapshots in this migration: the
Explorer and retained QA analysis do not consume them, and calibration is being
removed. Add a specific metadata artefact later only when it has a consumer.

`raw_results.parquet` is included for new releases when it is available. It is
an optional audit dataset, not an Explorer input and not a prerequisite for
legacy v308 support. Its availability is determined by finding the file in the
release, not by a manifest declaration.

## `PUBLISH-TIMES-NZ`

### Responsibilities

1. Assemble a release under the Git-ignored `releases/` root from selected
   solver `postprocessed/` directories, and validate it before it becomes
   visible as a named release.
2. Import the existing v308 clean-result parquets as a named legacy release;
   preserve their scenario IDs, record their legacy lineage, and make it
   usable through exactly the same release interface as a new release.
3. Serve the selected release in the Explorer and make every release Parquet
   available to standard charts and downloads.

### Assembly rules

- Carry every source Parquet into the release; do not maintain a filename
  allow-list or a central dataset-schema declaration. Keep scratch files and
  unrelated Parquets outside the selected source or release directory.
- Group labelled source files by topic filename, then concatenate every selected
  scenario's version of that topic into one scenario-batched labelled parquet.
  Validate `Scenario` values and preserve all source columns without creating
  a separate schema-version system.
- For an already batched legacy source, validate its `Scenario` values and
  copy it into the release; do not split it into temporary scenario-specific
  artefacts merely to reassemble it.
- A release is either one imported legacy result set or a batch of new solver
  runs. Do not combine legacy and new sources in one release in this migration.
- Reject duplicate scenario IDs before writing a release. This check applies
  both within a legacy batched source and across source runs. A consumer that
  needs a particular labelled Parquet reports clearly when it is absent.
- Stage to a new directory under `releases/` and publish only after
  validation. Never overwrite an existing release name.
- Preserve raw scenario identifiers in parquets. Display labels belong in the
  manifest, not in transformed source data.

### Explorer

- The Explorer reads one configured release path and uses `bundle.json` for
  its scenario selector. It has no `clean_results` fallback: create and prove
  the v308 legacy release before moving the Explorer.
- Move the app and its helpers with the Explorer. A
  chart's data remains a labelled parquet, so QA charts and Explorer downloads
  share the same canonical source.

### Explorer release seam

The current Explorer is coupled to the legacy location in two ways:

- `utilities.filepaths.FINAL_DATA` is the fixed
  `data/clean_results/` directory. The five main Explorer modules construct
  parquet paths from it at import time, and the download-all action zips every
  parquet it finds there.
- `config.current_scenarios` is a fixed v308 scenario list. The scenario
  selector uses it, while `utilities/value_mappings.json` supplies the legacy
  display names.

Replace those with one small release seam in PUBLISH. The app receives one
explicit release directory through deployment/local configuration (for
example, `TIMES_NZ_RELEASE_PATH`); it must never discover the newest directory
under `releases/`. At application startup, the seam loads and validates
`bundle.json`, verifies the format version, and fails with a clear error when
the release has no Parquet data.

The seam exposes only:

- `labelled_file(dataset_name)`, which returns a file below `labelled/` and
  fails clearly when that chart's file is absent; and
- ordered raw scenario IDs and display labels from `bundle.json`.

Each Explorer module replaces its `FINAL_DATA / "<topic>.parquet"` constant
with `labelled_file("<topic>.parquet")`. The scenario selector reads the
manifest scenarios directly; remove `current_scenarios` from PUBLISH and do
not use the legacy `Scenario` mapping from `value_mappings.json` there. Keep
the other value mappings unchanged. The download action receives the release's
discovered Parquet files, including raw results and future Parquet artefacts.

Remove `app_module_developers.py`, its developer-only UI/server wiring, dummy
parquets, and the infeasibilities information asset from PUBLISH. Do not
replace them with release datasets or a parent-directory inference. Future
inspection of capacity or other technical outputs belongs in `QA-TIMES-NZ`.

The retained QA analysis must remain runnable after the rename. Replace its
common `FINAL_DATA` access with one or more explicit PUBLISH release paths and
use the public bundle loader rather than duplicating manifest parsing. QA may
depend on that public PUBLISH reader, but PUBLISH must not depend on QA.
Existing analysis-specific scenario maps may remain where they express a chart's
comparison, but the common loader must not hard-code v308 as its source.
This makes internal analysis able to compare an imported v308 release with a
new release without making QA a release producer. Update or retire the PREP
residential analysis separately if it is intended to remain runnable.

### Suggested package shape

```text
PUBLISH-TIMES-NZ/
  releases/                         # Git-ignored named release bundles
  src/publish_times_nz/
    app/
    release_bundle.py
    cli.py
  tests/
  app.py
  run_local.py
  assets/
  www/
  requirements.txt
  rsconnect-python/
  readme.md
  pyproject.toml
```

Expose only the small commands needed to assemble/validate a named new-run
release and import/validate a named legacy release under `releases/`. Add the
Explorer's existing local and rsconnect entry points without changing its
user-facing behaviour.

## `QA-TIMES-NZ`

### Responsibilities

`QA-TIMES-NZ` is produced by renaming what remains after the Explorer move.
It retains the existing technical-analysis and non-published reporting scripts.
Those scripts are not otherwise reorganised, but their common data loader is
updated to read one or more explicitly selected PUBLISH releases. QA may compare named
releases and write charts or reports for internal developers and colleagues;
it must not assemble, alter, or publish release artefacts.

Suggested package shape after the rename:

```text
QA-TIMES-NZ/
  src/qa_times_nz/
    analysis/
    utilities/
  tests/
  readme.md
  pyproject.toml
```

Delete `calibration_checks/`, its calibration data, and generated calibration
report rather than moving them.  A replacement calibration design can define
its own release-reader and reference-data requirements later.

## Migration sequence

1. **Define and test the release contract.** Implement one small standard-
   library `bundle.json` loader/validator: check its format version and
   required keys, then locate every Parquet in the release directory. Create
   minimal synthetic Parquet fixtures; do not use production result data in
   pytest.
2. **Create PUBLISH and the release builder.** Implement assembly, validation,
   and legacy-v308 import. Produce one new-solver release and one imported v308
   release under `releases/`. The v308 bundle is untracked migration material:
   after it proves compatibility, it may be moved to the separately maintained
   release location rather than committed to this repository.
3. **Move the Explorer and rename QA.** Move the Shiny application, helpers,
   utilities, assets, entry point, and deployment documentation to PUBLISH;
   delete the orphan developer module and infeasibilities asset. Rename the
   remaining module and package to QA, remove calibration, update the common
   QA loader, and update the root uv workspace and imports.
4. **Prove compatibility.** Run the moved Explorer against each release.
   Verify scenario selection, all app datasets, and downloads.
   Compare the columns required by each chart, not value equality between v308
   and new solves.
5. **Cut over deployment.** Configure the production/development app to use
   one explicit path to the complete selected release. Deploy a development
   app first, then switch production only after the checks pass.
6. **Retire the old module name.** Update root documentation and workspace
   dependencies, then remove `TIMES-NZ-INTERNAL-QA` once PUBLISH is runnable
   from a clean checkout plus a release bundle in `releases/`.

## Tests and acceptance criteria

### PUBLISH unit tests

- valid new-run source creates a manifest and carries through all source
  Parquets;
- valid legacy v308 source creates a release with its available Parquets;
- new single-scenario run inputs become one multi-scenario topic parquet in
  the release;
- duplicate scenario IDs are caught whether they occur inside a legacy
  multi-scenario parquet or across new one-scenario sources;
- duplicate scenario IDs and incompatible manifest versions fail before
  publication;
- the Explorer release seam uses manifest scenarios and reports a missing
  chart dataset with a clear error;
- QA's common data loader reads explicitly selected releases and preserves
  supplied scenario IDs for analysis-specific comparison mapping.

### End-to-end acceptance

- a v308 release and a new-solver release both load in the Explorer;
- retained QA analysis loads explicitly selected v308 and new-solver releases
  and can compare their scenarios where its chart-specific inputs exist;
- an app download contains every Parquet in the selected release, including
  raw results when present;
- PUBLISH runs in a clean workspace with a release bundle placed under its
  Git-ignored `releases/` root;
- the renamed QA module imports and its retained tests pass after the package
  rename.

## Decisions deliberately deferred

- External artefact-store choice, authentication, retention, and upload/
  download implementation are handled separately.
- Whether manifests and small schema fixtures are committed is a repository
  policy decision; production parquet files are not committed.
- Release comparison-report design, styling, and HTML/PDF rendering are
  follow-up work.
