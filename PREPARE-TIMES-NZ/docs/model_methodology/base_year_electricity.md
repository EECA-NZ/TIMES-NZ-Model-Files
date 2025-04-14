# Base year electricity supply 

```
Calibrating the TIMES NZ base year data for electricity generation 
```


This documentation describes the methods used to create electricity base year data.

Electricity base year user config file is found at `data_raw/user_config/VT_TIMESNZ_ELC.toml`.
The key data processing script is found at `scripts/stage_2_baseyear/baseyear_electricity_generation.py`.
The reshaping script, which generates subtables used to generate the final excel file, can be found at `scripts/stage_4_veda_format/create_baseyear_ELC_files.py`.

The base year generation data is intended to reflect the distribution of 2023 generation across all generating New Zealand assets. 
These should be available to the model to meet future demand, but with enough information (region, technology, remaining life, etc) that the model will retire plants at appropriate points and can make least-cost dispatch and peak decisions. 

We have improved on TIMES 2.0 by building a bottom-up, asset-based model of the existing generation fleet. This gives us much greater detail in how the model utilises the existing generation fleet, and will allow us to make very precise changes as needed. 

Note that this does mean updating the base year will currently require a manual review of this existing asset list.

# Raw data used 

All raw data from external sources is stored in `data_raw/external_data/`

### MBIE 

