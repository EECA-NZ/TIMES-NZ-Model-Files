# Assumptions exploration

This is an inventory of model-input assumptions found in the current
PREPARE-TIMES-NZ code path which are **not stored in
`data_raw/coded_assumptions`**.  It is intentionally documentation only: it
does not prescribe a replacement file layout or move any values.

The sweep covered the modules under `src/prepare_times_nz` and the stage
scripts invoked by `dodo.py`.  It includes numerical values, dates, switches,
and fixed model selections that change a prepared model result.  It excludes
pure unit conversions (for example `3600` seconds/hour), VEDA interpolation
codes, implementation tolerances, and source-schema/code mappings that do not
themselves select a model result.  Some values below are currently derived
from raw data but are still assumptions because the code applies them as a
fixed override or selection.

## Transport

| Assumption | Current figure(s) | Current location |
| --- | --- | --- |
| PHEV input-fuel split | LPV PHEV: petrol 0.40, electricity 0.60 | `src/prepare_times_nz/stage_2/transport.py` — `FUEL_SPLIT_MAP` |
| Regional split of road modes | LPV, LCV, motorcycle, bus, light/medium/heavy truck: NI 0.73 / SI 0.27 | `src/prepare_times_nz/stage_2/transport.py` — `REGIONAL_SPLIT` |
| Regional split of rail, aviation and shipping | Rail freight diesel NI/SI 0.74/0.26; rail freight electricity 1/0; passenger rail diesel 1/0; passenger rail electricity 0.74/0.26; domestic aviation 0.58/0.42; international aviation 0.80/0.20; domestic shipping 0.34/0.66; international shipping 0.72/0.28 | `src/prepare_times_nz/stage_2/transport.py` — `REGIONAL_SPLIT` |
| Fuel shares used to split transport technologies | PHEV 0.40/0.60; dual-fuel heavy truck diesel/hydrogen 0.70/0.30; NI passenger rail electricity/diesel 0.79/0.21; NI rail freight diesel/electricity 0.97/0.03 | `src/prepare_times_nz/stage_2/transport.py` — `FUEL_SHARE` |
| Road-fuel energy content | Petrol 35.18 MJ/L; diesel 38.49 MJ/L; LPG 26.3735798 MJ/L | `src/prepare_times_nz/stage_2/transport.py` — `MJ_PER_LITRE` |
| Articulated-truck mass-band distribution | 3.5–7.5 t 0; 7.5–10 t 0.0100; 10–20 t 0.2102; 20–25 t 0.2317; 25–30 t 0.3781; >30 t 0.1700 | `scripts/stage_1_prep_raw_data/extract_fleet_vkt_pj_data.py` — `ARTIC_CLASS_PERC` |
| Rigid-truck mass-band distribution | 3.5–7.5 t 0.2038; 7.5–10 t 0.0697; 10–20 t 0.1278; 20–25 t 0.1348; 25–30 t 0.1908; >30 t 0.2731 | `scripts/stage_1_prep_raw_data/extract_fleet_vkt_pj_data.py` — `TRUCK_CLASS_PERC` |
| Articulated-to-truck class allocation | Six-by-six allocation matrix: `[[0,0,0,0,0,0], [1,0,0,0,0,0], [0,0.1,0.58,0.21,0.09,0.02], [0,0,0,0.29,0.595,0.115], [0,0,0,0.01,0.66,0.33], [0,0,0,0,0.5,0.5]]` | `scripts/stage_1_prep_raw_data/extract_fleet_vkt_pj_data.py` — `ARTIC_ALLOCATION_MATRIX` |
| Base-year transport extraction vintage and capacity/activity factor | Fleet workbook 2023; life rows 2022; `CAP2ACT = 0.08` (000 km); `ACT_BND_0 = -1` | `scripts/stage_2_baseyear/baseyear_transport_demand.py` — module constants |
| BEV heavy-truck productivity penalty | 2023: 13%; 2030: 7%; 2040 onward: 3%, with linear interpolation | `scripts/stage_2_baseyear/baseyear_transport_demand.py` — `apply_bev_heavy_truck_penalty` |
| Manual transport efficiency overrides | Electric motorcycle 2.82; hydrogen H2R heavy truck 0.08; hydrogen H2R medium truck 0.11; all domestic/international aviation and shipping 1.0 | `scripts/stage_2_baseyear/baseyear_transport_demand.py` — `enrich_with_efficiency` |
| Future transport PHEV and fuel-cell additions | PHEV diesel/electricity shares 0.4/0.6; fuel-cell efficiencies include car 0.735294117647059, light truck 0.128205128205128 (and further technology-specific entries in the list) | `scripts/stage_4_veda_format/create_newtechs_tra_files.py` — `add_newtechnames` |
| Future demand-technology start years | Commercial and transport new technologies start in 2024; agriculture/forestry/fishing new technologies start in 2025; the agriculture process list is taken from the Steady input rather than Shift | `scripts/stage_4_veda_format/create_newtechs_{com,tra,agr}_files.py` — `START` and `PROCESSES_SOURCE` |
| Transport fuel-delivery and H2R parameters | H2R: efficiency 0.37, life 20 years, FIXOM 100.40972; fuel delivery VAROM: NGA/LPG 4.946, petrol/diesel 0.92; DIJ/DID `FLO_DELIV` 2.4; diesel/DID share 1 and biodiesel share 0.07 | `src/prepare_times_nz/stage_4/baseyear/transport.py` — `create_fuel_process_parameters_df` |
| Transport fuel emission factors | LPG 61.04, petrol 68.79, diesel 69.63, jet fuel 67.76, fuel oil 75.36 | `src/prepare_times_nz/stage_4/baseyear/transport.py` — `emission_factors_df` |
| Road utilisation constraints | Each utilisation bucket must have a 33⅓% capacity share: own bucket coefficient `2/3`, other buckets `-1/3` | `src/prepare_times_nz/stage_4/baseyear/transport.py` — `create_constraints_df` |
| Shift transport-demand reduction | Per-capita demand declines 1% annually (`scale=0.01`) for Shift LCV and LPV demand | `src/prepare_times_nz/stage_3/demand_projections/transport.py` — `get_reduced_demand_index` and `main` |

