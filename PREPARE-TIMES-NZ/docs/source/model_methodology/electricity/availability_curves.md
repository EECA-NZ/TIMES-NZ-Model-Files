
# Availability curves 

This section details capacity factors used across all TIMES-NZ generation types.

## Dispatchable 

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

## Baseload 

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
Geothermal (electricity),88 
```

These plants will never flex generation up or down depending on demand. 

## Solar 

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
**Annual**,,,**11.4%**,**11.4%**
```


```{csv-table} Utility-scale fixed solar availability factors
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
**Annual**,,,**16.4%**,**16.4%**
```

```{csv-table} Utility-scale tracking solar availability factors
:header-rows: 1
:name: tab_solar_availability_utility_track
Season,Day Type,Time of Day,NI,SI
Summer,Weekday,Day,67.7%,75.9%
Summer,Weekday,Night,0.0%,0.1%
Summer,Weekday,Peak,30.2%,43.4%
Summer,Weekend,Day,73.9%,74.5%
Summer,Weekend,Night,0.0%,0.1%
Summer,Weekend,Peak,36.2%,40.7%
Autumn,Weekday,Day,27.2%,24.1%
Autumn,Weekday,Night,0.0%,0.0%
Autumn,Weekday,Peak,0.3%,3.3%
Autumn,Weekend,Day,25.5%,24.8%
Autumn,Weekend,Night,0.0%,0.0%
Autumn,Weekend,Peak,0.6%,3.2%
Winter,Weekday,Day,16.5%,12.9%
Winter,Weekday,Night,0.0%,0.0%
Winter,Weekday,Peak,0.0%,0.1%
Winter,Weekend,Day,15.7%,14.3%
Winter,Weekend,Night,0.0%,0.0%
Winter,Weekend,Peak,0.0%,0.0%
Spring,Weekday,Day,51.4%,50.6%
Spring,Weekday,Night,0.0%,0.0%
Spring,Weekday,Peak,8.7%,16.9%
Spring,Weekend,Day,55.3%,48.2%
Spring,Weekend,Night,0.0%,0.0%
Spring,Weekend,Peak,5.6%,15.5%
**Annual**,,,**19.2%**,**19.2%**
```

## Hydro 
Hydro electricity generation uses a different approach. Here we assume generation follows seasonal patterns, but generation is capable of flexing within these seasonal restrictions. Because average output within a season is fixed, but able to flex within any give timeperiod, the model should, if necessary, lower hydro output when it is not needed. This allows for higher generation at other points in the season while still meeting seasonal constraints. 

```{csv-table} Dispatchable hydro availability assumptions
:header-rows: 1
:name: tab_hydro_availability
Season,North Island,South Island
Sumner,45.3%,60.5%
Autumn,49.6%,56.1%
Winter,38.1%,54.0%
Spring,56.9%,64.0%
**Annual**,**47.5%**,**58.6%**
```
These figures have been extracted from assumptions used for TIMES 2.0. Note that run-of-river hydro is not afforded the same flexibility within the model.

## Wind 

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
**Annual**,,,**38%**,**50%**
```
