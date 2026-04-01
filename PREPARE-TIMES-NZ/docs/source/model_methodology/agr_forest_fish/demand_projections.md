
# Demand projections

Demand projections for the agriculture, forestry, and fishing sector are based on detailed projections from the Second Emissions Reduction Plan (ERP2) detailed results[^erp_results]. 

TIMES demand projections are all based on activity indexes from the base year (currently 2023). For workbook-based mappings, the ERP2 series is converted to a demand index by dividing each year by the 2023 value. The TIMES-NZ Traditional scenario uses the ERP2 `Baseline` scenario and the Transformation scenario uses the ERP2 `Baseline low` scenario. Where the ERP2 workbook only provides values for selected years, annual values between those years are linearly interpolated.

Agricultural subsector demand profiles are as follows: 

- `Dairy Cattle Farming` tracks ERP2 `Total dairy cattle`.
- `Livestock Farming` tracks ERP2 `Sheep and beef 'stock units'`.
- `Horticulture (Outdoor)` tracks ERP2 `Horticulture`.
- `Indoor Cropping` uses the same ERP2 `Horticulture` series as a proxy.
- `Forestry and Logging` tracks ERP2 `Forestry (million m3) / Harvested timber (TRV)`.
- `Other Agriculture` tracks ERP2 `Other agriculture / Total`.
- `Fishing, Hunting and Trapping` remains constant at an index of 1.0 in both scenarios, reflecting the assumption that activity is broadly constrained by the Quota Management System (QMS)[^qms].


[^erp_results]: MPI | New Zealand's second emissions reduction plan 2026-30: [Technical Annex](https://environment.govt.nz/publications/second-emissions-reduction-plan-technical-annex/) and [Detailed Results (.xlsx)](https://view.officeapps.live.com/op/view.aspx?src=https%3A%2F%2Fenvironment.govt.nz%2Fassets%2Fpublications%2Fclimate-change%2FERP2%2FDetailed-results-for-ERP2-projection-scenarios.xlsx&wdOrigin=BROWSELINK)
[^qms]: MPI | [Quota Management System](https://www.mpi.govt.nz/legal/legislation-standards-and-reviews/fisheries-legislation/quota-management-system)


```{csv-table} ERP2 category mappings for Traditional and Transformation scenarios
:header-rows: 1
:name: tab_agr_demand_proj

Subsector,Traditional,Transformation
Dairy Cattle Farming,Baseline / Total dairy cattle,Baseline low / Total dairy cattle
Livestock Farming,"Baseline / Sheep and beef 'stock units'","Baseline low / Sheep and beef 'stock units'"
Horticulture (Outdoor),Baseline / Horticulture,Baseline low / Horticulture
Forestry and Logging,Baseline / Forestry (million m3) / Harvested timber (TRV),Baseline low / Forestry (million m3) / Harvested timber (TRV)
Indoor Cropping,Baseline / Horticulture,Baseline low / Horticulture
"Fishing, Hunting and Trapping",Constant index = 1,Constant index = 1
Other Agriculture,Baseline / Other agriculture / Total,Baseline low / Other agriculture / Total
```