## Demand, load curves, and base-year sectors

| Assumption | Current figure(s) | Current location |
| --- | --- | --- |
| Residential space-conditioning heating share | Winter 1.0; summer 0; spring 0.9; autumn 0.9 | `src/prepare_times_nz/stage_2/load_curves/residential_curves.py` — `HEATING_SHARE_ASSUMPTIONS` |
| Residential-POC classification threshold | A GXP is residential when residential ICP share is at least 0.90 | `src/prepare_times_nz/stage_2/load_curves/national_curves.py` — `get_residential_pocs`; called with `0.90` |
| National instead of EMI residential load curves | `USE_EMI_RES_CURVES = False` | `src/prepare_times_nz/stage_2/load_curves/national_curves.py` |
| Ballance chemical-sector allocation | Feedstock share 0.53; direct-use share 0.38 | `src/prepare_times_nz/stage_2/industry/industry_align_eeud_sectors.py` — `BALLANCE_FEEDSTOCK_SHARE_ASSUMPTION`, `BALLANCE_DU_ASSUMPTION` |
| Fuel delivery costs for base-year demand sectors | Industrial diesel/petrol/fuel oil 0.92; commercial diesel/petrol 0.92; residential diesel/petrol 0.92 and wood 10; unlisted residential fuels (including LPG) are zero | `src/prepare_times_nz/stage_4/baseyear/{industrial,commercial,residential}.py` — `DELIVERY_COST_ASSUMPTIONS` |
| Agricultural base-year variable operating costs | AGRNGA 2.81; AGRDSL 0.92; AGRPET 0.92; DID 2.4 | `src/prepare_times_nz/stage_4/baseyear/ag_forest_fish.py` — `VAROM_COST_ASSUMPTIONS` |
| Base-year fuel delivery life and efficiency | Fuel-delivery processes use life 100 years and efficiency 1.0 across residential, commercial, industrial and agriculture/forestry/fishing writers | `src/prepare_times_nz/stage_4/baseyear/{residential,commercial,industrial,ag_forest_fish}.py` — fuel-delivery builders |
| Base-year fuel emission factors | Commercial/agriculture: coal 82.37, natural gas 54.10, LPG 59.32, diesel 69.63, petrol 68.79; agricultural fuel-oil factor is also assigned in the same builder | `src/prepare_times_nz/stage_4/baseyear/{commercial,ag_forest_fish}.py` — `emission_factors_df` |

