# Base year demand 

The base year commercial data is intended to reflect the distribution of 2023 energy end use across all sectors in New Zealand. These commercial technologies should be available to the model to meet future demand, but with enough information (efficiency, lifetime, availability factors, capital costs, etc.) that the model will retire technologies at appropriate points and can make least-cost decisions on fuel switching and utilisation across demand segments.

TIMES-NZ requires detailed information on the existing commercial technologies, including: 
 - Energy efficiency
 - Lifetime
 - Investment cost ($/kW)
 - O&M cost ($/kW)
 - Availability factor 
 - Installed capacity (GW)
 - Island splits

We have improved on TIMES-NZ 2.0 by adding data centre energy demand. This reflects the growth of New Zealand’s data centre energy demand due to rising digital demand, cloud services, and AI computing workloads. Also revisited other adjustments to the EEUD data, equipment lifetime, capital costs, and operating and maintenance costs.


## Historic demand 

Fuel energy demand for the 2023 year has primarily been sourced from the Energy Efficiency and Conservation Authority’s (EECA) Energy End Use Database (EEUD)[^eeud], for the period ending 2023. 

The EEUD’s stationary energy module uses a top-down approach: start with Ministry of Business, Innovation and Employment’s (MBIE) sector-by-fuel totals and then split them into finer categories using the best available information. In practice, for each combination of sector and fuel, EECA applies percentage splits (by subsector, end-use, and technology) to the MBIE total, yielding disaggregated estimates of delivered energy use. These percentage splits (the low-level detail) are based on data from either EECA’s internal research and modelling of energy profiles for given sectors (mainly 2020 estimates), or 2007 data estimates for given sectors.  EECA scales these estimates to derive a current year estimate.  The scaler for most sectors is sector-specific GDP values.  The scalars act as a proxy for energy use growth over time.  

Commercial categories in TIMES-NZ are defined combining a few EEUD categories together. Table 1 presents TIMES-NZ commercial sectors and EEUD sectors mapping. Some unallocated demand in EEUD was allocated to a TIMES-NZ “Other” sector. 

[^eeud]: EECA | EEUD: <https://www.eeca.govt.nz/insights/data-tools/energy-end-use-database/>


```{list-table} TIMES-NZ and EEUD sector mapping
:header-rows: 1
:name: tab-commercial-sector-map
* - TIMES-NZ commercial sector
  - EEUD commercial sector
* - Education
  - Education and Training: Pre-School, Primary and Secondary; Education and Training: Tertiary Education and Other Education
* - Healthcare
  - Health Care and Social Assistance
* - Office Blocks 
  - Financing, Insurance, Real Estate and Business Services; Information Media and Telecommunications; Local Government Administration; Public Administration and Safety; Defence
* - Warehouses, Supermarkets and Retail (WSR)
  - Accommodation and Food Services; Retail Trade – Food; Transport, Postal and Warehousing (Commercial - Non-Transport); Wholesale and Retail Trade - Non-Food; Wholesale Trade - Food
* - Other
  - Arts, Recreational and Other Services; Building Cleaning, Pest Control and Other Support Services 
* - Other (to be allocated to the above – assumptions applied)
  - NULL (unallocated)
* - Data centres
  - This is currently not defined in EEUD
```


```{list-table} Commercial sector historic demand
:header-rows: 1
:name: tab-commercial-historic-demand
* - Sector
  - Energy (PJ)
  - Energy share (%)
* - Education
  - 3.17
  - 6%
* - Healthcare
  - 4.77
  - 9%
* - Office Blocks 
  - 15.46
  - 28%
* - Warehouses, Supermarkets and Retail (WSR) 
  - 21.24
  - 38%
* - Other
  - 3.79
  - 7%
* - Other (to be allocated to the above)
  - 7.35
  - 13%
* - Total
  - 55.78
  - 100%
```

## Data centre demand 


MBIE/EEUD data does not recognise the energy use of Data Centers. The only known data available on data centre energy use is from NZTech[^nztech_2025] and MBIE’s Electricity Demand and Generation Scenarios (EDGS) 2024 model[^mbie_edgs]. 

There are 56 operating facilities with a combined ≈ 104 MW of deployable capacity, drawing 238 GWh per year (0.62 % of national demand) in New Zealand[^nz_data_centre_facilities]. While 58% operate with less than 1 MW each, most of the new capacity is being delivered through a small number of very large developments, particularly hyperscale (10–100+MW; Global cloud platforms, AI training) campuses for global cloud providers and large colocation (0.5–20 MW; Multi-tenant facilities) sites serving multiple clients[^nztech_data_centre_report].



