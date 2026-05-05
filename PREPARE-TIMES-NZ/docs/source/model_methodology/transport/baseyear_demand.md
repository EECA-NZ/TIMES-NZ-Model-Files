# Base year demand 

The base year vehicle data is intended to reflect the distribution of 2023 transport demand across the total vehicle fleet in New Zealand. These vehicles should be available to the model to meet future demand, but with enough information (region, technology, remaining life, etc.) that the model will retire vehicles at appropriate points and can make least-cost decisions on fleet replacement, fuel switching, and utilisation across demand segments.

TIMES-NZ requires detailed information on the existing vehicle stock, including: 

 - Billion vehicle kilometres travelled (Bvkt)
 - Vehicle stock (000vehicles)
 - Fuel efficiency (Bvkt/PJ)
 - Vehicle max annual travel distance (000km)
 - Annual utilisation rate (%)
 - Investment costs (000NZD/vehicle)
 - Operation and maintenance costs (000NZD/vehicle)
 - Mode or fuel share
 - Region (North Island/South Island)
 - Vehicle lifetime
 - Fuel use split of dual-fuel vehicles (i.e. PHEVs, Hydrogen dual-fuel)

We have improved on TIMES-NZ 2.0 by further disaggregating vehicles into differing levels of utilisation, giving greater representation of vehicle uses. This allows the model to make more nuanced least-cost decisions based on expected vehicle usage rates. 

## Existing transport asset data

EECA has compiled a dataset of current transport technologies and fleet composition for the 2023 base year, reflecting the distribution of energy service demand across the New Zealand vehicle fleet. This dataset is grounded in data from the Ministry of Transport (MoT)’s Vehicle Fleet Model (VFM)[^mot_vfem], MoT’s Annual Fleet Statistics[^mot_fleet_data], and other reputable data sources, including KiwiRail[^kiwirail_data] and the Ministry of Business, Innovation and Employment (MBIE) Energy Balances[^mbie_balances]. 


[^mot_vfem]: MoT: Vehicle Fleet Model/File: “VFM202405 outputs summary V3”: <https://www.transport.govt.nz/statistics-and-insights/vehicle-fleet-model/sheet/updated-future-state-model-results>
[^mot_fleet_data]: MoT: Vehicle Fleet Statistics/file: “2023 New Zealand Annual Vehicle Fleet Statistics”: <https://www.transport.govt.nz/statistics-and-insights/fleet-statistics>
[^kiwirail_data]: KiwiRail Personal Communication with Energy Efficiency and Conservation Authority (EECA)
[^mbie_balances]: MBIE: Energy Balances/file: “Energy Balance Tables | Calendar year 1990-2023”: <https://www.mbie.govt.nz/building-and-energy/energy-and-natural-resources/energy-statistics-and-modelling/energy-statistics/energy-balances/>