EDGS generation stack:
 - `mbie/electricity-demand-generation-scenarios-2024-assumptions.xlsx` | [Webpage](https://www.mbie.govt.nz/building-and-energy/energy-and-natural-resources/energy-statistics-and-modelling/energy-modelling/electricity-demand-and-generation-scenarios) | [File](https://www.mbie.govt.nz/assets/Data-Files/Energy/electricity-demand-generation-scenarios-2024-assumptions.xlsx)
 - Used for manual cross-checking against our existing list. We also use data on operating costs, fuel delivery costs, and fuel efficiency.

 Official electricity data:
 - `electricity.xlsx` | [Webpage](https://www.mbie.govt.nz/building-and-energy/energy-and-natural-resources/energy-statistics-and-modelling/energy-statistics/electricity-statistics) | [File](https://www.mbie.govt.nz/assets/Data-Files/Energy/nz-energy-quarterly-and-energy-in-nz/electricity.xlsx)
 - Used for ensuring that our base year generation and capacity is calibrated to official data 

### Electricity Authority (EMI)

The Electricity Authority data (sourced from [EMI](https://www.emi.ea.govt.nz/)) is stored in subdirectories per topic area.

EMI Current fleet data:
 - `emi_fleet_data/` | [Webpage](https://www.emi.ea.govt.nz/Wholesale/Datasets/Generation/GenerationFleet/Existing) | [File](https://www.emi.ea.govt.nz/Wholesale/Datasets/Generation/GenerationFleet/Existing/20230601_DispatchedGenerationPlant.csv)
 - Used for manual cross-checking of our list of current generating assets. Not used computationally but stored as reference.

EMI Network supply table: 
- `emi_nsp/` | [Webpage](https://www.emi.ea.govt.nz/Wholesale/Datasets/MappingsAndGeospatial/NetworkSupplyPointsTable) | [File](https://www.emi.ea.govt.nz/Wholesale/Datasets/MappingsAndGeospatial/NetworkSupplyPointsTable/20250308_NetworkSupplyPointsTable.csv)
- A mapping and concordance table used to link regions to POCs, etc.

EMI Modelled generation (Generation_MD):
 - `emi_md/` | [Webpage](https://www.emi.ea.govt.nz/Wholesale/Datasets/Generation/Generation_MD)
 - used to estimate generation per plant in historical years, where possible. Multiple files used.

EMI distributed solar installations:
 - `emi_distributed_solar/` | [Webpage](https://www.emi.ea.govt.nz/Retail/Reports/GUEHMT?DateFrom=20130901&DateTo=20250228&FuelType=solar_all&_rsdr=ALL&RegionType=REG_COUNCIL&_si=v|3)
 - Used for distributed solar capacity by region and sector in the base year.
 
### Stats NZ 

Consumer Price Index:

 - `cpi/cpi_infoshare.csv` | [Webpage](https://infoshare.stats.govt.nz/QueryUpload.aspx) 
 - (Load the query stored at `statsnz/infoshare_queries/infoshare_cpi_query.tqx`)
 - Used for the functions at `library/deflator.py` to deflate price data to different base years as needed.

# Assumptions used

All coded base electricity assumptions are stored in `data_raw/coded_assumptions/electricity_generation/`.

These include: 

 - Custom Plant Settings `CurrentPlantsCustom.csv` - contains generation methods for custom plants (currently just Huntly)
 - Generic Plant Settings `CurrentPlantsGeneric.csv` - contains plant types we wish to make generic versions of
 - The Generation Fleet `GenerationFleet.csv` - this is the list of existing generation assets, including capacities, references, lookups, and other parameters. It's manually created. 
 - Capacity Factors `CapacityFactors.csv` - Capacity factor assumptions, used for some base year estimates and also future availability upper bounds for different technologies.
 - Distribution parameters `DistributionAssumptions.csv` - these are the assumed distribution and transmission parameters from older versions of TIMES.
 - Other assumptions per technology `TechnologyAssumptions.csv` - these are other assumptions per technology, including plant technical life and peak contribution rates.

# Emission factor data and assumptions

Emission factor raw inputs can be found in `data_raw/coded_assumptions/emission_factors/emission_factors.csv`. 

These are based on data from: 

 - The [2024 Measuring Emissions Guide](https://environment.govt.nz/publications/measuring-emissions-a-guide-for-organisations-2024-detailed-guide/)
 - NZ Geothermal's [2018 Emission Factors](https://www.nzgeothermal.org.nz/geothermal-in-nz/what-is-geothermal/)
 - Additional assumptions on [Ngawha's decarbonisation program](https://www.energyawards.co.nz/article/awards-finalist-ng%C4%81wh%C4%81-generation)

# Detailed method

## 1 Existing asset List

EECA has prepared a list of current plants for the base year generating stock. It is closely based on the EA dispatch generation fleet list (found here) and includes mapping to the current plants from MBIE’s EDGS Generation Stack (ADD LINK). Where possible, we have included mapping to plant names found in the Electricity Authority’s generation data by plant (ADD LINK). The list has been reviewed and updated based on developer statements and Energy News resource files for each plant. In some cases, capacities were updated, or names were adjusted slightly. 

This list is not intended to capture all distributed or cogeneration facilities, which are instead represented by generic plants (see below).

In general, plant status has been set to align with MBIE’s EDGS generation stack categories for 2023. This allows us to also use the MBIE generation stack for potential future technologies without double-counting. For example, Kaiwera Downs Stage 1 is considered for the base year, but the rest of the build is considered a future technology. This is because Kaiwera Downs was only partially operational by the end of 2023.

## 2 Distributing base year generation using Electricity Authority data

We use the Electricity Authority’s “Generation_MD” data to find estimates of generation for the current plant list. This bottom-up approach means we can assign known generation to plants, regions, and technologies. 

This data covers 93%* of total generation for 2023. For the remaining generation, we make some assumptions on the location and technology of distributed generation (cogeneration or otherwise) to calibrate final figures with the MBIE data. 

For plants where we include multiple stages, but there is only one reference in the EMI data (such as Ngawha or Turitea), generation is proportionally distributed by the stage’s capacity.

There are minor limitations in using this dataset. First, it covers only metered injections into the grid, leading to unusually low figures for cogeneration plants that also supply industrial sites behind the grid. It also does not cover generation behind the grid, such as rooftop solar panels or the embedded Lodestone solar farms in Northland. The Authority also notes some issues in the estimate techniques, and notes that:

```
“This data series will be replaced by one that is more reliable… at some point in the future”.
```

To alleviate these minor issues, we will calibrate our final base year generation figures against MBIE official statistics, which include all generation and cogeneration.


*40,597 GWh in the EA’s dataset is 93% of the 43,494 GWh reported by MBIE for 2023. 

## 3 Capacity factor estimates 

In some cases, using generation data from the Electricity Authority is either incomplete or results in implied capacity factors outside normal ranges. This is especially true for some cogeneration plants, but can also indicate that the asset mapping to Electricity Authority plant definitions was inaccurate.

In these cases, we instead set some plants to have generation estimated by capacity factor. Capacity factor assumptions for different technologies are provided to the model already, so we can use these assumptions to assume generation for given plants. 

Capacity factor assumptions can be found in `data_raw/coded_assumptions/electricity_generation/CapacityFactors.csv`. These are used for calibrating the base year and also providing upper limits to future generation for these plant types. Note that intermittent plants (wind/solar/potentially hydro) have more detailed availability per timeslice provided elsewhere. (LINK TO THIS DOCUMENTATION WHEN AVAILABLE)

## 4 Custom Treatment: Huntly Rankine Units

EMI data for the Huntly Rankine Units does not distinguish the proportions of coal or gas used for generation. We therefore assume the generation from coal is equivalent to MBIE figures on total coal electricity generation (i.e. excluding cogeneration), and the remaining share is from natural gas. This section is scripted separately. 

A note on biomass: In February 2023, Genesis completed a biomass trial at the Rankines. This means some small proportion of the generation was fuelled by imported wood pellets. We assume these figures are negligible overall, and they are currently not included in the base year model.

## 5 Adding distributed solar generation

EMI does not provide figures on rooftop solar generation. We therefore create generic plant stocks intended to represent different levels of rooftop solar generation (residential, commercial, and industrial), and distribute MBIE’s official solar generation statistics according to region and island based on EMI distributed solar capacity data. 
A stock model is applied to the existing stock of distributed solar generation to estimate the rate at which panels are retired from rooftops across the model horizon.

The implied capacity factor is a little over 11% when considering 2023 solar generation estimates from MBIE against solar capacity available at the end of 2023. This is quite low, but reflects that some of this capacity came online towards the end of the year, meaning there was only partial generation. 

Potential improvement: use the EA solar capacity data to estimate the age distribution of existing solar stock. This will give TIMES a more accurate stock model. 

## 6 Calibrating to official data and adding generic plants. 

After adding either Electricity Authority generation data or plant generation estimates based on capacity factors, we calibrate total figures against official MBIE generation data (broken down by cogeneration status and fuel type). We expect to still be missing some generation when comparing to official statistics, which reflects smaller embedded or other plants not available in our plant list or Electricity Authority solar capacity data. 

We therefore add a few parameters for potential “generic” existing plants, and these have their capacities and generation figures for the base year generated automatically based on the missing generation data and capacity factor assumptions. In cases where they may be on either island (such as wind or hydro), they are distributed according to the known regional distribution of similar plants. In other cases (such as geothermal or natural gas plants) they are distributed only across the North Island. 

## 7 Checks against official statistics 

### Calibration to official generation 


Calibrating the base year figures against official generation stats gives the following results: 


![Generation calibration](assets/generation_calibration.png)


This method results in mostly perfect calibration with MBIE generation data. Some estimates are slightly higher in the original Electricity Authority data, particularly for gas generation. We currently assign coal cogeneration to Glenbrook. We exclude MBIE’s waste heat in the base model, as we don’t have enough information about this to include it in TIMES. 

Overall, this means our base model will generate an extra 55GWh in 2023 compared to official data. This is a 0.13% difference – well within statistical difference in official reporting.

### Calibration to official capacity  
![Capacity calibration](assets/capacity_calibration.png)


Capacity figures are slightly less well-aligned. This is because we are using assumed capacity factors to estimate capacity for some plant types, which might not align with specific plant's actual capacity factors in 2023. Maintenance or unusual rainfall or a host of other factors could lead to different actual capacity outputs. This leads to minor miscalibrations, particularly for Hydro, but the overall levels are within 0.09% of MBIE values for the year. 




## 8 Adding technical parameters
### Technical parameters: by assumption

Now that our base year plants are properly calibrated, we add the remaining technical parameters. Some of these come by assumption, and others from MBIE data. 

We then read in technical parameter assumptions by technology. These are hardcoded assumptions found in (found in `data_raw/coded_assumptions/electricity_generation/TechnologyAssumptions.csv`). 

These currently include plant lifetime and peak contribution rates by technology, which are applied to every plant. These assumptions have been extracted from TIMES 2.0.

We further ensure that the distributed solar outputs into the distributed network (ELCDD) as opposed to the grid (ELC). See below on transmission and distribution for further details on these mechanisms.

### Technical parameters: MBIE data

We then extract all the remaining technical parameters for each plant. 

We're looking to include: 

1) Heatrate (or fuel efficiency)
2) Variable opex (NZD/MWh)
3) Fixed opex (NZD/kw/year)
4) Fuel delivery costs (NZD/GJ)

Each of the plants in our original list includes an `MBIE_Name` variable, which was added after manual review. These variables are now used to merge in the technical parameters from the genstack.

In cases where plants in the TIMES base year do not have direct equivalents, we take the mean of these parameters for similar plants and apply those instead. We generate mean values for each of these parameters for each technology in MBIE's Reference scenario, then map these to our plants by `TechnologyCode` and `FuelType`. 

Currently, decommissioning costs are not included. This was also true in TIMES 2.0. We instead assume that plants always retire at the end of their technical lifetime without incurring decommissioning costs.

We assume hydro plants are maintained indefinitely (by their null lifetime assumption), and the cost of turbine replacements are spread across their operating and maintenance costs each year.

## 9 Transmission and distribution 

Transmission and distribution processes are created to represent how electricity flows from High voltage lines to distributed networks, including associated losses and operating costs. Capacity is also represented (differently per island).

Assumptions on current transmission capacity, costs, and losses, have been extracted from TIMES 2.0 and not updated for 2023. Costs have been adjusted to 2023 dollars using the CPI index, and assuming that the original costs were in 2015 dollars.

## 10 Emissions factors

Emission factor assumptions are (almost) all defined in `data_raw/coded_assumptions/emission_factors/emission_factors.csv`. Some adjustments are currently made in the config file, specifically for Ngāwhā's generation. This file lists relevant sources, and is heavily based on work previously done for EECA's emission factors by Achini Weerasinghe. 

Emission factors are processed directly from the raw data to TIMES output files in `scripts/stage_4_veda_format/create_emission_factor_files.py`.

### Thermal fuel emission factors 

The emission factors come in a range of units, and are all converted to CO2-e/PJ. Factors from the assumptions worksheet are directly mapped to TIMES commodities. We use industrial emission factors from MfE and apply these to electricity generation. Coal emission factors use sub-bituminous values.

Note that these are based on gross calorific values.

### Geothermal emission factors 
For geothermal emissions, the factors are delivered in CO2-e/kWh. We therefore instead map these to the activity for geothermal plants (ie, the output electricity, rather than the input fuel as for thermal plants.)

These are specified on a per-plant basis, using data from [NZ Geothermal](https://www.nzgeothermal.org.nz/geothermal-in-nz/what-is-geothermal/). Geothermal plants can have a wide range of fugitive emission values, depending on the chemical makeup of the field. If emission factors for a field are unknown, we apply the median value. 

For Ngāwhā, we assume the 2023 emissions are much lower than the 2018 values, following Ngāwhā Generation's work in decarbonising emissions from these fields. We set emissions to an assumed 30% of 2018 values. Further, in the config file we create additional parameters to TIMES, which will reduce Ngāwhā emissions to 0 by 2026, following company announcements.

## 11 Adding TIMES features

We finally add a few extra features required by Veda/TIMES. These are currently: 

1) Include output commodity (ELC for everything except distributed solar, which is ELCDD)
2) Generate unique process names for every plant (these are a function of the plant name label, and also include the fuel and tech codes for easy lookups and wildcards later)


## 12 save staging data for existing technologies

A single file is produced by this process containing all necessary information for the base year electricity generation: 

`data_intermediate/base_year_electricity_supply.csv`

## 13 compile base year electricity file 

The stage 4 script at `scripts/stage_4_veda_format/create_baseyear_ELC_files.py` reshapes the data for Veda, and creates the final tables that are referenced in the user config file `VT_TIMESNZ_ELC.toml`.

This file also adds tertiary data, including emission factors and transmission and distribution parameters:

 - Emission factors are quite simple, so are defined and sourced in the user config.
 - Transmission and distribution parameters are slightly more complicated, so these are produced according to the raw assumptions in `data_raw/coded_assumptions/electricity_generation/DistributionAssumptions.csv`. The relevant costs are based on 2015 assumptions and are indexed to 2023 dollars.

