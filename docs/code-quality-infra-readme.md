# Code Quality Infrastructure Setup

[Back to Main Documentation](../README.md)

![ci-and-deploy](https://github.com/EECA-NZ/eeca-python-template/actions/workflows/ci-and-deploy.yml/badge.svg)
[Test Coverage Report](https://eeca-nz.github.io/eeca-python-template/htmlcov)

This guide describes the code-quality infrastructure for this repository, including workflows for linting, testing, and dependency auditing.

Package and dependency management is handled using poetry.

## Features
*   **Code Formatting:** Enforces consistent code style with Black and Isort.
*   **Linting:** Analyzes code quality using Pylint.
*   **Dependency Auditing:** Uses pip-audit to detect known vulnerabilities in the Python dependencies.
*   **Testing:** Runs tests using Pytest and reports coverage with Coverage.py.
*   **Pre-commit Hooks:** Automates code formatting, linting, and dependency auditing before commits and pushes.
*   **Continuous Integration:** GitHub Actions workflows automate linting, testing, and dependency auditing on each push and pull request.
*   **Dependabot for Automated Updates:** A `.github/dependabot.yml` file keeps Python dependencies and GitHub Action versions updated.

## How to Use
It is assumed that the developer is working in Ubuntu (within `WSL` on an EECA laptop).

## 1. Initial one‑time setup (per machine)

```bash
# WSL (Ubuntu) assumed

# 1. Clone the repo (with submodules & LFS)
git clone --recurse-submodules git@github.com:EECA-NZ/TIMES-NZ-Model-Files.git

# 2. Install Git LFS and enable it (only once per machine)
sudo apt-get install git-lfs
git lfs install

# 3. Install Poetry (if you don't have it yet)
curl -sSL https://install.python-poetry.org | python3 -

# 4. Ensure consistent line‑ending behaviour
git config --global core.autocrlf input

# Git, .gitattributes and .editorconfig in the repo keep line‑endings and IDE settings consistent across platforms.
```

---

## 2. Configuring the Python environment

All Python code lives inside packages defined in subdirectories such as **`PREPARE-TIMES-NZ/`** and is managed by **Poetry**.

1. **Enter `PREPARE-TIMES-NZ`** and install package.
    ```bash
    cd PREPARE-TIMES-NZ
    poetry install --with dev
    ```

1.  **Still in `PREPARE-TIMES-NZ`, Install Pre-commit Hooks:**
    ```bash
    poetry run pre-commit install
    poetry run pre-commit install --hook-type pre-push
    ```

    This installs Git hooks specified in `.pre-commit-config.yaml`:
    *   On **commit**, fast checks (`black`, `isort`, `pylint` on staged files) are run.
    *   On **push**, thorough checks (`pip-audit`) are run.

1.  **Start Developing:**
    *   Develop the Python package in the `src/` directory.
    *   Write tests in the `tests/` directory.
    *   Write scripts in the `scripts/` directory.

1.  **Running Tests Locally:**
    ```bash
    poetry run pytest
    ```

1. **Run the tests locally with coverage:**
    ```bash
    poetry run coverage run -m pytest
    poetry run coverage report
    poetry run coverage html
    ```

1. **Running Linters and Formatters Locally:**
    *   Black and Isort:
        ```bash
        poetry run black $(git ls-files "*.py")
        poetry run isort $(git ls-files "*.py")
        ```

1. **Ensure Code Quality Before Pushing:**
    *   Ensure all tests pass and code adheres to style guidelines.
    *   Fix any reported vulnerabilities found by `pip-audit`.
    *   Run `pre-commit run --all-files` to ensure all existing files conform to the hooks.

## Viewing Coverage Reports on GitHub Pages
This template repository is configured to generate coverage reports using Coverage.py during GitHub Actions workflows. The reports are automatically pushed to the `gh-pages` branch.

### Steps to Enable GitHub Pages:

1.  **Navigate to Repository Settings:**
    *   Go to your repository on GitHub.
    *   Click the **Settings** tab.

2.  **Enable GitHub Pages:**
    *   In the sidebar, click **Pages** (or scroll down to the GitHub Pages section).
    *   Under **Source**, select the `gh-pages` branch and the `/ (root)` folder.
    *   Click **Save**.

3.  **Update the Coverage Report Link:**
    *   Your coverage report will be available at:
        ```
        https://[your-username].github.io/[your-repository-name]/htmlcov/
        ```
    *   Replace `[your-username]` and `[your-repository-name]` accordingly.

Example: For this template repository:
`https://eeca-nz.github.io/eeca-python-template/htmlcov/`

### Note that:

*   It may take a few minutes for GitHub Pages to become active.
*   The coverage report is updated each time tests are run in GitHub Actions.

## Notes on Pre-commit:
*   **Configuration:** The `.pre-commit-config.yaml` file defines the pre-commit hooks.
*   **Hooks Behavior:**

    *   Before running any checks, the hooks verify that the `.venv` virtual environment is activated. This ensures that the correct versions of tools and dependencies are used.
    *   On commit:
        *   Runs **Black**, **Isort**, and **Pylint (staged files only)**.
    *   On push:
        *   Runs **Pylint (entire codebase)** and **pip-audit** to catch broader issues and security vulnerabilities.

*   **Automatic Formatting and Checking:**
    If any formatter modifies files or a check fails, the commit will be blocked. After fixing issues or adding modified files, commit again.

*   **Skipping Hooks (not recommended):**
    ```bash
    git commit --no-verify
    ```

    Use only when necessary, e.g., for urgent hotfixes.
