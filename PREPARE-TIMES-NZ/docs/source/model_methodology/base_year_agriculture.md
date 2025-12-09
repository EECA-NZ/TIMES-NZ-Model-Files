# Base year agriculture demand 

```
Calibrating the TIMES NZ base year data for agriculture sector
```


This documentation describes the methods used to create agriculture base year data.

Agriculture base year user config file is found at `data_raw/user_config/VT_TIMESNZ_AGR.toml`.
The key data processing script is found at `scripts/stage_2_baseyear/baseyear_ag_forest_fish_demand.py`.
The reshaping script, which generates subtables used to generate the final excel file, can be found at `scripts/stage_4_veda_format/create_baseyear_agr_files.py`.

The base year agriculture, forestry and fishing data is intended to reflect the distribution of 2023 energy end use across all sectors in New Zealand. These agriculture, forestry and fishing (AFF) technologies should be available to the model to meet future demand, but with enough information (efficiency, lifetime, availability factors, capital costs, etc.) that the model will retire technologies at appropriate points and can make least-cost decisions on fuel switching and utilisation across demand segments.

# Raw data used 

### EECA

Energy End Use Data 2023:
 - `eeca_data/eeud/Final EEUD Outputs 2017 - 2023 12032025.xlsx` | [Webpage](https://www.eeca.govt.nz/insights/data-tools/energy-end-use-database/) | [File](https://www.eeca.govt.nz/assets/EECA-Resources/Research-papers-guides/EEUD-Data-2017-2023.xlsx)
 - Used for estimating energy consumed (PJ) by most residential technologies

# Assumptions used

All coded base agriculture assumptions are stored in `data_raw/coded_assumptions/ag_forest_fish_demand/`.

These include: 

 - Livestock, horticulture, and irrigation demand `livestock_horticulture_irrigation_patch.csv`. Energy demand splits for livestock, horticulture, and irrigation sectors were processed seperately and patched to the EEUD data.
 - Technology splits `technology_splits.csv`. Includes diesel off-road vehicle splits (ute, tractor, truck, cable yarding, ground based) and VSDs, and heat recovery for pumps.
 - Technology lifetime `tech_lifetimes.csv`. Equipment lifetimes are taken as estimated useful life (years) from the Inland Revenues General depreciation rates October 2024 document. 
 - Capital and Operation costs of technologies `tech_fuel_capex.csv`, `tech_fuel_opex.csv`. The capital costs represent the upfront expenditure required to install each technology in a typical New Zealand ag, forest, and fish sector. The sources for these estimates include EECA research and case studies, government datasets, and New Zealand supplier price lists. Operating and maintenance costs assumptions for some technologies were extracted from TIMES-NZ 2.0 model. All costs were adjusted to 2023 New Zealand dollars using the most appropriate price index (CPI, CGPI). 
 - Technology efficiencies `tech_fuel_efficiencies.csv`. Energy efficiencies of most technologies came from the TIMES-NZ 2.0 model. 
 - Availability factors `tech_afa.csv`. Availability factors were extracted for each ag, forest, and fish subsector from TIMES-NZ 2.0 model assumptions. 
 - Reginal splits by fuel and sector `regional_splits.csv`. The island splits for irrigation were all derived from irrigated areas according to Irrigation NZ. All other non-irrigation energy demands for Dairy Farming, Livestock Farming, Outdoor Horticulture, and Forestry Island splits were derived from land areas according to Statistics NZ. The island split for indoor cropping was from TIMES-NZ 2.0 which was identified from the PHINZ programme by MBIE and EECA. This was manipulated by fuel type using a weighted average to reflect the fact that natural gas and geothermal fuels are only available in the North Island. The island split for Fishing was from TIMES-NZ 2.0 which was derived using the amount of value of fish by fishing region from Seafood NZ.
 - Load curves `ag_curvs.csv`, `ag_curves_irrigation.csv`, `ag_curves_mpm.csv`, `yrfr_season.csv`. Load curves were adopted from TIMES-NZ 2.0 and applied for dairy sheds, heated greenhouses, off road vehicles, and irrigation systems to capture seasonal farming cycles and climatic effects. Dairy shed and heated greenhouse load curves were sourced from EECA internal datasets. Off road vehicle load curves were estimated by assuming charging would avoid peak periods. Irrigation load curves draw on University of Otago  estimates and are weighted toward drier seasons. Because irrigation is climate dependent, it is represented at seasonal level; day/night variation was not modelled as a constant value. 
 - New technologies `new_techs_traditional.csv`, `new_techs_transformation.csv`. Includes future transport technologies with different cost curves for TIMES-NZ scenarios.


# Detailed method

## 1 Historic Demand

The historic demand for agriculture, forestry and fishing sector was derived from EECA’s Energy End Use Database (EEUD). As there are some key differences in technologies and sub sector structure between TIMES-NZ 3.0 and the EEUD, the end-use energy in TIMES-NZ must be reconciled with the MBIE Energy Balance Tables. The key adjustments we made are to disaggregate 
 - the EEUD Non-Dairy Agriculture demand between TIMES-NZ sub sectors: Livestock Farming and Outdoor Horticulture & Arable Farming, and to disaggregate
  - the irrigation energy demand between Dairy Farming, Livestock Farming and Outdoor Horticulture & Arable Farming. Our approach is discussed below.

### Livestock and 

Farm level data for livestock and horticulture are normalised to activity units that vary across subsectors:
 - Other livestock farming: stock units, with weightings for different animal types 
 - Horticulture and arable farming: hectares . Horticulture: Energy use estimates are largely based on apple orchards, with specific adjustments for grapes and kiwifruit.

Expenditure data were available from both recent sources (post-2018) and older surveys (2012/13) depending on subsector coverage. Expenditure data are converted to litres or kWh using MBIE’s published energy prices at the time of data collection. Sector specific electricity tariffs are applied for the AFF sector, while retail diesel prices are used to reflect rural delivery costs.

The resulting bottom-up estimates are reconciled with EEUD Non-Dairy Agriculture data. This ensures consistency at the aggregate level while allowing for greater resolution in the distribution of energy use across farm activities.

### Irrigation

Irrigation was included in the EEUD for dairy farming but not for other livestock farming and outdoor horticulture and arable farming. Irrigation application areas were obtained from Irrigation NZ  where the relative irrigation land use proportions for livestock farming, and outdoor horticulture and arable farming were multiplied by the energy use for pumping and motive power stationary in EEUD Non-Dairy Agriculture after reconciliation with MBIE electricity data. This assumes that the irrigation intensity (energy use per hectare) is constant throughout all sub-sectors. We would expect this to be suitable for pastoral livestock production because the irrigation requirement is similar for dairy pastures and, for arable and vegetable production as most irrigation systems such as for cereal growing have similar requirements to pasture. 


## 2 Island split

Energy demand across the North and South Islands was allocated by ag, forest, fish subsector using appropriate proxy indicators:

 - Dairy Cattle Farming (all electricity (excluding irrigation): `NI`- 59% , irrigation: `NI`- 14%, all diesel: `NI`- 58%)
 - Livestock Farming (all electricity (excluding irrigation): `NI`- 44% , irrigation: `NI`- 8%, all diesel: `NI`- 44%)
 - Horticulture (Outdoor) (all electricity (excluding irrigation): `NI`- 45% , irrigation: `NI`- 19%, all diesel: `NI`- 45%)
 - Indoor Cropping (Coal: `NI`- 37%, Diesel: `NI`- 37%, Natural Gas: `NI`- 100%, Geothermal: `NI`- 100%, Electricity: `NI`- 64%)
 - Forestry and Logging (Natural Gas: `NI`- 100%, all other: `NI`- 74%)
 - Fishing, Hunting and Trapping (`NI`- 32%)
 - Other Agriculture (`NI`- 50%)


## 3 Demand projections

Demand projections for the sector were based on the land use projections from the Second Emissions Reduction Plan. We used their Baseline scenario projections for TIMES-NZ Traditional scenario and the Baseline Low scenario projections for the Transformation scenario and calculated the demand growth indexes. For Indoor cropping sector we have applied the same growth index as Horticulture (Outdoor). For Fishing sector, the demand for energy is assumed to be constant throughout time as it’s heavily regulated and dominated by wild catch, and future activity is limited by the Fish Quota Management System (QMS). However, EECA Energy Transition Accelerator (ETA) reports suggest a future shift to aquaculture. Also, ETA reports suggest that the Forestry and Logging demand is tied to projected harvest volumes. 


## 4 Future technologies

### Off-road vehicles
Off-road vehicles, including tractors and other machinery, are assumed to be decarbonised through the adoption of alternative fuels, specifically renewable electricity and green hydrogen. Both options are available within the TIMES-NZ framework.
For light-duty vehicles such as trucks (<10 tonnes), utility vehicles (Utes), and farm quads/bikes, assumptions were adopted from the transport sector. However, assumptions for electric or hydrogen tractors, ground-based forestry equipment, and cable-based forestry equipment were derived separately, as their operational profiles differ significantly from trucks. We have used the TIIMES-NZ 2.0 assumptions. 

#### Cost Assumptions and Methodology TIMES-NZ 2.0

The total cost of machinery (labelled as “tractors” but also including harvesters and similar equipment) was calculated using the following equations:
 - Electric machinery:
Battery size in kWh×(Battery cost+additional system costs)×(1+productivity penalty)+charger cost
 - Hydrogen machinery:
Fuel cell size×(Fuel cell cost+additional system  cost)+Fuelling station cost

These equations were applied across all time steps in TIMES-NZ. A productivity penalty was introduced for battery-electric tractors and harvesters to reflect the impact of additional battery mass on overall machine performance. Hydrogen-fuelled machinery was not subject to this penalty, as its mass is assumed to be comparable to that of conventional internal combustion engine (ICE) vehicles.

Assumptions include:
 - Charger cost for electric machinery: $1,000/kW
 - Battery round-trip efficiency: 0.8
 - Hydrogen fuelling station cost: based on World Energy Council data, originally derived from the IEA .

#### Battery/Fuel cell Costs

Battery costs were sourced from BloombergNEF (BNEF) projections up to 2030, after which they are assumed to remain constant due to long-term uncertainties in lithium and cobalt availability, and the potential emergence of alternative chemistries. It is also possible that as battery electric vehicles (BEVs) achieve cost parity with ICEs, innovation incentives may shift towards other technologies. These assumptions remain open to review.

#### Non-Battery Costs

Additional system costs (includes all the extra equipment, integration, and control hardware required to make a battery or fuel cell propulsion system fully operational) were estimated using EECA’s internal data for electric tractors. These costs were normalised to a per unit power basis and reduced annually using rates derived from projected cost reductions for medium and heavy trucks.

However, since these reductions depend on global economies of scale, agricultural and forestry machinery will not experience the same cost declines until market demand becomes sufficiently large.

The timing of cost reductions is assumed as follows:
 - Tractors: 2030 (Kea), 2035 (Tui)
 - Forestry (ground-based): 2035 (Kea), 2040 (Tui)
 - Forestry (cable yarding): 2040 (Kea), 2045 (Tui)

#### Sizing the battery/fuel cell

Electrifying agricultural machinery presents challenges in the high kWh numbers needed to perform some duties, but exchangeable batteries packs are a much more workable solution than is available to road vehicles, and provide operational flexibility during charging. This constraint is less significant for hydrogen fuel cell systems.

The battery size was determined using the following equation:
Energy Requirement (kWh)=Maximum power (kW)×Maximum hours used per day×Load Factor×Oversize factor

 - Oversize factor for batteries: 1.36 (36%), reflecting depth-of-discharge and efficiency considerations
 - Oversize factor for fuel cells: 1.55 (55%), accounting for lower fuel cell efficiency compared to batteries

### Space Heating

The primary sub-sector requiring space heating is indoor cropping, particularly in heated greenhouses. Heat demand associated with grain drying is categorised under arable farming and outdoor horticulture. In line with the approach adopted in TIMES-NZ 2.0, the TIMES-NZ 3.0 model includes the following technology options for meeting space heating requirements:
 - Coal boiler
 - Natural gas boiler
 - Wood pellet boiler
 - Electric heat pump (Air to water)
 - Hydrogen boiler

The cost, efficiency, and lifetime parameters for these technologies are primarily drawn from research undertaken by the University of Waikato on decarbonisation options for process heat . These values have been adjusted to reflect the specific characteristics of indoor cropping, where hot water rather than steam is sufficient to meet heating needs.

### Fishing

Decarbonisation technologies as identified are primarily around fuel-switching, in particular renewable diesel for the existing fleet, with LNG (mainly dual-fuel), ammonia and methanol possible options for new vessels, potentially via fuel-cell in combination with hybrid drives. Barriers to alternative fuels include both energy density and cost, since cleaner fuels have lower density the fuel tanks would be too large to fit into current ship designs, which would generally require new boats.


## 5 Biofuels

Both biodiesel and drop-in diesel are allowed to be selected in TIMES-NZ 3.0 for all diesel consuming technologies within the agricultural technologies. 


## 6 Constraints

Off road electric vehicles were constrained in TIMES-NZ until 2025 due to supply limitations. This covers the fact that there are limited amounts of electric Utes available on the market, so having them enter the solution was implausible for the near-term. 


## 7 Other Remarks

Although aquaculture in New Zealand is experiencing rapid growth, its current energy demand remains minor in comparison with the wider fishing industry. Consequently, its contribution has been considered negligible within the present analysis. This assumption may, however, be revisited as sectoral growth continues.

Irrigation systems differ significantly in both purpose and design, such as drip irrigation used in viticulture. As a result, a single set of techno-economic parameters cannot adequately represent irrigation across the sector. The aggregated treatment of agricultural subsectors in TIMES-NZ therefore omits several scheme specific opportunities. These may be incorporated in future updates should more detailed data become available.

Due to limited data availability, arable farming has been grouped with outdoor horticulture within TIMES-NZ to illustrate general food production trends, while sectors such as meat, dairy, and other food products are reported separately. It is acknowledged that horticultural activities, such as viticulture, have distinct energy requirements and intensities compared with arable farming.

The potential role of hydrogen as a fuel for ICE vehicles and machinery has not yet been incorporated into TIMES-NZ.


## 8 Emissions factors

Emissions factors for each thermal fuel are sourced from the Ministry for the Environment’s Measuring Emissions Guide 2025 . These are all converted to kt CO2e/PJ equivalents using gross calorific values from MfE’s data for use in modelling. The electricity supply portion of the model will handle the electricity emission factor for ag, forest, fish electricity. 

