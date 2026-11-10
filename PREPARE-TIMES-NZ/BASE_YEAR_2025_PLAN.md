# Plan: extend historical demand data through 2025

## Scope

The model base year remains **2023**. This work extends selected historical
series through 2025 for calibration checks and, where explicitly intended, to
set observed post-base-year industrial demand.

This is not a 2025 base-year conversion. Do not change `StartYear`, base-year
electricity calibration, EBT vintage, transport inputs, or the general
2023-NZD cost basis as part of this work.

## Current priority: 2025 historical-data extract

The immediate deliverable is a **national 2025 data extract**, not a model
change and not a historical-model-year case. It must contain:

1. industrial process heat, by TIMES industrial subsector, process-heat band
   and fuel;
2. agriculture process heat and space heating; and
3. commercial space and water heating.

Regional detail is not required. Build the extract from each sector module's
existing `times_eeud_alignment_timeseries.csv`, filtered to 2025, rather than
recreating EEUD sector, end-use, technology or fuel mappings. These check
outputs retain the full historical series; the corresponding `preprocessing/`
and final demand files intentionally retain only the 2023 model base year.

### Required steps

1. Confirm the completed workflow has refreshed the stage-1 EEUD and GIC
   extracts and the three sector-alignment time-series files through 2025.
2. Extract the requested 2025 end-use rows from the industry, agriculture and
   commercial aligned outputs, retaining source-relevant dimensions and PJ
   units.
3. Combine them into a clearly labelled delivery workbook/CSV. Keep the three
   sector tables separate rather than forcing unlike sector classifications
   into a common subsector scheme.
4. Reconcile each extract to its source alignment file and explicitly check:
   - industrial and commercial biomass-patch additions are included;
   - Aluminium, Methanol and Urea are separate industrial subsectors;
   - Urea feedstock is excluded from industrial *process heat*;
   - the 2025 Methanex and Urea allocations reconcile to
     `chemical_split_calculations.csv`.
5. Supply a short methodology note identifying EEUD/GIC vintages, coverage,
   the heat/end-use selection, PJ units, and that all values are national.

No regional allocator, VEDA-file generation, demand-index recalculation, or
historical-year model lock is required for this deliverable.

The intended updates are:

1. ingest stationary EEUD through calendar year 2025, while retaining the
   available transport EEUD through 2024;
2. ingest GIC data through 2025, and use observed Methanex/Ballance data
   through the historical cut-off; and
3. revise the biomass-demand patch so post-2023 values are historical
   observations rather than implicit forecasts.

### Optional workstream: historical model-year treatment

As a separate, optional enhancement, develop a scenario/model-file mechanism
that can lock selected post-base-year model years (initially 2024 and 2025)
to approved historical observations. This must be opt-in: the standard
projection cases must continue to use their normal demand and supply
projections.

Current treatment is inconsistent: Methanex and Urea/Ballance have bespoke
GIC-index logic, while most updated EEUD, biomass and unallocated-demand
series remain calibration checks only. Before implementation, maintain the
working inventory in `historical model year treatment.md`; define the
observation, model quantity, geographic/technology treatment, constraint
form, case inclusion and validation rule for every proposed lock.

## Current downstream flow

| Input / output | Current use | Effect of extension to 2025 |
| --- | --- | --- |
| Stage-1 `eeud/eeud.csv` | Industry, commercial, residential, agriculture/forestry/fishing and load-curve preparation read the full extract. | Alignment processes create 2025 check series, but their model-facing base-year files filter to 2023. Thus 2024–25 EEUD does **not** directly change TIMES base-year demand. |
| EEUD `times_eeud_alignment_timeseries.csv` checks | Calibration, demand-growth analysis and manual review. | Gains 2025 values; this is the principal purpose of the EEUD update. |
| GIC stage-1 extract | Industry chemical split and Methanex/Urea demand-projection logic read the full extract. | Observed GIC values become Methanex and Urea demand indices for their configured historical/estimated years. |
| Ballance GIC values / Urea | Chemical split within industry EEUD alignment; Ballance is represented as the `Urea` sector. | Observed Ballance GIC values drive Urea demand indices for 2024–25; the documented 2026 estimate is then held through the configured closure year. |
| Biomass patch | Applied to whole EEUD extract before sector alignment. | The 2023 patch contributes to base-year model demand. Post-2023 values appear in checks only; they do not automatically become future TIMES demand. |

The key distinction is historical data versus a model projection: loading
observed 2024–25 values does not itself make the model reproduce them. The
explicit exceptions are the Methanex and Urea GIC projection methods.

## Existing behaviour

### EEUD

`scripts/stage_1_prep_raw_data/extract_eeud.py` reads the configured EEUD
workbook and applies both patches. Downstream sector pipelines filter
model-facing output to `BASE_YEAR = 2023`; industry also writes an unfiltered
time-series alignment check.

