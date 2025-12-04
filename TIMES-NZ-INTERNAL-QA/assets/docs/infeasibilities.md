This page is only intended for TIMES-NZ developers and modellers. The results in here are used for model calibration. 

### Description

This section covers all infeasibilities found in the TIMES-NZ optimisation process. 

Effectively, the figures here reflect commodity demand or energy use that the model could not provide through any means. 

If the model is calibrated correctly, this page will be blank. Infeasible commodities reflect a system out of balance.

Note that the model will produce infeasible ENERGY first. This means that the system could produce the required service demand, but to do so it needed to create "fake" energy first. In the current model run, this often means natural gas, but incorrect specifications could lead to a failure to produce any energy type theoretically. 

If even "fake" energy cannot meet all demand, the model will also produce fake commodities. These imply that some service demand could not be met with the existing demand devices. For example, infeasible space heating residential demand would imply that not only are there no heaters, it is also impossible for the model to invest in more. This is not a cost issue, but points to incorrect specifications or potentially misaligned activity bounds in the model specification.


### Unrealistic results 


Any use of infeasible commodties for demand or energy in a model run will significantly imbalance the system costs in an unrealistic way. Take great care interpreting results while there are any infeasible demand or energy commodities.