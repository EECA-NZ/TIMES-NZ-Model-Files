# Service demand flexibility

TIMES models allow energy service demand to be shifted between different times of day. Within the model, these technologies are represented in a similar way to energy storage technologies: an energy service (for example, residential water heating or space heating) can be produced in one timeslice, stored, and consumed in a later timeslice. This enables the model to represent demand-side flexibility while accounting for storage losses and any additional energy required to provide the same level of service.

## Applied technologies

Flexibility provided by dedicated electricity storage technologies such as batteries or hydrogen is represented elsewhere in TIMES-NZ through separate technologies and processes.

TIMES-NZ currently represents residential service demand flexibility through three technologies:

1. Ripple-controlled hot water
2. Smart hot water cylinder controllers
3. Smart heat pump controllers

Each technology represents a different method of shifting electricity demand without materially changing the level of energy service provided to households.

### Hot water flexibility

Electric hot water cylinders inherently provide thermal storage. Heating can therefore be deferred during periods of high electricity demand, with the cylinder reheated later as stored hot water is depleted.

Both ripple control and smart hot water controllers are represented as demand-shifting technologies. Electricity demand reduced in one timeslice must be recovered in subsequent timeslices to restore the stored thermal energy.

Traditional ripple control operates using broadcast signals that control large groups of cylinders simultaneously. Smart hot water controllers provide more targeted control of individual cylinders, allowing heating to be delayed only when sufficient stored hot water is available and reducing unnecessary reheating.

TIMES-NZ does not explicitly represent these operational differences. Instead, both technologies use the same demand-shifting formulation, with smart controllers assumed to incur lower additional energy losses reflecting more efficient operation.

### Space heating flexibility

Buildings also provide a limited amount of thermal storage through their thermal mass. Smart heat pump controllers can temporarily reduce or defer electricity consumption by allowing indoor temperatures to drift within acceptable comfort limits before restoring the desired temperature later.

This flexibility is represented using the same demand-shifting approach as hot water, although the underlying storage mechanism is different. Rather than storing heat in a water cylinder, thermal energy is stored within the building envelope and indoor air.

The model assumes that temporarily reducing heating results in a small increase in subsequent electricity consumption as indoor temperatures are restored. Compared with hot water cylinders, these additional losses are assumed to be relatively small because heat pumps can selectively adjust operation while maintaining user comfort.

## Technology coverage

Residential demand flexibility is constrained by the proportion of households equipped with suitable control technologies.

EECA estimated that just over half of New Zealand electricity consumers had ripple-controlled hot water in 2020.[^eeca_ripple] Accordingly, TIMES-NZ assumes that approximately 50% of existing electric hot water cylinders are equipped with ripple control in the base year. This share gradually declines over time as legacy ripple systems are replaced by smarter digital control technologies.

Smart hot water control is assumed to increase from 5% of households in 2023 to 10% by 2050 in the Steady scenario and 20% in the Shift scenario.

Smart heat pump controllers are assumed to become increasingly common as residential heat pump ownership continues to increase and demand-response capability becomes a standard feature of heating systems. Coverage is assumed to increase from 0% in 2023 to 20% by 2050 in the Steady scenario and 60% in the Shift scenario.

Coverage represents the maximum proportion of residential service demand that is eligible for temporal shifting rather than the proportion actively shifted in every period.

## Parameter summary

```{csv-table}
:header-rows: 1
:name: tab_res_df_params

Technology,Load cap (2023),Load cap (2050 Steady),Load cap (2050 Shift),Additional energy loss
Ripple control,50%,40%,40%,6%
Smart hot water control,5%,10%,20%,2%
Smart heat pump control,0%,20%,60%,2%
```

Additional energy losses are modelling assumptions intended to represent the imperfect recovery of deferred heating.

[^eeca_ripple]: EECA (2020), *Ripple Control of Hot Water in New Zealand*. https://www.eeca.govt.nz/assets/EECA-Resources/Research-papers-guides/Ripple-Control-of-Hot-Water-in-New-Zealand.pdf


## Load caps: exogenous coverage

The load cap represents the total share of the underlying technology (water cylinders or heat pumps) that can utilise demand flexibility. Due to the efficiency losses associated with this process, the model will only choose to dispatch flex during periods that are advantageous for the system. 

The load cap, or demand flex coverage, is prescribed exogenously rather than determined through model optimisation. Demand flexibility technologies have relatively low capital costs compared with the value they provide to the electricity system, meaning that an unconstrained least-cost model would generally deploy them to their maximum extent. Prescribing maximum coverage provides a simple representation of practical limitations such as legacy infrastructure, customer participation, retailer offerings, equipment compatibility and rollout rates, while still allowing the model to optimise when available flexibility is used.

The assumed coverage trajectories and energy losses are modelling assumptions rather than forecasts. In particular, the additional energy losses represent the imperfect recovery of deferred heating and are intended to distinguish the relatively coarse operation of traditional ripple control from the more targeted operation of modern smart controllers. Future model versions may refine these assumptions as additional evidence becomes available.
