# Technology parameters

Existing technologies and their details, such as lifetimes, capacity factors, efficiencies are detailed here.

## Equipment lifetime and decommissioning

This section details the methods and data sources for equipment lifetimes, existing ages, and expected decommissioning dates.

### Rotating equipment such as pumps, fans, compressor, motors, refrigeration, internal combustion engines
Where possible, equipment lifetimes are taken as estimated useful life (years) from the Inland Revenue’s General depreciation rates October 2024 document[^ir_lifetimes], if unavailable, data are taken from other EECA sources such as technology scans, Energy Transition Accelerator Reports and industry sources/knowledge.

### Boilers/furnaces/ovens/refiners/reformers/heat exchangers
Boilers, refiners and reformers are all given a lifetime out to 2060 (i.e. the full TIMES model period), as this equipment is generally operated well past its original engineering and economic design life, and is typically only updated when it makes economic sense to (e.g. when the Net Present Value is greater than zero or the Marginal Abatement Cost is lower than the carbon price).

For coal fired boilers, the low to medium temperature coal boilers (i.e. under 300°C) are modelled to switch to renewable energy before 2037, when the National Direction for Greenhouse Gas Emissions from Industrial Process Heat regulations come into effect, or before that date if it makes financial sense. 

### Electrical equipment such as heaters

As with rotating equipment, lifetimes are taken as estimated useful life (years) from the Inland Revenue’s General depreciation rates October 2024 document, if unavailable, data are taken from other EECA sources such as technology scans, Energy Transition Accelerator Reports and industry sources/knowledge.

### Aluminium, urea, methanol and steel equipment

Aluminium, steel, methanol and urea technologies have their lifetimes extended throughout the model horizon. We assume these technologies will not be replaced, except for the NZ Steel furnace conversion which is planned to be operational in Q2 of 2026. 
A full list of lifetime assumptions can be found in {numref}`tab-ind_tech_lifetimes`. Technologies with `N/A` lifetimes are assumed to never retire,  unless it makes economic sense to switch to a different technology before the full model period. 

[^ir_lifetimes]: IR | General depreciation rates August 2024: <https://www.ird.govt.nz/-/media/project/ir/home/documents/forms-and-guides/ir200---ir299/ir265/ir265-august-2024.pdf>

```{list-table} Equipment lifetime by technology
:header-rows: 1
:name: tab-ind_tech_lifetimes
* - Technology
  - Life (years)
* - Electric Furnace
  - N/A
* - Lights
  - 10
* - Boiler Systems
  - N/A
* - Burner (Direct Heat)
  - N/A
* - Furnace/Kiln
  - N/A
* - Heat Pump (for Heating)
  - 15
* - Resistance Heater
  - 15.5
* - Electric Motor
  - 10
* - Pump Systems (for Fluids, etc.)
  - 10
* - Internal Combustion Engine (Land Transport)
  - 15.5
* - Stationary Engine
  - 20
* - Air Compressors
  - 15.5
* - Fan Systems
  - 16
* - HVAC
  - 10
* - Refrigeration Systems
  - 20
* - Industrial Ovens
  - N/A
* - Feedstock
  - N/A
* - Reformer
  - N/A
* - Refiners
  - N/A
```

## Availability factors

The availability factor represents the share of a given year a piece of equipment is “available” to operate:

```{math}
Availability Factor = (Available Operating Time) / (Total Time)
```

It is challenging to apply an availability to a piece of technology (e.g. medium temperature boiler) across different industrial sites. For example, Fonterra would operate their boiler differently to a small family-owned dairy manufacturing site. Therefore, we currently set a single availability factor. An availability factor of $0.5$ was selected to provide a standard value to use across technologies when accurate numbers are unavailable.


## Energy efficiency



A full list of energy efficiency assumptions can be found in {numref}`tab-ind_eff`. These assumptions are for standard technologies used across various sectors and not for specific bespoke technologies such as the furnaces used at New Zealand aluminium smelter and NZ steel.

Energy efficiency for process heat devices came from the Cost Assessment Tool developed for the Resource Management Act (RMA) National Direction for Greenhouse Gas Emissions from Industrial Process Heat[^cat]. The technology’s energy efficiency was taken as the middle range from the “lower efficiency bound” and the “upper efficiency bound”.

