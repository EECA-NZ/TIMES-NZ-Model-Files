[Back to Model Structure Index](../model-structure.md)
## VT_TIMESNZ_COM.xlsx
### WorkSheet: COM_Emissions
**CommercialEmissionsFactors**: 
Defines emissions factors for commercial fuels


 - Veda Tag: `~COMEMI`


 - Data Location: `data_intermediate/stage_4_veda_format/base_year_com/commercial_emission_factors.csv`


### WorkSheet: COM_Fuels
**CommercialFuelProcessParameters**: 
Defines technical parameters for dummy commercial fuel processes (barely used)


 - Veda Tag: `~FI_T`


 - Data Location: `data_intermediate/stage_4_veda_format/base_year_com/fuel_delivery_parameters.csv`


**CommercialFuelProcessDefinitions**: 
Defines the processes that can convert other TIMES Commodities into these fuels (eg COA -> COMCOA)


 - Veda Tag: `~FI_Process`


 - Data Location: `data_intermediate/stage_4_veda_format/base_year_com/fuel_delivery_definitions.csv`


**CommercialFuelCommodityDefinitions**: 
Defines commodities that are used to meet commercial demand (eg COMCOA)


 - Veda Tag: `~FI_Comm`


 - Data Location: `data_intermediate/stage_4_veda_format/base_year_com/fuel_commodity_definitions.csv`


### WorkSheet: COM_Demand
**CommercialCommodityDefinitions**: 
Defines commodities that are in the existing commercial sector


 - Veda Tag: `~FI_Comm`


 - Data Location: `data_intermediate/stage_4_veda_format/base_year_com/enduse_commodity_definitions.csv`


**CommercialProcessDefinitions**: 
Defines all existing technologies capable for commercial demand


 - Veda Tag: `~FI_Process`


 - Data Location: `data_intermediate/stage_4_veda_format/base_year_com/demand_process_definitions.csv`


**CommercialProcessParameters**: 
Technical parameters for existing commercial technologies


 - Veda Tag: `~FI_T`


 - Data Location: `data_intermediate/stage_4_veda_format/base_year_com/commercial_baseyear_demand.csv`


**CommercialProcessParameters2**: 
Summary of commercial demand for existing commercial technologies by commodity


 - Veda Tag: `~FI_T: Demand`


 - Data Location: `data_intermediate/stage_4_veda_format/base_year_com/commercial_baseyear_demand2.csv`

