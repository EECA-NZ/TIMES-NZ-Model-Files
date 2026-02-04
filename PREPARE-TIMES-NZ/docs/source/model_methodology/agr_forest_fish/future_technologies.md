# Future technologies


## Off-road vehicles

Off-road vehicles, including tractors and other machinery, are assumed to be decarbonised through the adoption of alternative fuels, specifically renewable electricity and green hydrogen. Both options are available within the TIMES-NZ framework.

For light-duty vehicles such as trucks (<10 tonnes), utility vehicles (Utes), and farm quads/bikes, assumptions were adopted from the transport sector. However, assumptions for electric or hydrogen tractors, ground-based forestry equipment, and cable-based forestry equipment were derived separately, as their operational profiles differ significantly from trucks. We have used the TIIMES-NZ 2.0 assumptions. 

### Cost assumptions and methodology

The total cost of machinery (labelled as “tractors” but also including harvesters and similar equipment) was calculated using the following equations:

```{math}
:name: eq_electric_machinery
    BatteryCost = Size_{kWh} \cdot (BatteryCost+SystemCosts) \cdot (1+p)+ChargerCost
```


```{math}
:name: eq_hydro_machinery
	FuelCellCost = Size_{kW} \cdot (FuelCellCost+SystemCosts)+Fuelling Station Cost
```

Here, $p$ represents the productivity penalty for battery electric vehicles. This productivity penalty was introduced for battery-electric tractors and harvesters to reflect the impact of additional battery mass on overall machine performance. Hydrogen-fuelled machinery was not subject to this penalty, as its mass is assumed to be comparable to that of conventional internal combustion engine (ICE) vehicles.

Assumptions include:
 - Charger cost for electric machinery: $1,000/kW
 - Battery round-trip efficiency: 0.8
 - Hydrogen fuelling station cost: based on World Energy Council data, originally derived from the IEA[^iea_cervo].


[^iea_cervo]: Personal Communication – M.Cervo, World Energy Council, 2020


### Battery/fuel cell costs

Battery costs were sourced from BloombergNEF (BNEF) projections up to 2030, after which they are assumed to remain constant due to long-term uncertainties in lithium and cobalt availability, and the potential emergence of alternative chemistries. It is also possible that as battery electric vehicles (BEVs) achieve cost parity with ICEs, innovation incentives may shift towards other technologies. 


```{csv-table} Battery cost projections (NZD/kWh)
:header-rows: 1
:name: tab_agr_batt_costs

Battery (NZD/kWh),2020,2025,2030,2040,2050
Traditional,222,168,111,111,111
Transformation,209,140,92,92,92
```


```{csv-table} Fuel cell cost projections (NZD/kW)
:header-rows: 1
:name: tab_agr_fc_costs

Fuel cell (NZD/kW),2020,2025,2030,2040,2050
Traditional,404,313,247,182,141
Transformation,401,282,180,133,103
```


### Non-battery costs 

Additional system costs (includes all the extra equipment, integration, and control hardware required to make a battery or fuel cell propulsion system fully operational) were estimated using EECA’s internal data for electric tractors. These costs were normalised to a per unit power basis and reduced annually using rates derived from projected cost reductions for medium and heavy trucks.
However, since these reductions depend on global economies of scale, agricultural and forestry machinery will not experience the same cost declines until market demand becomes sufficiently large. 
The timing of cost reductions is assumed as follows:
 - Tractors: 2030 (Transformation), 2035 (Traditional)
 - Forestry (ground-based): 2035 (Transformation), 2040 (Traditional)
 - Forestry (cable yarding): 2040 (Transformation), 2045 (Traditional)


### Sizing the battery/fuel cell 


Electrifying agricultural machinery presents challenges in the high kWh numbers needed to perform some duties, but exchangeable batteries packs are a much more workable solution than is available to road vehicles, and provide operational flexibility during charging. This constraint is less significant for hydrogen fuel cell systems.
The battery size was determined using the following equation:


```{math}

Energy Requirement (kWh)=Maximum power (kW)×Maximum hours used per day×Load Factor×Oversize factor

```

 - Oversize factor for batteries: 1.36 (36%), reflecting depth-of-discharge and efficiency considerations
 - Oversize factor for fuel cells: 1.55 (55%), accounting for lower fuel cell efficiency compared to batteries


### Other assumptions 

The main parameters underpinning the development of cost assumptions for electric and hydrogen machinery are summarised below. 

