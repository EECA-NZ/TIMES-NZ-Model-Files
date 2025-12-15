[Back to Model Structure Index](../model-structure.md)
## SubRES_TMPL/SubRES_NewTechs_ELC_Transformation.xlsx
### WorkSheet: ELC_DistSolar
**ResidentialSolarDetails**: 
Adds details for residential rooftop solar


 - Veda Tag: `~FI_T`


 - Data Location: `data_intermediate/stage_4_veda_format/subres_elc/dist_solar/parameters.csv`


**ResidentialSolarCostCurves**: 
Standard cost curve projections for residential rooftop solar (NREL Moderate)


 - Veda Tag: `~FI_T`


 - Data Location: `data_intermediate/stage_4_veda_format/subres_elc/dist_solar/cost_curves_moderate.csv`


**ResidentialSolarProcesses**: 
Declares processes for new residential rooftop solar


 - Veda Tag: `~FI_Process`


 - Data Location: `data_intermediate/stage_4_veda_format/subres_elc/dist_solar/process_definitions.csv`


### WorkSheet: ELC_GenerationStack
**GenStackProcesses**: 
Declares processes for plants from genstack (Transformation settings)


 - Veda Tag: `~FI_Process`


 - Data Location: `data_intermediate/stage_4_veda_format/subres_elc/genstack/Transformation_process.csv`


**GenStackDetails**: 
Adds details for new plants from genstack (Transformation settings)


 - Veda Tag: `~FI_T`


 - Data Location: `data_intermediate/stage_4_veda_format/subres_elc/genstack/Transformation_parameters.csv`


**GenStackCostCurves**: 
Standard cost curve projections for applicable genstack plants (Transformation settings)


 - Veda Tag: `~FI_T`


 - Data Location: `data_intermediate/stage_4_veda_format/subres_elc/genstack/Transformation_cost_curves.csv`


**GenStackCostFixedInstalls**: 
Defines fixed install dates for genstack plants (Transformation settings)


 - Veda Tag: `~FI_T`


 - Data Location: `data_intermediate/stage_4_veda_format/subres_elc/genstack/Transformation_fixed_installs.csv`


### WorkSheet: ELC_Batteries
**BatteryProcessDeclarations**: 
Declares processes for battery technologies


 - Veda Tag: `~FI_Process`


 - Data Location: `data_intermediate/stage_4_veda_format/subres_elc/storage/battery_processes.csv`


**BatteryParameters**: 
Describes key assumptions for battery technologies


 - Veda Tag: `~FI_T`


 - Data Location: `data_intermediate/stage_4_veda_format/subres_elc/storage/battery_parameters.csv`


**BatteryCostCurves**: 
Adds cost curves to battery technologies


 - Veda Tag: `~FI_T`


 - Data Location: `data_intermediate/stage_4_veda_format/subres_elc/storage/battery_costs_transformation.csv`


### WorkSheet: ELC_OffshoreWind
**OffshoreWindCostCurves**: 
Advanced cost curve projections for offshore wind plants (NREL Moderate)


 - Veda Tag: `~FI_T`


 - Data Location: `data_intermediate/stage_4_veda_format/subres_elc/offshore/cost_curves_moderate.csv`


**OffshoreWindDetails**: 
Provides key assumptions for offshore wind plants


 - Veda Tag: `~FI_T`


 - Data Location: `data_intermediate/stage_4_veda_format/subres_elc/offshore/base_file.csv`


**OffshoreWindProcesses**: 
Declares processes for offshore wind plants


 - Veda Tag: `~FI_Process`


 - Data Location: `data_intermediate/stage_4_veda_format/subres_elc/offshore/process_definitions.csv`

