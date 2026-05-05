# Base year demand 


The base year agriculture, forestry and fishing data is intended to reflect the distribution of 2023 energy end use across all sectors in New Zealand. These agriculture, forestry and fishing (AFF) technologies should be available to the model to meet future demand, but with enough information (efficiency, lifetime, availability factors, capital costs, etc.) that the model will retire technologies at appropriate points and can make least-cost decisions on fuel switching and utilisation across demand segments.
TIMES-NZ requires detailed information on the existing agriculture, forestry and fishing technologies, including: 
 - Energy efficiency
 - Lifetime
 - Investment cost ($/kW)
 - Operation and Maintenance (O&M cost) ($/kW)
 - Availability factor 
 - Installed capacity (GW)
 - Island splits


## Historic demand 


The historic demand for agriculture, forestry and fishing sector was derived from EECA’s Energy End Use Database (EEUD). As there are some key differences in technologies and sub sector structure between TIMES-NZ 3.0 and the EEUD, the end-use energy in TIMES-NZ must be reconciled with the MBIE Energy Balance Tables. The key adjustments we made are to disaggregate: 
1) the EEUD Non-Dairy Agriculture demand between TIMES-NZ sub sectors: Livestock Farming and Outdoor Horticulture & Arable Farming, and
2) the irrigation energy demand between Dairy Farming, Livestock Farming and Outdoor Horticulture & Arable Farming. 

This approach is discussed below.

### Livestock and horticulture

Farm level data for livestock and horticulture are normalised to activity units that vary across subsectors:
 - Other livestock farming: stock units, with weightings for different animal types[^ag_production_statistics]. 
 - Horticulture and arable farming: hectares[^ag_production_statistics]. Horticulture: Energy use estimates are largely based on apple orchards, with specific adjustments for grapes and kiwifruit.

Expenditure data were available from both recent sources (post-2018) and older surveys (2012/13) depending on subsector coverage. Expenditure data are converted to litres or kWh using MBIE’s published energy prices at the time of data collection. Sector specific electricity tariffs are applied for the AFF sector, while retail diesel prices are used to reflect rural delivery costs. 

The resulting bottom-up estimates are reconciled with EEUD Non-Dairy Agriculture data. This ensures consistency at the aggregate level while allowing for greater resolution in the distribution of energy use across farm activities.

