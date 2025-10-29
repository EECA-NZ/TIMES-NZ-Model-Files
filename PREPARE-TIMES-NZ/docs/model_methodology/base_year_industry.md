# Base year industry demand 

```
Calibrating the TIMES NZ base year data for industrial sector
```


This documentation describes the methods used to create industrial base year data.

Industrial base year user config file is found at `data_raw/user_config/VT_TIMESNZ_IND.toml`.
The key data processing script is found at `scripts/stage_2_baseyear/baseyear_industry_demand.py`.
The reshaping script, which generates subtables used to generate the final excel file, can be found at `scripts/stage_4_veda_format/create_baseyear_ind_files.py`.

The base year data is intended to reflect the distribution of 2023 energy end use across all industrial sectors in New Zealand. 

# Raw data used 

All raw data from external sources is stored in `data_raw/external_data/`

### GIC

- Gas Industry Company (GIC) production / consumption data `ProductionConsumption.csv`. To estimate the	Ballance and Methanex’s total natural gas demand

### MBIE

- MBIE energy balance natural gas demand `gas.csv`. To estimate the Methanex feedstock use and coal used as reductant at NZ Steel’s Glenbrook site.

### EECA

Energy End Use Data 2023:
 - `eeca_data/eeud/Final EEUD Outputs 2017 - 2023 12032025.xlsx` | [Webpage](https://www.eeca.govt.nz/insights/data-tools/energy-end-use-database/) | [File](https://www.eeca.govt.nz/assets/EECA-Resources/Research-papers-guides/EEUD-Data-2017-2023.xlsx)
 - Used for estimating energy consumed (PJ) by most commercial technologies

# Assumptions used

All coded base industry assumptions are stored in `data_raw/coded_assumptions/industry_demand`.

These include: 

 - Equipment lifetime and decommissioning `tech_lifetimes.csv`. 
     - Lifetimes of rotating equipment such as pumps, fans, compressor, motors, refrigeration, internal combustion engines, and electrical equipment such as heaters are taken as estimated useful life (years) from the Inland Revenue’s General depreciation rates October 2024 document , if unavailable, data are taken from other EECA sources such as technology scans, Energy Transition Accelerator Reports and industry sources/knowledge.
     - Boilers, refiners and reformers are all given a lifetime out to 2060 (i.e. the full TIMES model period), as this equipment is generally operated well past its original engineering and economic design life, and is typically only updated when it makes economic sense to (e.g. when the Net Present Value is greater than zero or the Marginal Abatement Cost is lower than the carbon price).
     - For coal fired boilers, the low to medium temperature coal boilers (i.e. under 300°C) are modelled to switch to renewable energy before 2037, when the National Direction for Greenhouse Gas Emissions from Industrial Process Heat regulations come into effect, or before that date if it makes financial sense. 
     - Aluminium, steel, methanol and urea technologies have their lifetimes extended throughout the model horizon. We assume these technologies will not be replaced, except for the NZ Steel furnace conversion which is planned to be operational in Q2 of 2026. 
 - Capital costs of technologies `tech_fuel_capex.csv`. 
     - Capital costs for process heat devices came from the Cost Assessment Tool developed for the RMA National Direction for Greenhouse Gas Emissions from Industrial Process Heat . A 30% factor was applied to these numbers due to feedback from industry that these numbers were too low during road testing of the tool.
     - Capital costs for internal combustion engine (land transport), pump systems (for fluids) and stationary engine were kept the same as in TIMES 2.0 due to lack of data. These have been adjusted for inflation.
 - Technology efficiencies `tech_fuel_efficiencies.csv`.
     - Energy efficiency for process heat devices came from the Cost Assessment Tool developed for the Resource Management Act (RMA) National Direction for Greenhouse Gas Emissions from Industrial Process Heat . The technology’s energy efficiency was taken as the middle range from the “lower efficiency bound” and the “upper efficiency bound”.
     - Efficiencies for internal combustion engine (land transport), pump systems (for fluids), electric motors, and stationary engines were found using literature reviews.
 - Availability factors `tech_afa.csv`. 
     - An availability factor of 0.5 was applied across all technologies. This represents a piece of equipment being “available” 50% of the time:
     - Availability Factor = (Available Operating Time) / (Total Time)
 - Reginal splits by fuel and sector `regional_splits_by_fuel.csv`, `regional_splits_by_sector.csv`, `regional_splits_by_sector_and_fuel.csv`.
 - Coal used as reductant at NZ Steel’s Glenbrook site `nz_steel_coal_use.csv`.
 - Urea and Methanol demand splits `chemical_split_category_definitions.csv`. 
 - The industrial load curves extracted from TIMES-NZ 2.0 model `load_curves_ind.csv`.


# Detailed method

## 1 Historic Demand

Fuel energy demand for the 2023 year has primarily been sourced from the Energy Efficiency and Conservation Authority’s (EECA) Energy End Use Database (EEUD), for the period ending 2023. 
Additional data for non-energy uses of fuels is sourced from Ministry of Business, Innovation and Employment (MBIE) data. These include natural gas for methanol and urea production, and coal for steel production. These are important to include for modelling and balancing supply and demand of fuels.

The TIMES-NZ model will be adjusted for any plant closures and major decarbonisation projects that have been commissioned between 1 Jan 2023 and 31 July 2025. The model will also be adjusted for high certainty future projects/closures that have publicly announced to happen after 31 July 2025, for example, NZ Steel’s electric arc furnace that is planned for early 2026. 

Industrial categories in TIMES-NZ are slightly different from those in the EEUD. For the purposes of the model, we combine some smaller categories, such as furniture manufacturing, into “Other”. We also model some larger industries separately, such as Aluminium or Methanol production.

Demand in the Urea and Methanol sectors have been calculated as a share of total Petroleum, Basic Chemical and Rubber Product Manufacturing use. The remaining demand in this sector is assigned to Chemicals in TIMES-NZ. Demand in the Iron & Steel and Aluminium sectors was calculated as a share of the Primary Metal and Metal Product Manufacturing sector. Methods for these calculations can be found under “Specific sectors and non-energy use” section below.


## 2 Specific sectors and non-energy use

Aluminium, Iron & Steel, Methanol, and Urea production are modelled separately in TIMES-NZ. However, these sectors are not detailed in the EEUD. This section details how we have estimated demand of these sectors, while using the EEUD as our base data. 

### Aluminium

Aluminium demand is the share of electricity demand in the EEUD’s Primary Metal and Metal Product Manufacturing sector used for high temperature process heat. This electricity demand aligns with Tiwai demand values, which are also accessible publicly through Electricity Authority node export data.

### Iron & Steel

The EEUD defines Primary Metal and Metal Product Manufacturing as Tiwai Aluminium Smelter, NZ Steel’s Glenbrook site, and Pacific Steel. This means that the remaining share of Primary Metal and Metal Product Manufacturing can be attributed to Iron & Steel. This means that Pacific Steel demand is included in the TIMES-NZ Iron & Steel sector. There is also some small energy demand for non-ferrous metal product production, and this is captured in “Other”.  

Coal used as reductant at NZ Steel’s Glenbrook site is not captured in the EEUD, as it does not qualify as end use. We add this coal to TIMES-NZ using MBIE’s energy balances, defined as the sum of coal used for other transformation and cogeneration. This gives a total coal use at Glenbrook of 16.4 PJ in 2023, in line with expected Glenbrook demand. Noting that the Electric Arc Furnace will be commissioned early in Q2 2026 and coal use as feedstock is expected to reduce by 50%, this change will also be captured in the model.

By defining the cogeneration coal as Glenbrook demand, we also remove this cogeneration from the electricity sector of the model. Note that all coal emissions at Glenbrook are defined as Industrial Process and Product Use (IPPU) rather than energy emissions.

We understand there is a small proportion of the national coal cogeneration demand used for cogeneration at other industrial sites. However, further disaggregation of this data is not available. Any resulting distortion is expected to be minor.

### Urea and Methanol demand

We model methanol and urea production (at the Methanex and Ballance Kapuni sites respectively) separately from the broader Petroleum, Basic Chemical and Rubber Product Manufacturing sector. Both sites use natural gas for energy and as a feedstock for their products. The energy use of natural gas is directly captured in the EEUD, but the feedstock is not. Feedstock demand is instead sourced from MBIE’s energy balances, defined as non-energy use of natural gas. We assume that Ballance and Methanex make up almost all this feedstock demand, which was 38.6 PJ in 2023.

To fully estimate the shares of Ballance and Methanex’s natural gas demand within the sector, we apply the following method:

 1)	Ballance and Methanex’s total natural gas demand is sourced from the Gas Industry Company (GIC) data on natural gas consumption for large users.

 2)	We assume 53% of Ballance’s natural gas demand is used for feedstock. Methanex feedstock use is estimated as MBIE data on total natural gas feedstock, minus the Ballance feedstock estimates.

 3)	We assume 9% of Ballance’s gas is used for cogeneration . This is therefore already captured in the electricity module of TIMES-NZ, so is not considered here. We consider the remaining 38% of Ballance’s total gas demand as energy use. This figure was 2.54 PJ in 2023. We allocate this among EEUD compressor  and reformer demand, aligning with existing EEUD data on compressor demand and allocating the rest to reforming.

 4)	Methanex process gas use is estimated as total Methanex gas demand minus their estimated feedstock use. This figure (process gas use) was 20.40 PJ in 2023, which is more than the EEUD reports for any single technology in the sector. We therefore allocate 2023 demand from the following categories, in order, to meet total Methanex 2023 energy demand:

     a.	High Temperature Heat (>300 C), Reformer, excluding Ballance use (13.92 PJ) 
     b.	High Temperature Heat (>300 C), Furnace/Kiln (2.75 PJ) 
     c.	High Temperature Heat (>300 C), Boiler Systems (3.73 PJ)
 
 Any demand from the above end uses that is allocated to Methanex is relabelled as “Reformer” demand in TIMES-NZ. 

