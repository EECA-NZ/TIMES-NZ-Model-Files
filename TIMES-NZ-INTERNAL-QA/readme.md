# TIMES-NZ-INTERNAL-QA


### Instructions

 - Navigate to `TIMES-NZ-INTERNAL-QA/scripts` 
 - Run `run_app.py`
 - Open your browser at `http://127.0.0.1:8050/`


### How it works

This script uses the `.vd` files generated in `TIMES-NZ-GAMS/times_scenarios` for data, and generates a dash app to compare differences in a detailed way. To choose which scenarios to compare, you must have run the model and generated these .vd files for each scenario. Four are included in the repo.

Then, choose two scenarios (which will correspond to the directory names in `TIMES-NZ-GAMS/times_scenarios`) by setting the variable in `library/config.py` and run the app.

Note that this app also uses the new concordance file generated at `TIMES-NZ-OUTPUT-PROCESSING/data/input/concordance/`.

Currently the app only looks at "VAR_FOut" from the .vd files, and this attribute is hardcoded. Other TIMES Attributes can be chosen by adjusting this in `run_app.py`. 