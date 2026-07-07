"""
Surfaces some config options for preprocessing and the app
These are the scenarios that will populate the cleaned parquet files 
in post processing 
These parquet files serve the app but can also be used for detailed analysis.
For sensitivty testing, we might want to expand the batch to variant scenarios
However, it's best not to upload many variant scenarios if they won't populate the app

The config options here also select which scenarios are shown on the app itself

So it might be desirable to trim the list for app uploads rather than
including dozens of variants. The data size is non-trivial.
"""

# MAIN BATCH 


current_scenarios = [
    "steady-v308",
    "steady-v308-noflex",
    "steady-v308-nodf",
    "steady-v308-shiftdf",
    "steady-v308-nobatt",
    "shift-v308",
    "shift-v308-noflex",
    "shift-v308-nodf",
    "shift-v308-steadydf",
    "shift-v308-nobatt",
]

