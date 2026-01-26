# Parameters

This section defines how each scenario and critical uncertainty is parameterised within the TIMES-NZ model. 

## Economic Structure

Demand projections for each subsector define our economic structure assumptions. These are listed in {numref}`scen_parms_ind_demand` below. 

Energy demand projections in TIMES are specifically for energy service demand. This is the useful service provided by the energy, such as kilometres travelled or water heating. For example, the model would not use projections of natural gas demand. It would instead use projections of space heating demand, then find the least-cost way of meeting this using available technologies and input fuels. One exception to this rule is for ‘new industries’ as discussed below.

For the Traditional scenario, we use the average growth rates in energy demand for the last 6 years from EECA’s Energy End Use Database (EEUD) and extrapolate these as energy service demand projections across the forecast horizon. The compound annual average growth rates used are listed below. For some subsectors, such as Aluminium, we have set growth rates to zero to imply continuous production. 

For the Transformation scenario, we select specific sectors to invert growth (or contraction) rates, representing the economic structure shifting over time. We model a short transition period (e.g. 5 years) to avoid this being an unrealistic step change. We also include a category for ‘new industries’. This is intended to represent the growth of advanced manufacturing, and is considered to be solely electricity demand. We do not model specific technologies (with specific conversion efficiencies) and so the demand is expressed directly as electricity demand, rather than energy service demand.

Each scenario is intended to imply roughly similar overall economic activity levels, but different components of that economic activity. Note that TIMES is not an economic model, and so we do not project economic activity, employment, or trade balances. 

The demand profiles (time of use) of each subsector are the same within each scenario, and specific sectors may or may not switch fuels or technologies to meet their demand, if possible and economically efficient.

By using historical energy demand to project energy service demand, we implicitly assume that incremental energy efficiency improvements within sectors continue across the model horizon. However, TIMES-NZ allows for fuel switching and technology upgrades within each sector, which may further increase efficiency and lower total energy demand.

```{csv-table} Annual growth rates of energy service demand for industrial subsectors
:name: scen_parms_ind_demand
:header-rows: 1 

Subsector,Traditional,Transformation
Aluminium,0% ,Same as Traditional
Construction,1.9%,Same as Traditional
Dairy,2.8%  ,-2.8%  
Iron/steel,EAF operational in 2026,Second EAF operational in 2036 
Meat,0.7%,-0.7%  
Methanol,Methanex exits in line with available gas supply,Same as Traditional
Non-Metallic Mineral Product Manufacturing,-4.6%,Same as Traditional
Mining,1.2%,0%
Other,-0.1%,Same as Traditional
Other Food Manufacturing,-1.7%,1.7%
"Other chemicals – excl. methanol, urea",0%,Same as Traditional
Urea,Ballance exits in line with available gas supply,Same as Traditional
Wood products,-1.8%,1.8%
Pulp and paper,-6.9%,Same as Traditional
New industries,No new industries,50GWh of electricity demand growth per annum. 
```

These assumptions result in the following demand curve projections to be used in the model: 



```{figure} figures/industry_projections_input_energy.png
---
name: fig_industry_projections_input_energy
alt: Industrial sector demand curve projections
---
Industrial sector demand curve projections
```



It is important to note that these projections reflect energy demand projections assuming technologies and fuels remain the same as they were in our model’s base year (2023). They are therefore illustrative only. In the actual model results, efficiency improvements or fuel switching mean that the final energy demand for these sectors will shift over time. 

We do not set exogenous projections for Methanol or Urea demand. Rather, we explicitly allow the model to reduce demand in these sectors to reflect potential deindustrialisation. The marginal price for these is set at 15 NZD/GJ for Methanol, and 18 NZD/GJ for Urea production, reflecting the potential value of lost load[^gas_voll]. These figures are initial estimates only and are subject to feedback and revision.

We further assume increased energy service demand for data centres and professional services in the Transformation scenario, as described in Table 2 on the following page.


[^gas_voll]: These are the assumed wholesale prices at which these businesses may exit the market if alternative feedstocks cannot be sourced. TIMES-NZ makes no effort to estimate the cost pressures faced by individual businesses, so they are necessarily rough estimates. 


We further assume increased energy service demand for data centres in the Transformation scenario, as described in {numref}`scen_parms_datacentre`.


 
```{csv-table} Growth rates of energy service demand for datacentres
:name: scen_parms_datacentre demand 
:header-rows: 1 

Traditional,Transformation
"Data centre demand growth follows the NZTech 2025 Baseline scenario. Growth is based on planned deployed capacity, with the assumption that as new builds come online and customers are onboarded, the proportion of non-vacant space remains steady across the forecast period. The average power usage effectiveness (PUE) is assumed to remain constant, though power-drawn load gradually rises as utilisation increases.","Demand is driven by a combination of accelerated digital uptake (boosted by AI) and ongoing efficiency improvements. Deployed capacity reflects higher uptake as the new baseline, with committed capacity filling more quickly and power-drawn load increasing at a faster pace compared to the traditional scenario."
```

Population growth assumptions remain the same in each scenario, following central projections, and therefore the energy service demand from population driven subsectors (Education and Healthcare) remain the same in both scenarios. Similarly, our current assumption is that energy service demand in the warehouses, supermarkets and retail (WSR), professional services/offices, and ‘other’ sub-sectors grows with GDP, which is assumed to be the same in both scenarios.


## Geopolitical forces 

Geopolitical forces that influence global commodity demand, such as export demand for New Zealand’s agricultural products, are already parameterised under “Economic Structure”. An additional assumption which differentiates the scenarios is that that the greater degree of global trade opportunities arising in the Transformation scenario accelerate the rate at which some technology costs fall.

