# Developer guide

This section is intended for developers and modellers seeking to maintain, update, or change the underlying method. It may also be useful for other users seeking to better understand the underlying codebase. 

In summary, the project: 

1. Hosts all data and assumptions used for TIMES-NZ, untouched from source files.
1. Processes these, aggregating or modelling as required for the TIMES model inputs
1. Outputs clean, machine-readable data for each key component. 
1. Additionally, formats these into the excel tables intended to be read by Veda or XL2TIMES before sending to GAMS for solving. 

Processing scripts are organised by sector (electricity generation, commercial demand, etc), and stage (raw data, base year processing, scenario processing, veda formatting)

```{toctree}
:maxdepth: 2
:caption: Project setup
developer-setup-guide
github-flow-readme
```

```{toctree}
:maxdepth: 2
:caption: PREPARE-TIMES-NZ structure

configuration_file_guide
data_structures
model-structure
code-lookups
```


```{toctree}
:maxdepth: 1
:caption: Other topics
documentation_maintenance
```

