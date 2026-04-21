# EEUD 2023 Comparison Report

## Scope

This report compares the 2023 rows in the `Data` sheet of the old EEUD workbook against the 2023 rows in the new 2024 EEUD workbook. It uses raw workbook content with light standardization of headers, dates, and the energy-value field so the comparison is like-for-like. It does **not** apply project-specific downstream patches or recoding rules.

## Headline Summary

| Metric | Value |
| --- | --- |
| Old workbook | Final EEUD Outputs 2017 - 2023 12032025.xlsx |
| New workbook | EEUD 2017 - 2024 FINAL 20032026.xlsx |
| 2023 rows in old workbook | 464 |
| 2023 rows in new workbook | 449 |
| 2023 category rows in old workbook | 464 |
| 2023 category rows in new workbook | 449 |
| 2023 total in old workbook (TJ) | 542,743.622227 |
| 2023 total in new workbook (TJ) | 532,188.999578 |
| Net delta (new - old, TJ) | -10,554.622649 |
| Exact added category rows | 15 |
| Exact removed category rows | 28 |
| Exact changed category rows | 280 |

Key takeaways:

- The 2023 total falls by -10,554.622649 TJ in the new workbook.
- There are 28 exact removals and 15 exact additions at the full category grain.
- There are 280 exact category rows where the category still exists but the 2023 value changed.
- The largest sector-level drop is `Air Transport`, down -5,064.172853 TJ.
- The most obvious new sector is `Data Centers` in commercial demand (+492 TJ).

## Air Transport Check

This was checked directly against the raw workbooks because the drop is large. The result appears to be a true source-data difference, not a comparison artifact:

| Check | Result |
| --- | --- |
| Old workbook raw row count for `Sector = Air Transport` in 2023 | 1 |
| New workbook raw row count for `Sector = Air Transport` in 2023 | 1 |
| Old workbook raw total for Air Transport (TJ) | 18,546.101337 |
| New workbook raw total for Air Transport (TJ) | 13,481.928484 |
| Raw delta for Air Transport (TJ) | -5,064.172853 |
| Old workbook raw row count for `Fuel = Av. Fuel/Kero` in 2023 | 1 |
| New workbook raw row count for `Fuel = Av. Fuel/Kero` in 2023 | 1 |
| Old workbook raw total for Av. Fuel/Kero (TJ) | 18,546.101337 |
| New workbook raw total for Av. Fuel/Kero (TJ) | 13,481.928484 |
| Raw delta for Av. Fuel/Kero (TJ) | -5,064.172853 |

Raw 2023 air-transport rows from each workbook:

| Workbook | SectorGroup | Sector | SectorANZSIC | FuelGroup | Fuel | TechnologyGroup | Technology | EnduseGroup | EndUse | Transport | Value |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Old | Transport | Air Transport | Z002 | Fossil Fuels | Av. Fuel/Kero | Plane | Turbine Engine | Mobile Motive Power | Motive Power, Mobile | Air Transport | 18,546.101337 |
| New | Transport | Air Transport | Z002 | Fossil Fuels | Av. Fuel/Kero | Plane | Turbine Engine | Mobile Motive Power | Motive Power, Mobile | Air Transport | 13,481.928484 |

Interpretation:

- There is exactly one 2023 `Air Transport` row in each workbook.
- There is exactly one 2023 `Av. Fuel/Kero` row in each workbook.
- They have the same category keys: `Transport / Air Transport / Z002 / Fossil Fuels / Av. Fuel/Kero / Plane / Turbine Engine / Mobile Motive Power / Motive Power, Mobile / Air Transport`.
- The difference is the raw value itself: `18,546.101337 TJ` in the old workbook versus `13,481.928484 TJ` in the new workbook.

## Workbook Structure Changes

| Change | Observation |
| --- | --- |
| Workbook sheets | Old has `Notes`, `Data`, `Fuel Lookup`; new has `Read Me`, `Data` |
| Date column header | `periodEndDate` -> `PeriodEndDate` |
| Value column header | `energyValue` -> `EnergyValue (Terrajoules)` |
| Category header casing | Old workbook mixes lower/camel case; new workbook uses more consistent Pascal/capitalized names |

