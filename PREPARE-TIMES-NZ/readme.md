# PREPARE TIMES-NZ

This module creates and populates all input excel configuration files for TIMES-NZ 3.0 and later. Because a TIMES model is entirely defined by its input configuration files, this effectively is TIMES-NZ, and everything else is just post-processing.

Full documentation for this module is housed at XXX. I will describe this in full soon because it's getting rebuilt 


Existing docs: 

 - See [Data Structures](docs/developer_guide/data_structures.md) for details about the module's structure and organization, including code and data locations.
 - Refer to [the Configuration File Guide](docs/developer_guide/configuration_file_guide.md) for descriptions and examples of the `.toml` configuration files.
 - The directory `docs/model_methodology/` contains documentation for methods used in creating TIMES 3.0. `THIS IS GOING TO BE UPDATED`
 - When running the workflow to build the configuration files, a metadata file is created at `data_intermediate/stage_0_config/config_metadata.csv`. This fully lists all input file Veda tags, including descriptions and input data locations, and we generated markdown for this too. 
 



