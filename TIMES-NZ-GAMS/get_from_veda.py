import os
import sys
from pathlib import Path
import shutil

def find_veda_working_directory(base_dir=None):
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
    # Create the specific directory for the given scenario
    scenario_dir = scenarios_dir / scenario
    if scenario_dir.exists():
        # prompt user to confirm deletion of existing directory
        confirm = input(f"Scenario directory already exists: {scenario_dir}. Clear it? [y/n]: ")
        if confirm.lower() == 'y':
            print("Clear the directory to avoid any outdated files")
            shutil.rmtree(scenario_dir)
        else:
            # Exit if the user does not confirm deletion
            print("Aborting.")
            exit()
    os.makedirs(scenario_dir, exist_ok=True)  # Create the scenario directory anew
    return scenario_dir

def copy_files_to_scenario(veda_working_dir, scenario_dir, scenario):
    # Define the file patterns to copy from the VEDA working directory
    file_patterns = ['*.dd', f'{scenario}.run', 'cplex.opt', 'times2veda.vdd']
    for pattern in file_patterns:
        for file in Path(veda_working_dir / scenario).glob(pattern):
            shutil.copy(file, scenario_dir)

def main(veda_working_dir, scenario):
    if veda_working_dir is None:
        # Use the automatic search function to find the VEDA working directory
        veda_working_dir = find_veda_working_directory()
        if veda_working_dir is None:
            print("VEDA working directory could not be found automatically. Please enter the directory manually.")
            return

    if scenario is None:
        # Get available scenario names
        try:
            scenarios = [f.name for f in Path(veda_working_dir).iterdir() if f.is_dir()]
        except FileNotFoundError:
            print(f"VEDA working directory not found: {veda_working_dir}")
            return
        scenario_list = ", ".join(scenarios)
        # Prompt user for the scenario name
        scenario = input(f"Enter the scenario name [Available: {scenario_list}]: ")

    # Setup the scenario directory
    original_dir = Path.cwd()
    scenarios_dir = original_dir / "scenarios"
    os.makedirs(scenarios_dir, exist_ok=True)  # Ensure the 'scenarios' directory exists
    
    # Setup the scenario directory after all checks have passed
    scenario_dir = setup_scenario_directory(scenarios_dir, scenario)

    # Copy necessary files
    copy_files_to_scenario(veda_working_dir, scenario_dir, scenario)
    print(f"Files successfully copied to scenario directory: {scenario_dir}")

if __name__ == "__main__":
    veda_dir = sys.argv[1] if len(sys.argv) > 1 else None
    scenario_name = sys.argv[2] if len(sys.argv) > 2 else None
    main(veda_dir, scenario_name)
