## Prerequisites

While VEDA needs to be run in Windows, we recommend running the scripted data processing pipelines in a WSL Linux environment.

Ensure the following prerequisites are installed:

- Windows 10 or later.
- [Windows Subsystem for Linux (WSL)](https://learn.microsoft.com/en-us/windows/wsl/install) with Ubuntu 22.04 or later.
- Python 3.12 or later installed within WSL.
- [GAMS](https://www.gams.com/) installed on Windows.
- A valid GAMS license placed at `C:\GAMS\44\gamslice.txt`.
- A working VEDA (VEDA 2.0 localhost) installation in your Windows user directory. See instructions [here](https://github.com/kanors-emr/Veda2.0-Installation/tree/master).
- Poetry for Python dependency management. Install Poetry within WSL by running: `curl -sSL https://install.python-poetry.org | python3 -`

## Getting the Code

Clone the repository with submodules:

```bash
git clone git@github.com:EECA-NZ/TIMES-NZ-Model-Files.git
```

## Workflow Overview

All commands below assume you are using a WSL (Ubuntu) shell.

### Step 1: Model Preparation

Navigate into the `PREPARE-TIMES-NZ` directory and install Python dependencies using Poetry:

```bash
cd PREPARE-TIMES-NZ
poetry install --with dev
```

Run the data preparation pipeline (`doit`):

```bash
poetry run doit
```

Alternatively, run a specific script:

```bash
poetry run python scripts/prepare_times_nz.py
```

### Running Tests

Run tests within `PREPARE-TIMES-NZ`:

```bash
poetry run pytest
```

### Running from poetry shell

It's a good idea to execute:

```bash
poetry env activate
```
from within `PREPARE-TIMES-NZ` or other modules managed by poetry. This returns a command which you can copy-paste and execute to activate the poetry environment shell. Doing this allows your terminal to run directly from the poetry shell, meaning that `poetry run` prefixes are not required to run scripts,  `doit`, or `pre-commit`.

### Poetry and VSCode
Poetry creates a virtual environment that may not be in your project directory, so VSCode might not pick it up automatically. We need to set the VSCode interpreter to align with Poetry.


If VSCode fails to automatically register the env, `poetry env activate` from within the vscode terminal still works to move into the poetry shell. The VSCode python interpreter is slightly different, and should register automatically. It sometimes struggles if you are moving between different modules, like `PREPARE-TIMES-NZ` and `TIMES-NZ-INTERNAL-QA`. If so, you may need to follow the steps below: 

1. Run the following in your terminal to find the virtual environment path: `poetry env info --path`. This will give you something like `/home/YourName/.cache/pypoetry/virtualenvs/prepare-times-nz-abc123`
1. Press Ctrl+Shift+P (or Cmd+Shift+P on Mac)
1. Search for and select: Python: Select Interpreter
1. Click Enter interpreter path
1. Paste the path from step 1 and append /bin/python (or Scripts/python.exe on Windows), e.g.:
    `/home/YourName/.cache/pypoetry/virtualenvs/prepare-times-nz-abc123/bin/python` 

### Step 2: Running the Model Using VEDA

The excel files for VEDA are generated in `TIMES-NZ` by the `PREPARE-TIMES-NZ` module. At this stage, it's recommended that you move these to a separate area to work on in VEDA separately. Future iterations will hopefully automate this stage better. 

This project assumes your VEDA installation is stored in Windows, under `C:/Users/yourusername/Veda`. VEDA is currently used for synchronising files, running the TIMES model, and generating output `.vd` files. 

### Step 3: result post-processing 

Assuming the VEDA installation is in the expected location, you can automatically retrive VEDA model results and apply post-processing using the below script: 

```bash
cd TIMES-NZ-INTERNAL-QA/src/times-nz-internal-qa/postprocessing
poetry run python run_all_postprocessing.py 
```

Note that some components of this script rely on data generated in `PREPARE-TIMES-NZ` to assign TIMES process and commodity codes to the relevant categories and add labels. If you don't have these, then you can skip the `define_data` steps of this script, and simply run the `get_data` and `process_data` functions.

If anything in the results is not defined, this will be flagged in the console. 

### Step 5: Visualization (internal qa method )

Visualize using the TIMES-NZ visualization tools. 

```bash
cd TIMES-NZ-INTERNAL-QA/
poetry run python run_local.py
```

Builds the explorer app to investigate results locally. 