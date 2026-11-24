# SOLVE summary migration

Implemented 24 November 2026 as step 3 of the [QA reporting plan](reporting-plan.md).
This records the current implementation, not a fixed catalogue for future summaries.

## Ownership and outputs

`solve_times_nz.reporting.build_summaries()` accepts already-loaded result and
metadata dataframes. It produces named per-scenario tables; file reading and
writing remain in post-processing. `reporting_flows` contains the battery/flex
timeslice calculations. Neither module imports QA or chart-rendering libraries.
Summaries are CSVs; raw and labelled result datasets remain Parquets. Names
describe contents rather than consumers. Subject folders remain a separate
follow-up.

| Existing capability | Prepared summary tables |
| --- | --- |
| Detailed fuel demand, including natural gas, diesel and petrol | `energy_demand_by_fuel_and_sector_group`, `energy_demand_by_fuel` in PJ |
| Electricity demand | `electricity_demand`, `electricity_demand_by_sector_group` in TWh |
| Woody biomass demand | `woody_biomass_demand`, `woody_biomass_demand_by_sector_group` in PJ, including onsite residues |
| Road fuel demand by vehicle class | `road_transport_demand_by_fuel_and_vehicle_class`; select `Fuel` |
| Annual generation and thermal fuel use | `electricity_generation`, `electricity_generation_by_technology_group`, `thermal_generation_fuel_use` |
| Demand by sector, fuel, island and industrial profile | Existing publication filename stems, plus `fuel_use_by_island_and_sector` |
| Emissions totals and sector groups | `emissions`, `emissions_by_sector_group`, `emissions_by_broad_sector_group` |
| Gas/biomass primary supply | Existing `primary_energy_*` views, plus unrounded `natural_gas_supply` and `natural_gas_supply_by_source` |
| Battery capacity and LPV/LCV/truck fleets | `battery_capacity`, `transport_capacity`; select fleet `EndUse` |
| Renewable electricity and TFEC indicators | `renewable_*_share`; select `Unit = Share` for fractions or `%` for percentages |
| Battery and demand-flex timeslices | `battery_flows`, `demand_flex_flows`; select `Period` (2035/2050) and `Unit` (GW/GWh); signed flows, labels and completed timeslices retained |
| Whole-run objective | `objective_function` in NZDb, without an annual period |
| Four existing technology-sensitivity CSVs | Values supplied by the same prepared demand/emissions series for the selected scenario IDs; no duplicate sensitivity calculation |

Summary generation normalizes annual years, validates grouping classifications
and units, and completes absent annual rows within each summary's observed
categories and model years. Existing nulls are not converted into zeroes. Empty
summary selections produce no dataset. QA will not perform category completion.

The detailed fuel and vehicle-class demand tables cover all observed fuels;
readers select the fuels they need. Their totals remain prepared by SOLVE.
`total_demand_by_fuel` retains the archived broad fuel classification and small
value cleanup, distinct from the unrounded `energy_demand_by_fuel` table.

The publication views retain archived fuel groupings. Industrial publication
profiles explicitly omit fuel oil and onsite wood residues, as the legacy profile
maps did. Complete QA demand/biomass totals and total-demand publication data
retain those fuels; the profile exclusions must not be applied to them.
`electricity_demand_by_sector_group` keeps agriculture separate;
`electricity_demand_by_sector_group_combined_industry` retains the archived view
with agriculture merged into industry and its small-value cleanup. Broad
emissions retain Electricity generation, Industry and Transport separately and
combine the remaining sectors as Other. Natural-gas supply remains unrounded
separately from the cleaned `primary_energy_*` supply views.

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

The local release now contains 38 datasets under `summaries/`, plus
`summary-provenance.json` and `summary-validation.json`. These record input and
output checksums, implementation checksums, comparison tolerances and exceptions.
Original labelled files, raw results, the fuel snapshot and release manifest were
verified unchanged. Back up these ignored release artefacts with the release.

The initial CSV format migration serialized 56 prepared tables without rerunning
any calculations. Every CSV was reread with exact key, value, row-order and null
equality to its source Parquet. `summary-provenance.json` now lists CSV paths and
checksums and retains the previous Parquet records under
`summary_format_migration`; `summary-validation.json` points to the CSV names.
All 56 publication exports also passed an exact round-trip check. The archived
battery discrepancies below are unchanged.

## Consumer-neutral names and consolidation

The next migration reduced v308's 56 summary files to 38. It rebuilt summaries
per scenario from the preserved labelled/raw results and recorded fuel/timeslice
snapshots, without rerunning legacy post-processing. All 56 former views were
matched by keys and values against selections from the consolidated tables,
using the existing relative tolerance `1e-8` and absolute tolerance `5e-7`.
Every new CSV also passed an exact serialization round trip and all 38 exported
successfully through PUBLISH. Raw/labelled results, metadata and the release
manifest were verified unchanged.

`summary-provenance.json` records previous summary checksums, replacement paths,
row filters and comparison results under `summary_consolidation`, with updated
implementation/output checksums. `summary-validation.json` now supplies
`summary_filters` where a historical CSV is a selection of a consolidated table.

| Previous table(s), without `.csv` | Replacement and selection |
| --- | --- |
| `qa_demand`, `qa_sector_demand` | `electricity_demand`, `electricity_demand_by_sector_group` |
| `qa_gas_demand`, `qa_diesel_demand`, `qa_petrol_demand` | `energy_demand_by_fuel_and_sector_group`, selecting `Fuel` |
| Their `*_total` tables | `energy_demand_by_fuel`, selecting `Fuel` |
| `qa_road_diesel`, `qa_road_petrol` | `road_transport_demand_by_fuel_and_vehicle_class`, selecting `Fuel` |
| `qa_biomass_demand`, `qa_biomass_demand_total` | `woody_biomass_demand_by_sector_group`, `woody_biomass_demand` |
| `qa_gas_supply`, `qa_gas_supply_total` | `natural_gas_supply_by_source`, `natural_gas_supply` |
| `qa_generation`, `elec_gen_by_tech` | `electricity_generation_by_technology_group` |
| `qa_generation_total`, `elec_gen_line` | `electricity_generation` |
| `qa_emissions`, `qa_emissions_total` / `emissions_line` | `emissions_by_sector_group`, `emissions` |
| `emissions_sector_facet` | `emissions_by_broad_sector_group` |
| `qa_objective` | `objective_function` |
| Previous `electricity_demand_by_sector_group` | `electricity_demand_by_sector_group_combined_industry` |
| `transport_lpv_capacity`, `transport_lcv_capacity`, `transport_truck_capacity` | `transport_capacity`, selecting `EndUse` |
| `indicator_ren_gen`, `indicator_ren_tfec` | `renewable_generation_share`, `renewable_tfec_share`, selecting `Unit = %`; former fraction views select `Share` |
| Separate battery/flex year/unit files | `battery_flows`, `demand_flex_flows`, selecting `Period` and `Unit` |

Shared generation tables use the exact PJ-to-TWh conversion (`Value / 3.6`),
replacing the publication views' rounded constant. The difference is within the
recorded validation tolerances. Other differing units, boundaries and
classifications remain explicit. Readers must select `Unit` before using tables
containing both fractions/percentages or GW/GWh; annual periods and vehicle
classes are selected from columns rather than filenames.

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
cleanup and CSV export. Before consolidation, an isolated real v309 post-processing run produced 54
summaries, PUBLISH preserved their values and exported all 54 CSVs, and a retry
removed an obsolete summary. No solver execution or existing run rewrite was
needed for that check.
