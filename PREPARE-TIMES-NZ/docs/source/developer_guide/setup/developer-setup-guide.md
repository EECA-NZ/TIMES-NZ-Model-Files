
# Developer setup 

## Prerequisites

While VEDA needs to be run in Windows, we recommend running the scripted data processing pipelines in a WSL Linux environment.

Ensure the following prerequisites are installed:

- Windows 10 or later.
- [Windows Subsystem for Linux (WSL)](https://learn.microsoft.com/en-us/windows/wsl/install) with Ubuntu 22.04 or later.
- Python 3.12 or later installed within WSL.
- [GAMS](https://www.gams.com/) installed on Windows.
- A valid GAMS license placed at `C:\GAMS\44\gamslice.txt`.
- A working VEDA (VEDA 2.0 localhost) installation in your Windows user directory. See instructions [here](https://github.com/kanors-emr/Veda2.0-Installation/tree/master).
- [uv](https://docs.astral.sh/uv/) for Python dependency management.

## Getting the Code

Clone the repository with submodules:

```bash
git clone git@github.com:EECA-NZ/TIMES-NZ-Model-Files.git
```

## Workflow Overview

All commands below assume you are using a WSL (Ubuntu) shell.

### Step 1: Model Preparation

From the repository root, install the shared workspace environment:

```bash
uv sync --group dev
```

This creates one `.venv` at the repository root for both Python modules. Run
commands with `uv run`; no environment activation is required.

### Building model files
Run the data preparation pipeline (`doit`):

```bash
uv run --directory PREPARE-TIMES-NZ doit
```

`doit` runs the entire data preparation method and creates TIMES model files in `PREPARE-TIMES-NZ/output`.

Alternatively, run a specific script:

```bash
uv run --directory PREPARE-TIMES-NZ python scripts/prepare_times_nz.py
```

#### Running Tests

Run tests within `PREPARE-TIMES-NZ`:

```bash
uv run --directory PREPARE-TIMES-NZ pytest
```

Note that these are unit tests for code, not data validation tests.

#### uv and VSCode

uv creates the shared environment at the repository root. Configure VSCode to
use that interpreter if it is not detected automatically:

1. From the repository root, use `.venv/bin/python` (or `.venv\\Scripts\\python.exe` on Windows).
1. Press Ctrl+Shift+P (or Cmd+Shift+P on Mac)
1. Search for and select: Python: Select Interpreter
1. Click Enter interpreter path
1. Select that interpreter path.

### Step 2: Running the Model Using VEDA

The excel files for VEDA are generated in `TIMES-NZ` by the `PREPARE-TIMES-NZ` module by running `doit`. At this stage, it's recommended that you move these to a separate area to work on in VEDA separately. Future iterations will hopefully automate this stage better. 

This project assumes your VEDA installation is stored in Windows, under `C:/Users/yourusername/Veda`. VEDA is currently used for synchronising files, running the TIMES model, and generating output `.vd` files. 

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
