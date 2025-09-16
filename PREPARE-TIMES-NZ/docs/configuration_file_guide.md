
`data_raw/user_config` contains all the toml files which outline the structure of the excel files that will be produced for TIMES/VEDA. These are effectively metadata describing what data should go into the excel sheets, and how it should be arranged.

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

  - `WorkBookName`: will specify a different workbook name for this table. Almost never needed, but useful if you need to output a subres or transformation or scenario workbook related to what you're doing and don't want to make a whole new config file for it. 
  - `SheetName`: will name the sheet this table is added to. If missing, it will default to creating a sheet that matches BookName
  - `TagName`: will set the tag for this table (eg "FI_T", etc). Tilde not needed. If missing, it will default to the TableName (this will almost always mean Veda doesn't know what you're talking about, except for some SysSettings tags)
  - `UCSets`: the uc_sets designation. If missing, will not be used. This is just for the user constraint tables and will often not be necessary. If used, they must be a dict (see below )
  - `Description`: Enter a short description of the purpose of this table. Not used by TIMES/VEDA, so can be anything you want. Will be read into the config metadata table, so can be helpful for reviewing the final structure later. Is also printed to the output tables for a quick reference. 
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
  Effectively what's happening here is that anything under `[TableName.Data]` is considered the data, but so are any values in each `TableName` that aren't explicitly set to metadata. So the above file will process exactly the same as this: 

  ```toml
  [TimePeriods]
  TagName = "TimePeriods" # not actually needed, as TagName inherits from TableName      
  5Year_increments = [1,2,5,5,5,5,5,5,5]
  1Year_increments = [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
  ```
  Adding `TableName.Data` is just a good way to explicitly clarify what your data items are. This can be especially useful if you're also using `UCSets` (below)

  However, most `TableNames` ingest data directly from the system, and will likely look more like this: 

  ```toml
  [YearFractions]
  SheetName = "YearFractions"
  TagName = "TFM_INS"
  DataLocation = "data_raw/0_config/year_fractions.csv"
  ```

 Config files that are mostly quick assumptions are generally written directly in the toml file to reduce data manipulation overheads. 
### Writing UCSets 

UCSets expect a python dictionary, which will be represented as a string dict in the metadata file, then evalauted during processing

There are two ways to do this in the config files. First is using a nested toml object (recommended):

  ```toml
  [UserConstraint]
  SheetName = "UserConstraints"
  TagName = "UC_T"
  DataLocation = "data_raw/constraints/some_constraints.csv"
  [UserConstraint.UCSets]
  R_S = "Allregions"
  T_S = ""
            
  ```
It's however also possible to just insert the dictionary as a string, like: 

  ```toml
  [UserConstraint]
  SheetName = "UserConstraints"
  TagName = "UC_T"
  DataLocation = "data_raw/constraints/some_constraints.csv"
  UCSets = "{'R_S': 'Allregions', 'T_S': ''}" 
            
  ```


