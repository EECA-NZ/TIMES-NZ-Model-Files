# Transformation processes

## Sustainable Aviation Fuel (SAF)

A single commercial facility could produce around 113 million litres of liquid fuels per year, of which around 90 percent would be SAF and the remainder renewable diesel. In energy terms, SAF output alone would represent almost 10 PJ per year, making it the largest single potential contributor to domestic aviation decarbonisation. The required feedstock comes from forestry residues (30%) and lower-value logs (70%) that have limited alternative markets. Although the exact feedstock volumes are commercially sensitive, the majority of the resource is concentrated in the central and eastern North Island, where plantation forestry is most active. While each step in the conversion process is commercially proven overseas, the fully integrated system has never been deployed in New Zealand, and the scale proposed would sit at the upper end of global examples. 

The economics are challenging. A feasibility study found that converting woody biomass into SAF would expect to contribute $428 million annually to the country’s GDP, however, under current conditions, SAF produced through this pathway would cost between two and five times the price of fossil jet fuel. Most of this premium reflects the capital intensity of the technology and the depth of conversion required. Biomass must pass through three separate transformation steps before becoming usable jet fuel. Even with optimised logistics and maturing supply chains, the project would remain significantly more expensive than fossil alternatives without government intervention. Because of these costs, we assume a domestic SAF industry will not emerge on a commercial basis unless the policy environment changes.

 High level numbers:

 - Domestic production of 102 million litres per year of unblended SAF each year, equivalent to 5 per cent of New Zealand’s 2019 total jet fuel uplift of 1.9 billion litres, or 26 per cent of New Zealand’s domestic jet fuel consumption; 
 - Expected carbon savings from use of this fuel of at least 233,000 tonnes of CO2 a year, based on the SAF having at least a 70 per cent reduction compared to fossil jet fuel; 
 - Reduced reliance on imported fuels, enhancing energy security and supply chain resilience; 
 - Adding $428 million to New Zealand’s annual GDP;
 - Domestic production of 11 million litres of renewable diesel each year.

### Imported SAF

We assume that SAF can be imported, and that global markets will supply enough to meet any potential demand. The energy price is based on conventional aviation fuel and an assumed multiplicative factor[^easa]. In New Zealand, the price of conventional jet fuel is 86.4 USD per barrel[^jet_a1_costs], which is equivalent to 0.967 NZD per litre[^jet_conversion_factors]. Applying the multiplier leads to an estimated SAF price of at 82 NZD per GJ.


