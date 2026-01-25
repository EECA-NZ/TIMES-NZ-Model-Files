# Technology parameters

## Equipment lifetimes 

Equipment lifetimes are taken as estimated useful life (years) from the Inland Revenues General depreciation rates October 2024 document[^ird_deprates].  
{numref}`tab_agr_lifetimes` includes the lifetime of each technology. Where not available, data are taken from industry sources/knowledge[^lighting_industry_knowledge]. 



[^ird_deprates]: 
IR | General depreciation rates August 2024: <https://www.ird.govt.nz/-/media/project/ir/home/documents/forms-and-guides/ir200—ir299/ir265/ir265-august-2024.pdf>

[^lighting_industry_knowledge]: An incandescent bulb typically last around 2,000 hours, a  fluorescent lamp around 10,000 hours, and an LED lamp around 30,000 hours [Choosing a lamp and how you can save money on energy efficiency](https://www.level.org.nz/energy/lighting-design/lamp-selection/), [How to buy LED bulbs - Consumer NZ](https://www.consumer.org.nz/articles/led-bulb-buying-guide)


```{csv-table} Equipment lifetime by technology
:header-rows: 1
:name: tab_agr_lifetimes

Technologies,Lifetime (Years)
Irrigator,10
Lights,3
Stationary Motor,20
Pump,12.5
Farm Bike,20
Tractor,15.5
Truck,34
Utility Vehicle,18
Skidder,12.5
Cable Yarder,20
Hot Water Cylinder,15.5
Heat Recovery System,15.5
Refrigerator,8
Boiler,25
Direct Heat,12.5
Fishing Boat (Non-Hybrid),20
```

## Availability factors

Availability factors for agricultural demand technologies have been extracted from TIMES 2.0 assumptions.


```{csv-table} Availability Factors
:header-rows: 1
:name: tab_agr_afa

Technology,AFA
Vacuum Pump,23%
Irrigator,16%
Hot Water Cylinder,23%
Heat Recovery & Heat Pump,23%
Tractor,9%
Light Truck,2%
Utility,17%
Motorbike/side by side,25%
Transfer Pumps etc,23%
Refrigeration,23%
Heat Recovery System,23%
Light,23%
Frost Protection windmills,7%
Boiler,27%
Direct Heat,100%
Motive Power Stationery,15%
Ground Based,15%
Cable Yarding,15%
Boat,100%
Refrigeration,100%
Other Agriculture Technology,100%
```


## Energy efficiency

Energy efficiency by technology


Energy efficiencies for agricultural demand technologies have been extracted from TIMES 2.0 assumptions.

```{csv-table} Energy efficiency by technology

:header-rows: 1
:name: tab_agr_energy_efficiency

Technology,Efficiency
Vacuum Pump,0.84
Vacuum pump with VSD,0.95
Irrigator,0.7
Irrigator with VSD,0.83
Hot Water Cylinder,0.9
Heat Recovery & Heat Pump,3.5
Tractor,0.11
Light Truck,0.13
Utility,0.23
Motorbike/side by side,0.1
Transfer Pumps etc,0.7
Refrigerator,1.8
Heat Recovery System,3.5
Light,0.14
Frost Protection windmills,0.33
Coal Boiler,0.75
Diesel Boiler,0.85
Natural Gas Boiler,0.85
Direct Heat,1
Electric Motor,0.9
Stationary Engine (Diesel),0.3
Ground Based,0.11
Cable Yarding,0.11
Boat,0.18
Other Agriculture Technology,1
```

## Load curves 

Load curves were adopted from TIMES-NZ 2.0 and applied for dairy sheds, heated greenhouses, off road vehicles, and irrigation systems to capture seasonal farming cycles and climatic effects. Dairy shed and heated greenhouse load curves were sourced from EECA internal datasets. Off road vehicle load curves were estimated by assuming charging would avoid peak periods. Irrigation load curves draw on University of Otago[^electricity_demand_peaks_dairy] estimates and are weighted toward drier seasons. Because irrigation is climate dependent, it is represented at seasonal level; day/night variation was not modelled as a constant value.  


[^electricity_demand_peaks_dairy]: Dew et al., 2021. [Reducing electricity demand peaks on large-scale dairy farms](https://www.sciencedirect.com/science/article/abs/pii/S2352550920303717?dgcid=author)

## Capital and operating and maintenance costs

A full list of capital and operation and maintenance costs assumptions can be found in {numref}`tab_agr_capex_opex` below. The costs of Light Truck, Utility, and Motorbike/side by side were estimated referring to TIMES-NZ 3.0 transport sector assumptions. Similarly, costs of boilers, heating technologies, refrigeration, stationary motors, and lighting were sourced from other TIMES-NZ 3.0 sectors. If data was unavailable, some costs were extracted from TIMES-NZ 2.0 assumptions and rebased to 2023 NZD.


```{csv-table} Energy efficiency by technology

:header-rows: 1
:name: tab_agr_capex_opex

Technology,CAPEX (2023NZD/kW),OPEX (2023NZD/kW/year)
Vacuum Pump,505,14
Vacuum pump with VSD,790,14
Irrigator,7370,917
Irrigator with VSD,7685,917
Hot Water Cylinder,931,18
Heat Recovery & Heat Pump,712,54
Tractor,1185,39
Light Truck,723,70
Utility,446,12
Motorbike/side by side,250,35
Transfer Pumps etc,1089,31
Refrigerator,4028,58
Heat Recovery System,2943,84
Light,112,
Frost Protection windmills,2948,
Coal Boiler,1654,11
Diesel Boiler,628,1
Natural Gas Boiler,513,4
Direct Heat – Geothermal,150,
Electric Motor,280,
Stationary Engine - Diesel,559,
Ground Based,1565,51
Cable Yarding,990,32
Boat,1212,
```



## Emissions factors 

Emissions factors for each thermal fuel are sourced from the Ministry for the Environment’s Measuring Emissions Guide 2025[^meg]. These are all converted to kt CO2e/PJ equivalents using gross calorific values from MfE’s data for use in modelling. Emissions associated with electricity generation are captured separately. The following figures are used in the model: 

```{csv-table} Thermal fuel emission factors

:header-rows: 1
:name: tab_agr_efs
Fuel,Unit,CV MJ/Unit,kg CO2e/unit,kt CO2e/PJ
Coal,kg,25.62,2.11,82.37
Natural Gas,GJ,,54.10,54.10
Petrol,Litre,35.18,2.41,68.79
Diesel,Litre,38.49,2.68,69.63
LPG,kg,50,2.97,59.32
```

[^meg]: Measuring Emissions Guide: <https://environment.govt.nz/publications/measuring-emissions-guide-2025/>