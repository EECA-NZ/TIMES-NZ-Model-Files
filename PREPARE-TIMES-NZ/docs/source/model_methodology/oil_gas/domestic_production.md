# Domestic production

Domestic supply of natural gas, LPG, and crude oil and condensate is based on the petroleum reserves data published by MBIE[^mbie_reserves]. This data includes forecast production rates for each field and fuel, and probable remaining reserves.

## Natural gas 


Natural gas supply data comes from oil and gas reserve data, which describes the state of production on January 1st, 2025. This covers the latest assessment of Proven and Probable (2P) gas reserves remaining in each field and expected profiles of future production.

{numref}`fig_mbie_prod_profile`, originally published by MBIE with Energy in New Zealand 2025[^mbie_enz_gas], shows the latest production forecasts, and how actual production often fell short of the forecast production profile over the last five years:


```{figure} figures/energy_in_new_zealand_2025_g5_production_profile_years.png
---
name: fig_mbie_prod_profile
alt: Gas production profiles as reported from 1 January 2020 through 1 January 2025
---
Gas production profiles as reported from 1 January 2020 through 1 January 2025
```
We make no assumptions regarding the wholesale price of natural gas in the model. Rather, we assume the production cost remains flat at 9.03 NZD/GJ[^mbie_prices], and allow the model to optimise how best to distribute the shrinking supply. As demand continues to outstrip supply, this effectively means that the marginal "system cost" of consuming an additional unit of natural gas is equivalent to the cost of replacing it - usually through fuel switching - elsewhere in the system. 

We note that the declining upstream natural gas market will likely have significant impacts on the downstream sector, particularly for feedstock use at Methanex and Ballance's Kapuni site. Further details for these and other sites are covered in the industry sector assumptions documentation.


[^mbie_reserves]: MBIE | [Petroleum reserves data](https://www.mbie.govt.nz/building-and-energy/energy-and-natural-resources/energy-statistics-and-modelling/energy-statistics/petroleum-reserves-data)

[^mbie_enz_gas]: MBIE | [Energy in New Zealand: Gas](https://www.mbie.govt.nz/building-and-energy/energy-and-natural-resources/energy-statistics-and-modelling/energy-publications-and-technical-papers/energy-in-new-zealand/energy-in-new-zealand-2025/gas)


[^mbie_prices]: Historical natural gas wholesale prices are published by MBIE at [Energy prices](https://www.mbie.govt.nz/building-and-energy/energy-and-natural-resources/energy-statistics-and-modelling/energy-statistics/energy-prices). 


[^supply_caveat]: As implemented using the TIMES model, this will mean that any unused production in a given year is lost. We do not expect this circumstance to occur, but this setup may require adjustment. 

## Future deliverability

Previous versions of TIMES-NZ assumed that natural gas supply could be delivered at the sector’s historical max deliverability. This does not reflect the current state of the sector, so we ensure max deliverability is instead equal to current forecast production profiles. The model will consider both cumulative reserves, and max deliverability per field, for any given year[^supply_caveat].  

Natural gas supply is therefore limited to the latest MBIE 2P production profiles for each field. We also apply a Maui closure patch, setting Maui gas production to zero from 2027 onward to reflect closure at the end of 2026. These assumptions lead to the following production projections for each field:

```{figure} figures/gas_projections_by_field.png
---
name: fig_gas_proj_by_field
alt: Gas production projections by field
---

Gas production projections by field[^reserve_definitions]
```


The national results are shown in {numref}`fig_gas_proj_national`.

```{figure} figures/gas_projections_national.png
---
name: fig_gas_proj_national
alt: National gas production projection assumptions
---

National gas production projection assumptions
```

[^reserve_definitions]: Existing reserves are the 2P reserves published in MBIE’s gas reserves data, with Maui production set to zero from 2027 onward.

## Crude oil and condensate

Crude oil production in TIMES-NZ follows oil production profiles for crude, condensate, and naphtha. We assume this fuel is entirely exported. This was true even when New Zealand had oil refining capacity, as New Zealand’s indigenous crude oil was not suitable for refining at Marsden Point. However, it is included in the model to ensure the TIMES-NZ energy balance aligns with official energy balances. Future expectations of indigenous oil production are derived from MBIE’s petroleum reserves data, which forecast production declining from 37.66 PJ in 2023 to 2.33 PJ by 2040.

As this fuel is entirely exported, we do not allocate it a cost. It does not compete with other fuels in the energy system. 

## LPG

LPG production forecasts show domestic production falling from 7.15 PJ in 2023  to 0.30 PJ by 2038, at which point Kapuni will be the only field producing LPG. After this point we assume domestic production ceases entirely.

LPG is also imported, and we assume there is no limitation on import volumes. For domestic production, we assume the price is constant through time at 39 NZD/GJ[^lpg_prices]. Import prices are slightly higher, between 42 and 40 NZD/GJ. This is a change from the approach used in TIMES-NZ 2.0, where LPG prices rose significantly across the projection period for both imported and domestically produced LPG.

[^lpg_prices]: In the absence of public data on wholesale LPG prices, we reference the [Mont Belvieu TX Propane Spot Price at Mont Belvieu, TX Propane Spot Price FOB (Dollars per Gallon)](https://www.eia.gov/dnav/pet/hist/eer_epllpa_pf4_y44mb_dpgD.htm) to estimate NZ import LPG commodity prices for LPG.