[^easa]: EASA | [2024 Aviation Fuels Reference Prices for ReFuelEU Aviation](https://www.easa.europa.eu/sites/default/files/dfu/easa_2025_briefing_note_2024_aviation_fuels_reference_prices_for_refueleu_aviation_1.pdf?). The EASA / ReFuelEU reference prices show 2024 average prices of about €734/t for conventional aviation fuel and €2,085/t for bio-SAF, with even higher estimates for synthetic SAF, implying SAF prices around 3× or more conventional fuel on a per-tonne basis.

[^jet_a1_costs]:[NZ JP54, JET A1 price in New Zealand 86.4 bbl/$](https://jet-a1-fuel.com/price/new-zealand?)
[^jet_conversion_factors]: Using the conversion rates: 1 USD = 1.78 NZD and 1 barrel = 159 litres

## Anaerobic digestion

TIMES-NZ includes anaerobic digestion (AD) as the transformation pathway for converting wood waste, agriculture residues, municipal waste, and animal manure into biogas. 
AD is a commercially demonstrated technology that biologically converts organic material into a mixture of methane, carbon dioxide, and nutrient-rich digestate. AD systems can accept a range of feedstocks, including food waste, crops residues, and manures, provided that nutrient and moisture balances are maintained. In practice, most operating facilities blend multiple waste streams to optimise biological performance. Biogas can be used directly for heat or power, while upgraded biomethane can substitute for fossil gas in pipeline or industrial applications. The North Island offers better opportunities due to proximity to large waste streams, existing gas network connections, and easier distribution of biomethane. In contrast, South Island systems would likely serve local heat or vehicle-fuel markets because of higher transport costs for gas or digestate.

A medium-scale anaerobic digestion facility with biogas upgrading and injection capability has an estimated total capital investment of NZD 22 million. (Including the cost of anaerobic digester, biogas upgrading system, grid connection infrastructure, and CO₂ recovery) Based on an indicative annual biogas output of 0.16 PJ, the resulting capital cost intensity is:

```{math}

\frac{\text{22 million NZD}}{\text{0.16 PJ/a}} = 137.5 \text{million NZD per PJ/a}
```



This value is applied in TIMES-NZ as the representative capital cost per unit of new biogas production capacity. Only commercially established AD and upgrading technologies are included in the modelling.

Annual operating and maintenance costs for a facility of this size are approximately NZD 1.2 million per year, including energy use for digestion, pumping, mixing, gas upgrading, and general plant operation. Expressed per unit of annual biogas output, this corresponds to:

```{math}

VAROM = \dfrac{\text{1.2 million NZD/a}}{\text {0.16 PJ/a}} = \text{7.52 NZD per PJ} 

```
## Woody biomass transformation

Woody biomass transformation generally includes several pre-treatment pathways such as chipping, drying, and pelletising. These processes convert forestry residues and sawmill by-products into more uniform fuels with defined efficiencies, energy inputs, and handling characteristics. Only commercially demonstrated technologies are considered. Moisture content is a key determinant of energy value for all wood fuels.

For TIMES-NZ 3.0, only wood chipping was modelled as the transformation from wood waste to usable woody biomass (wood chips). Pelletising and dedicated drying were not included; for the purposes of TIMES-NZ they are currently assumed to be sufficiently similar to wood chipping in terms of overall energy system impact when the full set of costs and benefits are included (such as different boiler technologies). The following section summarises the chipping process and presents the associated capital requirements, operating costs, and energy inputs using the calculations undertaken.

Wood chipping involves the mechanical reduction of logs, residues, or wood waste into uniform chips suitable for industrial boilers, bioenergy systems, or as intermediate feedstock for other processes. The technology is commercially mature and widely deployed in forestry operations, heat plant supply chains, and biomass processing facilities. 

For modelling purposes, a representative medium-scale chipping facility is assumed with the following characteristics:

 - Annual throughput: 300,000 tonnes of wood
 - Electricity consumption: The energy required for mechanical chipping is approximately 40 kWh per tonne, equivalent to just 0.15GJ/t or less than 2% of the total energy contained in the wood itself.
 - A total capital investment of NZD 5 million is assumed for this size of facility. This provides an indicative capital cost metric aligned with the mechanical capacity of the plant. 
 - The chipping process converts wood waste into air-dried wood chips; the appropriate net calorific value (NCV) range is: 13–16 MJ/kg (13–16 GJ/t) for air-dried wood chips. We use a midpoint of 14.5 for our calculation.
- Variable operating cost of NZD 20 per tonne


This results in total annual electricity use of 12GWh, implying a capacity of 1.37MW and a capital cost of 3,650 NZD/kW. The corresponding cost per unit of energy output is 1.395 NZD/GJ. 

## Wood waste to bioethanol 

In New Zealand, bioethanol is primarily produced through the fermentation of sugars and starches, using whey – a dairy by-product – as the main feedstock. Researchers are also exploring lignocellulosic sources such as wood chips, pulp residues, and municipal waste to diversify supply. 

The process typically retains about 65–70% of the feedstock’s original energy, although distillation and drying demand significant energy input. Using geothermal heat or waste-heat recovery could offset some of this requirement. Capital costs are estimated at around NZ /$0.8–1.2 million per million litres (ML) of annual capacity, while operating expenses are driven mainly by energy use and enzyme costs. As of 2023, New Zealand’s production sits at roughly 1.5 ML per year through Anchor Ethanol, with no confirmed expansion plans before 2026. Feedstock supply is concentrated in the North Island, reflecting the location of major dairy processing centres[^diesel_ternary_blends].


To express bioethanol investment costs in NZD per kW of output capacity, the annual ethanol volume must be converted into an equivalent continuous power output.

Energy content of annual production:
 - Energy content of ethanol: 21.2 MJ/L[^biofuel_production]
 - Annual output: 1.5 ML

```{math}

E_{annual} = 21.2_{MJ/L} \cdot 1.5_{ML} = 31,800_{GJ}

```
```{math}

Capacity = \dfrac{38,000 / 3600 }{8760} = 1.008_{MW}

```


TIMES-NZ uses a mid-pint CAPEX assumption of NZD 1 million per ML/year of capacity, for a 1.5 ML/year plant, implying CAPEX costs of 1,488 NZD/kW.

## Oil waste to biodiesel 

Biodiesel in New Zealand is produced via transesterification of animal fats and vegetable oils such as tallow, used cooking oil, and canola. This process achieves around 90% conversion efficiency, with 88–90% of the feedstock’s energy retained in the fuel. It requires moderate energy input – mainly heat for esterification and minimal electricity for separation.

Capital investment is about 1–1.5 million NZD per ML of capacity, while operating costs typically fall between 1.20–1.50 NZD per litre, largely dependent on feedstock prices. National capacity in 2023 was about 4–5 ML per year, led by Greenfuels NZ and several smaller producers. Growth is expected through local waste-oil recovery projects by 2026. Feedstock networks are denser in the North Island, whereas the South Island production depends more on tallow[^diesel_ternary_blends].


Annual energy output:
 - Energy content of biodiesel: 32.7 MJ/L[^biofuel_production]


 ```{math}
E_{annual} = 32.7_{MJ/L} \cdot 4.5_{ML} = 147,150_{GJ}
 ```


```{math}

Capacity = \dfrac{147,150 / 3600 }{8760} = 4.666_{MW}

```

Total capital cost for a 4.5 ML/year facility comes to 5.625 NZDm, implying CAPEX of 1,206 NZD/kW



[^diesel_ternary_blends]: Ayazi, M., Rasul, M. G., Khan, M. M. K., & Hassan, N. M. (2023). Experimental investigation of fuel consumption and emissions of diesel engine fueled with ternary fuel blends of diesel, biodiesel and bioethanol. Energy Reports, 9, 470-475.

[^biofuel_production]: Mahapatra, S., Kumar, D., Singh, B., & Sachan, P. K. (2021). Biofuels and their sources of production: A review on cleaner sustainable alternative against conventional fuel, in the framework of the food and energy nexus. Energy Nexus, 4, 100036.


## Wood waste to advanced or drop-in biofuels

TODO 

## Wood to black pellets

TODO 





