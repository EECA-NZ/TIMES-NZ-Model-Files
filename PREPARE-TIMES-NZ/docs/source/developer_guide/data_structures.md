This file describes the layout of the `PREPARE-TIMES-NZ` module. 
The intent is that this makes the structure - which is complex - easier to understand, interrogate, and modify. 

We want to make sure everything is replicable and scalable while minimising complexity as much as feasible. Minimising complexity should be our key guiding principle.

1) All data transformations should be replicable, with all source inputs and scripts clearly traceable. 
2) Steps are broken down into clear stages. This means it is clear for future modellers exactly what should be happening and when. 
3) It should be straightforward to add new data/methods/models/scenarios to future iterations of TIMES-NZ, without causing many breakages. 


# CODE 

## src 

This houses all the actual code in our model and does all the work 

Note that it should follow the same structure as `scripts`. The idea is that `scripts` executes the functions found in `src`. `scripts` then, should house very minimal actual code, but work as a coordinator for the relevant functions. The `dodo.py` file references scripts to be executed.

However, the scripts/src dichotomy was established halfway through development. These means there is currently inconsistent treatment - some scripts files do all the work and have no relevant src files. This needs to be tidied up. 

In any case, the relevant file in `scripts` always does the actual work, which may or may not import functions from `src`

`src` structure is as follows: 

 - `stage_0`: functions used in processing settings and user config files.
 - `stage_1`: functions used for loading and tidying input data. There should be very little processing or data manipulation in this stage. 
 - `stage_2`: creates base year data, including any joins, combinations, satellite modelling, etc, that are required. Should save data in sensible formats for reading by any program
 - `stage_3`: as stage 2, but for scenario or subres files. 
 - `stage_4`: takes the outputs of stage 2 and 3 and creates data formatted for Veda to be read by the TIMES model generator
 - `stage_5`: Uses the user config files and data from stage_4, to generate excel files. Note that the user_config files might also specify assumptions or other inputs to go into the excel files: `stage_5` handles any and all of this. Note that 
 - `utilities` houses common utility functions used across all stages
 

## scripts

Files in `scripts` are executed by `dodo.py`, which tracks dependencies and allows us to only run what's necessary on any refresh of the model files. 

`scripts` is currently separate from `src`, but breaks the structure down into the following stages. However, this is not ideal. Future refactors should ensure that all code is housed in `src` and executed via the `dodo.py` file, to remove redundant stages and minimise complexity in understanding the process. 

The scripts for this module are broken down into the following stages: 

0) `stage_0_settings`: System settings. Read configuration files and make any key parameters (such as base year) available for all future steps. 
1) `stage_1_prep_raw_data`: Prepare raw data, transforming and tidying where necessary (ie applying tidy data principles to excel files)
2) `stage_2_baseyear`: Prepare base year files. Combinations, transformations, apply assumptions, etc.
3) `stage_3_scenarios`: Prepare scenario files. Combinations, transformations, apply assumptions, etc.
4) `stage_4_veda_format`: Format the prepared data into files for Veda, using structures defined by the configuration settings and reading base year/scenario data as needed. Generate excel files. 

Additionally, scripts designed to fully recreates TIMES 2.1.3 from scratch using generated excel files are available in `scripts/times_2_methods`. These remain as a proof of concept. 

(Note: the archive scripts are currently broken because we did not put effort into maintaining them as the project structure evolved. We should either fix or delete these).

# DATA

## data_raw

All raw data is stored in this directory. It remains untouched from how it was downloaded or otherwise accessed.

 - `eeca_data` - any data sourced internally, such as the eeud extract. 
 - `external_data` - any data sourced externally. This is further categorised by source institution:
    - `mbie`
    - `electricity_authority`
    - etc. We can add anything we like to this, but it's good to keep separated by institution. 
 - `archive` - the original TIMES 2.1.3 excel files and a copy of the raw_tables.txt generated from these files. 
 - `coded_assumptions` - any raw files where assumptions have been built in. These are usually files that have been manually produced in some way. They're broken down by subject area, eg:
    - `electricity_generation`    
 - `concordances` - these are manual files, similar to `coded_assumptions`, but specifically designed to map different categories together, like regions to islands, etc. 
    - It might make more sense to add this to a subcategory of `coded_assumptions`
 - `user_config` - these are the toml configuration files which will define the structure of the final excel file outputs. You can read more about these in `readme.md`


## data_intermediate

This directory contains staging data - either tidied raw data or processed files.
The output files, produced in Stage 4, will use generated data that is stored in here. 
This directory is ignored by git and will not be tracked. To populate it, you will need to clone the repo and execute the module. 
The files in this module, depending on the stage, are either tidied raw data or tables used for other modules.
The structure for this directory has not yet been defined. In future development work, as more data and methods are added to the module, this will be revisited. 


## output

Similar to `data_intermediate`, this directory is not tracked by git and is fully generated by the module.

It contains all output files in Veda format for use by the TIMES model generator. 

When this system is fully mature, we will retire this directory and instead output all excel files for Veda directly to the `TIMES-NZ` module, allowing the model to run without requiring us to copy-paste excel files into `TIMES-NZ`. 









    
    