- New 2025 EEUD data supports trend checks without changing the model, provided
  the 2023 EEUD rows are unchanged.
- A replacement workbook may revise **2023** values or category labels. That
  *will* flow into base-year demand and can change model results. Compare old
  and new 2023 extracts before accepting it.
- The unallocated-demand patch ends at 2024. Extend it to 2025 with a value,
  zero, or documented non-applicability so its absence is not misread as a
  fall in 2025 checks.

### GIC and industrial demand

Industry alignment uses GIC values for Methanex and Ballance when splitting
natural-gas chemical demand. Its 2025 calculations are retained in
`chemical_split_calculations.csv` and the EEUD time-series check, but the
industry base-year file keeps only 2023.

`stage_3/demand_projections/industry.py` has a specific historical bridge for
Methanex:

- 2023 has index 1;
- `METHANEX_GIC_YEARS = [2024, 2025]` use observed GIC totals;
- the 2025 level is carried into 2026; and
- demand becomes zero after the configured closure year.

Refreshing GIC through 2025 will therefore change Methanex model demand in
2024–26 if observed totals change. That is expected if those years are being
locked to history.

Ballance is the model's **Urea** sector. Its demand path now uses observed GIC
totals for 2024–25, indexed to the 2023 base year. A documented provisional
2026 annual estimate based on partial GIC data is held through 2027, then set
to zero from 2028. 
### Biomass patch

`coded_assumptions/eeud_patches/biomass_demand_patch.csv` contains columns
through 2030. The patch loader retains only years in the EEUD workbook, so the
current EEUD (through 2024) prevents its 2025–30 values entering the EEUD
extract. An EEUD release through 2025 will add its 2025 values to historical
checks.

The patch contains industrial and commercial rows. “Industrial biomass patch”
therefore needs a precise rule:

- replace industrial values through 2025 with sourced historical estimates;
- decide separately whether commercial biomass should also be updated; and
- remove, blank, or clearly segregate 2026+ forecasts, so future EEUD releases
  cannot make them appear to be history.

If future TIMES industrial biomass must reproduce observed 2024–25 patch
values, new demand-projection logic is required. The present model starts
future industry demand from 2023 and applies projection indices.

## Required updates

### 1. EEUD historical series

1. Record the stationary 2025 and transport 2024 source vintages, their
   publication/final status, and any revisions to prior years.
2. Stage 1 now combines `EEUD Stationary Outputs 17-25 QAed.xlsx` (its
   `result` sheet) for non-transport energy and
   `EEUD 2017 - 2024 FINAL 20032026.xlsx` for transport rows. This deliberate
   coverage boundary means there is no 2025 transport EEUD data until an
   equivalent transport extract is supplied.
3. Validate schema and labels against sector/category concordances and
   technology-renaming rules.
4. Extend `unallocated_demand_patch.csv` through 2025 and validate the biomass
   patch's 2025 values.
5. Run extraction and sector alignment. Compare old versus new **2023** totals
   by sector, fuel, and material technology/end-use. Any difference is a
   base-year model change requiring review.
6. Retain 2024–25 sector-aligned series as checks, clearly labelling observed
   EEUD and patched values.

### 2. GIC historical series and Methanex/Urea lock-down

1. Update `data_raw/external_data/gic/ProductionConsumption.xlsx` so
   `Prod_Cons` and `Rep Major Users` contain all 2025 observations.
2. Confirm participant names still match the fixed Methanex and Ballance
   lists; a changed name otherwise falls out of the selected total.
3. Re-run extraction and inspect annual totals for 2023, 2024 and 2025.
   Reconcile units (the code converts GIC TJ to PJ) and account for missing
   months or revisions.
4. Retain `METHANEX_GIC_YEARS = [2024, 2025]` only if these are the approved
   observed lock-down years. Confirm 2026 treatment: it currently carries 2025
   observed demand, then applies the closure.
5. Review Methanex `Steady` and `Shift` indices. They should be identical for
   observed years and equal annual-GIC / 2023-GIC ratios.
6. Treat Ballance as Urea in the historical lock-down. Its GIC-index method
   uses observed 2024–25 values and the documented 2026 estimate, holds that
   level through the configured closure year, then sets demand to zero.

### 3. Biomass patch: history, cut-off and provenance

1. Record for each industrial row/year 2020–25: source, facility coverage,
   fuel basis, annualisation method, units and confidence/estimated status.
2. Replace 2024 and 2025 industrial values with observed or best-available
   historical estimates. Verify the EEUD dimensions exactly match the rows
   being supplemented.
