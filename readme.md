# TIMES-NZ-Model-Files
![CI Pipeline](https://github.com/EECA-NZ/TIMES-NZ-Model-Files/actions/workflows/ci.yml/badge.svg)
[Test Coverage Report](https://eeca-nz.github.io/TIMES-NZ-Model-Files)

Developed by [Energy Efficiency and Conservation Authority](https://github.com/EECA-NZ), [BusinessNZ Energy Council](https://bec.org.nz/) and [Paul Scherrer Institut](https://www.psi.ch/en)

This repository integrates the previously separate TIMES-NZ GAMS files into a unified model management system for the TIMES-NZ (The Integrated MARKAL-EFOM System - New Zealand) energy system model. It is intended for researchers and analysts working with the TIMES-NZ energy model.

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

## Documentation

The following guides are available:

- [System Configuration Guide](SystemConfigurationGuide.md) for step-by-step environment setup.
- [Structured Workbook Documentation](docs/README.md) for workbook details (out-of-date - needs fixing).
- [GitHub Flow Guide](docs/github-flow-readme.md) for our Git workflow.
- [Code Quality Infrastructure Setup](docs/code-quality-infra-readme.md) for linting, testing, and CI/CD configuration.
- [Setup VSCode for poetry](docs/vscode-and-poetry.md) to ensure VSCode understands your poetry environment

## Getting the Code

Clone the repository with submodules:

```bash
git clone --recurse-submodules git@github.com:EECA-NZ/TIMES-NZ-Model-Files.git
```

Update submodules after cloning if needed:

```bash
git submodule update --init --recursive
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
poetry shell
```
or
```bash
eval "$(poetry env activate)"
```
from within `PREPARE-TIMES-NZ`.

This allows your terminal to run directly from the poetry shell, meaning that `poetry run` prefixes are not required to run scripts,  `doit`, or `pre-commit`.

You can achieve similar results in the VSCode terminal by setting your python interpreter to the poetry interpreter. See [Setup VSCode for poetry](docs/vscode-and-poetry.md) documentation for further details.


### Step 2: Running the Model Using VEDA

Sync files to VEDA's PostgreSQL backend on Windows, select scenarios, and run the model from within VEDA.

VEDA will create scenario directories within:
```
/path/to/VEDA2/Installation/GAMS_WrkTIMES
```

Scenario naming convention example: `kea-v2_1_3`.

Export these items from VEDA:
- Select "Process" -> "Export to Excel"
- Select "Commodity" -> "Export to Excel"
- Select "Commodity Groups" -> "Export to Excel"

### Step 3: Model Retrieval and Scripted Execution

Fetch scenario files from VEDA:

```bash
cd TIMES-NZ-GAMS/scripts
python get_from_veda.py [veda_dir] [scenario_name]
```

Run the model scenario with GAMS:

```bash
python run_times_scenario.py [scenario_name]
```

### Step 4: Output Processing

Process outputs for visualization:

```bash
cd TIMES-NZ-OUTPUT-PROCESSING
python fetch_items_lists.py
python make_human_readable_data.py [release_number]
```

### Step 5: Visualization

Visualize using the TIMES-NZ visualization tools. (Currently RShiny; planned transition to Python Shiny.)

```R
cd ../TIMES-NZ-VISUALISATION
shiny::runApp()
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

