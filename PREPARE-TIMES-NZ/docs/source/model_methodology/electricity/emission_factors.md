# Emission factors

Electricity generation greenhouse gas emissions can come from the combustion of thermal fuels, such as coal or natural gas, or fugitive emissions from gases lost during geothermal electricity generation. 


## Thermal fuel emission factors

Emission factors for each thermal fuel are sourced from the Ministry for the Environment’s Measuring Emissions Guide 2025[^meg]. These are all converted to kt CO2e/PJ equivalents, using gross calorific values from MfE’s data, for use in modelling. Biogas emission factors and calorific values are not available from MfE, so we instead use UK Government data[^uk_ghgcf] for this fuel. 

The following figures are used in the model: 

```{list-table} Thermal fuel emission factors
:header-rows: 1
:name: tab-thermal-ele-efs
* - Fuel
  - Unit
  - CV MJ/Unit
  - kg CO2e/unit
  - kt CO2e/PJ
* - Coal - Sub-Bituminous
  - kg
  - 21.64
  - 2.01
  - 92.65
* - Diesel
  - Litre
  - 38.49
  - 2.67
  - 69.39
* - Natural Gas
  - GJ
  - 1000
  - 54.12
  - 54.12
* - Biogas
  - kg
  - 22
  - 0.0012
  - 0.06
* - Wood - Chips
  - kg
  - 15.15
  - 0.023
  - 1.52
```

[^meg]: MFE | Measuring Emissions Guide: <https://environment.govt.nz/publications/measuring-emissions-guide-2025/>
[^uk_ghgcf]: Greenhouse gas reporting: conversion factors 2022: <https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2022> 

## Fugitive geothermal emission factors

Fugitive geothermal emission factors are modelled based on the output electricity, rather than the input fuel, so are not directly comparable to the thermal fuel emission factors above. Geothermal emissions are highly variable, based on the field’s greenhouse gas concentration and reinjection technology in use.

Several existing or future plants have planned installation of future Non-Condensable Gas (NCG)[^ncg_explain] reinjection technology[^ncg_implement], which lead to reduced or even zero emissions. These NCG reinjections have been integrated into the TIMES-NZ model assumptions below.

[^ncg_explain]: NCG Reinjection explained | NZGA: <https://www.nzgeothermal.org.nz/downloads/NZGA-Fact-Sheet-CO2-Reinjection-Explained.pdf>
[^ncg_implement]: Details on planned NCG implementation for current and future plants can be found at the NZGA CO2 group presentation:  <https://www.nzgeothermal.org.nz/downloads/CO2-group-presentation-for-geo-week-2024_Final.pptx.pdf>

### Existing geothermal plant emissions

Emission factors for existing plants during 2023 are sourced from New Zealand Geothermal Association research[^nzga_research]. Plants with expected future reinjection, and subsequent decreased emissions, are noted in the table. The emission factors (and future reductions if applicable) that we are using are as follows: 

```{list-table} Emission factors for existing geothermal plants
:header-rows: 1
:name: tab-exist-geo-efs
* - Plant Name
  - Capacity (MW)
  - 2023 gCO2e/kWh
  - NCG implementation year
* - 
  - 
  - 
  - (new emission factor)
* - Kawerau
  - 106
  - 122
  - 
* - Mokai
  - 112
  - 27
  - 
* - Nga Awa Pūrua
  - 140
  - 59
  - 
* - Ngā Tamariki (OEC1-4)
  - 85
  - 43
  - 2026 (14.5 –> 7.6)[^nga_tamariki]
* - Ngāwhā (OEC1-3)
  - 28
  - 0
  - Already implemented
* - Ngāwhā (OEC4)
  - 31.5
  - 95
  - 2024 (0)
* - Ōhaaki
  - 50
  - 302
  - 
* - Poihipi
  - 55
  - 39
  - 
* - Rotokawa
  - 38
  - 58
  - 
* - Te Ahi O Maui
  - 27
  - 61
  - 2026 (0)
* - Te Huka Binary
  - 28
  - 24
  - 2024 (0)
* - Te Mihi
  - 166
  - 34
  - 
* - TOPP1
  - 21.5
  - 56
  - 2026 (0)
* - Wairakei A&B
  - 117
  - 21
  - 
* - Wairakei Binary
  - 14.4
  - 21
  - 

```

