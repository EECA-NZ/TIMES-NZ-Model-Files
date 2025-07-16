"""

Generates the files for TIMES 2.1.3 based on the contents of raw_tables.txt

"""

# libraries
import os

# get custom libraries/ locations
from prepare_times_nz.filepaths import OUTPUT_LOCATION, PREP_LOCATION
from prepare_times_nz.helpers import clear_data_intermediate, clear_output

TIMES_2_SCRIPTS = f"{PREP_LOCATION}/scripts/times_2_methods"

# delete the data_intermediate and output folders
clear_data_intermediate()
clear_output()

# Execute TIMES 2
print("Reading the archived summary data")
os.system(f"python {TIMES_2_SCRIPTS}/read_archive_summary.py")
print(f"Creating TIMES excel files in {OUTPUT_LOCATION}")
os.system(f"python {TIMES_2_SCRIPTS}/generate_excel_files_from_archive.py")
