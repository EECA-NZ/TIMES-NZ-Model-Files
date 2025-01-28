# TIMES-NZ-INTERNAL-QA


### Instructions

 - Navigate to `TIMES-NZ-INTERNAL-QA/library/config.py` and adjust the specific scenario names you want to compare within this script.  
 - Navigate to `TIMES-NZ-INTERNAL-QA/scripts` 
 - Run `run_glance_app.py` or `run_delta_app.py`, depending on which app you want to view
 - Open your browser at `http://127.0.0.1:8050/` 


### How it works

This script uses the `.vd` files generated in `TIMES-NZ-GAMS/times_scenarios` for data, and generates a dash app to compare differences in a detailed way. To choose which scenarios to compare, you must have run the model and generated these .vd files for each scenario. These must then be pulled from your Veda directory to this TIMES repo, which is done executing either `run_all_processes.py` in `/scripts`, or simply `preprocessing.py` in `TIMES-NZ-INTERNAL-QA/scripts/` (which requires you to define the run you want to ingest within that script).

Then, choose two scenarios (which will correspond to the directory names in `TIMES-NZ-GAMS/times_scenarios`) by setting the variable in `library/config.py` and running either app. Note that these apps also uses the new concordance file which is stored in `TIMES-NZ-OUTPUT-PROCESSING/data/input/concordance/`.

Currently the delta app only looks at "VAR_FOut" from the .vd files, and this attribute is hardcoded. Other TIMES Attributes can be chosen by adjusting this in `run_delta_app.py`. Currently only VAR_CAP, VAR_FIn, or VAR_FOut are supported.

The glance app is designed to be very easy to add new metrics to. At the top of `TIMES-NZ-INTERNAL-QA/library/`, users can define new dataframes and add new configs for specific views. The current views are included as examples. 


### To Do: 

 - Rebuild in Quarto or similar technology that can be hosted on github pages as part of CI/CD workflow
 - Remove the hardcoded attribute method from the delta app, either adding a script parameter or an input option on the actual app interface
 - Refactor and better functionalise between apps, allowing shared functionality and easier maintenance.  

Then, choose two scenarios (which will correspond to the directory names in `TIMES-NZ-GAMS/times_scenarios`) by setting the variable in `library/config.py` and running either app. Note that these apps also uses the new concordance file which is stored in `TIMES-NZ-INTERNAL-QA/data/concordance/`.
