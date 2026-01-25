# Technology parameters 


To model residential demand at the technology level, we include the following parameters for residential demand technologies: 
 - Efficiency
 - Capital and maintenance costs
 - Asset lifetimes
 - Availability factors

These are detailed below and are carried forward from TIMES-NZ 2.0 assumptions. 


## Efficiency 


Efficiency is a measure of how much input energy is required for a unit of energy service demand output. For each end use, the implied units of energy service demand may be different, so efficiencies are often not comparable between use types.

Note that these efficiency assumptions apply to slightly different technology definitions than those used in the {ref}`census heating disaggregation method<heading-residential-disaggregation-efficiency>`. While efforts have been made to align the two sets, the figures in {numref}`tab-residential-efficiency-enduse-assumptions` are the actual assumptions applied to TIMES-NZ residential technologies.


```{list-table} Residential technology efficiency by end use
:header-rows: 1
:name: tab-residential-efficiency-enduse-assumptions
* - End Use
  - Technology
  - Fuel
  - Efficiency
* - Clothes Dryer
  - Clothes Dryer
  - Electricity
  - 25%
* - Clothes Washers
  - Clothes Washers
  - Electricity
  - 25%
* - Cooking
  - Cooking Appliances
  - Electricity
  - 75%
* - 
  - Cooking Appliances
  - LPG
  - 40%
* - 
  - Cooking Appliances
  - Natural Gas
  - 40%
* - Dishwashers
  - Dishwashers
  - Electricity
  - 25%
* - IT and Entertainment
  - Electronics
  - Electricity
  - 90%
* - Lighting
  - Fluorescent
  - Electricity
  - 68%
* - 
  - Incandescent/Halogen
  - Electricity
  - 15%
* - 
  - LED
  - Electricity
  - 95%
* - Miscellaneous
  - Electronics
  - Electricity
  - 100%
* - Motive power
  - Internal Combustion Engine
  - Diesel
  - 25%
* - Motive power
  - Internal Combustion Engine
  - Petrol
  - 25%
* - Refrigeration
  - Refrigeration Systems
  - Electricity
  - 180%
* - Space cooling
  - Heat Pump (for Cooling)
  - Electricity
  - 345%
* - Space heating
  - Burner (Direct Heat)
  - LPG
  - 80%
* - 
  - Burner (Direct Heat)
  - Natural Gas
  - 80%
* - 
  - Burner (Direct Heat)
  - Wood
  - 70%
* - 
  - Coal Heaters
  - Coal
  - 55%
* - 
  - Ground source heat pump
  - Geothermal
  - 40%
* - 
  - Heat Pump (for Heating)
  - Electricity
  - 375%
* - 
  - Resistance Heater
  - Electricity
  - 100%
* - Water heating
  - Burner, with Wetback
  - Wood
  - 60%
* - 
  - Gas Water Heater
  - LPG
  - 80%
* - 
  - Gas Water Heater
  - Natural Gas
  - 80%
* - 
  - Hot Water Cylinder
  - Electricity
  - 100%
* - 
  - Solar thermal hot water cylinder
  - Solar
  - 60%
```


## Lifetime assumptions 

Technologies that reach their technical lifetime are replaced in the model. We assume that currently existing stock has a uniformly distributed range of ages. These lifetimes are detailed below and have been carried forward from TIMES 2.0.

```{list-table} Residential technology lifetime assumptions 
:header-rows: 1
:name: tab-res-lifetimes
* - End Use
  - Technology
  - Fuel
  - Lifetime (years)
* - Clothes Dryer
  - Clothes Dryer
  - Electricity
  - 15
* - Clothes Washers
  - Clothes Washers
  - Electricity
  - 15
* - Cooking
  - Cooking Appliances
  - Electricity
  - 13
* - 
  - Cooking Appliances
  - LPG
  - 13
* - 
  - Cooking Appliances
  - Natural Gas
  - 13
* - Dishwashers
  - Dishwashers
  - Electricity
  - 15
* - IT and Entertainment
  - Electronics
  - Electricity
  - 5
* - Lighting
  - Fluorescent
  - Electricity
  - 5
* - 
  - Incandescent/Halogen
  - Electricity
  - 7
* - 
  - LED
  - Electricity
  - 1
* - Miscellaneous
  - Electronics
  - Electricity
  - 14
* - Motive power
  - Internal Combustion Engine
  - Diesel
  - 15
* - Motive power
  - Internal Combustion Engine
  - Petrol
  - 15
* - Refrigeration
  - Refrigeration Systems
  - Electricity
  - 18
* - Space cooling
  - Heat Pump (for Cooling)
  - Electricity
  - 12
* - Space heating
  - Burner (Direct Heat)
  - LPG
  - 20
* - 
  - Burner (Direct Heat)
  - Natural Gas
  - 20
* - 
  - Burner (Direct Heat)
  - Wood
  - 50
* - 
  - Coal Heaters
  - Coal
  - 50
* - 
  - Ground source heat pump
  - Geothermal
  - 20
* - 
  - Heat Pump (for Heating)
  - Electricity
  - 12
* - 
  - Resistance Heater
  - Electricity
  - 5
* - Water heating
  - Burner, with Wetback
  - Wood
  - 50
* - 
  - Gas Water Heater
  - LPG
  - 20
* - 
  - Gas Water Heater
  - Natural Gas
  - 20
* - 
  - Hot Water Cylinder
  - Electricity
  - 20
* - 
  - Solar thermal hot water cylinder
  - Solar
  - 20
```


