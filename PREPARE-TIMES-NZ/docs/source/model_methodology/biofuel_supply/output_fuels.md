# Output fuels

Bioenergy outputs vary widely in how easily they substitute into existing energy systems.

## Biogas and biomethane

Biogas is produced through the anaerobic digestion of organic waste, a biological process that generates three primary outputs: methane (CH₄), carbon dioxide (CO₂), and digestate. The methane component can be combusted to produce heat or electricity. Captured CO₂ may be utilised in various industrial applications, including horticultural enrichment and food and beverage manufacturing. The digestate serves as a nutrient-rich fertiliser and can substitute for synthetic alternatives. In New Zealand, biogas production is currently concentrated in landfills and wastewater treatment facilities, where it is primarily combusted on-site for electricity generation.

Biomethane can be produced from upgrading biogas by removing CO2 and other impurities. It is chemically identical to fossil gas which is transmitted across the North Island in pipelines. Upgrading biogas to biomethane incurs costs. Note that biogas cannot commercially be upgraded to LPG fuel, which is a mix of propane and butane. In New Zealand there is just one facility producing biomethane and injecting into the gas pipeline network – Ecogas in Reporoa, with a second under development in Christchurch, which is expected to become operational at the end of 2026. 

In a New Zealand context, this means injection into the North Island gas grid or use in industrial boilers and process heat applications at food processors, pulp and paper mills, or dairy plants.

 - **Electricity and heat:** Smaller-scale AD systems can provide combined heat and power (CHP) for rural energy self-sufficiency (e.g. horticultural packhouses or greenhouses).
 - **Vehicle fuel:** Compressed biomethane (bio-CNG) could support fleet decarbonisation, particularly for rural freight and refuse collection vehicles.
 - **Grid integration:** The existing North Island gas network provides a direct pathway for scaling biomethane, while South Island applications would likely be off grid, serving local users or CHP units.

Biomethane is fully interchangeable with fossil natural gas at >97% CH₄. No burner or boiler modifications are required. In TIMES 3.0, we assume all existing natural gas devices in the North Island can also use biomethane, subject to the same delivery costs as natural gas. Biomethane is not a like-for-like substitute for LPG, so we do not assume it can be used directly in existing LPG-fuelled equipment. In the South Island, where distribution infrastructure is limited, biogas is better suited to onsite combined heat and power (CHP). Under this approach, South Island industrial users would rely on onsite anaerobic digestion and use the resulting biogas directly for CHP rather than attempting to replace LPG with biomethane.



## Liquid biofuels 

New Zealand’s liquid biofuel options fall into three broad categories – bioethanol, biodiesel, and advanced “drop-in” biofuels such as biocrude and SAF. Each has different implications for how easily it can substitute into existing industrial or transport systems, the capital and operating costs involved, and the extent of modification required at the demand side.

Biodiesel is the most straightforward substitute for conventional diesel. Its chemical and combustion properties are close enough that it can generally be used in unmodified diesel engines, pipelines, and storage infrastructure. Capital investment requirements are modest by comparison to other biofuel technologies. Because biodiesel integrates easily into current systems, its main cost barrier is feedstock collection rather than infrastructure change.

Advanced drop-in fuels such as SAF and biocrude are also intended for direct substitution into existing systems, but at present they remain limited to pilot and demonstration scale. These fuels are produced from woody biomass using thermochemical methods like pyrolysis or gasification, followed by upgrading through hydrotreating. They can be used in aircraft and heavy-duty engines without blending limits, but the economics are steep. Their advantage is compatibility; their drawback is cost and scale.


### Fuels that require blending or conversion

Bioethanol is less compatible with existing diesel or gasoline systems when used alone. It absorbs water and separates easily from diesel, which causes instability in fuel systems. To overcome this, it is commonly blended with biodiesel, which acts as a co-solvent and increases both the lubricity and cetane number of the mixture. Blended fuels can then be used in existing diesel engines without hardware modification, provided the ethanol proportion remains limited.

A Central Queensland University study tested ternary blends – 10% biodiesel, 10-20% bioethanol, and 70-80% diesel – and found encouraging results. Compared with pure diesel, these blends reduced carbon monoxide by up to 38%, carbon dioxide by up to 6%, and nitrogen oxides by up to 14%, while fuel consumption rose only 2-3%. The blend containing 15% bioethanol (B10E15D75) achieved the lowest total emissions with no measurable loss in efficiency[^diesel_ternary_blends]. For aviation, early adoption of SAF blends between 30% and 50% is expected, scaling toward full substitution once production matures.

Because ethanol production in New Zealand relies mainly on whey and other sugar-rich by-products, feedstock availability is concentrated in the North Island. Capital costs are similar to biodiesel but operating costs are more energy-intensive because of distillation and drying requirements.

### Overall perspective

In the near term, biodiesel offers the most practical drop-in pathway for reducing fossil-diesel use. Bioethanol blends provide additional emissions reductions where blending infrastructure exists, but they depend on co-solvents or minor fuel-handling changes. Advanced drop-ins like SAF promise seamless substitution in the long run but will require major capital investment and scaling before they become cost competitive.


[^diesel_ternary_blends]: Ayazi, M., Rasul, M. G., Khan, M. M. K., & Hassan, N. M. (2023). Experimental investigation of fuel consumption and emissions of diesel engine fueled with ternary fuel blends of diesel, biodiesel and bioethanol. Energy Reports, 9, 470-475.

## Emission factors 

Across a range of organic feedstocks, the full lifecycle emissions of biomethane which covers production, upgrading, distribution, and end-use averages around 17 kgCO₂e per GJ. This represents roughly a 70% reduction compared with conventional fossil gas, which has an emissions intensity of about 57 kgCO₂e per GJ including transmission and combustion. Most of the remaining emissions from biomethane arise from methane slip during biogas generation and upgrading. Minimising these fugitive emissions is therefore the most critical factor in improving the climate performance of biogas pathways.

For biomethane and other biofuels derived from organic waste streams that would otherwise decompose (e.g. landfill-bound food waste, wastewater sludge, industrial organics), the net climate benefit is even greater. In these cases, capturing the biogenic methane and converting it into renewable fuel avoids substantial methane emissions that would have occurred under business-as-usual conditions. As a result, the net lifecycle emissions can be negative, depending on system boundaries and avoided-emissions accounting. 


```{csv-table} Summary of GHG Emissions Intensity[^gic_gtp_biogas]
:name: tab_bio_efs
:header-rows: 1 

Gas,Emissions intensity (kgCO2e/GJ)
Biomethane from AD,19
Biomethane from landfill gas,10
Natural gas,57
```

In the current TIMES-NZ model, biogas and biomethane pathways are modelled with zero combustion and production emissions, meaning no explicit CO2, CH4, or fugitive emissions are assigned to either the combustion technologies or the biogas production.


[^gic_gtp_biogas]: Gas Industry Co | [Gas Transition Plan - Biogas Research Report] (https://www.gasindustry.co.nz/assets/CoverDocument/Gas-Transition-Plan-Biogas-Research-Report-February-2023.pdf)