These files are designed to consistently assign Tech_TIMES and Fuel_TIMES to our generation techs 

this is done differently for base year techs, which have more complex combinations of fuel and tech input
(ie we want to distinguish the Rankines, or the difference between a Gas or Diesel Peaker)

the output is the same: Tech_TIMES is used for defining every process name using the same technology consistently

Which is good for mapping to wildcards but also just knowing what's going on, and keeping the output processing files clearer 


Fuel_TIMES is used to define the input commodity so needs to align with selected TIMES commodities that we assume have already been declared  


This standard Tech/Fuel approach should be used if we want to add anything else! 