[^nzga_research]: McLean, K., Richardson, I., Hanik, F., Siega, F., & Gibson, B. (2024). Reducing greenhouse gas emissions from NZ geothermal power stations. New Zealand Geothermal Association. Retrieved from <https://www.worldgeothermal.org/pdf/IGAstandard/NZGW/2024//044.pdf>.
[^nga_tamariki]: Ngā Tamariki emissions, including OEC5, are estimated at 1.9 tCO2e/hour across all units (131 MW) from 2026, equivalent to 14.5 gCO2e/kWh. This declines to 1 tCO2e/hr, or 7.6 gCO2e/kWh, by 2050. We apply this to all Ngā Tamariki units. See slide 7 of the NZGA CO2 group’s presentation for further details at <https://www.nzgeothermal.org.nz/downloads/CO2-group-presentation-for-geo-week-2024_Final.pptx.pdf>

### Future geothermal plant emissions

Emission factors for future geothermal plants depend on whether NCG reinjection has been signalled at these plants and is otherwise based on assumption. If good information is not available for these plants, we apply a default emission factor of 62 gCO2e/kWh in the first year of operation, with emissions declining over time (see {ref}`'Field reductions over time' <heading-field-reductions>`). The emission factor assumptions for future geothermal plants are as follows: 

```{list-table} Emission factors for future geothermal plants
:header-rows: 1
:name: tab_future_geo_efs
* - Plant
  - Capacity (MW)
  - Capital cost (NZD/kW)
  - Emission Factor gCO2e/kWh
* - Ātiamuri Geothermal
  - 5
  - $11,417
  - 62
* - Kawerau (TOPP2)
  - 49
  - $6,559
  - 0
* - Ngā Tamariki expansion
  - 46
  - $4,413
  - (14.5 –> 7.6) 
* - Ngāwhā Expansion: Stage 5
  - 25
  - $9,120
  - 0
* - Ngāwhā Expansion: Stage 6
  - 25
  - $9,120
  - 0
* - Ngāwhā Stage 4 (OEC5)
  - 32
  - $9,190
  - 0
* - Reporoa: Stage 2
  - 25
  - $7,162
  - 62
* - Tāheke Geothermal Project
  - 35
  - $7,162
  - 62
* - Tāheke: Stage 2
  - 25
  - $7,162
  - 62
* - Tāheke: Stage 3
  - 25
  - $7,162
  - 62
* - Tauhara Stage 1
  - 152
  - $5,290
  - 32
* - Tauhara Stage 1 expansion
  - 22
  - $5,272
  - 32
* - Te Huka Unit 3
  - 51.4
  - $5,966
  - 0
* - Te Mihi (expansion)
  - 180
  - $5,576
  - 34
* - Tokaanu Geothermal (Stage 2)
  - 100
  - $5,984
  - 62
* - Wairākei C & D
  - 40
  - $5,890
  - 21
```
NCG reinjection has been signalled at TOPP2 and Te Huka Unit 3. We assume full reinjection at any potential future Ngāwhā units, not just OEC4. The Ngā Tamariki expansion (OEC5) follows the same method as the existing Ngā Tamariki units. We also assume that Wairākei C & D will use the same emission factor as Wairakei A&B, and the Te Mihi expansion will have the same emission factor as Te Mihi. The Tauhara expansion uses estimated Te Huka emissions without NCG reinjection[^tauhara_no_ncg]. Costs are based on the MBIE generation stack.

[^tauhara_no_ncg]: See table 5 at <https://www.worldgeothermal.org/pdf/IGAstandard/NZGW/2024//044.pdf>. Tauhara shares a field with Te Huka, but no reinjection has been signalled for this plant or its expansion.


(heading-field-reductions)=
### Field reductions over time
Emissions factors at geothermal fields tend to decline over time, as the greenhouse gas concentration in the fields falls. To include this impact in the model, we make the conservative assumption that the emission factor falls by 3% annually for the first 7 years of operation. This means the emissions factor stabilises at 50 gCO2e/kWh, which is the same as the median emissions factor of existing plants in 2023. This assumption is applied to any future geothermal plant with the default emissions factor, but not existing plants[^missing_method]. 


[^missing_method]: This feature is not yet built. 
