import os
import sys
import subprocess
from pathlib import Path

def get_scenario_names(scenarios_dir):
    return [d.name for d in scenarios_dir.iterdir() if d.is_dir() and any(d.glob('*.dd'))]

def run_scenario(scenario=None):
    original_dir = Path.cwd()
    scenarios_dir = original_dir / "scenarios"  # Path to the scenarios directory
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
        # Check if necessary files exist before running GAMS and GDX2VEDA
        if (scenario_dir / f"{scenario}.run").exists() and (scenario_dir / "times2veda.vdd").exists():
            # Ensure the GAMSSAVE directory exists
            os.makedirs(gams_save_dir, exist_ok=True)
            # Run GAMS to solve the scenario, maintaining relative paths for IDIR and r
            gams_command = f"GAMS {scenario}.run IDIR={source_dir_relative} GDX={gams_save_dir / scenario} PS=99999 r={source_dir_relative}\_times"
            print("Running GAMS with command:", gams_command)
            subprocess.run(gams_command, shell=True)
            # Run GDX2VEDA to convert the GDX file to VEDA format
            gdx2veda_command = f"GDX2VEDA {gams_save_dir / scenario} times2veda.vdd {scenario}"
            print("Running GDX2VEDA with command:", gdx2veda_command)
            subprocess.run(gdx2veda_command, shell=True)
        else:
            print("Necessary files missing to run the scenario:", scenario)
    except Exception as e:
        print("An error occurred:", e)
    finally:
        # Return to the original directory
        os.chdir(original_dir)

if __name__ == "__main__":
    scenario_name = sys.argv[1] if len(sys.argv) > 1 else None
    run_scenario(scenario_name)
