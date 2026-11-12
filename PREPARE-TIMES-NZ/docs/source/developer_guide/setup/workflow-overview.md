# Workflow overview

This very high-level overview describes how to perform a successful model solve using the raw data found in the repository. To solve the model, you must have a valid GAMS and solver license. However, you can prepare and inspect the data in more detail without this license. 

### Step 1: Model preparation 

**See [PREPARE-TIMES-NZ](../prepare_times_nz/index.md)**

This module processes all raw data and assumptions into TIMES model configuration files, ready for ingestion by `Veda` or `xl2times`. These are excel files, a common format for TIMES model configuration. 

### Step 2: LP generation and solution 

**See [SOLVE-TIMES-NZ](../solve_times_nz/index.md)**

The `SOLVE-TIMES-NZ` module uses the `xl2times` package to convert the excel configuration files to .dd files, pass these to the TIMES model generator to create the Linear Programming (LP) matrix, solves the model, and returns results. 


```{note}
It is also possible to instead use Veda, a common software used by TIMES modellers, to compile and solve the LP matrix. The files produced by `PREPARE-TIMES-NZ` are compatible with VEDA inputs. The VEDA software includes features designed for manual exploration of the model configuration, and can be a useful alternative pathway for some developers. 
```

### Step 3: Result post-processing 

`solve-times-nz solve` automatically writes labelled parquet outputs after the
model solve. It also stores the raw `.vd`, `raw_results.parquet`, and the PREP
metadata snapshot beside the result files:

```bash
uv run --directory SOLVE-TIMES-NZ solve-times-nz solve steady
```

For a failed or adjusted reporting run, regenerate parquets without solving:

```bash
uv run --directory SOLVE-TIMES-NZ solve-times-nz postprocess <run-dir>
```

### Step 4: Visualization (internal qa method)

Visualize using the TIMES-NZ visualization tools. 

```bash
uv run --directory TIMES-NZ-INTERNAL-QA python run_local.py
```

Builds the explorer app to investigate results locally.
