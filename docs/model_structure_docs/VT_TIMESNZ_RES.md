[Back to Index](../model-structure.md)
## VT_TIMESNZ_RES.xlsx
### WorkSheet: Residential demand
**ResidentialEndUseCommodityDefinitions**: 
Defines enduse residential commodities, such as space heating


 - Veda Tag: `~FI_Comm`


 - Data Location: `data_intermediate/stage_4_veda_format/base_year_res/enduse_commodity_definitions.csv`


**ResidentialFuelCommodityDefinitions**: 
Defines residential input fuel commodities, such as electricity (RESELC)


 - Veda Tag: `~FI_Comm`


 - Data Location: `data_intermediate/stage_4_veda_format/base_year_res/fuel_commodity_definitions.csv`


**ResidentialDemand**: 
Residential base year demand topology and technical parameters


 - Veda Tag: `~FI_T`


 - Data Location: `data_intermediate/stage_4_veda_format/base_year_res/residential_baseyear_details.csv`


**ResidentialDemand2**: 
Residential total commodity demand (met by activity bound per process)


 - Veda Tag: `~FI_T: Demand`


 - Data Location: `data_intermediate/stage_4_veda_format/base_year_res/residential_commodity_demand.csv`


**ResidentialProcessDefinitions**: 
Defines residential enduse processes, such as heatpumps


 - Veda Tag: `~FI_Process`


 - Data Location: `data_intermediate/stage_4_veda_format/base_year_res/demand_process_definitions.csv`


### WorkSheet: Fuel Delivery
**ResidentialFuelProcessParameters**: 
Sets parameters for residential fuel delivery processes (mostly delivery costs)


 - Veda Tag: `~FI_T`


 - Data Location: `data_intermediate/stage_4_veda_format/base_year_res/fuel_delivery_parameters.csv`


**ResidentialFuelProcessDefinitions**: 
Defines residential fuel delivery processes that convert fuels (like NGA) into RES fuels (INDNGA)


 - Veda Tag: `~FI_Process`


 - Data Location: `data_intermediate/stage_4_veda_format/base_year_res/fuel_delivery_definitions.csv`


### WorkSheet: Emissions
**ResidentialEmissionsParameters**: 
Defines emissions factors for residential fuels. Currently hardcoded and need a proper update. To do with all other demand emission factors for consistency


 - Veda Tag: `~COMEMI`


 - Data Location: `VT_TIMESNZ_RES.toml`


**ResidentialEmissionsDefinitions**: 
Defines the residential emissions commodity


 - Veda Tag: `~FI_Comm`


 - Data Location: `VT_TIMESNZ_RES.toml`