## New Or Removed Labels By Column

### Sector

Removed labels:

| Only in old workbook |
| --- |
| Electricity, Gas, Water and Waste Services |
| Furniture and Other Manufacturing |

New labels:

| Only in new workbook |
| --- |
| Data Centers |

### SectorANZSIC

Removed labels:

| Only in old workbook |
| --- |
| C25 |
| D |

New labels:

| Only in new workbook |
| --- |
| J592 |

### TechnologyGroup

Removed labels:

| Only in old workbook |
| --- |
| Very Heavy Truck |

New labels:

| Only in new workbook |
| --- |
| Light Truck |

### Technology

Removed labels: _None._

New labels:

| Only in new workbook |
| --- |
| Direct Heat |

## Likely Relabels Or Recodes

These are old/new rows with exactly the same 2023 TJ value but different category fields, so they look more like recoding than substantive demand changes.

| Value_TJ | DifferingFields | DiffFieldCount | Old_SectorGroup | Old_Sector | Old_SectorANZSIC | Old_Fuel | Old_TechnologyGroup | Old_Technology | Old_EnduseGroup | Old_EndUse | New_SectorGroup | New_Sector | New_SectorANZSIC | New_Fuel | New_TechnologyGroup | New_Technology | New_EnduseGroup | New_EndUse |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 364 | Sector | 1 | Residential | nan | Z001 | Solar | nan | nan | nan | nan | Residential | Residential | Z001 | Solar | nan | nan | nan | nan |
| 254.514083 | Sector | 1 | Commercial | Transport, Postal and Warehousing (Commercial - Non-Transport) | I52,I53 | Natural Gas | nan | nan | nan | nan | Commercial | nan | I52,I53 | Natural Gas | nan | nan | nan | nan |
| 209 | Sector, TechnologyGroup, Technology, EnduseGroup, EndUse | 5 | Residential | nan | Z001 | Geothermal | nan | nan | nan | nan | Residential | Residential | Z001 | Geothermal | Heat/Cooling Devices | Direct Heat | Heating/Cooling | Low Temperature Heat (<100 C), Space Heating |

Full table: `EEUD_2023_likely_relabels.csv`

## Highest-Risk Exact Removals

