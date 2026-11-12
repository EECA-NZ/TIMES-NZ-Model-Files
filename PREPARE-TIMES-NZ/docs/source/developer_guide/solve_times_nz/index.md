# SOLVE-TIMES-NZ

This module selects prepared workbooks, builds TIMES `.dd` cases, passes them to TIMES and a solver, and returns results. 



## Quick start guide


### Requirements 

1. `PREPARE-TIMES-NZ` has already generated the required Excel
workbooks in `PREPARE-TIMES-NZ/output`.
2. GAMS is installed on your system with a valid license and solver, and correctly configured on the PATH. See
   [TIMES and GAMS setup](times-gams-setup.md). 

### Workflow 

1. Set up a local Windows GAMS/TIMES *executor* once by creating `SOLVE-TIMES-NZ/config/solve.local.toml`. This is your personal machine's configuration, and is not tracked by git. See [Configure your executors](times-gams-setup.md#configure-your-executors) for more details.
2. From `SOLVE-TIMES-NZ`, build a versioned generated case from the prepared
   workbooks:

   ```bash
   uv run solve-times-nz build cases/steady.toml
   ```
   This selects the workbooks defined by the case manifest and writes DD
files to `build/cases/steady-v<workspace-version>`. 

3. Stage, solve, and collect VEDA results:

   ```bash
   uv run solve-times-nz solve steady
   ```
   This stages
that generated case on the configured executor, runs the solver, and returns result files to
`build/solves/`.

## Contents

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
postprocessing
```
