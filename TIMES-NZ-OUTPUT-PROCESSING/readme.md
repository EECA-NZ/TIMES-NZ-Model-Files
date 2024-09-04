## Convert TIMES output to human readable format.

### Workflow overview.

The following semi-manual steps are involved in using the python data processing scripts (under development) to generate the dataset for visualization within the RShiny app. These instructions by no means reflect an end-state for the project, but are a snapshot in time of a process that we are currently improving. It is assumed that `TIMES-NZ-Model-Files` is configured to produce two scenarios as follows:
* `kea-v<A>_<B>_<C>`
* `tui-v<A>_<B>_<C>`

where `<A>`, `<B>`, `<C>` respectively represent the major, minor and patch numbers of the current model run. It is assumed that the `TIMES-NZ-Visualization` git repository is checked out to a local `<TIMES-NZ-Visualization>` directory, e.g. `C:\Users\<user>\git\TIMES-NZ-Visualisation` and that the `TIMES-NZ-Model-Files` repository is checked out to a local `<TIMES-NZ-Model-Files>` directory, e.g. `C:\Users\<user>\git\TIMES-NZ-Model-Files`.

### In the TIMES-NZ-Model-Files repo:
* Update the TIMES model. For instance, modify the process and commodity description fields in the TIMES workbooks.
* Using VEDA, sync the TIMES database from the TIMES excel workbooks.
* Using VEDA, export `Items List` Excel files for `Processes`, `Commodities` and `Commodity Groups`.
* Using VEDA, run the TIMES scenarios to generate the output in the VEDA `GAMS_WrkTIMES` directory

### In the TIMES-NZ-Visualization repo:
* Manually copy the `VD` output files from the relevant VEDA `GAMS_WrkTIMES` directory to the following locations:
  * `<TIMES-NZ-Visualization>\data_cleaning\data\input\kea-v<A>_<B>_<C>.vd`.
  * `<TIMES-NZ-Visualization>\data_cleaning\data\input\tui-v<A>_<B>_<C>.vd`.
* Set the TIMES version number in `.\data_cleaning\library\constants.py`.
* Enter the `data_cleaning\scripts` directory:
```bash
cd <TIMES-NZ-Visualization>\data_cleaning\scripts
```
* Pull the latest `Items List` files over to the schema generation directory using `fetch_items_lists.py`:
```bash
python fetch_items_lists.py
```
* Generate the human-readable data file used for the RShiny visualization:
```bash
python make_human_readable_data.py
```
* Copy the output into the `data_loading` directory:
```bash
cp <TIMES-NZ-Visualization>\data_cleaning\data\output\output_combined_df_v<A>_<B>_<C>.csv <TIMES-NZ-Visualization>\data_loading\
```
* Update the version number in `data_loading\Load_Data.R`
```
times_nz_version <- "<A>.<B>.<C>"
```
* Run the `Load_Data.R` script:
```bash
cd <TIMES-NZ-Visualization>\data_loading
Rscript.exe .\Load_Data.R
```

Having done the above steps, the data loaded by the app locally has been updated. For instance, the app run locally using the `shiny::runApp()` command (as described in this repository's main README) should present the latest verion of the model.