## Primary energy and bioenergy

| Assumption | Current figure(s) | Current location |
| --- | --- | --- |
| Contingent natural-gas recovery share | 60% of reported contingent reserves | `src/prepare_times_nz/stage_3/gas_forecasts.py` — `CONTINGENT_SHARE_ASSUMPTION` |
| Contingent-gas production profile | Lognormal distribution: `sigma=0.8`, 40 years, two-year startup; peak calculation uses `startup + 1` | `src/prepare_times_nz/stage_3/gas_forecasts.py` — `distribute_new_gas` defaults |
| Maui production closure patch | Production set to zero after 2026 | `src/prepare_times_nz/stage_3/gas_forecasts.py` — `update_maui` |
| Currency and barrel conversion for imported fuel costs | USD/NZD 1.68; 158.987 L/barrel | `src/prepare_times_nz/stage_4/baseyear/oil_and_gas.py` — `USD_TO_NZD`, `LITRES_PER_BARREL` |
| Field aggregation choice | Kapuni maps to `MINNGA-KAP`; every other field maps to `MINNGA-OTH` | `src/prepare_times_nz/stage_4/baseyear/oil_and_gas.py` — `FIELD_MAPPING` and `aggregate_fields` default |
| Bioenergy supply overrides through 2053 | `MINMNCWST01`: NI 3.877, SI 1.158 PJ; `MINANMMNR00`: NI 4.234, SI 3.326 PJ | `src/prepare_times_nz/stage_4/biofuels.py` — `SUPPLY_CONSTANTS_ALL_YEARS`, applied to 2053 |
| Bioenergy supply overrides from 2026 through 2053 | `MINOILWST00`: NI 0.180, SI 0.054 PJ; `MINOILWST01`: NI 0, SI 6.240 PJ | `src/prepare_times_nz/stage_4/biofuels.py` — `SUPPLY_CONSTANTS_FROM_2026`, applied to 2053 |
| Enhanced-bioenergy multiplier | The all-years supply overrides are multiplied by 4 in the additional supply output | `src/prepare_times_nz/stage_4/biofuels.py` — `create_additional_bioenergy_supply_forecasts` |

## Electricity

| Assumption | Current figure(s) | Current location |
| --- | --- | --- |
| Winter energy margins | WEM national margin 0.16; WEM South Island margin 0.24 | `src/prepare_times_nz/stage_3/wem_wcm.py` — `make_uc_wem` and `make_uc_wem_si` |
| WEM eligible seasons and hard-coded availability | Winter and autumn (`WIN-`, `FAL-`) are used for the margin; `WindFloatOff` is NI-only and `HydRR` SI-only; `CoalCHP` is excluded; distributed solar is assigned `ELCDD` | `src/prepare_times_nz/stage_3/wem_wcm.py` — `get_weighted_winter_afs`, `get_ni_only_techs`, `get_si_only_techs`, `create_uc_table` |
| Future generation USD conversion and diesel-peaker heat rate | USD exchange-rate multiplier 0.62; diesel peaker heat rate 11,000 GJ/GWh | `scripts/stage_3_scenarios/electricity/electricity_new_gen_tech.py` — `EXCHANGE_RATE_USD`, `DSLPKR_HEATRATE` |
| Geothermal heat-rate override | 24,000 GJ/GWh (15% efficiency) | `scripts/stage_2_baseyear/baseyear_electricity_generation.py` — geothermal `HeatRate` patch |
| Non-fixed generation availability and start | New non-fixed generation begins in 2026; GasPkr and OCGT lower availability factor is set to 0.02 | `src/prepare_times_nz/stage_4/electricity/new_generation.py` — `EARLIEST_YEAR` and `get_genstack_parameters` |
| Battery cost conversion and distributed-battery uplift | NZD/AUD 0.924; distributed battery CAPEX factor 2; FOM equals 1% of CAPEX | `src/prepare_times_nz/stage_4/electricity/new_storage.py` — `NZD_AUD`, `DIST_FACTOR`, `FOM_FACTOR` |
| Battery availability and start timing | Storage ratio is capped at 24 hours and converted to a daily factor; batteries start in base year + 2 | `src/prepare_times_nz/stage_4/electricity/new_storage.py` — `create_battery_main_file` |
| Default fixed-build commissioning month | Month 7 | `src/prepare_times_nz/stage_4/electricity/fixed_plant_adjustments.py` — `DEFAULT_INSTALL_MONTH` |

