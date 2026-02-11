# Demand curves

TIMES-NZ models electricity demand in “timeslices” each year. These split the year into 4 seasons, 2 day types (weekends and weekdays), and three times of day (day, night, and peak), for a total of 24 different times of year. We define peak as the hour from 6-7pm. This is important for modelling the interaction between intermittent electricity supply and variable electricity demand.


## Residential load curve data 


To model the effective shape of residential demand according to these parameters, we use data from the 2021 Residential baseline study[^rbs], which models different patterns of electricity demand behaviour for residential users across Australia and New Zealand. This data does not distinguish space heating from space cooling, instead categorising this demand all under one category of "Space Conditioning". To apply this to TIMES-NZ, we disaggregate "Space Conditioning" into heating and cooling demand according to the assumptions in {numref}`tab_res_curve_conditioning`.

```{csv-table} Assumed heating shares of Space Conditioning demand
:header-rows: 1
:name: tab_res_curve_conditioning

Season, Heating %, Cooling %
Spring, 90%, 10%
Summer, 0%, 100%
Autumn, 90%, 10%
Winter, 100%, 0%
```

RBS end use categories are then assigned to TIMES-NZ categories as outlined in {numref}`tab_res_rbs_times_categories`.


```{csv-table} Residential baseline Study and TIMES-NZ use categories
:header-rows: 1
:name: tab_res_rbs_times_categories

TIMES-NZ Category,RBS Category
Refrigeration,White goods
Space Cooling,Space cooling
"Low Temperature Heat (<100 C), Clothes Drying",White goods
"Low Temperature Heat (<100 C), Clothes Washing",White goods
"Low Temperature Heat (< 100 C), Dishwashers",White goods
"Low Temperature Heat (<100 C), Space Heating",Space heating
"Low Temperature Heat (<100 C), Water Heating",Water heating
"Intermediate Heat (100-300 C), Cooking",Cooking
Electronics and other Electrical Uses,IT&HE
Lighting,Lighting
```

## Ripple control adjustments 

We modify the peak demand of hot water heating to allow for ripple controlled hot water. We assume that 50% of electric hot water cylinders are currently operating with ripple control. The relevant demand is shifted to night in the model.

[^rbs]: Energy Rating | [2021 Residential Baseline Study for Australia and New Zealand for 2000 to 2040](https://www.energyrating.gov.au/industry-information/publications/report-2021-residential-baseline-study-australia-and-new-zealand-2000-2040)


## Resulting peak demand


The resulting average demand curves for weekday loads are demonstrated in {numref}`fig_res_loadcurves`.


```{figure} figures/res_rbs_weekday_ripple.png 
---
name: fig_res_loadcurves
alt: Residential weekday load curves 2023
---
Residential weekday load curves 2023

```

Because our winter peak period still covers 66 hours (1 hour out of every weekday in winter), the average load during this period is lower than actual peak for any given year. To model peak more accurately, we include a residential peak ratio on top of this time slice method. We assume residential peak demand was close to 4GW during the 7.3GW peak on August 2nd, 2023. We therefore add a ratio of 50% for residential peak demand to accommodate for demand variance during these hours. This is additional to the North Island margin included in the TIMES-NZ peaking equation[^times_nz_elc]. This residential peak ratio feature was not included in TIMES 2.0, which likely lead to an underestimate of peak demand in previous releases. 


[^times_nz_elc]: See the TIMES-NZ 3.0 electricity assumptions documentation for more information on peak constraint modelling.