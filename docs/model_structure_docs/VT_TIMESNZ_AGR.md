[Back to Index](../model-structure.md)
## VT_TIMESNZ_AGR.xlsx
### WorkSheet: AGR_Emissions
**AgrEmissionsFactors**: 
Defines emissions factors for agr fuels


 - Veda Tag: `~AGREMI`


 - Data Location: `data_intermediate/stage_4_veda_format/base_year_agr/agr_emission_factors.csv`


### WorkSheet: AGR_Demand
**AgrProcessParameters2**: 
Summary of agr demand for existing agr technologies by commodity


 - Veda Tag: `~FI_T: Demand`


 - Data Location: `data_intermediate/stage_4_veda_format/base_year_agr/agr_baseyear_demand2.csv`


**AgrProcessParameters**: 
Technical parameters for existing agr technologies


 - Veda Tag: `~FI_T`


 - Data Location: `data_intermediate/stage_4_veda_format/base_year_agr/agr_baseyear_demand.csv`


**AgrProcessDefinitions**: 
Defines all existing technologies capable for agr demand


 - Veda Tag: `~FI_Process`


 - Data Location: `data_intermediate/stage_4_veda_format/base_year_agr/demand_process_definitions.csv`


**AgrCommodityDefinitions**: 
Defines commodities that are in the existing agr sector


 - Veda Tag: `~FI_Comm`


 - Data Location: `data_intermediate/stage_4_veda_format/base_year_agr/enduse_commodity_definitions.csv`


### WorkSheet: AGR_Fuels
**AgrFuelProcessParameters**: 
Defines technical parameters for dummy agr fuel processes (barely used)


 - Veda Tag: `~FI_T`


 - Data Location: `data_intermediate/stage_4_veda_format/base_year_agr/fuel_delivery_parameters.csv`


**AgrFuelProcessDefinitions**: 
Defines the processes that can convert other TIMES Commodities into these fuels (eg COA -> COMCOA)


 - Veda Tag: `~FI_Process`


 - Data Location: `data_intermediate/stage_4_veda_format/base_year_agr/fuel_delivery_definitions.csv`


**AgrFuelCommodityDefinitions**: 
Defines commodities that are used to meet ag, forest, fish demand (eg AGRCOA)


 - Veda Tag: `~FI_Comm`


 - Data Location: `data_intermediate/stage_4_veda_format/base_year_agr/fuel_commodity_definitions.csv`

