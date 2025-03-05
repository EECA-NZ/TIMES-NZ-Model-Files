## Pre-processing with Python

```
THIS MODULE IS UNDER DEVELOPMENT
```

To prepare the TIMES-NZ model files, we will be implementing pre-processing using the following command:

```python
prepare_times_nz.py
```

## STRUCTURE

All inputs will be in `data_raw`. 

This includes:
 - ALL source data in csv form. 
 - All configuration settings, stored in toml files 
 - Where we are using figures from research papers to modify or estimate shares etc, these can just have sources linked 

The raw data in `data_raw` should be the single source of truth. We won't version this beyond git - any published version of the model should be appropriately tagged to ensure replicability. 

This module should also contain the main methodology documentation, which describes sources and topology for each step of the model buildup. If we estimate demand disaggregations or project demand per sectors, the data and scripts for this will be here, and there will be an entry in the methodology document. This module, then, is the single source of truth for all technical information on TIMES-NZ. 

`data_intermediate` stores the files in structures aligning to the final outputs. These are csv files ready to be converted to Veda tags. This area is currently slightly loose, and we may need to break it up further (possibly by stages, as we progress we will learn more about how to do this)

`scripts` contains structural methods for moving the toml files and data into excel files, and also data preprocessing scripts.
`output` stores the outputs which are the excel files to be read by Veda (and later XL2TIMES, hopefully). 

## TOML Structure Rules


`data_raw/0_config` contains all the toml files which outline the structure of the excel files that will be produced for TIMES/VEDA. These are effectively metadata describing what data should go into the excel sheets, and how it should be arranged.

Each toml configuration file should contain: 

### 1: A workbook name (internally referred to as `WorkBookName`). 

All tags designated in a particular toml will be added to the workbook specified at the top of the file. It is possible to have multiple tomls insert data into the same workbook, but if you want a different workbook, you'll need to make a new toml. 
This will name the workbook you're creating, so it needs to:
a) follow Veda rules for these, and
b) if it's intended to be a baseyear workbook (VT_NAME_SECTOR_VERSION) then it also needs to be mapped the same way in the TIMES BookRegion_Map variable 

### 2: A list of tables specified by `[TableName]`.

`[TableName]` is not actually used by TIMES or Veda, so it can be whatever you want. Come up with a descriptive name for whatever the table is, or match the Veda name (like "TimePeriods" or something). The table names must be unique for each table and workbook, as BookName/TableName are used as a lookup key for these. 

### 3: `TableName` metadata rules:


TableName can contain anything you want, but some variables will be explicitly treated: 

  - `SheetName`: will name the sheet this table is added to. If missing, it will default to creating a sheet that matches BookName
  - `TagName`: will set the tag for this table (eg "FI_T", etc). Tilde not needed. If missing, it will default to the TableName (this will almost always mean Veda doesn't know what you're talking about, except for some SysSettings tags)
  - `UCSets`: the uc_sets designation. If missing, will not be used. This is just for the user constraint tables and will often not be necessary.
  - `Description`: Enter a short description of the purpose of this table. Not used by TIMES/VEDA, so can be anything you want. Will be read into the config metadata table, so can be helpful for reviewing the final structure later. 

  - `DataLocation`: the file path for the data this table is expected to contain. If missing, it will instead look for `Data`.
  - `Data`: a dictionary for the data contained in this TableName. Allows you to specify the data directly in the config file rather than an external file, which can be useful for smaller, simpler tables.


  Note: If both `Data` and `DataLocation` are not included within TableName, then the module will take all variables not listed above and assume these are intended to be a dictionary of data. This means it will insert these into the final excel file. 


### TOML `TableName` examples

  This means we can represent a whole table in a config file as simply as follows:   


  ```toml
  [StartYear]
  StartYear = 2023
  ```

  Or store data in `TableName.Data` more directly: 

  ```toml
    [TimePeriods]
    TagName = "TimePeriods" # not actually needed, as TagName inherits from TableName    
    [TimePeriods.Data]
    5Year_increments = [1,2,5,5,5,5,5,5,5]
    1Year_increments = [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
  ```

  However, most `TableNames` will likely look like this `[YearFractions]` example from `SysSettings`: 

  ```toml
  [YearFractions]
  SheetName = "YearFractions"
  TagName = "TFM_INS"
  DataLocation = "data_raw/0_config/year_fractions.csv"
  ```



(Can we remove the Data variable entirely?)
(Would also be good to add a uniqueness check to the table names)

## General Future State

```mermaid
flowchart LR
    CSV[("CSV/TOML Files")]
    EXCEL["Excel Processing"]
    MIGRATE_FORMULAS["Migrate formula logic (iterative)"]
    VEDA["VEDA Analysis"]
    OUTPUT["Data Output"]
    SHINY["Public Shiny Dashboard"]
    
    INTERNAL_QA["Internal QA Tools"]    

    subgraph XL2TIMES["XL2Times"]
        EXCEL["Excel Processing"]
        VEDA["VEDA Analysis"]
    end



    CSV --> EXCEL
    EXCEL --> MIGRATE_FORMULAS
    MIGRATE_FORMULAS --> CSV
    EXCEL --> VEDA
    VEDA --> OUTPUT
    OUTPUT --> SHINY
    OUTPUT --> INTERNAL_QA
    


```
