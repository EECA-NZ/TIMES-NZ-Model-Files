# Future technologies 

The base of future road transport technologies made available to the model is based on the MOT’s VFM, with adjustments for future capital and O&M costs derived from the National Renewable Energy Laboratory (NREL) Annual Technology Baseline (ATB) data[^nrel_transport_atb]. This includes a list of future vehicle types (ICE, BEV, PHEV, and FC), with detailed estimates of investment costs (CAPEX), fixed operating and maintenance costs (FIXOM), fuel efficiency, AFA, vehicle lifetime, and earliest availability years.
We made the following adjustments and additions to the baseline vehicle technology data:
 - We included cost projections from NREL for advanced ICEs, BEVs, PHEVs, and hydrogen FC vehicles across light, medium, and heavy vehicle classes.
 - We used NREL learning curve assumptions to model CAPEX and FIXOM costs for future transport technologies in TIMES-NZ 3.0 scenarios over time.



## Learning curves for transport technologies

Data from the NREL Annual Technology Baseline (ATB) was used to generate learning curves for key vehicle technologies, providing projections of CAPEX and FIXOM costs over time based on assumed technological advancement. The NREL projections extend from 2023 to 2050 across three scenarios, reflecting different rates of innovation and market development.
 - Conservative: Minor technology changes; low R&D investment.
 - Moderate: Widespread innovation consistent with current investment trends.
 - Advanced: Strong technology improvements driven by increased R&D investment.

For TIMES-NZ, the Conservative scenario was used for Steady, and the Moderate scenario was used for the Shift. The Advanced scenario is not currently used, reflecting the fact that New Zealand’s market maturity and supply chains are behind those of the US.

Learning curves were applied to adjust CAPEX and FIXOM costs for vehicles meeting the following criteria:
 - Vehicles representing future technologies that are not yet mature in the 2023 fleet (e.g., heavy-duty hydrogen trucks, long-range BEVs)
 - Technologies with market entry years of 2025 or later
 - Future BEV, PHEV, and FCEV technologies have cost reductions applied
 - Dual fuel diesel-hydrogen vehicles aren’t modelled by NREL, so these were indexed to the diesel equivalent, and given half the cost reduction rate of FCEV vehicles to reflect the improvements of the hydrogen tanks and related equipment. 

Technologies already widely available in the base year (e.g., ICE petrol vehicles) retain static costs across the model horizon.
The NREL transport categories were mapped to TIMES-NZ vehicle types as follows:


```{list-table} Road transport NREL technology mapping
:header-rows: 1
:name: tab-transport-nrel-tech-map
* - TIMES Vehicle Category
  - Mapped NREL Category
* - LPV
  - Light Duty: Compact, midsize, small SUV, midsize SUV
* - LCV
  - Light Duty: Pickup and Class 2 and 3
* - Light Truck 
  - Medium/Heavy Duty: Class 4, 5, and 6
* - Medium Truck 
  - Medium/Heavy Duty: Class 7
* - Heavy Truck 
  - Medium/Heavy Duty: Class 8
* - Bus
  - Medium/Heavy Duty: Class 8
* - Motorcycle
  - Not explicitly in ATB – used Light Duty: Compact, midsize, small SUV, midsize SUV
```



[^nrel_transport_atb]: NREL 2024 Transportation Annual Technology Baseline: <https://atb.nrel.gov/transportation/2024/index>

### Cost application methodology 


To apply the learning curves:
 - Percentage indices for changes in CAPEX were calculated relative to the base year, using NREL projections.
 - The base year for cost application is set to 2023, aligned with the TIMES-NZ 3.0 fleet base year.
 - For projected CAPEX, the NREL-derived percentage indices were applied to the base capital cost.
 - FIXOM costs were extracted from NREL for the base year, where data is not available in the NZ context.


