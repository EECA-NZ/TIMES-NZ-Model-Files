# Base year transport demand 

```
Calibrating the TIMES NZ base year data for transport sector
```


This documentation describes the methods used to create transport base year data.

Transport base year user config file is found at `data_raw/user_config/VT_TIMESNZ_TRA.toml`.
The key data processing script is found at `scripts/stage_2_baseyear/baseyear_transport_demand.py`.
The reshaping script, which generates subtables used to generate the final excel file, can be found at `scripts/stage_4_veda_format/create_baseyear_TRA_files.py`.

The base year vehicle data is intended to reflect the distribution of 2023 transport demand across the total vehicle fleet in New Zealand. These vehicles should be available to the model to meet future demand, but with enough information (region, technology, remaining life, etc.) that the model will retire vehicles at appropriate points and can make least-cost decisions on fleet replacement, fuel switching, and utilisation across demand segments.

We have improved on TIMES-NZ 2.0 by building a bottom-up, asset-based model of the existing transport fleet. This gives us much greater detail in how the model utilises the existing transport fleet and will allow us to make very precise changes as needed.

Note that this does mean updating the base year will currently require a manual review of this existing asset list.

# Raw data used 

All raw data from external sources is stored in `data_raw/external_data/`

### Ministry of Business Innovation and Employement (MBIE) 