| SectorGroup | Sector | SectorANZSIC | FuelGroup | Fuel | TechnologyGroup | Technology | EnduseGroup | EndUse | Transport | Old_TJ |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Transport | Road Transport | Z002 | Fossil Fuels | Diesel | Very Heavy Truck | Internal Combustion Engine | Mobile Motive Power | Motive Power, Mobile | Heavy Vehicles | 34,365.716677 |
| Industrial | Electricity, Gas, Water and Waste Services | D | Electricity | Electricity | Stationary Motors | Pump Systems (for Fluids, etc.) | Stationary Motive Power | Pumping | Non-Transport | 2,085.82496 |
| Industrial | Furniture and Other Manufacturing | C25 | Electricity | Electricity | Stationary Motors | Electric Motor | Stationary Motive Power | Motive Power, Stationary | Non-Transport | 712.117026 |
| Industrial | Dairy Product Manufacturing | C113 | Fossil Fuels | LPG | Heat/Cooling Devices | Boiler Systems | Heating/Cooling | Intermediate Heat (100-300 C), Process Requirements | Non-Transport | 398.084 |
| Industrial | Food and Beverage Product Manufacturing (excluding Dairy, Meat, Seafood) | C114-C119, C12 | Fossil Fuels | Diesel | Heat/Cooling Devices | Boiler Systems | Heating/Cooling | Intermediate Heat (100-300 C), Process Requirements | Non-Transport | 387.997933 |
| Residential | nan | Z001 | Renewables | Solar | nan | nan | nan | nan | Non-Transport | 364 |
| Industrial | Primary Metal and Metal Product Manufacturing | C21 | Fossil Fuels | Fuel Oil | Heat/Cooling Devices | Furnace/Kiln | Heating/Cooling | High Temperature Heat (>300 C), Process Requirements | Non-Transport | 344.646364 |
| Industrial | Food and Beverage Product Manufacturing (excluding Dairy, Meat, Seafood) | C114-C119, C12 | Fossil Fuels | LPG | Heat/Cooling Devices | Boiler Systems | Heating/Cooling | Intermediate Heat (100-300 C), Process Requirements | Non-Transport | 318.062183 |
| Commercial | Transport, Postal and Warehousing (Commercial - Non-Transport) | I52,I53 | Fossil Fuels | Natural Gas | nan | nan | nan | nan | Non-Transport | 254.514083 |
| Residential | nan | Z001 | Renewables | Geothermal | nan | nan | nan | nan | Non-Transport | 209 |
| Industrial | Petroleum, Basic Chemical and Rubber Product Manufacturing | C17-C19 | Fossil Fuels | Fuel Oil | Heat/Cooling Devices | Boiler Systems | Heating/Cooling | High Temperature Heat (>300 C), Process Requirements | Non-Transport | 206.882336 |
| Industrial | Dairy Product Manufacturing | C113 | Fossil Fuels | Diesel | Heat/Cooling Devices | Boiler Systems | Heating/Cooling | Intermediate Heat (100-300 C), Process Requirements | Non-Transport | 118.089 |
| Industrial | Petroleum, Basic Chemical and Rubber Product Manufacturing | C17-C19 | Fossil Fuels | Fuel Oil | Heat/Cooling Devices | Furnace/Kiln | Heating/Cooling | High Temperature Heat (>300 C), Process Requirements | Non-Transport | 117.622422 |
| Industrial | Pulp, Paper and Converted Paper Product Manufacturing | C15 | Fossil Fuels | Fuel Oil | Heat/Cooling Devices | Boiler Systems | Heating/Cooling | Intermediate Heat (100-300 C), Process Requirements | Non-Transport | 105.062129 |
| Industrial | Furniture and Other Manufacturing | C25 | Electricity | Electricity | Electronics and Lights | Lights | Electronics and Lighting | Lighting | Non-Transport | 69.947439 |
| Industrial | Wood Product Manufacturing | C14 | Fossil Fuels | Diesel | Heat/Cooling Devices | Boiler Systems | Heating/Cooling | Intermediate Heat (100-300 C), Process Requirements | Non-Transport | 48.380118 |
| Industrial | Furniture and Other Manufacturing | C25 | Electricity | Electricity | Heat/Cooling Devices | Furnace/Kiln | Heating/Cooling | High Temperature Heat (>300 C), Process Requirements | Non-Transport | 45.551603 |
| Transport | Road Transport | Z002 | Fossil Fuels | Petrol | Medium Truck | Internal Combustion Engine | Mobile Motive Power | Motive Power, Mobile | Heavy Vehicles | 44.217153 |
| Industrial | Dairy Product Manufacturing | C113 | Renewables | Biogas | Heat/Cooling Devices | Boiler Systems | Heating/Cooling | Intermediate Heat (100-300 C), Process Requirements | Non-Transport | 43.968 |
| Industrial | Wood Product Manufacturing | C14 | Fossil Fuels | Fuel Oil | Heat/Cooling Devices | Boiler Systems | Heating/Cooling | Intermediate Heat (100-300 C), Process Requirements | Non-Transport | 31.022875 |

Full table: `EEUD_2023_exact_removed_categories.csv`

## Highest-Risk Exact Additions