3. Decide 2026+ treatment. Recommended: move forecasts out of the historical
   patch (or leave them blank) and use a separate, explicitly consumed
   projection assumption. This prevents accidental inclusion in later EEUD
   releases.
4. Confirm whether commercial biomass is in scope; if not, retain it but mark
   it unchanged and document its source/cut-off.
5. Compare patched and unpatched EEUD by sector and fuel for 2023–25. This
   exposes patch additions and guards against double counting if EEUD starts
   covering the same biomass uses.

## Downstream checks and expected impacts

| Check | Expected result / why it matters |
| --- | --- |
| `eeud_no_patch.csv` versus `eeud.csv` | Quantifies annual patch additions; confirm 2025 biomass and unallocated adjustments are intentional. |
| Industry `chemical_split_calculations.csv` | Confirms 2023–25 Methanex/Ballance totals, feedstock/direct-use allocation and MBIE non-energy-gas reconciliation remain feasible. |
| Industry `times_eeud_alignment_timeseries.csv` | Provides EEUD-plus-patch history for review; check 2025 category coverage and sector/fuel totals. |
| Industry base-year preprocessing and `baseyear_industry_demand.csv` | Must be equivalent to the prior run if 2023 EEUD and patch values are unchanged. |
| Stage-3 industrial projections | Methanex and Urea should follow their configured observed/estimated GIC indices and carry-forward/closure rules. |
| Final VEDA/TIMES demand files | Apart from intended Methanex and Urea future-demand updates, should not change solely because 2024–25 EEUD, Ballance GIC, or biomass-history values were added. |

If other model files change, trace the difference before accepting it. In
particular, distinguish a revised 2023 EEUD input (a real base-year change)
from a new 2024–25 observation (normally checks only).

## Recommended sequence

1. Archive current stage-1 EEUD/GIC extracts, industry checks, base-year
   industry file and stage-3 projection output.
2. Add and profile updated EEUD and GIC sources; document their vintages.
3. Update unallocated and biomass patches with a clear history/forecast
   boundary.
4. Re-run stage 1 and industry alignment; compare all 2023 values first.
5. Review 2024–25 EEUD, biomass and GIC check series.
6. Review and approve Methanex and Urea indices and their closure rules.
7. Run the full workflow and diff model inputs, accepting only intended
   Methanex/Urea future-demand changes and separately approved 2023 revisions.
8. If the optional historical model-year treatment is approved, prototype it
   as a separate model file/case include, starting with the documented
   Methanex and Urea/Ballance demand series. Validate that it affects only its
   selected historical years and does not alter standard projection cases.

## Decisions still needed

- Which EEUD release and what is the status of its 2025 data (final or
  provisional)?
- Does “industrial biomass patch” exclude commercial rows, or should both be
  historical through 2025?
- Should 2026+ patch values be removed from the historical input and represented
  by an explicit future-demand assumption instead?
- Is the current Methanex rule—observed 2024–25, carry 2025 into 2026, then
  zero—the approved lock-down behaviour?
- Should 2024 and 2025 be optionally modelled as historical years, and which
  demand, supply and operational quantities are sufficiently robust to lock?

## Follow-up to-do

- [ ] **Industrial biomass patch:** confirm that 2024–25 industrial values are
  historical observations, record their source and annualisation basis, and
  remove or segregate 2026+ forecast values from the historical patch.
- [ ] **Unallocated-demand patch:** give 2025 an explicit value, zero, or
  documented non-applicability, so its absence is not misread as a fall in
  demand.
- [ ] **2025 transport EEUD:** obtain and ingest an equivalent transport
  extract when it becomes available; the present combined EEUD intentionally
  has no transport observations for 2025.
- [ ] **Statistical-difference adjustment:** review the current patch and its
  source basis against the updated EEUD and balance data; document whether it
  remains necessary and confirm it does not double count demand.
- [ ] **Coal demand:** replace the current manual treatment with an automated,
  source-driven calculation, then validate its historical totals and
  allocation against the balance data.
- [ ] **Data centres:** reconcile the dedicated EEUD data-centre rows and the
  ANZSIC J deduction against Energy Balance Table electricity consumption
  before changing or removing the current data-centre allocation patch.
- [ ] **Electricity generation:** assess the revised generation data, rerun
  the electricity base-year preparation, and reconcile generation, capacity,
  fuel input and calibration checks before accepting changes to model inputs.
- [ ] **Final reconciliation:** compare old and updated 2023 prepared demand
  by sector, fuel, technology and end use; then diff the final VEDA/TIMES
  demand inputs and accept only explained changes.
- [ ] **Optional historical model-year treatment:** use `historical model year
  treatment.md` to define a generic, opt-in case include for approved 2024–25
  historical locks; do not convert the standard projection pathway into a
  retrospective calibration case.
