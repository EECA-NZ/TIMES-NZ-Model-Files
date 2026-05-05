# Natural gas fugitive emission factors

The production of natural gas leads to fugitive greenhouse gas emissions. These reflect greenhouse gases that escape into the atmosphere rather than being released by end-use combustion.

These practices include: 
 - Production: unintentional leakage of natural gas during production
 - Venting: the deliberate release of gases into the atmosphere
 - Flaring: onsite combustion of gas/oils to dispose of waste

In New Zealand, most venting activity is at Kapuni, where high-carbon gas is treated at a low temperature separation unit, and then waste carbon dioxide is vented to the atmosphere. However, there is also periodic venting of natural gas at other gas production fields. In TIMES-NZ, we only model Kapuni production separately, to account for the large difference in venting emissions. Other fields are grouped together. 


Emission factors are calculated based on the relevant categories in the GHG inventory 2023[^fug_detail], and net production statistics for each field[^net_gas_prod]. Estimates are used to distinguish venting emissions between Kapuni and other fields. The resulting emission factors are described in {numref}`tab_gas_efs`.

```{csv-table} Natural gas production fugitive emission factors
:name: tab_gas_efs
:header-rows: 1

Emission Category,Emission factor (tCO2e/TJ)
Production fugitive emissions (all fields),0.962
Venting of CO2 (Kapuni LTS),26.96
Venting of natural gas (other fields) ,0.164
Flaring (all fields),0.408

```

Note that TIMES-NZ does not currently account for transmission or distribution losses of natural gas, or the associated fugitive emissions. These values are very minor. Further, emission factors for the combustion of oil and gas products are described in the relevant sector’s documentation. 

[^fug_detail]: Detailed fugitive emissions data available from MfE’s timeseries emissions data by category, available at <https://environment.govt.nz/assets/publications/GhG-Inventory/GHG-Inventory-2025/Time-series-emissions-data-1990-to-2023-from-NZ-GHG-Inventory-2025.xlsx>

[^net_gas_prod]: Net production figures for each field from 2023, which exclude field own use, LPG production, and natural gas reinjection, are sourced from MBIE | [Gas statistics](Ministry of Business, Innovation & Employment).

