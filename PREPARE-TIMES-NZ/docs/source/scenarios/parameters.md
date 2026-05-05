# Parameters

This section defines how each scenario and critical uncertainty is parameterised within the TIMES-NZ model. All individual changes between scenarios are listed here. Where appropriate more detail may be found in the sector-specific documentation.

## Economic Structure

Demand projections for each subsector define our economic structure assumptions. For industrial subsectors, the detailed projection methods and assumptions are documented in the industrial demand projections methodology.

Energy demand projections in TIMES are specifically for energy service demand. This is the useful service provided by the energy, such as kilometres travelled or water heating. For example, the model would not use projections of natural gas demand. It would instead use projections of space heating demand, then find the least-cost way of meeting this using available technologies and input fuels. One exception to this rule is for ‘new industries’ as discussed below.

Each scenario is intended to imply roughly similar overall economic activity levels, but different components of that economic activity. Note that TIMES is not a full economic model, and so we do not project economic activity, employment, or trade balances. 

The demand profiles (time of use) of each subsector are the same within each scenario, and specific sectors may or may not switch fuels or technologies to meet their demand, if possible and economically efficient.

By using historical energy demand to project energy service demand, we implicitly assume that incremental energy efficiency improvements within sectors continue across the model horizon. However, TIMES-NZ allows for fuel switching and technology upgrades within each sector, which may further increase efficiency and lower total energy demand.

### Industrial

Industrial subsectors use a mix of simple annual growth assumptions and custom sector-specific treatments. The table below reflects the current build assumptions at a summary level.

```{csv-table} Industrial demand projection assumptions
:name: tab_scen_industrial_demand_actual
:header-rows: 1

Subsector,Steady,Shift,Notes
Aluminium,0%,Same as Steady, Assume Tiwai open across full model horizon. 
Construction,1.9% per year,Same as Steady,Based on recent EEUD demand trends.
Dairy,"Tracks ERP2 dairy cattle projections (high)[^erp2_refs]","Tracks ERP2 dairy cattle projection index (low)[^erp2_refs]",""
Iron & Steel,EAF in 2026,Second EAF from 2036,"Steel demand assumed flat, but the demand structure is modified by EAF build timing assumptions"
Meat,0.7% per year,-0.7% per year,Steady follows recent EEUD demand trends; Shift applies an alternative assumption.
Methanol,Closed from 2027,Same as Steady,Closure assumption based on Maui closure timing.
Non-Metallic Mineral Product Manufacturing,0%,-1.0% per year,Steady follows recent EEUD demand trends; Shift applies an alternative assumption.
Mining,1.2% per year,0%,Steady follows recent EEUD demand trends; Shift applies an alternative assumption.
Other Industry,-0.1% per year,Same as Steady,Based on EEUD trends.
Food and Beverage,-1.7% per year,1.7% per year,Steady follows recent EEUD demand trends; Shift applies an alternative assumption.
Chemicals (excl. Urea and Methanol),0%,Same as Steady,Flat demand index
Urea,Flat demand index,Same as Steady,"The Ballance Urea plant can endogenously shrink demand if costs rise above 18 NZD/GJ."
Wood Products,-1.8% per year,1.8% per year,Steady follows recent EEUD demand trends; Shift applies an alternative assumption.
Pulp and Paper,-2.0% per year,Same as Steady,Based on international trends.
New industries,No new industries,"50 GWh of additional electricity demand growth per year from 2026","Generic additional demand intended to represent growth in other areas."
```

### Residential

Residential energy service demand is projected from median Stats NZ national population projections in both scenarios. In the current build, the residential demand driver is population in both Steady and Shift, so there is no scenario differentiation in the exogenous residential demand trajectory itself. The main assumptions are that regional joined/detached dwelling shares remain constant, residents per dwelling remain constant, and other non-technology parameters such as insulation quality or consumer behaviour do not change exogenously over time.


### Commercial

Commercial demand growth assumptions are split by subsector and listed in the table below.

```{csv-table} Commercial demand assumptions
:name: tab_scen_commercial_demand
:header-rows: 1

Subsector,Steady,Shift
Data centres,NZTech 2025 Baseline pathway[^nztech_datacentres],NZTech Faster Uptake pathway[^nztech_datacentres]
Education,Population growth index,Same as Steady
Healthcare,Population growth index,Same as Steady
"Warehouses, Supermarkets, Retail (WSR)",GDP growth index,Same as Steady
Office Blocks / Professional Services,GDP growth index,Same as Steady
Other,GDP growth index,Same as Steady
```

Data centres are described in more detail in {numref}`tab_scen_parms_datacentre_demand` below. 

```{csv-table} Growth rates of energy service demand for datacentres
:name: tab_scen_parms_datacentre_demand 
:header-rows: 1 

Steady,Shift
"Data centre demand growth follows the NZTech 2025 Baseline scenario[^nztech_datacentres]. Growth is based on planned deployed capacity, with the assumption that as new builds come online and customers are onboarded, the proportion of non-vacant space remains steady across the forecast period. The average power usage effectiveness (PUE) is assumed to remain constant, though power-drawn load gradually rises as utilisation increases.","Demand is driven by a combination of accelerated digital uptake (boosted by AI) and ongoing efficiency improvements. Deployed capacity reflects higher uptake as the new baseline, with committed capacity filling more quickly and power-drawn load increasing at a faster pace compared to the steady scenario."
```

