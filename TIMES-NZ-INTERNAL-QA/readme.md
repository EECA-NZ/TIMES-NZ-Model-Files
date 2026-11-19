# TIMES-NZ-INTERNAL-QA


This module contains the legacy internal QA app and analysis tools. The Explorer
now lives in `PUBLISH-TIMES-NZ`. `SOLVE-TIMES-NZ` owns result post-processing.

## Solver result bundles

`SOLVE-TIMES-NZ` now writes labelled parquet outputs for every completed model
run. Build and solve a case with:

```bash
uv run --directory SOLVE-TIMES-NZ solve-times-nz solve steady
```

The run directory under `SOLVE-TIMES-NZ/build/solves/` contains the raw `.vd`,
`raw_results.parquet`, the labelled output parquets, and the PREP metadata used
for that run. PUBLISH combines selected run outputs into named releases.

## Explorer deployment

For deployment payloads and deployment instructions, see the internal TIMES-NZ Explorer deployment runbook.
