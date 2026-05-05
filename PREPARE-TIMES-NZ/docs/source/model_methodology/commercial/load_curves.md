# Load curves


The commercial sector load curves currently used are from the TIMES-NZ 2.0 model. These were developed using the EECA energy audit reports as the primary source. Because the commercial subsectors are defined at a relatively broad level, each subsector’s load curve was constructed in a structured, multi-step process. Representative buildings were selected from audit data to capture typical demand behaviour for each subsector.

 - Education: high schools and universities
 - Healthcare: several hospitals
 - Office blocks: several large office buildings, some smaller government buildings, and EECA office building load curve research by ESP Consulting
 - WSR: multiple warehouses, supermarkets, retail stores, shopping malls
 - Other: matched to the WSR load curves, due to the broadness and uncertainty of sector


Each representative building had an hourly or sub-hourly electricity demand profile from audits. These raw profiles were grouped into a time-slice structure reflecting weekday/weekend and day/night/peak periods and expressed as a share of daily demand. These daily shares were then mapped onto the annual fraction of each time slice (YRFR) to scale the daily load shares into annual fractions for each building. The building-level profiles were averaged together, with weights reflecting each end-user’s share of energy use within the subsector (for example, retail contributes more to WSR demand than warehouses or supermarkets). The subsector commodity fraction[^com_fr] values were finally normalised so that all slices sum to 1.0, ensuring they represent a complete distribution of annual demand. In most commercial subsectors, all end-use technologies (computers, lights, heating/cooling) were assumed to follow the same subsector load curve, since they typically operate together during business hours. An exception was made for space heating and cooling in Healthcare and Other sectors, where seasonal adjustments were applied to capture climate-driven variations in heating and cooling demand.

[^com_fr]: Commodity fractions are represented in the model through the variable `COM_FR`.