| SectorGroup | Sector | SectorANZSIC | FuelGroup | Fuel | TechnologyGroup | Technology | EnduseGroup | EndUse | Transport | New_TJ |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Transport | Road Transport | Z002 | Fossil Fuels | Diesel | Light Truck | Internal Combustion Engine | Mobile Motive Power | Motive Power, Mobile | Heavy Vehicles | 6,045.621141 |
| Industrial | Industrial - Unallocated | Z003 | Electricity | Electricity | nan | nan | nan | nan | Non-Transport | 2,937.907055 |
| Industrial | Industrial - Unallocated | Z003 | Fossil Fuels | Fuel Oil | nan | nan | nan | nan | Non-Transport | 809.91067 |
| Commercial | Data Centers | J592 | Electricity | Electricity | Electronics and Lights | Electronics | Electronics and Lighting | Electronics and Other Electrical Uses | Non-Transport | 408.36 |
| Residential | Residential | Z001 | Renewables | Solar | nan | nan | nan | nan | Non-Transport | 364 |
| Commercial | nan | I52,I53 | Fossil Fuels | Natural Gas | nan | nan | nan | nan | Non-Transport | 254.514083 |
| Residential | Residential | Z001 | Renewables | Geothermal | Heat/Cooling Devices | Direct Heat | Heating/Cooling | Low Temperature Heat (<100 C), Space Heating | Non-Transport | 209 |
| Commercial | Data Centers | J592 | Electricity | Electricity | Heat/Cooling Devices | Heat Pump (for Cooling) | Heating/Cooling | Space Cooling | Non-Transport | 73.8 |
| Industrial | Industrial - Unallocated | Z003 | Fossil Fuels | Natural Gas | nan | nan | nan | nan | Non-Transport | 73.62552 |
| Transport | Road Transport | Z002 | Fossil Fuels | Petrol | Light Truck | Internal Combustion Engine | Mobile Motive Power | Motive Power, Mobile | Heavy Vehicles | 42.702014 |
| Commercial | Data Centers | J592 | Electricity | Electricity | Electronics and Lights | LED | Electronics and Lighting | Lighting | Non-Transport | 9.84 |
| Transport | Road Transport | Z002 | Electricity | Electricity | Medium Truck | Battery Electric Vehicle | Mobile Motive Power | Motive Power, Mobile | Heavy Vehicles | 2.5508 |
| Transport | Road Transport | Z002 | Electricity | Electricity | Heavy Truck | Battery Electric Vehicle | Mobile Motive Power | Motive Power, Mobile | Heavy Vehicles | 1.852084 |
| Transport | Road Transport | Z002 | Electricity | Electricity | Light Truck | Battery Electric Vehicle | Mobile Motive Power | Motive Power, Mobile | Heavy Vehicles | 0.947717 |
| Transport | Road Transport | Z002 | Electricity | Electricity | Motorcycle | Battery Electric Vehicle | Mobile Motive Power | Motive Power, Mobile | Other | 0.590882 |

Full table: `EEUD_2023_exact_added_categories.csv`

## Largest Value Changes In Matched Categories

