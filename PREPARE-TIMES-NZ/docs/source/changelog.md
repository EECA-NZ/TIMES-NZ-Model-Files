
# Changelog 

## 3.0.1

**Features**
- Incorporated documentation into sphinx-based site for hosting on readthedocs.io

**Model fixes**
- (Commerical) Resolved an error that led to some demand technologies being cheaper than intended.
- (Natural gas) Resolved a methodological error that resulted in double-counting natural gas costs. 
- (Transport) Ensured utilisation band constraints were properly fixed across model horizon.
- (Transport) Resolved an error that led to electric heavy truck costs decreasing faster than intended in some scenarios. 
- (Transport) Resolved an error that led to some vehicle types having unrealistic utilisation rates.

## 3.0.0

**Features**

- Initial build of `PREPARE-TIMES-NZ` module, which creates TIMES-NZ model files based on hosted data and code.
- Initial build of `TIMES-NZ-INTERNAL-QA` module, which allows for post-processing and interrogation of model results.
- Rebuilt and updated model for base year 2023 and new Traditional and Transformation scenarios.