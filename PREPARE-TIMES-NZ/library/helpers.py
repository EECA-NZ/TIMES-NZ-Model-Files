

import sys 
import os 
from openpyxl import Workbook, load_workbook
from ast import literal_eval
import pandas as pd 
import string

# get custom locations
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, "..", "library"))
from config import INPUT_LOCATION, OUTPUT_LOCATION


def get_csv_data(book_name, sheet_name, tag_name, csv_name):   
    file_location = f"{INPUT_LOCATION}/{book_name}/{sheet_name}/{tag_name}/{csv_name}.csv"
    # must read as string in order to pull through full precision
    df = pd.read_csv(file_location, dtype = str)
    return df



def strip_headers_from_tiny_df(df):
    """    
    We need special handling for some tables with one value
    XL2TIMES outputs these with a header called VALUE, but we need the value to be in the header column (with no data underneath)
    This function replaces the header with the value for specific tables 

    """
    df = df.T  # Transpose the df
    df.columns = [df.iloc[0][0]]  # Set the column name to the value
    df = df.iloc[0:0]  # Remove all rows 
    return df

def return_csvs_in_folder(folder_name):
    path = os.path.abspath(folder_name)
    # Get all CSV files and their stem names (name without suffix)
    base_names = [os.path.splitext(f)[0] for f in os.listdir(path) 
                 if f.lower().endswith('.csv')]
    return base_names

def return_subfolders(folder_name):
    # this will be used for returning all the tags in a given sheet folder
    path = os.path.abspath(folder_name)    
    # Get all subfolders and their names
    subfolder_names = [f.name for f in os.scandir(path) if f.is_dir()]    
    return subfolder_names    


def get_sheets_for_book(book_name):
    book_folder = f"{INPUT_LOCATION}/{book_name}"
    sheets = return_subfolders(book_folder)
    return sheets 

def get_tags_for_sheet(book_name, sheet_name):
    sheet_folder = f"{INPUT_LOCATION}/{book_name}/{sheet_name}"
    tags = return_subfolders(sheet_folder)
    return tags 
    

def get_metadata_df():
    file_location = f"{INPUT_LOCATION}/metadata.csv"
    df = pd.read_csv(file_location)
    # reverse engineering this, but not good practise doing the same thing in diff directions like this.
    # better to just do stuff once - but i expect this to be very temporary! (famous last words)    
    df['csv_name'] = df['tag_counter'].apply(lambda x: string.ascii_lowercase[x-1])
    df['csv_name'] = df['csv_name'].apply(lambda x: f"data_{x}")
    return df

# getting uc_sets, which are currently stored in metadata
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
        # print(f"uc_set is nan")
        uc_set = {}
    else:        
        # print(f"attempting uc_eval")
        uc_set = literal_eval(uc_set)

    return uc_set
    

def create_empty_workbook(book_name, sheets, suffix = "_test_automate"):
    # This function creates the workbook with empty sheets
    # Later, data is appended to these sheets by overlay.        
    book_location = f"{OUTPUT_LOCATION}/{book_name}{suffix}.xlsx"

    # create the folder if needed
    os.makedirs(os.path.dirname(book_location), exist_ok=True)

    # create workbook:
    wb = Workbook()

    # remove the default sheet which gets activated
    wb.remove(wb.active)

    # add each sheet 
    for sheet in sheets: 
        wb.create_sheet(sheet)

    # save 
    wb.save(book_location)


def write_data(df, book_name, sheet_name, tag, uc_set, startrow=0):    
    new_workbook = f"{OUTPUT_LOCATION}/{book_name}.xlsx"
    
    # Fix up the tag to match Veda expectations
    tag = f"~{tag}"
    tag = tag.replace("·", ":")
    
    # Get uc_set length
    uc_set_length = len(uc_set)
    if uc_set_length > 0:
        startrow += uc_set_length-1
        
    # Load existing workbook
    book = load_workbook(new_workbook)
    sheet = book[sheet_name]
    
    # Write the header row
    for col_idx, column_name in enumerate(df.columns, 1):
        sheet.cell(row=startrow + 2, column=col_idx, value=column_name)
    
    # Write the data
    for row_idx, row in enumerate(df.values, startrow + 3):
        for col_idx, value in enumerate(row, 1):
            sheet.cell(row=row_idx, column=col_idx, value=value)
    
    # Write the tag
    tag_row = startrow + 1
    sheet.cell(row=tag_row, column=1, value=tag)
    
    # Add UC_Set tags if needed
    if uc_set_length > 0:
        for n in range(uc_set_length):
            uc_set_tag_row = startrow - n + 1
            key = list(uc_set.keys())[n]
            value = uc_set[key]
            sheet.cell(row=uc_set_tag_row, column=2, value=f"~UC_Sets: {key}: {value}")
    
    # Save the workbook
    book.save(new_workbook)
        
def write_all_tags_to_sheet(book_name, sheet_name):

    # The sheets with multiple tags need to be stacked up.
    # Each table we write will need to have its row number saved in here so other tables can move down. 
       
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

            # Patch for small files
            # TO-DO: automate handling of these rather than hardcoding which tables receive this treatment.
            # This currently covers all of TIMES-NZ but better to be flexible to future changes if needed.

            if (book_name == "SysSettings"
                    and sheet_name == "TimePeriods" 
                    and tag_name in ["StartYear", "ActivePDef"]):
                df = strip_headers_from_tiny_df(df)

            # create the tag (this also returns the colons where necessary)
            write_data(df, book_name, sheet_name, tag_name, uc_set, startrow = startrow)
            # measure the length (row count), adding extra space for additional uc_sets if needed, so the next table has space
            df_row_count= len(df) + len(uc_set)
            # add the dataframe rows to our start row index so we can keep going without overwriting
            # and additional rows for a healthy gap.            
            startrow += df_row_count + 3     
        
def write_workbook(book_name):
    print(f"Creating {book_name}.xlsx:")
    sheets = get_sheets_for_book(book_name)
    # create structure, overwriting everything already there
    create_empty_workbook(book_name, sheets, suffix = "")

    for sheet in sheets: 
        # Verbose printing
        print(f"     - Sheet: '{sheet}'")
        # the workbook exists now we write each tag set to each sheet 
        write_all_tags_to_sheet(book_name, sheet_name = sheet)



