# Demand projections 

We exogenously project energy service demand for each category (space heating, water heating, etc) based on median StatsNZ population projections[^snz_pop_projections]. By default, we assume that each region’s share of population in joined/detached dwellings remains the same, and that the residents per dwelling remain the same. Every additional unit of population therefore is assumed to increase demand for all residential services based on the dwelling types and shares. 

```{figure} figures/population_projections.png 
---
name: fig-pop-projections
alt: National residential growth projection assumptions
---
National residential growth projection assumptions

```

Median population projections reach 6.6 million residents by 2050, a 27% increase over the population of 5.2 million in 2023. We effectively assume that total residential service demand growth aligns with population growth. However, efficiency improvements, such as switching to heat pumps, may lower total energy consumption from the residential sector. 

By default, we assume that other energy efficiency parameters (such as insulation quality or consumer behaviour) remain the same across the projection horizon. It would be possible to instead adjust this over time. 
 

[^snz_pop_projections]: [National population projections: 2024(base)–2078 | Stats NZ](https://www.stats.govt.nz/information-releases/national-population-projections-2024base2078/)