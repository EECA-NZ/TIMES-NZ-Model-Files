# SOLVE-TIMES-NZ

Guidance for selecting prepared workbooks, building TIMES DD cases, and
staging them for a solver executor.

## Quick start guide

These steps assume `PREPARE-TIMES-NZ` has already generated the required Excel
workbooks in `PREPARE-TIMES-NZ/output`.

1. Set up a local Windows GAMS/TIMES executor once. Copy
   `SOLVE-TIMES-NZ/config/solve.local.example.toml` to
   `solve.local.toml`, configure the staging, GAMS, and TIMES source paths,
   and confirm the native Windows installation can run GAMS and GDX2VEDA. See
   [TIMES and GAMS setup](times-gams-setup.md).
2. From `SOLVE-TIMES-NZ`, build a versioned generated case from the prepared
   workbooks:

   ```bash
   uv run solve-times-nz build cases/steady.toml
   ```

3. Stage, solve, and collect VEDA results:

   ```bash
   uv run solve-times-nz solve steady
   ```

The build selects the workbooks defined by the case manifest and writes DD
files to `build/cases/steady-v<workspace-version>`. The solve command stages
that generated case on the configured executor and returns result files to
`build/solves/`.

Use the pages below for more information on case selection and workbook ordering, every command
option and generated artefact, run-file behaviour, solver configuration, and
xl2times compatibility details.

```{toctree}
:maxdepth: 1

command-reference
scenario-configuration
times-gams-setup
run-file
solver-options
xl2times-compatibility
```
