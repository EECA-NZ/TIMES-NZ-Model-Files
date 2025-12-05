[Back to Index](../model-structure.md)
## VT_TIMESNZ_TRA.xlsx
### WorkSheet: TRA_FuelSupply
**TransportFuelProcessDefinitions**: 
Defines the processes that can convert other TIMES Commodities into these fuels (eg PET -> TRAPET)


 - Veda Tag: `~FI_Process`


 - Data Location: `data_intermediate/stage_4_veda_format/base_year_tra/tra_fuel_process_definitions.csv`


**TransportFuelCommodityDefinitions**: 
Defines commodities that are used to meet transport demand (eg TRAPET)


 - Veda Tag: `~FI_Comm`


 - Data Location: `data_intermediate/stage_4_veda_format/base_year_tra/tra_fuel_commodity_definitions.csv`


**TransportFuelProcessParameters**: 
Defines technical parameters for dummy transport fuel processes (barely used)


 - Veda Tag: `~FI_T`


 - Data Location: `data_intermediate/stage_4_veda_format/base_year_tra/tra_fuel_process_parameters.csv`


### WorkSheet: TRA_Emissions
**TransportEmissionsFactors**: 
Defines emissions factors for transport fuels. Sources and references listed in config file. Excludes CH4 and N2O.


 - Veda Tag: `~COMEMI`


 - Data Location: `data_intermediate/stage_4_veda_format/base_year_tra/tra_emission_factors.csv`


### WorkSheet: TRA_Demand-Vehicles
**TransportProcessParameters2**: 
Summary of transport demand for existing transport technologies by commodity


 - Veda Tag: `~FI_T: Demand`


 - Data Location: `data_intermediate/stage_4_veda_format/base_year_tra/tra_process_parameters2.csv`


**TransportProcessParameters**: 
Technical parameters for existing transport technologies


 - Veda Tag: `~FI_T`


 - Data Location: `data_intermediate/stage_4_veda_format/base_year_tra/tra_process_parameters.csv`


**TransportCommodityDefinitions**: 
Defines commodities that are in the existing transport fleet


 - Veda Tag: `~FI_Comm`


 - Data Location: `data_intermediate/stage_4_veda_format/base_year_tra/tra_commodity_definitions.csv`


**TransportProcessDefinitions**: 
Defines all existing technologies capable for transport demand


 - Veda Tag: `~FI_Process`


 - Data Location: `data_intermediate/stage_4_veda_format/base_year_tra/tra_process_definitions.csv`