The dataset includes detailed vehicle stock, Bvkt, fuel use(litres), kWh use, and energy consumption (PJ) by a combination of vehicle type (i.e. light passenger vehicles (LPV), light commercial vehicles (LCV), trucks, buses, motorcycles, rail, aviation, shipping), technology type (i.e. Internal Combustion Engine (ICE), BEV, Plug-In Hybrid Electric Vehicle (PHEV), Fuel Cell (FC) and fuel type (i.e. petrol, diesel, electric).

```{list-table} Vehicle type, demand drivers and sources
:header-rows: 1
:name: tab-tra_vehicle_drivers_sources
* - Vehicle Type
  - Description
  - Demand Driver
  - Data Sources
* - Light Passenger Vehicles 
  - Cars and SUVs less than 3.5 tonnes gross vehicle mass (GVM)
  - Bvkt
  - MoT Annual Fleet Statistics
* - Light Commercial Vehicles 
  - Vans and Utilities less than 3.5 tonnes GVM 
  - 
  - 
* - Light trucks
  - Goods vehicles between 3.5 and 10 tonnes GVM
  - 
  - 
* - Medium Trucks 
  - Trucks between 10 and to 30 tonnes GVM 
  - 
  - 
* - Heavy Trucks 
  - Long haul trucks greater than 30 tonnes GVM 
  - 
  - 
* - Buses 
  - Passenger vehicles over 3.5 tonnes GVM 
  - 
  - 
* - Motorcycles 
  -  Motor vehicles with 2-3 wheels
  - 
  - 
* - Rail: Passenger 
  -  Rail vehicles used for the transport of passengers
  - PJ
  - KiwiRail
* - Rail: Freight 
  -  Rail vehicles used for the transport of freight
  - 
  - 
* - Aviation: Domestic 
  - Internal NZ air passenger transport 
  - PAX/PJ
  - MBIE Energy Balances
* - Aviation: International 
  - NZ residents travel and overseas visitors 
  - 
  - 
* - Coastal Shipping: Domestic 
  - Traffic between NZ ports 
  - PJ
  - MBIE Energy Balances
* - Coastal Shipping: International 
  - Bunkers for ships travelling overseas 
  - 
  - 
```



The transport asset list does not aim to capture every variation or niche vehicle type (such as rare fuel types or specific commercial variants). Instead, these are represented by technology-averaged or generic categories within the model to maintain modelling tractability. In cases where only pilot deployment occurred by the base year (i.e., early-stage electric truck deployments or pilot hydrogen buses), these have not been included due to their low numbers. 

In this 3.0 release we have added another category of trucks, aiming to represent the high utilisation long haul vehicles in the fleet. The split point has been set at 30t GVM to capture just the heaviest vehicles. It should be noted that in 2.0 we used the terms Medium Trucks and Heavy Trucks, but to align with industry terminology we have added a Light Trucks category and moved the vehicles weights accordingly, rather than adding a ‘Very Heavy’ category.


## Regional demand disaggregation

The division of energy service demand between the North and South Islands is determined using a mix of proxies:

**Road Transport:** MoT Regional VKT data[^mot_regional_vkt] is used as the basis for calculating the split. The detailed data showing VKT based on region and vehicle type are not publicly available

**Rail - Freight:** Assumes all electricity is consumed in Auckland and Wellington, and diesel is split as per rail freight tonnages in MoT freight inter-regional flows[^mot_figs].

**Rail - Passenger:** Assumes all electricity is consumed in Auckland and Wellington, and diesel is split as per freight (has an immaterial impact on overall outcomes).

**Aviation - Domestic:** MoT Arrival/Departures by Airport (2017/2018 data) used as proxy for fuel consumption in the absence of detailed trip length data[^aviation_island_assumptions].

**Aviation - International:** Statistics NZ international arrival data and MoT International Arrivals/Departures data are used to estimate the fuel consumed by the airport[^aviation_island_assumptions].

**Shipping:** These are currently based on original assumptions made for TIMES-NZ 2.0[^mbie_domestic_shipping]. 


[^mot_figs]: MoT FIGS: Rail: <https://www.transport.govt.nz/statistics-and-insights/freight-and-logistics/figs-rail/>
[^mot_regional_vkt]: MoT: Vehicle Fleet Statistics/file: “2023 New Zealand Annual Vehicle Fleet Statistics”: <https://www.transport.govt.nz/statistics-and-insights/fleet-statistics>
[^aviation_island_assumptions]: These assumptions on aviation demand shares per island were extracted from TIMES-NZ 2.0.
[^mbie_domestic_shipping]: MBIE has indicated that Domestic Shipping has shifted to Diesel use in the recent years prior to publishing, but they are unable to quantify volumes due to data limitations, so continue to publish Domestic Shipping energy use as Fuel Oil only. TIMES-NZ has used MBIE figures, but should this change in future, the model will be updated to match.


```{list-table} Transport demand shares by island
:header-rows: 1
:name: tab-transport_island_demand_shares
* - Category
  - Fuel
  - North Island %
  - South Island %
* - Road Transport
  - All
  - 73%
  - 27%
* - Rail Freight
  - Diesel
  - 74%
  - 26%
* - 
  - Electricity
  - 100%
  - 0%
* - Rail Passenger
  - Diesel
  - 74%
  - 26%
* - 
  - Electricity
  - 100%
  - 0%
* - Aviation Domestic
  - Av.Fuel/Kero
  - 58%
  - 42%
* - Aviation International
  - Av.Fuel/Kero
  - 80%
  - 20%
* - Shipping Domestic
  - Fuel Oil
  - 34%
  - 66%
* - Shipping International
  - Fuel Oil
  - 72%
  - 28%
```

## Distributing the base year transport demand 


We used MOT’s Annual Fleet Statistics and New Zealand Transport Agency’s (NZTA) Motor Vehicle Register (MVR)[^mvr] to estimate vehicle stock, Bvkt, and regional Bvkt for the 2023 base year. This bottom-up approach allows us to distribute existing transport demand across vehicle types, technologies, fuel types, and regions (North and South Islands). 

This dataset covers the majority of New Zealand's on-road transport energy demand. For categories where data is more limited (e.g., non-road modes like shipping, aviation, rail, or emerging technologies such as hydrogen trucks), assumptions are made based on the best available data from MBIE Energy Balances, KiwiRail, and Energy End Use Database (EEUD)[^eeud_2023]. These assumptions allow us to calibrate total fuel use and transport activity to align with the official historical energy demand reported by the MBIE.

In cases where the MOT provides vehicle categories in aggregated form, we disaggregate VKT, and vehicle counts by fuel type or technology class using market share estimates and registration data from the MVR data. Further disaggregation of VKT into utilisation tertiles (discussed below) was undertaken using extra VKT data provided by MoT for the purpose of improving the model.


[^mvr]: The Motor Vehicle Register, NZ Transport Agency Waka Kotahi. Personal Communication with Energy Efficiency and Conservation Authority (EECA)

[^eeud_2023]: EECA: Energy End Use Database/File: “EEUD Data 2017-2023”: <https://www.eeca.govt.nz/insights/data-tools/energy-end-use-database/>

## Utilisation bands 

The modelled energy system makes least-cost decisions on vehicle purchase decisions. Because different vehicle options can have large differences in capital and operating costs, the utilisation rate - or how often a vehicle is driven in any given year - can have a significant impact on the Total Cost of Ownership and appropriate least-cost decision. 

To better reflect the real-world distribution of vehicle utilisation, we split all categories into utilisation bands. For each vehicle class, vehicle counts are evenly split into low, medium, and high utilisation tertiles, where each tertile represents exactly 33% of the vehicle fleet. Each tertile of each vehicle class is given a conditional mean VKT using data provided by MoT. 

```{list-table} Annual VKT per vehicle utilisation band (km)
:header-rows: 1
:name: tab-tra_util_band_data
* - Category 
  - Low
  - Medium
  - High
* - LPV
  -  3,557 
  -  8,597 
  -  17,490 
* - LCV
  -  5,361 
  -  12,372 
  -  23,507 
* - Light Truck
  -  1,995 
  -  6,839 
  -  19,662 
* - Medium Truck
  -  3,855 
  -  12,047 
  -  31,805 
* - Heavy Truck
  -  17,549 
  -  44,548 
  -  74,246 
* - Bus
  -  7,637 
  -  21,384 
  -  47,349 
* - Motorcycle
  -  288 
  -  1,095 
  -  4,382 
```

Note that utilisation in TIMES-NZ is always expressed as an "availability factor", or share of maximum possible utilisation in a year. We currently set this figure to 80,000km per vehicle, so the above utilisation bands are defined internally as fractions of 80,000km. If necessary, it's possible to express utilisation factors higher than 100%, representing vehicles travelling further than 80,000km per year.

2023 availability factors are based on empirical data on fleet counts and travel distance. This means they can differ within use groups: for example, diesel light passenger vehicles currently have higher utilisation than overall light passenger vehicles. However, when modelling future years, we assume that all technologies within a usage group have the same utilisation factor applied. This ensures that technology choices within use groups are based on like-for-like comparisons. However, it implicitly assumes small changes in driving behaviour for some vehicle classes. To manage this tradeoff between ensuring clear model investment choices and aligning with empirical data, we do not allow any step changes in availability. Instead, availability factors gradually transition from empirical levels to standardised model levels over the first ten years of the model horizon.


Please note that these values are averaged over the life of the vehicle. New vehicles (particularly trucks) do travel greater distances while new, which is then balanced by the lower distances they travel later in life. For technologies in early deployment (e.g., BEVs and FCEVs), VKT is proportionally allocated using known fleet counts from MVR and technology-specific energy use per kilometre assumptions (e.g., kWh/km or MJ/km). 

Non-road modes (aviation, rail, shipping) are incorporated using available MBIE and KiwiRail data, and do not include utilisation bands: 
 - MBIE Energy Balances[^mbie_balances] (for domestic/international aviation in PAX or PJ and shipping in PJ)
 - KiwiRail[^kiwirail_data] (for rail passenger and freight demand)



## Battery electric freight productivity penalty 

To represent the need for Heavy trucks to carry large payloads, we have applied a productivity penalty to BEV trucks due to the weight of their batteries. This is applied as a decrease in VKT per vehicle, resulting in the model needing to purchase more BEV trucks to do the same job as diesel or hydrogen. 

The weight difference was determined by removing the estimated weight of the powertrain and replacing these with the weight of an EV drivetrain and battery. Power train weights were sourced from ICCT[^icct_power_train_weights]. Base year battery weights used 160Wh/kg (current day estimates), moving to 400Wh/kg in 2040[^idtechex_400]. This results in a 13% penalty in 2023, gradually reducing to 3% in 2040.

Hydrogen trucks were assumed to be the same weight as their ICE counterparts. 


[^icct_power_train_weights]: TOTAL COST OF OWNERSHIP OF ALTERNATIVE POWERTRAIN TECHNOLOGIES FOR CLASS 8 LONG-HAUL TRUCKS IN THE UNITED STATES <tco-alt-powertrain-long-haul-trucks-us-apr23.pdf>

[^idtechex_400]: This 400Wh/kg figure is from IDTechEX as their 2030 ‘state of the art’ density. We allow model vehicle batteries to linearly approach this density by 2040, conservatively reflecting the delay in operationalising the technology.