| SectorGroup | Sector | SectorANZSIC | FuelGroup | Fuel | TechnologyGroup | Technology | EnduseGroup | EndUse | Transport | Old_TJ | New_TJ | Delta_TJ |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Transport | Road Transport | Z002 | Fossil Fuels | Diesel | Heavy Truck | Internal Combustion Engine | Mobile Motive Power | Motive Power, Mobile | Heavy Vehicles | 12,547.44391 | 34,461.087291 | 21,913.643381 |
| Transport | Road Transport | Z002 | Fossil Fuels | Diesel | Medium Truck | Internal Combustion Engine | Mobile Motive Power | Motive Power, Mobile | Heavy Vehicles | 6,050.284502 | 12,598.009427 | 6,547.724925 |
| Transport | Air Transport | Z002 | Fossil Fuels | Av. Fuel/Kero | Plane | Turbine Engine | Mobile Motive Power | Motive Power, Mobile | Air Transport | 18,546.101337 | 13,481.928484 | -5,064.172853 |
| Industrial | Wood Product Manufacturing | C14 | Renewables | Wood | Heat/Cooling Devices | Boiler Systems | Heating/Cooling | Intermediate Heat (100-300 C), Process Requirements | Non-Transport | 16,883.579568 | 12,410.545678 | -4,473.03389 |
| Industrial | Pulp, Paper and Converted Paper Product Manufacturing | C15 | Renewables | Wood | Heat/Cooling Devices | Boiler Systems | Heating/Cooling | Intermediate Heat (100-300 C), Process Requirements | Non-Transport | 6,131.151416 | 4,506.801085 | -1,624.350331 |
| Industrial | Food and Beverage Product Manufacturing (excluding Dairy, Meat, Seafood) | C114-C119, C12 | Electricity | Electricity | Stationary Motors | Electric Motor | Stationary Motive Power | Motive Power, Stationary | Non-Transport | 1,004.613845 | 1,810.080541 | 805.466696 |
| Industrial | Food and Beverage Product Manufacturing (excluding Dairy, Meat, Seafood) | C114-C119, C12 | Electricity | Electricity | Heat/Cooling Devices | Refrigeration Systems | Heating/Cooling | Refrigeration | Non-Transport | 824.40491 | 1,485.385944 | 660.981034 |
| Industrial | Dairy Product Manufacturing | C113 | Electricity | Electricity | Electronics and Lights | Fan Systems | Electronics and Lighting | Fans | Non-Transport | 1,463.248327 | 895.845492 | -567.402835 |
| Industrial | Dairy Product Manufacturing | C113 | Electricity | Electricity | Stationary Motors | Pump Systems (for Fluids, etc.) | Stationary Motive Power | Pumping | Non-Transport | 1,301.937877 | 797.086289 | -504.851588 |
| Residential | Residential | Z001 | Electricity | Electricity | Heat/Cooling Devices | Hot Water Cylinder | Heating/Cooling | Low Temperature Heat (<100 C), Water Heating | Non-Transport | 12,716.265423 | 13,208.147352 | 491.881929 |
| Industrial | Dairy Product Manufacturing | C113 | Electricity | Electricity | Heat/Cooling Devices | Refrigeration Systems | Heating/Cooling | Refrigeration | Non-Transport | 1,164.983982 | 713.238915 | -451.745067 |
| Transport | Road Transport | Z002 | Electricity | Electricity | Light Commercial Vehicle | Battery Electric Vehicle | Mobile Motive Power | Motive Power, Mobile | Light Vehicles | 18.909833 | 368.277952 | 349.368119 |
| Transport | Road Transport | Z002 | Electricity | Electricity | Light Passenger Vehicle | Battery Electric Vehicle | Mobile Motive Power | Motive Power, Mobile | Light Vehicles | 562.756667 | 273.245434 | -289.511233 |
| Industrial | Food and Beverage Product Manufacturing (excluding Dairy, Meat, Seafood) | C114-C119, C12 | Electricity | Electricity | Stationary Motors | Pump Systems (for Fluids, etc.) | Stationary Motive Power | Pumping | Non-Transport | 287.560031 | 518.116307 | 230.556276 |
| Residential | Residential | Z001 | Electricity | Electricity | Heat/Cooling Devices | Refrigeration Systems | Heating/Cooling | Refrigeration | Non-Transport | 5,621.58962 | 5,839.040091 | 217.450471 |
| Residential | Residential | Z001 | Electricity | Electricity | Heat/Cooling Devices | Resistance Heater | Heating/Cooling | Low Temperature Heat (<100 C), Space Heating | Non-Transport | 5,248.047686 | 5,451.049058 | 203.001372 |
| Transport | Road Transport | Z002 | Fossil Fuels | Diesel | Light Commercial Vehicle | Internal Combustion Engine | Mobile Motive Power | Motive Power, Mobile | Light Vehicles | 33,742.580962 | 33,540.28858 | -202.292382 |
| Residential | Residential | Z001 | Electricity | Electricity | Heat/Cooling Devices | Misc, Residential Only (Battery chargers, Pools, Pumps)   | Electronics and Lighting | Electronics and Other Electrical Uses | Non-Transport | 5,153.97668 | 5,353.339312 | 199.362632 |
| Residential | Residential | Z001 | Electricity | Electricity | Electronics and Lights | IT and Entertainment | Electronics and Lighting | Electronics and Other Electrical Uses | Non-Transport | 4,610.924495 | 4,789.281139 | 178.356644 |
| Residential | Residential | Z001 | Electricity | Electricity | Heat/Cooling Devices | Cooking Appliances, Residential Only (Cooktops/Microwaves/Ovens/Uprights)   | Heating/Cooling | Intermediate Heat (100-300 C), Cooking | Non-Transport | 4,442.205222 | 4,614.035582 | 171.83036 |
| Residential | Residential | Z001 | Electricity | Electricity | Heat/Cooling Devices | Heat Pump (for Heating) | Heating/Cooling | Low Temperature Heat (<100 C), Space Heating | Non-Transport | 4,414.108011 | 4,584.851499 | 170.743488 |
| Industrial | Meat and Meat Product Manufacturing and Seafood | C111-C112 | Electricity | Electricity | Heat/Cooling Devices | Refrigeration Systems | Heating/Cooling | Refrigeration | Non-Transport | 1,744.297389 | 1,581.272486 | -163.024903 |
| Industrial | Food and Beverage Product Manufacturing (excluding Dairy, Meat, Seafood) | C114-C119, C12 | Electricity | Electricity | Electronics and Lights | Lights | Electronics and Lighting | Lighting | Non-Transport | 187.230791 | 337.346349 | 150.115558 |
| Industrial | Dairy Product Manufacturing | C113 | Electricity | Electricity | Stationary Motors | Electric Motor | Stationary Motive Power | Motive Power, Stationary | Non-Transport | 306.28813 | 187.518985 | -118.769145 |
| Industrial | Dairy Product Manufacturing | C113 | Electricity | Electricity | Electronics and Lights | Air Compressors | Electronics and Lighting | Compressed Air | Non-Transport | 276.933663 | 169.547279 | -107.386384 |

