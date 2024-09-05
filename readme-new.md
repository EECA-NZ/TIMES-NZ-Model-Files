# TIMES-NZ-Model-Files

This repository now integrates the previously separate TIMES-NZ GAMS files into a unified model management system for the TIMES-NZ (The Integrated MARKAL-EFOM System - New Zealand) energy system model. It is intended for use by researchers and analysts working with the TIMES-NZ energy model for New Zealand.

## Prerequisites

Before you begin, ensure the following prerequisites are met:

- Running Windows 10 or later.
- Python 3.10 or later installed.
- [GAMS](https://www.gams.com/) installed on your system.
- A valid GAMS license placed in the system's designated location (e.g., `C:\GAMS\42\gamslice.txt`).
- A working VEDA (VEDA 2.0 localhost) installation, located within your user's home directory.

For GAMS and VEDA installation instructions, refer to their respective documentation.

## Getting the Code
Clone the repository
```bash
git clone --recurse-submodules git@github.com:EECA-NZ/TIMES-NZ-Model-Files.git
```

Workflow Overview
## Step 1: Model Preparation
TODO: establish scripts in `PREPARE-TIMES-NZ`.
When these are in place, the first step will be to use the scripts in `PREPARE-TIMES-NZ` to set up the model's Excel configuration files.

## Step 2: Running the model using VEDA.
Complete the usual workflow of syncing the files to VEDA's postgresql back-end, selecting scenarios, and running the model from within VEDA.

VEDA will create a directory for each scenario within `/path/to/VEDA2/Installation/GAMS_WrkTIMES`.

To make it explicit which version of TIMES-NZ we are running, we have a convention of including the release number in the scenario name, e.g. `kea-v2_1_3`.

After running both `kea-vA_B_C` and `tui-vA_B_C`, also navigate to the `Items List` module.
* Select "Process" (top left) and click "Export to Excel" (bottom right).
* Select "Commodity" (top left) and click "Export to Excel" (bottom right).
* Select "Commodity Groups" (top left) and click "Export to Excel" (bottom right).

## Step 3: Model Retrieval and Scripted Execution
Navigate to `TIMES-NZ-GAMS` and fetch the scenario files for each scenario.
```
cd TIMES-NZ-GAMS
python get_from_veda.py [veda_dir] [scenario_name]
```
To generate the model results, the scenario can now be executed using the `run_times_scenario.py` script which calls GAMS:
```
python run_times_scenario.py [scenario name]
```

## Step 4: Output Processing
After running both the kea and the tui scenario for a given release number, the outputs can be processed for visualization. For example, for release `2.1.3`, in the previous step you have run both `python run_times_scenario.py kea-v2_1_3` and `python run_times_scenario.py tui-v2_1_3`.

* Enter the `TIMES-NZ-OUTPUT-PROCESSING` directory
* The `Items List` exports that were generated in step 2 are an input to the data postprocessing. Retrieve these:
```
python .\fetch_items_lists.py
```
* Process the raw output to make the data human-readable:
```
python make_human_readable_data.py 2.1.3`
```

## Step 5: Visualization
TODO: we intend to move from the RShiny app to Python shiny.
Visualize the results using the tools in `TIMES-NZ-VISUALISATION`:
```
cd ../TIMES-NZ-VISUALISATION
shiny::runApp()
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
