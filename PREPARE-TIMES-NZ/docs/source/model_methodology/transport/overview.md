# Overview 

TIMES-NZ produces a model solution that meets the projected energy demand while minimising costs. For the transport sector, this means determining how to meet future passenger and freight mobility needs using existing and emerging future technologies, fuels, and infrastructure while accounting for energy efficiency, cost, emissions, and other constraints. The model uses detailed costs and technical parameters of: 
 - Existing vehicle fleet
 - Potential future fleet
 - Fuel types
 - Electric Vehicle (EV) chargers


## Scenario adjustments 


The different TIMES-NZ 3.0 scenarios, Steady and Shift, are created by varying vehicle cost and transport demand parameters. 

### Vehicle costs
We assume the costs of future transport technologies fall over time as technology matures, and the assumed rates of cost decline are varied across scenarios. We use the National Renewable Energy Laboratory (NREL)[^nrel_transport_atb] cost projection scenarios for TIMES-NZ. The Conservative scenario is used for the Steady pathway, and the Moderate scenario is used for Shift. The Advanced scenario is not currently used, reflecting the fact that New Zealand’s market maturity and supply chains are behind those of the US.
These cost reduction curves are applied to electric vehicles, hybrid vehicles, plug-in hybrids, and hydrogen fuel cell EVs. 

### Transport demand
In the Steady scenario, we assume that future transport demand follows central Ministry of Transport (MoT) projections. However, in the Shift scenario, we reduce light vehicle road transport demand per capita by 1% annually, reflecting a scenario of greater urbanisation and public transport use. When combined with population growth projections, this leads to light vehicle transport demand remaining roughly flat over the model horizon.

Unless mentioned otherwise, all other assumptions detailed in this documentation refer to current transport sector assumptions that apply no matter the scenario.


[^nrel_transport_atb]: NREL 2024 Transportation Annual Technology Baseline: <https://atb.nrel.gov/transportation/2024/index>
