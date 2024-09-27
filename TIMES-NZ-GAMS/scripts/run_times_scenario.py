"""
Run a TIMES scenario and convert the results to VEDA format.

This script runs a TIMES scenario and converts the results to VEDA format. The scenario directory
is expected to contain the following files:

- A GAMS run file named "{scenario}.run".
- A VEDA data dictionary file named "times2veda.vdd".

The script will prompt the user to enter the scenario name if it is not provided as an argument.
"""


import os
import sys
import subprocess
from pathlib import Path

def get_scenario_names(scenarios_dir):
    """
    Get the names of the scenarios in the given directory.

    Arguments:
        scenarios_dir: Directory containing the scenarios.

    Returns:
        List of scenario names.
    """
    return [d.name for d in scenarios_dir.iterdir() if d.is_dir() and any(d.glob('*.dd'))]

def run_scenario(scenario=None):
    """
    Run a TIMES scenario and convert the results to VEDA format.

    Arguments:
    
            scenario: Name of the scenario to run. If not provided, the user will be
            prompted to enter the scenario name.

    The scenario directory is expected to contain the following files:

        - A GAMS run file named "{scenario}.run".
        - A VEDA data dictionary file named "times2veda.vdd".

    """
    original_dir = Path(__file__).resolve().parents[1]
    scenarios_dir = original_dir / "times_scenarios"
    try:
        if scenario is None:
            scenarios = get_scenario_names(scenarios_dir)
            scenario_list = ", ".join(scenarios)
            scenario = input(f"Enter the scenario name [Available: {scenario_list}]: ")
        scenario_dir = scenarios_dir / scenario
        if not scenario_dir.exists():
            print(f"Scenario directory not found: {scenario}")
            return
        os.chdir(scenario_dir)
        source_dir_relative = "../../etsap-TIMES"
        gams_save_dir = original_dir / "GAMSSAVE"
        if (scenario_dir / f"{scenario}.run").exists() and \
            (scenario_dir / "times2veda.vdd").exists():
            os.makedirs(gams_save_dir, exist_ok=True)
            gams_command = f"GAMS {scenario}.run IDIR={source_dir_relative} \
                GDX={gams_save_dir / scenario} PS=99999 r={source_dir_relative}\\_times"
            print("Running GAMS with command:", gams_command)
            subprocess.run(gams_command, shell=True, check=True)
            gdx2veda_command = f"GDX2VEDA {gams_save_dir / scenario} times2veda.vdd {scenario}"
            print("Running GDX2VEDA with command:", gdx2veda_command)
            subprocess.run(gdx2veda_command, shell=True, check=True)
        else:
            print("Necessary files missing to run the scenario:", scenario)
    except subprocess.CalledProcessError as error:
        print("An error occurred while running the command:", error)
    except Exception as error: # pylint: disable=broad-except
        print("An error occurred:", error)
    finally:
        os.chdir(original_dir)

if __name__ == "__main__":
    SCENARIO_NAME = sys.argv[1] if len(sys.argv) > 1 else None
    run_scenario(SCENARIO_NAME)
