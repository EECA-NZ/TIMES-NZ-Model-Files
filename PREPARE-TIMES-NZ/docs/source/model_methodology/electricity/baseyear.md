# Base year generation
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

## Distributing base year generation using Electricity Authority data

We use the Electricity Authority’s “Generation_MD”[^ea_md_generation] data to find estimates of generation for the current plant list. This bottom-up approach means we can assign known generation to plants, regions, and technologies. This data covers 93%[^eeca_plant_list] of total generation for 2023. For the remaining generation, we make some assumptions on the location and technology of distributed generation (cogeneration or otherwise) to calibrate final figures with historical generation and capacity data published by MBIE[^mbie_official_generation]. 

For plants where we include multiple stages, but there is only one reference in the Electricity Authority data (such as Ngāwhā or Turitea), generation is proportionally distributed by the stage’s capacity.

We further test our final base year generation figures against MBIE’s official historical statistics to ensure accuracy. 


## Capacity factor estimates


In some cases, using generation data from the Electricity Authority is either incomplete or results in implied capacity factors outside normal ranges. This is especially true for some cogeneration plants but could also indicate that our manual asset mapping to Electricity Authority plant definitions was inaccurate.

In these cases, we instead set some plants to have generation estimated by capacity factor. These capacity factor assumptions are used for calibrating the base year and provide upper limits to future generation for these plant types. 

These capacity factor assumptions are either extracted from TIMES-NZ 2.0, or (where these were not available) estimated based on 2023 base year calibration. 
Annual capacity factors for wind, solar, and hydro are not used in the model. Instead, the model uses availability curves, which dictate availability for these intermittent technologies as a function of the time of year or day. 
 

```{list-table} Capacity factor assumptions
:header-rows: 1
:label: tab-capacity_factors
* - Plant Type
  - Capacity Factor (%)
* - Biogas
  - 75
* - Biomass (cogeneration)
  - 55
* - Coal (cogeneration)
  - 55
* - Diesel (peakers)
  - 2
* - Geothermal (cogeneration)
  - 80
* - Geothermal (electricity)[^geothermal_availability]
  - 93
* - Hydro
  - Varies (47.4 - 58.6)
* - Huntly Rankine units
  - 37
* - Natural gas (cogeneration)
  - 55
* - Natural gas (CCGT)
  - 65
* - Natural gas (OCGT)
  - 33
* - Solar
  - Varies (11.5 - 19.3)
* - Wind (onshore)
  - Varies (35.3 – 39.0)
* - Wind (offshore)
  - Varies (50 - 58)

```




## Availability curves
Solar, wind, and hydro electricity generation is subject to seasonal or daily variation. In TIMES-NZ, we can limit the availability of specific plants during specific periods. For example, solar availability is zero during night periods and varies seasonally during day and peak periods. Onshore wind availability curves are based on analysis of the availability of New Zealand’s wind farms since 2020[^onshore_wind_availability]. 

Offshore wind availability, for potential future installation, is based on similar seasonal patterns to onshore wind, but with an assumed increase to availability. Availability curves for hydro generation have been extracted from modelling done for TIMES-NZ 2.0. 
Full availability curves for these technologies are available in the attached file `Availability Curves.xlsx`.[^MISSING_AV_CURVES]


## Huntly Rankine units

To estimate the split of coal and natural gas at the Huntly Rankine units, we assume the Rankine 2023 generation from coal is equivalent to MBIE figures on total coal electricity generation (i.e. excluding cogeneration), and the remaining share is from natural gas. The resulting figures align with Genesis reporting on Huntly coal use during calendar year 2023[^huntly_coal_use].

```{eval-rst}
.. admonition:: A note on biomass
   :class: note

   In February 2023, Genesis completed a biomass trial at the Rankine units. This means some small proportion of the generation was fuelled by imported wood pellets. These figures are negligible overall, and they are currently not included in the base year model.
```

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
:widths: auto
:label: tab-peak_contribution

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
:widths: auto
:label: tab-plant_lifetimes

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



[^eeca_plant_list]: TODO
[^ea_dispatch_generationfleet]: TODO
[^edgs_assumptions]: TODO
[^edgs_assumptions]: TODO
[^ea_md_generation]: TODO
[^mbie_official_generation]: Electricity statistics | Ministry of Business, Innovation & Employment: <https://www.mbie.govt.nz/building-and-energy/energy-and-natural-resources/energy-statistics-and-modelling/energy-statistics/electricity-statistics>

[^huntly_coal_use]: Calendar values of coal use at the Rankine Units can be found by compiling quarterly report values from <https://www.genesisenergy.co.nz/investor/results-and-reports/reports-and-presentations>
[^onshore_wind_availability]: Note that we have manually increased onshore wind farm availability slightly from historical levels. We assume new windfarms are likely to use more efficient technology and therefore achieve higher capacity factors than existing stock. 
[^energy_news]: Energy News: [https://www.energynews.co.nz/](https://www.energynews.co.nz/)
[^geothermal_availability]: Geothermal capacity factors are set to remain at 93% across all time slices, rather than on average over a year. For all other plants without availability curve settings, the listed factors are annual limits, so these factors may be exceeded during specific time periods. 
[^huntly_life]:The Rankine units were commissioned across 1982-1985, and we have set the commissioning date to 1983. This lifetime assumption means they will be retired in 2033.