```{list-table} Road transport CAPEX projections - Steady scenario (NZD2025)
:header-rows: 1
:name: tab_transport_capex_learning_curves_steady
* - Type
  - Technology
  - Fuel
  - 2030
  - 2040
  - 2050
* - LPV
  - ICE
  - Petrol
  - $40,340
  - $41,111
  - $41,563
* - 
  - ICE
  - Diesel
  - $56,350
  - $57,156
  - $57,631
* - 
  - BEV
  - Electricity
  - $42,683
  - $40,776
  - $40,196
* - 
  - ICE Hybrid
  - Petrol
  - $44,041
  - $44,452
  - $44,740
* - 
  - ICE Hybrid
  - Diesel
  - $61,520
  - $61,800
  - $62,037
* - 
  - PHEV
  - Petrol/Electricity
  - $51,687
  - $50,624
  - $50,534
* - 
  - PHEV
  - Diesel/Electricity
  - $72,201
  - $70,380
  - $70,071
* - 
  - FC
  - Hydrogen
  - $59,091
  - $53,116
  - $50,669
* - LCV
  - ICE
  - Petrol
  - $64,771
  - $65,865
  - $66,230
* - 
  - ICE
  - Diesel
  - $58,353
  - $58,300
  - $58,297
* - 
  - BEV
  - Electricity
  - $62,755
  - $59,163
  - $57,664
* - 
  - ICE Hybrid
  - Petrol
  - $60,985
  - $61,432
  - $61,549
* - 
  - ICE Hybrid
  - Diesel
  - $56,993
  - $57,411
  - $57,520
* - 
  - PHEV
  - Petrol/Electricity
  - $52,936
  - $51,908
  - $51,714
* - 
  - PHEV
  - Diesel/Electricity
  - $73,945
  - $72,166
  - $71,707
* - 
  - FC
  - Hydrogen
  - $114,482
  - $101,005
  - $93,086
* - Light Truck
  - ICE
  - Diesel
  - $80,012
  - $79,926
  - $79,892
* - 
  - BEV
  - Electricity
  - $108,550
  - $99,961
  - $96,169
* - 
  - FC
  - Hydrogen
  - $163,024
  - $147,204
  - $137,791
* - Medium truck
  - ICE
  - Diesel
  - $179,504
  - $179,381
  - $179,314
* - 
  - BEV
  - Electricity
  - $336,246
  - $287,780
  - $274,602
* - 
  - FC
  - Hydrogen
  - $370,890
  - $340,657
  - $322,709
* - Heavy truck
  - ICE
  - Diesel
  - $352,333
  - $352,670
  - $352,601
* - 
  - BEV
  - Electricity
  - $538,525
  - $471,324
  - $443,012
* - 
  - FC
  - Hydrogen
  - $673,288
  - $599,693
  - $555,747
* - 
  - DSLH2
  - Diesel/Hydrogen
  - $442,246
  - $422,078
  - $409,649
* - Bus
  - ICE
  - Diesel
  - $400,451
  - $400,452
  - $400,452
* - 
  - ICE
  - Electricity
  - $497,743
  - $458,333
  - $441,813
* - 
  - BEV
  - Hydrogen
  - $801,556
  - $766,886
  - $745,571
* - Motorcycle
  - ICE
  - Petrol
  - $5,209
  - $5,333
  - $5,437
* - 
  - BEV
  - Electricity
  - $7,039
  - $6,700
  - $6,608
```


```{list-table} Road transport CAPEX projections - Shift scenario (NZD2025)
:header-rows: 1
:name: tab_transport_capex_learning_curves_shift
* - Type
  - Technology
  - Fuel
  - 2030
  - 2040
  - 2050
* - LPV
  - ICE
  - Petrol
  - $39,406
  - $41,350
  - $41,043
* - 
  - ICE
  - Diesel
  - $54,734
  - $54,730
  - $54,581
* - 
  - BEV
  - Electricity
  - $41,604
  - $37,137
  - $34,476
* - 
  - ICE Hybrid
  - Petrol
  - $43,034
  - $44,354
  - $43,804
* - 
  - ICE Hybrid
  - Diesel
  - $59,773
  - $58,707
  - $58,252
* - 
  - PHEV
  - Petrol/Electricity
  - $47,985
  - $45,106
  - $43,275
* - 
  - PHEV
  - Diesel/Electricity
  - $66,651
  - $59,702
  - $57,548
* - 
  - FC
  - Hydrogen
  - $57,827
  - $53,056
  - $50,669
* - LCV
  - ICE
  - Petrol
  - $62,671
  - $65,395
  - $65,221
* - 
  - ICE
  - Diesel
  - $58,088
  - $57,555
  - $57,518
* - 
  - BEV
  - Electricity
  - $53,167
  - $44,721
  - $39,484
* - 
  - ICE Hybrid
  - Petrol
  - $58,704
  - $60,130
  - $59,552
* - 
  - ICE Hybrid
  - Diesel
  - $54,363
  - $53,849
  - $53,741
* - 
  - PHEV
  - Petrol/Electricity
  - $43,227
  - $39,622
  - $36,073
* - 
  - PHEV
  - Diesel/Electricity
  - $60,041
  - $52,444
  - $47,972
* - 
  - FC
  - Hydrogen
  - $95,932
  - $83,724
  - $78,801
* - Light Truck
  - ICE
  - Diesel
  - $79,445
  - $78,679
  - $78,521
* - 
  - BEV
  - Electricity
  - $89,954
  - $74,588
  - $65,349
* - 
  - FC
  - Hydrogen
  - $141,558
  - $126,959
  - $120,924
* - Medium truck
  - ICE
  - Diesel
  - $177,870
  - $176,883
  - $176,874
* - 
  - BEV
  - Electricity
  - $266,945
  - $218,980
  - $190,213
* - 
  - FC
  - Hydrogen
  - $329,044
  - $301,247
  - $290,025
* - Heavy truck
  - ICE
  - Diesel
  - $350,806
  - $350,202
  - $350,988
* - 
  - BEV
  - Electricity
  - $451,838
  - $360,545
  - $304,772
* - 
  - FC
  - Hydrogen
  - $616,491
  - $555,807
  - $530,458
* - 
  - DSLH2
  - Diesel/Hydrogen
  - $424,128
  - $406,236
  - $400,250
* - Bus
  - ICE
  - Diesel
  - $401,415
  - $401,415
  - $401,909
* - 
  - ICE
  - Electricity
  - $454,287
  - $406,707
  - $370,439
* - 
  - BEV
  - Hydrogen
  - $754,170
  - $721,967
  - $708,217
* - Motorcycle
  - ICE
  - Petrol
  - $5,106
  - $5,335
  - $5,316
* - 
  - BEV
  - Electricity
  - $6,916
  - $6,092
  - $5,609
```

