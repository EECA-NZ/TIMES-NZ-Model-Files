[Back to Model Structure Index](../model-structure.md)
## VT_TIMESNZ_IND.xlsx
### WorkSheet: Industry demand
**IndustryEndUseCommodityDefinitions**: 
Defines enduse industry commodities, such as space heating


 - Veda Tag: `~FI_Comm`


 - Data Location: `data_intermediate/stage_4_veda_format/base_year_ind/enduse_commodity_definitions.csv`


**IndustryFuelCommodityDefinitions**: 
Defines industry input fuel commodities, such as electricity (indELC)


 - Veda Tag: `~FI_Comm`


 - Data Location: `data_intermediate/stage_4_veda_format/base_year_ind/fuel_commodity_definitions.csv`


**IndustryProcessDefinitions**: 
Defines industry enduse processes, such as heatpumps


 - Veda Tag: `~FI_Process`


 - Data Location: `data_intermediate/stage_4_veda_format/base_year_ind/demand_process_definitions.csv`


**IndustryDemand**: 
Industry base year demand topology and technical parameters


 - Veda Tag: `~FI_T`


 - Data Location: `data_intermediate/stage_4_veda_format/base_year_ind/industry_baseyear_details.csv`


**IndustryDemand2**: 
Industry total commodity demand (met by activity bound per process)


 - Veda Tag: `~FI_T: Demand`


 - Data Location: `data_intermediate/stage_4_veda_format/base_year_ind/industry_commodity_demand.csv`


### WorkSheet: Fuel Delivery
**IndustryFuelProcessDefinitions**: 
Defines industry fuel delivery processes that convert fuels (like NGA) into ind fuels (INDNGA)


 - Veda Tag: `~FI_Process`


 - Data Location: `data_intermediate/stage_4_veda_format/base_year_ind/fuel_delivery_definitions.csv`


**IndustryFuelProcessParameters**: 
Sets parameters for industry fuel delivery processes (mostly delivery costs)


 - Veda Tag: `~FI_T`


 - Data Location: `data_intermediate/stage_4_veda_format/base_year_ind/fuel_delivery_parameters.csv`


### WorkSheet: Emissions
**IndustryEmissionsParameters**: 
Defines emissions factors for industry fuels. Currently hardcoded and need a proper update. To do with all other demand emission factors for consistency


 - Veda Tag: `~COMEMI`


 - Data Location: `VT_TIMESNZ_IND.toml`


**IndustryEmissionsDefinitions**: 
Defines the industry emissions commodity


 - Veda Tag: `~FI_Comm`


 - Data Location: `VT_TIMESNZ_IND.toml`

