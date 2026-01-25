# Base year demand

The base year data is intended to reflect the distribution of 2023 energy end use across all industrial sectors in New Zealand. 

TIMES requires detailed information on the existing industrial technologies, including: 
 - Capacity
 - Fuel type
 - Capital costs
 - Asset lifetime 
 - Energy efficiency
 - Region (North Island/South Island)

## EEUD and TIMES alignment
Fuel energy demand for the 2023 year has primarily been sourced from the Energy Efficiency and Conservation Authority’s (EECA) Energy End Use Database (EEUD)[^eeud], for the period ending 2023. 

Additional data for non-energy uses of fuels is sourced from Ministry of Business, Innovation and Employment (MBIE) data[^mbie_balance_tables].  These include natural gas for methanol and urea production, and coal for steel production. These are important to include for modelling and balancing supply and demand of fuels.
The TIMES-NZ model will be adjusted for any plant closures and major decarbonisation projects that have been commissioned between 1 Jan 2023 and 31 July 2025. The model will also be adjusted for high certainty future projects/closures that have publicly announced to happen after 31 July 2025, for example, NZ Steel’s electric arc furnace that is planned for early 2026. These projects are detailed in Appendix A.

Industrial categories in TIMES-NZ are slightly different from those in the EEUD. For the purposes of the model, we combine some smaller categories, such as furniture manufacturing, into “Other”. We also model some larger industries separately, such as Aluminium or Methanol production. The TIMES-NZ industrial sectors and their relationships to EEUD industrial sectors are found in {numref}`tab-eeud_times_map`. 

[^eeud]: EECA | EEUD: <https://www.eeca.govt.nz/insights/data-tools/energy-end-use-database/>
[^mbie_balance_tables]: Energy statistics | Ministry of Business, Innovation & Employment: <https://www.mbie.govt.nz/building-and-energy/energy-and-natural-resources/energy-statistics-and-modelling/energy-statistics>

```{list-table} TIMES-NZ and EEUD sector mapping
:header-rows: 1
:name: tab-eeud_times_map

* - TIMES-NZ industrial sector
  - EEUD industrial sector
* - Aluminium
  - Primary Metal and Metal Product Manufacturing (excluding Iron & Steel)
* - Chemicals
  - Petroleum, Basic Chemical and Rubber Product Manufacturing (excl. Urea and Methanol)
* - Construction
  - Construction
* - Dairy
  - Dairy Product Manufacturing
* - Food and Beverage
  - Food and Beverage Product Manufacturing (excluding Dairy, Meat, Seafood)
* - Iron & Steel
  - Primary Metal and Metal Product Manufacturing (excluding Aluminium)
* - Meat
  - Meat and Meat Product Manufacturing and Seafood
* - Methanol
  - Petroleum, Basic Chemical and Rubber Product Manufacturing (a proportion)
* - Mining
  - Mining
* - Non-Metallic Mineral Product Manufacturing
  - Non-Metallic Mineral Product Manufacturing
* - Other
  - Fabricated Metal Product, Transport Equipment, Machinery and Equipment Manufacturing
* - 
  - Electricity, Gas, Water and Waste Services
* - 
  - Furniture and Other Manufacturing
* - 
  - Industrial - Unallocated
* - 
  - Printing
* - 
  - Textile, Leather, Clothing and Footwear Manufacturing
* - Pulp and Paper
  - Pulp, Paper and Converted Paper Product Manufacturing
* - Urea
  - Petroleum, Basic Chemical and Rubber Product Manufacturing (a proportion)
* - Wood Products
  - Wood Product Manufacturing

```


Demand in the Urea and Methanol sectors have been calculated as a share of total Petroleum, Basic Chemical and Rubber Product Manufacturing use. The remaining demand in this sector is assigned to Chemicals in TIMES-NZ. Demand in the Iron & Steel and Aluminium sectors was calculated as a share of the Primary Metal and Metal Product Manufacturing sector. Methods for these calculations can be found under “Specific sectors and non-energy use” section below.

