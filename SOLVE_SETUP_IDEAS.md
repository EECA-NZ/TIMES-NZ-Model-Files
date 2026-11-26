# SOLVE setup ideas

Ideas for capturing more from the GAMS/TIMES working environment in stored SOLVE builds.
Raised while investigating why v309 peak behaviour differs from v308. Nothing here is implemented or tested in GAMS.

## Already available
- `EQ_Peak` levels are in the `.vd` (672 rows), alongside `EQ_PeakM` marginals.

## Ideas (priority order)

1. **Preprocessed peak sets/parameters in the `.vd`.**
   `RPC_PKC`, `RPC_ACT`, `PRC_ACTFLO`, `COM_PKTS`, post-preprocessing `NCAP_PKCNT`, `FLO_PKCOI`, `COM_GMAP`.
   - Not in `times2veda.vdd` today, so not in the `.vd`.
   - Option A: add mappings, e.g. `PAR_Top  par_top  r t p c uc_n` style. Unchecked whether the sets survive preprocessing.
   - Option B: small GAMS extract writing them to a separate GDX/CSV.
2. **`RPT_TOP`.** `PAR_Top` is already mapped in `times2veda.vdd` but opted out by default (TIMES Part II). Add `SET RPT_TOP YES` to the `.run` template (SOLVE generates it, so it is trackable). Topology flags only, not the peak sets.
3. **Model statistics in the run manifest.** Equation, variable and non-zero counts, solve status, objective, CPLEX iterations and time. The non-zero difference between runs (3.36M vs 3.25M) was a useful clue found by grepping the `.lst`.
4. **Optional equation listing.** Per-run `LIMROW` for named equations (e.g. `EQ_Peak`). Default stays `LIMROW=0`.
5. **`QA_CHECK.LOG` and input hash.** Store `QA_CHECK.LOG` and a hash of `output.dd` so builds can be shown to differ or not.

## Where `times2veda.vdd` comes from
- Not produced by xl2times. SOLVE reads it from the executor's `times_source_dir` (the external TIMES v4.8.3 install) in `SOLVE-TIMES-NZ/src/solve_times_nz/execution.py` (`_gdx2veda_command`, `_validated_gams_tools`).
- Editing the external install affects every solve on that machine and is not tracked.
- Proposed: a repo-owned `SOLVE-TIMES-NZ/config/times2veda.vdd`, used by `_gdx2veda_command` in place of the install copy.