[^nz_data_centre_facilities]: [New Zealand Data Centers - 55 Facilities from 46 Operators](https://www.datacentermap.com/new-zealand/)


[^nztech_data_centre_report]: NZTech 2025: [Empowering Aotearoa New Zealand’s Digital Future: Our national data centre infrastructure](https://technewzealand.org.nz/wp-content/uploads/sites/8/2025/09/NZTech-Data-Centres-Report-Final-DIGITAL-002.pdf)


TIMES-NZ 3.0 considered NZTech’s approach which is built based on a bottom-up inventory of every New Zealand datacentre, adjusting the numbers to reflect realistic deployable capacity rather than maximum design ratings. Where needed, it applied 89% deployable capacity. This excluded MWs already leased within other facilities to avoid double counting, and cross-checked results against public sources. This yielded a national total of 104 MW deployable capacity. To estimate electricity use we assume 80% of that space is occupied and servers draw 25% of name-plate power. We then apply the country’s median Power Usage Effectiveness (PUE)[^pue_explain] of 1.3. This estimates about 238 GWh (or 0.856 PJ), or ~0.6 % of NZ’s 2024 demand. This total data centre demand 0.856 PJ is allocated in TIMES-NZ 3.0 as a new subsector, and an equivalent amount is deducted from TIMES-NZ Office Blocks to avoid double-counting.

Further disaggregation of base year capacity, based on the end use energy profile (IT equipment load, cooling system, power infrastructure, and building services) is conducted when implementing it into the TIMES-NZ technologies. {numref}`tab-datacentre_distribution` includes energy distribution in a more efficient hyperscale style centre with a PUE of 1.3. 


```{csv-table} Energy distribution of typical vs hyperscale-style data centre
:name: tab-datacentre_distribution
:header-rows: 1
Component ,Share of Total Energy (%) — PUE 1.3 ,Notes 
"IT Equipment (incl. servers, storage, networking) ",~77%,Core computing load including storage and network gear 
Cooling Systems ,~15%,"CRACs, chillers, air/liquid systems "
Power Infrastructure ,~6%,"UPS inefficiency, PDU losses, power conversion "
Building Services ,<1%,"Lighting, security, fire suppression "

```



[^nztech_2025]: NZTech (2025). [Empowering Aotearoa New Zealand’s Digital Future: Our national data centre infrastructure](https://technewzealand.org.nz/wp-content/uploads/sites/8/2025/09/NZTech-Data-Centres-Report-Final-DIGITAL-002.pdf)
[^mbie_edgs]: MBIE | EDGS 2024: <https://www.mbie.govt.nz/assets/electricity-demand-and-generation-scenarios-report-2024.pdf>

[^pue_explain]: PUE = Total Facility Energy / IT Equipment Energy. An ideal PUE is 1.0, meaning all electricity goes to IT equipment (no overhead). In practice, some energy is always consumed by cooling, power conditioning, and other support systems.




## Unallocated EEUD demand

EEUD includes some unallocated amounts of biogas, diesel, geothermal, and petrol energy use. We have allocated these unallocated quantities of biogas, diesel, and petrol energy use to the TIMES-NZ “Other” sector. For petrol and diesel, the end use technology is assumed to be non-transport “Motive Power, Mobile”. EECA identifies this as a significant stationary energy end-use category, largely covering off-road, or recreational uses (i.e., forklifts, grounds-keeping equipment, and recreational marine vehicles for adventure tourism)[^eeud_insights].

[^eeud_insights]: EECA | [Energy End Use Database Insights 2023 data](https://www.eeca.govt.nz/assets/EECA-Resources/Research-papers-guides/Energy-End-Use-Database-Insights.pdf)

For biogas, Nelson Hospital operates a 2.0 MW landfill gas–fired boiler that supplies over 60% of the hospital’s thermal energy needs for heating, hot water, and steam[^nelson_hospital_landfill_gas]. The Nelson Tasman Regional Landfill Business Unit (NTRLBU) sells landfill gas from York Valley to Health NZ, with an expected annual supply of about 2 million m³, equivalent to approximately 40% of the gas recovered from the landfill[^nelson_hospital_ditches_coal]. Typical landfill gas containing around 50% methane has a lower heating value of about 18–19 MJ per m³, giving the hospital’s annual landfill gas consumption an energy content of roughly 0.037 PJ[^biogas_miomethane_iea]. This demand is captured by EECA Regional Energy Transition Accelerator (RETA) for process heating[^reta_nelson_marlborough_tasman] applications at the hospital. Therefore, a 0.037 PJ of EEUD unallocated biogas was allocated to the “Healthcare” sector “Intermediate Heat (100-300 C), Process Requirements”.

[^nelson_hospital_landfill_gas]: Bioenergy facilities directory | [Nelson Hospital - landfill gas from York Valley Landfill](https://www.bioenergyfacilities.org/facility/nelson-hospital-landfill-gas-from-york-valley-landfill)
[^nelson_hospital_ditches_coal]: RNZ | [Nelson Hospital ditches coal now heating fully powered by landfill gas](https://www.rnz.co.nz/news/national/565133/nelson-hospital-ditches-coal-now-heating-fully-powered-by-landfill-gas)
[^biogas_miomethane_iea]: IEA | [An introduction to biogas and biomethane](https://www.iea.org/reports/outlook-for-biogas-and-biomethane-prospects-for-organic-growth/an-introduction-to-biogas-and-biomethane)
[^reta_nelson_marlborough_tasman]: EECA | [Regional Energy Transition Accelerator (RETA) Nelson, Marlborough, Tasman – Phase One Report](https://www.eeca.govt.nz/assets/EECA-Resources/Co-funding/RETA-Nelson-Marlborough-Tasman-Phase-One-Report.pdf)



The EEUD includes a large amount of unallocated geothermal, and this has been split across subsectors using the GNS New Zealand geothermal use database[^gns_database]. Percentages were derived based on the geothermal capacity by primary use and sector descriptions as given in the database and then applied these percentages to the EEUD unallocated geothermal demand. 
[^gns_database]:  GNS Science | [New Zealand Geothermal Use Database](https://data.gns.cri.nz/geothermal/)


EEUD also includes some amount of natural gas within Transport, Postal and Warehousing (Commercial - Non-Transport) WSR sector, which has not been allocated to any end use or technology. Given the operation of this sector, the total amount of natural gas is assumed to be use for motive power, mobile. Tracing back to EEUD original version in 2006-2007 further clarifies this. Table 4 includes those adjusted fuel demand by TIMES sector, end use, and technology. Within the office sector, natural gas motive power (mobile) was merged with LPG, since it accounted for only a small portion of total demand.



```{csv-table} TIMES-NZ commercial sector unallocated 2023 base year demand
:name: tab-commercial_demand_baseyear
:header-rows: 1
TIMES Sector,TIMES Fuel,TIMES end use,TIMES Technology,Demand 2023 PJ,Share of fuel demand (%)
Other,Diesel,"Motive Power, Mobiles",Internal Combustion Engine (Land Transport),4.033,100%
Other,Petrol,"Motive Power, Mobile",Internal Combustion Engine (Land Transport),0.429,100%
Healthcare,Biogas,Process Heat,Boiler,0.037,6%
Other,Biogas,Process Heat,Boiler,0.223,94%
Education,Geothermal,Space Heating,Direct Heat,0.064,3%
Healthcare,Geothermal,Space Heating,Direct Heat,0.239,10%
WSR,Geothermal,Space Heating,Direct Heat,0.71,30%
WSR,Geothermal,Water Heating,Direct Heat,0.729,31%
Other,Geothermal,Space Heating,Direct Heat,0.544,23%
Other,Geothermal,Water Heating,Direct Heat,0.092,4%
WSR,Natural Gas,"Motive Power, Mobile",Internal Combustion Engine (Land Transport),0.254,100%
```

## Island disaggregation

Energy demand across the North and South Islands was allocated by commercial subsector using appropriate proxy indicators:
 - Education: Number of enrolled students by island[^school_rolls]   
 - Healthcare: Number of hospital beds by island[^moh_providers]  
 - Office Blocks: Regional GDP[^rgdp] of the relevant subsectors
 - WSR: Regional GDP of the relevant subsectors
 - Other: Population[^rc_population]  


[^school_rolls]: Education Counts | [School rolls](https://www.educationcounts.govt.nz/statistics/school-rolls)
[^moh_providers]: Ministry of Health | [Certified Providers](https://www.health.govt.nz/regulation-legislation/certification-of-health-care-services/certified-providers)
[^rgdp]: Stats NZ | Infoshare | [Regional Gross Domestic Product – RNA Gross domestic product, by region and industry (Annual-Mar)](https://infoshare.stats.govt.nz/Default.aspx)
[^rc_population]: Stats NZ | Infoshare | [DPE Estimated Resident Population for Regional Council Areas, on 30 June (1996+) (Annual-Jun)](https://infoshare.stats.govt.nz/Default.aspx)

The resulting distribution of demand is shown in {numref}`tab_com_island_demand`.


```{csv-table} Energy end-use share between North Island and South Island
:header-rows: 1
:name: tab_com_island_demand

Sector,NI Share,SI Share
Education,78.70%,21.30%
Healthcare,75.30%,24.70%
Office Blocks,78.50%,21.50%
WSR,81.60%,18.40%
Other,76.40%,23.60%
```

Natural gas and geothermal energy use are assumed to be 100% in the North Island, reflecting the fact that both the gas network and geothermal resources are located exclusively there. 


## Existing commercial end use

The following categories were used to represent end-use demand in the Commercial sector. These were adapted from the EEUD framework with several adjustments: cooking was divided into elements and ovens; lighting was disaggregated into incandescent, fluorescent, and LED; and pumping was combined with electronics, as it represented only a minor share when considered independently. TIMES 2.0 share assumptions were used for the items where further detail was added.


```{csv-table} Existing commercial end use technologies
:header-rows: 1
:name: tab_com_end_use

End use, Found in 
"Intermediate Heat (100-300 C), Process Requirements ","Healthcare, Other"
"Intermediate Heat (100-300 C), Cooking Elements ",WSR 
"Intermediate Heat (100-300 C), Cooking Ovens ",WSR 
Electronics and Other Electrical Uses ,All 
Lighting ,All 
"Low Temperature Heat (<100 C), Space Heating ",All 
"Low Temperature Heat (<100 C), Water Heating ",All 
"Motive Power, Mobile ",All 
"Motive Power, Stationary ",All 
Refrigeration ,"Education, Healthcare, WSR "
Space Cooling ,All 
```
