 # GitHub flow guide

If you're new to Git and GitHub, this guide shows how to use the standard [GitHub Flow](https://docs.github.com/en/get-started/quickstart/github-flow), augmented to track changes in the Excel configuration workbooks.

## Prerequisites

- Make sure you have Git installed on your machine. You can download it from here: https://git-scm.com/downloads.

## Steps

### 1. Clone the Repository

First, you'll need to make a copy of this repository on your local machine. This is called "cloning". If you're using command line, use the following command:
```PowerShell
git clone git@github.com:EECA-NZ/TIMES-NZ-Model-Files.git
```
or alternatively:
```PowerShell
git clone https://github.com/EECA-NZ/TIMES-NZ-Model-Files.git
```

### 2. Ensure your repository is in a clean state and on the head of `main`

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

### 3. Create a Branch

Before making changes, create a new branch. This keeps your changes isolated until they're ready to be merged into the main branch. After ensuring you are on the head of the `main` branch, here's how you can branch from it:

Command line:
```PowerShell
git checkout -b <your-branch-name>
```
This command has two effects:
* it branches from your current location in the git project (the head of main) and creates a new branch, named <your-branch-name>, which currently exists only on your local machine
* it switches your local copy of the git repository to be that branch
Any changes that you now commit will be committed to that branch, so you can modify the model without affecting the `main` branch until you are ready to merge the changes.

### 4. Make Your Changes

Now you can start making changes to the code. You can create new files, modify existing ones, and delete what you don't need. Keep your changes focused and related to a single feature or fix.

### 5. Test Your Changes

When changes are trivial, ensure that they haven't affected model behaviour by noting the value of the objective function on model convergence before and after the change.

### 6. Commit Your Changes

After you've made some changes, you need to "commit" them. This takes a snapshot of your changes, which you can then push to GitHub. **Important**: Please take care to ensure that only changes you intend to commit are committed!

Command line:
```PowerShell
# Add changes to the staging area
git status
git add [specific changed file or files related to commit]
# Commit the changes
git commit -m "Your descriptive commit message"
```

### 7. Push Your Changes

After committing, you need to "push" your changes to GitHub. This makes them available to others.

Command line:
```PowerShell
git push --set-upstream origin <your-branch-name>
```

### 8. Create a Pull Request

Finally, you can ask for your changes to be merged into the main branch by creating a "pull request".

Go to the repository on GitHub, and click on the "Pull request" button. Select your branch from the dropdown, write a brief description of your changes, and click "Create pull request".

### 9. Pull latest changes

Incorporates changes from a remote repository into the current branch. If the current branch is behind the remote, then by default it will fast-forward the current branch to match the remote. For instance, as before, to ensure you are on the head of the `main` branch:
Command line:
```PowerShell
git checkout main
git pull
```
