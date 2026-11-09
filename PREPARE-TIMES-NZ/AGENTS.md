# TIMES-NZ preparation-specific instructions

The repository-level development and testing conventions are in `../AGENTS.md`.

## Never cut for TIMES-NZ preparation

- **Source lineage:** retain the source, vintage, coverage and rationale for raw data and coded assumptions. Do not silently replace an authoritative source or turn a historical estimate into a forecast.
- **Year, unit and boundary semantics:** preserve base-year versus historical versus projected data, calendar coverage, units, currency years, signs and energy conversions. An intentional data gap must be explicit.
- **No silent loss or double count:** validate source schemas, category maps, joins, filters and allocations. Missing, unmatched, duplicated or reclassified data needs a visible check or a deliberate, documented rule.
- **Calibration and reconciliation:** keep checks that compare prepared data with its source totals (for example EEUD, MBIE, GIC or EA) and explain any material difference rather than smoothing it away.
- **Reproducible staged outputs:** keep transformations in the preparation pipeline and configuration; do not rely on manual edits to generated files.
- **Model integrity:** preserve the relationships required for a feasible TIMES model—commodity/process mappings, regional and timeslice balance, and demand/supply accounting—unless the task deliberately changes them.
- Anything the user explicitly asks to retain or validate.

## Script/src definitions

Scripts orchestrate functions found in `src/`. Scripts that import `src` functions should read and write data independently before processing. `src` functions do not explicitly read or write data; processing applies only to dataframes. Keep data I/O explicit in scripts.

When changing legacy scripts or `src` functions that do not follow these rules, estimate the size of any refactor and flag it for the user. Do not broaden a focused task into a whole-pipeline refactor without their direction.

