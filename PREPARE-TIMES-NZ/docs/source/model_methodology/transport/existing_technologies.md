# Existing technologies

This section details data and assumptions on technical parameters of existing transport technologies, such as capital costs, efficiency, etc 


## Capital and operating costs 

### Road transport 

Capital (CAPEX) and fixed operating and maintenance (FIXOM) costs for light vehicles in the model are primarily derived from EECA’s Total Cost of Ownership (TCO) Tool[^tco_tool] using a curated list of top-selling models across multiple technology types and vehicle categories. Vehicles are classified by category (e.g. car, SUV, ute, van, bus, motorcycle, truck), use type (e.g. LPV, LCV, bus, motorcycle, light, medium, heavy truck), and technology (e.g. petrol ICE, diesel ICE, hybrid, plug-in hybrid, battery electric vehicle, and hydrogen fuel cell). For each representative model, key cost components are recorded, including purchase price (capital cost), servicing costs, tyre costs, and a combined per-kilometre operating cost. 
Truck costs are sourced from publicly available sales data where possible, as well as aggregated internal EECA data. Dual fuel heavy trucks are determined by the price of the diesel truck plus $150,000 for the dual fuel system[^hydrogen_dual_fuel_costs]. Operating costs were assumed the same as a diesel truck.

If vehicle cost data was not available in the TCO tool, we used proxy figures from the National Renewable Energy Laboratory[^nrel_transport_atb] or the Argonne National Laboratory[^anl]. These costs do not include battery or fuel cell replacements, which may become significant in the cost of these vehicles given we are modelling their entire lifespan. 

```{list-table} Vehicle capital costs (2023 NZD)
:header-rows: 1
:name: tab-vehicle-capital-costs
:class: expandable-table
* - Vehicle Type
  - Diesel
  - Diesel Hybrid
  - Diesel/Hydrogen
  - BEV
  - Hydrogen
  - LPG
  - Petrol
  - Petrol Hybrid
  - PHEV
* - LPV
  -  53,565 
  - 
  - 
  -  48,087 
  -  69,630 
  -  60,836 
  -  37,907 
  -  42,201 
  -  52,065 
* - LCV
  -  56,728 
  -  54,283 
  - 
  -  70,913 
  -  148,676 
  -  70,364 
  -  60,645 
  -  62,141 
  -  75,193 
* - Light Truck
  -  78,244 
  -  89,981 
  - 
  -  126,271 
  -  211,896 
  - 
  - 
  - 
  -  238,692 
* - Medium Truck
  -  175,680 
  -  193,429 
  - 
  -  381,808 
  -  447,231 
  - 
  - 
  - 
  -  364,301 
* - Heavy Truck
  -  344,470 
  -  270,081 
  -  492,100 
  -  677,130 
  -  876,923 
  - 
  - 
  - 
  -  690,526 
* - Bus
  -  393,680 
  -  425,166 
  - 
  -  576,413 
  -  875,939 
  -  393,680 
  -  393,680 
  - 
  -  669,042 
* - Motorcycle
  - 
  - 
  - 
  -  8,110 
  - 
  - 
  -  4,890 
  - 
  - 
```



```{list-table} Vehicle operating and maintenance costs (2023 NZD/km)
:header-rows: 1
:name: tab-vehicle-varom
:class: expandable-table
* - Vehicle Type
  - Diesel
  - Diesel Hybrid
  - Diesel/Hydrogen
  - BEV
  - Hydrogen
  - LPG
  - Petrol
  - Petrol Hybrid
  - PHEV
* - LPV
  - 0.09
  - 
  - 
  - 0.06
  - 0.1
  - 0.16
  - 0.07
  - 0.07
  - 0.08
* - LCV
  - 0.08
  - 0.09
  - 
  - 0.05
  - 0.13
  - 0.15
  - 0.05
  - 0.14
  - 0.1
* - Light Truck
  - 0.14
  - 0.14
  - 
  - 0.09
  - 0.14
  - 
  - 
  - 
  - 0.14
* - Medium Truck
  - 0.18
  - 0.18
  - 
  - 0.11
  - 0.18
  - 
  - 
  - 
  - 0.18
* - Heavy Truck
  - 0.18
  - 0.18
  - 
  - 0.11
  - 0.18
  - 
  - 
  - 
  - 0.18
* - Bus
  - 0.18
  - 0.18
  - 
  - 0.11
  - 0.18
  - 0.85
  - 0.85
  - 
  - 0.18
* - Motorcycle
  - 
  - 
  - 
  - 
  - 
  - 
  - 
  - 
  - 

```