This method results in an implied feedstock share of 63.2% at Methanex in 2023, which is somewhat lower than standard estimates of 70%.

Ballance and Methanex’s energy use of natural gas accounts for 94% of the gas use in the EEUD’s Petroleum, Basic Chemical and Rubber Product Manufacturing sector. The remaining 6% is assigned to the Chemicals sector (excluding Urea and Methanol) in TIMES-NZ.  


## 3 Other adjustments to the EEUD data 

In addition to recategorising sectors, we make the following minor adjustments to technology definitions in mapping EEUD data to TIMES-NZ:

 - Boiler technologies using geothermal steam as energy are renamed to “Heat Exchangers”.
 - Pump system technologies using natural gas at Ballance are renamed to “Compressors”. 
 - All direct use of natural gas at Methanex is labelled “Reformers”.
 - The EEUD shows that there is some high temperature (over 300°C) process heat use in the wood processing sector. This uses electricity, and the total demand is very low; roughly 3TJ in 2023. As there should be no process heat over 300°C in this sector, we believe this may be a category error, and recategorise it as intermediate heat (100°C-300°C) provided by electric boilers.


## 4 Industrial biomass demand

EEUD demand data is based primarily on data from the MBIE energy balance tables. This data’s coverage of biomass demand was incomplete, as it only captured biomass used for energy in the residential and wood processing sectors. Biomass demand in other industrial sectors, such as dairy or meat processing, was missing. 

