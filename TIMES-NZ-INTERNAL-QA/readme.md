# TIMES-NZ-INTERNAL-QA


This module is designed to do 3 key things:

1) Import staging data from `PREPARE-TIMES-NZ` to build necessary concordance files to describe and label all the model processes 
2) use these concordance files to create clean and self-documenting outputs for model runs
3) Render a deployable app to show results 


It overwrites a previous module used for analysis of TIMES 2.1.3. That module has been retired. 

Note: there are several references to terminal commands below. These all assume that your terminal is currently in `TIMES-NZ-INTERNAL-QA`, which is the project root. 


## Stage One: import staging data (optional) 

These scripts assume that `PREPARE-TIMES-NZ` has been run and `data_intermediate` has been populated. This needs to be rerun if new processes have been added to the prep module, but otherwise is not required regularly. New model runs or scenarios do not neces

## Building clean data files.

The concordance files built should describe all commodities and processes used in TIMES-NZ 3.0. The attribute outputs are then labelled to build multiple different outputs, which each have different structures. All data is output at the highest level of detail available from the model. These are currently: 

1) electricity generation: Input fuels, output generation, and generation capacity. Includes plant names and technologies. 
2) Energy demand: all final demand of energy, including non-energy use. (Not quite sure how to handle NZSteel at this stage, if modelled with the auxiliary electricity output from the coal use!)


More can be added from the available attributes in the scenario .vd files. At the minimum, these should include (not yet built): 

Energy production - energy imports or domestic production 
Other energy transformation (eg biomass or hydrogen) - likely to be an expansion of the electricity generation data, where each named process has an input and output energy type. 
Emissions 

Other potential outputs may be generated later (objective functions, item costs, shadow prices, etc)

All of these files are considered "final outputs" so should meet the following critera: 

a) be surfaced as downloadable outputs
b) be clearly labelled and interpretable by anyone 
c) be used to generate any charts in the app 
d) be at the maximum level of detail produced by the model

Later, it might be useful to package these .csv files as inputs into a single output excel file, including a data dictionary and other descriptors. 

## Running postprocessing 

Postprocessing can be run from the source script `src/times_nz_internal_qa/postprocessing/run_all_postprocessing.py`. It contains three steps: 

1) Build definitions for TIMES items based on data from `PREPARE-TIMES-NZ` and some internal logic (and a few patches, included)
2) Pull scenario results from a local installation of Veda. This is just for modellers. 
3) Apply the definitions to the scenario results, and populate the `data` folder with categorised and described data

The first two steps are not completely portable: Step 1 requires you to have previously run `PREPARE-TIMES-NZ` to populate those files. Step 2 requires you to have your own Veda installation. For this reason, the script has a few switches you can use to adjust depending on your environment. 

The results in `data` are used to populate the app. Note that raw results (converted vd files) are currently stored in the repo under `data_raw/scenario_files`. This is mostly so that they are accessible to anyone, but there might be better solutions for this problem. 

Note that all the categorised data is available for download from the public version of the app, currently at https://eeca-nz.shinyapps.io/times-nz-3-alpha/

## Deploying the app 

A few adjustments are made to our standard poetry structure to enable the app to build on shinyapps.io: 

1) app.py in root includes a line adding `src` to the system path. This enables shinyapps to identify the src modules and the usual imports work. Locally, this isn't necessary, because `src` is identified by the pylint dependencies in `pyproject.toml`. 
2) Shinyapps.io uses the `requirements.txt` file to install the necessary packages. Again, we don't usually do this with poetry. If you have added packages, you need to refresh requirements.txt by exporting your poetry requirements using `poetry export -f requirements.txt -o requirements.txt --without-hashes`

In general, you can deploy the app locally by simply running the script `run_local.py`


Deploy to shinyapps.io by entering the following into the terminal: 

```
poetry run rsconnect deploy shiny . \
  --entrypoint app \
  --title times-nz-3-alpha
```