Full table: `EEUD_2023_changed_categories.csv`

## Aggregate Deltas

### By SectorGroup

| SectorGroup | Old_TJ | New_TJ | Delta_TJ |
| --- | --- | --- | --- |
| Industrial | 166,710.471147 | 159,324.260022 | -7,386.211124 |
| Transport | 207,544.288153 | 202,436.110997 | -5,108.177156 |
| Residential | 83,552.495409 | 85,395.819124 | 1,843.323715 |
| Commercial | 55,527.656466 | 55,623.942632 | 96.286166 |
| Agriculture, Forestry and Fishing | 29,408.711052 | 29,408.866803 | 0.155751 |

### By Sector

| SectorGroup | Sector | Old_TJ | New_TJ | Delta_TJ |
| --- | --- | --- | --- | --- |
| Transport | Air Transport | 18,546.101337 | 13,481.928484 | -5,064.172853 |
| Industrial | Wood Product Manufacturing | 21,095.270261 | 16,543.895896 | -4,551.374365 |
| Industrial | Industrial - Unallocated | 9,986.607357 | 13,806.755113 | 3,820.147756 |
| Industrial | Dairy Product Manufacturing | 32,669.33676 | 30,165.980716 | -2,503.356044 |
| Residential | Residential | 82,979.495409 | 85,395.819124 | 2,416.323715 |
| Industrial | Electricity, Gas, Water and Waste Services | 2,085.82496 | 0 | -2,085.82496 |
| Industrial | Pulp, Paper and Converted Paper Product Manufacturing | 12,518.870936 | 10,807.079761 | -1,711.791175 |
| Industrial | Food and Beverage Product Manufacturing (excluding Dairy, Meat, Seafood) | 6,409.626925 | 7,929.34617 | 1,519.719245 |
| Industrial | Furniture and Other Manufacturing | 844.705862 | 0 | -844.705862 |
| Residential | <NA> | 573 | 0 | -573 |
| Commercial | Data Centers | 0 | 492 | 492 |
| Commercial | <NA> | 7,099.6315 | 7,460.508542 | 360.877042 |
| Industrial | Primary Metal and Metal Product Manufacturing | 24,817.175836 | 24,472.529473 | -344.646363 |
| Industrial | Petroleum, Basic Chemical and Rubber Product Manufacturing | 26,330.934591 | 26,006.235991 | -324.6986 |
| Commercial | Transport, Postal and Warehousing (Commercial - Non-Transport) | 3,183.591092 | 2,894.898785 | -288.692307 |

### By Fuel

