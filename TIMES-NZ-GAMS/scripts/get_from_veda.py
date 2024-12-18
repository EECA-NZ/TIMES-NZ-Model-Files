"""
This script copies the necessary files from the VEDA working directory
to the scenario directory.

Usage:
    python get_from_veda.py [SCENARIO_NAME] [VEDA_DIR]

Arguments:
    SCENARIO_NAME: Name of the scenario to copy files for.
    VEDA_DIR: Path to the VEDA working directory. If not provided,
    the script will try to find it automatically.

The script will prompt the user to enter the scenario name if it is
not provided as an argument.

If the VEDA working directory is not provided, the script will try
to find it automatically.

If the VEDA working directory is not found automatically, the user will
be prompted to enter the directory manually.
"""
import os
import sys
from pathlib import Path
import shutil

def find_veda_working_directory(base_dir=None):
    """
    Finds the VEDA working directory under the given base directory.

    Arguments:
        base_dir: Base directory to search for the VEDA working directory.
        If not provided, the home directory will be used.

    Returns:
        Path to the VEDA working directory if found, otherwise None.

    The VEDA working directory is expected to be named "*veda*" and contain
    a subdirectory named "GAMS_WrkTIMES".
    """
    if base_dir is None:
        base_dir = Path.home()
    for dir_path in base_dir.glob('*veda*'):
        if dir_path.is_dir():
            for sub_dir_path in dir_path.rglob('GAMS_WrkTIMES'):
                if sub_dir_path.is_dir():
                    print("VEDA working directory found:", sub_dir_path)
                    return sub_dir_path
    print(f"VEDA working directory not found under {base_dir}.")
    return None

def setup_scenario_directory(scenarios_dir, scenario):
    """
    Creates the scenario directory and clears it if it already exists.

    Arguments:
        scenarios_dir: Directory to store the scenarios.
        scenario: Name of the scenario.

    Returns:
        Path to the scenario directory.

    If the scenario directory already exists, it will be cleared before returning the path.

    The scenario directory will be created under the scenarios directory with the given name.
    """
    scenario_dir = scenarios_dir / scenario
    if scenario_dir.exists():
        print(f"Scenario directory already exists: {scenario_dir}. Clearing it.")
        shutil.rmtree(scenario_dir)
    os.makedirs(scenario_dir, exist_ok=True)
    return scenario_dir

def copy_files_to_scenario(veda_working_dir, scenario_dir, scenario):
    """
    Copies the necessary files from the VEDA working directory to the scenario directory.

    Arguments:

        veda_working_dir: Path to the VEDA working directory.

        scenario_dir: Path to the scenario directory.

        scenario: Name of the scenario.

    The following files will be copied from the VEDA working directory to the scenario directory:

        - All files with the extension ".dd"
        - The file "{scenario}.run"
        - The file "cplex.opt"
        - The file "times2veda.vdd"
    """
    file_patterns = ['*.dd', f'{scenario}.run', 'cplex.opt', 'times2veda.vdd']
    for pattern in file_patterns:
        for file in Path(veda_working_dir / scenario).glob(pattern):
            shutil.copy(file, scenario_dir)

def main(veda_working_dir, scenario):
    """
    Main function to copy files from the VEDA working directory to the scenario directory.

    Arguments:
    
            veda_working_dir: Path to the VEDA working directory.
    
            scenario: Name of the scenario to copy files for.   
    """
    if veda_working_dir is None:
        veda_working_dir = find_veda_working_directory()
        if veda_working_dir is None:
            print("VEDA working directory could not be found automatically. \
                  Please enter the directory manually.")
            return
    if scenario is None:
        try:
            scenarios = [f.name for f in Path(veda_working_dir).iterdir() if f.is_dir()]
        except FileNotFoundError:
            print(f"VEDA working directory not found: {veda_working_dir}")
            return
        scenario_list = ", ".join(scenarios)
        scenario = input(f"Enter the scenario name [Available: {scenario_list}]: ")

    original_dir = Path.cwd().parent
    scenarios_dir = original_dir / "times_scenarios"
    os.makedirs(scenarios_dir, exist_ok=True)

    scenario_dir = setup_scenario_directory(scenarios_dir, scenario)
    copy_files_to_scenario(veda_working_dir, scenario_dir, scenario)
    print(f"Files successfully copied to scenario directory: {scenario_dir}")

if __name__ == "__main__":
    os.chdir(Path(__file__).parent)
    SCENARIO_NAME = sys.argv[1] if len(sys.argv) > 1 else None
    VEDA_DIR = sys.argv[2] if len(sys.argv) > 2 else None
    main(VEDA_DIR, SCENARIO_NAME)