```{csv-table} Impacts of the degree of free trade on technology costs 
:name: tab_scen_techtrade
:header-rows: 1

Parameter,Traditional,Transformation
"Generation technology (offshore/onshore wind, solar) and electric vehicle costs","Generation technology and BEV/Hybrid vehicle costs follow expected trends (Using NREL Conservative scenario)",Generation technology and electric vehicle costs reduce faster (Using NREL Moderate scenario) 
Utility-scale and distributed battery technology,"Costs follow expected trends, following the CSRIO Current Policy scenario","Battery costs reduce faster, following the CSIRO NZE by 2050 scenario"
Process heat demand technologies,Existing process heat technology costs remain constant in real terms. New process heat technology costs reduce.,Same as Traditional
```

## Individualistic or cooperative

This key uncertainty describes policy settings and consumer behaviour, and influences how we prioritise sustainability against affordability and energy security.

```{csv-table} National outlook parameters
:name: tab_scen_ind_coop
:header-rows: 1

Parameter,Traditional,Transformation
Carbon price,Reaches $52/tonne by 2035 then stabilises[^mfe_erp2_detail],"Reaches $260/tonne by 2050, matching the Climate Change Commission’s updated demonstration path[^ccc_demopath]."
Consenting environment for electricity generation projects,"Some community resistance to new generation. The electricity generation pipeline is slightly constrained, using the EDGS Reference scenario[^genstack].","No community resistance to new generation. More plants made available to the pipeline, using the additional plants from the EDGS Innovation scenario[^genstack]."
Travel mode shifting,Standard VKT demand projections (using MoT projections),Passenger VKT per capita decreases by 1% annually. This leads to roughly flat passenger VKT demand over time. 
Low Emission Heavy Vehicle Fund,Ends in 2028,Continues to 2032
Discount rate: Public sector[^tsy_discount],8%,2%
Discount rate: Businesses[^firm_discount],10%,"8% default rate and 5% for green investments. This reflects a longer-term view being taken across the economy, and a focus of global finance on green investments."
Discount rate: Households[^hh_discount],As per businesses.,As per businesses.
```
[^mfe_erp2_detail]: MFE | [ERP2 Detailed results (.xlsx)](https://environment.govt.nz/assets/publications/climate-change/ERP2/Detailed-results-for-ERP2-projection-scenarios.xlsx)

[^genstack]: EDGS 2024 generation stacks available at: [Electricity Demand and Generation Scenarios (EDGS)](https://www.mbie.govt.nz/building-and-energy/energy-and-natural-resources/energy-statistics-and-modelling/energy-modelling/electricity-demand-and-generation-scenarios)
[^ccc_demopath]: Climate Change Commission | [Updated demonstration path and current policy reference settings (.xlsx)](https://view.officeapps.live.com/op/view.aspx?src=https%3A%2F%2Fwww.climatecommission.govt.nz%2Fassets%2FAdvice-to-govt-docs%2FERP2%2Fdraft-erp2%2Fsupporting-documents%2FERP2-supporting-spreadsheet-Updated-demonstration-path-and-CPR-2022.xlsx)




[^tsy_discount]: The 8% and 2% rates are taken from Treasury’s [public sector discount rates](https://www.treasury.govt.nz/information-and-services/public-sector-leadership/guidance/reporting-financial/discount-rates). For ease of implementation in TIMES-NZ, these are applied to schools and hospitals only. This excludes defence (which sits within ‘other’), other smaller categories, and the public sector vehicle fleet.
[^firm_discount]: Private firm discount rates of 10% and 8% are representative of weighted average cost of capital (WACC) for different companies. See for example PWC's [Cost of Capital Report 22](https://www.pwc.co.nz/pdfs/2022/cost-of-capital-report-2022.pdf). The 5% rate is based on an assumed discounted rate for green finance (in the Transformation scenario only).
[^hh_discount]: We propose to use the same discount rates for businesses and households. This is contrary to the evidence that consumer decision making is generally based on higher discount rates. For example, the US Energy Information Administration’s discount rate use for representing residential consumer behaviour is 20%. See: [Residential Demand Module of the National Energy Modeling System: Model Documentation 2025](https://www.eia.gov/outlooks/aeo/nems/documentation/residential/pdf/RDM_AEO2025.pdf). On the other hand, many consumers do have access to lower cost finance through mortgages and green loans (where the rate is lower than that for businesses). Our assumption of equivalent discount rates therefore implies a slightly higher risk premium being applied by households, relative to businesses, but not the full extent of ‘hyperbolic discounting’.

## Natural gas


We assume that indigenous supply follows the latest reserve estimates. We also assume that investment uncertainty means that there is no successful exploration of new fields in either scenario. 

In the Traditional scenario, we assume there is greater investment in the upstream sector, and therefore some contingent reserves can be released to the market. We also assume government support allows investment in LNG imports, although the model will only invest in LNG if it is the least-cost option for the energy system.

In the Transformative scenario, we instead assume that investment is focused on sustainable alternatives, such as biomass, biogas, or hydrogen, and LNG is not considered.


```{csv-table} Gas supply parameters
:name: tab_scen_gas
:header-rows: 1

Parameter,Traditional,Transformation
Proven plus probable reserves,Follows availability and deliverability of latest 2P production profiles,Same as Traditional
Contingent reserves,60% of domestic contingent (2C) reserves are made available to the market.,No domestic contingent reserves are made available to the market
Domestic natural gas wholesale price,Rises to $35/GJ as supply falls to 0.,Same as Traditional
LNG supply,LNG import options are made available for model investment from 2028.,LNG not available in Transformation scenario
Alternative fuel supply,"Biogas, biomass, and hydrogen costs and availability follow conservative projections",Alternative fuel costs are reduced and availability increased.
```