"""
This script fetches the latest "Items List" export files from the TIMES `Exported_files` directory,
renames them to remove the timestamp and converts them to CSV. This is to ease the process of updating
the schema generation process with the latest data.

Usage:
* First, using VEDA, export the "Items List" files for Commodity, Commodity Groups, and Process.
* Run this script to fetch the latest files and convert them to CSV:

python scripts/fetch_items_lists.py
"""



import os
import pandas as pd
from datetime import datetime

MYUSER = os.getlogin().lower()
SOURCE_DIR = os.path.join(r"C:\Users", MYUSER, r"TIMES-NZ-Model-Files\TIMES-NZ\Exported_files")
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TARGET_DIR = os.path.join(SCRIPT_DIR, os.pardir, 'data', 'input')

def fetch_and_convert_latest_item_lists(source_directory, target_directory):
    # Define patterns for commodity and process files
    commodity_pattern = "Items List-Commodity("
    commodity_groups_pattern = "Items List-Commodity Groups("
    process_pattern = "Items List-Process("

    # Initialize variables to hold the latest file details
    latest_commodity_file = {"path": None, "datetime": None}
    latest_commodity_groups_file = {"path": None, "datetime": None}
    latest_process_file = {"path": None, "datetime": None}

    # Get the latest files from the source directory
    try:
        files = os.listdir(source_directory)
        assert files
    except:
        warn = f"""\nFiles not found in source directory {source_directory}.
    In the VEDA Items List Module:
        Select Process and click "Export to Excel"
        Select Commodity and click "Export to Excel"
        Select Commodity Groups and click "Export to Excel"
    """
        print(warn)
        return

    # Iterate through files in the source directory
    for file in os.listdir(source_directory):
        if commodity_pattern in file:
            datetime_str = file.split(commodity_pattern)[-1].split(').xlsx')[0]
            datetime_obj = datetime.strptime(datetime_str, "%Y%m%d%H%M%S")
            if latest_commodity_file["datetime"] is None or datetime_obj > latest_commodity_file["datetime"]:
                latest_commodity_file["path"] = os.path.join(source_directory, file)
                latest_commodity_file["datetime"] = datetime_obj
        elif process_pattern in file:
            datetime_str = file.split(process_pattern)[-1].split(').xlsx')[0]
            datetime_obj = datetime.strptime(datetime_str, "%Y%m%d%H%M%S")
            if latest_process_file["datetime"] is None or datetime_obj > latest_process_file["datetime"]:
                latest_process_file["path"] = os.path.join(source_directory, file)
                latest_process_file["datetime"] = datetime_obj
        elif commodity_groups_pattern in file:
            datetime_str = file.split(commodity_groups_pattern)[-1].split(').xlsx')[0]
            datetime_obj = datetime.strptime(datetime_str, "%Y%m%d%H%M%S")
            if latest_commodity_groups_file["datetime"] is None or datetime_obj > latest_commodity_groups_file["datetime"]:
                latest_commodity_groups_file["path"] = os.path.join(source_directory, file)
                latest_commodity_groups_file["datetime"] = datetime_obj

    # Convert and save the latest files found
    if latest_commodity_file["path"]:
        df = pd.read_excel(latest_commodity_file["path"])
        output_path = os.path.join(target_directory, "Items-List-Commodity.csv")
        df.to_csv(output_path, index=False)
        print(f"Latest commodity list {latest_commodity_file['path']} saved to {output_path}")

    if latest_process_file["path"]:
        df = pd.read_excel(latest_process_file["path"])
        output_path = os.path.join(target_directory, "Items-List-Process.csv")
        df.to_csv(output_path, index=False)
        print(f"Latest process list {latest_process_file['path']} saved to {output_path}")
    
    if latest_commodity_groups_file["path"]:
        df = pd.read_excel(latest_commodity_groups_file["path"])
        output_path = os.path.join(target_directory, "Items-List-Commodity-Groups.csv")
        df.to_csv(output_path, index=False)
        print(f"Latest commodity groups list {latest_commodity_groups_file['path']} saved to {output_path}")

if __name__ == "__main__":
    # Ensure the target directory exists
    os.makedirs(TARGET_DIR, exist_ok=True)
    fetch_and_convert_latest_item_lists(SOURCE_DIR, TARGET_DIR)