[^ag_production_statistics]: Stats NZ | [Agricultural production statistics (.xlsx)](https://view.officeapps.live.com/op/view.aspx?src=https%3A%2F%2Fwww.stats.govt.nz%2Fassets%2FUploads%2FAgricultural-production-statistics%2FAgricultural-production-statistics-Year-to-June-2024-final%2FDownload-data%2Fagricultural-production-statistics-year-to-june-2024-final.xlsx)


### Irrigation 

Irrigation was included in the EEUD for dairy farming but not for other livestock farming and outdoor horticulture and arable farming. Irrigation application areas were obtained from Irrigation NZ[^inz_data] where the relative irrigation land use proportions for livestock farming, and outdoor horticulture and arable farming were multiplied by the energy use for pumping and motive power stationary in EEUD Non-Dairy Agriculture after reconciliation with MBIE electricity data. This assumes that the irrigation intensity (energy use per hectare) is constant throughout all sub-sectors. We would expect this to be suitable for pastoral livestock production because the irrigation requirement is similar for dairy pastures and, for arable and vegetable production as most irrigation systems such as for cereal growing have similar requirements to pasture. 




{numref}`tab_agr_eeud_mapping` presents TIMES-NZ agriculture, forestry and fishing sectors with EEUD and other sector mapping, and {numref}`tab_agr_demand_shares` shows the relative shares of each defined subsector's energy demand.

```{csv-table} TIMES-NZ sector mapping
:header-rows: 1
:name: tab_agr_eeud_mapping

Sector,Inclusions,Data sources,
Dairy Cattle Farming,"Includes all dairy cattle and associated pasture required for feed. Also includes the energy for irrigation.",EEUD[^eeud]
Livestock Farming,"Includes all other farmed animals (e.g. sheep, beef, pig farming, other livestock) and associated pasture/crops grown for feed. Also includes the energy for irrigation.","EEUD, MBIE[^mbie_energy_balance],Stats NZ[^ag_production_statistics], Beef and lamb[^beef_and_lamb], MPI[^mpi_deer], Irrigation NZ[^inz_data]"
Horticulture (Outdoor),"Includes all outdoor grown fruit (kiwifruit, wine grapes), vegetables and arable crops (excluding ones grown on livestock farms). Horticulture (fruit and vegetables) (broad category, fits here unless under covered cropping). Also, includes the energy for irrigation.","EEUD, MBIE,Stats NZ, MPI[^mpi_hort], Irrigation NZ[^inz_data]"
Indoor Cropping,"All fruit, vegetables, flowers that are grown in both heated and unheated greenhouses (e.g., covered cropping, plant nursery / floriculture)",EEUD
Forestry and Logging,"All forest operations from planting, silviculture to harvesting trees, extracting logs and chipping wood residues",EEUD
"Fishing, Hunting and Trapping",Includes all commercial fishing and aquaculture,EEUD
Other Agriculture,EEUD and MBIE reconciliation,"EEUD, MBIE"
```

[^mpi_deer]: MPI | [South Island deer model (.xlsx)](https://view.officeapps.live.com/op/view.aspx?src=https%3A%2F%2Fwww.mpi.govt.nz%2Fdmsdocument%2F1618-Key-parameters-financial-results-and-budget-for-the-South-Island-deer-model)
[^eeud]: EECA | [EEUD](https://www.eeca.govt.nz/insights/data-tools/energy-end-use-database/)
[^mbie_energy_balance]: MBIE | [Energy balance tables (.xlsx)](https://view.officeapps.live.com/op/view.aspx?src=https%3A%2F%2Fwww.mbie.govt.nz%2Fassets%2FData-Files%2FEnergy%2Fnz-energy-quarterly-and-energy-in-nz%2Fenergy-balance-tables.xlsx)

[^inz_data]: Irrigation NZ | [Electricity price review submission](https://www.mbie.govt.nz/dmsdocument/4869-irrigation-new-zealand-submission-electricity-price-review-options-paper-pdf#:~:text=On%20a%20national%20basis%20it,network%20infrastructure%20and%20seasonal%20load), [2015 Industry snapshot](https://www.irrigationnz.co.nz/Attachment?Action=Download&Attachment_id=191)

[^beef_and_lamb]: Beef and Lamb NZ | [Sheep and Beef Farm Survey (.xlsx)](https://view.officeapps.live.com/op/view.aspx?src=https%3A%2F%2Fbeeflambnz.com%2Fknowledge-hub%2Fspreadsheet%2Fnz-class-9-nz-all-classes.xlsx)
[^mpi_hort]: MPI | Various datasets: [Marlborough Vineyard Monitoring Report (.xlsx)](https://view.officeapps.live.com/op/view.aspx?src=https%3A%2F%2Fwww.mpi.govt.nz%2Fdmsdocument%2F65619-2024-Marlborough-vineyard-monitoring-report-data), [Canterbury arable cropping model (.xlsx)](https://view.officeapps.live.com/op/view.aspx?src=https%3A%2F%2Fwww.mpi.govt.nz%2Fdmsdocument%2F1591-Key-parameters-financial-results-and-budget-for-the-Canterbury-arable-cropping-model), [Hawke's bay pipfruit orcharde model profitability trends (.xlsx)](https://view.officeapps.live.com/op/view.aspx?src=https%3A%2F%2Fwww.mpi.govt.nz%2Fdmsdocument%2F1589-Hawkes-Bay-pipfruit-orchard-model-profitability-trends), [Bay of Plenty kiwifruit orchard model (.xlsx)](https://view.officeapps.live.com/op/view.aspx?src=https%3A%2F%2Fwww.mpi.govt.nz%2Fdmsdocument%2F1592-Key-parameters-financial-results-and-budget-for-the-Bay-of-Plenty-kiwifruit-orchard-model)






```{csv-table} Agriculture, forestry and fishing sector historic demand 2023
:header-rows: 1
:name: tab_agr_demand_shares

Sector,Energy (PJ),Energy share (%)
Dairy Cattle Farming,10.26,35%
Livestock Farming,7,24%
Horticulture (Outdoor),3.29,11%
Indoor Cropping,3.4,12%
Forestry and Logging,2.02,7%
"Fishing, Hunting and Trapping",1.99,7%
Other Agriculture,1.14,4%
Total,29.11,100%

```


## Current uptake of technologies 



We have identified many alternative decarbonisation technologies which have already been implemented. We use those base year shares for key technologies ({numref}`tab_agr_current_eeo_uptake`) and off-road vehicle diesel splits ({numref}`tab_agr_diesel_onfarm`). These figures are assumptions, but are based on the EEUD, in-house expertise, and published estimates (Massey University[^power_systems_dairy_sheds]; University of Canterbury for forestry[^timber_harvesting_fuel]). 

[^power_systems_dairy_sheds]: Marshall-Tate, 2017, [Power Systems for Dairy Sheds](https://mro.massey.ac.nz/bitstream/handle/10179/13433/02_whole.pdf?sequence=3&isAllowed=y)

[^timber_harvesting_fuel]: Oyier, 2015, [Fuel consumption of timber harvesting systems in New Zealand](https://ir.canterbury.ac.nz/bitstream/handle/10092/11751/Oyier,%20Paul_Masters%20Thesis.pdf;sequence=1 )




```{csv-table} Current uptake by farmers and growers of energy efficiency opportunities
:header-rows: 1
:name: tab_agr_current_eeo_uptake

Technology,Current Estimated Uptake (%)
Variable Speed Drives – Vacuum pumps in dairy sheds,58%
Variable Speed Drives – Irrigation pump motors,25%
Heat recovery systems with heat pumps – dairy sheds,38%
```

```{csv-table} Assumed proportion of diesel vehicle used on-farm by subsector
:header-rows: 1
:name: tab_agr_diesel_onfarm

Sub-sector,Technology,Diesel share of off-road vehicle use (%)
Dairy Cattle Farming,Ute,15%
Dairy Cattle Farming,Tractor,80%
Dairy Cattle Farming,Truck (<10 tonne),5%
Livestock farming,Ute,5%
Livestock farming,Tractor,90%
Livestock farming,Truck (<10 tonne),5%
Horticulture (Outdoor),Ute,5%
Horticulture (Outdoor),Tractor,90%
Horticulture (Outdoor),Truck (<10 tonne),5%
Forestry and Logging,Cable Yarding ,44%
Forestry and Logging,Ground Based,56%
```


## Island disaggregation 


The island splits for irrigation were all derived from irrigated areas according to Irrigation NZ. All other non-irrigation energy demands for Dairy Farming, Livestock Farming, Outdoor Horticulture, and Forestry Island splits were derived from land areas according to Statistics NZ. The island split for indoor cropping was from TIMES-NZ 2.0 which was identified from the PHINZ programme by MBIE and EECA. This was manipulated by fuel type using a weighted average to reflect the fact that natural gas and geothermal fuels are only available in the North Island. The island split for Fishing was from TIMES-NZ 2.0 which was derived using the amount of value of fish by fishing region from Seafood NZ.


```{csv-table} Energy demand split between North Island and South Island
:header-rows: 1
:name: tab_agr_island_shares 

Sub-Sector,Input Fuel Type,Technology,NI %
Dairy Cattle Farming,Electricity,All (excluding Irrigator),59%
Dairy Cattle Farming,Electricity,Irrigator,14%
Dairy Cattle Farming,Diesel,All,58%
Livestock Farming,Electricity,All (excluding Irrigator),44%
Livestock Farming,Electricity,Irrigator,8%
Livestock Farming,Diesel,All,44%
Horticulture (Outdoor),Electricity,All (excluding Irrigator),45%
Horticulture (Outdoor),Electricity,Irrigator,19%
Horticulture (Outdoor),Diesel,All,45%
Indoor Cropping,Coal,All,37%
Indoor Cropping,Diesel,All,37%
Indoor Cropping,Natural Gas,All,100%
Indoor Cropping,Geothermal,All,100%
Indoor Cropping,Electricity,All,64%
Forestry and Logging,All (excluding Natural Gas),All,74%
Forestry and Logging,Natural Gas,All,100%
"Fishing, Hunting and Trapping",All,All,32%
Other Agriculture,All,All,50%
```

