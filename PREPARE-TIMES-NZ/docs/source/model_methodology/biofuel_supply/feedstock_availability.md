# Feedstock availability

Feedstock availability assumptions in TIMES-NZ are based on RETA datasets[^reta], Scion’s projections for the IEA Bioenergy Technology Collaboration Programme[^iea_bioenergy_projections], and Beca–EECA biogas studies. For each feedstock type, the model applies annual availability limits, recoverability factors, and delivered-cost ranges. These limits represent the fraction of technically available resources that can be economically mobilised under the Steady and Shift scenarios.

```{figure} figures/feedstock_supply_projections.png
---
name: fig_bio_supply_proj
alt: Feedstock supply projections
---

Feedstock supply projections
```


[^reta]: EECA | [Regional Energy Transition Accelerator](https://www.eeca.govt.nz/co-funding-and-support/products/about-reta/)

[^iea_bioenergy_projections]: IEA Bioenergy | [Residual biomass fuel projections for New Zealand; 2024](https://www.ieabioenergy.com/wp-content/uploads/2024/11/NZ-Woody-Biomass-Residues-and-Resources-2024.pdf). Peter Hall, Scion.


## Domestic wood waste 


TIMES-NZ adopts Scion’s 2024–2053 projections for forestry residues, sawmill by-products, and municipal wood waste. These projections provide gross resource quantities, regional distribution, calorific values, and long-term harvest cycles.

Gross woody biomass generation is assumed at ~8 million green tonnes/year, inclusive of logs, chips, bark, thinnings, and slash. Municipal wood waste rises with population, with gross availability plotted nationally and by region (noted as growing over time).

TIMES-NZ applies the below recoverability factors depending on residue type. 




```{csv-table} Recoverability factors for wood residue
:name: tab_bio_residue_recoverable
:header-rows: 1 

Residue type,Recoverability factor 1 (% of gross),Recoverability factor 2 (% of gross)
In-forest residues – landings,0.8,0.65
In-forest residues - cutover,0.7,0.55
Wood processing residues,0.95,0.9
Municipal wood waste,0.8,0.6
Port bark,0.8,0.7
Horticultural residues,0.8,0.65
Straw and Stover,0.7,0.6
Shelter belt residuals,0.8,0.6
Production thinnings residuals,0.8,0.5
Waste thinnings,0.5,0.25
Prunings,0.3,0.15
Pulp log,0.95,0.9
Sawmill chip,0.75,0.5
K grade logs,0.95,0.8
A grade logs,0.9,0.8
Douglas-fir production thinnings,0.8,0.5
```

The estimated costs of producing fuel from wood residue, municipal wood waste, and slash are shown in {numref}`tab_bio_biomass_cost_estimates`. These figures are estimates and indicate production costs, not actual market prices, which could be higher. The estimates are based on operating costs as of January 2022. The total costs include a payment to the owner of the residual biomass, which varies depending on the type of material. They also include transport costs, assuming an average transport distance of 90 kilometres from the source of the residue to the end user.

```{csv-table} Estimated costs for various biomass resources delivered (90km) in fuel form.
:name: tab_bio_biomass_cost_estimates
:header-rows: 1 

Residue type,Owner's fee (NZD/green tonne),Cost (NZD/green tonne),Cost (NZD/GJ)
Port bark,$5,$21,$3.04
Shelter belt residuals,$20,$36,$3.27
Horticultural residues,$10,$26,$3.77
Municipal wood waste,$10,$30,$4.35
Wood processing residues,$20,$48,$7.02
Pulp log,$59,$59,$8.55
Straw and stover[^straw_wet],$100,$130,$11.82
In-forest residues - landings,$25,$85,$12.32
Douglas-fir production thinnings ,$65,$93,$13.48
In-forest residues – cutover,$20,$94,$13.62
Production thinnings residuals,$20,$95,$13.77
K grade logs,$95,$95,$13.77
Waste thinnings,$20,$105,$15.22
Sawmill chip,$80,$108,$15.71
A grade logs,$117,$117,$16.96
Prunings ,$5,$120,$17.39
Stumps,$25,$145,$21.07
```

[^straw_wet]: Straw is assumed to have a “green” moisture content of 15% wet basis

Delivered wood fuel costs are assumed to remain broadly stable in real terms over time. This reflects increasing market maturity, additional suppliers entering the sector, and economies of scale in biomass processing. The model does not assume structural upward price pressure beyond standard cost escalation factors.

The available quantities reflect long-term supply projections, which reach their lowest point between 2036 and 2040. The overall deficit is around 8% of the total demand.

## Agricultural waste (straw/stover, fruit/vegetable culls)
Gross straw/stover availability is concentrated in Canterbury (~70% of national supply). TIMES-NZ applies a mandatory 50% retention constraint for soil health. Residual volumes use recoverability factors of 70% reflecting field losses, access constraints, and competing uses. Orchard and vineyard residues are modelled using turnover rates of 4–12% annually and recoverability factors of 80%. Regional supply availability is highest in Hawke’s Bay, Nelson, and Gisborne. 

## Municipal waste

Municipal waste data is based on a 2021 report by Beca, Firstlight Group, Fonterra, and EECA[^feedstock_analysis]. Municipal food-waste availability is assumed at ~354,000 t/year[^reynolds] (1.5 PJ/year biogas potential) under current recovery conditions. Scenario-dependent source-segregation increases allow up to 15–20 PJ/year potential in Shift. Urban areas such as Auckland and Christchurch contain the largest recoverable volumes. Although 90% of organic waste goes to landfills with gas capture, average efficiency is only about 68%, and most gas is flared rather than used. Industrial organic waste streams contribute an additional 3–4 PJ/year of potential feedstock. Recovery is constrained by fragmented organic waste streams, limited source-segregated collection, high costs for recovery and preprocessing, and insufficient infrastructure for gas upgrading, grid injection, and digestate management. 

Feedstock availability from food waste will increase as more councils adopt source-segregated collection systems. There are currently 71 facilities operating nationwide, and this number is expected to rise as landfill levies increase, and emissions targets tighten. Purpose-built anaerobic digestion (AD) facilities such as the Reporoa plant indicate the emerging capacity to process segregated food waste at scale. With continued expansion of municipal collection systems and improved public participation, the volume of recoverable feedstock is expected to grow substantially over the next decade. However, many regulatory, economic, and behavioural barriers remain unresolved[^blunomy]. Low landfill levies weaken incentives for diversion and create investment uncertainty. If these barriers were addressed through a clear national framework, strong policy support, and targeted incentives, AD deployment could scale to levels comparable with international peers. Denmark (population 5.8 million) produces around 20 PJ of biogas annually. Under similar regulatory certainty and investment conditions, New Zealand could plausibly achieve 20–23 PJ per year, equivalent to roughly 20 percent of current gas demand (117.7 PJ in 2024).

Municipal food waste is the most visible organic feedstock, yet treatment capacity is constrained. The Ecogas Reporoa Organics Processing Facility, one of the country’s largest AD plants, processes around 75,000 tonnes of waste annually – primarily from Auckland – producing 0.22–0.25 PJ of biomethane per year. The 30 million NZD investment equates to roughly 15,000NZD per Nm³/h of capacity, aligning with national estimates of 20,000–65,000NZD per Nm³/h depending on technology and location. Annual operating costs are around 1 million NZD, largely from gas-upgrading energy use (~0.4 kWh per Nm³ biomethane). Beyond gas injection to the North Island grid, Reporoa also recovers heat and CO₂ for nearby glasshouse operations, yielding about 2.5 GJ per tonne of feedstock.

## Commercial and industrial food waste 

Industrial and food-processing sites, particularly in the dairy sector, already generate biogas through high-COD effluent digestion. For example, Fonterra’s Tirau plant produces about 12 TJ annually, offsetting fossil gas on-site. Across New Zealand, around 0.5 PJ per year of additional biomethane potential exists in this sector – mostly consumed internally rather than upgraded for grid injection. Investment costs for industrial digesters are 20,000–30,000 NZD per Nm³/h, similar to municipal systems, while operating costs and electricity demand (≈ 0.4 kWh per Nm³ biomethane) are comparable. High-rate hydraulic digesters for liquid effluents average about 27,000 NZD per Nm³/h. Financial modelling (Beca report) indicates break-even at ~5 NZD/GJ, with a 10-year payback near 21 NZD/GJ once revenues from CO₂ and digestate are included.


[^feedstock_analysis]: Note that EECA is currently working on New Zealand organic feedstock analysis project which, once completed, will provide a more fulsome and complete picture of municipal waste available for energy. [Biogas and Biomethane in NZ - Unlocking New Zealand's Renewable Natural Gas Potential](https://www.beca.com/getmedia/4294a6b9-3ed3-48ce-8997-a16729aff608/Biogas-and-Biomethane-in-NZ-Unlocking-New-Zealand-s-Renewable-Natural-Gas-Potential.pdf)

[^reynolds]: Reynolds et al. (2016)
[^blunomy]: Blunomy (2023)


```{csv-table} Municipal, commercial and industrial food waste supply
:name: tab_bio_food_waste_supply
:header-rows: 1 

Category,Feedstock,Quantity (wet t/year),Methane yield (m3 CH4/wet tonne),Max biogas potential (PJ/year)
Municipal waste,Source-segregated food waste,0.354m,128,1.5
Municipal waste,Municipal wastewater,N/A,N/A,0.735
Industrial wastewater,Dairy,67.4m,0.50 – 0.84,1.5
Industrial wastewater,Meat,22m,1.0,0.72
Industrial wastewater,Pulp and paper,36.1m,0.49,0.58
```

TIMES-NZ 3.0 assumes a constant total energy supply of 5.035 PJ from municipal solid waste, wastewater, and industrial wastewater. This supply is expected to remain steady over time.

## Animal manure 

TIMES-NZ adopts national manure-based biogas potential of 5–6 PJ/year (dairy, poultry, piggery). Co-digestion with food or industrial organics can enhance methane yield by 15-25%. Regional concentrations (Waikato, Canterbury, Southland) support clustered anaerobic digestion hubs. Current estimates suggest potential yields of approximately 1.3 PJ per year from poultry manure and 0.36 PJ per year from pig manure[^pig_manure], assuming full collection. However, as more farms transition to free-range systems, the accessible feedstock volume may decline.

```{csv-table} Summary of available animal manure feedstocks in New Zealand[^beca_biomass]
:name: tab_bio_manure_supply
:header-rows: 1 

Feedstock,Wet tonne/year,Methane yield (m3 CH4/wet tonne),Max biogas potential (PJ/year)
Dairy manure,5.32m,39,5.9
Pig manure,0.281m,39,0.36
Poultry manure,0.825m,49,1.3
```


[^pig_manure]: Jain, S. (2019). Global Potential of Biogas. <https://www.worldbiogasassociation.org/wpcontent/uploads/2019/09/WBA-globalreport-56ppa4_digital-Sept-2019.pdf>
[^beca_biomass]: BECA | [Biogas and Biomethane in New Zealand](https://www.beca.com/getmedia/4294a6b9-3ed3-48ce-8997-a16729aff608/Biogas-and-Biomethane-in-NZ-Unlocking-New-Zealand-s-Renewable-Natural-Gas-Potential.pdf)

Poultry manure, with its favourable carbon-to-nitrogen ratio, offers high biogas yields (50–100 m³/wet tonne), while pig manure yields range from 40–80 m³/wet tonne. Dairy farms remain heavily concentrated in the North Island (71.1% of herds), with Waikato holding the largest share. Poultry farms are assumed to cluster around major urban centres, while pig production is split 66% in the South Island and 34% in the North. 

In TIMES-NZ 3.0, this supply is expected to remain steady over time.

## Tallow and cooking oil waste


Biodiesel in New Zealand is produced by transesterifying feedstocks such as animal-fats (notably tallow), used cooking oil (UCO) and vegetable oils (e.g., canola). Tallow is generated as an abattoir-by-product with an estimated production ~160 000 t/year in 2021. This represents a biodiesel potential of 122,000 t[^gic_gtp_biogas] biodiesel/year (4.5 PJ/year) (scaled from biodiesel production). New Zealand had one biodiesel plant in Wiri which was mothballed in 2020 due to the global price increase for tallow. Waste cooking oil is estimated at between 5 000 - 7 000 t/year available for biodiesel use. Much of what exists is already allocated to use within industries for a heat source (such as cement and asphalt manufacture, greenhouse heating). Vegetable oil (canola) production is limited (~15 000 t/year) with the majority sold as edible oil.

Accordingly, TIMES-NZ 3.0 assumed a tallow supply of 6.240 PJ and waste cooking oil of 0.234 PJ considering a calorific value of 39 MJ/kg[^biodiesel_prod]. This supply is expected to remain steady over time but will be adjusted in the future based on growth factors.

[^gic_gtp_biogas]: Gas Industry Co | [Gas Transition Plan - Biogas Research Report] (https://www.gasindustry.co.nz/assets/CoverDocument/Gas-Transition-Plan-Biogas-Research-Report-February-2023.pdf)
[^biodiesel_prod]:Sharif, Y. A., & Akosman, C. (2025). [Biodiesel Production Using Vegetable Oil and Animal Fat Mixtures](https://dergipark.org.tr/en/download/article-file/4429814). Turkish Journal of Science and Technology, 20(1), 259-268.

## Regional and sector insights

The North Island benefits from stronger gas-grid connections, enabling biomethane injection, while the South Island is better suited to local utilisation for heat and transport. Integration of municipal, commercial, and industrial feedstocks underpins the economic case for AD, with moderate operating costs, scalable yields, and predictable output. As these facilities mature, performance data will help optimise feedstock efficiency, emissions reduction, and cost structure – guiding future renewable gas infrastructure deployment nationwide. The regional splits for wood waste are based on Scion’s 2024–2053 projections, while splits for other fuels are based on the assumptions noted in the table below.

```{csv-table} Regional splits based on bioenergy type 
:name: tab_bio_regions
:header-rows: 1 

Feedstock,NI,SI,Notes
"Municipal, commercial and industrial food waste",77%,23%,Based on regional population
Animal Manure,56%,44%,Based on total pigs and dairy cattle numbers
Waste Cooking Oil,77%,23%,Based on regional population
Tallow Waste,,100%,100% SI assumption
```
While biomethane could technically contribute to dispatchable generation (e.g. gas peakers), bioenergy technologies are not currently enabled to compete as firming or peak-serving capacity in the electricity supply module. This modelling boundary should be considered when interpreting relative electrification and bioenergy outcomes.

