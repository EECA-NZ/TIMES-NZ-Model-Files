# Existing plants

The base year generation data is intended to reflect the distribution of 2023 generation across all generating New Zealand assets. These should be available to the model to meet future demand, but with enough information (region, technology, remaining life, etc.) that the model will retire plants at appropriate points and can make least-cost dispatch and peak decisions.

TIMES-NZ requires detailed information on the existing generation stock, including: 
 - Capacity (GW)
 - Fuel inputs and efficiencies 
 - Maintenance costs, including fuel delivery costs. All costs are in 2023 NZD
 - Asset lifetime and current age 
 - Region (North Island/South Island)
 - Peak contribution availability 
 - Capacity factors (the upper limit on the proportion of the year the plant spends generating at full output)
 - Generation levels in the base year, to calibrate historical data (GWh)
 - Availability curves for intermittent generators, such as wind or solar

We have improved on TIMES-NZ 2.0 by building a bottom-up, asset-based model of the existing generation fleet. This gives us much greater detail in how the model utilises the existing generation fleet and will allow us to make very precise changes as needed.

## Existing asset list 
EECA has prepared a list of current plants for the base year generating stock[^eeca_plant_list]. It is closely based on the EA dispatch generation fleet list[^ea_dispatch_generationfleet] and includes mapping to the current plants from MBIE’s EDGS Generation Stack[^edgs_assumptions]. Where possible, we have included mapping to plant names found in the Electricity Authority’s “Generation_MD” estimates of generation by plant[^ea_md_generation]. The asset list has been reviewed and updated based on developer statements and Energy News[^energy_news] resource files for each plant. In some cases, capacities were updated, or names were adjusted slightly. 

This list is not intended to capture all distributed or cogeneration facilities, which are instead represented by generic plants (see below). In general, plant status has been set to align with MBIE’s EDGS generation stack categories for 2023. This allows us to also use the MBIE generation stack for potential future generation assets without double-counting. For example, Kaiwera Downs Stage 1 is included in the base year, but the rest of the build is considered a future technology. This is because Kaiwera Downs was only partially operational by the end of 2023.


