# Demand projections

Industrial demand projections are based on energy service demand rather than final fuel demand. For most industrial subsectors, TIMES-NZ applies scenario-specific demand growth rates derived from recent EEUD history, as described in the scenario parameters documentation.

## Methanex projections

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

Year,Index (2023 = 1),Demand (PJ),Basis
2023,1.000000,55.488696,Base year aligned to 2023 GIC demand
2024,0.486131,26.974803,Observed annual GIC demand
2025,0.369498,20.502967,Observed annual GIC demand
2026,0.369498,20.502967,2025 demand carried forward
2027,0.000000,0.000000,Exogenous closure
2030,0.000000,0.000000,Exogenous closure
2050,0.000000,0.000000,Exogenous closure
```

This approach replaces the previous treatment in which Methanol demand could decline endogenously in response to gas market conditions.
