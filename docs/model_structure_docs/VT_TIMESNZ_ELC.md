[Back to Index](../model-structure.md)
## VT_TIMESNZ_ELC.xlsx
### WorkSheet: Distribution
**DistributionProcessParameters**: 
Sets technical parameters for distribution processes (eg losses, capacity, etc)


 - Veda Tag: `~FI_T`


 - Data Location: `data_intermediate/stage_4_veda_format/base_year_elc/distribution_parameters.csv`


**DitributionCommodityDefinitions**: 
Defines electricity distribution subprocessses (eg ELCHV, ELCMV, ELCDD)


 - Veda Tag: `~FI_Comm`


 - Data Location: `data_intermediate/stage_4_veda_format/base_year_elc/distribution_commodities.csv`


**DistributionProcessDefinitions**: 
Defines all processes involved in distribution (eg Processes that convert ELC to ELCHV)


 - Veda Tag: `~FI_Process`


 - Data Location: `data_intermediate/stage_4_veda_format/base_year_elc/distribution_processes.csv`


### WorkSheet: Existing Technologies
**ElectricityProcessParameters**: 
Technical parameters for existing electricity generation technologies


 - Veda Tag: `~FI_T`


 - Data Location: `data_intermediate/stage_4_veda_format/base_year_elc/existing_tech_parameters.csv`


**JustDefiningElectricity**: 
Defines ELC and ELCCO2 (should these just be added to [ElectricityCommodityDefinitions]?)


 - Veda Tag: `~FI_Comm`


 - Data Location: `VT_TIMESNZ_ELC.toml`


**ElectricityProcessDefinitions**: 
Defines all existing technologies capable of generating electricity


 - Veda Tag: `~FI_Process`


 - Data Location: `data_intermediate/stage_4_veda_format/base_year_elc/existing_tech_process_definitions.csv`


**ElectricityProcessSpecificCapacityFactors**: 
Locking specific capacity factors for plants where we have precise data, to ensure alignment.


 - Veda Tag: `~FI_T`


 - Data Location: `data_intermediate/stage_4_veda_format/base_year_elc/base_year_capacity_factors.csv`


**ElectricityProcessAgeDistributions**: 
Adds age distributions for each plant or plant type (either NCAP_PASTI when lifetime is known, or PRC_RESID to represent a capacity stock of mixed lifetimes otherwise)


 - Veda Tag: `~FI_T`


 - Data Location: `data_intermediate/stage_4_veda_format/base_year_elc/existing_tech_capacity.csv`


### WorkSheet: Emission Factors
**ElectricityEmissionFactors**: 
Defines co2e kt/PJ emission factors for electricity generation (input basis).


 - Veda Tag: `~COMEMI`


 - Data Location: `data_intermediate/stage_4_veda_format/base_year_elc/emission_factors_elc_fuels.csv`


**GeothermalEmissionFactors**: 
Defines co2e kt/PJ emission factors for geothermal electricity generation per field (output basis). Median value applied if plant data unavailable.


 - Veda Tag: `~FI_T`


 - Data Location: `data_intermediate/stage_4_veda_format/base_year_elc/emission_factors_geo.csv`


**NgawhaEmissionFactorAdjustments**: 
Manual adjustments to reduce Ngawha emissions to 0 by 2026. Note these are hardcoded assumptions in config file.


 - Veda Tag: `~FI_T`


 - Data Location: `VT_TIMESNZ_ELC.toml`


### WorkSheet: Sector_Fuels_ELC
**ElectricityFuelCommodityDefinitions**: 
Defines commodities that can be used for electricity generation (eg ELCNGA)


 - Veda Tag: `~FI_Comm`


 - Data Location: `data_intermediate/stage_4_veda_format/base_year_elc/elc_input_commodity_definitions.csv`


**ElectricityFuelProcessParameters**: 
Defines technical parameters for dummy electricity fuel processes (barely used)


 - Veda Tag: `~FI_T`


 - Data Location: `data_intermediate/stage_4_veda_format/base_year_elc/elc_dummy_fuel_process_parameters.csv`


**ElectricityFuelProcessDefinitions**: 
Defines the processes that can convert other TIMES Commodities into these fuels (eg NGA -> ELCNGA)


 - Veda Tag: `~FI_Process`


 - Data Location: `data_intermediate/stage_4_veda_format/base_year_elc/elc_dummy_fuel_process_definitions.csv`

