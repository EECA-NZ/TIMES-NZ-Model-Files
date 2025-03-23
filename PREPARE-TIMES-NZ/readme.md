## Pre-processing with Python

```
THIS MODULE IS UNDER DEVELOPMENT
```

To prepare the TIMES-NZ model files, we will be implementing pre-processing using the following command:

```python
prepare_times_nz.py
```

## STRUCTURE

See `docs/data_structures.md` for an outline of this module's structure and organisation methods. 

## Configuration files 

See `docs/configuration_file_guide.md` for a description and examples on how the `.toml` configuration files work. 



## General Future State

```mermaid
flowchart LR
    CSV[("CSV/TOML Files")]
    EXCEL["Excel Processing"]
    MIGRATE_FORMULAS["Migrate formula logic (iterative)"]
    VEDA["VEDA Analysis"]
    OUTPUT["Data Output"]
    SHINY["Public Shiny Dashboard"]
    
    INTERNAL_QA["Internal QA Tools"]    

    subgraph XL2TIMES["XL2Times"]
        EXCEL["Excel Processing"]
        VEDA["VEDA Analysis"]
    end



    CSV --> EXCEL
    EXCEL --> MIGRATE_FORMULAS
    MIGRATE_FORMULAS --> CSV
    EXCEL --> VEDA
    VEDA --> OUTPUT
    OUTPUT --> SHINY
    OUTPUT --> INTERNAL_QA
    


```
