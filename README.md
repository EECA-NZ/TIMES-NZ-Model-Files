# TIMES-NZ-Model-Files

## Excel Model Configuration Files for TIMES-NZ

This repository houses the Excel files defining the TIMES-NZ (The Integrated MARKAL-EFOM System - New Zealand) energy system model configuration. It is intended for use by researchers and analysts working with energy models in New Zealand.
* For a guide on getting started with the TIMES-NZ model, refer to the [TIMES-NZ-internal-guide-EECA](https://github.com/EECA-NZ/TIMES-NZ-internal-guide-EECA) repository.
* For step by step system configuration instructions, refer to the [SystemConfigurationGuide.md](docs/SystemConfigurationGuide.md) file in this repository.
* For detailed documentation on the workbooks and their contents, refer to the structured documentation in the [docs](docs/README.md) directory.

## Integrated Workflow Across Repositories

The TIMES-NZ project is divided across three main repositories, each serving a distinct purpose in the overall modeling and visualization process. The repositories and their functions are as follows:

1. [TIMES-NZ-Model-Files](https://github.com/EECA-NZ/TIMES-NZ-Model-Files): Houses the Excel files defining the TIMES-NZ energy system model configuration, along with additional resources and tools for change tracking.

2. [TIMES-NZ-GAMS-Files](https://github.com/EECA-NZ/TIMES-NZ-GAMS-Files): Contains the GAMS model files for TIMES-NZ scenarios and scripts to enable reproducible scenario execution.

3. [TIMES-NZ-Visualisation](https://github.com/EECA-NZ/TIMES-NZ-Visualisation): Provides a tool for visualizing the results of TIMES-NZ scenarios using an RShiny application.

### High-Level Workflow Overview

#### Step 1: Model Configuration and Release Tagging
- Begin by configuring the TIMES-NZ model in the TIMES-NZ-Model-Files repository, and using VEDA to run the model. Work is done in a development branch and merged to the main branch after review - i.e. we follow the standard [GitHub Flow](https://docs.github.com/en/get-started/quickstart/github-flow).
- When ready to release a new version of the model, name your scenarios to include the release tag (use the naming convention `kea-v2_1_2` where kea is an identifier for the scenario set, and v2_1_2 indicates the version number).
- Once the configuration is complete and scenarios are named, commit your changes and tag the release (e.g., v2.1.2).
Release tagging allows users and collaborators to easily identify and revert to specific versions of the model.

#### Step 2: Scenario Execution with GAMS
- Move to the TIMES-NZ-GAMS-Files repository. Ensure that your local environment is set up correctly with GAMS installed, including a valid license. Verify that the version of GAMS you're using is compatible with the model files.
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
- Ensure that the file paths are correctly set in the script to avoid any file not found errors.
- Run the data extraction script in the `data_cleaning` subdirectory to process the output and generate a file ready for visualization (e.g., to process a scenario named tui-v2_1_2, you might run a script that generates a file named tui-v2_1_2.rda).
- After running the extraction script, it's a good practice to verify the integrity of the generated data file. Check for any inconsistencies or missing data that might impact the accuracy of your visualizations.

#### Step 4: Visualization with RShiny
- Launch the RShiny application to visualize the scenario results interactively.
- Navigate to the directory where the RShiny application files for TIMES-NZ are stored. This should be within your local copy of the TIMES-NZ-Visualisation repository.
- Ensure that you have R and the Shiny package installed on your machine. If not, you can install them from the Comprehensive R Archive Network (CRAN).
- Open an R console and set the working directory to the location of the RShiny application files.
- Run the RShiny application by executing the app script, usually with a command like `shiny::runApp()`.

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

### Steps

#### 1. Clone the Repository

First, you'll need to make a copy of this repository on your local machine. This is called "cloning". If you're using command line, use the following command:
```PowerShell
git clone git@github.com:EECA-NZ/TIMES-NZ-Model-Files.git
```
or if you have not yet configured your GitHub account with ssh keys for your laptop (instructions to do so [here](./docs/SystemConfigurationGuide.md)):
```PowerShell
git clone https://github.com/EECA-NZ/TIMES-NZ-Model-Files.git
```

#### 2. Ensure your repository is in a clean state and on the head of `main`

After the clone, you can list the tags with `git tag -l` and then checkout a specific tag:
```PowerShell
git checkout tags/<tag_name>
```
This allows us to roll back our model to earlier releases and replicate earlier results. However, for improving the model, our development pattern is to work from the head of the `main` branch. Before making any changes, ensure that you are on the head of `main` by running
```PowerShell
git checkout main
git pull
```
These commands ensure you are working from the most up-to-date state of the project: the head of the main branch. To get the above commands to work, you may need to discard any local changes that you don't need. You can do this by identifying any local changes using
```PowerShell
git status
```
which will list any modified files, new files not under version control and other local uncommitted changes to the project. Revert all of these by first (important!) backing up any changes that you want to retain, then running
```PowerShell
rm <any-local-untracked-file-that-is-not-part-of-the-project>
git checkout <any-local-file-that-has-changes-to-discard>
```
when you have completely tidied up your local copy of the repo, and moved to the head of `main`, running `git status` will produce a very minimal output that looks like
```
On branch main
Your branch is up to date with 'origin/main'.

nothing to commit, working tree clean
```

#### 3. Create a Branch

Before making changes, create a new branch. This keeps your changes isolated until they're ready to be merged into the main branch. After ensuring you are on the head of the `main` branch, here's how you can branch from it:

Command line:
```PowerShell
git checkout -b <your-branch-name>
```
This command has two effects:
* it branches from your current location in the git project (the head of main) and creates a new branch, named <your-branch-name>, which currently exists only on your local machine
* it switches your local copy of the git repository to be that branch
Any changes that you now commit will be committed to that branch, so you can modify the model without affecting the `main` branch until you are ready to merge the changes.

#### 4. Make Your Changes

Now you can start making changes to the code. You can create new files, modify existing ones, and delete what you don't need. Keep your changes focused and related to a single feature or fix.

#### 5. Document Your Changes

Use the Dockerized `times-excel-reader` tool to generate a summary of the model at `TIMES-NZ/raw_table_summary/raw_tables.txt`. This will help reviewers see the changes you've made to the Excel files by viewing the diff of this text file in the pull request.

After changing the TIMES-NZ model excel files, before committing the changes and making a pull request, please run the following `docker run` command to generate a summary of the new model. Before running the following docker command for the first time, you will need to build the Docker image:
```PowerShell
docker build -t times_excel_reader .
```
This will also need to be done when there are updates to the Dockerfile or `requirements.txt`. Otherwise, you can just run the container as needed with the following `docker run` command:
```PowerShell
docker run -it --rm --name my_times_reader -v ${PWD}/TIMES-NZ:/usr/src/app/TIMES-NZ times_excel_reader
```

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
If you have changed the TIMES configuration files, one of the files you commit should be `TIMES-NZ/raw_table_summary/raw_tables.txt`. 

#### 6. Push Your Changes

After committing, you need to "push" your changes to GitHub. This makes them available to others.

Command line:
```PowerShell
git push --set-upstream origin <your-branch-name>
```

#### 7. Create a Pull Request

Finally, you can ask for your changes to be merged into the main branch by creating a "pull request". 

Go to the repository on GitHub, and click on the "Pull request" button. Select your branch from the dropdown, write a brief description of your changes, and click "Create pull request".

#### 8. Pull latest changes

Incorporates changes from a remote repository into the current branch. If the current branch is behind the remote, then by default it will fast-forward the current branch to match the remote. For instance, as before, to ensure you are on the head of the `main` branch:
Command line:
```PowerShell
git checkout main
git pull
```

---

## Usage

Guide on getting started with the TIMES-NZ model stored here: https://github.com/EECA-NZ/TIMES-NZ-internal-guide-EECA

---

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please ensure that you have the necessary dependencies installed, as outlined at the beginning of this document.
