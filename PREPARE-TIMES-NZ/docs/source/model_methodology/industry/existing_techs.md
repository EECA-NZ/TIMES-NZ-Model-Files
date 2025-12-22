# Existing technologies

Existing technologies and their details, such as lifetimes, capacity factors, efficiencies are detailed here. 

## Equipment lifetime and decommissioning

### Rotating equipment such as pumps, fans, compressor, motors, refrigeration, internal combustion engines
Where possible, equipment lifetimes are taken as estimated useful life (years) from the Inland Revenue’s General depreciation rates October 2024 document[^ir_lifetimes], if unavailable, data are taken from other EECA sources such as technology scans, Energy Transition Accelerator Reports and industry sources/knowledge.

### Boilers/furnaces/ovens/refiners/reformers/heat exchangers
Boilers, refiners and reformers are all given a lifetime out to 2060 (i.e. the full TIMES model period), as this equipment is generally operated well past its original engineering and economic design life, and is typically only updated when it makes economic sense to (e.g. when the Net Present Value is greater than zero or the Marginal Abatement Cost is lower than the carbon price).

For coal fired boilers, the low to medium temperature coal boilers (i.e. under 300°C) are modelled to switch to renewable energy before 2037, when the National Direction for Greenhouse Gas Emissions from Industrial Process Heat regulations come into effect, or before that date if it makes financial sense. 

### Electrical equipment such as heaters

As with rotating equipment, lifetimes are taken as estimated useful life (years) from the Inland Revenue’s General depreciation rates October 2024 document, if unavailable, data are taken from other EECA sources such as technology scans, Energy Transition Accelerator Reports and industry sources/knowledge.

### Aluminium, urea, methanol and steel equipment

Aluminium, steel, methanol and urea technologies have their lifetimes extended throughout the model horizon. We assume these technologies will not be replaced, except for the NZ Steel furnace conversion which is planned to be operational in Q2 of 2026. 
A full list of lifetime assumptions can be found in {numref}`tab-ind_tech_lifetimes`. Technologies with `N/A` lifetimes are assumed to never retire,  unless it makes economic sense to switch to a different technology before the full model period. 

[^ir_lifetimes]: IR | General depreciation rates August 2024: <https://www.ird.govt.nz/-/media/project/ir/home/documents/forms-and-guides/ir200---ir299/ir265/ir265-august-2024.pdf>

```{list-table} Equipment lifetime by technology
:header-rows: 1
:name: tab-ind_tech_lifetimes
* - Technology
  - Life (years)
* - Electric Furnace
  - N/A
* - Lights
  - 10
* - Boiler Systems
  - N/A
* - Burner (Direct Heat)
  - N/A
* - Furnace/Kiln
  - N/A
* - Heat Pump (for Heating)
  - 15
* - Resistance Heater
  - 15.5
* - Electric Motor
  - 10
* - Pump Systems (for Fluids, etc.)
  - 10
* - Internal Combustion Engine (Land Transport)
  - 15.5
* - Stationary Engine
  - 20
* - Air Compressors
  - 15.5
* - Fan Systems
  - 16
* - HVAC
  - 10
* - Refrigeration Systems
  - 20
* - Industrial Ovens
  - N/A
* - Feedstock
  - N/A
* - Reformer
  - N/A
* - Refiners
  - N/A
```

## Availability factors

The availability factor represents the share of a given year a piece of equipment is “available” to operate:

```{math}
Availability Factor = (Available Operating Time) / (Total Time)
```

It is challenging to apply an availability to a piece of technology (e.g. medium temperature boiler) across different industrial sites. For example, Fonterra would operate their boiler differently to a small family-owned dairy manufacturing site. Therefore, we currently set a single availability factor. An availability factor of $0.5$ was selected to provide a standard value to use across technologies when accurate numbers are unavailable.


## Energy efficiency



A full list of energy efficiency assumptions can be found in Table 9. These assumptions are for standard technologies used across various sectors and not for specific bespoke technologies such as the furnaces used at New Zealand aluminium smelter and NZ steel.
Energy efficiency for process heat devices came from the Cost Assessment Tool developed for the Resource Management Act (RMA) National Direction for Greenhouse Gas Emissions from Industrial Process Heat . The technology’s energy efficiency was taken as the middle range from the “lower efficiency bound” and the “upper efficiency bound”.
Efficiencies for internal combustion engine (land transport), pump systems (for fluids), electric motors, and stationary engines were found using literature reviews.


# INCOMPLETE