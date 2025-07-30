## Pre-processing with Python

```
THIS MODULE IS UNDER DEVELOPMENT
```

To install this module into your local environment, enter the `PREPARE-TIMES-NZ` with your `.venv` activated and run:
```
python -m pip install -e .
```

To prepare the TIMES-NZ model files, we will be implementing pre-processing using the following command, run in the `PREPARE-TIMES-NZ` directory:

```powershell
doit
```

This runs a `doit` pipeline to create an output folder of excel files ready for Veda processing based on the user config and data for TIMES 3.0.

Alternatively, you can run `python prepare_times_nz_from_archive.py` in `scripts` to fully generate the TIMES 2.1.3 excel files from the raw tables summary text. This exists as a proof of concept for the generation methods, as these files create a model that matches TIMES 2.1.3 perfectly.

Note that each script is designed to run locally, and stores all outputs in `output` and intermediate data in `data_intermediate`. These directories are not tracked by git and are fully refreshed on every run.


## STRUCTURE

See `docs/data_structures.md` for an outline of this module's structure and organisation methods.

## Configuration files

See `docs/configuration_file_guide.md` for a description and examples on how the `.toml` configuration files work.

## Model methodology and documentation

`docs/model_methodology/` contains documentation on various methods used for creating TIMES 3.0.

After executing `prepare_times_nz.py`, a metadata file is also created in `data_intermediate/stage_0_config/config_metadata.csv` This file lists all worksheets and tags generated with helpful descriptions (which have been assigned to Veda tags in the config files.)

Any user creating new methods or submodels should add accompanying method documentation to this folder.


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
