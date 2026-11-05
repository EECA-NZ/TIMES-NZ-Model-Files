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


```{warning}
Post-processing needs to be rebuilt to link to the new SOLVE-TIMES-NZ results. 

This module still ingests Veda results for legacy comparisons 

This must be resolved before the next release. 
```

Assuming the VEDA installation is in the expected location, you can automatically retrive VEDA model results and apply post-processing using the below script: 

```bash
uv run --directory TIMES-NZ-INTERNAL-QA python src/times_nz_internal_qa/postprocessing/run_all_postprocessing.py
```

Note that some components of this script rely on data generated in `PREPARE-TIMES-NZ` to assign TIMES process and commodity codes to the relevant categories and add labels. If you don't have these, then you can skip the `define_data` steps of this script, and simply run the `get_data` and `process_data` functions.

If anything in the results is not defined, this will be flagged in the console. 

### Step 4: Visualization (internal qa method)

Visualize using the TIMES-NZ visualization tools. 

```bash
uv run --directory TIMES-NZ-INTERNAL-QA python run_local.py
```

Builds the explorer app to investigate results locally.