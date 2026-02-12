
# Changelog 

## 3.0.2

**Features**
- Added more detail to residential load curves, allowing for different load profiles per use type.

**Model fixes**
- (Residential) Resolved an error that undercounted space heating demand in detached dwellings.
- (Natural gas) Fixed a methodological error that double-counted domestic natural gas costs.

## 3.0.1

**Features**
- Incorporated documentation into sphinx-based site for hosting on readthedocs
- Explorer now includes detailed transport demand, service, and capacity chart options

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
- Initial build of `TIMES-NZ-INTERNAL-QA` module, which allows for post-processing and interrogation of model results.
- Rebuilt and updated model for base year 2023 and new Traditional and Transformation scenarios.