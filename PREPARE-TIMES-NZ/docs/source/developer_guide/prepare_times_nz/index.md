# PREPARE-TIMES-NZ

Guidance for configuring, understanding, and maintaining the preparation
pipeline that creates the model workbooks.

## Quickstart guide

1) Ensure you have successfully pulled all data from the repo, even those marked with `git lfs`, via

```bash
git lfs install
git lfs pull
```
This downloads the large raw files required to produce the model. 

2) Run the data preparation pipeline (`doit`):

```bash
uv run --directory PREPARE-TIMES-NZ doit
```

`doit` runs the entire data preparation method and creates TIMES model files in `PREPARE-TIMES-NZ/output`.


## Contents 

See pages below for detail on the mechanics and maintenance of the `PREPARE-TIMES-NZ` module.

```{toctree}
:maxdepth: 1

configuration_file_guide
data_structures
code-lookups
```
