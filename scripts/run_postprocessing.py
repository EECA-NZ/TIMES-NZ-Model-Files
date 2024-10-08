"""
Pipeline script to run all the processes in sequence to generate the visualisation app.
This script:
* fetches "Items Lists" exports from VEDA,
* adds human-readable data labels to the spreadsheets,
* creates summary plot data,
* loads data into the RShiny visualisation, and 
* deploys the visualisation app to RShiny.
"""

import os
import sys
import subprocess


def run_commands(version):
    """
    Run just the postprocessing commands in sequence to generate the visualisation app.
    """
    # Base directory
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    post_script_dir = os.path.join(base_dir, "TIMES-NZ-OUTPUT-PROCESSING", "scripts")
    vis_script_dir = os.path.join(base_dir, "TIMES-NZ-VISUALISATION", "scripts")

    # Define commands with absolute paths
    commands = [
        f"python {os.path.join(post_script_dir, 'fetch_items_lists.py')}",
        f"python {os.path.join(post_script_dir, 'add_human_readable_data_labels.py')} {version}",
        f"python {os.path.join(post_script_dir, 'make_summary_plot_data.py')} {version}",
        f"Rscript.exe {os.path.join(vis_script_dir, 'loadData.R')} {version}",
        f"Rscript.exe {os.path.join(vis_script_dir, 'deployApp.R')} {version}",
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


if __name__ == "__main__":
    # Check if the version argument is provided
    if len(sys.argv) < 2:
        print("Usage: python script_name.py <version_number>")
        sys.exit(1)

    # Extract the version number from command line argument
    VERSION_NUMBER = sys.argv[1]
    run_commands(VERSION_NUMBER)
