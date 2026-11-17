# PUBLISH-TIMES-NZ

`PUBLISH-TIMES-NZ` holds named result releases for the Explorer and other
result consumers. A release is a directory containing a small manifest and
the Parquet files that belong to that release. It is separate from an
individual solver run: a release may contain results from one or more runs.

## Build a configured bundle

Run these commands from the repository root. Tracked definitions under
`PUBLISH-TIMES-NZ/bundles/` describe which cases belong together without local
paths, run timestamps, or a hard-coded model version. For example,
`PUBLISH-TIMES-NZ/bundles/standard.toml` contains:

```toml
name = "standard"
scenarios = ["steady", "shift"]
```

Build it with:

```bash
uv run publish-times-nz build-bundle PUBLISH-TIMES-NZ/bundles/standard.toml
```

With workspace version `3.0.9`, this selects `steady-v3.0.9` and
`shift-v3.0.9` and creates `PUBLISH-TIMES-NZ/releases/v3.0.9-standard/`.
Add another definition with a different name and case list for a release
containing the baselines and selected sensitivities. Definitions do not inherit
other releases: each release contains its complete selected results.

Selection searches `SOLVE-TIMES-NZ/build/solves/*/manifest.json` and matches
`case_name` and the versioned `scenario_name`. For each requested case it chooses
the most recently completed successful solve whose postprocessing is also
complete. It uses the solve manifest's `execution.completed_at`, never directory
names, filesystem modification times, or postprocessing time. Failed and
unfinished runs are skipped. A missing case, tied latest completion times, or
missing files recorded by completed postprocessing stops the build.
The Parquet scenario IDs must also match the resolved cases and workspace version.

Older runs lack the postprocessing completion record and are not eligible for
automatic selection. Rerun postprocessing once to produce that record; a new
solve is unnecessary:

```bash
uv run solve-times-nz postprocess SOLVE-TIMES-NZ/build/solves/<run-directory>
```

Postprocessing invalidates its prior completion record before starting and marks
completion only after all dataset writes succeed. A failed attempt remains
ineligible until rerun successfully. Existing output files are retained for
inspection; their presence alone does not indicate completion.

The build prints the selected scenario and run identities. Its `bundle.json`
records the definition, resolved workspace version, and exact timestamped run
identities. Source runs remain in `solves/`; the release is a self-contained
snapshot for Explorer, QA, or public sharing. It has the same layout as an
imported legacy v308 release.

The recipe is portable when the matching runs are available locally. It is not
a guarantee that colleagues select identical results: code and inputs can change
without a version bump, and local toolchains can differ. Share the completed
release to share agreed results. Rebuilding the recipe selects the latest local
runs again. Named releases are never overwritten; use a distinct definition name
for another release under the same workspace version.

## Temporary comparison bundles from explicit runs

Use the explicit-path `build` command for temporary or one-off comparisons,
including comparisons across model versions. Select the completed solver
`postprocessed/` directories to combine and give the comparison its own name:

```bash
uv run publish-times-nz build steady-v306-v307-comparison \
  SOLVE-TIMES-NZ/build/solves/<steady-v306-run>/postprocessed \
  SOLVE-TIMES-NZ/build/solves/<steady-v307-run>/postprocessed
```

Unlike `build-bundle`, this command does not select runs by workspace version or
add a version prefix to the release name. It preserves the scenario IDs in the
source data and creates the same release layout for consumers to filter and
compare. Matching Parquet schemas must be compatible across the selected runs.
Prefer this command for ad hoc comparisons; tracked definitions remain the
repeatable recipe for standard bundles at the current workspace version. No
TOML version override is needed for temporary comparisons.

Each selected solver directory must contain exactly one scenario, and selected
directories must not repeat a scenario ID. PUBLISH batches matching labelled
Parquets by filename and includes every source Parquet; it places
`raw_results.parquet` in `raw/` when available.

Topics may intentionally occur in only some scenarios. A topic is combined from
the runs that supply it; matching schemas are required only between files being
combined. Missing topic coverage is not an error. Consumers decide whether the
available data meets their analysis requirements. The explicit-run command
retains its original behaviour and does not require a completion record.

Import an already scenario-batched legacy result directory with:

```bash
uv run publish-times-nz import-legacy v308 \
  TIMES-NZ-INTERNAL-QA/data/clean_results \
  --legacy-source "v308 clean results"
```

Both commands stage and validate the new directory before publishing it. They
never overwrite an existing release name. Use `--releases-root <path>` only
when the local release root must be elsewhere.

## Deploy the Explorer

Create the deployment payload immediately before each deployment:

```bash
uv run --directory PUBLISH-TIMES-NZ publish-times-nz prepare-deployment-payload
uv run --directory PUBLISH-TIMES-NZ rsconnect deploy shiny deployment_payload \
  --entrypoint app --app-id <APP-ID>
```

`deployment_payload/` is Git-ignored and regenerated from scratch. It contains
only the app runtime files, the tracked v308 release, a requirements export
from `uv.lock`, and the local `.env` file used for Pendo. Deploy this directory,
not `PUBLISH-TIMES-NZ/`; do not edit the generated payload by hand.

## Release layout

Place local releases below `PUBLISH-TIMES-NZ/releases/`. That directory is
ignored by Git, so result data is not committed with the source code.

```text
PUBLISH-TIMES-NZ/releases/<release-name>/
  bundle.json
  labelled/
    energy_demand.parquet
    ...
  raw/
    raw_results.parquet
```

Every `*.parquet` file anywhere below the release directory is part of the
release. This includes raw solver results when they are available; no file
list is maintained in `bundle.json`.

`bundle.json` must contain the release format version, release name, creation
time, scenarios, and source lineage. For example:

```json
{
  "format_version": 1,
  "release_name": "v3.0.9-steady",
  "created_at": "2026-11-13T00:00:00Z",
  "scenarios": [
    {"id": "steady-v3.0.9", "label": "steady-v3.0.9"}
  ],
  "source": {
    "type": "solver_runs",
    "runs": ["steady-v3.0.9-20261112T060842Z"],
    "definition": {
      "name": "steady",
      "scenarios": ["steady"],
      "workspace_version": "3.0.9"
    }
  }
}
```

For imported historical results, identify the source without inventing solver
run identities:

```json
"source": {"type": "legacy", "legacy_source": "v308 clean results"}
```

Each scenario needs a unique raw `id` and its human-readable `label`. Keep
the raw IDs in the Parquet `Scenario` column; display labels are manifest
metadata. Until a display-label policy is added, PUBLISH uses each raw ID as
its label.

## Reading a selected release

The Explorer currently uses the tracked `releases/v308` path. It never chooses
the newest directory under `releases/`.

```python
from pathlib import Path

from publish_times_nz.release_bundle import load_bundle

release_path = Path("PUBLISH-TIMES-NZ/releases/v3.0.9-steady")
bundle = load_bundle(release_path)

print(bundle.scenarios)
for parquet_file in bundle.parquet_files:
    print(parquet_file.relative_to(release_path))

energy_demand = bundle.labelled_file("energy_demand.parquet")
```

`load_bundle()` rejects missing or invalid manifests, unsupported format
versions, duplicate scenario IDs, missing source lineage, and releases with no
Parquet files. `bundle.parquet_files` includes labelled and raw data.
`bundle.labelled_file()` is for an Explorer chart that needs one conventional
`labelled/<name>.parquet` file; it fails clearly if that file is absent.
