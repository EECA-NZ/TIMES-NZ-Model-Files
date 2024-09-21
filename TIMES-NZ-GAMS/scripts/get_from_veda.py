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
    scenario_dir = scenarios_dir / scenario
    if scenario_dir.exists():
        confirm = input(f"Scenario directory already exists: {scenario_dir}. Clear it? [y/n]: ")
        if confirm.lower() == 'y':
            print("Clear the directory to avoid any outdated files")
            shutil.rmtree(scenario_dir)
        else:
            print("Aborting.")
            exit()
    os.makedirs(scenario_dir, exist_ok=True)
    return scenario_dir

def copy_files_to_scenario(veda_working_dir, scenario_dir, scenario):
    file_patterns = ['*.dd', f'{scenario}.run', 'cplex.opt', 'times2veda.vdd']
    for pattern in file_patterns:
        for file in Path(veda_working_dir / scenario).glob(pattern):
            shutil.copy(file, scenario_dir)

def main(veda_working_dir, scenario):
    if veda_working_dir is None:
        veda_working_dir = find_veda_working_directory()
        if veda_working_dir is None:
            print("VEDA working directory could not be found automatically. Please enter the directory manually.")
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
    veda_dir = sys.argv[1] if len(sys.argv) > 1 else None
    scenario_name = sys.argv[2] if len(sys.argv) > 2 else None
    main(veda_dir, scenario_name)