For reference, each sector’s base year demand and share of total industrial demand can be found in {numref}`tab-ind_by_demand`. Note that this excludes non-energy use, such as Methanex feedstock demand, or coal used as reductant at NZ Steel.  


```{list-table} TIMES-NZ industrial sector 2023 base year demand
:header-rows: 1
:name: tab-ind_by_demand
* - Subsector
  - Demand 2023 PJ
  - Share of Industrial demand (%)
* - Aluminium
  - 17.85
  - 10.56
* - Chemicals (excl. Urea and Methanol)
  - 3.39
  - 2.01
* - Construction
  - 9.41
  - 5.56
* - Dairy
  - 34.44
  - 20.36
* - Food and Beverage
  - 6.81
  - 4.03
* - Iron & Steel
  - 6.62
  - 3.91
* - Meat
  - 7.4
  - 4.38
* - Methanol
  - 20.4
  - 12.07
* - Mining
  - 6.12
  - 3.62
* - Non-Metallic Mineral Product Manufacturing
  - 4.77
  - 2.82
* - Other
  - 15.73
  - 9.3
* - Pulp and Paper
  - 12.52
  - 7.4
* - Urea
  - 2.54
  - 1.5
* - Wood Products
  - 21.1
  - 12.48
* - TOTAL
  - 169.09
  - 100
```

Note that the total demand shown in {numref}`tab-ind_by_demand` will be higher than that reported by the EEUD for 2023. This is due to additional biomass demand estimates added for TIMES-NZ. See “Industrial biomass demand” for more information. NEED TO ADD REFERENCE HERE 



## Specific sectors and non-energy use 

Aluminium, Iron & Steel, Methanol, and Urea production are modelled separately in TIMES-NZ. However, these sectors are not detailed in the EEUD. This section details how we have estimated demand of these sectors, while using the EEUD as our base data. 

### Aluminium

Aluminium demand is the share of electricity demand in the EEUD’s Primary Metal and Metal Product Manufacturing sector used for high temperature process heat. This electricity demand aligns with Tiwai demand values, which are also accessible publicly through Electricity Authority node export data.

### Iron & Steel

The EEUD defines Primary Metal and Metal Product Manufacturing as Tiwai Aluminium Smelter, NZ Steel’s Glenbrook site, and Pacific Steel. This means that the remaining share of Primary Metal and Metal Product Manufacturing can be attributed to Iron & Steel. This means that Pacific Steel demand is included in the TIMES-NZ Iron & Steel sector. There is also some small energy demand for non-ferrous metal product production, and this is captured in “Other”.  

Coal used as reductant at NZ Steel’s Glenbrook site is not captured in the EEUD, as it does not qualify as end use. We add this coal to TIMES-NZ using MBIE’s energy balances, defined as the sum of coal used for other transformation and cogeneration. This gives a total coal use at Glenbrook of 16.4 PJ in 2023, in line with expected Glenbrook demand. Noting that the Electric Arc Furnace will be commissioned early in Q2 2026 and coal use as feedstock is expected to reduce by 50%, this change will also be captured in the model.

Cogeneration coal is modelled separately - we include this in Glenbrook modelling, but as a generation process, rather than demand. The electricity generated by the coal cogeneration is only available for the steel sector. We assume that the cogeneration does not sell back to the grid. 

### Urea and Methanol demand

We model methanol and urea production (at the Methanex and Ballance Kapuni sites respectively) separately from the broader Petroleum, Basic Chemical and Rubber Product Manufacturing sector. Both sites use natural gas for energy and as a feedstock for their products. The energy use of natural gas is directly captured in the EEUD, but the feedstock is not. Feedstock demand is instead sourced from MBIE’s energy balances[^mbie_balance_tables], defined as non-energy use of natural gas. We assume that Ballance and Methanex make up almost all this feedstock demand, which was 38.6 PJ in 2023.