EECA currently maintain an internal database of known industrial and commercial consumers of biomass for energy use. We used this internal data to estimate existing biomass demand for the relevant sectors. We further make assumptions on the end use, depending on the sector involved. 

Note that this additional demand raises total industrial demand by 1.4%. This means that TIMES-NZ base year demand data will not perfectly align with the EEUD or energy balance tables.


## 5 Island split

To model industrial demand, we need to estimate the share of demand in each island to better understand fuel availability and potential grid load. These fuel consumption island splits were estimated based on process heat data collected from the Regional Energy Transition Accelerator (RETA) Programme Regional Energy Transition Accelerator | EECA,  Statistics New Zealand Regional Gross Domestic Product breakdown, annual survey data from New Zealand Petroleum & Minerals and wood processing data from Ministry for Primary Industries.

As most of the stationary energy used in industry is from process heat, we believe using RETA data for certain industrial sub-sectors (including dairy, meat, non-metallic mineral product manufacturing, other industry and food & beverage) is a fair representation. 

Natural gas and geothermal industrial energy end use are assumed to be 100% in the North Island. We estimate dairy’s biomass demand was 70% in the North Island during 2023.

We also make some adjustments to the regional splits for coal for some sectors, with the North Island percentages as follows: 
 - Food and Beverage (excluding Meat and Dairy processing): 0%
 - Dairy processing: 4% [TBC]
 - Other: 16% 

This reflects that for some industries, coal use is predominantly in the South Island. Coal shares remain at 100% for Iron & Steel and Pulp and Paper, as these industries are 100% in the North Island. There is also a high North Island share of Non-Metallic Mineral Product Manufacturing, as most of this sector’s coal use is in cement production in the North Island. 

Finally, following the above assumptions, other fuels for a given use are re-allocated to the appropriate island in the fuel splits. This ensures that the total sector use of each fuel and end use remains balanced. 