| FuelGroup | Fuel | Old_TJ | New_TJ | Delta_TJ |
| --- | --- | --- | --- | --- |
| Renewables | Wood | 30,456.629979 | 24,359.245758 | -6,097.384221 |
| Fossil Fuels | Av. Fuel/Kero | 18,546.101337 | 13,481.928484 | -5,064.172853 |
| Electricity | Electricity | 138,212.862011 | 140,115.982838 | 1,903.120827 |
| Fossil Fuels | LPG | 10,372.495072 | 9,654.903307 | -717.591765 |
| Fossil Fuels | Diesel | 147,334.130413 | 146,778.367877 | -555.762536 |
| Renewables | Biogas | 354.2296 | 310.2616 | -43.968 |
| Renewables | Geothermal | 7,448.885421 | 7,470.021329 | 21.135908 |
| Fossil Fuels | Natural Gas | 68,694.263993 | 68,694.263983 | -0.00001 |
| Fossil Fuels | Coal | 18,637.485013 | 18,637.485016 | 0.000003 |
| Fossil Fuels | Fuel Oil | 1,401.774361 | 1,401.77436 | -0.000001 |
| Fossil Fuels | Petrol | 100,920.765028 | 100,920.765027 | -0.000001 |
| Renewables | Solar | 364 | 364 | 0 |

### By EndUse

| EndUse | Old_TJ | New_TJ | Delta_TJ |
| --- | --- | --- | --- |
| Intermediate Heat (100-300 C), Process Requirements | 45,057.248009 | 37,586.500125 | -7,470.747884 |
| Motive Power, Mobile | 252,495.606742 | 247,337.932139 | -5,157.674603 |
| <NA> | 19,192.015531 | 22,832.564223 | 3,640.548692 |
| Pumping | 6,302.329255 | 3,944.114948 | -2,358.214307 |
| Electronics and Other Electrical Uses | 13,745.059225 | 14,564.322879 | 819.263654 |
| High Temperature Heat (>300 C), Process Requirements | 48,336.312052 | 47,619.73832 | -716.573732 |
| Fans | 2,786.891435 | 2,219.4886 | -567.402835 |
| Low Temperature Heat (<100 C), Space Heating | 41,653.101225 | 42,096.540422 | 443.439197 |
| Low Temperature Heat (<100 C), Water Heating | 37,275.495869 | 37,717.374067 | 441.878198 |
| Intermediate Heat (100-300 C), Cooking | 8,137.899204 | 8,368.831585 | 230.932381 |
| Refrigeration | 16,194.031532 | 16,391.224166 | 197.192634 |
| Motive Power, Stationary | 17,395.975474 | 17,233.484719 | -162.490755 |

### By Technology

| Technology | Old_TJ | New_TJ | Delta_TJ |
| --- | --- | --- | --- |
| Boiler Systems | 81,532.445243 | 73,805.409154 | -7,727.03609 |
| Turbine Engine | 18,546.101337 | 13,481.928484 | -5,064.172853 |
| <NA> | 19,192.015531 | 22,832.564223 | 3,640.548692 |
| Pump Systems (for Fluids, etc.) | 7,200.965007 | 4,842.7507 | -2,358.214307 |
| Fan Systems | 2,786.891435 | 2,219.4886 | -567.402835 |
| Furnace/Kiln | 10,281.138611 | 9,769.551122 | -511.587489 |
| Hot Water Cylinder | 18,093.886569 | 18,542.829914 | 448.943345 |
| Electronics | 3,980.15805 | 4,421.702428 | 441.544378 |
| Resistance Heater | 12,108.819097 | 12,343.95042 | 235.131323 |
| Direct Heat | 0 | 209 | 209 |
| Misc, Residential Only (Battery chargers, Pools, Pumps)   | 5,153.97668 | 5,353.339312 | 199.362632 |
| Refrigeration Systems | 16,194.031532 | 16,391.224166 | 197.192634 |

## Notes For Follow-Up

- `Data Centers` appears as a genuinely new commercial sector in the new workbook.
- `Electricity, Gas, Water and Waste Services` and `Furniture and Other Manufacturing` disappear as sector labels in the new workbook.
- One commercial natural-gas row appears to have lost its sector label rather than its value.
- Residential `Solar` and `Geothermal` rows move from mostly blank category fields in the old workbook to more explicit categorization in the new workbook.
- The air-transport drop appears to be a direct source change in the raw EEUD workbook rather than a rename or redistribution within 2023 aviation rows.