Energy Balance Table:
 - `mbie/energy-balance-tables.xlsx` | [Webpage](https://www.mbie.govt.nz/building-and-energy/energy-and-natural-resources/energy-statistics-and-modelling/energy-statistics/energy-balances/) | [File](https://www.mbie.govt.nz/assets/Data-Files/Energy/nz-energy-quarterly-and-energy-in-nz/energy-balance-tables.xlsx)
 - Used for estimating energy consumed (PJ) by aviation and shipping 

### Ministry of Transport (MoT)

Annual Fleet Statistics:
 - `mot/NZVehicleFleet_2023.xlsx` | [Webpage](https://www.transport.govt.nz/statistics-and-insights/fleet-statistics/annual-fleet-statistics/) | [File](https://www.mot-dev.link/fleet/annual-motor-vehicle-fleet-statistics/session/bf578685bf8933e466fee5daa90b1ff2/download/download_all_tables?w=)
 - Used for estimating vehicle kilometers travelled (million vkt), and vehicle lifetime (years)

### New Zealand TRansport Agency (NZTA)

Motor Vehicle Register (MVR):
 - `nzta/Fleet-31Dec2023.csv` | [Source](NZ Transport Agency Waka Kotahi. Personal Communication with Energy Efficiency and Conservation Authority (EECA))
 - Used for estimating vehicle counts and vehicle proportions to futher disaggregate vkt based on fuel type and technology

### Kiwi Rail

Energy used for Rail Transport:
 - `kiwirail/Kiwirail data check 2022-23 Input data.xlsx` | [Source](KiwiRail Personal Communication with EECA)
 - Used for estimating energy consumed (PJ) by passenger and freight rail
 
### Stats NZ 

Consumer Price Index:
 - `cpi/cpi_infoshare.csv` | [Webpage](https://infoshare.stats.govt.nz/QueryUpload.aspx) 
 - (Load the query stored at `statsnz/infoshare_queries/infoshare_cpi_query.tqx`)
 - Used for the functions at `library/deflator.py` to deflate price data to different base years as needed.

### NREL 

2024 Transportation Annual Technology Baseline Data: 
 - `nrel/NREL_vehicles_fuels_2023.csv` | [Webpage](https://atb.nrel.gov/transportation/2024/data) | [File](https://atb.nrel.gov/img/other/2024_atb_transportation_data_v1.zip)
 - Used for estimating vehicle investment costs, maintenance costs and future cost indices (the Moderate and the Conservative scenarios were used for estimating costs)

### EECA

Energy End Use Data 2023:
 - `eeca_data/eeud/EEUD_PJ_2023.xlsx` | [Webpage](https://www.eeca.govt.nz/insights/data-tools/energy-end-use-database/) | [File](https://www.eeca.govt.nz/assets/EECA-Resources/Research-papers-guides/EEUD-Data-2017-2023.xlsx)
 - Used for estimating energy consumed (PJ) by all road transport technologies

Total Cost of Ownership (TCO):
 - `eeca_data/tcoe/vehicle_costs_2023.xlsx` | [Webpage](https://www.genless.govt.nz/for-business/vehicles-and-transport/vehicle-total-cost-of-ownership-calculator/) | [File](A curated list of top-selling models across multiple technology types and vehicle categories) - Used for estimating key cost components, including purchase price (capital cost), servicing costs, tyre costs, and a combined per-kilometre operating cost for each representative model

# Assumptions used

All coded base transport assumptions are stored in `data_raw/coded_assumptions/transport_demand/`.

These include: 

 - Mode or Fuel Share (%) `Mode_fuelshare.xlsx` - contains mode or fuel share % for a few technologies (e.g. light passenger plung-in hybrids petrol/electricity fuel share)
 - Regional Splits for Transport Demand `Transport region splits.xlsx` - contains the division of energy service demand between the North and South Islands which is determined using a mix of proxies
 - Travel splits for rigid and articulated distances by GVM class `transporthelpers.py` <ARTIC_CLASS_PERC> - split travel into rigid and articulated distances by GVM class (3.5-7.5t, 7.5-10t, 10-20t, 20-25t, 25-30t, > 30t)
 - Splits for GVM classes to GCM bands `transporthelpers.py` <ARTIC_ALLOCATION_MATRIX> - split GVM classes into GCM bands (14-20t, 20-28t, 28-34t, 34-40t, 40-50t, 50-60t)
 - `fill on the total artic truck by GVM class (41%) and total trucks based on 2019 splits, and calculation of trucks into classes Medium, Heavy, Very Heavy (Rigid trucks by GVM class + artic truck by GCM bands)........`

# Detailed method

## 1 Existing transport asset List

EECA has compiled a list of current transport technologies and fleet composition for the 2023 base year, reflecting the distribution of energy service demand across the New Zealand vehicle fleet. This list is grounded in data from the Ministry of Transport (MoT)’s Vehicle Fleet Model (VFM) (VFM202405 outputs summary V3: https://www.transport.govt.nz/statistics-and-insights/vehicle-fleet-model/sheet/updated-future-state-model-results), MoT’s Annual Fleet Statistics, and other reputable data sources, including KiwiRail and the Ministry of Business, Innovation and Employment (MBIE) Energy Balances.

The asset list includes detailed vehicle stock, Bvkt, fuel use(litres), kWh use, and energy consumption (PJ) by a combination of vehicle type (i.e. light passenger vehicles (LPV), light commercial vehicles (LCV), trucks, buses, motorcycles, rail, aviation, shipping), technology type (i.e. Internal Combustion Engine (ICE), BEV, Plug-In Hybrid Electric Vehicle (PHEV), Fuel Cell (FC)), power type (i.e. petrol, diesel, electric), and import status (i.e. new, used).

The transport asset list does not aim to capture every variation or niche vehicle type (such as rare fuel types or specific commercial variants). Instead, these are represented by technology-averaged or generic categories within the model to maintain modelling tractability. In cases where only pilot deployment occurred by the base year (i.e., early-stage electric truck deployments or pilot hydrogen buses), these have not been included due to their low numbers. 

In this 3.0 release we have added another category of trucks, aiming to represent the high utilisation long haul vehicles in the fleet. The split point has been set at 30t GVM to capture just the heaviest vehicles. It should be noted that in 2.0 we used the terms Medium Trucks and Heavy Trucks, but to align with industry terminology we have added a Light Trucks category and moved the vehicles weights accordingly, rather than adding a ‘Very Heavy’ category. 

## 2 Split between North and South Island data

The division of energy service demand between the North and South Islands is determined using a mix of proxies:

 - Road Transport: MoT Regional VKT data in their annual fleet statistics is used as the basis for calculating the split. The detailed data showing VKT based on region and vehicle type are not publicly available | [Source](Table 1.4b - Annual Fleet Statistics)
 - Rail Freight: Assumes all electricity is consumed in Auckland and Wellington, and diesel is split as per rail freight tonnages in MoT freight inter-regional flows | [Source] (MoT FIGS: Rail: https://www.transport.govt.nz/statistics-and-insights/freight-and-logistics/figs-rail/)
 - Rail Passenger: Assumes all diesel is consumed in Auckland and Wellington, and electricity is split as per freight (has an immaterial impact on overall outcomes)
 - Aviation Domestic: MoT Arrival/Departures by Airport (2017/2018 data) used as proxy for fuel consumption in the absence of detailed trip length data | [Source](TIMES-NZ 2.0 inputs)
 - Aviation International: Statistics NZ international arrival data and MoT International Arrivals/Departures data are used to estimate the fuel consumed by the airport | [Source](TIMES-NZ 2.0 inputs)
 - Shipping: We extracted the TIMES-NZ 2.0 splits for now and will be reviewed and updated for the current status based on any significant changes identified by the Assumption Working Group

## 3 Distributing the base year transport demand 

We used the MOT’s Annual Fleet Statistics and New Zealand Transport Agency’s (NZTA) Motor Vehicle Register (MVR) to estimate vehicle stock, Bvkt, and regional Bvkt for the 2023 base year. This bottom-up approach allows us to distribute existing transport demand across vehicle types, technologies, fuel types, and regions (North and South Islands). 

This dataset covers the majority of New Zealand's on-road transport energy demand. For categories where data is more limited (e.g., non-road modes like shipping, aviation, rail, or emerging technologies such as hydrogen trucks), assumptions are made based on the best available data from MBIE Energy Balances, KiwiRail, and Energy End Use Database (EEUD). These assumptions allow us to calibrate total fuel use and transport activity to align with the official historical energy demand reported by the MBIE.

In cases where the MOT provides vehicle categories in aggregated form, we disaggregate VKT, and vehicle counts by fuel type or technology class using market share estimates and registration data from the MVR data. Further disaggregation of VKT into utilisation tertiles (discussed below) was undertaken using extra VKT data provided by MoT for the purpose of improving the model.

## 4 VKT disaggregation

To try and better reflect that vehicle use will change the TCO equation, vehicle utilisation bands we created. For each vehicle class, vehicle counts are evenly split into low, medium, and high-utilisation tertiles. Each tertile of each vehicle class is given a conditional mean VKT using data provided by MoT. These figures are then balanced against the overall VKT figures given in the MoT Annual Fleet Statistics. 

Please note that these values are averaged over the life of the vehicle. New vehicles (particularly trucks) do travel greater distances while new, which is then balanced by the lower distances they travel later in life. For technologies in early deployment (e.g., BEVs and FCEVs), VKT is proportionally allocated using known fleet counts from MVR and technology-specific energy use per kilometre assumptions (e.g., kWh/km or MJ/km). 

Non-road modes (aviation, rail, shipping) are incorporated using available MBIE and KiwiRail data: 
 - MBIE Energy Balances  (for domestic/international aviation in PAX or PJ and shipping in PJ)
 - KiwiRail  (for rail passenger and freight demand)

We further validate the final 2023 transport sector demand distribution against MBIE’s energy balance tables and EEUD transport data to ensure the consistency and completeness of the base year representation. Aligning the classification and data treatment with MoT and MBIE sources also allows for seamless integration with forward-looking demand and technology scenarios, providing consistency across historical, current, and future transport sector modelling inputs.

## 5 Productivity penalty 

To represent the need for Heavy trucks to carry large payloads, we have applied a productivity penalty to BEV trucks due to the weight of their batteries. This is applied as a decrease in VKT per vehicle, resulting in the model needing to purchase more BEV trucks to do the same job as diesel or hydrogen. 

The weight difference was determined by removing the estimated weight of the powertrain and replacing these with the weight of an EV drivetrain and battery. Power train weights were sourced from ICCT.  Base year battery weights used 160Wh/kg (from a current day XCMG), moving to 400Wg/kg in 2040. This figure is from IDTechEX as their 2030 ‘state of the art’ density, we have pushed 10 years to conservatively reflect the delay in operationalising the technology. This result in a 13% penalty in 2030, gradually reducing to 3% in 2040.

Hydrogen trucks were assumed to be the same weight as their ICE counterparts. 

## 6 Transport cost assumptions

Capital (CAPEX) and fixed operating and maintenance (FIXOM) costs for light vehicles in the model are primarily derived from EECA’s Total Cost of Ownership (TCO) Tool  using a curated list of top-selling models across multiple technology types and vehicle categories. Vehicles are classified by category (e.g. car, SUV, ute, van, bus, motorcycle, truck), use type (e.g. LPV, LCV, bus, motorcycle, light, medium, heavy truck), and technology (e.g. petrol ICE, diesel ICE, hybrid, plug-in hybrid, battery electric vehicle, and hydrogen fuel cell). For each representative model, key cost components are recorded, including purchase price (capital cost), servicing costs, tyre costs, and a combined per-kilometre operating cost.

Truck costs are sourced from publicly available sales data where possible, as well as aggregated internal EECA data. Dual fuel heavy trucks are determined by the price of the diesel truck plus $150,000 for the dual fuel system . Operating costs were assumed the same as a diesel truck.

NREL was used as a source for maintenance for vehicles not in the TCO tool. These costs do not include battery or fuel cell replacements, which may become significant in the cost of these vehicles given we are modelling their entire lifespan. We’re interested on your thoughts if these should be added, which vehicle classes they would be relevant for, and projected costs. 

TIMES-NZ 2.0 did not include the cost of domestic and international shipping. For the 3.0 update we have extracted CAPEX and OPEX figures from Calculate Total Cost of Ownership (TCO) for decarbonization of vessels | Mærsk Mc-Kinney Møller Center for Zero Carbon Shipping . TIMES-NZ shipping technologies are based on Heavy fuel oil, so the most relevant category is Vessel 1 - ICE – LSFO (Low Sulfur Fuel Oil).  Little reliable data was found for alternative technologies, anything that can be shared in this area would be of interest to us.

There is also limited publicly available data for rail costs. One data point is from media releases relating to the Stadler and KiwiRail contract for 57 mainline locomotives .  Any other data of alternative technology costs and capabilities would be appreciated.

## 6 Fuel efficiency

Fuel efficiencies for the base year technologies were determined using the below equation and listed in Table 8. VKT figures come from our breakdowns discussed above, and fuel used from MBIE energy balance tables split per the EEUD. This method allows for simple balancing between these two data sets.

Fuel Efficiency =  (Vehicle kilometres travelled (Bvkt))/(Fuel Used (PJ))

TSome technologies weren’t present in the data so were determined manually – for LCV Hybrids and ICE motorcycles we used the relativity in between ICE LPVs and the LPV version of their respective technology. Hydrogen trucks used publicly claimed fuel capacities and range to determine fuel consumption. For Medium trucks the Hyundai Xcient was used , for Heavy trucks the GBV Semi .

## 7 Lifetime of transport technologies

To reflect differences in how vehicles exit the fleet over time, we allocated the total fleet across utilisation bands, referred to as tertiles based on their initial share and their expected survival as vehicles age. Each tertile’s base share is calculated from the overall fleet and adjusted using an age-based decay factor that models the likelihood of a vehicle remaining in the fleet as it gets older.

The decay factor is defined as:

age based decay factor = 1 - age /(max_age)

This factor declines from 1 at age 0 to 0 at the maximum observed vehicle age. To allow for faster turnover in higher tertiles, this decay factor is raised to the 

power of the tertile index, resulting in the following weighting formula: 

〖weight〗_t=〖base_share〗_t×(1-age/(max_age))^t

These weights are then normalised within each age group to preserve total fleet size while reflecting different survival patterns across tertiles. Using this weighted distribution, the scrappage age is calculated for each vehicle type and tertile. This is defined as the age by which 70% of vehicles in that group have exited the fleet, representing a higher than median estimate of fleet turnover. It reflects differences in how quickly vehicles are typically retired across segments and provides insight into the upper range of vehicle survival patterns.

## 9 Mode and fuel shares

Other required parameters that are not included in the external data are applied by assumption. These assumptions on Vehicle max annual travel distance (000km) and Mode or fuel share have been extracted from TIMES-NZ 2.0, where available. The following fuel share figures have been assigned to some of the technologies.

## 10 Demand projections

The existing demand projections for Kea and Tūī scenarios were also extracted from TIMES-NZ 2.0 and listed separately, these will be reviewed and updated based on any significant changes identified by the Narrative Working Group.

## 11 Future transport technologies

The base of future transport technologies made available to the model is based on the MOT’s VFM, with adjustments for future capital and O&M costs derived from the National Renewable Energy Laboratory (NREL) Annual Technology Baseline (ATB) data . This includes a list of future vehicle types (ICE, BEV, PHEV, and FC), with detailed estimates of investment costs (CAPEX), fixed operating and maintenance costs (FIXOM), fuel efficiency, AFA, vehicle lifetime, and earliest availability years.

We made the following adjustments and additions to the baseline vehicle technology data:
 - We included cost projections from NREL for advanced ICEs, BEVs, PHEVs, and hydrogen FC vehicles across light, medium, and heavy vehicle classes.
 - We used NREL learning curve assumptions to model CAPEX and FIXOM costs for future transport technologies in TIMES-NZ 3.0 scenarios over time.

### Learning curves for transport technologies

Data from the NREL Annual Technology Baseline (ATB) was used to generate learning curves for key vehicle technologies, providing projections of CAPEX and FIXOM costs over time based on assumed technological advancement. The NREL projections extend from 2023 to 2050 across three scenarios, reflecting different rates of innovation and market development.
 - Conservative: Minor technology changes; low R&D investment.
 - Moderate: Widespread innovation consistent with current investment trends.
 - Advanced: Strong technology improvements driven by increased R&D investment.
For TIMES-NZ, the Moderate scenario was used for the Kea pathway, and the Conservative scenario was used for Tūī, consistent with previous practice in TIMES-NZ 2.0 electricity supply sector. The Advanced scenario is not currently used, reflecting the fact that New Zealand’s market maturity and supply chains are behind those of the US.

Learning curves were applied to adjust CAPEX and FIXOM costs for vehicles meeting the following criteria:
 - Vehicles representing future technologies that are not yet mature in the 2023 fleet (e.g., heavy-duty hydrogen trucks, long-range BEVs)
 - Technologies with market entry years of 2025 or later
 - Only future BEV, PHEV, and FCEV technologies have cost reductions applied
Technologies already widely available in the base year (e.g., ICE petrol vehicles) retain static costs across the model horizon.
The NREL transport categories were mapped to TIMES-NZ vehicle types 

### Cost application methodology

To apply the learning curves:
 - Percentage indices for changes in CAPEX were calculated relative to the base year, using NREL projections.
 - The base year for cost application is set to 2023, aligned with the TIMES-NZ 3.0 fleet base year.
 - For projected CAPEX, the NREL-derived percentage indices were applied to the base capital cost.
 - FIXOM costs were extracted from NREL for the base year, where data is not available in the NZ context.

### Potential vehicle deployment limits
The future potential for the deployment of emerging technologies is constrained by the restraint on light EV uptake. The below EV import limits for LPVs were extracted from TIMES-NZ 2.0 and need to be reviewed and updated for the current status, or the possibility of introducing a supply constraint.

## 12 Chargers
For battery electric and plug-in hybrids, each vehicle has a charger cost added to their CAPEX, with prices from IDTechEX. Most vehicles are assumed to charge overnight and are assigned an appropriately sized charger for this. 
The exception is for heavy trucks which we have assumed charge at the depot, sharing a 500kW charger between 5 trucks. This is to ensure that electric vehicles in this category are capable of completing high utilisation duty cycles, while also trying to reflect that chargers will be shared amongst vehicles to ensure their own utilisation. 
In future iterations of the model, we would like to have a charging network made up of multiple nodes, however this is out of scope for this release.
Cost of hydrogen infrastructure is considered by the model in determining the delivered cost of fuel, so is not included in any vehicle CAPEX figures.

## 13 Emissions factors

Emissions factors for each thermal fuel are sourced from the Ministry for the Environment’s Measuring Emissions Guide 2025 . These are all converted to kt CO2e/PJ equivalents using gross calorific values from MfE’s data for use in modelling. The electricity supply portion of the model will handle the electricity emission factor for transport electricity.

## 14 Biofuel/Hydrogen supply
This will be covered in a separate document at a later date. 

