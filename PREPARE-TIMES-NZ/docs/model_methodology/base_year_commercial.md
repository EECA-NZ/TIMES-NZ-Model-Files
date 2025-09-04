# Base year commercial demand 

```
Calibrating the TIMES NZ base year data for commercial sector
```


This documentation describes the methods used to create commercial base year data.

Commercial base year user config file is found at `data_raw/user_config/VT_TIMESNZ_COM.toml`.
The key data processing script is found at `scripts/stage_2_baseyear/baseyear_commercial_demand.py`.
The reshaping script, which generates subtables used to generate the final excel file, can be found at `scripts/stage_4_veda_format/create_baseyear_com_files.py`.

The base year commercial data is intended to reflect the distribution of 2023 energy end use across all sectors in New Zealand. These commercial technologies should be available to the model to meet future demand, but with enough information (efficiency, lifetime, availability factors, capital costs, etc.) that the model will retire technologies at appropriate points and can make least-cost decisions on fuel switching and utilisation across demand segments.

We have improved on TIMES-NZ 2.0 by adding data centre energy demand. This reflects how New Zealand keep face with data centre energy demand growth due to rising digital demand, cloud services, and AI computing workloads. Also revisited other adjustments to the EEUD data, equipment lifetime, capital costs, and operating and maintenance costs.

# Raw data used 

All raw data from external sources is stored in `data_raw/external_data/`
 
### Stats NZ 