Population growth assumptions remain the same in each scenario, following central projections, and therefore the energy service demand from population driven subsectors (Education and Healthcare) remain the same in both scenarios. Similarly, our current assumption is that energy service demand in the warehouses, supermarkets and retail (WSR), professional services/offices, and ‘other’ sub-sectors grows with GDP, which is assumed to be the same in both scenarios.

### Agriculture, Forestry and Fishing

Agriculture, forestry, and fishing demand projections are based on ERP2 activity series[^erp2_refs] rather than simple constant growth rates. In the current build, most Steady mappings use ERP2 Baseline, while Shift generally uses ERP2 Baseline low. Dairy Cattle Farming is an exception, using Baseline high in Steady. Where ERP2 provides only selected years, annual values are linearly interpolated.

```{csv-table} Agriculture, forestry and fishing demand assumptions
:name: tab_scen_agr_demand
:header-rows: 1

Subsector,Steady,Shift
Dairy Cattle Farming,Baseline high / Total dairy cattle (ERP2),Baseline low / Total dairy cattle (ERP2)
Livestock Farming,"Baseline / Sheep and beef 'stock units'","Baseline low / Sheep and beef 'stock units'"
Horticulture (Outdoor),Baseline / Horticulture,Baseline low / Horticulture
Indoor Cropping,Baseline / Horticulture,Baseline low / Horticulture
Forestry and Logging,Baseline / Forestry (million m3) / Harvested timber (TRV),Baseline low / Forestry (million m3) / Harvested timber (TRV)
Other Agriculture,Baseline / Other agriculture / Total,Baseline low / Other agriculture / Total
"Fishing, Hunting and Trapping",Constant index = 1,Constant index = 1
```


## Technology costs

An additional assumption which differentiates the scenarios is that the greater degree of global trade opportunities arising in the Shift scenario accelerates the rate at which some technology costs fall.

```{csv-table} Impacts of the degree of free trade on technology costs 
:name: tab_scen_techtrade
:header-rows: 1

Parameter,Steady,Shift
"Generation technology (offshore/onshore wind, solar) and electric vehicle costs","Generation technology and BEV/Hybrid vehicle costs follow expected trends (Using NREL Moderate scenario)",Generation technology and electric vehicle costs reduce faster (Using NREL Advanced scenario) 
Utility-scale and distributed battery technology,"Costs follow expected trends, following the CSRIO Current Policy scenario","Battery costs reduce faster, following the CSIRO NZE by 2050 scenario"
Process heat demand technologies,Existing process heat technology costs remain constant in real terms. New process heat technology costs reduce.,Same as Steady
```

## Individualistic or cooperative

This key uncertainty describes policy settings and consumer behaviour, and influences how we prioritise sustainability against affordability and energy security.