Efficiencies for internal combustion engine (land transport), pump systems (for fluids), electric motors, and stationary engines were found using literature reviews.

```{list-table} Energy efficiency by technology
:header-rows: 1
:name: tab-ind_eff
* - Technology
  - Fuel
  - Efficiency
* - Boiler Systems
  - Biogas
  - 0.85
* - Boiler Systems
  - Coal
  - 0.78
* - Boiler Systems
  - Diesel
  - 0.85
* - Boiler Systems
  - Electricity
  - 0.94
* - Boiler Systems
  - Fuel Oil
  - 0.85
* - Boiler Systems (Heat Exchanger)
  - Geothermal
  - 0.85
* - Boiler Systems
  - LPG
  - 0.85
* - Boiler Systems
  - Natural Gas
  - 0.85
* - Boiler Systems
  - Wood
  - 0.78
* - Burner (Direct Heat)
  - LPG
  - 0.88
* - Burner (Direct Heat)
  - Natural Gas
  - 0.88
* - Electric Furnace
  - Electricity
  - 0.9
* - Electric Motor
  - Electricity
  - 0.9
* - Furnace/Kiln
  - Coal
  - 0.78
* - Furnace/Kiln
  - Electricity
  - 0.9
* - Furnace/Kiln
  - Fuel Oil
  - 0.85
* - Furnace/Kiln
  - Natural Gas
  - 0.85
* - Heat Pump (space heating)
  - Electricity
  - 3.15
* - Heat Pump (process heat)
  - Electricity
  - 4.05
* - Industrial Ovens
  - Coal
  - 0.78
* - Industrial Ovens
  - Electricity
  - 0.9
* - Industrial Ovens
  - Natural Gas
  - 0.85
* - Internal Combustion Engine (Land Transport)
  - Diesel
  - 0.2
* - Internal Combustion Engine (Land Transport)
  - Natural Gas
  - 0.12
  ````


[^cat]: The Cost Assessment Tool can be found on EECA’s website: [EECA | Emissions Plan Guidance](https://www.eeca.govt.nz/regulations/emissions-plan-guidance/)

## Capital costs 

A full list of capital cost assumptions can be found in Table UPDATE REFERENCE  below. These assumptions are for standard technologies used across various sectors and not for specific bespoke technologies such as the furnaces used at New Zealand aluminium smelter and NZ steel.

These capital costs consider the cost of the equipment plus the materials handling equipment for coal and biomass boilers as well as the electrical upgrades for electric boilers and heat pumps and anaerobic digesters for biogas boilers. Operating costs such as fuel and maintenance are also not included.

Capital costs for process heat devices came from the Cost Assessment Tool developed for the RMA National Direction for Greenhouse Gas Emissions from Industrial Process Heat[^cat]. A 30% factor was applied to these numbers due to feedback from industry that these numbers were too low during road testing of the tool.

Capital costs for internal combustion engine (land transport), pump systems (for fluids) and stationary engine were kept the same as in TIMES 2.0 due to lack of data. These have been adjusted for inflation, but are necessarily by assumption.

```{list-table} Capital cost (NZD/kW) for various technology
:header-rows: 1
:name: tab-ind_capex
* - Tech
  - Fuel
  - Capital Cost (NZD/kW), 2023
* - Boiler Systems
  - Biogas
  - $4,259
* - Boiler Systems
  - Coal
  - $1,654
* - Boiler Systems
  - Diesel
  - $628
* - Boiler Systems
  - Electricity
  - $1,020[^capex_elc_boiler]
* - Boiler Systems
  - Fuel Oil
  - $628
* - Boiler Systems
  - LPG
  - $712
* - Boiler Systems
  - Natural Gas
  - $513
* - Boiler Systems
  - Wood
  - $1,103[^capex_wood_burner]
* - Burner (Direct Heat)
  - LPG
  - $691
* - Burner (Direct Heat)
  - Natural Gas
  - $691
* - Electric Furnace
  - Electricity
  - $136
* - Electric Motor
  - Electricity
  - $280
* - Furnace/Kiln
  - Coal
  - $1,654
* - Furnace/Kiln
  - Electricity
  - $136
* - Furnace/Kiln
  - Fuel Oil
  - $691
* - Furnace/Kiln
  - Natural Gas
  - $691