## Scenario constraints and new industrial technologies

| Assumption | Current figure(s) | Current location |
| --- | --- | --- |
| Coal-ban policy | Coal is banned for five listed process-heat end uses by 2037; final activity is zero | `src/prepare_times_nz/stage_4/coal_ban.py` — `get_all_commodities_to_ban` and `create_ban_veda` |
| EAF rollout and effect on Glenbrook cogeneration | First EAF: 2026; second in Shift: 2036; each is 0.03 GW (0.94608 PJ); coal cogeneration baseline 1.9426176 PJ and is halved per EAF | `src/prepare_times_nz/stage_4/industry/eaf.py` — module constants and `create_eaf_demand` |
| New industrial demand growth | Starts 2026; 50 GWh/year incremental growth; NI share 0.80 (SI 0.20); runs to 2060 | `src/prepare_times_nz/stage_4/industry/new_demand.py` — module constants |
| Future industrial technology defaults | General availability factor 0.5; BEV and HFCV start in 2030 rather than base year + 1 | `src/prepare_times_nz/stage_4/industry/new_techs.py` — `AF`, `TECH_START_OVERRIDES` |

## Input-preparation currency assumptions

These inputs affect the cost data subsequently supplied to the model, so they
are included even though they occur in stage 1 rather than a model-table
writer.

| Assumption | Current figure(s) | Current location |
| --- | --- | --- |
| Vehicle-cost currency and distance conversions | USD/NZD 1.68; EUR/NZD 1.98; mile/km 1.60934; EECA price-sheet vintage 2025; NREL cost vintage 2022 | `scripts/stage_1_prep_raw_data/extract_vehicle_costs_data.py` — module constants |
| NREL price base year | 2022 | `scripts/stage_1_prep_raw_data/extract_nrel_data.py` — `PRICE_BASE_YEAR` |

## Substantive values embedded in `user_config` TOMLs

The original code sweep did not systematically include direct values in
`data_raw/user_config`.  This section adds the substantive candidates found in
those TOMLs.  `WorkBookName`, `SheetName`, `TagName`, `DataLocation`, and
similar workbook-assembly metadata are deliberately excluded: they should stay
in `user_config`.  The values below are migration candidates: substantive
assumptions should move to an appropriate assumption file, with the TOML
changed to reference the resulting input or generated table.

