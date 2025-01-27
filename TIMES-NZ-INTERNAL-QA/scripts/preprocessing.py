import os
import subprocess

run_to_process = "tui-v2_1_3_iat"

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
gams_script_dir = os.path.join(base_dir, "TIMES-NZ-GAMS", "scripts")

commands = [


        f"python {os.path.join(gams_script_dir, 'get_from_veda.py')} {run_to_process}",
        f"python {os.path.join(gams_script_dir, 'run_times_scenario.py')} {run_to_process}",
        
    ]

    # Run each command in sequence
for command in commands:
    print(f"Running command: {command}")
    # Run the command using subprocess
    process = subprocess.run(command, shell=True, check=True, text=True)
    # Check if the command was successful
    if process.returncode != 0:
        print(f"Command failed with return code {process.returncode}")
        break
    print("Command executed successfully")