"""
This script fetches the latest "Items List" export files from the TIMES `Exported_files`
directory, renames them to remove the timestamp and converts them to CSV. This is to ease
the process of updating the schema generation process with the latest data.

Usage:
* First, using VEDA, export the "Items List" files for Commodity, Commodity Groups, and Process.
* Run this script to fetch the latest files and convert them to CSV:

python scripts/fetch_items_lists.py
"""

import os
from datetime import datetime
import pandas as pd

MYUSER = os.getlogin().lower()
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SOURCE_DIR = os.path.join(SCRIPT_DIR, os.pardir, os.pardir, 'TIMES-NZ', 'Exported_files')
TARGET_DIR = os.path.join(SCRIPT_DIR, os.pardir, 'data', 'input')

def get_latest_file_info(source_directory, pattern):
    """
    Get the path and timestamp of the latest file matching the pattern.

    Args:
        source_directory: Path to the directory containing the exported files.
        pattern: Pattern to match the file name.

    Returns:
        Dictionary containing the path and timestamp of the latest file.

    """
    latest_file = {"path": None, "datetime": None}
    for file in os.listdir(source_directory):
        if pattern in file:
            datetime_str = file.split(pattern)[-1].split(').xlsx')[0]
            datetime_obj = datetime.strptime(datetime_str, "%Y%m%d%H%M%S")
            if latest_file["datetime"] is None or datetime_obj > latest_file["datetime"]:
                latest_file["path"] = os.path.join(source_directory, file)
                latest_file["datetime"] = datetime_obj
    return latest_file

def convert_to_csv(file_info, target_directory, output_name):
    """
    Convert the latest "Items List" export file to CSV format.

    Args:
        file_info: Dictionary containing the path and timestamp of the latest file.
        target_directory: Path to the directory to save the converted CSV files.
        output_name: Name of the output CSV file.

    Returns:
        None

    """
    if file_info["path"]:
        data = pd.read_excel(file_info["path"])
        output_path = os.path.join(target_directory, output_name)
        data.to_csv(output_path, index=False)
        print(f"Latest {output_name[:-4]} {file_info['path']} saved to {output_path}")

def fetch_and_convert_latest_item_lists(source_directory, target_directory):
    """
    Fetch the latest "Items List" export files from the TIMES `Exported_files` directory,

    Args:
        source_directory: Path to the directory containing the exported files.
        target_directory: Path to the directory to save the converted CSV files.

    Returns:
        None
    
    """
    # Define file patterns
    file_patterns = {
        "Items-List-Commodity.csv": "Items List-Commodity(",
        "Items-List-Process.csv": "Items List-Process(",
        "Items-List-Commodity-Groups.csv": "Items List-Commodity Groups("
    }

    # Ensure the target directory exists
    os.makedirs(target_directory, exist_ok=True)

    # Process each file type
    for output_name, pattern in file_patterns.items():
        file_info = get_latest_file_info(source_directory, pattern)
        convert_to_csv(file_info, target_directory, output_name)

if __name__ == "__main__":
    fetch_and_convert_latest_item_lists(SOURCE_DIR, TARGET_DIR)