## Vehicle deployment limits 

TIMES-NZ 2.0 used a supply constraint to model the likelihood that New Zealand wouldn’t be able to access global production of BEVs, due to our small market size. Given that BEVs are now readily available in New Zealand without supply constraint, we have removed this from the model.


## Chargers 

For battery electric and plug-in hybrids, each vehicle has a charger cost added to their CAPEX (other than LPVs and motorcycles which are assumed to home charge), with prices from IDTechEX. Most vehicles are assumed to charge overnight and are assigned an appropriately sized charger for this. 
The exception is for heavy trucks which we have assumed charge at the depot, sharing a 500kW charger between 5 trucks. This is to ensure that electric vehicles in this category are capable of completing high utilisation duty cycles, while also trying to reflect that chargers will be shared amongst vehicles to ensure their own utilisation. 

In future iterations of the model, we would like to have a charging network made up of multiple nodes, however this is out of scope for this release.
These are applied as below:


```{list-table} Charger costs (NZD)
:header-rows: 1
:name: tab-transport-charger-costs
* - Type
  - Charger (kW)
  - CAPEX
* - LCV
  - 7
  - 3,500
* - Light Truck
  - 22
  - 8,000
* - Medium Truck
  - 50
  - 73,000
* - Heavy Truck
  - 500
  - 110,000[^heavy_freight_chargers]
* - Bus
  - 50
  - 73,000
```


The model is free to optimise charging times to reduce peak loads. Initially set charging times were implemented to represent uncontrolled charging, however feedback from industry indicated that many consumers were already managing charging due to incentives such as Time of Use electricity plans. Businesses are assumed to manage their loads to reduce their own energy costs.

Cost of hydrogen infrastructure is considered by the model in determining the delivered cost of fuel, so is not included in any vehicle CAPEX figures.
[^heavy_freight_chargers]: This is a cost per vehicle. Total charger cost $617,400

## Aviation 

The aviation sector has the ability to use SAF or move to Hydrogen aircraft. Figures are sourced from IDTechEx, using their narrowbody assumptions. The earliest that the H2 option can be selected is 2035. It was not considered realistic for battery densities to improve to the level required for commercial flight within the model horizon, so BEV planes have not been modelled.

```{list-table} Aviation CAPEX and efficiency
:header-rows: 1
:name: tab-aviation-capex-efficiency
* - Technology
  - CAPEX
  - Efficiency
  - Lifespan (years)
* - ICE
  - $42m
  - 40%
  - 20
* - Hydrogen Fuel Cell (H2 700 bar)
  - $54.6m
  - 57%
  - 20
```


Note that this only applies to domestic aviation. International aviation exists in the model for its impact on fuel demand but does not contribute to emissions. Hydrogen was not deemed feasible for international travel, so it has not been provided as an option in this area.

Estimates in this area are still very uncertain. The model will be updated when and if more accurate information on alternative aviation fuels becomes available. 


