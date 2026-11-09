# Historical model year treatment

Historical model years are those years AFTER the base year (model years) for which we have historical data

At the time of writing this is 2024 and 2025. Partial 2026 data is available sometimes.


## Status and purpose

Working note for a possible **opt-in** model file that represents selected
post-base-year years as historical years. The initial scope is 2024 and 2025;
the model base year remains 2023.

This is not a proposal to turn all standard cases into back-casts. The normal
cases should retain their existing projection inputs. A historical-year case
would be assembled only when a user elects to include the additional model
file, and only for quantities with an approved observation and a clear model
mapping.

For each lock, record the source vintage and status, measurement units,
coverage, transformation to model units, affected regions/processes, VEDA
constraint or input form, and the expected result of a run with and without
the optional include.

## What is currently locked to history

### Industrial demand: Methanex

Methanex is the clearest current historical demand treatment. The industrial
demand-projection code totals annual Gas Industry Company (GIC) consumption
for Methanex Motunui and Waitara Valley, then converts the 2024 and 2025
totals into demand indices relative to 2023. The same indices apply to both
Steady and Shift.

The current implementation then carries the final observed level into 2026
and sets demand to zero after the configured closure year. It is built into
the ordinary industry projection pathway, rather than supplied as a separate
historical-year case include.

### Industrial demand: Urea / Ballance

Urea uses the same generic GIC-index mechanism, with GIC consumption for
Ballance. The configured observed/estimated years are 2024, 2025 and 2026;
the 2026 value is a documented annual estimate where applicable. The last
observed/estimated level is used through the closure year, then Urea demand
is zero afterwards.

This is also embedded in the ordinary projection pathway. It should be
treated as an existing bespoke lock, not evidence that all industrial EEUD
history is locked.

### Historical drivers, not energy-model locks

Population projections prefer historical population observations where they
overlap with projections. This can affect demand drivers, but it is not a
lock on an energy demand, fuel use, technology activity, capacity or supply
quantity in TIMES.

### No other explicit post-2023 demand or supply locks identified

The current code search found no comparable generic mechanism that passes
observed 2024–25 EEUD, biomass-patch, unallocated-electricity, transport,
electricity-generation or fuel-supply values into model constraints. Those
series may be loaded or used in checks, but are not thereby reproduced by a
model run.

## Historical series that currently remain checks or projections

| Area | Current treatment | Implication |
| --- | --- | --- |
| Stationary EEUD through 2025 | Available to alignment/check series; base-year model-facing processing filters to 2023. | 2024–25 observations do not set service demand in the model. |
| Transport EEUD through 2024 | Historical input/check coverage only. | Does not make a 2024 transport model year historical. |
| Industrial/commercial biomass patch | Appended to EEUD; only its 2023 value enters the base-year model. | Post-2023 values are checks unless a separate demand treatment is added. |
| Unallocated onsite-generation electricity patch | Maps to a fixed Other Industry electricity demand in 2023; 2024 is retained in the time series. | The model starts from the 2023 value; it does not use the 2024 observation. |
| Other Industry future demand | The detailed industry check applies the -0.1% annual growth assumption. The model-facing driver allocation currently assigns its commodities to `Constant`. | In the current model, the unallocated electricity commodity is flat after 2023, not historical and not the detailed check projection. |
| Electricity generation and capacity | Prepared as a 2023 base-year calibration. | Updated generation data should be reconciled before considering 2024–25 operational locks. |
| Fuel and resource supply | Modelled using supply assumptions/projections. | No identified mechanism currently locks annual observed supply or production. |

## Candidate optional locks

These are candidates for assessment, not commitments. A historical case
should only include a coherent set of demand and supply constraints; locking
one side alone can produce an artificial balance or infeasibility.

| Area | Possible historical quantity | Main design question |
| --- | --- | --- |
| Methanex and Urea | Annual GIC totals, potentially replacing the embedded bespoke logic in the optional case. | Preserve the chemical/feedstock allocation and define how closure assumptions apply after the locked period. |
| Industry, commercial, residential and agriculture demand | EEUD sector/fuel/end-use values after reconciliation. | Convert energy observations into service-demand constraints without preventing legitimate fuel switching or double counting patch rows. |
| Unallocated onsite electricity | Reconciled annual balance residual. | Decide whether it is a fixed electricity load, a specific onsite-generation/load representation, and whether Other Industry regional allocation remains defensible. |
| Transport | Vehicle stock, activity, fuel consumption and mode totals. | Lock a consistent combination of activity and fuel use; avoid conflicting with technology-efficiency relationships. |
| Electricity | Generation by plant/fuel, capacity, demand and inter-island flows. | Choose whether the historical case is an operational calibration with fixed activity, fixed capacity, or both, and reconcile losses and hydro conditions. |
| Gas and other fuels | Production, imports/exports, storage and large-user consumption. | Ensure supply, conversion and final-use locks reconcile on a common annual balance. |
| Biomass and biofuels | Observed facility consumption, production and feedstock supply. | Establish provenance, avoid overlap with EEUD, and distinguish physical flow from allocation assumptions. |

## Suggested implementation approach

1. Create a documented lock register with one row per quantity/year and an
   approval status. Do not use an observation merely because it is available.
2. Generate a standalone VEDA/TIMES include for the approved 2024–25 locks;
   keep it out of normal cases by default.
3. Prefer annual demand or activity bounds only where the model quantity and
   observational quantity genuinely match. Use tolerances where warranted.
4. Apply linked supply, conversion and demand locks together where a balance
   requires them. Record deliberate residual flexibility.
5. Run three checks: normal case, historical include, and a reconciliation of
   model results against the approved historical register. The normal case
   must be unchanged.

## Open decisions

- Is the historical-year case intended for validation only, or for published
  retrospective scenarios?
- Which years are final enough to lock: 2024 only, or 2024 and provisional
  2025?
- Should the existing Methanex and Urea/Ballance logic move into the optional
  include, or remain standard-case exceptions?
- What tolerance is acceptable for each class of historical quantity?
- Who approves source vintages and reconciliation exceptions?
