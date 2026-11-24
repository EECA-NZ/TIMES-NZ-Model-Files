# SOLVE summary migration

Implemented 24 November 2026 as step 3 of the [QA reporting plan](reporting-plan.md).
This records the current implementation, not a fixed catalogue for future summaries.

## Ownership and outputs

`solve_times_nz.reporting.build_summaries()` accepts already-loaded result and
metadata dataframes. It produces named per-scenario tables; file reading and
writing remain in post-processing. `reporting_flows` contains the battery/flex
timeslice calculations. Neither module imports QA or chart-rendering libraries.
Summaries are CSVs; raw and labelled result datasets remain Parquets. Summary
names and subject folders have not yet been consolidated.

| Existing capability | Prepared summary tables |
| --- | --- |
| QA demo demand, generation, gas, road fuels, biomass and emissions | `qa_*`, including required totals and `qa_objective` |
| Annual generation and thermal fuel use | `elec_gen_*`, `thermal_generation_fuel_use` |
| Demand by sector, fuel, island and industrial profile | Existing publication filename stems, plus `fuel_use_by_island_and_sector` |
| Emissions totals and publication sector groups | `emissions_line`, `emissions_sector_facet` |
| Gas/biomass primary supply | Existing `primary_energy_*` publication filename stems, plus `primary_energy_by_fuel` |
| Battery capacity and road fleets | `battery_capacity`, `transport_*_capacity` |
| Renewable electricity and TFEC indicators | Decimal `renewable_*_share` tables in `Share` units; legacy `indicator_ren_*` exports in percent |
| Battery and demand-flex timeslices | GW/GWh tables for the existing 2035 and 2050 selections, including signed flows, labels and completed timeslices |
| Four existing technology-sensitivity CSVs | Values supplied by the same prepared demand/emissions series for the selected scenario IDs; no duplicate sensitivity calculation |

Summary generation normalizes annual years, validates grouping classifications
and units, and completes absent annual rows within each summary's observed
categories and model years. Existing nulls are not converted into zeroes. Empty
summary selections produce no dataset. QA will not perform category completion.

The publication views retain archived fuel groupings. Industrial publication
profiles explicitly omit fuel oil and onsite wood residues, as the legacy profile
maps did. Complete QA demand/biomass totals and total-demand publication data
retain those fuels; the profile exclusions must not be applied to them.

Mixed-fuel renewable generation retains plant, region, vintage and year matching
and the equal-conversion-efficiency assumption. TFEC excludes international
aviation and shipping. Undefined shares remain null. Demand-flex heat/service
flows are converted using matching underlying raw input/output efficiencies.

Post-processing remains incomplete until every labelled and summary write
succeeds. Its manifest lists summary paths. Successful retries remove superseded
summary CSVs and old summary Parquets; failed attempts remain ineligible for
publication or QA.

PUBLISH batches prepared summary CSVs, preserving relative paths and values.
CSV reads retain text identifiers and labels, require integer annual periods and
numeric values, and preserve full float precision and blank undefined values.
The Explorer's full-results ZIP includes summary CSVs beneath `summaries/` to
avoid collisions with labelled-result exports. Its `export-summaries`
command selects release scenarios, applies display labels and writes CSVs plus
an export provenance record. It performs no summary calculation. Original QA
calculations and saved exports remain available until later caller migration and
retirement; the report has not yet switched to summary reads.

## v308 backfill and provenance

The manual backfill reads the preserved v308 labelled Parquets and recovered raw
results. It does not rerun legacy post-processing. Renewable classifications come
from the explicitly approved frozen `metadata/fuel_labels.csv` described in the
[recovery record](v308-recovery.md).

Timeslice weights come from archived `G_YRFR` in
`SOLVE-TIMES-NZ/veda_ground_truths/steady-v308/syssettings.dd`. The 48 region/slice
records were checked for identical NI/SI weights and collapsed to 24 unique
slices summing to one, frozen as `v308/metadata/timeslices.csv`. The backfill does
not use live PREP timeslice weights.

The local release contains 56 datasets under `summaries/`, plus
`summary-provenance.json` and `summary-validation.json`. These record input and
output checksums, implementation checksums, comparison tolerances and exceptions.
Original labelled files, raw results, the fuel snapshot and release manifest were
verified unchanged. Back up these ignored release artefacts with the release.

The CSV format migration serializes those 56 prepared tables without rerunning
any calculations. Every CSV was reread with exact key, value, row-order and null
equality to its source Parquet. `summary-provenance.json` now lists CSV paths and
checksums and retains the previous Parquet records under
`summary_format_migration`; `summary-validation.json` points to the CSV names.
All 56 publication exports also passed an exact round-trip check. The archived
battery discrepancies below are unchanged.

## Validation and historical exceptions

Compared all 33 saved top-level CSV exports against the prepared values, allowing
newly completed zero rows. Thirty match within relative tolerance `1e-8` and
absolute tolerance `5e-7`. The four sensitivity exports use the corresponding
prepared demand/emissions series, with `MT`/`Mt` unit spelling normalized only
for this comparison.

| Saved CSV that differs | Differing rows | Maximum absolute difference |
| --- | ---: | ---: |
| `battery_flows_gw_2050.csv` | 60 | 0.6792033024 GW |
| `battery_flows_gwh_2035.csv` | 57 | 91.32679207 GWh |
| `battery_flows_gwh_2050.csv` | 60 | 73.83206300 GWh |

All 620 labelled battery-flow rows for the two main scenarios match the recovered
raw values. The saved 2035 GW/GWh pair is itself inconsistent in 57 rows under
the recorded timeslice weights. The saved 2050 pair is mutually consistent but
differs from the released raw/labelled data. Preserve these historical CSVs;
new summaries follow the released source values rather than forcing agreement.
They require review before the archived exports are retired.

Synthetic tests cover grouping, legacy years, completion, renewable allocation,
exclusions, undefined ratios, flow conversions, failure/retry handling, stale-file
cleanup and CSV export. An isolated real v309 post-processing run produced 54
summaries, PUBLISH preserved their values and exported all 54 CSVs, and a retry
removed an obsolete summary. No solver execution or existing run rewrite was
needed for that check.
