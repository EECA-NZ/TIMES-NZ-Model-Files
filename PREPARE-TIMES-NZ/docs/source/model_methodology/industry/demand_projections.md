# Demand projections

## Industrial demand projections 

Industrial demand projections are based on energy service demand rather than final fuel demand. For most industrial subsectors, TIMES-NZ applies scenario-specific demand growth assumptions derived from recent EEUD history.

For the `Steady` scenario, we extrapolate the compound annual average growth rates in energy demand over the last 6 years of EEUD data. For the `Shift` scenario, selected sectors switch to alternative growth assumptions to represent a different economic structure over time. A short transition period is applied when building the `Shift` indices to avoid unrealistic step changes.

Some sectors use custom treatments rather than a simple EEUD-based growth rate:

- `Dairy` demand is mapped to the same projection used for `Dairy Cattle Farming` in the agriculture module, which tracks the ERP2 `Total dairy cattle` series[^erp2_results].
- `Iron & Steel` demand is further adjusted through the Electric Arc Furnace (EAF) pathway.
- `Methanol` uses an exogenous Methanex demand path based on observed GIC demand.
- `Urea` is held flat in the demand projections, but may still reduce endogenously in the model if gas becomes sufficiently scarce and expensive.
- `New industries` are represented as exogenous electricity demand growth rather than standard energy service demand.

```{csv-table} Industrial demand projection assumptions
:name: tab_ind_demand_projection_assumptions
:header-rows: 1

Subsector,Steady,Shift
Aluminium,0%,Same as Steady
Construction,1.9%,Same as Steady
Dairy,"Tracks `Dairy Cattle Farming` demand (`Baseline high` / `Total dairy cattle` in ERP2)","Tracks `Dairy Cattle Farming` demand (`Baseline low` / `Total dairy cattle` in ERP2)"
Iron & Steel,EAF operational in 2026,Second EAF operational in 2036
Meat,0.7%,-0.7%
Methanol,See exogenous Methanex pathway below,Same as Steady
Non-Metallic Mineral Product Manufacturing,0%,-1.0%
Mining,1.2%,0%
Other,-0.1%,Same as Steady
Food and Beverage,-1.7%,1.7%
Chemicals (excl. Urea and Methanol),0%,Same as Steady
Urea,May reduce endogenously,Same as Steady
Wood Products,-1.8%,1.8%
Pulp and Paper,-2.0%,Same as Steady
New industries,No new industries,50 GWh of electricity demand growth per annum
```

## Specific sectors

### Methanol 

Methanol demand is treated separately from the standard industrial growth-rate method. The base-year Methanol demand in TIMES-NZ is calibrated to 2023 Methanex gas demand using Gas Industry Company (GIC) large-user data together with the base-year feedstock split described in the historic demand methodology.

For future years, we apply an exogenous projection for Methanex demand using the following method:

1. Annual Methanex gas demand is taken from GIC data for 2024 and 2025.
2. Demand indices are calculated relative to the 2023 base year.
3. The 2025 level is carried forward into 2026.
4. Demand is set to zero from 2027 onward.

This exogenous path is applied in both the `Steady` and `Shift` scenarios.

```{csv-table} Exogenous Methanex demand projections
:name: tab_ind_methanex_exogenous
:header-rows: 1

Year,Demand (PJ),Basis
2023,55.49,Base year aligned to 2023 GIC demand
2024,26.97,Observed annual GIC demand
2025,20.50,Observed annual GIC demand
2026,20.50,2025 demand carried forward
2027 and onwards,0,Assumed closure
```

It is alternatively possible to allow Methanex to close endogenously, based on the model's marginal cost of natural gas and an assumed cut-off point. This method is not currently implemented.

### Urea 

Urea demand is treated differently from most other industrial subsectors. Rather than applying a declining exogenous demand path, TIMES-NZ keeps the demand projection flat and allows production at the Ballance Kapuni site to reduce endogenously if natural gas becomes too scarce or expensive.

This is implemented using a marginal price of 18 NZD/GJ to represent the potential value of lost load for Urea production[^gas_voll]. If the internal marginal price of natural gas exceeds this level, the model can reduce Urea production rather than continue to consume gas at a higher cost.

This means the `Urea` sector is not assigned an exogenous closure year in the demand projections. Instead, closure or partial reduction can emerge from modelled gas market conditions.

[^gas_voll]: This is the assumed price at which this business may exit the market if alternative feedstocks cannot be sourced. TIMES shadow prices reflect either the cost of production or, if demand exceeds supply, the marginal cost of reducing gas demand elsewhere. TIMES-NZ makes no effort to estimate the cost pressures faced by individual businesses, so this value is necessarily a rough estimate.
[^erp2_results]: MPI | New Zealand's second emissions reduction plan 2026-30: [Technical Annex](https://environment.govt.nz/publications/second-emissions-reduction-plan-technical-annex/) and [Detailed Results (.xlsx)](https://view.officeapps.live.com/op/view.aspx?src=https%3A%2F%2Fenvironment.govt.nz%2Fassets%2Fpublications%2Fclimate-change%2FERP2%2FDetailed-results-for-ERP2-projection-scenarios.xlsx&wdOrigin=BROWSELINK)
