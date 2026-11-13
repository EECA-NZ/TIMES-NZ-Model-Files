# PUBLISH-TIMES-NZ

`PUBLISH-TIMES-NZ` holds named result releases for the Explorer and other
result consumers. A release is a directory containing a small manifest and
the Parquet files that belong to that release. It is separate from an
individual solver run: a release may contain results from one or more runs.

## Create a release

Build a release from one or more completed solver `postprocessed/` directories:

```bash
uv run publish-times-nz build v3.0.9-comparison \
  SOLVE-TIMES-NZ/build/solves/steady-v3.0.9-20261112T060842Z/postprocessed \
  SOLVE-TIMES-NZ/build/solves/shift-v3.0.9-20261112T060842Z/postprocessed
```

Each selected solver directory must contain exactly one scenario, and selected
directories must not repeat a scenario ID. PUBLISH batches matching labelled
Parquets by filename and includes every source Parquet; it places
`raw_results.parquet` in `raw/` when available.

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
    {"id": "steady", "label": "Steady"}
  ],
  "source": {
    "type": "solver_runs",
    "runs": ["steady-v3.0.9-20261112T060842Z"]
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
