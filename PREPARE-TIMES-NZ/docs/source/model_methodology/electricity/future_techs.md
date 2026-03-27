# Future technologies

The base of future technologies made available to the model aligns with the MBIE generation stack used for EDGS 2024. This lists many future consented, planned or generic plants, and includes detailed estimates of costs (investment, connection, and maintenance) as well as other important parameters like fuel efficiency, relevant substation, or earliest possible commissioning year.

For the Traditional scenario, we use the MBIE Reference generation stack. For the Transformation scenario, we use the Innovation generation stack, which contains more potential new generation plants at lower capital costs.

We make the following adjustments and additions to the MBIE generation stack:
- Future costs in the MBIE generation stack[^mbie_edgs] are assumed to be static. We allow these to decline over time, based on the United States’ National Renewable Energy Laboratory (NREL)[^nrel] assumptions of future cost declines for solar, wind, and geothermal technologies.
- We add data for distributed solar generation and offshore wind plant types.
- Utility solar plants in the MBIE generation stack with tracking capabilities are identified and categorised as such. Tracking solar has higher costs, but also better capacity factors and different availability curves.

[^mbie_edgs]: MBIE EDGS: <https://www.mbie.govt.nz/building-and-energy/energy-and-natural-resources/energy-statistics-and-modelling/energy-modelling/electricity-demand-and-generation-scenarios>
[^nrel]: NREL: <https://www.nrel.gov/>. This documentation was written before NREL was renamed to the *National Laboratory of the Rockies (NLR)*.

## Learning curves 

Data from the NREL ATB database[^nrel_atb] was used to produce learning curves for certain solar, wind, and geothermal technologies, where the costs of technologies decrease over time assuming technological advancement. The cost data from NREL is projected from 2022 to 2050 across a range of scenarios and technology types. 

NREL projections consider three different scenarios: Conservative, Moderate, and Advanced. The NREL scenarios are defined as follows[^nrel_atb_definitions]:

 - Conservative: Small changes in technology with decreases in public and private research and development investments.
 - Moderate: Innovation in the market is more widespread with current levels of investment in public and private research and development.
 - Advanced: Innovation in the market is widespread with an increase of investment in public and private research and development.

For the Traditional scenario we apply the Moderate projections, and for Transformation we use Advanced.

Learning curves were applied to reduce the future capital cost (CAPEX) and fixed operating and maintenance costs (FOM) to plants that met the following criteria: 

 - Only solar, wind, and geothermal plants have had reduced future costs applied.
 - The plant status must be less advanced than “Fully Consented” or “Under Construction”.
 - Plants must have an earliest or fixed commissioning year no earlier than 2030, or no information on commissioning year. 

All remaining plants have their CAPEX and FOM remain fixed across the model horizon. The NREL technology categories used for each plant type are as follows: 



```{list-table} Technology types and NREL category matching
:header-rows: 1
:name: tab-nrel_mapping
* - Technology Type
  - NREL technology used
* - Utility solar (fixed)
  - Tracking PV[^tracking_pv]
* - Utility solar (tracking)
  - Tracking PV
* - Distributed solar
  - Rooftop PV
* - Onshore wind
  - Wind Turbine Technology 1
* - Offshore wind (fixed)
  - Offshore Wind Fixed-Bottom
* - Offshore wind (floating)
  - Offshore Wind Floating
* - Geothermal
  - Geothermal - Hydro / Flash
```
To apply the learning curves, the percentage indices of the NREL CAPEX and FOM data was found. The percentage indices were found using $PI_i=(Expense_i)/(Expense_{2023})$, where $PI$ is the percentage index and $i$  is the year.

The base year was set to 2023 to match the base year of the MBIE data. For the forecasted CAPEX of the future technology, the percentage indices were applied to the capital cost, which does not include the cost of connection. The cost of connection was divided by the capacity of the plant and then added as a constant to the projected CAPEX. For the FOMs the percentage indices were able to be applied without extra addition of other costs. 

[^tracking_pv]: NREL does not provide learning curves for fixed solar panels. We assume the cost reductions are not specifically driven by the tracking technology and so apply the learning curves to both fixed and tracking technology types.
[^nrel_atb]: Electricity Data | NREL: <https://atb.nrel.gov/electricity/2024/data>
[^nrel_atb_definitions]: Electricity Definitions | NREL: <https://atb.nrel.gov/electricity/2024/definitions>


## Offshore wind
Offshore wind costs use the NREL data, converted to 2023 NZD.  Note that NREL CAPEX costs for offshore wind[^nrel_atb_offshore] include the connection costs. The distances to land and water depth are different for the different classes of offshore wind technology. 

The potential future capacity of offshore wind was estimated in PWC’s National Impacts Report[^nir] on the offshore wind industry in New Zealand. This report lists offshore wind opportunities that were in early development at the time of publication. The proposed wind farms and sizes for the selected regions are added to TIMES-NZ, using NREL cost data. While some of these offshore wind opportunities may never go ahead, these act as an upper limit on offshore wind potential in the model. 

The earliest commissioning year for offshore wind farms was set to 2035, as all potential developers project at least a 10-year project implementation time. 

[^nrel_atb_offshore]: Offshore wind | NREL: <https://atb.nrel.gov/electricity/2023/offshore_wind>

[^nir]: National Impacts Report: New Zealand Offshore Wind Industry | PWC: <https://www.pwc.co.nz/pdfs/2024/national-impacts-report-new-zealand-offshore-wind-industry-mar-2024.pdf>

## Distributed rooftop solar

We do not model distributed solar uptake in TIMES, and instead provide exogenous assumptions on rooftop solar uptake. 

This is because TIMES uses a system cost perspective when selecting optimal technologies. This often means that it will not invest in distributed solar, preferring the economies of scale of utility-scale solar. This is true even when considering the efficiency and grid maintenance benefits of off-grid generation[^distribution_note]. 

Because it would not be realistic to assume no distributed solar installations, we instead use external forecasts of distributed solar installation from MBIE's EDGS scenarios[^edgs_solar]. We use the Reference projections for our Traditional scenario, and the Innovation projections for Transformation. This means that TIMES-NZ distributed solar uptake rates are not the product of any other model properties; they are hardcoded assumptions. 


[^edgs_solar]: MBIE | [EDGS 2024 Assumptions](https://www.mbie.govt.nz/building-and-energy/energy-and-natural-resources/energy-statistics-and-modelling/energy-modelling/electricity-demand-and-generation-scenarios)
[^distribution_note]: While distributed solar is often not selected in a system cost approach, this is not a universal rule for distributed assets. For example, we note that the model often chooses to build distributed batteries, despite the higher per-unit costs compared to grid-scale batteries, because of the benefits of reducing grid load during peak demand periods. For this reason, we still allow the model to choose the efficient level of distributed battery build, rather than using a fixed assumption. 


## Diesel peakers 

We allow the model to also build diesel peakers, as this could prove a useful option based on future oil import costs and gas availability. Diesel OCGT peakers do not exist in the MBIE generation stack, so have set their parameters equivalent to existing natural gas OCGT peakers. However, the heat rates were adjusted to 11,000 GJ/GWh, implying a fuel efficiency of 32.7%, which is in line with existing assumptions on the operation of the Whirinaki diesel plant. 


## New fuels in existing assets 

We add additional fuel options to some existing plants to incorporate potential future renewable fuels. All gas-fired electricity generation can also use biomethane directly.  Similarly, the Huntly Rankines have the option to use black pellets, if these are produced via torrefaction facility. See documentation on biofuel assumptions for more details on the production and distribution of these fuels. 