To fully estimate the shares of Ballance and Methanex’s natural gas demand within the sector, we apply the following method: 

1) Ballance and Methanex’s total natural gas demand is sourced from the Gas Industry Company (GIC) data on natural gas consumption for large users[^gic_data]. 
1) We assume 53% of Ballance’s natural gas demand is used for feedstock[^ballance_assumptions]. Methanex feedstock use is estimated as MBIE data on total natural gas feedstock, minus the Ballance feedstock estimates. 
1) We assume 9% of Ballance’s gas is used for cogeneration[^ballance_assumptions]. This is therefore already captured in the electricity module of TIMES-NZ, so is not considered here. We consider the remaining 38% of Ballance’s total gas demand as energy use. This figure was 2.54 PJ in 2023. We allocate this among EEUD compressor[^compressor_note] and reformer demand, aligning with existing EEUD data on compressor demand and allocating the rest to reforming.
1)  Methanex process gas use is estimated as total Methanex gas demand minus their estimated feedstock use. This figure (process gas use) was 20.40 PJ in 2023, which is more than the EEUD reports for any single technology in the sector. We therefore allocate 2023 demand from the following categories, in order to meet total Methanex 2023 energy demand:
     - High Temperature Heat (>300 C), Reformer, excluding Ballance use (13.92 PJ) 
     - High Temperature Heat (>300 C), Furnace/Kiln (2.75 PJ) 
     - High Temperature Heat (>300 C), Boiler Systems (3.73 PJ)


Any demand from the above end uses that is allocated to Methanex is relabelled as “Reformer” demand in TIMES-NZ. 

This method results in an implied feedstock share of 63.2% at Methanex in 2023, which is somewhat lower than standard estimates of 70%. Results of the method are detailed in {numref}`tab-chem_demand_estimates`.

```{list-table} 2023 chemical demand estimates for specific sectors
:header-rows: 1
:name: tab-chem_demand_estimates
* - 
  - Ballance
  - Methanex
* - Total demand
  - 6.67 PJ
  - 55.49 PJ[1]
* - Feedstock demand
  - 3.54 PJ
  - 35.08 PJ
* - Direct energy use
  - Reformers: 1.64 PJ
  - Reformers: 20.40 PJ
* - 
  - Compressors: 0.90 PJ
  - 
* - Cogeneration
  - 0.60 PJ
  - 
* - Feedstock share of demand
  - 53%
  - 63.20%
```


Ballance and Methanex’s energy use of natural gas accounts for 94% of the gas use in the EEUD’s Petroleum, Basic Chemical and Rubber Product Manufacturing sector. The remaining 6% is assigned to the Chemicals sector (excluding Urea and Methanol) in TIMES-NZ. 

[^gic_data]: GIC | Gas Production and Consumption: <https://www.gasindustry.co.nz/data/gas-production-and-consumption/>
[^ballance_assumptions]: Accelerating renewable energy and energy efficiency submission by Ballance Agri-Nutrients (p6): <https://www.mbie.govt.nz/dmsdocument/11988-ballance-agri-nutrients-accelerating-renewable-energy-and-energy-efficiency-submission-pdf>
[^compressor_note]: This compressor demand is referred to as “Pump System Technology” in the EEUD.

## Other adjustments to the EEUD

In addition to recategorising sectors, we make the following minor adjustments to technology definitions in mapping EEUD data to TIMES-NZ:
 - Boiler technologies using geothermal steam as energy are renamed to “Heat Exchangers”.
 - Pump system technologies using natural gas at Ballance are renamed to “Compressors”. 
 - All direct use of natural gas at Methanex is labelled “Reformers”.
 - The EEUD shows that there is some high temperature (over 300°C) process heat use in the wood processing sector. This uses electricity, and the total demand is very low; roughly 3TJ in 2023. As there should be no process heat over 300°C in this sector, we believe this may be a category error, and recategorise it as intermediate heat (100°C-300°C) provided by electric boilers.


