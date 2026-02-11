# Demand curves

TIMES-NZ models electricity demand in “timeslices” each year. These split the year into 4 seasons, 2 day types (weekends and weekdays), and three times of day (day, night, and peak), for a total of 24 different times of year. We define peak as the hour from 6-7pm. This is important for modelling the interaction between intermittent electricity supply and variable electricity demand.


To model the effective shape of residential demand according to these parameters, we use data from the 2021 Residential baseline study[^rbs], which models different patterns of electricity demand behaviour for residential users across Australia and New Zealand. This data does not distinguish space heating from space cooling, instead categorising this demand all under one category of "Space Conditioning". To apply this to TIMES-NZ, we disaggregate "Space Conditioning" into heating and cooling demand according to the following assumptions in each season: 

```{csv-table} Assumed heating shares of Space Conditioning demand
:header-rows: 1
:label: tab_res_curve_conditioning

Season, Heating %, Cooling %
Spring, 90%, 10%
Summer, 0%, 100%
Autumn, 90%, 10%
Winter, 100%, 0%
```

RBS end use categories are assigned to TIMES-NZ categories as outlined in {numref}`tab_res_rbs_times_categories`.


```{csv-table} Assumed heating shares of Space Conditioning demand
:header-rows: 1
:label: tab_res_curve_conditioning

Season, Heating %, Cooling %
Spring, 90%, 10%
Summer, 0%, 100%
Autumn, 90%, 10%
Winter, 100%, 0%
```






[^rbs]: Energy Rating | [2021 Residential Baseline Study for Australia and New Zealand for 2000 to 2040](https://www.energyrating.gov.au/industry-information/publications/report-2021-residential-baseline-study-australia-and-new-zealand-2000-2040)



 REMI GXP demand data and identify which GXPs serve mostly residential connection points[^emi_res_gxp]. We then assume that the demand from these residential GXPs is consistent with overall residential demand. Average residential GW load, using total 2023 demand as an example, is shown in {numref}`fig-average-res-load`.




```{figure} figures/residential_load_curves.png
---
name: fig-average-res-load
alt: Average residential load by timeslice
---
Average residential load by timeslice
```
Because our winter peak period still covers 66 hours (1 hour out of every weekday in winter), the average load during this period is lower than actual peak for any given year. To model peak more accurately, we include a residential peak ratio on top of this time slice method. We assume residential peak demand was close to 4GW during the 7.3GW peak on August 2nd, 2023. We therefore add a ratio of 50% for residential peak demand to accommodate for demand variance during these hours. This is additional to the 15% North Island margin included in the TIMES-NZ peaking equation[^times_nz_elc]. This residential peak ratio feature was not included in TIMES 2.0, which likely lead to an underestimate of peak demand in previous releases. 

[^emi_res_gxp]: We define residential GXPs as those with 90% or more of the attached ICPs defined as “residential”, as per the market share data hosted by EMI at [Electricity Authority - EMI (market statistics and tools) | Market share snapshot](https://www.emi.ea.govt.nz/Retail/Reports/R_MSS_C)

[^times_nz_elc]: See the TIMES-NZ 3.0 electricity assumptions documentation for more information on peak constraint modelling.