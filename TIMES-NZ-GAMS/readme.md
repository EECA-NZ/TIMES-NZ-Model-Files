# TIMES-NZ-Model-Files

This repository now integrates the previously separate TIMES-NZ GAMS files into a unified model management system for the TIMES-NZ (The Integrated MARKAL-EFOM System - New Zealand) energy system model. It is intended for use by researchers and analysts working with energy models in New Zealand.

## Prerequisites

Before you begin, ensure the following prerequisites are met:

- Running Windows 10 or later.
- Python 3.10 or later installed.
- [GAMS](https://www.gams.com/) installed on your system.
- A valid GAMS license placed in the system's designated location (e.g., `C:\GAMS\42\gamslice.txt`).
- A working VEDA (VEDA 2.0 localhost) installation.

For GAMS and VEDA installation instructions, refer to their respective documentation.

## Getting the Code

You can clone the repository using either SSH or HTTPS:
```bash
git clone --recurse-submodules git@github.com:EECA-NZ/TIMES-NZ-Model-Files.git
```
or
```powershell         
git clone --recurse-submodules https://github.com/EECA-NZ/TIMES-NZ-Model-Files.git
```

## Preparing and Running Scenarios

### Obtaining and Updating the TIMES Source Code
The directory 'etsap-TIMES' should contain the TIMES source code. This is a git submodule, so to update it, run:
```powershell
git submodule init
git submodule update --recursive --remote
```

### Getting Scenario Files from VEDA

It is assumed that the user has a working VEDA installation and has already used VEDA to run a scenario specified in the TIMES-NZ model configuration repository [TIMES-NZ-Model-Files](https://github.com/EECA-NZ/TIMES-NZ-Model-Files). The scenario name should contain a specification of the release tag for the TIMES-NZ configuration, for instance `kea-v2_0_0`. After running the scenario using VEDA, the scenario files will be present in the VEDA working directory.

To get scenario files from VEDA, run the `get_from_veda.py` script:

```powershell
python .\get_from_veda.py [VEDA working directory] [scenario name]
```
If the optional positional arguments are not provided, you will be prompted to enter the VEDA working directory and select a scenario from the available options. The script will copy the necessary files to a new directory within the repository.

### Running a Scenario
To run a specific scenario, use the `run_times_scenario.py` script:

```powershell
python .\run_times_scenario.py [scenario name]
```
If the optional positional argument is not provided, you will be prompted to select a scenario from the available options. The script will execute the GAMS model run and save the output in the designated directory.

### Version Control
After collecting and running a scenario, you might want to commit the run files to the repository:
```powershell
git add .\scenarios\scenario-directory\
git commit -m "Run files for scenario-directory"
```
Replace `scenario-directory` with the appropriate directory name for your scenario. Note that TIMES output files (.gdx, .vd*) are in the `.gitignore` file and will not be committed to the repository - only the GAMS source code will be committed.