## Industrial biomass demand 

EEUD demand data is based primarily on data from the MBIE energy balance tables . At the time of writing, this data’s coverage of biomass demand was incomplete, as it only captured biomass used for energy in the residential and wood processing sectors. Biomass demand in other industrial sectors, such as dairy or meat processing, was missing. 

EECA currently maintain an internal database of known industrial and commercial consumers of biomass for energy use. To resolve this issue, we used this internal data to estimate existing biomass demand for the relevant sectors. We further make assumptions on the end use, depending on the sector involved. These assumptions and estimates are detailed in {numref}`tab-industry_biomass_demand` below. 

```{list-table} Additional biomass demand estimates
:header-rows: 1
:name: tab-industry_biomass_demand
* - Industrial subsector
  - End use assumption
  - 2023 demand
  - 2024 demand
* - Dairy
  - Intermediate Heat (100-300 C)
  - 1.8 PJ
  - 2.7 PJ
* - Meat
  - Intermediate Heat (100-300 C)
  - 0.2 PJ
  - 0.3 PJ
* - Food and beverage
  - Intermediate Heat (100-300 C)
  - 0.4 PJ
  - 0.9 PJ
* - Mining
  - Intermediate Heat (100-300 C)
  -
  - 0.01 PJ
* - **Total**
  - 
  - **2.4 PJ**
  - **3.9 PJ**
```


These are estimates only, as EECA’s internal data may not fully capture all users throughout the sector. Note that this additional demand raises total industrial demand by 1.4%. This means that TIMES-NZ base year demand data will not perfectly align with the EEUD or energy balance tables.

## Island demand shares 


To model industrial demand, we need to estimate the share of demand in each island to better understand fuel availability and potential grid load. These fuel consumption island splits were estimated based on process heat data collected from the Regional Energy Transition Accelerator (RETA) Programme[^reta] and suported by other data as detailed in the notes section in {numref}`tab-ind_island_shares` below. 

As most of the stationary energy used in industry is from process heat, we believe using RETA data for certain industrial sub-sectors (including dairy, meat, non-metallic mineral product manufacturing, other industry and food & beverage) is a fair representation. 

```{list-table} Industrial demand island share methods and data
:header-rows: 1
:name: tab-ind_island_shares
* - Industrial sub-sector
  - NI \%
  - Notes
* - Aluminium
  - 0%
  - Only NZAS operating in New Zealand. Note aluminium extrusion operations covered in “Other”.
* - Chemicals (excl. Urea and Methanol)
  - 100%
  - No RETA chemical manufacturing in the South Island
* - Construction
  - 74%
  - Based on Regional GDP, March 2024[^snz_rgdp]
* - Dairy
  - 58%
  - Combination of RETA and EEUD data
* - Food and Beverage
  - 75%
  - Taken from RETA data
* - Iron & Steel
  - 100%
  - Only NZ Steel and Pacific Steel operating in North Island
* - Meat
  - 43%
  - Taken from RETA data
* - Methanol
  - 100%
  - Only Methanex operating in the North Island
* - Mining
  - 67%
  - 2023 NZPAM mining production statistics[^nzpam_regional]
* - Non-Metallic Mineral Product Manufacturing
  - 95%
  - Taken from RETA data as all businesses that were categorised as Concrete/Lime sector as these activities use significant process heat. Includes Golden Bay Cement and Graymont sites.
* - Other
  - 88%
  - Taken from RETA data
* - Pulp and Paper
  - 100%
  - No pulp and paper manufacturing in the South Island
* - Urea
  - 100%
  - Only Ballance Kapuni site in New Zealand
* - Wood Products
  - 75%
  - Data taken from MPI’s wood processing data[^mpi_wood_processing]
```

