
# Developer setup 

## Prerequisites

While VEDA needs to be run in Windows, we recommend running the scripted data processing pipelines in a WSL Linux environment.

Ensure the following prerequisites are installed:

- Windows 10 or later.
- [Windows Subsystem for Linux (WSL)](https://learn.microsoft.com/en-us/windows/wsl/install) with Ubuntu 22.04 or later.
- Python 3.12 or later installed within WSL.
- [GAMS](https://www.gams.com/) installed on Windows or WSL, with a valid license. Note that the model is too large to work on trial versions of GAMS. 
- A working VEDA (VEDA 2.0 localhost) installation in your Windows user directory. See instructions [here](https://github.com/kanors-emr/Veda2.0-Installation/tree/master).
- [uv](https://docs.astral.sh/uv/) for Python dependency management.
- [git lfs](https://git-lfs.com/) for handling large data files. 

## Getting the code

Clone the repository with submodules:

```bash
git clone git@github.com:EECA-NZ/TIMES-NZ-Model-Files.git
```

From the repository root, install the shared workspace environment:

```bash
uv sync --all-groups 
```

This creates one `.venv` at the repository root for both Python modules. Run
commands with `uv run`; no environment activation is required. 

It's optional and sometimes convenient to activate the environment in your shell, meaning `uv run` prefixes are not required to run commands. You can do this with: 

```
source .venv/bin/activate
```


#### uv and VSCode

uv creates the shared environment at the repository root. Configure VSCode to
use that interpreter if it is not detected automatically:

1. From the repository root, use `.venv/bin/python` (or `.venv\\Scripts\\python.exe` on Windows).
1. Press Ctrl+Shift+P (or Cmd+Shift+P on Mac)
1. Search for and select: Python: Select Interpreter
1. Click Enter interpreter path
1. Select that interpreter path.


## Workflow overview

This very high-level overview describes how to perform a successful model solve using the raw data. To solve the model, you must have a valid GAMS and solver license. However, you can prepare and inspect the data in more detail without this license. 

### Step 1: Model preparation 

**`PREPARE-TIMES-NZ`**

This module processes all raw data and assumptions into TIMES model configuration files, ready for ingestion by `Veda` or `xl2times`. These are excel files, a common format for TIMES model configuration. 

### Step 2: LP generation and solution 

**`SOLVE-TIMES-NZ`**

The `SOLVE-TIMES-NZ` module uses the `xl2times` package to convert the excel configuration files to .dd files, pass these to the TIMES model generator to create the Linear Programming (LP) matrix, solves the model, and returns results. 



### Step 2: Running the Model Using VEDA

VEDA workflows, common in TIMES modelling work, are supported. This requires a VEDA installation and license. 

The excel files for VEDA are generated in `TIMES-NZ` by the `PREPARE-TIMES-NZ` module by running `doit`. If using VEDA, it's recommended that you move these to a separate area to work on in VEDA separately. 

This project assumes your VEDA installation is stored in Windows, under `C:/Users/yourusername/Veda`. VEDA is currently used for synchronising files, running the TIMES model, and generating output `.vd` files. 

### Step 2: Running the model 

The `SOLVE-TIMES-NZ` module

### Step 3: Result post-processing 

Assuming the VEDA installation is in the expected location, you can automatically retrive VEDA model results and apply post-processing using the below script: 

```bash
uv run --directory TIMES-NZ-INTERNAL-QA python src/times_nz_internal_qa/postprocessing/run_all_postprocessing.py
```

Note that some components of this script rely on data generated in `PREPARE-TIMES-NZ` to assign TIMES process and commodity codes to the relevant categories and add labels. If you don't have these, then you can skip the `define_data` steps of this script, and simply run the `get_data` and `process_data` functions.

If anything in the results is not defined, this will be flagged in the console. 

### Step 5: Visualization (internal qa method)

Visualize using the TIMES-NZ visualization tools. 

```bash
uv run --directory TIMES-NZ-INTERNAL-QA python run_local.py
```

Builds the explorer app to investigate results locally.
