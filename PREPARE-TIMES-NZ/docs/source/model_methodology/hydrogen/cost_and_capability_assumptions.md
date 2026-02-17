# Cost and capability assumptions


The model can select either Proton Exchange Membrane (PEM) or Alkaline electrolysers, each with their own costs and efficiencies. These values have been sourced from Aurecon, with the work they undertook with the Australian Energy Market Operator (AEMO) the Commonwealth Scientific and Industrial Research Organisation (CSIRO) for their GenCost model[^energy_technology_parameter].

Electrolyser cost figures can vary significantly by source, the CSIRO/Aurecon figures were chosen due to their recency and Australia being seen as a similar business environment to New Zealand. We are aware of claims of Alkaline electrolysers from China at very low costs, however we note that both Aurecon and the International Energy Agency (IEA)[^global_hydrogen] have found that once installed in Western countries these costs increase significantly. Should this change in future, the values can be updated.

Projections for future costs are from the GenCost[^gencost_2024-25] model, using their ‘Current Policies’ scenario for our Traditional Scenario, and their ‘Post 2050 net zero’ for our Transformational scenario.

Electricity costs are excluded from the table below, as they are determined by the model in its solution. Fixed O&M costs include refreshing the electrolyser every 10 years and are from the CSIRO/Aurecon work.

Efficiencies are based on Higher Heating Value. Compression and storage costs apply to sectors that require compressed hydrogen for vehicles (Transport/Agriculture) and are sourced from GHD’s work for CSIRO[^hydrogen_vehicle_refuelling]  on hydrogen refuelling stations, using their 1,000kg/day onsite production station.    


```{csv-table} Traditional scenario electrolyser costs
:header-rows: 1
:name: tab_trad_electrolyser_costs

Variable,Unit,PEM,Alkaline,Source
CAPEX (2023),$/kW," 3,004 "," 2,862 ",Aurecon
CAPEX (2035),$/kW," 2,225 "," 2,120 ",CSIRO
CAPEX (2050),$/kW," 1,732 "," 1,824 ",CSIRO
```


```{csv-table} Transformation scenario electrolyser costs
:header-rows: 1
:name: tab_transformation_electrolyser_costs

Variable,Unit,PEM,Alkaline,Source
CAPEX (2023),$/kW," 3,004 "," 2,862 ",Aurecon
CAPEX (2035),$/kW," 1,396 "," 1,331 ",CSIRO
CAPEX (2050),$/kW," 1,183 "," 1,127 ",CSIRO
```


```{csv-table} Other parameters (common to both scenarios)
:header-rows: 1
:name: tab_other_parameters

Variable,Unit,PEM,Alkaline,Source
Efficiency,%,66,72,Aurecon
Fixed O&M,$/kW annual,52.6,49.2,Aurecon
Compression + Storage,$/GJ,7.2,7.2,GHD
Lifespan,years,25,25,Aurecon
Availability Factor,%,80,80,Assumed
```


```{eval-rst}
.. note::
   All financial costs in all spreadsheets are in New Zealand dollars and exclude GST.
```


[^energy_technology_parameter]:  Aurecon | [2024 Energy Technology Cost and Technical Parameter Review] (https://www.aemo.com.au/-/media/files/major-publications/isp/2025/aurecon-2024-energy-technology-costs-and-technical-parameter-review.pdf?la=en)

[^global_hydrogen]: IEA | [Global Hydrogen Review 2025] (https://iea.blob.core.windows.net/assets/a6c466dd-b6f0-44bd-a60a-6940eccfb1c3/GlobalHydrogenReview2025.pdf)

[^gencost_2024-25]:  CSIRO | [GenCost 2024-25 - Consultation draft, pg. 67] (https://www.csiro.au/-/media/Energy/GenCost/GenCost2024-25ConsultDraft_20241205.pdf)

[^hydrogen_vehicle_refuelling]: GHD Advisory| [Hydrogen vehicle refuelling infrastructure - Priorities and opportunities for Australia] (https://www.csiro.au/-/media/Missions/Hydrogen/Hydrogen_Vehicle_Refuelling_Infrastructure_Report.pdf)