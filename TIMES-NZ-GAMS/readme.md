# TIMES-NZ-GAMS-Files

This repository houses the model files for the TIMES-NZ (The Integrated MARKAL-EFOM System - New Zealand) GAMS (General Algebraic Modeling System) models. It is intended for use by researchers and analysts working with energy models in New Zealand.

## Prerequisites

Before you begin, ensure the following prerequisites are met:

- Running Windows 10 or later and using PowerShell (version 5 or later recommended).
- [GAMS](https://www.gams.com/) installed on your system.
- A valid GAMS license placed in the system's designated location (e.g., `C:\GAMS\42\gamslice.txt`).
- A working VEDA (VEDA 2.0 localhost) installation.

For GAMS and VEDA installation instructions, refer to their respective documentation.

## Getting the Code

You can clone the repository using either SSH or HTTPS:
```powershell         
git clone --recurse-submodules git@github.com:EECA-NZ/TIMES-NZ-GAMS-Files.git
```
or
```powershell         
git clone --recurse-submodules https://github.com/EECA-NZ/TIMES-NZ-GAMS-Files.git
```

## Preparing and Running Scenarios

### Obtaining and Updating the TIMES Source Code
The directory 'source' should contain the TIMES source code. This is a git submodule, so to update it, run:
```powershell
git submodule init
git submodule update --recursive --remote
```

### Getting Scenario Files from VEDA

It is assumed that the user has a working VEDA installation and has already used VEDA to run a scenario specified in the TIMES-NZ model configuration repository [TIMES-NZ-Model-Files](https://github.com/EECA-NZ/TIMES-NZ-Model-Files). The scenario name should contain a specification of the release tag for the TIMES-NZ configuration, for instance `kea-v2_0_0`. After running the scenario using VEDA, the scenario files will be present in the VEDA working directory.

To get scenario files from VEDA, run the `get_from_veda.ps1` script:

```powershell
.\get_from_veda.ps1 [VEDA working directory] [scenario name]
```
If the optional positional arguments are not provided, you will be prompted to enter the VEDA working directory and select a scenario from the available options. The script will copy the necessary files to a new directory within the repository.

### Running a Scenario
To run a specific scenario, use the `run_times_scenario.ps1` PowerShell script:

```powershell
.\run_times_scenario.ps1 [scenario name]
```
If the optional positional argument is not provided, you will be prompted to select a scenario from the available options. The script will execute the GAMS model run and save the output in the designated directory.

### Extracting output data

The `collect_single.bat` script can be used to extract data from the GAMS output files and save it in a format that can be used for further analysis. The script takes two positional arguments: the scenario name and the output directory. For example, to extract data from the `scen1` scenario and save it in the current directory, run:
```powershell
cmd.exe /c collect_single.bat scen1 .
```
The `scen1.gdx` .GDX file from the JRC-EU-TIMES model run that is compatible with this routine requires 500 GB of storage and isn't checked into this repo.

The main files used by `collect_single.bat` are:
* The .gms file that contains GAMS and Python code to process the files containing the TIMES results
* An EXCEL file (`results_template.xlsx`) serving as a template for creating tables or charts

The main idea of the whole routine is:
1.      Call GDX2VEDA (provided as standard with any GAMS distribution) to convert the .GDX result file to the VEDA text files
2.      Call the GMS routine and collect all VEDA results in a single GAMS parameter named veda_vdd
3.      Use GAMS commands to process parts of the veda_vdd parameter according to the results that we would like to report. Complement GAMS commands with Python code to be able to do filtering of processes and commodities with wildcards when processing the results
4.      Export the processed results to a pre-created EXCEL file containing charts and other results calculations.
5.      Use the .bat files to drive the whole procedure and allow parallel execution of the code over multiple CPUs for simultaneous processing of the results from many runs.

### Version Control
After collecting and running a scenario, you might want to commit the run files to the repository:
```powershell
git add .\scenario-directory\
git commit -m "Run files for scenario-directory"
```
Replace `scenario-directory` with the appropriate directory name for your scenario. Note that TIMES output files (.gdx, .vd*) are in the `.gitignore` file and will not be committed to the repository - only the GAMS source code will be committed.


### Contributing

We welcome contributions to the `TIMES-NZ-GAMS-Files` repository. To contribute, please follow the established workflow and ensure that any submitted code includes appropriate documentation. For any questions or support, you can contact [dataandanalytics@eeca.govt.nz].
