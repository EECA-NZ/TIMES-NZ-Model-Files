# Model issues log

This log refers only to issues or missing features in the model itself. This excludes any potential issues related to post-processing or backend data management. 


## Emissions 

- Historical modelled emissions (2024/2025) do not align perfectly with historical data 
- Would be good to add a sensitivity for a net zero scenario. Can make a new run with a single emisisons constraint to achieve this - in theory not much trouble but solution might be infeasible. 


## Electricity generation 
 - The generation stack needs expanding to: a) include diesel peakers, and b) allow natural gas plants to use biogas. 
 - Rankine black pellet use and lifetime may need review
 - Geothermal electricity generation emisisons do not currently consider future carbon capture installation plans or field carbon intensity decay. Currently, only one emissions factor is used for all fields, which is not accurate.

## Electricity demand 

 - Residential load curves currently assume all use follows the same curve. This is the TIMES 2.0 method. However, it is a problem, because space heating is the key driver of peak load, limiting overall system uptake, so we should represent this load curve separately, allowing more efficient space heating techs to have the correct impact on peak.
 - Residential demand flex and the Tiwai demand flex contract are not currently modelled. This is especially important for residential hot water ripple control.
 - Modelling homes as blocks per region allows model consumers to switch between heating devices, only using less efficient resistance heaters when heat pump capacity is already fully utilised. We should instead assign availability curves per time of day for all heating technologies, as real consumers often cannot choose which technology to use on an hourly basis. 

## Natural gas 
- Kapuni gas is underutilised, presumably due to higher carbon costs. This points to a minor imbalance in the demand sector - in reality, Kapuni natural gas is in high demand. 
 - The model representation of gas network maintenance costs leads to unintended outcomes. Currently, these are assigned based on real-world delivery costs on a per-unit basis. The model, then, optimises maintenance costs by quickly and significantly reducing residential natural gas demand, as this is the highest maintenance cost on a per-unit basis. This is not realistic, as a reduction in natural gas demand does not reduce maintenance costs but should raise them for other users. It would be better to represent maintenance/delivery costs as a fixed capacity cost, which will capture behaviour better but also capture the "death spiral". 
- Currently, scrubbed biogas (biomethane) can replace industrial use of LPG. This assumes onsite anaerobic diestion. However, LPG and biomethae have different chemical properties, so this is likely unrealistic. We should ensure that biomethane use requires natural gas or biomethane equipped boilers, rather than being able to perfectly replace industrial LPG use. 

## Other supply side 

- Bioenergy feedstock availability and costs are not yet changed between scenarios to represent different possible regulatory environments. 
 - Hydrogen production is currently very crudely modelled, not appropriately calling on electricity demand for electrolysis. 
 - Hydrogen demand side currently limited to transport and a few minor agriculture machines. We need to add more detail on where and how green hydrogen can be used. Likely we should allow all industrial natural gas use to be replaced with hydrogen, assuming onsite electrolysis and subsequent electricity demand. 
 - Industrial coal boiler retrofit options to biomass are not currently implemented, meaning model industrial users must purchase a biomass boiler rather than refiting their existing coal boilers.



