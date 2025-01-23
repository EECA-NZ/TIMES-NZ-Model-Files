

"""
The structure works like this: 

1) For each book, we create one sheet per tag found in the original sheet.
2) Each tag gets its own table 
"""



"""
Execution: 

1) get all csvs in a folder 
2) for each csv, create a worksheet 



"""

import sys 
import os 
from pathlib import Path 
# niche libraries (might not need these later!)
# from openpyxl.utils import get_column_letter
from openpyxl import Workbook
from ast import literal_eval

import pandas as pd 
import string

# get custom libraries
current_dir = Path(__file__).resolve().parent
sys.path.append(os.path.join(current_dir, "..", "library"))
from config import INPUT_LOCATION, OUTPUT_LOCATION


def get_csv_data(book_name, sheet_name, tag_name, csv_name):   
    file_location = f"{INPUT_LOCATION}/{book_name}/{sheet_name}/{tag_name}/{csv_name}.csv"
    df = pd.read_csv(file_location)
    return df


# Handle special dataframes: 


# we need special handling for some tables with one value, and expect that value to be in the header column. 
# This is just a bit of annoying stuff from Veda as far as I can tell 

def strip_headers_from_tiny_df(df):
    df = df.T  # Transpose the df
    df.columns = [df.iloc[0][0]]  # Set the column name to the value
    df = df.iloc[0:0]  # Remove all rows 
    return df





def return_csvs_in_folder(folder_name):
    path = Path(folder_name)    
    # Get all CSV files and their stem names (name without suffix)
    base_names = [f.stem for f in path.glob('*.csv')]    
    return base_names

def return_subfolders(folder_name):
    # this will be used for returning all the tags in a given sheet folder
    path = Path(folder_name)    
    # Get all subfolders and their names
    subfolder_names = [f.name for f in path.iterdir() if f.is_dir()]    
    return subfolder_names    


def get_sheets_for_book(book_name):
    book_folder = f"{INPUT_LOCATION}/{book_name}"
    sheets = return_subfolders(book_folder)
    return sheets 

def get_tags_for_sheet(book_name, sheet_name):
    sheet_folder = f"{INPUT_LOCATION}/{book_name}/{sheet_name}"
    tags = return_subfolders(sheet_folder)
    return tags 
    

# Get uc_sets 
# should return the uc sets for the file 



# these are stored in the metadata for now, but this is not appropriate long-term. They should be kept within the configuration files
#for user constraints once these are developed


def get_metadata_df():
    file_location = f"{INPUT_LOCATION}/metadata.csv"
    df = pd.read_csv(file_location)
    # reverse engineering this, but not good practise doing the same thing in diff directions like this.
    # better to just do stuff once - but i expect this to be very temporary! (famous last words)    
    df['csv_name'] = df['tag_counter'].apply(lambda x: string.ascii_lowercase[x-1])
    df['csv_name'] = df['csv_name'].apply(lambda x: f"data_{x}")
    return df

# will require a range formula here to handle cases of a sheet having multiple tags with different uc_sets 

def get_uc_sets(book_name, sheet_name, tag, csv_name):
    metadata = get_metadata_df()

    metadata = metadata[
    (metadata['folder_name'] == book_name) & 
    (metadata['sheet_name'] == sheet_name) & 
    (metadata['tag_name'] == tag) &
    (metadata['csv_name'] == csv_name) 
]
    if len(metadata) > 1:
        print(f"Warning: metadata filter returned multiple entries. Please review")
    # first row uc_sets (should only be one row)    
    uc_set = metadata.iloc[0]['uc_sets']   
    
    if pd.isna(uc_set):
        print(f"uc_set is nan")
        uc_set = {}
    else:        
        print(f"attempting uc_eval")
        uc_set = literal_eval(uc_set)

    return uc_set
    

def create_empty_workbook(book_name, sheets, suffix = "_test_automate"):
    # we want to create the full workbook with empty sheets first. 
    # then we can append everything with overlays

    # definitions:
    # sheets = get_sheets_for_book(book_name)
    book_location = f"{OUTPUT_LOCATION}/{book_name}{suffix}.xlsx"

    # create workbook:
    wb = Workbook()

    # remove the default sheet which gets activated
    wb.remove(wb.active)

    # add each sheet 
    for sheet in sheets: 
        wb.create_sheet(sheet)

    # save 
    wb.save(book_location)

