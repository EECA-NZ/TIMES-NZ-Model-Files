# Technology parameters

## Equipment lifetimes

Equipment lifetimes are taken as estimated useful life (years) from the Inland Revenues General depreciation rates October 2024 document[^ird]. Table 7 includes the IRD proxies considered to estimate lifetime of each technology. Where not available, data are taken from industry sources/knowledge[^lighting_industry_knowledge]. 


```{csv-table} Equipment lifetime by technology
:header-rows: 1
:name: tab_com_equipment_lifetimes

Technologies,Lifetime (Years),IRD Proxies
Electronics and Other Appliances,4,RESD - Appliances (small)
Lights (Incandescent) ,1,N/A
Lights (Fluorescent) ,3,N/A
Lights (LED),10,N/A
Boiler,25,BOIL - Boilers
Burner (Direct Heat),12.5,BOIL – Space heaters
Direct Heat,12.5,BOIL – Space heaters
Heat Pump,10,RESD - Air conditioners and heat pumps/ Water heaters (heat pump type)
Resistance Heater,10,RESD - Air conditioners and heat pumps/ Water heaters (heat pump type)
Hot Water Cylinder,15.5,RESD - Water heaters (other)
Internal Combustion Engine (Land Transport),20,TRAN - Forklift trucks (8 tonnes and over
Stationary Engine - Electricity,10,BDFO - Motors
Stationary Engine - Petrol,20,POWR - Generators (oil fired)
Refrigerator,8,MEDI - Refrigerators
Cooking Element,12.5,HOTS - Cookers
Oven,20,BAKE - Ovens (built-in)
```

