# we just want to run this script to pull in some new vd files real quick so we can run the delta checks 

import os 
import subprocess 
import sys 
from pathlib import Path



scenario_to_run = "tui-v2_1_3_iat" # change me! 

# get custom libraries
current_dir = Path(__file__).resolve().parent
sys.path.append(os.path.join(current_dir, "..", "library"))
from config import  TIMES_LOCATION



gams_script_dir = os.path.join(TIMES_LOCATION, "TIMES-NZ-GAMS", "scripts")


commands = [
    f"python {os.path.join(gams_script_dir, 'get_from_veda.py')} {scenario_to_run}",
    f"python {os.path.join(gams_script_dir, 'run_times_scenario.py')} {scenario_to_run}"
]
    
    



for command in commands:
        print(f"Running command: {command}")
        # Run the command using subprocess
        process = subprocess.run(command, shell=True, check=True, text=True)
        # Check if the command was successful
        if process.returncode != 0:
            print(f"Command failed with return code {process.returncode}")
            break
        print("Command executed successfully")