# Demand projections

## Industrial demand projections 

Industrial demand projections are based on energy service demand rather than final fuel demand. For most industrial subsectors, TIMES-NZ applies scenario-specific demand growth assumptions derived from recent EEUD history.

For the `Steady` scenario, we extrapolate the compound annual average growth rates in energy demand over the last 6 years of EEUD data. For the `Shift` scenario, selected sectors switch to alternative growth assumptions to represent a different economic structure over time. A short transition period is applied when building the `Shift` indices to avoid unrealistic step changes.

Some sectors use custom treatments rather than a simple EEUD-based growth rate:

- `Dairy` demand is mapped to the same projection used for `Dairy Cattle Farming` in the agriculture module, which tracks the ERP2 `Total dairy cattle` series[^erp2_results].
- `Iron & Steel` demand is further adjusted through the Electric Arc Furnace (EAF) pathway.
- `Methanol` uses an exogenous Methanex demand path based on observed GIC demand.
- `Urea` uses an exogenous Ballance demand path based on observed GIC demand.
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
Urea,See exogenous Ballance pathway below,Same as Steady
Wood Products,-1.8%,1.8%
Pulp and Paper,-2.0%,Same as Steady
New industries,No new industries,50 GWh of electricity demand growth per annum
```

## Specific sectors

### Methanol 

Methanol demand is treated separately from the standard industrial growth-rate method. The base-year Methanol demand in TIMES-NZ is calibrated to 2023 Methanex gas demand using Gas Industry Company (GIC) production and consumption data for large industrial users[^gic_production_consumption], together with the base-year feedstock split described in the historic demand methodology.

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

Urea demand is treated as the Ballance Kapuni site's demand. Its 2023 base-year demand is calibrated to GIC production and consumption data for large industrial users[^gic_production_consumption]. Annual Ballance GIC demand is used for 2024 and 2025, expressed as an index relative to the 2023 total. For 2026, the model uses a provisional 6.25 PJ annual estimate derived from incomplete GIC data available to 3 November 2026, annualised using the matching 2025 period. This estimate is carried through 2027, and demand is set to zero from 2028 onward. The provisional estimate must be replaced with the final annual GIC total when available. This exogenous path is applied in both the `Steady` and `Shift` scenarios; the previous price-responsive closure process is not used.

```{csv-table} Exogenous Ballance demand projections
:name: tab_ind_ballance_exogenous
:header-rows: 1

Year,Demand (PJ),Basis
2023,6.67,Base year aligned to 2023 GIC demand
2024,6.31,Observed annual GIC demand
2025,7.22,Observed annual GIC demand
2026,6.25,Provisional annual estimate from partial GIC data to 3 November 2026
2027,6.25,2026 provisional estimate carried forward
2028 and onwards,0,Assumed closure
```

[^erp2_results]: MPI | New Zealand's second emissions reduction plan 2026-30: [Technical Annex](https://environment.govt.nz/publications/second-emissions-reduction-plan-technical-annex/) and [Detailed Results (.xlsx)](https://view.officeapps.live.com/op/view.aspx?src=https%3A%2F%2Fenvironment.govt.nz%2Fassets%2Fpublications%2Fclimate-change%2FERP2%2FDetailed-results-for-ERP2-projection-scenarios.xlsx&wdOrigin=BROWSELINK)
[^gic_production_consumption]: Gas Industry Company | [Production & consumption](https://www.gasindustry.co.nz/data/resources/gas-production-and-consumption/)
