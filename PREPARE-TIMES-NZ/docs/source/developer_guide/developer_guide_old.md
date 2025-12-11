# PREPARE-TIMES-NZ Developer Guide

This document is intended for analysts and modellers wishing to work with the PREPARE-TIMES-NZ package, and either modify or update the TIMES-NZ model. 

It is a WIP 

In summary, the project: 

1. Hosts all data and assumptions used for TIMES-NZ, untouched from source files.
1. Processes these, aggregating or modelling as required for the TIMES model inputs
1. Outputs clean, machine-readable data for each key component. 
1. Additionally, formats these into the excel tables intended to be read by Veda or XL2TIMES before sending to GAMS for solving. 


Processing scripts are organised by sector (electricity generation, commercial demand, etc), and stage (raw data, base year processing, scenario processing, veda formatting)


## Contents: 

- [Installation and setup guide] (To be written, combining docs from elsewhere in a central location), which just ensures your machine is correctly setup for the project.
- [A description of the project's structure](./developer_guide/data_structures.md), which explains how everything is staged and flows from raw data to Veda outputs. 
- [Working with input configuration files](./developer_guide/configuration_file_guide.md), listing key components of the input structures and how to use these to shape the outputs

Read about the assumptions and methodology 

## Poetry environment switching 

It's important to stick to the poetry env that's been designated for each module. The fastest way to approach this is to navigate to the package directory that you want to work in in the terminal, then: 

1) `deactivate` disables whatever poetry env you previously had working 
2) `poetry env activate` prints to console the command for activating that package's env. Just paste that into the terminal.