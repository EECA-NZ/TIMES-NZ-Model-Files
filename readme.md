# TIMES-NZ-Model-Files
![CI Pipeline](https://github.com/EECA-NZ/TIMES-NZ-Model-Files/actions/workflows/ci.yml/badge.svg)
[Test Coverage Report](https://eeca-nz.github.io/TIMES-NZ-Model-Files)

Developed by [Energy Efficiency and Conservation Authority](https://github.com/EECA-NZ), [BusinessNZ Energy Council](https://bec.org.nz/) and [Paul Scherrer Institut](https://www.psi.ch/en)

## TIMES-NZ 101 

TIMES-NZ is a model of New Zealand’s entire energy system, from raw materials, to generation, to consumption. It shows how New Zealand might meet future energy demand while minimising costs.

It was built for New Zealand based on the International Energy Agency’s TIMES framework, which has been used by more than 60 countries worldwide.
TIMES-NZ is designed to select for the lowest-cost energy system, making it a useful complement to other energy modelling. EECA and the Business Energy Council (BEC) are currently the only organisations in New Zealand to have invested the resources and expertise to develop TIMES for New Zealand.

TIMES NZ can be used to explore a huge range of different energy futures, showing how factors such as falling gas supply, oil prices, carbon prices, the cost of EVs and solar (and more) could interact.

We give it information on the New Zealand energy system as it is today, along with plausible projections for what the future technology and fuel options will be, including and emerging fuels such as hydrogen and biomass. It then finds the lowest-cost pathway to restructure the country’s entire energy system to meet expected levels of energy demand, for example demand for transport, manufacturing, residential heating, commercial activity and more. It is built to account for all the linkages and interactions between different parts of the system.

The model doesn’t answer how to run the energy system; instead it can help structure conversations about trade-offs and uncertainties – and the implications of different energy policies.

TIMES NZ 3.0 is the third iteration of the model using New Zealand data and incorporates feedback from users of previous versions. EECA and BEC plan to update TIMES NZ 3.0 regularly to keep pace with major energy developments.

## Documentation

See all project documentation at our [documentation site](https://times-nz-dev.readthedocs.io/en/latest/index.html).

## Developer Quickstart

This is a shortened setup guide for developers who want to either build model input files or run the internal Shiny app. For the full workflow, including VEDA and GAMS setup, use the [developer documentation](https://times-nz-dev.readthedocs.io/en/latest/index.html).

### Prerequisites

- WSL/Ubuntu is the recommended development environment.
- Python 3.12+ and [Poetry](https://python-poetry.org/docs/) are required.
- If you want to run the full model workflow through VEDA, you will also need a working Windows installation of VEDA and GAMS.

### Build the model input files

Install the prep module and run the full data-preparation pipeline:

```bash
cd PREPARE-TIMES-NZ
poetry install --with dev
poetry run doit
```

This generates the TIMES model files in `PREPARE-TIMES-NZ/output`.

Useful alternatives:

```bash
poetry run python scripts/prepare_times_nz.py
poetry run pytest
```

### Run the internal Shiny app

Install the app module dependencies and start the app locally:

```bash
cd TIMES-NZ-INTERNAL-QA
poetry install
poetry run python run_local.py
```

The app uses processed data in `TIMES-NZ-INTERNAL-QA/data`. If you need to refresh model outputs and labels from the latest prep outputs and local VEDA results, run the post-processing workflow first:

```bash
cd TIMES-NZ-INTERNAL-QA
poetry run python src/times_nz_internal_qa/postprocessing/run_all_postprocessing.py
```

Note: parts of post-processing depend on `PREPARE-TIMES-NZ/data_intermediate` already being populated, and VEDA result import requires a local VEDA installation.


## License

This project is licensed under the MIT License - see the LICENSE file for details.
