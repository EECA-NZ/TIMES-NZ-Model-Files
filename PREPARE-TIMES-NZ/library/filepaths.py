
"""
This file includes configuration directories and variable settings 
This way any scripts can use these without hardcoding, which maintains a bit more flexibility in separate environments
The structure will need to change if this file is moved, as it uses the current location:

PREPARE-TIMES-NZ/library
"""
import os 

# main directories
PREP_LIBRARY_LOCATION = os.path.dirname(os.path.abspath(__file__))
PREP_LOCATION = os.path.dirname(PREP_LIBRARY_LOCATION)
TIMES_LOCATION = os.path.dirname(PREP_LOCATION)


# data locations
# NOTE: OUTPUT_LOCATION is the directory for the final excel files. 
# It is regularly wiped and replaced with new files, so do not adjust this to the TIMES-NZ module without being careful
OUTPUT_LOCATION = os.path.join(PREP_LOCATION, "output") 
# DATA_INTERMEDIATE is gitignored and regularly wiped. It acts as a staging area but nothing should be stored here permanently.
DATA_INTERMEDIATE = os.path.join(PREP_LOCATION, "data_intermediate")
DATA_RAW = os.path.join(PREP_LOCATION, "data_raw")