| Assumption | Current figure(s) | Current location |
| --- | --- | --- |
| Historical domestic-gas activity bounds | Kapuni: 12.11 PJ (2023), 14.24 PJ (2024); other fields: 135.94 PJ (2023), 104.73 PJ (2024) | `data_raw/user_config/base_year/VT_TIMESNZ_PRI.toml` — `GasSupplyHistorical` |
| Gas-distribution network parameters | Existing capacity 150 PJa; `CAP2ACT` 1; FIXOM 200; life 100 years; natural-gas and biomethane conversion efficiencies 1.0 | `data_raw/user_config/base_year/VT_TIMESNZ_PRI.toml` — `GasDistributionNetworkParameters` and `GasDistributionNetworkTopology` |
| Coal supply price and availability | Mining/import cost 7; mining activity bound 25 PJ; import activity bound 15 PJ | `data_raw/user_config/base_year/VT_TIMESNZ_PRI.toml` — `CoalParameterDeclarations` |
| Total-CO2 aggregation coefficients | ELCCO2, TRACO2, RESCO2, INDCO2, COMCO2, AGRCO2 and GASCO2 each have coefficient 1 | `data_raw/user_config/base_year/VT_TIMESNZ_PRI.toml` — `TOTCO2AggregationDefinition` |
| Residential fuel emission factors | Coal 92; natural gas 53.96; LPG 60.43; petrol 68.79; diesel 69.69; wood 4 | `data_raw/user_config/base_year/VT_TIMESNZ_RES.toml` — `ResidentialEmissionsParameters` |
| Industrial fuel emission factors | Coal 92.65; natural gas 54.11; LPG 59.32; diesel 69.45; petrol 68.87; fuel oil 73.25; geothermal 0; wood 0 | `data_raw/user_config/base_year/VT_TIMESNZ_IND.toml` — `IndustryEmissionsParameters` |
| Electricity statistical-difference calibration demand | Fixed activity bounds: 1.3 PJ in 2023 and 2.0 PJ in 2024, carried forward | `data_raw/user_config/base_year/VT_TIMESNZ_ELC.toml` — `StatDiffProcessParameters` |
| LNG import and terminal parameters | LNG import cost: Steady 20, Shift 40; terminal CAPEX 800 NZDm; `CAP2ACT` 40; efficiency/AFA 1; lower AFA 0; FIXOM 90; NI only | `data_raw/user_config/new_technologies/NewTech_LNG_{Steady,Shift}.toml` — LNG parameter sections |
| EAF process parameters | Start 2026; existing capacity 0.03 GW in 2027; efficiency 1; life 50 years; `CAP2ACT` 31.536 | `data_raw/user_config/new_technologies/NewTech_IND.toml` — `EAFParameters` |
| New industrial-demand process parameters | Start 2026; efficiency 1; `CAP2ACT` 31.536 | `data_raw/user_config/new_technologies/NewTech_IND.toml` — `NewDemandParameters` |
| Residential demand-flex parameters | 2023 shares `[0.5, 0.5, 0.05, 0.05, 0, 0]`; 2050 shares Steady `[0.4, 0.4, 0.1, 0.1, 0.2, 0.2]`, Shift `[0.4, 0.4, 0.2, 0.2, 0.6, 0.6]`; storage efficiencies `[0.94, 0.94, 0.98, 0.98, 0.98, 0.98]`; start 2024 | `data_raw/user_config/scenarios/DemandFlex.toml` — `ResidentialFlexParametersSteady` and `ResidentialFlexParametersShift` |
| WCM NI peak reserve | 5% from 2023, extrapolated forward | `data_raw/user_config/scenarios/WEM_WCM.toml` — `PeakConstraintNIMargin` |
| Gas-network blending coefficients | NI coefficients `[1, 1, 0, 0]` for NGA/BIM input-output combinations | `data_raw/user_config/scenarios/BaseConstraints.toml` — `GasNetworkBlendingConstraints` |
| LPG trade cost | 0.00538 NZD/GJ | `data_raw/user_config/scenarios/TradeParameters.toml` — `LPGTradeCosts` |
| Sector-closure availability | Urea closure: NI 1, SI 0 | `data_raw/user_config/scenarios/SectorClosures.toml` — `SectorClosureIslands` |
| Global discount rate | 10% (with 2015 as the associated year entry) | `data_raw/user_config/settings/SysSettings.toml` — `DiscountRates` |
| Dummy-import penalty costs | 1,000,000 and 100,000,000 for the two dummy-import groups | `data_raw/user_config/settings/SysSettings.toml` — `DummyVariableCosts` |

Values such as the start year, active period definition, units, VEDA
interpolation codes, and deliberately high infeasibility-avoidance values need
a later classification.  They are model-relevant configuration, but are not
automatically candidates for the sector/system assumptions tree merely because
they are literals.

## Follow-up boundary

This list is deliberately not a migration plan.  Before moving an entry, it
should be confirmed whether it is a scenario input, a base-year calibration
choice, a policy setting, or a physical/unit conversion.  The latter category
may reasonably remain in code, whereas the first three should normally become
versioned data under `data_raw/coded_assumptions`.

