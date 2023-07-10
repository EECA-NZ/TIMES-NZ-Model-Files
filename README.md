# TIMES-NZ-Model-Files

## Model excel files for TIMES-NZ

Guide on getting started with the TIMES-NZ model stored here: https://github.com/EECA-NZ/TIMES-NZ-internal-guide-EECA

## Installation

Here's how to get the project installed on your local machine for development:

```bash
git clone git@github.com:EECA-NZ/TIMES-NZ-Model-Files.git
cd TIMES-NZ-Model-Files
```

## Working with Git & GitHub

If you're new to Git and GitHub, here's a simple guide on how to get started.

### Prerequisites

- Make sure you have Git installed on your machine. You can download it from here: https://git-scm.com/downloads.
- If you prefer a graphical user interface, GitHub Desktop is a good option. You can download it here: https://desktop.github.com/.

### Steps

#### 1. Clone the Repository

First, you'll need to make a copy of this repository on your local machine. This is called "cloning". If you're using command line, use the following command:

```bash
git clone git@github.com:EECA-NZ/TIMES-NZ-Model-Files.git
```

If you're using GitHub Desktop, you can clone the repository by selecting "File -> Clone Repository" from the menu, and then select the repository from the list.

#### 2. Create a Branch

Before making changes, it's best practice to create a new branch. This keeps your changes isolated until they're ready to be merged into the main branch. Here's how you can do it:

Command line:
```bash
git checkout -b <your-branch-name>
```

GitHub Desktop: Select "Branch -> New Branch" from the menu, and enter your branch name.

#### 3. Make Your Changes

Now you can start making changes to the code. You can create new files, modify existing ones, and delete what you don't need.


#### 4. Document Your Changes
Use the python script `utils/raw_table_summary.py` to generate a summary of the model. This will help reviewers understand the changes made.

We recommend using a Python virtual environment:
```bash
python3 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

After changing the TIMES-NZ model excel files, before committing the changes and making a pull request, please run `times_excel_summary.py` in the utils subdirectory to generate a summary of the new model.
```bash
.venv/Scripts/Activate.ps1
cd utils
python .\raw_table_summary.py
```
Then commit changes that have been made by the script to `TIMES-NZ/raw_table_summary/raw_tables.txt`, alongside your changes to the excel workbooks. These changes will be visible if you run `git diff` before committing.

#### 4. Commit Your Changes

After you've made some changes, you need to "commit" them. This takes a snapshot of your changes, which you can then push to GitHub.

Command line:
```bash
# Add changes to the staging area
git add .
# Commit the changes
git commit -m "Your descriptive commit message"
```

GitHub Desktop: In the Changes tab, write a commit message summarizing your changes and click "Commit to [branch name]".

#### 5. Push Your Changes

After committing, you need to "push" your changes to GitHub. This makes them available to others.

Command line:
```bash
git push origin <your-branch-name>
```

GitHub Desktop: Click the "Push origin" button in the toolbar.

#### 6. Create a Pull Request

Finally, you can ask for your changes to be merged into the main branch by creating a "pull request". 

Go to the repository on GitHub, and click on the "Pull request" button. Select your branch from the dropdown, write a brief description of your changes, and click "Create pull request".

---

## Usage

Guide on getting started with the TIMES-NZ model stored here: https://github.com/EECA-NZ/TIMES-NZ-internal-guide-EECA

---

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.