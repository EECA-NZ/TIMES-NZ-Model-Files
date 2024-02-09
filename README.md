# TIMES-NZ-Model-Files

## Excel Model Configuration Files for TIMES-NZ

This repository houses the Excel files defining the TIMES-NZ (The Integrated MARKAL-EFOM System - New Zealand) energy system model configuration. It is intended for use by researchers and analysts working with energy models in New Zealand.
* For a guide on getting started with the TIMES-NZ model, refer to the [TIMES-NZ-internal-guide-EECA](https://github.com/EECA-NZ/TIMES-NZ-internal-guide-EEC) repository.
* For detailed documentation on the workbooks and their contents, refer to the structured documentation in the [docs](docs/README.md) directory.

## Integrated Workflow Across Repositories

The TIMES-NZ project is divided across three main repositories, each serving a distinct purpose in the overall modeling and visualization process. The repositories and their functions are as follows:

1. [TIMES-NZ-Model-Files](https://github.com/EECA-NZ/TIMES-NZ-Model-Files): Houses the Excel files defining the TIMES-NZ energy system model configuration, along with additional resources and tools for change tracking.

2. [TIMES-NZ-GAMS-Files](https://github.com/EECA-NZ/TIMES-NZ-GAMS-Files): Contains the GAMS model files for TIMES-NZ scenarios and scripts to enable reproducible scenario execution.

3. [TIMES-NZ-Visualisation](https://github.com/EECA-NZ/TIMES-NZ-Visualisation): Provides a tool for visualizing the results of TIMES-NZ scenarios using an RShiny application.

### High-Level Workflow Overview

#### Step 1: Model Configuration and Release Tagging
- Begin by configuring the TIMES-NZ model in the TIMES-NZ-Model-Files repository, and using VEDA to run the model. Work is done in a development branch and merged to the main branch after review - i.e. we follow the standard [GitHub Flow](https://docs.github.com/en/get-started/quickstart/github-flow).
- When ready to release a new version of the model, name your scenarios to include the release tag (e.g., kea-v2_1_2).
- Once the configuration is complete and scenarios are named, commit your changes and tag the release (e.g., v2.1.2).

#### Step 2: Scenario Execution with GAMS
- Move to the TIMES-NZ-GAMS-Files repository.
- Fetch the GAMS 'dd' files and the '.run' file associated with the scenario using the `get_from_veda.ps1` PowerShell script.
- Run the GAMS solver using the `run_times_scenario.ps1` PowerShell script, and the output files will be generated.

#### Step 3: Visualization Preparation
- After running the scenario, take the output vd file and copy it into the TIMES-NZ-Visualisation's `data_cleaning` subdirectory. Depending on the details of the user's system configuration, this could look something like the following:
```PowerShell
$times_nz_gams_files_local_repo = "C:\Users\$env:USERNAME\git\TIMES-NZ-GAMS-Files"
$times_nz_visualization_local_repo = "C:\Users\$env:USERNAME\git\TIMES-NZ-Visualisation"
$scenario='tui-v2_1_2'
cp $times_nz_gams_files_local_repo\$scenario\$scenario.vd $times_nz_visualization_local_repo\data_cleaning
```
- Run the data extraction script in the `data_cleaning` subdirectory to process the output and generate a file ready for visualization (e.g., tui-v2_1_2.rda).

#### Step 4: Visualization with RShiny
- Launch the RShiny application to visualize the scenario results interactively.

### Additional Details
For more specific instructions, including the commands and scripts to be used at each step, please refer to the README files in the respective repositories:
- [TIMES-NZ-Model-Files README](https://github.com/EECA-NZ/TIMES-NZ-Model-Files/blob/main/README.md)
- [TIMES-NZ-GAMS-Files README](https://github.com/EECA-NZ/TIMES-NZ-GAMS-Files/blob/main/README.md)
- [TIMES-NZ-Visualisation README](https://github.com/EECA-NZ/TIMES-NZ-Visualisation?files=1#readme)

For any questions or support, you can contact [dataandanalytics@eeca.govt.nz].

**Note:** The above workflow describes current state. In the future we hope to:
* automate the process of generating the Excel configuration files using Reproducible Analytical Pipelines (RAPs);
* automate the production of GAMS files directly from the excel files without the use of VEDA.


## Dependencies

Before you start working with this project, you will need the following tools installed on your machine:

- **Git**: Used for version control. Download and install from https://git-scm.com/downloads.
- **Docker**: Required for running the `times-excel-reader` tool. Download and install from https://www.docker.com/get-started.

- [GAMS](https://www.gams.com/) installed on your system.
- A valid GAMS license placed in the system's designated location (e.g., `C:\GAMS\42\gamslice.txt`).
- A working VEDA (VEDA 2.0 localhost) installation ([instructions here](https://veda-documentation.readthedocs.io/en/latest/pages/Getting%20started.html)).

Ensure that you are able to use Git via the command line in a PowerShell-like environment. This README assumes Windows 10 or higher.

## Installation

Here's how to get the project installed on your local machine for development:

```PowerShell
git clone git@github.com:EECA-NZ/TIMES-NZ-Model-Files.git
cd TIMES-NZ-Model-Files
```

## Working with Git & GitHub

If you're new to Git and GitHub, here's a simple guide on how to get started.

### Prerequisites

- Make sure you have Git installed on your machine. You can download it from here: https://git-scm.com/downloads.
- If you prefer a graphical user interface, GitHub Desktop is an option, but the use of command-line tools is preferred in order to ensure repeatability. If you want to use GitHub Desktop, you can download it here: https://desktop.github.com/.

### Steps

#### 1. Clone the Repository

First, you'll need to make a copy of this repository on your local machine. This is called "cloning". If you're using command line, use the following command:

```PowerShell
git clone git@github.com:EECA-NZ/TIMES-NZ-Model-Files.git
```

If you're using GitHub Desktop, you can clone the repository by selecting "File -> Clone Repository" from the menu, and then select the repository from the list.

#### 2. Create a Branch

Before making changes, it's best practice to create a new branch. This keeps your changes isolated until they're ready to be merged into the main branch. Here's how you can do it:

Command line:
```PowerShell
git checkout -b <your-branch-name>
```

GitHub Desktop: Select "Branch -> New Branch" from the menu, and enter your branch name.

#### 3. Make Your Changes

Now you can start making changes to the code. You can create new files, modify existing ones, and delete what you don't need.

#### 4. Document Your Changes

Use the Dockerized `times-excel-reader` tool to generate a summary of the model at `TIMES-NZ/raw_table_summary/raw_tables.txt`. This will help reviewers see the changes you've made to the Excel files by viewing the diff of this text file in the pull request.

After changing the TIMES-NZ model excel files, before committing the changes and making a pull request, please run the following `docker run` command to generate a summary of the new model. Before running the following docker command for the first time, you will need to build the Docker image:
```PowerShell
docker build -t times_excel_reader .
```
This will also need to be done when there are updates to the Dockerfile or `requirements.txt`. Otherwise, you can just run the container as needed with the following `docker run` command:
```PowerShell
docker run -it --rm --name my_times_reader -v ${PWD}/TIMES-NZ:/usr/src/app/TIMES-NZ times_excel_reader
```

Then commit changes that have been made by the script to `TIMES-NZ/raw_table_summary/raw_tables.txt`, alongside your changes to the excel workbooks. These changes will be visible if you run `git diff` before committing.

**Note:**

* If you are unable to run the `times-excel-reader` tool on your machine, you can open a pull request without changing the `raw_tables.txt` file. The GitHub Actions check will fail on your PR, and the check will create an artifact containing the updated `raw_tables.txt`. You can download this and update the one on your branch instead.

* The `times-excel-reader` tool generates file paths with forward slashes (`/`). If you're working on Windows, the file paths in the `raw_tables.txt` may contain backslashes (`\`). To maintain consistency across environments, we recommend running the tool in a Linux-like environment (e.g., using WSL on Windows) or normalizing file paths using a tool like `sed` before committing your changes.


#### 5. Commit Your Changes

After you've made some changes, you need to "commit" them. This takes a snapshot of your changes, which you can then push to GitHub. **Important**: Please take care to ensure that only changes you intend to commit are committed!

Command line:
```PowerShell
# Add changes to the staging area
git status
git add [specific changed file or files related to commit]
# Commit the changes
git commit -m "Your descriptive commit message"
```

GitHub Desktop: In the Changes tab, write a commit message summarizing your changes and click "Commit to [branch name]".

#### 6. Push Your Changes

After committing, you need to "push" your changes to GitHub. This makes them available to others.

Command line:
```PowerShell
git push --set-upstream origin <your-branch-name>
```

GitHub Desktop: Click the "Push origin" button in the toolbar.

#### 7. Create a Pull Request

Finally, you can ask for your changes to be merged into the main branch by creating a "pull request". 

Go to the repository on GitHub, and click on the "Pull request" button. Select your branch from the dropdown, write a brief description of your changes, and click "Create pull request".

---

## Usage

Guide on getting started with the TIMES-NZ model stored here: https://github.com/EECA-NZ/TIMES-NZ-internal-guide-EECA

---

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please ensure that you have the necessary dependencies installed, as outlined at the beginning of this document.
