
"""
This file includes configuration directories and variable settings 
This way any scripts can use these without hardcoding, which maintains a bit more flexibility in separate environments
The structure will need to change if this file is moved, as it uses the current location:

PREPARE-TIMES-NZ/library
"""
import os 
from pathlib import Path


# main directories
PREP_LIBRARY_LOCATION = Path(__file__).resolve().parent 
PREP_LOCATION = os.path.dirname(PREP_LIBRARY_LOCATION)
TIMES_LOCATION = os.path.dirname(PREP_LOCATION)


# data location
TIMES_INPUT_FILES = os.path.join(TIMES_LOCATION, "TIMES-NZ")
DATA_INTERMEDIATE = os.path.join(PREP_LOCATION, "data_intermediate")

