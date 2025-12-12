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
:caption: Key topics

data_structures
configuration_file_guide

```

```{toctree}
:maxdepth: 1
:caption: Other topics

documentation_maintenance

```


## Poetry environment switching 

It's important to stick to the poetry env that's been designated for each module. The fastest way to approach this is to navigate to the package directory that you want to work in in the terminal, then: 

1) `deactivate` disables whatever poetry env you previously had working 
2) `poetry env activate` prints to console the command for activating that package's env. Just paste that into the terminal.