* - Heat Pump (space heating)
  - Electricity
  - $712
* - Heat Pump (process heat)
  - Electricity
  - $1,506[^capex_heat_pump]
* - Industrial Ovens
  - Coal
  - $314
* - Industrial Ovens
  - Electricity
  - $283
* - Industrial Ovens
  - Natural Gas
  - $262
* - Internal Combustion Engine
  - Diesel
  - $700
* - Internal Combustion Engine
  - Natural Gas
  - $700
* - Internal Combustion Engine
  - Petrol
  - $700[^diesel_ice]
* - Pump Systems (for Fluids, etc.)
  - Electricity
  - $2,835
* - Resistance Heater
  - Electricity
  - $141
* - Stationary Engine
  - Diesel
  - $559
* - Stationary Engine
  - Petrol
  - $559[^diesel_ice]
```


[^capex_elc_boiler]: Average capital cost taken from GIDI funded projects including electrical upgrades (where required)
[^capex_wood_burner]: Average capital cost taken from GIDI funded projects including handling system
[^capex_heat_pump]: Average capital cost taken from GIDI funded projects including electrical upgrades (where required)
[^diesel_ice]: Limited data for these petrol technologies were available, so we assumed the capital costs matched the equivalent diesel engine costs.


## Operating and maintenance costs 

We have included the ability to model different operating and maintenance costs by subsector/end use/technology/fuel. However, due to lack of detailed and complete information, this functionality has not been implemented at this stage.

## Maximum uptake

Maximum uptake is used as a constraint where it would not be possible for a specific technology to be used to produce more than a certain percentage of the end use energy for a specific subsector. 

For instance, it is often not possible for heat recovery technologies to provide enough heat for a specific end use (as it is constrained by the level of current wasted heat). This technology may therefore be constrained to a maximum uptake.

## Setting default uses for "Unknown"/"Other" industrial demand data 

Data in the EEUD is incomplete for some industrial demand. When the industrial subsector or enduse category is unknown, these are assigned to "Unknown". 

Modelling this unknown industrial demand requires additional assumptions. In TIMES 2.0 these were left as “other” technology and “other” enduse, effectively meaning there was no ability to fuel switch or change technologies in this sector. 

However, interrogating the EEUD shows that the Industrial others subsector has significant energy use. From previous EECA analysis, it has been shown that the majority of emissions (noting that emissions can be taken as a proxy for energy use) in the Industrial others subsector are coming from Small to Medium Enterprise (SME) (defined by EECA as outside the top 100 stationary energy users), i.e. 95%. Most SME’s stationary energy is likely from low and intermediate heat requirements, as they are unlikely to have complex manufacturing facilities requiring high pressure, high temperature process heat.

For TIMES-NZ 3.0, fuel use in the EEUD that is not assigned to any end use or technology is instead assigned to default technology and use options. These are defined as the most common technology and use options for any given fuel within this sector. By assigning assumed enduses and technologies, the model can then select the most cost-effective option for this use as normal. Assumed uses and technologies for this sector are detailed in {numref}`tab-other_ind_tech_assumptions`.

```{list-table} Updated technology assumptions in Other (Industry) for TIMES 3.0
:header-rows: 1
:name: tab-other_ind_tech_assumptions
* - Fuel
  - Default Technology
  - Default Use
* - Biogas
  - Boiler Systems
  - Intermediate Heat (100-300°C), Process Requirements
* - Coal
  - Boiler Systems
  - Intermediate Heat (100-300°C), Process Requirements
* - Diesel
  - Internal Combustion Engine (Land Transport)
  - Motive Power, Mobile
* - Electricity
  - Electric Motor
  - Motive Power, Stationary
* - Fuel Oil
  - Furnace/Kiln
  - Intermediate Heat (100-300°C), Process Requirements
* - Geothermal
  - Boiler Systems
  - Intermediate Heat (100-300°C), Process Requirements
* - LPG
  - Boiler Systems
  - Intermediate Heat (100-300°C), Process Requirements
* - Natural Gas
  - Boiler Systems
  - Intermediate Heat (100-300°C), Process Requirements
* - Petrol
  - Internal Combustion Engine (Land Transport)
  - Motive Power, Mobile
* - Wood
  - Boiler Systems
  - Intermediate Heat (100-300°C), Process Requirements
```
