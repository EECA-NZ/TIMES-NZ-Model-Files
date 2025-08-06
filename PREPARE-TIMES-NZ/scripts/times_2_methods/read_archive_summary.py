"""

This is a one-off script designed to recreate the raw data as a series of csvs in folders mirroring the original structure

There are a few redundant calls but I do not expect this script to make it into any production system so will not refactor.

"""

import ast
import csv
import logging

# libraries
import os
import string
import sys
from io import StringIO

import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO)

# get custom libraries/ locations
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(current_dir, "..", "library"))
from filepaths import DATA_INTERMEDIATE, PREP_LOCATION

# file locations
table_location = os.path.join(
    PREP_LOCATION, "data_raw", "archive"
)  # archived summary table, won't update with new loads
file_location = f"{table_location}/raw_tables.txt"
output_location = DATA_INTERMEDIATE

if not os.path.exists(output_location):
    os.mkdir(output_location)

if not os.path.exists(output_location):
    os.mkdir(output_location)


# Read the data from the summary tables
def parse_data_blocks(filepath):
    with open(filepath, "r", encoding="utf-8") as file:
        content = file.read()

    blocks = content.strip().split("\n\n")

    parsed_blocks = []
    for block_num, block in enumerate(blocks, 1):
        lines = block.strip().split("\n")

        if len(lines) == 1 and lines[0] == "":
            # empty carriage returns, skipping these
            continue

        if len(lines) < 6:
            logging.debug(
                f"Warning: Block {block_num} - Skipping probably empty block with fewer than 6 lines:"
            )
            for line in lines:
                logging.debug(f"        - {line}")
            continue

        block_data = {}

        # Find the line with headers (it will be the first line after types)
        header_line_idx = None
        for i, line in enumerate(lines):
            if line.startswith("types:"):
                header_line_idx = i + 1
                break

        if header_line_idx is None:
            logging.debug(
                f"Warning: Block {block_num} - No header line found for {lines[0]}"
            )
            continue

        if header_line_idx is None or header_line_idx >= len(lines):
            logging.debug(f"Warning: Block {block_num} - Invalid header line index")
            continue

        # Parse all metadata lines before the header
        for line in lines[:header_line_idx]:
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()

                # Special handling for uc_sets which contains a dictionary
                if key == "uc_sets":
                    try:
                        value = ast.literal_eval(
                            value
                        )  # Safely evaluate string representation of dict
                    except:
                        logging.debug(
                            f"Warning: Block {block_num} - Could not parse uc_sets dictionary"
                        )
                        value = {}

                block_data[key] = value

        # Get headers
        headers = [h.strip() for h in lines[header_line_idx].split(",")]
        block_data["headers"] = headers

        # Parse data rows using csv module to ensure commas are handled correctly
        data_rows = []
        data_content = "\n".join(lines[header_line_idx + 1 :])
        csv_reader = csv.reader(StringIO(data_content))

        for line_num, row in enumerate(csv_reader, header_line_idx + 2):
            if not row:  # Skip empty rows
                continue

            num_cols = len(row)
            if num_cols != len(headers):
                logging.debug(
                    f"\nWarning: Block {block_num} Line {line_num} - Column mismatch:"
                )
                logging.debug(f"Expected {len(headers)} columns, found {num_cols}")

                # Pad or truncate as needed
                if num_cols < len(headers):
                    row.extend([np.nan] * (len(headers) - num_cols))
                else:
                    logging.debug("Truncating row to match header count")
                    row = row[: len(headers)]

            # Convert empty strings to NaN
            row = [val.strip() if val.strip() else np.nan for val in row]
            data_rows.append(row)

        try:
            block_data["data"] = pd.DataFrame(data_rows, columns=headers)
        except Exception as e:
            logging.debug(
                f"\nError creating DataFrame for block {block_num}. Error: {str(e)}"
            )
            continue

        parsed_blocks.append(block_data)

    return parsed_blocks


# get all data
blocks = parse_data_blocks(file_location)


def create_metadata(blocks):

    # get counts for each combination of file name, sheet, and tag
    rows = []
    for block in blocks:
        row_data = {
            "folder_name": block["filename"].removesuffix(".xlsx"),
            "sheet_name": block["sheetname"],
            "tag_name": block["tag"].replace("~", "").replace(":", "·"),
            "range": block["range"],
            "uc_sets": block.get("uc_sets", None),
        }
        rows.append(row_data)

    # Create block description metadata as dataframe
    block_descriptions = pd.DataFrame(rows)

    # We sort the values for a cleaner output
    block_descriptions = block_descriptions.sort_values(
        ["folder_name", "sheet_name", "tag_name", "range"]
    )
    # Add a counter within the tags
    groups = block_descriptions.groupby(["folder_name", "sheet_name", "tag_name"])
    block_descriptions["tag_counter"] = groups.cumcount() + 1

    return block_descriptions


block_descriptions = create_metadata(blocks)


def get_tag_counter(block, df=block_descriptions):
    df = block_descriptions

    df = df[df["folder_name"] == block["filename"].removesuffix(".xlsx")]
    df = df[df["sheet_name"] == block["sheetname"]]
    # we have to do this because we are making folders out of tags, some tags have colons, and windows hates colons
    df = df[df["tag_name"] == block["tag"].replace("~", "").replace(":", "·")]
    df = df[df["range"] == block["range"]]

    # return the counter for this tag in this folder/sheet
    counter = df["tag_counter"].iloc[0]
    # make it a number for no real reason
    counter = string.ascii_lowercase[counter - 1]
    return counter


def write_block_data_to_csv(block):

    # find the file it was from
    file_name = block["filename"]
    folder_name = file_name.removesuffix(".xlsx")

    # The sheetname will be our subfolder
    sheet_name = block["sheetname"]

    # get the tag name and remove the '~', this will be our final folder name.
    # The processing script will handle adding it so Veda can read it
    tag_name = block["tag"]
    tag_name = tag_name.replace("~", "")
    # we also need to remove the colons so that the names can live in windows file systems.
    tag_name = tag_name.replace(":", "·")

    output_folder = os.path.join(output_location, folder_name, sheet_name, tag_name)
    # get the counter so we can add a different suffix to the data if needed for unique names within tag directory
    counter = get_tag_counter(block)
    csv_name = f"data_{counter}"
    # get the data
    df = block["data"]
    # write blocks:
    os.makedirs(output_folder, exist_ok=True)
    write_location = f"{output_folder}/{csv_name}.csv"
    logging.info(f"Writing data to {write_location}")
    df.to_csv(
        write_location, index=False, encoding="utf-8-sig"
    )  # must encode against BOM


# Write data

# Metadata
block_descriptions.to_csv(
    f"{output_location}/metadata.csv", index=False, encoding="utf-8-sig"
)  # must encode against BOM

# CSV files
for block in blocks:
    write_block_data_to_csv(block)