[^reta]: EECA | Regional Energy Transition Accelerator: <https://www.eeca.govt.nz/co-funding-and-support/products/about-reta/>
[^nzpam_regional]: NZPAM | Industry Statistics: <https://www.nzpam.govt.nz/nz-industry/nz-minerals/minerals-statistics/industry-statistics>
[^mpi_wood_processing]: MPI | Wood Processing Data: <https://www.mpi.govt.nz/forestry/forest-industry-and-workforce/forestry-wood-processing-data/wood-processing-data/>
[^snz_rgdp]: SNZ | Regional Gross Domestic Product: <https://www.stats.govt.nz/information-releases/regional-gross-domestic-product-year-ended-march-2024/>

Natural gas and geothermal industrial energy end use are assumed to be 100% in the North Island. We estimate dairy’s biomass demand was 70% in the North Island during 2023. 

We also make some adjustments to the regional splits for coal for some sectors, with the North Island percentages as follows: 
 - Food and Beverage (excluding Meat and Dairy processing): 0%
 - Dairy processing: 4%
 - Other: 16% 

This reflects that for some industries, coal use is predominantly in the South Island. Sectors not mentioned here have their coal use aligned with the broad sector North Island share assumptions. 

Finally, following the above assumptions, other fuels for a given use are re-allocated to the appropriate island in the fuel splits. This ensures that the total sector use of each fuel and end use remains balanced. The final calculated North Island shares of each fuel use are detailed in {numref}`tab-final_island_shares`.


```{list-table} North Island shares of fuel used per sector 
:header-rows: 1
    :class: expandable-table
    :name: tab-final_island_shares
* - Industrial sub-sector
  - Biogas
  - Coal
  - Diesel
  - Electricity
  - Fuel Oil
  - Geothermal
  - LPG
  - Natural Gas
  - Petrol
  - Wood
* - Aluminium
  - 
  - 
  - 
  - 0%
  - 
  - 
  - 
  - 
  - 
  - 
* - Chemicals (excl. Urea and Methanol)
  - 
  - 
  - 
  - 100%
  - 100%
  - 
  - 
  - 100%
  - 
  - 
* - Construction
  - 
  - 
  - 72.90%
  - 74%
  - 
  - 
  - 
  - 100%
  - 72.80%
  - 
* - Dairy
  - 0%
  - 4%
  - 0%
  - 58%
  - 0%
  - 100%
  - 0%
  - 100%
  - 
  - 70%
* - Food and Beverage
  - 
  - 
  - 30.80%
  - 71.70%
  - 
  - 
  - 30.80%
  - 100%
  - 
  - 
* - Iron & Steel
  - 
  - 100%
  - 
  - 100%
  - 
  - 
  - 
  - 100%
  - 
  - 
* - Meat
  - 
  - 
  - 
  - 43%
  - 
  - 
  - 
  - 100%
  - 
  - 
* - Methanol
  - 
  - 
  - 
  - 
  - 
  - 
  - 
  - 100%
  - 
  - 
* - Mining
  - 
  - 0%
  - 38%
  - 38%
  - 
  - 
  - 
  - 100%
  - 38%
  - 
* - Non-Metallic Mineral Product Manufacturing
  - 
  - 91.60%
  - 
  - 94.40%
  - 
  - 
  - 
  - 100%
  - 
  - 
* - Other
  - 100%
  - 16%
  - 88%
  - 87.90%
  - 74.50%
  - 
  - 100%
  - 100%
  - 88%
  - 
* - Pulp and Paper
  - 
  - 100%
  - 
  - 100%
  - 100%
  - 100%
  - 
  - 100%
  - 
  - 100%
* - Urea
  - 
  - 
  - 
  - 
  - 
  - 
  - 
  - 100%
  - 
  - 
* - Wood Products
  - 
  - 74.50%
  - 74.50%
  - 75%
  - 74.50%
  - 100%
  - 75%
  - 100%
  - 
  - 74.50%
```