[^ird]: Inland Revenue | [General depreciation rates August 2024](https://www.ird.govt.nz/-/media/project/ir/home/documents/forms-and-guides/ir200---ir299/ir265/ir265-august-2024.pdf?modified=20240918025046&modified=20240918025046)
[^lighting_industry_knowledge]: An incandescent bulb typically last around 2,000 hours, a  fluorescent lamp around 10,000 hours, and an LED lamp around 30,000 hours [Choosing a lamp and how you can save money on energy efficiency](https://www.level.org.nz/energy/lighting-design/lamp-selection/), [How to buy LED bulbs - Consumer NZ](https://www.consumer.org.nz/articles/led-bulb-buying-guide)

## Availability factors (AF)

Availability factors were estimated separately for each commercial subsector in TIMES-NZ 2.0. The calculation was based on the underlying load curves prior to normalisation (i.e., before scaling so that all time-slice fractions sum to 1.0). This ensures that the availability factors reflect the absolute intensity and timing of energy use rather than just the relative distribution. For most end-uses, it was assumed that technologies operate concurrently during business operating hours and thus follow the sectoral load curve. Exceptions were introduced for end-uses with different utilisation patterns: space heating and cooling were scaled down to reflect their seasonal operation, while mobile motive power (e.g., equipment used intermittently) was assigned a lower availability factor than the primary continuously operated technologies. 

{numref}`tab_com_availability_factors` lists the assumed number of average active hours per day. These are converted into availability factors for the model (eg 2.4 active hours implies a 10% availability factor).


```{csv-table} Commercial technology availability factors
:header-rows: 1
:name: tab_com_availability_factors

Technology,Education,Healthcare,Office Blocks,WSR,Other
Cooking,5.3,11,10.8,11.5,13.2
Process Heat,5.3,11,10.8,11.5,13.2
Electronics,5.3,11,10.8,11.5,13.2
Lighting,5.3,11,10.8,11.5,13.2
Space Heating,2.4,2.4,2.4,2.4,2.4
Water Heating,5.3,11,10.8,11.5,13.2
Internal Combustion Engine (Land Transport),1.2,1.2,2.4,11.5,2.4
Stationary Engine,5.3,11,10.8,11.5,13.2
Refrigeration,5.3,11,10.8,11.5,13.2
Space Cooling,2.6,5.5,5.3,5.8,6.5
```

## Energy efficiency 

A full list of energy efficiency assumptions can be found in {numref}`tab_com_efficiency`. Energy efficiencies of most technologies came from the TIMES-NZ 2.0 model. Efficiencies for internal combustion engine (land transport)[^ice_efficiency], stationary engines[^stationary_engine_efficiency], and cooking ovens[^oven_efficiency] were updated using literature reviews.

[^ice_efficiency]: [Estimation of tank-to-wheel efficiency functions based on type approval data](https://www.researchgate.net/publication/343138786_Estimation_of_tank-to-wheel_efficiency_functions_based_on_type_approval_data), [Comparison of the Overall Energy Efficiency for Internal Combustion Engine Vehicles and Electric Vehicles](https://www.researchgate.net/publication/350712005_Comparison_of_the_Overall_Energy_Efficiency_for_Internal_Combustion_Engine_Vehicles_and_Electric_Vehicles)

[^stationary_engine_efficiency]: GNS | [Technology scan of electric motors applications](https://www.eeca.govt.nz/assets/EECA-Resources/Research-papers-guides/Technology-Scan-of-Electric-Motor-Applications_EECA.pdf)

[^oven_efficiency]: Energy Star | [Commercial Oven Key Product Criteria](https://www.energystar.gov/products/commercial_food_service_equipment/commercial_ovens/key_product_criteria)



```{csv-table} Energy efficiency by technology
:header-rows: 1
:name: tab_com_efficiency

Technology,Fuel,Energy Efficiency %
Boiler Systems,Coal,75%
Boiler Systems,Diesel,85%
Boiler Systems,LPG,85%
Boiler Systems,Natural Gas,85%
Burner (Direct Heat),Coal,77%
Burner (Direct Heat),LPG,80%
Burner (Direct Heat),Natural Gas,80%
Heat Pump Air Source,Electricity,350%
Heat Pump (Water Heating),Electricity,250%
Resistance Heater,Electricity,99%
Direct Heat,Geothermal,100%
Hot Water Cylinder,Electricity,90%
Hot Water Cylinder,Natural Gas,60%
Incandescent Lamp,Electricity,2%
Fluorescent Lamp,Electricity,14%
LED Lamp,Electricity,25%
Internal Combustion Engine (Land Transport),Diesel,20%
Internal Combustion Engine (Land Transport),LPG,12%
Internal Combustion Engine (Land Transport),Petrol,20%
Stationary Engine,Electricity,90%
Stationary Engine,Petrol,14%
Refrigerator,Electricity,180%
Electronics,Electricity,90%
Cooking Elements,Electricity,74%
Cooking Ovens,Electricity,76%
Cooking Ovens,LPG,49%
Cooking Ovens,Natural Gas,49%
```

## Capital costs

A full list of capital cost assumptions can be found in {numref}`tab_com_capex` below. These capital costs represent the upfront expenditure required to install each technology in a typical New Zealand commercial building context. Costs are expressed in NZD per kW of installed capacity and include both the equipment and standard installation. For example, capital cost of a gas boiler reflects the unit cost plus typical installation labour and materials. Operating costs (fuel, maintenance, servicing) are not included.

The sources for these estimates include EECA research and case studies, government datasets, and New Zealand supplier price lists. For example, EECA’s industrial decarbonisation reports and hot water heat pump guidance[^hwhp_capex]<sup>,</sup>[^hp_for_processheat] provide comparative project costs, the New Zealand Geothermal Association provides costs of the geothermal direct heat for delivered energy[^nzga_heat_costs], and retail suppliers[^retail_supplier_capex] provide market-based prices for appliances and smaller equipment. 

Cost values are adjusted to 2023 New Zealand dollars using the most appropriate price index (CPI or CGPI).

[^hwhp_capex]: [EECA | Hot water heat pumps in commercial buildings](https://www.eeca.govt.nz/insights/eeca-insights/hot-water-heat-pumps-in-commercial-buildings/#:~:text=Capital%20cost)

[^hp_for_processheat]: [EECA | Heatpumps for process heat](https://www.eeca.govt.nz/insights/eeca-insights/industrial-heat-pumps-for-process-heat)

[^nzga_heat_costs]: [NZGA | Action Plan 2024-2025](https://www.nzgeothermal.org.nz/downloads/2024-2025-Geoheat-Action-Plan.pdf)

[^retail_supplier_capex]: Various prices pulled from retail sites, including: [Kiwi heat pumps](https://kiwiheatpumps.co.nz/compare-heat-pump-prices/), [Hot water cylinders](https://hotwatercylinders.nz/), [Mitre 10](https://www.mitre10.co.nz/shop/heating-cooling/heating/electrical-heating/c/RS2059?inStockNationwide=false&inStockSelectedStore=false&sort=RELEVANCY), [Bunnings](https://www.bunnings.co.nz/), and [OMC Power Equipment](https://www.omcpowerequipment.co.nz/replacement-engines)


```{csv-table} Capital costs by technology 
:header-rows: 1
:name: tab_com_capex
Technology,Fuel,Capital cost (NZD/kW)
Boiler Systems,Coal,"1,654"
Boiler Systems,Diesel,628
Boiler Systems,LPG,712
Boiler Systems,Natural Gas,513
Burner (Direct Heat),Coal,"1,382"
Burner (Direct Heat),LPG,691
Burner (Direct Heat),Natural Gas,691
Heat Pump Air Source,Electricity,712
Heat Pump (Water Heating),Electricity,712
Resistance Heater,Electricity,141
Direct Heat,Geothermal,150
Hot Water Cylinder,Electricity,931
Hot Water Cylinder,Natural Gas,307
Incandescent Lamp,Electricity,15
Fluorescent Lamp,Electricity,112
LED Lamp,Electricity,500
Internal Combustion Engine (Land Transport),Diesel,700
Internal Combustion Engine (Land Transport),LPG,700
Internal Combustion Engine (Land Transport),Petrol,700
Electric Motor,Electricity,280
Stationary Engine,Petrol,559
Refrigerator,Electricity,"4,028"
Electronics,Electricity,900
Cooking Elements,Electricity,283
Cooking Ovens,Electricity,283
Cooking Ovens,LPG,262
Cooking Ovens,Natural Gas,262
```

Some distinction between the costs of technologies were added, to represent the fact that some subsectors will pay significantly more than others for the same technology, due to their requirements or scale. For example, previous EECA projects have found that a school will pay 5-10x more per kW for their heating or lighting CAPEX than an equivalent office building. This is primarily due to the scaling of these organisations, schools are likely to span many small buildings over a relatively large area, each only needing a relatively small amount of heating. Office blocks can take advantage of their higher density, giving a more centralised area to heat, and a larger, more cost-effective heating option can be purchased.

## Operating and maintenance costs

Operating and maintenance costs assumptions for some technologies can be found in {numref}`tab_com_opex`. These have been extracted from the TIMES-NZ 2.0 model. Technologies not listed here are assumed to have 0 additional operating or maintenance costs.


```{csv-table} Operating and maintenance costs
:header-rows: 1
:name: tab_com_opex

Technology,Fuel,O&M cost (NZD/kW/year)
Boiler Systems,Coal,15
Boiler Systems,Diesel,3
Boiler Systems,LPG,2
Boiler Systems,Natural Gas,2
Internal Combustion Engine (Land Transport),Diesel,7
Internal Combustion Engine (Land Transport),LPG,7
Internal Combustion Engine (Land Transport),Petrol,7
Stationary Engine,Petrol,5
Refrigerator,Electricity,5
```

## Fuel market share constraints

Market shares for technologies and fuels for each demand of each sub-sector were added in the TIMES-NZ 2.0 model to avoid near complete uptake of technologies at an unrealistic rate. As TIMES-NZ is a least-cost model, when not limited it was immediately replacing the bulk of its technologies with whichever was cheapest, resulting in a near complete uptake of electrification from 2020 onwards.

The base year of 2023 was estimated using the EEUD, with 2030 and 2050 projections being made based upon assumptions of the TIMES-NZ team. For example, the EEUD has only 1% of school heating demand being met by heat pumps. While we see this as a definite growth area, we don’t expect 100% uptake by 2030, so we have limited this to 50%. By 2050, we have raised this to 70%, allowing the remainder to be supplied by resistance heaters and gas or biomass boilers.

Please note these are maximum bounds, i.e. they are the maximum that one fuel/technology combination can provide output, so numbers in 2030 and 2050 may sum to over 100%. This gives the model room to choose preferred technologies, but limited at a realistic rate, without prescribing the total of each fuel/technology.


## Emission factors

Emissions factors for each thermal fuel are sourced from the Ministry for the Environment’s Measuring Emissions Guide 2025[^mfe_meg]. These are all converted to kt CO2e/PJ equivalents using gross calorific values from MfE’s data for use in modelling. The electricity supply portion of the model will handle the electricity emission factor for commercial electricity. The following figures are used in the model: 

[^mfe_meg]: MfE | [Measuring Emissions Guide 2025](https://environment.govt.nz/publications/measuring-emissions-guide-2025/ )

```{csv-table} Thermal fuel emission factors
:header-rows: 1
:name: tab_com_efs

Fuel,Unit,CV MJ/Unit,kg CO2e/unit,kt CO2e/PJ
Coal,kg,25.62,2.11,82.37
Natural Gas,GJ,,54.1,54.1
Petrol,Litre,35.18,2.41,68.79
Diesel,Litre,38.49,2.68,69.63
LPG,kg,50,2.97,59.32
```