def write_data(df, book_name, sheet_name, tag, uc_set, startrow = 0):    
    # this requires the workbook to exist already with all the sheets in it! 
    # TO DO: add handling for data with uc_sets, which will require moving the table down a bit and writing the uc_sets above
    # in these cases the uc_sets will go in A, and the tag will go in B
    # actually wait maybe the tag should always go in B? leaving room for the uc_sets in A? 
    new_workbook = f"{OUTPUT_LOCATION}/{book_name}.xlsx"

    # we will also fix up the tag to match Veda expectations, adding back the tilde and fixing colons where necessary 

    tag = f"~{tag}"
    tag = tag.replace( "·", ":")

    # get uc_set length

    uc_set_length = len(uc_set)
    # if we have any sets 
    if uc_set_length > 0:
        # first we move this table down if necessary. 
        # the first uc_set is free, but any additional sets mean we need to shift it down a bit
        startrow += uc_set_length-1




    
    with pd.ExcelWriter(new_workbook, 
                        mode = 'a',
                        if_sheet_exists = "overlay") as writer:
        
        # first we handle the uc_sets if necessary, starting these 
    # Write DataFrame starting from row 1 (which is the second row - Excel is 0-based)
        df.to_excel(writer, 
                    sheet_name=sheet_name,
                    startcol=0,
                    startrow=startrow + 1,    # Start the table from second row - we are leaving a gap for the tag! 
                    index=False)       
        
        # Add header string so Veda picks up the correct tag 
        # Find the sheet in writer:        
        worksheet = writer.sheets[sheet_name]
        # Write the header string in cell A1.        
        tag_row = startrow + 1 
        # then just write the tag we fixed up earlier 
        worksheet[f"A{tag_row}"] = tag

        # now add the uc_set tags if needed 
        if uc_set_length > 0: 
            for n in range(uc_set_length):
                # 1-indexed                
                uc_set_tag_row = startrow - n + 1 # additional 1 for 0 indexing
                key = list(uc_set.keys())[n]                
                value = uc_set[key]
                # add to worksheet b, moving up as needed
                worksheet[f"B{uc_set_tag_row}"] = f"~UC_Sets: {key}: {value}"
        
def write_all_tags_to_sheet(book_name, sheet_name):


    # The sheets with multiple tags need to be stacked up.
    # Each table we write will need to have its row number saved in here so we can move other tables down 
    # we also need to add the uc sets to the tables, and these need to be stored somewhere more sensible
    
    
    tag_list = get_tags_for_sheet(book_name, sheet_name)
    sheet_folder = f"{INPUT_LOCATION}/{book_name}/{sheet_name}"

    # we start from the first row and will move down as needed
    startrow = 0

    for tag_name in tag_list:
        csv_files = return_csvs_in_folder(f"{sheet_folder}/{tag_name}")

        for csv_name in csv_files:
            # read the data 
            df = get_csv_data(book_name, sheet_name, tag_name, csv_name)
            # include the uc_set if needed (this comes up null otherwise)
            uc_set = get_uc_sets(book_name, sheet_name, tag_name, csv_name)

            # we put our patch for annoying files here
            # we might be able to build better checks for these! but for now only apply to the 2 specific cases we have found 

            if (book_name == "SysSettings"
                    and sheet_name == "TimePeriods" 
                    and tag_name in ["StartYear", "ActivePDef"]):
                df = strip_headers_from_tiny_df(df)

            # create the tag, replacing back the colons where necessary
            write_data(df, book_name, sheet_name, tag_name, uc_set, startrow = startrow)
            # measure the length (row count), adding extra space for additional uc_sets if needed, so the next table has space
            df_row_count= len(df) + len(uc_set)
            # add the dataframe rows to our start row index so we can keep going without overwriting
            # we add an extra three lines to ensure a gap (this should ensure 2 lines between every table)
            startrow += df_row_count + 3     
        
def write_workbook(book_name):
    print(f"Creating {book_name}.xlsx:")
    sheets = get_sheets_for_book(book_name)

    # create structure, overwriting everything already there
    create_empty_workbook(book_name, sheets, suffix = "")

    for sheet in sheets: 
        # just some verbosity
        print(f"     - Sheet: '{sheet}'")
        # the workbook exists now we write each tag set to each sheet 
        write_all_tags_to_sheet(book_name, sheet_name = sheet)



# test = get_metadata_df()

test = get_csv_data("SuppXLS/Scen_Base_constraints", "TRA_Policy", "UC_T", "data_a")
test2 = get_csv_data("SuppXLS/Scen_Base_constraints", "Thermal_gencap", "UC_T", "data_a")
print(test2)

"""
# test2 = get_uc_sets("SuppXLS/Scen_Base_constraints", "Cars", "UC_T", "data_b")
test2 = get_uc_sets("SuppXLS/Scen_AF_Renewable", "RES_SOL", "TFM_INS", "data_a")
# test2 = get_metadata_df()

kps = len(test2)
# kp = dict([list(test2.items())[0]])


print(test2)

print(f"kps: {kps}")
# print(f"kp: {kp}")
"""

