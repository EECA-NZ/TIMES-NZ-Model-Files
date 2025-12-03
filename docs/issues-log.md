# Model issues log

This log refers only to issues or missing features in the model itself. This excludes any potential issues related to post-processing or backend data management. 


## Electricity generation 
 - The generation stack needs expanding to: a) include diesel peakers, and b) allow natural gas plants to use biogas. 
 - Rankine black pellet use and lifetime may need review
 - Geothermal electricity generation emisisons do not currently consider future carbon capture installation plans or field carbon intensity decay. Currently, only one emissions factor is used for all fields, which is not accurate.

## Electricity demand 

 - Residential load curves currently assume all use follows the same curve. This is the TIMES 2.0 method. However, it is a problem, because space heating is the key driver of peak load, limiting overall system uptake, so we should represent this load curve separately, allowing more efficient space heating techs to have the correct impact on peak.
 - Residential demand flex and the Tiwai demand flex contract are not currently modelled. This is especially important for residential hot water ripple control.

## Natural gas 
- Kapuni gas is underutilised, presumably due to higher carbon costs. This points to a minor imbalance in the demand sector - in reality, Kapuni natural gas is in high demand. 
 - Not an issue, per se, but LNG outputs are not realistic unless using MIP solution methods (to disable partial LNG port builds). This is only a problem because MIP is much less computationally efficient than standard linear solutions, so this limits our ability to perform quick model runs unless significantly limiting the number of years we solve for. 

## Other supply side 

- Bioenergy feedstock availability and costs are not yet changed between scenarios to represent different possible regulatory environments. 
 - Hydrogen production is currently very crudely modelled, not appropriately calling on electricity demand for electrolysis. 
 - Hydrogen demand side currently limited to transport and a few minor agriculture machines. We need to add more detail on where and how green hydrogen can be used. Likely we should allow all industrial natural gas use to be replaced with hydrogen, assuming onsite electrolysis and subsequent electricity demand, 



