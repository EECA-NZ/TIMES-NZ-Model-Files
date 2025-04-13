
# libraries 
import os 
import sys

# get custom libraries/ locations 
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, "..", "library"))
from filepaths import PREP_LOCATION, DATA_INTERMEDIATE, OUTPUT_LOCATION
from helpers import clear_data_intermediate, clear_output

# delete the data_intermediate and output folders
clear_data_intermediate()
clear_output()

# Execute TIMES 2
print(f"Reading the archived summary data")
os.system(f"python {PREP_LOCATION}/scripts/times_2_methods/read_archive_summary.py")
print(f"Creating TIMES excel files in {OUTPUT_LOCATION}")
os.system(f"python {PREP_LOCATION}/scripts/times_2_methods/generate_excel_files_from_archive.py")       