[^tco_tool]: EECA TCO tool: <https://www.eeca.govt.nz/for-businesses/work-vehicles/vehicle-total-cost-of-ownership-calculator/>

[^hydrogen_dual_fuel_costs]: [Southland-based transport company building hydrogen fuel station | Stuff](https://www.stuff.co.nz/southland-times/news/133344057/southlandbased-transport-company-building-hydrogen-fuel-station#:~:text=The%20first%20HWR%20dual%2Dfuel,lighter%20vehicles%20going%20shorter%20distances)

[^nrel_transport_atb]: NREL 2024 Transportation Annual Technology Baseline: <https://atb.nrel.gov/transportation/2024/index>

[^anl]: Argonne National Laboratory | Detailed Simulation Study to Evaluate Future Transportation Decarbonization Potential : <https://anl.app.box.com/s/hv4kufocq3leoijt6v0wht2uddjuiff4>


### Shipping


TIMES-NZ 2.0 did not include the cost of domestic and international shipping. For the 3.0 update we have used CAPEX and OPEX figures used in the Mærsk Mc-Kinney Møller Center TCO tool[^maersk_tco]. TIMES-NZ shipping technologies are based on Heavy fuel oil, so the most relevant category is Vessel 1 - ICE – LSFO (Low Sulfur Fuel Oil).  Little reliable data has been found for alternative technologies.


[^maersk_tco]: Calculate Total Cost of Ownership (TCO) for decarbonization of vessels | Mærsk Mc-Kinney Møller Center for Zero Carbon Shipping: <https://www.zerocarbonshipping.com/publications/calculate-total-cost-of-ownership-tco-for-decarbonization-of-vessels/> (using the `Vessel 1 - ICE – LSFO (Low Sulfur Fuel Oil)` category).


```{list-table} Shipping technology costs
:header-rows: 1
:name: tab-shipping-costs
* - Vessel
  - 2020
  - 2025
  - 2030
  - 2035
  - 2040
  - 2045
  - 2050
* - CAPEX (USD/Vessel)
  - 4,255,140
  - 4,255,140
  - 4,255,140
  - 4,255,140
  - 4,255,140
  - 4,255,140
  - 4,255,140
* - OPEX (USD/vessel/year)
  - 23,169,449
  - 21,576,516
  - 21,187,545
  - 21,187,545
  - 21,187,545
  - 21,187,545
  - 21,187,545
```

### Rail

There is also limited publicly available data for rail costs. Currently, we use data from media releases relating to the Stadler and KiwiRail contract for 57 mainline locomotives[^stadler_press_release]. 


```{list-table} Cost of rail (Million euros)
:header-rows: 1
:name: tab-cost-of-rail
* - Type
  - Fuel type
  - No. of locomotives
  - Contracted amount (million euros)
  - Per unit cost (million euros)
* - Mainline locomotives
  - Low-emission diesel
  - 57
  - 228
  - 4
* - Hybrid yard shunt locomotives
  - Hybrid battery-diesel
  - 24
  - No data publicly available
  - 
```


[^stadler_press_release]:  Stadler and KiwiRail sign a contract for 57 mainline locomotives (11/10/2021): <https://www.stadlerrail.com/api/docs/0ea5972cb4/2021_1011_media-release_kiwirail_en.pdf>


## Fuel efficiency 

Fuel efficiencies for base year technologies were determined based on historical information on actual fuel consumption, from the EEUD and vehicle travel data as described above. This is described in Equation {eq}`vkt_efficiency_eq` and the results are listed in {numref}`tab-fuel-efficiency-tra-existing`. 

```{math}
:label: vkt_efficiency_eq     

Fuel Efficiency = \frac{Billion Vehicle Kilometres Travelled}{PJ Fuel Used}

```

```{list-table} Fuel efficiencies of existing technologies
:header-rows: 1
:name: tab-fuel-efficiency-tra-existing
* - Type
  - Technology
  - Fuel
  - BVkt/PJ
  - L/100km
  - kWh/100km
  - kg/100km
* - LPV
  - ICE
  - Petrol
  - 0.38
  - 7.47
  - 
  - 
* - 
  - ICE
  - Diesel
  - 0.31
  - 8.34
  - 
  - 
* - 
  - ICE
  - LPG
  - 0.06
  - 
  - 
  - 
* - 
  - ICE Hybrid
  - Petrol
  - 0.53
  - 5.34
  - 
  - 
* - 
  - BEV
  - Electricity
  - 1.56
  - 
  - 17.84
  - 
* - 
  - PHEV
  - Petrol
  - 0.53
  - 5.34
  - 
  - 
* - 
  - PHEV
  - Electricity
  - 1.56
  - 
  - 17.84
  - 
* - LCV
  - ICE
  - Petrol
  - 0.26
  - 10.92
  - 
  - 
* - 
  - ICE
  - Diesel
  - 0.27
  - 9.62
  - 
  - 
* - 
  - ICE
  - LPG
  - 0.05
  -
  - 
  - 
* - 
  - ICE Hybrid
  - Petrol
  - 0.36
  - 7.67
  - 
  - 
* - 
  - BEV
  - Electricity
  - 1.19
  - 
  - 23.32
  - 
* - Light Truck
  - ICE
  - Petrol
  - 0.18
  - 15.88
  - 
  - 
* - 
  - ICE
  - Diesel
  - 0.14
  - 18.18
  - 
  - 
* - 
  - BEV
  - Electricity
  - 0.67
  - 
  - 41.53
  - 
* - Medium truck
  - ICE
  - Diesel
  - 0.06
  - 44.77
  - 
  - 
* - 
  - BEV
  - Electricity
  - 0.3
  - 
  - 93.79
  - 
* - 
  - H2R
  - Hydrogen
  - 0.11
  - 
  - 
  - 7.75
* - Heavy truck
  - ICE
  - Diesel
  - 0.05
  - 55.2
  - 
  - 
* - 
  - BEV
  - Electricity
  - 0.2
  - 
  - 141.9
  - 
* - 
  - H2R
  - Hydrogen
  - 0.08
  - 
  - 
  - 10.4
* - Bus
  - ICE
  - Petrol
  - 0.13
  - 22.58
  - 
  - 
* - 
  - ICE
  - Diesel
  - 0.08
  - 33.19
  - 
  - 
* - 
  - ICE
  - LPG
  - 0.02
  -
  - 
  - 
* - 
  - BEV
  - Electricity
  - 0.31
  - 
  - 89.56
  - 
* - Motorcycle
  - ICE
  - Petrol
  - 0.69
  - 4.12
  - 
  - 
* - 
  - BEV
  - Electricity
  - 2.82
  - 
  - 9.85
  - 

```



Some technologies weren’t present in the data so were determined manually – for LCV Hybrids and ICE motorcycles we used the relativity in between ICE LPVs and the LPV version of their respective technology. 

Hydrogen trucks used publicly claimed fuel capacities and range to determine fuel consumption. For Medium trucks the Hyundai Xcient was used[^hyundai_xcient], for Heavy trucks the GBV Semi[^gbv_semi]. 


[^hyundai_xcient]: [Xcient Fuel Cell Hydrogen Truck | Hyundai New Zealand](https://www.hyundai.co.nz/trucks/xcient/fuel-cell#:~:text=Long%20Range,solution%20for%20long%2Ddistance%20operation)

[^gbv_semi]:[TR Group Showcases Hydrogen Truck to Energy Minister](https://www.trgroup.co.nz/news/tr-group-showcases-hydrogen-truck-to-energy-minister-as-government-backs-cleaner-freight-future/)


## Lifetime of transport technologies 



To reflect differences in how vehicles exit the fleet over time, we allocated the total fleet across utilisation bands, referred to as tertiles based on their initial share and their expected survival as vehicles age. Each tertile’s base share is calculated from the overall fleet and adjusted using an age-based decay factor that models the likelihood of a vehicle remaining in the fleet as it gets older. The decay factor ($\alpha$) is defined as:



Equation {eq}`age_based_decay_eq`: Age-based decay factor
```{math}
:label: age_based_decay_eq

\alpha = 1-  (\frac{Age}{Maximum Age})

```

This factor declines from 1 at age 0 to 0 at the maximum observed vehicle age. 

We assume that vehicles which are used more regularly age faster. To allow for faster turnover in higher utilisation tertiles, the decay factor is raised to the power of the tertile index $i$, resulting in the following weighting formula: 


Equation {eq}`tertile_decay_weight_eq`: Utilisation weighting

```{math}
:label: tertile_decay_weight_eq

Weight_i = Base Share_i \cdot \alpha^i

```

These weights are then normalised within each age group to preserve total fleet size while reflecting different survival patterns across tertiles. Using this weighted distribution, the scrappage age is calculated for each vehicle type and tertile. This is defined as the age by which 70% of vehicles in that group have exited the fleet, representing a higher than median estimate of fleet turnover. It reflects differences in how quickly vehicles are typically retired across segments and provides insight into the upper range of vehicle survival patterns.


```{list-table} Scrappage age in years
:header-rows: 1
:name: tab-transport-scrappage-age
* - Category
  - Low
  - Medium
  - High
* - LPV
  - 28.12
  - 27.08
  - 20.77
* - LCV
  - 20.19
  - 18.37
  - 12.51
* - Bus
  - 37.5
  - 20.72
  - 16.05
* - Motorcycle
  - 22.48
  - 19.87
  - 18.23
* - Light Truck
  - 38.53
  - 34
  - 29.39
* - Medium Truck
  - 39.32
  - 23.86
  - 21.18
* - Heavy Truck
  - 39.32
  - 23.86
  - 21.18
```

## Fuel share constraints

We apply a few constraint assumptions to some dual-fuel technologies, exogenously limiting their fuel shares to provide more realistic fuel share modelling. The model doesn't capture all the practical considerations faced by these technologies, so these constraints are required to enforce realistic modelled behaviour. These assumptions have been extracted from TIMES-NZ 2.0.


```{list-table} Fuel share constraints
:header-rows: 1
:name: tab-fuel-share-constraints
* - Type
  - Technology
  - Fuel
  - Fuel share
* - LPV
  - PHEV
  - Petrol
  - 40%
* - 
  - PHEV
  - Electricity
  - 60%
* - Heavy Truck
  - Dual Fuel
  - Diesel
  - 70%
* - 
  - Dual Fuel
  - Hydrogen
  - 30%
* - Passenger Rail
  - 
  - Electricity
  - 79%
* - 
  - 
  - Diesel
  - 21%
* - Freight Rail
  - 
  - Diesel
  - 97%
* - 
  - 
  - Electricity
  - 3%
```


## Emission factors 

Emissions factors for each thermal fuel are sourced from the Ministry for the Environment’s Measuring Emissions Guide 2025[^meg]. These are all converted to kt CO2e/PJ equivalents using gross calorific values from MfE’s data for use in modelling. The electricity supply portion of the model will handle the electricity emission factor for transport electricity. The following figures are used in the model: 


```{list-table} Transport fuel emission factors
:header-rows: 1
:name: insert-table-name-here
* - Fuel
  - Unit
  - CV MJ/Unit
  - kg CO2e/unit
  - kt CO2e/PJ
* - Petrol
  - Litre
  - 35.18
  - 2.42
  - 68.79
* - Diesel
  - Litre
  - 38.49
  - 2.68
  - 69.63
* - Fuel oil
  - Litre
  - 40.74
  - 3.07
  - 75.36
* - Aviation fuel
  - Litre
  - 37.19
  - 2.52
  - 67.76
* - LPG
  - Litre
  - 26.54
  - 1.62
  - 61.04
```


[^meg]: MfE’s Measuring Emissions Guide 2025: <https://environment.govt.nz/publications/measuring-emissions-guide-2025/>