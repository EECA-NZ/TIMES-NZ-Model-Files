
"""
This file includes configuration directories and variable settings 
This way any scripts can use these without hardcoding, which maintains a bit more flexibility in separate environments
The structure will need to change if this file is moved, as it uses the current location:

TIMES-NZ-INTERNAL-QA/library
"""
import os 


#### QA RUNS
# these might go somewhere else but need to be surfaced here so anyone can use them? 

qa_runs = ["tui-v2_1_3", "tui-v2_1_3_iat"]

# main directories
QA_LIBRARY_LOCATION = os.path.dirname(os.path.abspath(__file__))
QA_LOCATION = os.path.dirname(QA_LIBRARY_LOCATION)
TIMES_LOCATION = os.path.dirname(QA_LOCATION)


# data location
TIMES_OUTPUTS_RAW = os.path.join(TIMES_LOCATION, "TIMES-NZ-GAMS", "times_scenarios")