## Migration Plan

### Recommendation

Rename `data_raw/coded_assumptions` to `data_raw/assumptions` and use it as the
authoritative home for maintained model-input assumptions.  The existing tree
is suitable for this: it already has around 90 clearly named files, grouped
largely by model domain, and the pipeline already accesses most of them through
the single `ASSUMPTIONS` path constant.

The migration should retain `data_raw/concordances` as a separate sibling.
Concordances are maintained mapping/reference data; treating every mapping as a
model assumption would make both concepts less legible.  A mapping which is a
genuine modelling choice can instead be stored under `assumptions` and named as
such.

### Target organisation

Keep the current domain-first layout rather than creating one large folder by
assumption type.  A reader usually starts with the part of the model they are
changing, and the current `electricity_generation/future_techs` pattern shows
that a second level works well where it is needed.

The principal improvement should be consistent domain names and a small set of
subdirectories for assumptions which are not sector technology tables:

```text
data_raw/assumptions/
  transport/                 # rename transport_demand
    base_year/
    future_techs/
    constraints/
  residential/
    base_year/
    future_techs/
    constraints/
  commercial/                # rename commercial_demand
    base_year/
    future_techs/
    constraints/
  industry/                  # rename industry_demand
    base_year/
    future_techs/
    constraints/
  ag_forest_fish/            # rename ag_forest_fish_demand
    base_year/
    future_techs/
    constraints/
  electricity_generation/
    base_year/
    future_techs/
    constraints/
    renewable_curves/
    storage/
  oil_and_gas/
    base_year/
    forecasts/
    constraints/
  biofuels/
    base_year/
    forecasts/
    constraints/
  hydrogen/
    future_techs/
    constraints/
  system/
    carbon_prices/
    demand_projections/
    load_curves/
    policy/
    cross_sector_constraints/
    patches/
    model_configuration/
```

This is a target taxonomy, not a requirement to move every existing file in
the first change.  Existing folders can initially be copied over unchanged
apart from the top-level rename.  New files should use the target names; a
later, mechanical tidy-up can rename `*_demand` folders once all references
are updated.

The `base_year` / `future_techs` / `constraints` split is the default within a
sector.  It makes historical calibration, prospective technology inputs and
feasibility restrictions visible in the path itself.  Use `forecasts` where a
domain has future inputs that are not technology assumptions, notably oil and
gas and biofuel supply.

`system` is the intentional exception: it holds inputs whose purpose is
model-wide rather than sector-owned.  Its `cross_sector_constraints` folder is
only for rules that genuinely link sectors, commodities or the whole model.
Sector-specific constraints—such as WEM, transport utilisation and industrial
biogas availability—remain under the owning sector.  The current mixed
`banned_techs.csv` and `capacity_limits.toml` files may live temporarily in
`system/cross_sector_constraints`, then be split by sector when their contents
are migrated.

Use small, topic-specific CSV or TOML files, with a short `README.md` in each
domain that explains the files, units, grain, source, and consuming module.
Prefer CSV for tabular values and TOML for a compact named set of scalars,
switches, and lists.  Avoid a single `all_assumptions.csv`: it would be hard to
validate, edit, and trace back to a pipeline stage.

For every migrated assumption file, include at least these fields or metadata:

| Need | Suggested representation |
| --- | --- |
| Human-facing name and intent | `Assumption` / `Description` column, or TOML comments |
| Value and unit | `Value`, `Unit` columns; named TOML values for scalars |
| Scope/grain | Explicit columns such as `Scenario`, `Region`, `Sector`, `Fuel`, `Technology`, `Year` as applicable |
| Provenance | `Source` and `SourceDate` columns, or README metadata |
| Code traceability | `UsedBy` column or README path/function reference |

For example, the WEM values should become a compact reliability file with
named WEM/WEM_SI rows (margin, eligible seasons, constraint scope); transport
regional and fuel splits should become keyed tables under
`transport/base_year`; and the biofuel constants should be rows keyed by
technology, region, first year, last year, and scenario/multiplier.

