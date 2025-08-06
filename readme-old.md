# TIMES-NZ-Model-Files

Developed by [Energy Efficiency and Conservation Authority](https://github.com/EECA-NZ), [BusinessNZ Energy Council](https://bec.org.nz/) and [Paul Scherrer Institut](https://www.psi.ch/en)

This repository now integrates the previously separate input data preprocessing steps, GAMS files, and the downstream visualization tool into the TIMES-NZ-Model-Files repository, providing a unified model management system for the TIMES-NZ model (the Integrated MARKAL-EFOM System - New Zealand energy system model). It is intended for use by researchers and analysts working with the TIMES-NZ energy model for New Zealand.

## Prerequisites
Before you start working with this project, you will need the following tools installed on your machine:

- Running Windows 10 or later.
- Python 3.12 or later installed.
- Git: Used for version control. Download and install from https://git-scm.com/downloads. Ensure that you are able to use Git via the command line in a PowerShell-like environment. This README assumes Windows 10 or higher.
- Docker: Required for running the `times-excel-reader` tool. Download and install from https://www.docker.com/get-started.
- [GAMS](https://www.gams.com/) installed on your system.
- A valid GAMS license placed in the system's designated location (e.g., `C:\GAMS\42\gamslice.txt`).
- A working VEDA (VEDA 2.0 localhost) installation, located within your user's home directory. (Follow the installation instructions [here](https://github.com/kanors-emr/Veda2.0-Installation/tree/master) or [here](https://veda-documentation.readthedocs.io/en/latest/pages/Getting%20started.html).)

## Documentation

For more information and detailed guides, see:

- [Getting Started Guide](https://github.com/EECA-NZ/TIMES-NZ-internal-guide-EECA) on GitHub.
- [System Configuration Guide](SystemConfigurationGuide.md) for step-by-step environment setup.
- [Structured Workbook Documentation](docs/README.md) for workbook details.
- [GitHub Flow Guide](docs/github-flow-readme.md) for our Git workflow.
- [Code Quality Infrastructure Setup](docs/code-quality-infra-readme.md) for linting, testing, and CI/CD configuration.

## Installation

Here's how to get the project installed on your local machine for development: Clone the repository
```PowerShell
git clone --recurse-submodules git@github.com:EECA-NZ/TIMES-NZ-Model-Files.git
```
If you need to fetch or update the submodules after cloning the repository, run the following command:
```PowerShell
git submodule update --init --recursive
```
Configure your local development environment as described in the Code Quality Infrastructure Setup guide: [docs/code-quality-infra-readme.md](docs/code-quality-infra-readme.md).

## High-Level Workflow Overview

### Preamble: Notes on Model Configuration and Release Tagging
- Begin by configuring the TIMES-NZ model in the TIMES-NZ-Model-Files repository, and using VEDA to run the model. Work is done in a development branch and merged to the main branch after review - i.e. we follow the standard [GitHub Flow](https://docs.github.com/en/get-started/quickstart/github-flow).
- When ready to release a new version of the model, name your scenarios to include the release tag (use the naming convention `kea-v2_1_2` where kea is an identifier for the scenario set, and v2_1_2 indicates the version number).
- Once the configuration is complete and scenarios are named, commit your changes and tag the release (e.g., v2.1.2).
Release tagging allows users and collaborators to easily identify and revert to specific versions of the model.

To make it explicit which version of TIMES-NZ we are running, we have a convention of including the release number in the scenario name, e.g. `kea-v2_1_3`.

### Step 1: Model Preparation
TODO: establish scripts in `PREPARE-TIMES-NZ`.
When these are in place, the first step will be to use the scripts in `PREPARE-TIMES-NZ` to set up the model's Excel configuration files:
```
cd PREPARE-TIMES-NZ\scripts
python prepare_times_nz.py
```

### Step 2: Running the model using VEDA.
TODO: establish the ability to bypass this step using `xl2times`.

Complete the usual workflow of syncing the files to VEDA's postgresql back-end, selecting scenarios, and running the model from within VEDA.

VEDA will create a directory for each scenario within `/path/to/VEDA2/Installation/GAMS_WrkTIMES`.

After running both `kea-vA_B_C` and `tui-vA_B_C`, also navigate to the `Items List` module.
* Select "Process" (top left) and click "Export to Excel" (bottom right).
* Select "Commodity" (top left) and click "Export to Excel" (bottom right).
* Select "Commodity Groups" (top left) and click "Export to Excel" (bottom right).


### Step 3: Model Retrieval and Repeatable Execution
Ensure that your local environment is set up correctly with GAMS installed, including a valid license. Verify that the version of GAMS you're using is compatible with the model files.

Navigate to the `scripts` directory within `TIMES-NZ-GAMS` and fetch the scenario files for each scenario.
```
cd TIMES-NZ-GAMS\scripts
python get_from_veda.py [veda_dir] [scenario_name]
```
To generate the model results, the scenario can now be executed using the `run_times_scenario.py` script which calls GAMS:
```
python run_times_scenario.py [scenario name]
```

### Step 4: Output Processing
After running both the kea and the tui scenario for a given release number, the outputs can be processed for visualization. For example, for release `2.1.3`, in the previous step you have run both `python run_times_scenario.py kea-v2_1_3` and `python run_times_scenario.py tui-v2_1_3`.

* Enter the `TIMES-NZ-OUTPUT-PROCESSING` directory
* The `Items List` exports that were generated in step 2 are an input to the data postprocessing. Retrieve these:
```
python .\fetch_items_lists.py
```
* Process the raw output to make the data human-readable:
```
python make_human_readable_data.py 2.1.3
```

### Step 5: Visualization Preparation
- After running the scenario, take the output vd file and copy it into the TIMES-NZ-Visualisation's `data_cleaning` subdirectory. Depending on the details of the user's system configuration, this could look something like the following:
```PowerShell
$times_nz_gams_files_local_repo = "C:\Users\$env:USERNAME\git\TIMES-NZ-GAMS-Files"
$times_nz_visualization_local_repo = "C:\Users\$env:USERNAME\git\TIMES-NZ-Visualisation"
$scenario='tui-v2_1_2'
cp $times_nz_gams_files_local_repo\$scenario\$scenario.vd $times_nz_visualization_local_repo\data_cleaning
```
- Ensure that the file paths are correctly set in the script to avoid any file not found errors.
- Run the data extraction script in the `data_cleaning` subdirectory to process the output and generate a file ready for visualization (e.g., to process a scenario named tui-v2_1_2, you might run a script that generates a file named tui-v2_1_2.rda).
- After running the extraction script, it's a good practice to verify the integrity of the generated data file. Check for any inconsistencies or missing data that might impact the accuracy of your visualizations.

### Step 6: Visualization
TODO: we intend to move from the RShiny app to Python shiny.
- Ensure that you have R and the Shiny package installed on your machine. If not, you can install them from the Comprehensive R Archive Network (CRAN).
Visualize the results using the tools in `TIMES-NZ-VISUALISATION`:
```
cd ../TIMES-NZ-VISUALISATION
shiny::runApp()
```

### Additional Details
For more specific instructions, including the commands and scripts to be used at each step, please refer to the README files in the respective repositories:
- [TIMES-NZ-Model-Files README](https://github.com/EECA-NZ/TIMES-NZ-Model-Files/blob/main/README.md)
- [TIMES-NZ-GAMS-Files README](https://github.com/EECA-NZ/TIMES-NZ-GAMS-Files/blob/main/README.md)
- [TIMES-NZ-Visualisation README](https://github.com/EECA-NZ/TIMES-NZ-Visualisation?files=1#readme)

For any questions or support, you can contact [dataandanalytics@eeca.govt.nz].

**Note:** The above workflow describes current state. In the future we hope to:
* automate the process of generating the Excel configuration files using Reproducible Analytical Pipelines (RAPs);
* automate the production of GAMS files directly from the excel files without the use of VEDA.

---

## Usage

Guide on getting started with the TIMES-NZ model stored here: https://github.com/EECA-NZ/TIMES-NZ-internal-guide-EECA

---

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please ensure that you have the necessary dependencies installed, as outlined at the beginning of this document.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