```{csv-table} National outlook parameters
:name: tab_scen_ind_coop
:header-rows: 1

Parameter,Steady,Shift
Carbon price,Reaches $52/tonne by 2035 then stabilises[^mfe_erp2_detail],"Reaches $260/tonne by 2050, matching the Climate Change Commission’s updated demonstration path[^ccc_demopath]."
Consenting environment for electricity generation projects,"Some community resistance to new generation. The electricity generation pipeline is slightly constrained, using the EDGS Reference scenario[^genstack].","No community resistance to new generation. More plants made available to the pipeline, using the additional plants from the EDGS Innovation scenario[^genstack]."
Travel mode shifting,Standard VKT demand projections (using MoT projections),Passenger VKT per capita decreases by 1% annually. This leads to roughly flat passenger VKT demand over time. 
Residential hot water peak load shifts, 50% of peak demand can be shifted, Level of demand shift grows to 90% by 2050
Low Emission Heavy Vehicle Fund,Ends in 2028,Continues to 2032
Discount rate: Public sector[^tsy_discount],8%,2%
Discount rate: Businesses[^firm_discount],10%,"8% default rate and 5% for green investments. This reflects a longer-term view being taken across the economy, and a focus of global finance on green investments."
Discount rate: Households[^hh_discount],As per businesses.,As per businesses.
```
[^mfe_erp2_detail]: MFE | [ERP2 Detailed results (.xlsx)](https://environment.govt.nz/assets/publications/climate-change/ERP2/Detailed-results-for-ERP2-projection-scenarios.xlsx)
[^erp2_refs]: MPI | New Zealand's second emissions reduction plan 2026-30: [Technical Annex](https://environment.govt.nz/publications/second-emissions-reduction-plan-technical-annex/) and [Detailed Results (.xlsx)](https://view.officeapps.live.com/op/view.aspx?src=https%3A%2F%2Fenvironment.govt.nz%2Fassets%2Fpublications%2Fclimate-change%2FERP2%2FDetailed-results-for-ERP2-projection-scenarios.xlsx&wdOrigin=BROWSELINK)
[^nztech_datacentres]: NZTech (2025). [Empowering Aotearoa New Zealand’s Digital Future: Our national data centre infrastructure](https://technewzealand.org.nz/wp-content/uploads/sites/8/2025/09/NZTech-Data-Centres-Report-Final-DIGITAL-002.pdf)

[^genstack]: EDGS 2024 generation stacks available at: [Electricity Demand and Generation Scenarios (EDGS)](https://www.mbie.govt.nz/building-and-energy/energy-and-natural-resources/energy-statistics-and-modelling/energy-modelling/electricity-demand-and-generation-scenarios)
[^ccc_demopath]: Climate Change Commission | [Updated demonstration path and current policy reference settings (.xlsx)](https://view.officeapps.live.com/op/view.aspx?src=https%3A%2F%2Fwww.climatecommission.govt.nz%2Fassets%2FAdvice-to-govt-docs%2FERP2%2Fdraft-erp2%2Fsupporting-documents%2FERP2-supporting-spreadsheet-Updated-demonstration-path-and-CPR-2022.xlsx)




[^tsy_discount]: The 8% and 2% rates are taken from Treasury’s [public sector discount rates](https://www.treasury.govt.nz/information-and-services/public-sector-leadership/guidance/reporting-financial/discount-rates). For ease of implementation in TIMES-NZ, these are applied to schools and hospitals only. This excludes defence (which sits within ‘other’), other smaller categories, and the public sector vehicle fleet.
[^firm_discount]: Private firm discount rates of 10% and 8% are representative of weighted average cost of capital (WACC) for different companies. See for example PWC's [Cost of Capital Report 22](https://www.pwc.co.nz/pdfs/2022/cost-of-capital-report-2022.pdf). The 5% rate is based on an assumed discounted rate for green finance (in the Shift scenario only).
[^hh_discount]: We propose to use the same discount rates for businesses and households. This is contrary to the evidence that consumer decision making is generally based on higher discount rates. For example, the US Energy Information Administration’s discount rate use for representing residential consumer behaviour is 20%. See: [Residential Demand Module of the National Energy Modeling System: Model Documentation 2025](https://www.eia.gov/outlooks/aeo/nems/documentation/residential/pdf/RDM_AEO2025.pdf). On the other hand, many consumers do have access to lower cost finance through mortgages and green loans (where the rate is lower than that for businesses). Our assumption of equivalent discount rates therefore implies a slightly higher risk premium being applied by households, relative to businesses, but not the full extent of ‘hyperbolic discounting’.

## Natural gas


We assume that indigenous supply follows the latest reserve estimates. We also assume that investment uncertainty means that there is no successful exploration of new fields in either scenario. 

In the Steady scenario, we assume government support allows investment in LNG imports, although the model will only invest in LNG if it is the least-cost option for the energy system.

In the Shift scenario, we instead assume that investment is focused on sustainable alternatives, such as biomass, biogas, or hydrogen, and LNG is not considered. Domestic production in both scenarios follows the latest MBIE 2P production profiles, with Maui assumed to close at the end of 2026.


```{csv-table} Gas supply parameters
:name: tab_scen_gas
:header-rows: 1

Parameter,Steady,Shift
Proven plus probable reserves,Follows availability and deliverability of the latest MBIE 2P production profiles,Same as Steady
Domestic natural gas wholesale price,Rises to $35/GJ as indigenous supply declines,Same as Steady
LNG supply,Standard LNG terminal available in 2027 if selected by the model as the least-cost option,LNG not available in Shift scenario
Biogas supply,"Base bioenergy supply assumptions. Municipal organic waste fixed at 5.035 PJ/year and animal manure fixed at 7.56 PJ/year; additional biogas potential remains limited by current recovery settings.","Higher bioenergy supply assumptions. Municipal organic waste and animal manure supply each scale significantly from 2026 onward, assuming new policies allow for much greater collection rates."
Biomass supply,"Woody residues, agricultural residues, and municipal wood waste use Scion regional biomass projections[^scion_biomass] scaled with Recoverability factor 2 (% of gross).","The same feedstocks use the higher Recoverability factor 1 (% of gross), increasing accessible biomass supply from 2026 onward."
Hydrogen supply,"Hydrogen is produced only via electrolysis. Costs follow the CSIRO/Aurecon Current Policies pathway, with 2035 electrolyser CAPEX of about NZD 2,120-2,225/kW and 2050 CAPEX of NZD 1,732-1,824/kW depending on technology.","Hydrogen is produced only via electrolysis. Costs follow the CSIRO Post 2050 net zero pathway, with lower 2035 electrolyser CAPEX of about NZD 1,331-1,396/kW and 2050 CAPEX of NZD 1,127-1,183/kW."
```

[^scion_biomass]: IEA Bioenergy | [Residual biomass fuel projections for New Zealand; 2024](https://www.ieabioenergy.com/wp-content/uploads/2024/11/NZ-Woody-Biomass-Residues-and-Resources-2024.pdf). Peter Hall, Scion.
