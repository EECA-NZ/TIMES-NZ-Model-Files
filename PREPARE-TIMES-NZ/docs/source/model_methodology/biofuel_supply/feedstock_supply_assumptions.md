# Feedstock supply assumptions

This page summarises the TIMES-NZ feedstock supply assumptions used for biofuel and bioenergy supply limits.

## Scenario summary

```{list-table} TIMES feedstock supply assumptions by scenario
:name: tab_bio_feedstock_supply_scenarios
:header-rows: 1

* - Scenario
  - Feedstock supply assumption
  - TIMES implementation
* - `Steady`
  - Uses the baseyear biofuel supply assumptions.
  - Variable feedstocks use Scion’s 2024–2053 regional biomass projections with `Recoverability factor 2 (% of gross)`. Constant supply overrides are applied for municipal waste, animal manure, waste oil, and tallow waste.
* - `Shift`
  - Uses the higher bioenergy supply assumptions represented by `AdditionalBioenergySupply`.
  - Variable feedstocks use `Recoverability factor 1 (% of gross)`. Municipal waste and animal manure constant supply assumptions are multiplied by four. Waste oil and tallow waste assumptions are unchanged. The additional scenario applies from 2026 onward.
```

## Feedstocks covered

The supply assumptions above apply across the feedstock processes used in the biofuel supply module:

- Woody residues and wood supply streams
- Agricultural residues
- Municipal wood waste and municipal organic waste
- Animal manure
- Waste oil
- Tallow waste

## Detailed assumptions

```{list-table} Detailed TIMES feedstock supply assumptions
:name: tab_bio_feedstock_supply_detail
:header-rows: 1

* - Feedstock group
  - `Steady`
  - `Shift`
* - Woody residues, agricultural residues, and municipal wood waste
  - Derived from Scion’s 2024–2053 regional biomass projections and scaled using `Recoverability factor 2 (% of gross)`.
  - Derived from the same Scion’s 2024–2053 regional biomass projections and scaled using `Recoverability factor 1 (% of gross)`.
* - Municipal organic waste (`MINMNCWST01`)
  - Fixed at 5.035 PJ/year, split 77% North Island and 23% South Island.
  - Fixed at 20.14 PJ/year, split 77% North Island and 23% South Island.
* - Animal manure (`MINANMMNR00`)
  - Fixed at 7.56 PJ/year, split 56% North Island and 44% South Island.
  - Fixed at 30.24 PJ/year, split 56% North Island and 44% South Island.
* - Waste oil (`MINOILWST00`)
  - Fixed from 2026 at 0.234 PJ/year, split 77% North Island and 23% South Island.
  - Unchanged from `Steady`.
* - Tallow waste (`MINOILWST01`)
  - Fixed from 2026 at 6.240 PJ/year, with all supply in the South Island.
  - Unchanged from `Steady`.
```

