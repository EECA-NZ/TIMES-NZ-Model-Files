# PUBLISH-TIMES-NZ

`PUBLISH-TIMES-NZ` holds named result releases for the Explorer and other
result consumers. A release is a directory containing a small manifest and
the Parquet files that belong to that release. It is separate from an
individual solver run: a release may contain results from one or more runs.

## Current status

The release-bundle reader is available now. Release assembly and legacy import
commands will be added separately; until then, this page documents the bundle
format and how consumers read a selected release.

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
metadata.

## Reading a selected release

Consumers must receive an explicit release path. They must not choose the
newest directory under `releases/`.

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
