[Back to Model Structure Index](../model-structure.md)
## SysSettings.xlsx
### WorkSheet: SysSettings
**ActivePDef**: 
Model Period Definition. Will be used to select period definitions


 - Veda Tag: `~ActivePDef`


 - Data Location: `SysSettings.toml`


**Currencies**: 
Default currency unit


 - Veda Tag: `~Currencies`


 - Data Location: `SysSettings.toml`


**StartYear**: 
The model base year. Used by several scripts for downstream processing.


 - Veda Tag: `~StartYear`


 - Data Location: `SysSettings.toml`


**TimePeriods**: 
These time periods are calculated based on the current ActivePDef and milestone year inputs in milestone_years.csv. Only the active definition will be used.


 - Veda Tag: `~TimePeriods`


 - Data Location: `data_intermediate/stage_4_veda_format/sys_settings/active_periods.csv`


**BookRegions_Map**: 
Map books to regions. In the current version, all region information is contained within a single book.


 - Veda Tag: `~BookRegions_Map`


 - Data Location: `SysSettings.toml`


**DefaultUnits**: 
Default activity units for each sector. We should be definined the units for all processes and commodities individually anyway, so this may be redundant.


 - Veda Tag: `~DefUnits`


 - Data Location: `SysSettings.toml`


**DiscountRates**: 
Default discount rate. Need to figure out how to adjust this in scenarios


 - Veda Tag: `~TFM_INS`


 - Data Location: `SysSettings.toml`


### WorkSheet: TimeSlices
**TimeSlices**: 
Timeslice categories. Changing these will require changes to other settings input files and load curve methods.


 - Veda Tag: `~TimeSlices`


 - Data Location: `SysSettings.toml`


**YearFractions**: 
Year fractions as calculated based on the number of hours in each slice. Currently calculated in stage 2 load curve processing.


 - Veda Tag: `~TFM_INS`


 - Data Location: `data_intermediate/stage_4_veda_format/sys_settings/yrfr.csv`


### WorkSheet: ImportSettings
**DisableDummyVariables**: 
Disables activity of dummy variables. Exclude this table (or change to LO) if you want to solve with infeasibilities.


 - Veda Tag: `~TFM_INS`


 - Data Location: `SysSettings.toml`


**DummyVariableCosts**: 
Define costs for generated dummy variables. These should be very high so the model only uses them when there are no other options


 - Veda Tag: `~TFM_UPD`


 - Data Location: `SysSettings.toml`


**InterpolExtrapol**: 
Default interpolation/extrapolation rules. These may need adjusting.


 - Veda Tag: `~TFM_MIG`


 - Data Location: `data_raw/user_config/settings/interpolation_extrapolation.csv`


**ImportSettings**: 
Standard Veda control import settings.


 - Veda Tag: `~ImpSettings`


 - Data Location: `data_raw/user_config/settings/import_settings.csv`

