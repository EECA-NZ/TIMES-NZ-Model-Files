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

Use the Dockerized `times-excel-reader` tool to generate a summary of the model at `TIMES-NZ/raw_table_summary/raw_tables.txt`. This will help reviewers see the changes you've made to the Excel files by viewing the diff of this text file in the pull request.

After changing the TIMES-NZ model excel files, before committing the changes and making a pull request, please run the following `docker run` command to generate a summary of the new model. Before running the following docker command for the first time, you will need to build the Docker image:
```bash
docker build -t times_excel_reader .
```
This will also need to be done when there are updates to the Dockerfile or `requirements.txt`. Otherwise, you can just run the container as needed with the following `docker run` command:
```bash
docker run -it --rm --name my_times_reader -v ${PWD}/TIMES-NZ:/usr/src/app/TIMES-NZ times_excel_reader
```

Then commit changes that have been made by the script to `TIMES-NZ/raw_table_summary/raw_tables.txt`, alongside your changes to the excel workbooks. These changes will be visible if you run `git diff` before committing.

**Note:**

* If you are unable to run the `times-excel-reader` tool on your machine, you can open a pull request without changing the `raw_tables.txt` file. The GitHub Actions check will fail on your PR, and the check will create an artifact containing the updated `raw_tables.txt`. You can download this and update the one on your branch instead.

* The `times-excel-reader` tool generates file paths with forward slashes (`/`). If you're working on Windows, the file paths in the `raw_tables.txt` may contain backslashes (`\`). To maintain consistency across environments, we recommend running the tool in a Linux-like environment (e.g., using WSL on Windows) or normalizing file paths using a tool like `sed` before committing your changes.


#### 5. Commit Your Changes

After you've made some changes, you need to "commit" them. This takes a snapshot of your changes, which you can then push to GitHub.

Command line:
```bash
# Add changes to the staging area
git add .
# Commit the changes
git commit -m "Your descriptive commit message"
```

GitHub Desktop: In the Changes tab, write a commit message summarizing your changes and click "Commit to [branch name]".

#### 6. Push Your Changes

After committing, you need to "push" your changes to GitHub. This makes them available to others.

Command line:
```bash
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