[^energy_news]: Energy News: <https://www.energynews.co.nz/>
[^ea_md_generation]: Generation by plant | EA: <https://www.emi.ea.govt.nz/Wholesale/Datasets/Generation/Generation_MD>
[^eeca_plant_list]: The current version of this plant list can be viewed on our github [here](https://github.com/EECA-NZ/TIMES-NZ-Model-Files/blob/main/PREPARE-TIMES-NZ/data_raw/coded_assumptions/electricity_generation/GenerationFleet.csv).
[^ea_dispatch_generationfleet]: Existing Generation Plants | EA: <https://www.emi.ea.govt.nz/Wholesale/Datasets/Generation/GenerationFleet/Existing>
[^edgs_assumptions]: Electricity Demand and Generation Scenarios - Assumptions Data | MBIE: <https://www.mbie.govt.nz/assets/Data-Files/Energy/electricity-demand-generation-scenarios-2024-assumptions.xlsx>

  


## Distributing base year generation using Electricity Authority data

We use the Electricity Authority’s “Generation_MD”[^ea_md_generation] data to find estimates of generation for the current plant list. This bottom-up approach means we can assign known generation to plants, regions, and technologies. This data covers 93%[^93_percent] of total generation for 2023. For the remaining generation, we make some assumptions on the location and technology of distributed generation (cogeneration or otherwise) to calibrate final figures with historical generation and capacity data published by MBIE[^mbie_official_generation]. 

For plants where we include multiple stages, but there is only one reference in the Electricity Authority data (such as Ngāwhā or Turitea), generation is proportionally distributed by the stage’s capacity.

We further test our final base year generation figures against MBIE’s official historical statistics to ensure accuracy. 

[^93_percent]: 40,597 GWh in the EA’s dataset is 93% of the 43,494 GWh reported by MBIE for 2023.
[^mbie_official_generation]: Electricity statistics | Ministry of Business, Innovation & Employment: <https://www.mbie.govt.nz/building-and-energy/energy-and-natural-resources/energy-statistics-and-modelling/energy-statistics/electricity-statistics>


## Capacity factor estimates


In some cases, using generation data from the Electricity Authority is either incomplete or results in implied capacity factors outside normal ranges. This is especially true for some cogeneration plants but could also indicate that our manual asset mapping to Electricity Authority plant definitions was inaccurate.

In these cases, we instead set some plants to have generation estimated by capacity factor. These capacity factor assumptions are used for calibrating the base year and provide upper limits to future generation for these plant types. 

These capacity factor assumptions are either extracted from TIMES-NZ 2.0, or (where these were not available) estimated based on 2023 base year calibration. 



### Dispatchable 

For dispatchable plants, the capacity factor estimate is considered an annual upper bound. However, they are free to generate at different times of year depending on system needs. 

```{csv-table} Dispatchable plant capacity factor assumptions
:header-rows: 1
:name: tab-capacity_factors
Plant Type,Capacity Factor (%)
Biogas,75
Diesel (peakers),2
Huntly Rankine units,37
Natural gas (cogeneration),55
Natural gas (CCGT),65
Natural gas (OCGT),33
```
We note that this is a limitation for CCGT plants, as this method allows them too much flexibility in how quickly they might begin or halt generation. 

### Baseload 

Geothermal and cogeneration plants are considered "baseload". This means that their generation within the model is fixed at every time of year and day according to the below assumptions

```{csv-table} Baseload plant capacity factors
:header-rows: 1
:name: tab_baseload_capacity factors 
Plant Type,Capacity Factor (%)
Biomass (cogeneration),55
Coal (cogeneration),55
Natural gas (cogeneration),55
Natural gas (CCGT),65
Natural gas (OCGT),33
Geothermal (cogeneration),80
Geothermal (electricity),93 
```

These plants will never flex generation up or down depending on demand. 

### Solar 

Solar seasonal generation curves are from TIMES 2.0, and listed separately depending on whether it is distributed or grid scale, and fixed/tracking. Curves are also different per island, as sun patterns are different on each island. 

All solar availability curves are considered fixed, rather than upper bounds. This means solar will always generate at the listed output in the model, and not flex depending on demand. Distributed and grid scale availability factors are listed below.

```{csv-table} Distributed solar availability factors
:header-rows: 1
:name: tab_solar_availability_dist
Season,Day Type,Time of Day,North Island,South Island
Autumn,Weekend,Day,14.5%,13.7%
Autumn,Weekend,Night,0.0%,0.0%
Autumn,Weekend,Peak,0.3%,0.7%
Autumn,Weekday,Day,14.6%,13.3%
Autumn,Weekday,Night,0.0%,0.0%
Autumn,Weekday,Peak,0.3%,0.5%
Spring,Weekend,Day,30.9%,32.4%
Spring,Weekend,Night,0.0%,0.0%
Spring,Weekend,Peak,2.5%,4.9%
Spring,Weekday,Day,31.2%,31.2%
Spring,Weekday,Night,0.0%,0.0%
Spring,Weekday,Peak,2.3%,5.1%
Summer,Weekend,Day,46.9%,44.6%
Summer,Weekend,Night,0.0%,0.0%
Summer,Weekend,Peak,11.7%,13.8%
Summer,Weekday,Day,44.4%,46.5%
Summer,Weekday,Night,0.0%,0.1%
Summer,Weekday,Peak,11.1%,17.2%
Winter,Weekend,Day,8.0%,7.9%
Winter,Weekend,Night,0.0%,0.0%
Winter,Weekend,Peak,0.0%,0.0%
Winter,Weekday,Day,8.2%,7.2%
Winter,Weekday,Night,0.0%,0.0%
Winter,Weekday,Peak,0.0%,0.0%
```


```{csv-table} Utility-scale solar availability factors
:header-rows: 1
:name: tab_solar_availability_utility_fixed
Season,Day Type,Time of Day,North Island,South Island
Autumn,Weekend,Day,19.2%,19.3%
Autumn,Weekend,Night,0.0%,0.0%
Autumn,Weekend,Peak,0.3%,1.9%
Autumn,Weekday,Day,19.9%,19.5%
Autumn,Weekday,Night,0.0%,0.0%
Autumn,Weekday,Peak,0.2%,2.5%
Spring,Weekend,Day,47.3%,43.2%
Spring,Weekend,Night,0.0%,0.0%
Spring,Weekend,Peak,3.2%,14.4%
Spring,Weekday,Day,45.1%,43.4%
Spring,Weekday,Night,0.0%,0.0%
Spring,Weekday,Peak,4.4%,14.1%
Summer,Weekend,Day,68.8%,65.8%
Summer,Weekend,Night,0.1%,0.1%
Summer,Weekend,Peak,19.2%,32.7%
Summer,Weekday,Day,64.3%,66.4%
Summer,Weekday,Night,0.1%,0.1%
Summer,Weekday,Peak,17.2%,35.3%
Winter,Weekend,Day,10.7%,10.0%
Winter,Weekend,Night,0.0%,0.0%
Winter,Weekend,Peak,0.0%,0.0%
Winter,Weekday,Day,10.5%,9.9%
Winter,Weekday,Night,0.0%,0.0%
Winter,Weekday,Peak,0.0%,0.1%
```


### Hydro 
Hydro electricity generation uses a different approach. Here we assume generation follows seasonal patterns, but generation is capable of flexing within these seasonal restrictions. Because average output within a season is fixed, but able to flex within any give timeperiod, the model should, if necessary, lower hydro output when it is not needed. This allows for higher generation at other points in the season while still meeting seasonal constraints. 

```{csv-table} Dispatchable hydro availability assumptions
:header-rows: 1
:name: tab_hydro_availability
Season,North Island,South Island
Sumner,45.3%,60.5%
Autumn,49.6%,56.1%
Winter,38.1%,54.0%
Spring,56.9%,64.0%
```
These figures have been extracted from assumptions used for TIMES 2.0. Note that run-of-river hydro is not afforded the same flexibility within the model.

### Wind 

Onshore wind availability curves are based on analysis of the availability of New Zealand’s wind farms since 2020. These are then scaled up slightly to meet a 38% annual average, as we assume future generation may perform better than existing plants as technology improves. We keep the same generation curves for offshore wind, but scaled up across every timeslice to give an annual availability assumption of 50%. 


```{eval-rst}
.. admonition:: Wind peak modelling
   :class: note

   There is a difference between modelled generation during "peak" timeslices, or the highest-demand hour in every day, and the "peak constraint", which refers to the highest demand in any given year.
   
   In the case of wind, we assume a reasonably high output during peak timeslices, but a lower peak contribution rate. Peak contribution rates are described in more detail in the Technical Parameters section.
```

Currently, we use the same factors for the North and South Islands.

```{csv-table} Wind availability factors
:header-rows: 1
:name: tab_wind_availability
Season,Day Type,Time of Day,Onshore,Offshore
Autumn,Weekend,Day,34.2%,44.9%
Autumn,Weekend,Night,32.6%,42.9%
Autumn,Weekend,Peak,35.8%,47.1%
Autumn,Weekday,Day,33.9%,44.6%
Autumn,Weekday,Night,33.8%,44.5%
Autumn,Weekday,Peak,34.9%,45.9%
Spring,Weekend,Day,43.3%,57.0%
Spring,Weekend,Night,41.1%,54.1%
Spring,Weekend,Peak,43.8%,57.6%
Spring,Weekday,Day,44.6%,58.7%
Spring,Weekday,Night,43.0%,56.5%
Spring,Weekday,Peak,47.2%,62.0%
Summer,Weekend,Day,37.9%,49.9%
Summer,Weekend,Night,35.8%,47.2%
Summer,Weekend,Peak,42.0%,55.3%
Summer,Weekday,Day,36.9%,48.5%
Summer,Weekday,Night,35.8%,47.2%
Summer,Weekday,Peak,39.8%,52.3%
Winter,Weekend,Day,39.2%,51.6%
Winter,Weekend,Night,37.0%,48.7%
Winter,Weekend,Peak,38.2%,50.3%
Winter,Weekday,Day,38.5%,50.6%
Winter,Weekday,Night,38.0%,50.0%
Winter,Weekday,Peak,38.7%,50.9%
```


## Huntly Rankine units

To estimate the split of coal and natural gas at the Huntly Rankine units, we assume the Rankine 2023 generation from coal is equivalent to MBIE figures on total coal electricity generation (i.e. excluding cogeneration), and the remaining share is from natural gas. The resulting figures align with Genesis reporting on Huntly coal use during calendar year 2023[^huntly_coal_use].

```{eval-rst}
.. admonition:: A note on biomass
   :class: note

   In February 2023, Genesis completed a biomass trial at the Rankine units. This means some small proportion of the generation was fuelled by imported wood pellets. These figures are negligible overall, and they are currently not included in the base year model.
```
[^huntly_coal_use]: Calendar values of coal use at the Rankine Units can be found by compiling quarterly report values from <https://www.genesisenergy.co.nz/investor/results-and-reports/reports-and-presentations>

## Distributed solar generation
The Electricity Authority does not provide figures on rooftop solar generation. However, distributed solar capacity data is available. We therefore create generic plant stocks intended to represent different levels of rooftop solar generation (residential, commercial, and industrial), and distribute MBIE’s official solar generation statistics according to region and island based on EMI distributed solar capacity data. 

A stock model is applied to the existing stock of distributed solar generation to estimate the rate at which panels are retired from rooftops across the model horizon. Plants linearly retire according to the technical lifetime assumption for solar plants. 


## Adding generic plants

After adding either Electricity Authority generation data or plant generation estimates based on capacity factors, we calibrate total figures against official MBIE generation data (broken down by cogeneration status and fuel type). We expect to still be missing some generation when comparing to official statistics, which reflects smaller embedded or other plants not available in our plant list or Electricity Authority solar capacity data. 

We therefore add several “generic” existing plants. These have their capacities and generation figures for the base year generated automatically based on the missing generation data and capacity factor assumptions. In cases where they may be on either island (such as wind or hydro), they are distributed according to the known regional distribution of similar plants. In other cases (such as geothermal or natural gas plants) they are distributed only across the North Island. 


## Technical parameters from MBIE data
Any generating asset in the model requires detailed technical parameters. The following are available in the MBIE generation stack for current plants:
1)	Heatrate (or fuel efficiency)
2)	Variable O&M (NZD/MWh)
3)	Fixed O&M (NZD/kW/year)
4)	Fuel delivery costs (NZD/GJ)

