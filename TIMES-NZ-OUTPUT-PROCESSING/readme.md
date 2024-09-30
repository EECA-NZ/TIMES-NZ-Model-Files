## Convert TIMES output to human readable format.

### Workflow overview.

The following steps are an automated recapitulation of a previously manual process for pulling together output for the two `TIMES-NZ` scenarios, `kea` and `tui`. We intend to overhaul the process to be much cleaner in a future release.

The following semi-manual steps are involved in using the python data processing scripts (under development) to generate the dataset for visualization within the RShiny app.

These instructions by no means reflect an end-state for the project, but are a snapshot in time of a process that we are currently improving. It is assumed that `TIMES-NZ-Model-Files` is configured to produce two scenarios as follows:
* `kea-v<A>_<B>_<C>`
* `tui-v<A>_<B>_<C>`

where `<A>`, `<B>`, `<C>` respectively represent the major, minor and patch numbers of the current model run.


The following steps need to have already been completed:

* In the `TIMES-NZ` folder:
  * Update the TIMES model. For instance, modify the process and commodity description fields in the TIMES workbooks.
  * Using VEDA, sync the TIMES database from the TIMES excel workbooks.
  * Using VEDA, using the `Items List` module, click the `Export To Excel` button at bottom right to export `Items List` Excel files for three tabs: `Process`, `Commodity` and `Commodity Groups`.
  * Using VEDA, run the TIMES scenarios to generate the output in the VEDA `GAMS_WrkTIMES` directory.

* In the `TIMES-NZ-GAMS` folder:
  * Enter the scripts directory: `cd scripts`
  * Run the `get_from_veda.py` script to pull thec scenario files from VEDA.
  * Run the `run_times_scenario.py` script to run the TIMES scenarios. This will produce the output files for each scenario within the `times_scenarios` directory.

### In the TIMES-NZ-OUTPUT-PROCESSING folder:
* Enter the `scripts` directory:
```bash
cd scripts
```
* Pull the latest `Items List` files over to the schema generation directory using `fetch_items_lists.py`:
```bash
python fetch_items_lists.py
```
* Generate the human-readable data file used for the RShiny visualization:
```bash
python make_human_readable_data.py
```

Having done the above steps, the dataset contained in `.\data\output\output_combined_df_v<A>_<B>_<C>.csv` will have been updated to reflect the updated `TIMES-NZ` scenarios.