### Migration sequence

1. Define `data_raw/assumptions` as the new root and update
   `utilities/filepaths.py` so `ASSUMPTIONS = DATA_RAW / "assumptions"`.
   Update the two stage scripts which currently bypass that constant:
   `scripts/stage_1_prep_raw_data/extract_vehicle_costs_data.py` and
   `scripts/stage_2_baseyear/baseyear_electricity_generation.py`.

2. Update the six source `DataLocation` references under `data_raw/user_config`
   (base-year primary-energy, LNG, battery-build, residential-fossil and trade
   parameter TOMLs), plus documentation links and descriptions.  The
   `data_intermediate/stage_0_config` copies are generated outputs and should
   be regenerated, not edited by hand.

3. Move the existing tree without changing internal layout.  Run the full
   preparation pipeline and compare generated stage-4 tables to establish that
   the rename is behaviour-preserving.

4. Migrate the discovered code-held values incrementally, domain by domain.
   For each file: add the data file, replace the literal with a validated read,
   add a small test for missing/duplicate/out-of-range values, and compare the
   affected output with the pre-migration output.

5. Start with high-impact, compact assumptions: WEM/WCM; transport splits and
   manual efficiencies; gas contingent/production-profile settings; biofuel
   overrides; electricity currency/heat-rate/battery adjustments; then sector
   delivery costs and emissions.  Migrate large legacy technology lists only
   after their active stage-script ownership is confirmed.

6. Once all consumers use the new root, apply the optional domain-name tidy-up
   (`*_demand` to the sector name) and split the current mixed cross-sector
   constraint files into sector-owned files where appropriate, in one
   separately tested change.  Update the domain READMEs and this inventory as
   each group is completed.

### Guardrails

Do not migrate physical constants or VEDA syntax merely because they are
literals.  A useful test is whether a modeller could reasonably choose a
different value and expect a different scenario or calibration result.  Also,
avoid silently retaining fallback values in code after migration: fail clearly
when a required assumption is missing, while keeping only explicitly documented
defaults where a default is an intended model choice.

### Deferred documentation-build optimisation

Once the assumption structure and documentation method have been settled, it
may be worthwhile to reduce the Read the Docs (RTD) checkout to the files that
the documentation build actually consumes.  This is explicitly deferred: the
current priority is making assumptions authoritative, legible, and reliably
rendered in documentation.

At present, the repository-level `.readthedocs.yaml` points Sphinx to
`PREPARE-TIMES-NZ/docs/source/conf.py`.  The Sphinx build does not import the
PREPARE source package, read `data_raw`, or use filesystem links outside the
documentation tree.  Documentation tables referenced with `csv-table` are
currently stored below `docs/source`, including tables generated and committed
by separate preparation tasks.  References to raw data elsewhere in the prose
are descriptive text or GitHub hyperlinks, not build-time file dependencies.

The intended documentation method is to make the documentation source tree
self-contained, rather than to read raw assumptions directly on RTD:

```text
data_raw/assumptions/...                    # authoritative model inputs
docs/source/_generated/assumptions/...      # selected generated copies
docs/source/_data/assumption_substitutions.toml
```

A documentation-assets task will copy only the TOML/CSV files selected for
documentation from `data_raw/assumptions` to
`docs/source/_generated/assumptions`.  The files in `_generated` are derived
assets: they must not be edited directly, and the task should be run and its
outputs committed whenever their source assumptions change.  The substitution
manifest will assign stable documentation names and display formats to values
in those copied files; `conf.py` can then expose them to MyST as, for example,
`{{ national_wem }}`.  Existing `csv-table` documentation can likewise read
the copied CSV assets.

The task should have a CI staleness check, so a raw-assumption change fails the
documentation check until its selected documentation asset has been refreshed.
After this method is in place, an RTD sparse checkout can include only `docs/`
and need not include the raw assumption tree or PREPARE source package.  The
RTD custom checkout should be configured and tested only after those
dependencies are explicit; it is an external RTD-project setting and is not a
replacement for the assumptions migration.