In many cases, we can directly map base year generating assets to MBIE plant names to add these parameters. In cases where plants in the TIMES-NZ base year do not have direct equivalents, we take the mean of these parameters for similar plants and apply those instead.

## Technical parameters by assumption
Other required parameters are not included in MBIE’s data, so these are applied by assumption. 

### Peak contribution rate
The peak contribution is the assumed proportion of capacity available to meet peak demand. These peak contribution rate assumptions are as follows: 



```{list-table} Peak contribution assumptions
:header-rows: 1
:name: tab-peak_contribution

* - Plant Type
  - Peak contribution (%)
* - Hydro (dispatchable)
  - 80
* - Hydro run-of-river
  - 72
* - Peakers (all fuels)
  - 97
* - Natural gas (CCGT)
  - 97
* - Wind (onshore)
  - 10
* - Wind (offshore)
  - 25
* - Solar
  - 0
* - Huntly Rankine Units
  - 97
* - Geothermal
  - 92
* - Biogas
  - 66
* - Battery storage
  - 98
* - All other generation
  - 66
```

For intermittent generation, such as wind and solar, peak contribution rates are based on the lower likelihoods of availability during peak hours (winter 6pm-7pm). Onshore wind peak contribution rates are based on the 10th percentile of historical wind availability during peak hours (winter 6pm-7pm). This figure comes to around 10%. Offshore wind peak availability is by assumption, but we expect that offshore wind resource will be more reliable than onshore. We assume solar is not available when it is dark. Dispatchable hydro peak contribution rates are 80%. This accounts for consenting and reserve capacity requirements and the possibility of reduced hydro availability during peak periods.

