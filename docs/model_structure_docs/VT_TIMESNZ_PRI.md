[Back to Index](../model-structure.md)
## VT_TIMESNZ_PRI.xlsx
### WorkSheet: Total CO2
**TOTCO2AggregationDefinition**: 
Defines TOTCO2 as the sum of all other emissions commodities. No refinery.


 - Veda Tag: `~COMAGG`


 - Data Location: `VT_TIMESNZ_PRI.toml`


**TOTCO2CommodityDefinition**: 
Declares TOTCO2 commodity. In old TIMES, all other emissions were re-declared here (not necessary)


 - Veda Tag: `~FI_Comm`


 - Data Location: `VT_TIMESNZ_PRI.toml`


### WorkSheet: Coal
**CoalProcessDeclarations**: 
Declare coal processes (mining and importing)


 - Veda Tag: `~FI_Process`


 - Data Location: `VT_TIMESNZ_PRI.toml`


**CoalCommodityDeclarations**: 
Declare coal commodity


 - Veda Tag: `~FI_Comm`


 - Data Location: `VT_TIMESNZ_PRI.toml`


**CoalParameterDeclarations**: 
Declare coal processes (mining and importing). Sets coal price (sans carbon) and annual availability . Very simple approach


 - Veda Tag: `~FI_T`


 - Data Location: `VT_TIMESNZ_PRI.toml`


### WorkSheet: Oil
**OilProcessDeclarations**: 
Declare oil and oil product supply processes (mining, imports). Include exports


 - Veda Tag: `~FI_Process`


 - Data Location: `data_raw/coded_assumptions/oil_and_gas/oil_process_definitions.csv`


**OilSupplyProcessParameters**: 
Set base year activity and cost assumptions for oil product imports. Note extremely simple imports used directly


 - Veda Tag: `~FI_T`


 - Data Location: `data_intermediate/stage_4_veda_format/base_year_pri/imported_fuel_costs.csv`


**OilSupplyCommodityDefinitions**: 
Define Oil and oil product commodities


 - Veda Tag: `~FI_Comm`


 - Data Location: `VT_TIMESNZ_PRI.toml`


### WorkSheet: Biofuels
**BiofuelSupplyForecasts**: 
Biomass/biofuel supply and costs forecasts per region 


 - Veda Tag: `~FI_T`


 - Data Location: `data_intermediate/stage_4_veda_format/base_year_pri/biofuel_supply_forecasts.csv`


**BiofuelProcessDeclarations**: 
Declare biomass/biofuel processes, including raw production and transformation


 - Veda Tag: `~FI_Process`


 - Data Location: `data_intermediate/stage_4_veda_format/base_year_pri/biofuel_supply_process_declarations.csv`


**BiofuelParameterDeclarations**: 
Declare conversion processes for biofuel. Sets investment and operation costs, annual availability, lifetime


 - Veda Tag: `~FI_T`


 - Data Location: `data_raw/coded_assumptions/biofuels/plant_processes.csv`


**DeclareBiofuels**: 
Declare biofuel energy commodities


 - Veda Tag: `~FI_Comm`


 - Data Location: `VT_TIMESNZ_PRI.toml`


### WorkSheet: Natural Gas
**GasSupplyForecasts**: 
Add natural gas production forecast limits. Excludes contingent - only the 2P reserves.


 - Veda Tag: `~FI_T`


 - Data Location: `data_intermediate/stage_4_veda_format/base_year_pri/deliverability_forecasts_2p.csv`


**GasSupplyParameters**: 
Production costs and fugitive emissions for domestic gas fields, and output commodity declaration.


 - Veda Tag: `~FI_T`


 - Data Location: `data_intermediate/stage_4_veda_format/base_year_pri/natural_gas_production_parameters.csv`


**GasSupplyProcessDefinitions**: 
Declare natural gas production processes


 - Veda Tag: `~FI_Process`


 - Data Location: `VT_TIMESNZ_PRI.toml`


**GasSupplyCommodityDefinitions**: 
Declare natural gas and fugitive emissions commodities (North Island only). Hardcoded in user config.


 - Veda Tag: `~FI_Comm`


 - Data Location: `VT_TIMESNZ_PRI.toml`


### WorkSheet: Hydrogen
**HydrogenProcessDeclarations**: 
Declare hydrogen production placeholder. We need to later build actual electrolysis.


 - Veda Tag: `~FI_Process`


 - Data Location: `VT_TIMESNZ_PRI.toml`


**HydrogenPlaceHolderParameterDeclarations**: 
Placeholder hydrogen production process, just to ensure the model doesn't get free hydrogen before electrolysis added 


 - Veda Tag: `~FI_T`


 - Data Location: `VT_TIMESNZ_PRI.toml`


**DeclareHydrogenCommodity**: 
Hydrogen commodity


 - Veda Tag: `~FI_Comm`


 - Data Location: `VT_TIMESNZ_PRI.toml`

