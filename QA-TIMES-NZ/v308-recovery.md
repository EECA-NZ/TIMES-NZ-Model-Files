# v308 raw-result recovery

Completed 24 November 2026 as step 1 of the [QA reporting plan](reporting-plan.md).
This was a manual legacy-data recovery, with no pipeline changes or rerun of
v308 post-processing.

## Recovered artefacts

Under `PUBLISH-TIMES-NZ/releases/v308/`:

- `raw_results.parquet`: 7,245,817 rows for the ten scenarios in the existing
  release manifest. Original CSV dimensions, identifier case and placeholders
  are retained as strings; `PV` retains raw values as float64 using round-trip
  CSV parsing. `Scenario` is the exact source filename stem. No unit conversion
  or labelling was applied to the recovered raw values.
- `metadata/fuel_labels.csv`: an exact copy of the current PREP fuel-label file,
  approved specifically for this manual legacy adjustment.
- `raw-results-provenance.json`: absolute archive paths, per-source SHA-256
  checksums and row counts, the output checksum, numerical checks, the fuel
  snapshot checksum and the explicit classification exception.

Source CSVs came from the OneDrive TIMES-NZ 3.0 archive under
`Product Management/Data Release Bundles/Result Backups/v3_0_8/`. The four ETS
sensitivity CSVs absent from the existing release manifest were excluded and
listed in the provenance record.

## Classification exception

The user confirmed that changes since v308 do not affect the efficacy of
`PREPARE-TIMES-NZ/data_raw/coded_assumptions/reporting/fuel_labels.csv` for this
recovery and explicitly approved its use. The copied file is a reviewed current
source, not a recovered historical snapshot. Use this frozen copy for subsequent
v308 summary backfilling. This exception does not establish a pipeline fallback
to current PREP classifications for other archived results.

## Validation

- All ten raw objectives divided by 1,000 match the existing NZDb objectives
  within relative and absolute tolerances of 1e-12.
- All 2,664,373 existing `energy_demand` and `elec_generation` rows match the raw
  dimensions and values within relative and absolute tolerances of 1e-10.
- Source raw keys are unique; numeric values are finite; Parquet scenario IDs
  and per-scenario row counts match the sources and release manifest.
- The fuel snapshot covers all 17 fuels in the existing energy-demand and
  electricity-fuel-use datasets, with no missing classifications.
- SHA-256 checks confirm that the original labelled Parquets and release manifest
  were unchanged. The recovery adds data alongside them.

The recovered files live in the ignored local releases directory. Back them up
with the release; this record alone does not contain the recovered data.
