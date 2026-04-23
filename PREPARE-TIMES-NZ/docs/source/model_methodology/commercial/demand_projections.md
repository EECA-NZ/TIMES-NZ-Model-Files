# Demand projections 

Commercial demand growth assumptions for the model are driven by different growth indexes per subsector. We assume increased energy service demand for data centres in the Shift scenario, as described in {numref}`tab_com_growth_projections`. Population and GDP growth projection indices use central estimates unless specified otherwise.


```{csv-table} Growth rates in commercial subsectors
:header-rows: 1
:name: tab_com_growth_projections

Subsector,Steady,Shift
Data centres,"Data centre demand growth follows the NZTech 2025 Baseline scenario. Growth is based on planned deployed capacity, with the assumption that as new builds come online and customers are onboarded, the proportion of non-vacant space remains steady across the forecast period. The average power usage effectiveness (PUE) is assumed to remain constant, though power-drawn load gradually rises as utilisation increases.","Demand is driven by a combination of accelerated digital uptake (boosted by AI) and ongoing efficiency improvements. Deployed capacity reflects higher uptake as the new baseline, with committed capacity filling more quickly and power-drawn load increasing at a faster pace compared to the steady scenario."
Education,Population growth index,Same as Steady
Healthcare,Population growth index,Same as Steady
"Warehouses, Supermarkets, Retail",GDP growth index,Same as Steady
Office/Professional Services,GDP growth index,Same as Steady
Other,GDP growth index,Same as Steady
```


Population growth assumptions remain the same in each scenario, following central projections, therefore the energy service demand from population driven subsectors (Education and Healthcare) remain the same in both scenarios. Similarly, our current assumption is that energy service demand in the warehouses, supermarkets and retail (WSR), professional services/offices, and ‘other’ sub-sectors grows with GDP, which is assumed to be the same in both scenarios.

{numref}`tab_com_datacentre_projection_comparisons` compares electricity demand forecasts from different modelling approaches for New Zealand’s data centre sector across three key years. It includes projections from the NZTech bottom-up build pipeline, and the MBIE EDGS under both Reference and High Growth scenarios[^edgs_datacentres].

```{csv-table} Data centre energy demand forecast
:header-rows: 1
:name: tab_com_datacentre_projection_comparisons

Year ,NZTech Baseline[^nztech_baseline],NZTech Faster Uptake[^nztech_faster_uptake],EDGS Reference[^edgs_ref_env],EDGS High growth[^edgs_innovation],Comment
2025 ,0.238 TWh,0.238 TWh,,,Early-stage demand; based on build announcements and current capacity ramp-up. 
2030 ,0.913 TWh,1.207 TWh,1.8 TWh,≈ 4.6 TWh,"Wide band (0.9–4.6 TWh) captures commercial uncertainty and differing assumptions on build pace, utilisation, power draw, accelerated digital uptake (boosted by AI), and ongoing efficiency improvements."
2035,2.120 TWh,2.886 TWh,,,
2050,,,2.5–3 TWh,5–7 TWh,"Only EDGS extends this far, long-term growth highly speculative. TEM[^tem] could be adapted for sensitivity testing of efficiency or policy interventions."
```

[^tem]: IEA | [Total Energy Model 4.0 - Data Centres](https://www.iea-4e.org/wp-content/uploads/2025/05/TEM-4-Report-Draft-v0-15-FINAL.pdf)

[^nztech_baseline]: Based on the baseline (planned) deployed capacity, if as builds occur and customers are onboarded, on average, non-vacant space remains the same across the forecast period. The average PUE remains the same across the forecast period. However, assumptions on increasing power drawn load as more customers come onboard are applied. [Committed Capacity: Building from 80% current, reaching 85% in 2030 and 90% in 2035. Power Drawn Load: Building from 25% current, reaching 30% in 2030 and 50% in 2035.]
[^nztech_faster_uptake]: Uses the AI boosted digital uptake scenarios impact on deployed capacity as the new baseline, assumes committed capacity is filled faster and power drawn load increases faster, while assuming PUE remains consistent. [Committed Capacity: Building from 80% current, reaching 85% in 2030 and 90% in 2035. Power Drawn Load: Building from 25% current, reaching 35% in 2030 and 60% in 2035]
[^edgs_datacentres]: MBIE | [EDGS](https://www.mbie.govt.nz/building-and-energy/energy-and-natural-resources/energy-statistics-and-modelling/energy-modelling/electricity-demand-and-generation-scenarios):  Economy-wide scenario model (SADEM + GEM). Datacentres treated as a dedicated baseload at 90 % load-factor; five macro-scenarios vary build pace and macro drivers.
[^edgs_ref_env]: Reference / Environmental: 233 MW by 2029
[^edgs_innovation]: Innovation: 583 MW by 2035; Annual demand in 2030 spans 1.8 TWh (Ref.) to ≈4.6 TWh (upper bound) – the latter comparable to today’s Tiwai aluminium smelter. Beyond 2030 the curves diverge further, reaching ~5–7 TWh in high-growth cases by 2050. High server utilisation, this is the actual power going to servers (not including cooling or power losses) 


