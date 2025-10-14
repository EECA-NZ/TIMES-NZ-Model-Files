This app is designed to explore all result outputs of TIMES-NZ 3.0 in a high level of detail. It is intended as an "explorer", rather than a communication tool. 

It is for QA purposes and as an early way to distribute results.

### Layout

As TIMES-NZ is a total energy system model, results are organised according to the structure of the energy balance tables:

 - Production (Primary energy production and imports)
 - Transformation (conversion of one form of energy into another)
 - Energy demand (energy end use)

Additional sections include: 

 - Emissions (energy emissions from all sources)
 - "Energy service demand", 
 - Model infeasibilities. These are developer facing items used in QAing the model results. They will be removed once the model results are calibrated correctly. 

 Each section includes a detailed explorer, and potentially multiple different charts. You can adjust the groups by which data is presented, and filter along many dimensions, depending on the underlying data. 
 
 Filter options always relate to the underlying data. This means, for example, you could filter for "SectorGroup" = "Transport", and then the more detailed "Sector" filter options would only include Transport subsectors. 

 You can always download the full data for that section on the button to the left, or download summary chart data based on your current group and filter selection. 

#### Production 

*(not yet built)*

This is primary energy production in the model, which includes domestic production and imports of energy, excluding exports. It does not include energy transformation processes, such as electricity generation or biofuel production.

#### Electricity generation 

This page covers all generation, including output generation, fuels used for generation, and capacity. Data is available per plant, as TIMES-NZ 3.0 models all electricity generation assets individually. This is a specific form of energy transformation.

#### Other energy transformation

*not yet built* 

This page covers all energy transformation not covered in the electricity generation section. If we had a refinery, 

#### Energy demand 

This covers final energy demand. This includes non-energy use of fuels, such as feedstock gas at Methanex or coal used for steel production. However, it excludes energy used for transformation

#### Emissions 

Covers energy emissions from all areas of the energy system.

#### Energy service demand 

*not yet built*

Shows the useful output delivered by energy demand devices. This could be number of kilometres travelled by a vehicle, or hot water, or dry clothes. These levels of demand are set exogenously in the model; TIMES-NZ then optimises the energy system to meet the demand. This means that the end use demands on this page can be thought of as a key *model input* of demand projections. 