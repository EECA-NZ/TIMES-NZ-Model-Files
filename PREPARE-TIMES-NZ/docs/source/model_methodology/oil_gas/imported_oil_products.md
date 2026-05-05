# Imported oil products

We assume that we will continue to be able to import oil products as required. This includes petrol, diesel, aviation fuel, and fuel oil. We assume no limitations on the potential import quantities, and that prices are in line with global oil price outlooks. We assume other price components of oil products, including refining margins and transport costs, remain the same across the projection period. We hold exchange rates constant at 0.60 USD per NZD, as per other modules of TIMES-NZ. 

Oil price projections are from the International Energy Agency’s World Energy Outlook[^weo]. We assume the trajectory follows the Stated Policies Scenario (STEPS), which shows crude oil prices moderately declining from 82 USD/barrel in 2023 to 75 USD/ barrel by 2050, and refined fuels following the same trend. Other IEA scenarios, including the Announced Pledges Scenario and Net Zero Emissions, assume much faster decline in global oil demand and so result in steeper price declines. 

We note that current oil prices and short-term projections are falling below the long-term trends implied by the WEO. We do not currently adjust the model for this, as the long-term oil prices are more important for TIMES-NZ. 


```{csv-table}
:name: tab_imported_fuel_assumptions
:header-rows: 1

Fuel,2023,2030,2050
Crude oil USD/barrel[^iea_crude],82,79,75
Petrol landed cost USD/barrel[^importer_costs],104.6,101.6,97.6
Diesel landed cost USD/barrel,113.6,110.6,106.6
Aviation fuel USD/barrel[^jet_crack],102,99,95
Fuel oil USD/barrel[^fuel_oil],82,79,75
LPG NZD/GJ[^lpg_import],42,41,40
```


All prices are landed costs, so exclude taxes, carbon prices, and local distribution costs.


[^weo]: IEA | [World Energy Outlook 2024](https://www.iea.org/reports/world-energy-outlook-2024). For TIMES-NZ, we select the price projections from the STEPS scenario.
[^iea_crude]: IEA crude prices take the average of crude prices across member countries.
[^importer_costs]: Historical importer costs for petrol or diesel are from: [MBIE | Energy prices](https://www.mbie.govt.nz/building-and-energy/energy-and-natural-resources/energy-statistics-and-modelling/energy-statistics/energy-prices). Conversions are done based on an exchange rate of 1.67 NZD/USD.
[^jet_crack]: We assume a refining margin of 20 USD/barrel for aviation fuel across the projection horizon. Historical refining margins are available at: [IATA - Fuel Price Monitor](https://www.iata.org/en/publications/economics/fuel-monitor/)
[^fuel_oil]: We assume that fuel oil prices are equivalent to crude. Depending on the sulfur content, fuel oil refining margins may even be negative (implying prices cheaper than crude oil). This is necessarily a rough estimate without more information on the composition of fuel oil currently imported. 
[^lpg_import]: LPG import price projections are EECA assumptions and subject to error.