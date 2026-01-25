# Demand disaggregation


TIMES-NZ models residential demand across different regions, and also across different dwelling types (joined/detached), as these have different energy demand profiles. We disaggregate the EEUD demand data across regions and dwelling types to model residential demand in more detail.
This input disaggregation is based on modelling done for TIMES-NZ 2.0 and at the University of Otago[^otago_modelling]. At a high level, energy demand is disaggregated by:

a)	Population and dwelling type data per region from Census 2023
b)	Known fuel availability (South Island regions do not have access to natural gas)
c)	Census 2023 responses on dwelling heating methods per region and dwelling type
d)	Typical meteorological year Heating-degree days per region 	

These methods are detailed further below. The resulting residential demand model is designed per regional council area. However, TIMES-NZ currently only models each island, so this is aggregated to demand per island for use in the model itself. The full regional results are made available separately. 

## Regional space heating model 


To model where space heating technologies and fuels from the EEUD[^eeud] are used, we distribute known fuel demand using:
 - Census 2023 data on heating methods per region and dwelling type[^census_heating]
 - Census 2023 data on population per region and dwelling type
 - Assumptions on floor area per dwelling type
 - Heating-degree days, or heat demand per region in a typical meteorological year
 - Technology efficiency assumptions


We align with the method used for TIMES 2.0 and “Regional breakdown of New Zealand’s residential heat demand and associated emissions”[^otago_modelling], while simplifying slightly to model demand at a regional council level, rather than by district. 


[^census_heating]: Census heating data retrieved from [SNZ | Aotearoa Data Explorer](https://explore.data.stats.govt.nz/vis?tm=heating&pg=0&snb=22&df[ds]=ds-nsiws-disseminate&df[id]=CEN23_HOU_012&df[ag]=STATSNZ&df[vs]=1.0&dq=2018%2B2023.15%2B14%2B13%2B12%2B18%2B17%2B16%2B09%2B08%2B07%2B06%2B04%2B05%2B03%2B02%2B01%2B99999.99.999&to[TIME]=false)
[^otago_modelling]: [Regional breakdown of New Zealand’s residential heat demand and associated emissions](https://www.sciencedirect.com/science/article/pii/S0378778825004451?ref=pdf_download&fr=RR-2&rr=96eac9737ef11c4e)
[^eeud]: EECA | EEUD: <https://www.eeca.govt.nz/insights/data-tools/energy-end-use-database/>


### Step 1: Model total heat demand for each region and dwelling type

Equation {eq}`eq_heat_demand_region_dwelling_type`: Heat demand for each region and dwelling type

```{math}
:label: eq_heat_demand_region_dwelling_type
HeatDemand_{r,d} = FloorArea_{r,d} \cdot HDD_r \cdot C
```

Where: 

 - $HeatDemand_{r,d}$ is the residential space heating demand in each region $r$ and dwelling type $d$.
 - $FloorArea_{r,d}$ is the residential dwelling floor area in each region $r$ and dwelling type $d$.
 - $HDD$ are the heating-degree days[^HDD_explain] for the region $r$. We use the same assumptions on regional heating-degree days as TIMES 2.0. These are based on a typical meteorological year.
 - $C$ is a constant which captures other drivers of a region’s heating demand, such as insulation properties or behavioural differences. We assume that these other drivers are the same between regions.


Floor area assumptions are **171** m<sup>2</sup> for detached dwellings, and **115** m<sup>2</sup> for joined dwellings. \


[^HDD_explain]: HDD is a measure of how often the area would heating to meet a defined temperature. A higher HDD effectively means a colder climate. HDD calculations done by [NIWA](https://www.building.govt.nz/assets/Uploads/getting-started/building-for-climate-change/niwa-client-report-weather-files-for-energy-modelling.pdf) for specific climate zones have been mapped to regional council areas for TIMES-NZ. 

### Step 2: Disaggregate floor area heat demand by heating methods 
Equation {eq}`eq_floor_area_heating_demand`: Floor area heating demand 

We expand the floor area method of determining heat demand by breaking it down by share of heating method. 


```{math}
:label: eq_floor_area_heating_demand

HeatDemand_{r,d} = \sum_h{(FloorArea_{r,d} \cdot HeatingTypeShare_{r,d,h})} \cdot HDD_r \cdot C
```

Where $HeatingTypeShare_{r,d,h}$ is the share of heating method $h$ used in dwelling type $d$ and region $r$.

Heating method shares can be found using Census 2023 data[^census_heating]. The census respondents could provide multiple answers, but it is not possible to distinguish dwellings using multiple heating methods. We therefore simplify the results to estimate shares of heating method per region and dwelling type. The resulting heating shares are detailed in {numref}`fig-heating-shares`. 



```{figure} figures/heating_shares.png
---
name: fig-heating-shares
alt: Heating methods per region and dwelling type
---
Heating methods per region and dwelling type

```

(heading-residential-disaggregation-efficiency)=
### Step 3: Convert heat demand into fuel demand 


Different heating technologies have different efficiencies, and so the input energy is different across different types. To appropriately disaggregate *energy demand*, rather than heating service demand, we apply efficiency assumptions for each technology: 


```{math}
:label: eq_fuel_energy_demand
EnergyDemand_{r,d,h} = \dfrac{HeatDemand_{r,d,h}}{FuelEfficency_h}
```

Efficiency assumptions used for each heating technology are listed in {numref}`tab-heating-tech-efficiency-assumptions`.



```{list-table} Efficiency assumptions for space heating technologies
:header-rows: 1
:name: tab-heating-tech-efficiency-assumptions
* - Technology
  - Fuel efficiency
* - Coal burner
  - 55%
* - Electric heater
  - 100%
* - Fixed gas heater
  - 80%
* - Heat pump
  - 375%
* - Pellet fire
  - 75%
* - Portable gas heater
  - 80%
* - Wood burner
  - 65%
```

### Step 4: Apply modelled fuel demand shares to known residential fuel demand


We map the census technologies to known EEUD technologies and fuels. We then apply the modelled fuel demand shares to the EEUD results to estimate heat demand by technology, fuel, region, and dwelling type. Results of this exercise are displayed in {numref}`fig-regional-space-heating-demand`



```{figure} figures/demand_by_fuel_space_heating.png
---
name: fig-regional-space-heating-demand
alt: Estimated regional shares of space heating demand
---
Estimated regional shares of space heating demand

```


Note that total demand for joined dwellings is much lower than for detached dwellings, because standalone houses are much more common than apartments or joined townhouses in all areas of the country. 

## Other energy demand 

Other energy demand is disaggregated by population and dwelling type per region, without controlling for temperature. This includes water heating demand, which we assume is mostly driven by population rather than ground temperature.

Again, natural gas use for other end use demand is distributed entirely across the North Island, and demand reallocated for those end uses. This impacts cooking and water heating demand shares.


## Geothermal and solar demand 

The EEUD lists geothermal and direct solar energy use by residences but does not allocate these to specific uses or technologies. We assume that all geothermal residential use is for space heating through ground source heat pumps, and we assume all solar thermal use (which excludes rooftop solar for electricity generation) is used for water heating. Limited information is available on the use of these technologies[^gns_database], so we simply distribute the use according to population. The estimated energy values involved are very small. 

[^gns_database]: The GNS database of geothermal demand sites shows geothermal residential heating installations across both the North and South Islands: [GNS Science - New Zealand Geothermal Use Database](https://data.gns.cri.nz/geothermal/index.html)