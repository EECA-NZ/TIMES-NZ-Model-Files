""" TODO: implement an automated TIMES configuration script """

# libraries 
import os 
import sys
from pathlib import Path
import pandas as pd 

# niche libraries (might not need these later!)
from openpyxl.utils import get_column_letter
from openpyxl import Workbook

# get custom libraries
current_dir = Path(__file__).resolve().parent
sys.path.append(os.path.join(current_dir, "..", "library"))
from config import DATA_INTERMEDIATE, TIMES_INPUT_FILES



# MAIN - Creating SysSettings.xlsx

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


def get_tag_data(book_name, sheet_name, tag):   
    file_location = f"{DATA_INTERMEDIATE}/{book_name}/{sheet_name}/{tag}.csv"
    df = pd.read_csv(file_location)
    return df


def return_tags_in_folder(folder_name):
    path = Path(folder_name)    
    # Get all CSV files and their stem names (name without suffix)
    base_names = [f.stem for f in path.glob('*.csv')]    
    return base_names


def get_sheets_for_book(book_name):

    book_folder = f"{DATA_INTERMEDIATE}/{book_name}"
    sheets = [p.name for p in Path(book_folder).iterdir() if p.is_dir()]   

    return sheets 
    


def create_empty_workbook(book_name, sheets, suffix = "_test_automate"):
    # we want to create the full workbook with empty sheets first. 
    # then we can append everything with overlays

    # definitions:
    # sheets = get_sheets_for_book(book_name)
    book_location = f"{TIMES_INPUT_FILES}/{book_name}{suffix}.xlsx"

    # create workbook:
    wb = Workbook()

    # remove the default sheet which gets activated
    wb.remove(wb.active)

    # add each sheet 
    for sheet in sheets: 
        wb.create_sheet(sheet)

    # save 
    wb.save(book_location)

def write_tag(df, book_name, sheet_name, tag, startcol = 0):    
    # this requires the workbook to exist already with all the sheets in it! 
    new_workbook = f"{TIMES_INPUT_FILES}/{book_name}.xlsx"
    with pd.ExcelWriter(new_workbook, 
                        mode = 'a',
                        if_sheet_exists = "overlay") as writer:
    # Write DataFrame starting from row 1 (which is the second row - Excel is 0-based)
        df.to_excel(writer, 
                    sheet_name=sheet_name,
                    startcol=startcol,
                    startrow=1,    # Start the table from second row
                    index=False)       
        
        # Add header string so Veda picks up the correct tag 
        # Find the sheet in writer:        
        worksheet = writer.sheets[sheet_name]
        # Write the header string in cell A1.
        # first convert our index to an excel format so the worksheet knows what we mean (A1, D1, etc)
        col_letter = get_column_letter(startcol + 1)
        worksheet[f"{col_letter}1"] = f"~{tag}"



def write_all_tags_to_sheet(book_name, sheet_name):


    # The sheets with multiple tags need to be stacked up.
    # Each table we write will need to have its col number saved in here so we can move the others to the right
    # First, lets get all tags for the sheet. Note that we need to be ready for only one tag
    tag_list = return_tags_in_folder(f"{DATA_INTERMEDIATE}/{book_name}/{sheet_name}")

    # we start from the first column
    startcol = 0

    for tag in tag_list:
        # get data and measure its length
        df = get_tag_data(book_name, sheet_name, tag)
        df_length = len(df.columns)

        write_tag(df, book_name, sheet_name, tag, startcol = startcol)

        # add the dataframe length to our start column index so we can keep going without overwriting
        # we add an extra one to make a gap
        startcol += df_length + 1
        
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


    
        


    

# write_all_tags_to_sheet("SysSettings", "Region and Time Slices")


# need to add verbosity?? 
#  sheets = get_sheets_for_book("SysSettings")


# create_empty_workbook("SysSettings")

write_workbook("SysSettings")
write_workbook("VT_NI_ELC_V4")
# write_all_tags_to_sheet("SysSettings", "Region and Time Slices")

