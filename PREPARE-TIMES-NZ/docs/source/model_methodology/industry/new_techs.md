# New technologies

New technologies are based on proven commercially available technology (TRL 7 and above) that have been, or will be, installed and commissioned in New Zealand through initiatives such as EECA’s technology demonstration fund and the Government Investment in Decarbonising Industry (GIDI) and haven’t been included in TIMES 3.0 existing technology. This list will be reviewed regularly to ensure that all commercially available new technologies are considered in TIMES.

New technologies that will be considered in TIMES 3.0 are listed in {numref}`tab-new_ind_techs`.

```{list-table} New industrial technologies to be considered in TIMES 3.0
:header-rows: 1
:name: tab-new_ind_techs
* - Fuel
  - Technology
  - Use
  - Lifetime (years)
  - Energy Efficiency
  - Capital Cost ($/kW)
* - Electricity
  - Steam Generating Heat Pumps
  - Intermediate Heat (100-300°C), Process Requirements
  - 15
  - 2.3
  - 3,000
* - Biomass
  - Biomass conversion (existing coal boiler to biomass boiler)
  - Intermediate Heat (100-300°C), Process Requirements
  - N/A
  - 0.78
  - 286[^biomass_conversion_costs]
* - Electricity
  - Mechanical Vapour Recompression (MVR)
  - Intermediate Heat (100-300°C), Process Requirements
  - 15
  - [TBC]
  - 2,000
* - Electricity
  - Internal Combustion Engine (Land Transport) – Battery Electric
  - Motive Power, Mobile
  - 15.5
  - 0.55
  - 4,776[^battery_electric_costs]
* - Electricity
  - Internal Combustion Engine (Land Transport) – Plug-in Hybrid
  - Motive Power, Mobile
  - 15.5
  - 0.28
  - 1,331
* - Electricity
  - Internal Combustion Engine (Land Transport) - Hydrogen
  - Motive Power, Mobile
  - 15.5
  - 0.28
  - 5,970[^hydrogen_fuelcell_costs]
```


[^biomass_conversion_costs]: Average capital cost for boiler conversions taken from GIDI funded projects. 
[^battery_electric_costs]: Average capital cost for battery electric calculated relative to diesel ICE. 
[^hydrogen_fuelcell_costs]: Average capital cost for hydrogen fuelcell calculated relative to diesel ICE. 

Note the values provided above are preliminary and based on limited industry knowledge/sources. These will be updated as better source information is obtained.

**Steam generating heat pumps:** this technology typically requires waste heat, so we assume they can be deployed at industrial sites with existing process heat needs above 100°C, i.e. where waste heat is likely to already be available. An 80°C temperature lift is assumed, yielding a Coefficient of Performance (COP), or energy efficiency, of 2.3.

**Mechanical Vapour Recompression:** this technology increases process efficiency by recovering and reusing low-pressure steam. It is commonly implemented as a retrofit alongside existing or new steam boilers to reduce fuel consumption.

**Low temperature heatpumps:** These do not strictly count as "new technology", as they exist in the historical data. However, we note that they do not exist in all industrial subsectors in EEUD data. By default, TIMES subsectors can only make use of existing technologies identifed within the subsector, or any new technologies assigned to the subsector. This means that the model by default cannot install heatpumps in sectors where they are not already found. We assume this is an unlikely constraint, so instead allow low temperature heatpumps to be built in all industrial subsectors. These use cost and efficiency parameters identified in the existing data. We apply this method to both low temperature process heat and low temperature space heating heatpumps.