## Availability factors 


Availability factors detail our assumptions on how often a particular technology might run to meet the energy service demand. These assumptions are detailed in {numref}`ab-res-af-assumptions`. While the percentage share is the direct model input for TIMES, we include the implied average running hours per week for each technology. This impacts the relationship between capacity and output, as it might be more cost-effective to upgrade technology that is used more often.

```{list-table} Availability factor assumptions
:header-rows: 1
:name: tab-res-af-assumptions
* - End Use
  - Assumed weekly hours
  - Availability factor
* - Electronics
  - 28
  - 16.70%
* - Cooking
  - 7
  - 4.20%
* - Lighting
  - 28
  - 16.70%
* - Dishwashers
  - 7
  - 4.20%
* - Clothes Drying
  - 1
  - 0.60%
* - Clothes Washing
  - 7
  - 4.20%
* - Space Heating
  - 13.8
  - 8.20%
* - Water Heating
  - 21
  - 12.50%
* - Motive Power, Mobile
  - 0.5
  - 0.30%
* - Refrigeration
  - 70
  - 41.70%
* - Space Cooling
  - 1.8
  - 1.10%
```


## Capital and operating costs 

Capital costs are from TIMES 2.0 and have been adjusted for inflation to 2023 dollars. Costs are listed specifically for technology at detached dwellings. If the cost is different for a joined dwelling, these are listed in parentheses. Some technologies do not include a capital cost. These are technologies that we assume can no longer be built, so capital costs are not relevant. Maintenance costs are included for natural gas technologies, as per TIMES 2.0. 



```{list-table} Capital and operating costs for residential service technologies (NZD 2023)
:header-rows: 2
:name: tab-res-capex
* - End Use
  - Technology
  - Fuel
  - Capital cost NZD/kW
  - 
  - OPEX NZD/kW/year
* - 
  - 
  - 
  - Detached
  - Joined
  - 
* - Clothes Dryer
  - Clothes Dryer
  - Electricity
  - 2,045
  - 2,045
  - 
* - Clothes Washers
  - Clothes Washers
  - Electricity
  - 4,907
  - 4,907
  - 
* - Cooking
  - Cooking Appliances
  - Electricity
  - 553
  - 553
  - 
* - 
  - Cooking Appliances
  - LPG
  - 430
  - 430
  - 184
* - 
  - Cooking Appliances
  - Natural Gas
  - 430
  - 430
  - 184
* - Dishwashers
  - Dishwashers
  - Electricity
  - 3,243
  - 3,243
  - 
* - IT and Entertainment
  - Electronics
  - Electricity
  - 900
  - 900
  - 
* - Lighting
  - Fluorescent
  - Electricity
  - 1,444
  - 1,444
  - 
* - 
  - Incandescent/Halogen
  - Electricity
  - 955
  - 955
  - 
* - 
  - LED
  - Electricity
  - 1,410
  - 1,410
  - 
* - Motive power
  - Internal Combustion Engine
  - Diesel
  - 1,801
  - 1,801
  - 
* - Motive power
  - Internal Combustion Engine
  - Petrol
  - 1,801
  - 1,801
  - 
* - Refrigeration
  - Refrigeration Systems
  - Electricity
  - 4,028
  - 4,028
  - 
* - Space cooling
  - Heat Pump (for Cooling)
  - Electricity
  - 1105
  - 841
  - 
* - Space heating
  - Burner (Direct Heat)
  - LPG
  - 1548
  - 991
  - 184
* - 
  - Burner (Direct Heat)
  - Natural Gas
  - 1548
  - 991
  - 184
* - 
  - Burner (Direct Heat)
  - Wood
  - 458
  - NA[^no_more_wood]
  - 
* - 
  - Coal Heaters
  - Coal
  - 
  - 
  - 
* - 
  - Ground source heat pump
  - Geothermal
  - 
  - 
  - 
* - 
  - Heat Pump (for Heating)
  - Electricity
  - 685
  - 863
  - 
* - 
  - Resistance Heater
  - Electricity
  - 29
  - 29
  - 
* - Water heating
  - Burner, with Wetback
  - Wood
  - 
  - 
  - 
* - 
  - Gas Water Heater
  - LPG
  - 307
  - 307
  - 184
* - 
  - Gas Water Heater
  - Natural Gas
  - 307
  - 307
  - 184
* - 
  - Hot Water Cylinder
  - Electricity
  - 931
  - 931
  - 
* - 
  - Solar hot water cylinder
  - Solar
  - 2,121
  - 2,121
  - 
```


[^no_more_wood]: We assume no further wood burners can be built in joined dwellings.