Consumer Price Index:
 - `cpi/cpi_infoshare.csv` | [Webpage](https://infoshare.stats.govt.nz/QueryUpload.aspx) 
 - (Load the query stored at `statsnz/infoshare_queries/infoshare_cpi_query.tqx`)
 - `cgpi/cgpi_infoshare.csv` | [Webpage](https://infoshare.stats.govt.nz/QueryUpload.aspx) 
 - (Load the query stored at `statsnz/infoshare_queries/infoshare_cgpi_query.tqx`)
 - Used for the functions at `library/deflator.py` to deflate price data to different base years as needed.
GDP
 - `gdp/gdp_infoshare.csv` | [Webpage](https://infoshare.stats.govt.nz/QueryUpload.aspx) 
 - (Load the query stored at `statsnz/infoshare_queries/infoshare_gdp_query.tqx`)
 - Used for allocating energy demand across the North and South Islands for commercial subsectors Office Blocks and WSR
Population 
 - `population/erp_regions.csv` | [Webpage](https://infoshare.stats.govt.nz/QueryUpload.aspx) 
 - Used for allocating energy demand across the North and South Islands for commercial subsector Other

### GNS
`gns/2025-08-27-geothermal-features.xlsx` https://data.gns.cri.nz/geothermal/ EEUD includes a large amount of unallocated geothermal, and this has been split across subsectors using the GNS New Zealand geothermal use database.  Percentages were derived based on the geothermal capacity by primary use and sector descriptions as given in the database and then applied these percentages to the EEUD unallocated geothermal demand. 

### Educationcounts
 - `educationcounts\1-Time-Series-for-Trend-Analysis-1996-2024.xlsx` https://www.educationcounts.govt.nz/statistics/school-rolls Used for allocating energy demand across the North and South Islands for commercial subsector Education

### MOH
 - `moh/LegalEntitySummaryNGOHospital.csv` https://www.health.govt.nz/regulation-legislation/certification-of-health-care-services/certified-providers
 - `moh/LegalEntitySummaryPublicHospital.csv` https://www.health.govt.nz/regulation-legislation/certification-of-health-care-services/certified-providers
 - Used for allocating energy demand across the North and South Islands for commercial subsector Healthcare


### EECA

Energy End Use Data 2023:
 - `eeca_data/eeud/Final EEUD Outputs 2017 - 2023 12032025.xlsx` | [Webpage](https://www.eeca.govt.nz/insights/data-tools/energy-end-use-database/) | [File](https://www.eeca.govt.nz/assets/EECA-Resources/Research-papers-guides/EEUD-Data-2017-2023.xlsx)
 - Used for estimating energy consumed (PJ) by most commercial technologies

# Assumptions used

All coded base transport assumptions are stored in `data_raw/coded_assumptions/commercial_demand/`.

These include: 

 - Technology lifetime `tech_lifetimes.csv`. Equipment lifetimes are taken as estimated useful life (years) from the Inland Revenues General depreciation rates October 2024 document. 
 - Capital and Operation costs of technologies `tech_fuel_capex.csv`, `tech_fuel_opex.csv`. The capital costs represent the upfront expenditure required to install each technology in a typical New Zealand commercial building context. The sources for these estimates include EECA research and case studies, government datasets, and New Zealand supplier price lists. Operating and maintenance costs assumptions for some technologies were extracted from TIMES-NZ 2.0 model
 - Technology efficiencies `tech_fuel_efficiencies.csv`. Energy efficiencies of most technologies came from the TIMES-NZ 2.0 model. Efficiencies for internal combustion engine (land transport), stationary engines, and cooking ovens were updated using literature reviews.
 - Availability factors `tech_afa.csv`. Availability factors were estimated separately for each commercial subsector in TIMES-NZ 2.0. The calculation was based on the underlying load curves prior to normalisation (i.e., before scaling so that all time-slice fractions sum to 1.0). This ensures that the availability factors reflect the absolute intensity and timing of energy use rather than just the relative distribution. For most end-uses, it was assumed that technologies operate concurrently during business operating hours and thus follow the sectoral load curve. Exceptions were introduced for end-uses with different utilisation patterns: space heating and cooling were scaled down to reflect their seasonal operation, while mobile motive power (e.g., equipment used intermittently) was assigned a lower availability factor than the primary continuously operated technologies.
 - Reginal splits by fuel and sector `regional_splits_by_fuel.csv`, `regional_splits_by_sector.csv`. Energy demand across the North and South Islands was allocated by commercial subsector using raw data from Stats NZ, MOH, GNS, and Educationcounts. Natural gas and geothermal energy use are assumed to be 100% in the North Island, reflecting the fact that both the gas network and geothermal resources are located exclusively there. 
 - Lights splits across Incandescent, Fluorescent, and LED. Based on TIMES-NZ 2.0. `light_splits.csv`
 - Fuel splits by sector and enduse `fuel_splits_by_sector_enduse.csv`. This is for unallocate EEUD energy demand of Biogas, Geothermal, Deisel, Petrol, Natural Gas.
 - Fuel market share for technologies `fuel_market_share.xlsx`. Market shares for technologies and fuels for each demand of each sub-sector were added in TIME-NZ 2.0 model to avoid near complete uptake of technologies at an unrealistic rate. 
 - Fuel emissions `emissions.csv`. 


# Detailed method

## 1 Historic Demand

Fuel energy demand for the 2023 year has primarily been sourced from the Energy Efficiency and Conservation Authority’s (EECA) Energy End Use Database (EEUD), for the period ending 2023. 
The EEUD’s stationary energy module uses a top-down approach: start with Ministry of Business, Innovation and Employment’s (MBIE) sector-by-fuel totals and then split them into finer categories using the best available information. In practice, for each combination of sector and fuel, EECA applies percentage splits (by subsector, end-use, and technology) to the MBIE total, yielding disaggregated estimates of delivered energy use. These percentage splits (the low-level detail) come from the modifier datasets, either recent sector studies (if available) or the 2007 baseline proportions as a default. Because many modifier inputs come from past years (e.g. 2007), EECA scales them to the current year’s level before deriving proportions. This is done using growth scalars that act as proxies for energy use growth in each sector. For commercial sector, inflation-adjusted GDP is used to scale energy use over time.  
Commercial categories in TIMES-NZ are defined combining a few EEUD categories together. 

 - `Education`: Education and Training: Pre-School, Primary and Secondary; Education and Training: Tertiary Education and Other Education
 - `Healthcare`: Health Care and Social Assistance
 - `Office Blocks`: Financing, Insurance, Real Estate and Business Services; Information Media and Telecommunications; Local Government Administration; Public Administration and Safety
 - `Warehouses, Supermarkets and Retail (WSR)`: Accommodation and Food Services; Retail Trade – Food; Transport, Postal and Warehousing (Commercial Non-Transport); Wholesale and Retail Trade - Non-Food; Wholesale Trade - Food
 - `Other`: Arts, Recreational and Other Services; Building Cleaning, Pest Control and Other Support Services; Defence
 - `Other (to be allocated to the above)`: NULL (unallocated)


## 2 Data centre energy demand

The energy use of data centres would be included in the ANZSIC code J “Information Media and Telecommunications. However, MBIE only receives actual retail sales data broken down into ANZSIC codes and data centre electricity use is not separately estimated or disaggregated. Given the data provided to MBIE there isn’t a clear way to isolate electricity going to data centres. Therefore, the data centre energy demand is sourced from a study done by NZTech  and MBIE’s Electricity Demand and Generation Scenarios (EDGS) 2024 model. 

There are 56 operating facilities with a combined ≈ 104 MW of deployable capacity, drawing 236 GWh yr-¹ (0.62 % of national demand) in New Zealand. 58 % of sites are “micro” (< 1 MW), while most new megawatts belong to a handful of hyperscale or large colocation campuses.  , 
TIMES-NZ 3.0  considered the NZTech’s approach which is build based on a bottom-up inventory of every New Zealand data-centre, converting each public design rating to a realistic “deployable” figure using an 89 % fitted-to-design proxy where needed, removes any MW that are merely leased inside another site, and cross-checks against public data, yielding a national total of 104 MW deployable capacity. To estimate electricity use it assumes 80 % of that space is occupied and servers draw 25% of name-plate power, then applies the country’s median PUE of 1.3 and scales for the year, producing about 236 GWh, or ~0.6 % of NZ’s 2024 demand. 
Further disaggregation of base-year capacity, based on the end-use energy profile (IT equipment load, cooling system, power infrastructure, and building services) will be conducted when implementing it into the TIMES-NZ technologies. 

`Data centre energy demand is yet to be included in the upstream processing`

## 3 Other adjustments to the EEUD data 

EEUD includes some unallocated amounts of biogas, diesel, geothermal, and petrol energy use. We have allocated these unallocated quantities of biogas, diesel, and petrol energy use to the TIMES-NZ “Other” sector. For petrol and diesel, the end use technology is assumed to be non-transport “Motive Power, Mobile”. EECA identifies this as a significant stationary energy end-use category, largely covering off-road, or recreational uses (i.e., forklifts, grounds-keeping equipment, and recreational marine vehicles).  
For biogas, Nelson Hospital operates a 2.0 MW landfill gas–fired boiler that supplies over 60% of the hospital’s thermal energy needs for heating, hot water, and steam.  The Nelson Tasman Regional Landfill Business Unit (NTRLBU) sells landfill gas from York Valley to Health NZ, with an expected annual supply of about 2 million m³, equivalent to approximately 40 % of the gas recovered from the landfill.  Typical landfill gas containing around 50 % methane has a lower heating value of about 18–19 MJ per m³, giving the hospital’s annual landfill gas consumption an energy content of roughly 0.037 PJ. ,  This demand is captured by EECA Regional Energy Transition Accelerator (RETA) for process heating.  applications at the hospital.  Therefore, a 0.037 PJ of EEUD unallocated biogas was allocated to the “Healthcare” sector “Intermediate Heat (100-300 C), Process Requirements”.
EEUD includes a large amount of unallocated geothermal, and this has been split across subsectors using the GNS New Zealand geothermal use database.  Percentages were derived based on the geothermal capacity by primary use and sector descriptions as given in the database and then applied these percentages to the EEUD unallocated geothermal demand. 
EEUD also includes some amount of natural gas within Transport, Postal and Warehousing (Commercial - Non-Transport) WSR sector, which has not been allocated to any end use or technology. Given the operation of this sector, the total amount of natural gas is assumed to be use for motive power, mobile. Tracing back to EEUD original version in 2006-2007 further clarifies this. Table 4 includes those adjusted fuel demand by TIMES sector, end use, and technology. Within the office sector, natural gas motive power (mobile) was merged with LPG, since it accounted for only a small portion of total demand.


## 4 Island split

Energy demand across the North and South Islands was allocated by commercial subsector using appropriate proxy indicators:

 - Education: Number of enrolled students by island (`NI`: 78.7% `SI`: 21.3%)
 - Healthcare: Number of hospital beds by island   (`NI`: 75.3% `SI`: 24.7%)
 - Office Blocks: GDP  of the relevant subsectors (`NI`: 78.5% `SI`: 21.5%)
 - WSR: GDP of the relevant subsectors (`NI`: 81.6% `SI`: 18.4%)
 - Other: Population  (`NI`: 76.4% `SI`: 23.6%)


## 5 Load curves

The commercial load curves currently used are from the TIMES-NZ 2.0 model. These were developed using the EECA energy audit database as the primary source. Because the commercial subsectors are defined at a relatively broad level, each subsector’s load curve was constructed in a structured, multi-step process. Representative buildings were selected from audit data to capture typical demand behaviour for each subsector.

 - Education: high schools and universities
 - Healthcare: several hospitals
 - Office blocks: large several large office buildings, some smaller government buildings, EECA office building load curve research by ESP Consulting
 - WSR: multiple warehouses, supermarkets, retail stores, shopping malls
 - Other: matched to the WSR profile, due to the broadness and uncertainty of sector

Each representative building had an hourly or sub hourly electricity demand profile from audits. These raw profiles were grouped into a time-slice structure reflecting weekday/weekend and day/night/peak periods and expressed as a share of daily demand. These daily shares were then mapped onto the annual fraction of each time slice (YRFR) to scale the daily load shares into annual fractions for each building. The building-level profiles were averaged together, with weights reflecting each end-user’s share of energy use within the subsector (for example, retail contributes more to WSR demand than warehouses or supermarkets). The subsector COM_FR values were finally normalised so that all slices sum to 1.0, ensuring they represent a complete distribution of annual demand. In most commercial subsectors, all end-use technologies (computers, lights, heating/cooling) were assumed to follow the same subsector load curve, since they typically operate together during business hours. An exception was made for space heating and cooling in Healthcare and Other sectors, where seasonal adjustments were applied to capture climate-driven variations in heating and cooling demand.

## 6 Demand projections

We assume increased energy service demand for data centres and professional services in the Transformation scenario. These will be reviewed and updated based on any significant changes identified by the Narrative Working Group.

Population growth assumptions remain the same in each scenario, following central projections, therefore the energy service demand from population driven subsectors (Education and Healthcare) remain the same in both scenarios. Also, there is potential to change individual subsectors to grow at a higher rate than GDP, as they may be expected to grow faster than other parts of the economy. This would likely affect WSR most, as we see an increased demand growth in professional services.

Data centre demand growth matches the EDGS 2024 Reference scenario.	Increased demand for AI and other new technologies means data centre utilisation increases. 

## 7 Future commercial technologies

New technologies are based on proven commercially available technology (TRL 7 and above) that have been, or will be, installed and commissioned in New Zealand through initiatives such as EECA’s technology demonstration fund and the Government Investment in Decarbonising Industry (GIDI) and haven’t been included in TIMES 2.0 existing technology. It is recommended that this list is reviewed regularly to ensure that all commercially available new technologies are considered in TIMES.

## 8 Emissions factors

Emissions factors for each thermal fuel are sourced from the Ministry for the Environment’s Measuring Emissions Guide 2025 . These are all converted to kt CO2e/PJ equivalents using gross calorific values from MfE’s data for use in modelling. The electricity supply portion of the model will handle the electricity emission factor for commercial electricity. 