```{csv-table} Assumptions for decarbonising agricultural machinery by displacing diesel fuel with renewable electricity or green hydrogen
:header-rows: 1
:name: tab_agr_other

Technology,"Load Factor[^california_air_resources_board]<sup>,</sup>[^harvesting_cost_factors]",Maximum usage hours per day,Average hours used per year,Number of Battery Packs (for electric),Engine power
Dairy farm tractor,48%,4,800,112,84 kW
Livestock farm tractor,48%,4,800,112,84 kW
Arable/horticulture tractor,44%,12,540,168,114 kW
Forestry-Ground based,54%,7,1346,56,173 kW[^harvesting_fuel_consumption]
Forestry-Cable yarding,54%,8,1344,56,384 kW[^modern_cable_yarders]
```
[^california_air_resources_board]: California Air Resources Board, 2018, [Analysis of California’s Diesel Agricultural Equipment Inventory according to Fuel Use, Farm Size, and Equipment Horsepower](https://ww3.arb.ca.gov/msei/ordiesel/agfuelstudy2018.pdf)

[^harvesting_cost_factors]: Akay & Sessions, 2004, [Identifying the Factors Influencing the Cost of Mechanized Harvesting Equipment](https://www.researchgate.net/publication/242723734_Identifying_the_Factors_Influencing_the_Cost_of_Mechanized_Harvesting_Equipment)

[^harvesting_fuel_consumption]: Oyier, 2015, [Fuel consumption of timber harvesting systems in New Zealand](https://ir.canterbury.ac.nz/bitstream/handle/10092/11751/Oyier,%20Paul_Masters%20Thesis.pdf;sequence=1)

[^modern_cable_yarders]: Campbell, 2016, [Assessment of the Opportunity of Modern Cable Yarders for Application in New Zealand](https://ir.canterbury.ac.nz/bitstream/handle/10092/12832/Campbell%2CThornton%20MForSc%20Thesis.pdf?sequence=1)


## Space heating 

The primary sub-sector requiring space heating is indoor cropping, particularly in heated greenhouses. Heat demand associated with grain drying is categorised under arable farming and outdoor horticulture. In line with the approach adopted in TIMES-NZ 2.0, the TIMES-NZ 3.0 model includes the following technology options for meeting space heating requirements:
 - Coal boiler
 - Natural gas boiler
 - Wood pellet boiler
 - Electric heat pump (Air to water)
 - Hydrogen boiler

The cost, efficiency, and lifetime parameters for these technologies are primarily drawn from research undertaken by the University of Waikato on decarbonisation options for process heat[^space_heating_decarb]. These values have been adjusted to reflect the specific characteristics of indoor cropping, where hot water rather than steam is sufficient to meet heating needs.

[^space_heating_decarb]: Atkins, 2019, [Options to Reduce New Zealand’s Process Heat Emissions: Process Heat Options Draft Report](https://www.eeca.govt.nz/assets/EECA-Resources/Research-papers-guides/Options-to-Reduce-New-Zealands-Process-Heat-Emissions.pdf)

## Fishing 

Decarbonisation technologies as identified are primarily around fuel-switching, in particular renewable diesel for the existing fleet, with LNG (mainly dual-fuel), ammonia and methanol possible options for new vessels, potentially via fuel-cell in combination with hybrid drives. Barriers to alternative fuels include both energy density and cost, since cleaner fuels have lower density the fuel tanks would be too large to fit into current ship designs, which would generally require new boats.

## Biofuels 

Both biodiesel and drop-in diesel are allowed to be selected in TIMES-NZ 3.0 for all diesel consuming technologies within agricultural technologies. 

## Uptake constraints 

Off road electric vehicles were constrained in TIMES-NZ until 2025 due to supply limitations. This covers the fact that there are limited amounts of electric Utes available on the market, so having them enter the solution was implausible for the near-term. 


```{csv-table} Technology uptake constraints
:header-rows: 1
:name: tab_agr_uptake_constraints

Technology,2025,2030,2035
Maximum electric Ute uptake,5%,50%,100%
Maximum electric medium truck uptake,5%,50%,100%
Maximum electric tractor uptake,30%,60%,100%
```

## Caveats

Although aquaculture in New Zealand is experiencing rapid growth, its current energy demand remains minor in comparison with the wider fishing industry. Consequently, its contribution has been considered negligible within the present analysis. This assumption may, however, be revisited as sectoral growth continues.

Irrigation systems differ significantly in both purpose and design, such as drip irrigation used in viticulture. As a result, a single set of techno-economic parameters cannot adequately represent irrigation across the sector. The aggregated treatment of agricultural subsectors in TIMES-NZ therefore omits several scheme specific opportunities. These may be incorporated in future updates should more detailed data become available.

Due to limited data availability, arable farming has been grouped with outdoor horticulture within TIMES-NZ to illustrate general food production trends, while sectors such as meat, dairy, and other food products are reported separately. It is acknowledged that horticultural activities, such as viticulture, have distinct energy requirements and intensities compared with arable farming.

The potential role of hydrogen as a fuel for ICE vehicles and machinery has not yet been incorporated into TIMES-NZ.