## 6 Industrial sector’s future energy demand

Energy demand projections in TIMES are specifically for energy service demand. This is the useful service provided by the energy, such as kilometres travelled or water heating. For example, the model would not use projections of natural gas demand. It would instead use projections of space heating demand, then find the least-cost way of meeting this using available technologies and input fuels. One exception to this rule is for ‘new industries’ as discussed below.

For the Traditional scenario, we use the average growth rates in energy demand for the last 6 years from EECA’s Energy End Use Database (EEUD) and extrapolate these as energy service demand projections across the forecast horizon. The compound annual average growth rates used are listed below. For some subsectors, such as Aluminium or Methanol, we have set growth rates to 0 to imply continuous production.

For the Transformation scenario, we select specific sectors to invert growth (or contraction) rates, representing the economic structure shifting over time. We intend to model a short transition period (e.g. 5 years) to avoid this being an unrealistic step change. We also include a category for ‘new industries’. This is intended to represent the growth of advanced manufacturing, and is considered to be solely electricity demand. We do not model specific technologies (with specific conversion efficiencies) and so the demand is expressed directly as electricity demand, rather than energy service demand.

Each scenario is intended to imply roughly similar overall economic activity levels, but different components of that economic activity. Note that TIMES is not an economic model, and so we do not project economic activity, employment, or trade balances.

The demand profiles (time of use) of each subsector are the same within each scenario, and specific sectors may or may not switch fuels or technologies to meet their demand, if possible and economically efficient.

By using historical energy demand to project energy service demand, we implicitly assume that incremental energy efficiency improvements within sectors continue across the model horizon. However, TIMES-NZ allows for fuel switching and technology upgrades within each sector, which may further increase efficiency and lower total energy demand.


## 7 Maximum uptake

Maximum uptake is used as a constraint where it would not be possible for a specific technology to be used to produce more than a certain percentage of the end use energy for a specific subsector. For instance, it is often not possible for heat recovery technologies to provide enough heat for a specific end use (as it is constrained by the level of current wasted heat). This technology may therefore be constrained to a maximum uptake.


## 8 Industrial others

To match data in TIMES, EEUD and MBIE, the Industrial others subsector data needed some additional assumptions. In TIMES 2.0 these were left as “other” technology and “other” endues and mostly given a lifetime of 1 so that their input was ignored. However, interrogating the EEUD shows that the Industrial others subsector has significant energy use.

From previous EECA analysis, it has been shown that the majority of emissions (noting that emissions can be taken as a proxy for energy use) in the Industrial others subsector are coming from Small to Medium Enterprise (SME) (defined by EECA as outside the top 100 stationary energy users), i.e. 95%. Most SME’s stationary energy is likely from low and intermediate heat requirements, as they are unlikely to have complex manufacturing facilities requiring high pressure, high temperature process heat.

Fuel use in the EEUD that is not assigned to any end use or technology is instead assigned to default technology and use options. These are defined as the most common technology and use options for any given fuel within this sector.


## 9 New Technologies

New technologies are based on proven commercially available technology (TRL 7 and above) that have been, or will be, installed and commissioned in New Zealand through initiatives such as EECA’s technology demonstration fund and the Government Investment in Decarbonising Industry (GIDI) and haven’t been included in TIMES 2.0 existing technology. It is recommended that this list is reviewed regularly to ensure that all commercially available new technologies are considered in TIMES.

 - Steam generating heat pumps: this technology typically requires waste heat, so we assume they can be deployed at industrial sites with existing process heat needs above 100°C, i.e. where waste heat is likely to already be available. An 80°C temperature lift is assumed, yielding a Coefficient of Performance (COP), or energy efficiency, of 2.3.
 - Mechanical Vapour Recompression: this technology increases process efficiency by recovering and reusing low-pressure steam. It is commonly implemented as a retrofit alongside existing or new steam boilers to reduce fuel consumption.
 - Pulsed Electric Field (PEF): this technology uses short bursts of high-voltage electricity to permeabilise cell membranes in liquids and semi-solids, enabling processes such as pasteurisation. It is typically applied as a non-thermal or low-thermal alternative to conventional heat-based treatments, improving energy efficiency. There is limited data on the efficiency and costs of this technology for widespread use in New Zealand and therefore this technology will not be modelled for TIMES 3.0 but  it will be kept in the table above as a placeholder for future updates of the model. 


