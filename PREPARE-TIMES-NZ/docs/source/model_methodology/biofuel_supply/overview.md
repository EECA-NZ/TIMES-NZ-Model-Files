# Overview


TIMES-NZ demand sectors (e.g. industrial, residential, transport) and transformation sectors (e.g. electricity generation) determine fuel use and end-use efficiencies. Those parameters, and any demand-side retrofit costs, are specified in their respective assumptions documents. The purpose of this document is to ensure the TIMES-NZ bioenergy module reflects the latest information on feedstock potential, costs, and technology readiness across New Zealand’s bioenergy sector. The supply module clarifies:

1)	Quantities of available bioenergy feedstocks and/or fuels by future year.
2)	Supply/production costs and, where relevant, delivery costs to transformation or end use nodes.
3)	Supply-side emissions (non-combustion) associated with production, processing, and logistics, excluding combustion emissions, which are handled on the demand side per TIMES convention.

Domestic producing commodities that might serve as feedstocks for biofuel are expected to be material to New Zealand’s energy transition. This module covers supply availability and cost projections for all relevant bioenergy fuels, including:

 - Potential feedstocks. This includes delivery costs to specific sectors (where relevant)
    - Domestic wood waste/residue and wood logs 
    - Agricultural waste (straw/stover, fruit/vegetable culls) 
    - Municipal waste
    - Animal manure
    - Waste oils and tallow
 - Emission factors associated with the production of bioenergy for each feedstock.

The diverse range of biogas feedstocks available in New Zealand demonstrates that expanding the production of biogas and biomethane will require utilising all potential feedstock types, including livestock manure, source-segregated food waste, municipal and industrial waste, waste oil and tallow and crop residues. Currently, New Zealand generates biogas primarily from municipal wastewater treatment plant (WWTP) sludge, landfill gas recovery, and industrial wastewater. However, livestock manure, crop residues, and source-segregated organic waste – feedstocks not yet widely used – could collectively yield about 13 PJ of additional biogas potential.

Agriculture, one of New Zealand’s largest sectors, could play a pivotal role in scaling up renewable gas production. Although agricultural feedstocks are available in large quantities, challenges remain around the logistics of collection and transport. Nonetheless, the regional concentration of agricultural land offers opportunities for efficient systems. For instance, Canterbury holds roughly 70 percent of the nation’s crop residue, while Waikato is home to about 33 percent of New Zealand’s dairy herds (Dairy NZ, 2018). 

Industrial wastewater is generally produced at scales that make on-site reuse feasible, with anaerobic digestion often integrated into existing treatment processes. In particular, the dairy and meat processing sectors, which generate wastewater with high biological loadings, are well suited to biogas production. Municipal organic waste also represents a significant opportunity, however, to fully realise this potential, New Zealand will need to establish a standardised national system for organic waste collection to support consistent and scalable biogas production.

## Scenario adjustments 

Work in progress release note: The text below describes the scenario variations which we are working to implement. In the released setup, `Traditional` uses the base biofuel supply assumptions, while `Transformation` uses the higher bioenergy supply assumptions represented by `AdditionalBioenergySupply`.

TIMES-NZ 3.0 includes two bioenergy supply scenarios designed to test how future policy and investment settings could affect the scale and cost of domestic renewable fuel production.

Bioenergy remains one of the key uncertainties identified by stakeholders, particularly regarding how waste and residue regulations might expand feedstock availability and reduce supply costs over time.

In the **Traditional** scenario, current regulatory and investment conditions are assumed to persist. Feedstock recovery and processing capacity remain limited to resources that are already accessible under today’s settings. Collection and delivery costs are assumed to broadly reflect present-day estimates for accessible forestry and agricultural residues. Limited recovery of additional waste streams means resource availability grows only marginally to 2050. Imports of bio-based fuels remain available to supplement domestic production where cost-effective.

In the **Transformation** scenario, new and strengthened waste and residue management regulations – for example, those incentivising recovery of organic waste or forestry residues – are assumed to improve feedstock access and reduce supply costs. Improved collection systems and regional aggregation hubs also play a role, particularly in regions with high resource density such as the central North Island and Canterbury. Increased availability supports moderate expansion of biogas, biomass combustion, and biodiesel capacity.
