import subprocess
import sys
import os

def run_commands(version):
    # Base directory
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

    version_str = version.replace(".", "_")

    # Define commands with absolute paths
    commands = [
        f"python {os.path.join(base_dir, 'TIMES-NZ-GAMS', 'scripts', 'get_from_veda.py')} kea-v{version_str}",
        f"python {os.path.join(base_dir, 'TIMES-NZ-GAMS', 'scripts', 'get_from_veda.py')} tui-v{version_str}",
        f"python {os.path.join(base_dir, 'TIMES-NZ-GAMS', 'scripts', 'run_times_scenario.py')} kea-v{version_str}",
        f"python {os.path.join(base_dir, 'TIMES-NZ-GAMS', 'scripts', 'run_times_scenario.py')} tui-v{version_str}",
        f"python {os.path.join(base_dir, 'TIMES-NZ-OUTPUT-PROCESSING', 'scripts', 'fetch_items_lists.py')}",
        f"python {os.path.join(base_dir, 'TIMES-NZ-OUTPUT-PROCESSING', 'scripts', 'add_human_readable_data_labels.py')} {version}",
        f"Rscript.exe {os.path.join(base_dir, 'TIMES-NZ-VISUALISATION', 'scripts', 'loadData.R')} {version}",
        f"Rscript.exe {os.path.join(base_dir, 'TIMES-NZ-VISUALISATION', 'scripts', 'runApp.R')}"
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
        else:
            print("Command executed successfully")

if __name__ == "__main__":
    # Check if the version argument is provided
    if len(sys.argv) < 2:
        print("Usage: python script_name.py <version_number>")
        sys.exit(1)

    # Extract the version number from command line argument
    version_number = sys.argv[1]
    run_commands(version_number)