Other peak contribution rates are assumptions extracted from previous iterations of TIMES-NZ. 

### Plant lifetimes
All generating assets are provided with their original commissioning date where possible. The technical lifetimes are by assumption for each technology type. If a plant reaches the end of its technical lifetime, it is decommissioned in the model. These assumptions have been extracted from TIMES-NZ 2.0.

```{list-table} Plant lifetime assumptions
:header-rows: 1
:name: tab-plant_lifetimes

* - Plant Type
  - Technical lifetime (years)
* - Biogas
  - 30
* - Generic cogeneration
  - 25
* - Diesel (peakers)
  - 30
* - Geothermal
  - 40
* - Hydro
  - N/A
* - Huntly Rankine units
  - 50[^huntly_life]
* - Natural gas 
  - 25
* - Solar (distributed and utility)
  - 20
* - Wind (onshore and offshore)
  - 25 
```

Currently, decommissioning costs are not included. This was also true in TIMES-NZ 2.0. We instead assume that plants always retire at the end of their technical lifetime without incurring decommissioning costs. We also assume hydro plants are maintained through the entire model horizon; hence the technical lifetimes are `N/A`. We assume the cost of turbine replacements are spread across their operating and maintenance costs each year.



[^huntly_life]:The Rankine units were commissioned across 1982-1985, and we have set the commissioning date to 1983. This lifetime assumption means they will be retired in the model in 2033.


