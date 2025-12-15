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

For each of these technologies, we assume a 15-year technical lifespan, and 85% round-trip efficiency. We further assume a 98% peak contribution factor. The model can choose to install battery capacity if the ability to shift generation across time slices is worth the associated costs and inefficiencies. Cost assumptions are listed in {numref}`tab-battery-costs`. For ease of comparison with other references, capital costs are expressed in terms of both $/kW and $/kWh. To be clear, only a single capital cost applies.

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

