# Code Quality Infrastructure Setup

[Back to Main Documentation](../README.md)

![ci-and-deploy](https://github.com/EECA-NZ/eeca-python-template/actions/workflows/ci-and-deploy.yml/badge.svg)
[Test Coverage Report](https://eeca-nz.github.io/eeca-python-template/htmlcov)

This guide describes the code quality infrastructure for this repository, including workflows for linting, testing, and dependency auditing.

## Features
*   **Code Formatting:** Enforces consistent code style with Black and Isort.
*   **Linting:** Analyzes code quality using Pylint.
*   **Dependency Auditing:** Uses pip-audit to detect known vulnerabilities in the Python dependencies.
*   **Testing:** Runs tests using Pytest and reports coverage with Coverage.py.
*   **Pre-commit Hooks:** Automates code formatting, linting, and dependency auditing before commits and pushes.
*   **Continuous Integration:** GitHub Actions workflows automate linting, testing, and dependency auditing on each push and pull request.
*   **Dependabot for Automated Updates:** A `.github/dependabot.yml` file keeps Python dependencies and GitHub Action versions updated.

## How to Use
It is assumed that the developer is working in Windows Powershell or in Ubuntu (within `wsl` on an EECA laptop).

1.  **Use the Template:**
    *   Click on "Use this template" on the GitHub repository page.
    *   Create a new repository using this template.

2.  **Clone the Repository:**
    ```bash
    git clone git@github.com:<gituser>/<new_repo_name>.git
    ```

3.  **Update Project Metadata:**
    *   Update `pyproject.toml` and, if necessary, add a `setup.py` with your project's details.

4.  **Create and Activate a Virtual Environment:**
    In Ubuntu or WSL:
    ```bash
    python -m venv .venv
    source ./.venv/bin/activate
    ```
    In PowerShell (Windows):
    ```bash
    python -m venv .venv
    .\.venv\Scripts\activate
    ```
    Ensure your virtual environment is activated before running the commands below.

5.  **Install Required Dependencies:**
    ```bash
    python -m pip install --upgrade pip
    python -m pip install -r requirements-dev.txt
    ```

6.  **Install Pre-commit Hooks:**
    ```bash
    pre-commit install
    pre-commit install --hook-type pre-push
    ```

    This installs Git hooks specified in `.pre-commit-config.yaml`:
    *   On **commit**, fast checks (`black`, `isort`, `pylint` on staged files) are run.
    *   On **push**, thorough checks (`pip-audit`) are run.

7.  **Start Developing:**
    *   Develop your Python package in the `src/` directory.
    *   Write tests in the `tests/` directory.

8.  **Running Tests Locally:**
    ```bash
    python -m pytest
    ```

9. **Run the tests locally with coverage:**
    ```bash
    python -m coverage run -m pytest
    python -m coverage report
    python -m coverage html
    ```

11. **Running Linters and Formatters Locally:**
    *   Black and Isort:
        ```bash
        python -m black $(git ls-files "*.py")
        python -m isort $(git ls-files "*.py")
        ```
    *   Full Codebase Pylint (as run pre-push):
        ```bash
        pylint --disable=R0801 $(git ls-files "*.py")
        ```
    *   Pip-Audit:
        ```bash
        pip-audit
        ```

12. **Ensure Code Quality Before Pushing:**
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
*   **Configuration:** The `.pre-commit-config.yaml` file defines the pre-commit and pre-push hooks.
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
