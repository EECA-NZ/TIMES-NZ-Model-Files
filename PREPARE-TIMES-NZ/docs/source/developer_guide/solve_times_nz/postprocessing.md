# Post-processing solver results

`solve-times-nz solve <case>` automatically runs post-processing after GAMS
and GDX2VEDA have completed successfully. It reads the copied `.vd` result
file in the repository-local solver-run directory and the generated PREP
reporting metadata, then writes parquet files beside the raw results.

For example:

```bash
cd SOLVE-TIMES-NZ
uv run solve-times-nz solve steady
```

The resulting run directory contains both the unchanged raw VEDA results and
the derived outputs:

```text
build/solves/steady-v<workspace-version>-<run-id>/
  steady.vd
  manifest.json
  postprocessed/
    metadata/                 # CSV labels copied from PREP for this run
    raw_results.parquet
    elec_generation.parquet
    energy_demand.parquet
    energy_service_demand.parquet
```

The parquet `Scenario` column uses the versioned `scenario_name` recorded in
the generated-case manifest, for example `steady-v3.0.9`.

Before creating parquets, `solve` copies the generated PREP reporting CSVs to
`postprocessed/metadata/`. These are the labels used for that run and remain
available for a later re-run even if PREP has since changed.

## Re-run without solving

Post-processing can be re-run without staging or solving the model. This is
the normal recovery path after a post-processing failure, or after changing
the post-processing code or PREP reporting metadata:

```bash
cd SOLVE-TIMES-NZ
uv run solve-times-nz postprocess \
  build/solves/steady-v3.0.9-<run-id>
```

This command reads the run's existing `.vd` result file and rewrites only its
`postprocessed/` parquet files. It does not alter the raw VEDA files,
re-execute GAMS, or invoke GDX2VEDA.

By default it uses that run's copied metadata directory:

```text
build/solves/<case>-v<version>-<run-id>/postprocessed/metadata/
```

In the rare case of a controlled comparison, direct post-processing at another
run's copied labels (or a generated PREP metadata directory):

```bash
uv run solve-times-nz postprocess <run-dir> --metadata-dir <metadata-dir>
```

The directory must contain the expected PREP reporting CSVs. If metadata is
missing or incompatible, post-processing fails and leaves the raw result files
available for correction and retry.

## Current output coverage

The initial implementation publishes raw results, electricity generation,
energy demand, and energy-service demand. Additional result families will be
added incrementally after comparison with their historical QA outputs.
