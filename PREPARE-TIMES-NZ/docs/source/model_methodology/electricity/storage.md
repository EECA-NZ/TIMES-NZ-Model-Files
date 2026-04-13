# Storage technologies

Three electricity storage technologies are made available to the model, all lithium-ion:
 - Utility scale batteries (2 hour) 
 - Utility scale batteries (8 hour)
 - Distributed residential batteries (2 hour)

## Overview
Storage technologies in TIMES-NZ allow the model to draw additional power in some time slices and discharge in others, limited by the installed storage capacity.

In TIMES, batteries operate according to the model’s defined time slices. For TIMES-NZ, each day is split into three slices: Day, Night, and Peak, with Peak representing the highest demand hour of the day. Batteries can charge in one or more time slices, and discharge in one or more time slices, but cannot charge and discharge in the same time slice. Further, they cannot transfer energy between days, or between seasons.

The hour settings represent the ratio between the discharge capacity and available storage. For example, a 2-hour 1MW battery would include 2MWh of storage.  If we assume batteries fully charge overnight  and discharge during peak, this means they spend the entire peak hour discharging and then have some leftover storage to discharge during the day. The 8-hour battery is more expensive for peak load capacity but more effective during the day. The optimal system choice of battery within the model will depends on storage costs, capacity costs, supply and demand during each period of the day, etc. 

(storage-key-assumptions)=
## Key assumptions

For each of these technologies, we assume a 20-year technical lifespan, and 85% round-trip efficiency. We further assume a 98% peak contribution factor. The model can choose to install battery capacity if the ability to shift generation across time slices is worth the associated costs and inefficiencies. Cost assumptions are listed in {numref}`tab-battery-costs`. For ease of comparison with other references, capital costs are expressed in terms of both NZD/kW and NZD/kWh. To be clear, only a single capital cost applies.

```{list-table} Battery cost assumptions for Traditional scenario.
:header-rows: 1
:name: tab-battery-costs
* - Battery type
  - Variable
  - 2023
  - 2030
  - 2040
  - 2050
* - Utility-scale (2 hour)
  - Capital costs ($NZD/kW)
  - 1581.6
  - 962.8
  - 731.3
  - 692.3
* - 
  - Capital costs ($NZD/kWh)
  - 790.8
  - 481.4
  - 365.6
  - 346.2
* - 
  - Fixed OM ($NZD/kW)
  - 15.8
  - 15.8
  - 15.8
  - 15.8
* - Utility-scale (8 hour)
  - Capital costs ($NZD/kW)
  - 4491.6
  - 2527
  - 1860.7
  - 1748.2
* - 
  - Capital costs ($NZD/kWh)
  - 561.4
  - 315.9
  - 232.6
  - 218.5
* - 
  - Fixed OM ($NZD/kW)
  - 44.9
  - 44.9
  - 44.9
  - 44.9
* - Distributed (2 hour)
  - Capital costs ($NZD/kW)
  - 3163.1
  - 1925.6
  - 1462.6
  - 1384.7
* - 
  - Capital costs ($NZD/kWh)
  - 1581.6
  - 962.8
  - 731.3
  - 692.3
* - 
  - Fixed OM ($NZD/kW)
  - 31.6
  - 31.6
  - 31.6
  - 31.6

```


### Utility-scale capital costs

Capital cost projections for utility scale batteries are taken from CSRIO GenCost projections , converted to 2023 NZD by an exchange rate assumption of 0.924 AUD/NZD . We use the “Current policies” CSIRO prices for our Traditional scenario, and “Global NZE by 2050” for Transformation, leading to costs falling faster.

### Distributed residential capital costs

Residential battery costs projections are not available in CSIRO data. We assume that distributed batteries are two times the cost of utility-scale batteries. This gives an estimated 2023 cost of 3,163 NZD/kW. Applying the CSIRO cost curve to this price gives 2025 prices of 2,579 NZD/kW, which is in line with currently advertised prices for home battery units, including installation. 
### Fixed maintenance costs

Some maintenance costs are required to ensure that batteries maintain their operational capacity throughout the 15-year lifespan. We assume 1% of current capital costs are required in maintenance annually. This is on the lower end of possible fixed maintenance cost assumptions , as we do not assume capacity augmentation, but only simple maintenance covering repairs and servicing. We assume these maintenance costs remain fixed even as the technology costs improve over time. 


## Existing investment

While the model is able to invest in new battery construction as appropriate, we also include known investment in grid-scale batteries that are either currently operational or under construction. The batteries included are listed in {numref}`tab-battery-existing-installs`.


```{csv-table} Existing or under construction grid-scale battery projects.
:header-rows: 1
:name: tab-battery-existing-installs

Name, Region, Capacity (MW), Installation Date
Rotohiko[^existing_battery_rotohiko], Waikato, 35, 2023
Ruakākā[^existing_battery_ruakaka], Northland, 100, 2024
Glenbrook-Ohurua[^existing_battery_glenbrook], Auckland, 100, 2026
Huntly[^existing_battery_huntly], Waikato, 100, 2027
Glenbrook 2.0[^existing_battery_glenbrook_2], Auckland, 200, 2028
```

While further battery projects have been signalled or consented, these are not listed here nor currently explicitly modelled in TIMES-NZ. All of these are treated as 2-hour ratio batteries, meaning they are modelled with 2 MWh of storage capacity for each MW of output capacity.

[^existing_battery_rotohiko]: [Launch of New Zealand's First Utility Scale Battery Energy Storage System (BESS)](https://www.wel.co.nz/about-us/news/launch-of-new-zealands-first-utility-scale-battery-energy-storage-system-bess/). Note that this battery has a 1-hour storage ratio, but is modelled as 2-hour in TIMES-NZ for simplicity.
[^existing_battery_ruakaka]: [Completion of Ruakākā Battery Energy Storage System](https://www.meridianenergy.co.nz/news-and-events/completion-of-ruakaka-battery-energy-storage-system)
[^existing_battery_glenbrook]: [Contact | Glenbrook-Ohurua Battery](https://contact.co.nz/about-us/sustainability/our-projects/glenbrook-ohurua-battery)
[^existing_battery_huntly]: [Genesis kicks off battery construction at Huntly Power Station](https://www.genesisenergy.co.nz/about/news/genesis-kicks-off-battery-construction-at-huntly-power-station)

[^existing_battery_glenbrook_2]: [Contact to advance new battery, solar and 
geothermal investment (PDF download)](https://contact.co.nz/getContentAsset/41d392c8-c410-4e09-b13e-6623a290f11a/a677e4b4-b3c2-492c-ae74-9399720288b8/CEN-advances-investments%3B-%24525m-equity-raise-announced.pdf)


