
# Changelog

## 3.0.5

**Assumption changes**

- Solar generation capacity factors for different timeslices are now generated from NIWA EPW weather files using PVWatts, using MBIE's October 2024 TMY3 (present climate) release.
- Allowed the electricity sector to build new diesel peakers, using cost and efficiency assumptions from existing OCGT data.
- Assumed all grid-scale solar utilised single-axis tracking technology.
- Added or tweaked several new industrial technologies, allowing more flexibility in the demand end, including some hydrogen uses.
- Added biomass as a fuel option for high-temperature heat in cement production to reflect the Golden Bay Cement biomass transition. 
- Added existing/known grid-scale battery installations.
- Increased battery lifespan assumptions.
- Increased geothermal generation lifespan assumptions.


**Model features**

- Rebuilt hydrogen electrolysis methods to correctly utilise electricity demand.
- Increased model detail of distributed solar, reflecting improved capacity factor from larger-scale rooftop installations. 
- Added a more robust demand-flex method. This means ripple control is reflected more accurately with minimal processing overhead. Scalable to other demand flex areas as needed. 

**Model fixes** 
- Resolved an error which led to excessive technology inflexibility in transport utilisation constraints. This allows for more realistic purchasing behaviour across different utilisation categories.
- Disabled excessive optimisation of energy service demand between timeslices, which was leading to unrealistic demand flex behaviour. Note that this change also disables ESD timeslice reporting. 
- Corrected several links in biogas topology. 

## 3.0.4

**Assumption changes**
 - Adjusted lightbulb lifetimes in residential and commercial sectors according to usage assumptions.
 - Ensured realistic minimum utilisation of peaking plants.
 - Slightly increased conservative hydro peaking contribution assummption to 90%.
 - Create "two-tier" LNG market, limiting its use to electricity generation.


**Model fixes**
 - Corrected implementation of new technologies for industrial applications.
 - Resolved a bug in implementation of 2037 coal boiler ban for intermediate process heat.
 - Resolved an issue that made industrial petrol engines more efficient than intended.
 - Resolved a bug leading to infeasible coal and biogas usage.
 - Added unallocated onsite generation to total system demand, ensuring system balance.
 - Add missing residential petrol emissions.
 - Allowed some industrial subsectors to electrify water heating using technologies already found in other subsectors.

## 3.0.3

**Features**
 - Changed distributed solar process to use exogenous forecasts, providing more realistic results.
 - Rebuilt gas distribution network to allow for biomethane blending and more accurately represent maintenance costs as fixed, rather than per unit of throughput.


**Assumption changes**
 - Adjusted LNG terminal to fixed installation date in 2027 for Traditional scenario. LNG remains excluded from Transformation.
    - Also removed MIP functionality as this is no longer required.
 - Minor adjustments to capital costs for agricultural heating technologies following review.
 - Decreased average geothermal generation assumption slightly to align better with base year data.
 - Removed contingent gas from Traditional scenario.

**Model fixes**
- (Biofuel) Improved municipal waste production differences between scenarios.
- (Gas supply) Fixed historical domestic field output levels.
- (Electricity generation) Fixed incorrect wind availability curve assumptions.
- (Electricity generation) Fixed dispatchable hydro and wind peak contribution factors not aligning with documentation.
- (Agriculture) Improved modelling of geothermal heating for indoor cropping.
- (Agriculture) Fixed a bug that meant agricultural energy emissions were counted incorrectly.
- (Agriculture) Added greater distinction for refrigeration, offroad transport, and heating technologies.
- (Agriculture) Resolved an issue that meant petrol-powered boats and farm bikes were more efficient than intended.
- (Residential) Fixed an issue allowing too much flexibility in space heating technologies.
- (Commercial) Added greater distinction for boilers, burners, and resistance heaters.
- (Commercial) Fixed modelling of geothermal heating for education, healthcare, WSR, and other commercial sectors.
- (Commercial) Resolved an error that led to some LPG, natural gas, diesel, and petrol technologies being cheaper than intended.
- (Industry) Resolved an error that allowed Methanol and Urea to close different parts of their business at different rates.


## 3.0.2

**Features**
- Added more detail to residential load curves, allowing for different load profiles per use type.
- Added an additional biofuel supply forecast scenario with AD feedstock growth and higher recoverability of biomass.
- Separated biogas and biomethane modelling commodities, including a specific process for carbon scrubbing.
- Added demand flex options for residential water heating, including splits between scenarios.

**Model fixes**
- (Residential) Resolved an error that undercounted space heating demand in detached dwellings.
- (Natural gas) Fixed a methodological error that double-counted domestic natural gas costs.
- (Commercial) Resolved an error that left commercial heatpumps more expensive and with worse efficiency than intended.
- (Residential, Commercial) Fixed a methodological error that overly restricted demand device time flexibility.
- (Electricity generation) Ensured geothermal plants operate as baseload.
- (Electricity generation) Resolved an error that limited hydro dam output flexibility.

**Assumption changes**
- (Electricity generation) Adjusted Traditional and Transformation NREL scenarios from Conservative and Moderate to Moderate and Advanced, respectively.
- (Commercial, Residential) Increased heatpump lifetimes slightly.
- (Industrial) Removed some load curve assumptions.

## 3.0.1

**Features**
- Incorporated documentation into sphinx-based site for hosting on readthedocs.
- Explorer now includes detailed transport demand, service, and capacity chart options.

**Model fixes**
- (Biofuel) Ensured electricity demand was integrated into biofuel transformation processes.
- (Commercial) Resolved an error that led to some demand technologies being cheaper than intended.
- (Electricity) Ensured biogas and biomethane were made available as options for existing gas-fired plants.
- (Electricity) Allowed Huntly Rankines to use black pellets.
- (Transport) Ensured utilisation band constraints were properly fixed across model horizon.
- (Transport) Resolved an error that led to electric heavy truck costs decreasing faster than intended in some scenarios.
- (Transport) Resolved an error that led to some vehicle types having unrealistic utilisation rates.

## 3.0.0

**Features**

- Initial build of `PREPARE-TIMES-NZ` module, which creates TIMES-NZ model files based on hosted data and code.
    - All preprocessing methods migrated to python and open-sourced, to ensure replicability and tracability.
- Initial build of `TIMES-NZ-INTERNAL-QA` module, which allows for post-processing and interrogation of model results.
    - Results hosted publicly and can be explored at the highest possible level of detail to ensure transparency.
- Rebuilt and updated model for base year 2023 and new Traditional and Transformation scenarios.
