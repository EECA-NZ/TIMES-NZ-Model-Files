"""

so I am going to try reading the raw_data summary, which should match the inputs perfectly. 

If I can read it then I can just write it out to a bunch of structured csvs 

"""
# libraries 
import os 
import sys
import numpy as np
from pathlib import Path
import pandas as pd 
from io import StringIO
import csv
import ast 
import string

# get custom libraries
current_dir = Path(__file__).resolve().parent
sys.path.append(os.path.join(current_dir, "..", "library"))
from config import TIMES_LOCATION, PREP_LOCATION

# file locations 
table_location = os.path.join(TIMES_LOCATION, "TIMES-NZ", "raw_table_summary")
file_location = f"{table_location}/raw_tables.txt"
output_location = f"{PREP_LOCATION}/data_raw/data_scraping"

# Read the data from the summary tables
def parse_data_blocks(filepath, debug = False):
    with open(filepath, 'r') as file:
        content = file.read()
    
    blocks = content.strip().split('\n\n')
    
    parsed_blocks = []
    for block_num, block in enumerate(blocks, 1):
        lines = block.strip().split('\n')

        if len(lines) == 1 and lines[0] == '':
            # empty carriage returns, skipping these             
            continue
        
        if len(lines) < 6:
            if debug: 
                print(f"Warning: Block {block_num} - Skipping probably empty block with fewer than 6 lines:")
            for line in lines: 
                print(f"        - {line}")
            continue
            
        block_data = {}
        
        # Find the line with headers (it will be the first line containing a comma)
        header_line_idx = None
        for i, line in enumerate(lines):
            if ': ' not in line:
                header_line_idx = i
                break
        
        if header_line_idx is None:
            if debug:
                print(f"Warning: Block {block_num} - No header line found for {lines[0]}")
            continue
        
        # Parse all metadata lines before the header
        for line in lines[:header_line_idx]:
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                
                # Special handling for uc_sets which contains a dictionary
                if key == 'uc_sets':
                    try:
                        value = ast.literal_eval(value)  # Safely evaluate string representation of dict
                    except:
                        if debug:
                            print(f"Warning: Block {block_num} - Could not parse uc_sets dictionary")
                        value = {}
                
                block_data[key] = value
        
        # Get headers
        headers = [h.strip() for h in lines[header_line_idx].split(',')]
        
        # Parse data rows using csv module
        data_rows = []
        data_content = '\n'.join(lines[header_line_idx + 1:])
        csv_reader = csv.reader(StringIO(data_content))
        
        for line_num, row in enumerate(csv_reader, header_line_idx + 2):
            if not row:  # Skip empty rows
                continue
            
            num_cols = len(row)
            if num_cols != len(headers):
                if debug:
                    print(f"\nWarning: Block {block_num} Line {line_num} - Column mismatch:")
                    print(f"Expected {len(headers)} columns, found {num_cols}")
                
                # Pad or truncate as needed
                if num_cols < len(headers):
                    row.extend([np.nan] * (len(headers) - num_cols))
                else:
                    if debug:
                        print("Truncating row to match header count")
                    row = row[:len(headers)]
            
            # Convert empty strings to NaN
            row = [val.strip() if val.strip() else np.nan for val in row]
            data_rows.append(row)
        
        try:
            block_data['data'] = pd.DataFrame(data_rows, columns=headers)
        except Exception as e:
            if debug:
                print(f"\nError creating DataFrame for block {block_num}:")
                print(f"Error: {str(e)}")
            continue
        
        parsed_blocks.append(block_data)
    
    return parsed_blocks

def main():
    
    blocks = parse_data_blocks(file_location)
    
    for i, block in enumerate(blocks, 1):
        print(f"\nBlock {i}:")
        print("Sheet Name:", block['sheetname'])
        print("File Name:", block['filename'])
        print("Range:", block['range'])
        print("Tag:", block['tag'])
        if 'data' in block:
            print("\nData Shape:", block['data'].shape)
            print("\nSample of rows with non-null values:")
            print(block['data'].dropna(how='all').head())
        print("-" * 50)





# get all data 
blocks = parse_data_blocks(file_location)


# get counts for each combination of file name, sheet, and tag 
# best to put these in a table? maybe this is smart generally 

rows = []
for block in blocks:
    row_data = {
        "folder_name": block['filename'].removesuffix(".xlsx"),
        "sheet_name": block['sheetname'],
        "tag_name": block['tag'].replace("~", "").replace(":", "·"),
        "range" : block['range'], 
        "uc_sets" : block.get('uc_sets', None)       
    }
    rows.append(row_data)

block_descriptions = pd.DataFrame(rows)

# just gonna sort these for fun 

block_descriptions = block_descriptions.sort_values(["folder_name", "sheet_name", "tag_name", "range"])
# add a counter within the tags 
groups = block_descriptions. groupby(["folder_name", "sheet_name", "tag_name"])
block_descriptions["tag_counter"] = groups.cumcount() + 1

def get_tag_counter(block): 
    df = block_descriptions

    df = df[df['folder_name'] == block['filename'].removesuffix(".xlsx")]
    df = df[df['sheet_name'] == block['sheetname']]
    df = df[df['tag_name'] == block['tag'].replace("~", "").replace(":", "·")]
    df = df[df['range'] == block['range']]

    # return the counter for this tag in this folder/sheet 
    counter = df['tag_counter'].iloc[0]
    # make it a number for no real reason
    counter = string.ascii_lowercase[counter-1]

    return counter


write_data = True

test = block_descriptions[block_descriptions["tag_name"].str.contains(":")]
#print(test)

block_descriptions.to_csv(f"{output_location}/metadata.csv", index = False, encoding='utf-8-sig') # awkward encoding, hacky for colons 


def write_block_data_to_csv(block):

    # find the file it was from 
    file_name = block['filename']
    folder_name = file_name.removesuffix(".xlsx")

    # The sheetname will be our subfolder 
    sheet_name = block['sheetname']

    # get the tag name and remove the '~', this will be our final folder name.
    # The processing script will handle adding it so Veda can read it
    tag_name = block['tag']
    tag_name = tag_name.replace("~", "")
    # we also need to remove the colons 
    tag_name = tag_name.replace(":", "·")

    output_folder = os.path.join(output_location, folder_name, sheet_name, tag_name)   
    # get the counter so we can add a suffix to the data if needed
    counter = get_tag_counter(block)
    csv_name = f"data_{counter}"

    # get the data 
    df = block['data']

    # We are not going to write everything just yet, just syssettings and the base year data for now 
    # write blocks: 
    Path(output_folder).mkdir(parents=True, exist_ok=True)
    write_location = f"{output_folder}/{csv_name}.csv"
    print(f"Writing BY data to {write_location}")
    df.to_csv(write_location, index = False)

for block in blocks:
   write_block_data_to_csv(block)


