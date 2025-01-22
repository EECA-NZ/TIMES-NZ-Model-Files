

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

import pandas as pd 

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

def write_data(df, book_name, sheet_name, tag, startrow = 0):    
    # this requires the workbook to exist already with all the sheets in it! 
    # TO DO: add handling for data with uc_sets, which will require moving the table down a bit and writing the uc_sets above
    # in these cases the uc_sets will go in A, and the tag will go in B
    # actually wait maybe the tag should always go in B? leaving room for the uc_sets in A? 
    new_workbook = f"{OUTPUT_LOCATION}/{book_name}.xlsx"

    # we will also fix up the tag to match Veda expectations, adding back the tilde and fixing colons where necessary 

    tag = f"~{tag}"
    tag = tag.replace( "·", ":")


    
    with pd.ExcelWriter(new_workbook, 
                        mode = 'a',
                        if_sheet_exists = "overlay") as writer:
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
        # first convert our index to an excel format so the worksheet knows what we mean (A1, D1, etc)
        tag_row = startrow + 1
        # then just write the tag we fixed up earlier 
        worksheet[f"A{tag_row}"] = tag
        



def write_all_tags_to_sheet(book_name, sheet_name):


    # The sheets with multiple tags need to be stacked up.
    # Each table we write will need to have its col number saved in here so we can move the others to the right

    # for each sheet, there will be folders for each tag

    # we want to get each tag in the folder, and then each file in the tag 
    # most tags have only one file but we need to be able to write multiple tags with the same name to a sheet sometimes 
    
    
    tag_list = get_tags_for_sheet(book_name, sheet_name)
    sheet_folder = f"{INPUT_LOCATION}/{book_name}/{sheet_name}"

    # we start from the first row and will just move down I guess     
    startrow = 0

    for tag_name in tag_list:
        csv_files = return_csvs_in_folder(f"{sheet_folder}/{tag_name}")

        for csv_name in csv_files:
            # read the data 
            df = get_csv_data(book_name, sheet_name, tag_name, csv_name)

            # we put our patch for annoying files here
            # we might be able to build better checks for these! but for now only apply to the 2 specific cases we have found 

            if (book_name == "SysSettings"
                    and sheet_name == "TimePeriods" 
                    and tag_name in ["StartYear", "ActivePDef"]):
                df = strip_headers_from_tiny_df(df)

            # create the tag, replacing back the colons where necessary
            write_data(df, book_name, sheet_name, tag_name, startrow = startrow)
            # measure the length (row count)
            df_row_count= len(df)
            # add the dataframe rows to our start row index so we can keep going without overwriting
            # we add an extra three lines to make a big old gap 
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


