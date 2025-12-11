# Base year residential demand 

```
Calibrating the TIMES NZ base year data for residential sector
```


This documentation describes the methods used to create residential base year data.

Residential base year user config file is found at `data_raw/user_config/VT_TIMESNZ_RES.toml`.
The key data processing script is found at `scripts/stage_2_baseyear/baseyear_residential_demand.py`.
The reshaping script, which generates subtables used to generate the final excel file, can be found at `scripts/stage_4_veda_format/create_baseyear_res_files.py`.

Residential sector follows the below high-level approach: 

 - We define the base year residential demand, based on Energy End Use Database (EEUD ) data, which includes end uses for each fuel and sector. This defines the currently existing technology stocks and demand profile.
 - We disaggregate the demand profile across islands, and optionally across specific subsectors technologies where the necessary detail is not available in the EEUD. 
     - For the residential sector, we disaggregate demand across regions, and by whether the private dwelling is joined (such as an apartment or some townhouses) or detached (freestanding). 
 - Define technology parameter assumptions, including capital costs, energy efficiency, lifetimes and availability factors, for all demand technologies, such as heat pumps or hot water cylinders. 
 - Add exogenous service demand projections for the model. Energy service demand is the demand for useful energy (such as heated rooms). These can be met with different technologies and fuels.
     - For the residential sector, energy service demand projections are based on Stats NZ population projections

The TIMES-NZ model will then optimise the energy allocation to meet the service demand projections across the entire energy sector, taking into consideration other demand, electricity generation, fuel availability, and so on. 


# Raw data used 

All raw data from external sources is stored in `data_raw/external_data/`
 
### Stats NZ 

Dwelling heating methods per region and dwelling type:
 - `dwelling_heating.csv` | [Webpage](https://infoshare.stats.govt.nz). Used to split the space heating technology and fuel demand.

Population by dwelling
 - `population_by_dwelling.csv` | [Webpage](https://infoshare.stats.govt.nz). Used to split the space heating technology and fuel demand.

Total dwellings:
 - `total_dwellings.csv` | [Webpage](https://infoshare.stats.govt.nz). Used to split the space heating technology and fuel demand.

### Residential Baseline Study
 - `RBS.md`. Explain the Residential Baseline Study

### EECA

Energy End Use Data 2023:
 - `eeca_data/eeud/Final EEUD Outputs 2017 - 2023 12032025.xlsx` | [Webpage](https://www.eeca.govt.nz/insights/data-tools/energy-end-use-database/) | [File](https://www.eeca.govt.nz/assets/EECA-Resources/Research-papers-guides/EEUD-Data-2017-2023.xlsx)
 - Used for estimating energy consumed (PJ) by most residential technologies

# Assumptions used

All coded base residential assumptions are stored in `data_raw/coded_assumptions/residential/`.

These include: 

 - Technology lifetime `lifetime_assumptions.csv`. Technologies that reach their technical lifetime are replaced in the model. We assume that currently existing stock has a uniformly distributed range of ages. These lifetimes have been carried forward from TIMES 2.0.
 - Capital costs of technologies `capex_assumptions.csv`. Capital costs are from TIMES 2.0 and have been adjusted for inflation to 2023 dollars. Costs are listed specifically for technology at detached dwellings. If the cost is different for a joined dwelling, these are listed in parentheses. Some technologies do not include a capital cost. These are technologies that we assume can no longer be built, so capital costs are not relevant. Maintenance costs are included for natural gas technologies, as per TIMES 2.0.
 - Technology efficiencies `eff_by_tech_and_fuel.csv`, `eff_for_census_heating_types.csv`. Efficiency is a measure of how much input energy is required for a unit of energy service demand output. For each end use, the implied units of energy service demand may be different, so efficiencies are often not comparable between use types.
 - Availability factors `afa_assumptions.csv`. Availability factors detail our assumptions on how often a particular technology might run to meet the energy service demand. While the percentage share is the direct model input for TIMES, we include the implied average running hours per week for each technology. This impacts the relationship between capacity and output, as it might be more cost-effective to upgrade technology that is used more often. Availability factors are set per type of use, reflecting patterns of service demand. 
 - Reginal Heating-degree days `regional_hdd_assumptions.csv`. Used to model total heat demand for each region and dwelling type
 - Residential dwelling floor area in each region `floor_area_per_dwelling.csv`. Used to model total heat demand for each region and dwelling type


# Detailed method

## 1 Regional space heating model

To model where space heating technologies and fuels from the EEUD are used, we spread known fuel demand using:
 - Census 2023 data on heating methods per region and dwelling type
 - Census 2023 data on population per region and dwelling type
 - Assumptions on floor area per dwelling type
 - Heating-degree days, or heat demand per region in a typical meteorological year
 - Technology efficiency assumptions

We align with the method used for TIMES 2.0 and “Regional breakdown of New Zealand’s residential heat demand and associated emissions” , while simplifying slightly to model demand at a regional council level, rather than by district. 

### Step 1: Model total heat demand for each region and dwelling type: 

 - HeatDemand_(r,d)=  FloorArea_(r,d)*HDD_r*C

Where:
 - HeatDemand_(r,d)   is the residential space heating demand in each region r and dwelling type d. 
 - FloorArea_(r,d) \  is the residential dwelling floor area in each region r and dwelling type d.
 - HDD_r are the heating-degree days for the region r. We use the same assumptions on regional heating-degree days as TIMES 2.0. 
 - C_r is a constant which captures other drivers of a region’s heating demand, such as insulation properties or behavioural differences. We assume that these other drivers are the same between regions. 
 - Floor area assumptions are 171 m2 for detached dwellings, and 115 m2 for joined dwellings. 

### Step 2: Disaggregate floor area heat demand by heating methods

We expand the floor area method of determining heat demand by breaking it down by share of heating method. 

 - HeatDemand_(r,d)=  ∑_h▒〖(FloorArea_(r,d)*HeatingTypeShare_(r,d,h))〗*HDD_r*C 

Where:
 - HeatingTypeShare_(r,d,h) is the share of heating method h used in dwelling type d and region r.

Heating method shares can be found using Census 2023 data. The census respondents could provide multiple answers, but it is not possible to distinguish dwellings using multiple heating methods. We therefore simplify the results to estimate shares of heating method per region and dwelling type.
 
### Step 3: Convert heat demand into fuel demand 

Different heating technologies have different efficiencies, and so the input energy is different across different types. To appropriately disaggregate energy demand, rather than heating service demand, we apply efficiency assumptions for each technology: 

 - EnergyDemand_(r,d,h)= HeatDemand_(r,d,h)/FuelEfficency_h

### Step 4: Apply modelled fuel demand shares to known residential fuel demand

We map the census technologies to known EEUD technologies and fuels. We then apply the modelled fuel demand shares to the EEUD results to estimate heat demand by technology, fuel, region, and dwelling type. 
 
Note that total demand for joined dwellings is much lower than for detached dwellings, because standalone houses are much more common than apartments or joined townhouses in all areas of the country. 


## 2 Other energy demand

Other energy demand is disaggregated by population and dwelling type per region, without controlling for temperature. This includes water heating demand, which we assume is mostly driven by population rather than ground temperature.

Again, natural gas use for other end use demand is distributed entirely across the north island, and demand reallocated for those end uses. This impacts cooking and water heating demand shares.


## 3 Geothermal and solar demand 

The EEUD lists geothermal and direct solar energy use by residences but does not allocate these to specific uses or technologies. We assume that all geothermal residential use is for space heating through ground source heat pumps, and we assume all solar thermal use (which excludes rooftop solar for electricity generation) is used for water heating. Limited information is available on the use of these technologies , so we simply distribute the use according to population. The estimated energy values involved are very small. 


## 4 Residential demand curves

TIMES-NZ models electricity demand in “timeslices” each year. These split the year into 4 seasons, 2 day types (weekends and weekdays), and three times of day (day, night, and peak), for a total of 24 different times of year. We define peak as the hour from 6-7pm. This is important for modelling the interaction between intermittent electricity supply and variable electricity demand.

To model the effective shape of residential demand according to these parameters, we use EMI GXP demand data and identify which GXPs serve mostly residential connection points. We then assume that the demand from these residential GXPs is consistent with overall residential demand. 

Because our winter peak period still covers 66 hours (1 hour out of every weekday in winter), the average load during this period is lower than actual peak for any given year. To model peak more accurately, we include a residential peak ratio on top of this time slice method. We assume residential peak demand was close to 4GW during the 7.3GW peak on August 2nd, 2023. We therefore add a ratio of 50% for residential peak demand to accommodate for demand variance during these hours. This is additional to the 15% North Island margin included in the TIMES-NZ peaking equation . This residential peak ratio feature was not included in TIMES 2.0, which likely lead to an underestimate of peak demand in previous releases. 


## 5 Future available technologies

Technologies not modelled in the base year may be introduced to residences in future years. The model makes several new technologies available, which typically offer energy efficiency improvements for increased capital cost.


## 6 Exogenous demand projections 

We exogenously project energy service demand for each category (space heating, water heating, etc) based on median StatsNZ population projections . By default, we assume that each region’s share of population in joined/detached dwellings remains the same, and that the residents per dwelling remain the same. Every additional unit of population therefore is assumed to increase demand for all residential services based on the dwelling types and shares. 

Median population projections reach 6.6 million residents by 2050, a 27% increase over the population of 5.2 million in 2023. We effectively assume that total residential service demand growth aligns with population growth. However, efficiency improvements, such as switching to heat pumps, may lower total energy consumption from the residential sector. 

By default, we assume that other energy efficiency parameters (such as insulation quality or consumer behaviour) remain the same across the projection horizon. It would be possible to instead adjust these over time. 


