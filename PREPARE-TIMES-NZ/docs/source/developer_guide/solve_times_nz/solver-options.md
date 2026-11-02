# Solver options

This page describes the CPLEX options used by generated TIMES-NZ cases. Solver
settings affect how CPLEX solves a mathematical model; they do not change the
workbooks or the model formulation. They can nevertheless affect run time,
numerical behaviour, and the particular solution returned when an LP has
multiple equivalent or near-equivalent optima.

## Where options are defined and applied

The versioned source of truth is
`SOLVE-TIMES-NZ/templates/cplex.opt`. When a case selects `cplex` in its
`[times]` manifest section, the case builder copies that file to the generated
case directory as `cplex.opt`. The Windows executor invokes GAMS with the
`OPTFILE=1` command-line parameter, which tells GAMS to load the selected
solver's option file.

Staging copies the complete generated case, including `cplex.opt`, to the
Windows solver directory. The generated `manifest.json` records a SHA-256 hash
of the options template so a run can be tied to the exact options used.

The template currently mirrors the options in the VEDA Steady ground truth.
It applies only to CPLEX cases; another solver needs its own solver-specific
option file and documented staging behaviour.

## Current CPLEX settings

| Option | Current value | Purpose |
| --- | ---: | --- |
| `lpmethod` | `4` | Force the barrier (interior-point) method for LP solves. |
| `baralg` | `1` | Use CPLEX's infeasibility-estimate barrier start. |
| `barcrossalg` | `0` | Let CPLEX choose the crossover method after barrier. |
| `barorder` | `0` | Let CPLEX choose the barrier row-ordering method. |
| `scaind` | `1` | Use CPLEX's more aggressive matrix scaling. |
| `aggind` | `3` | Apply the presolve aggregator up to three times. |
| `advind` | `0` | Do not use an advanced basis from an earlier solve. |
| `THREADS` | `7` | Permit seven solver threads. |
| `rerun` | `yes` | If presolve reports infeasible or unbounded, retry without presolve. |
| `iis` | `1` | Run conflict/IIS analysis after an infeasible solve. |
| `Names` | `no` | Do not load GAMS symbol names into CPLEX. This reduces solver memory/log overhead. |

The template does not explicitly set CPLEX's LP optimality or feasibility
tolerances. With the installed GAMS 44 / CPLEX 22.1 solver, their defaults are
`epopt = 1e-6` (reduced-cost optimality) and `eprhs = 1e-6` (primal
feasibility). These tolerances are numerical units, not percentages of the
objective.

## Changing options

Change `SOLVE-TIMES-NZ/templates/cplex.opt`, then rebuild and stage a new case.
Do not edit `cplex.opt` only in a generated or staged directory: rebuilding a
case replaces that directory, and the one-off edit would not be reproducible.

For example, a tolerance investigation could add the following lines to a
dedicated branch or an explicitly named experimental template:

```text
epopt 1e-9
eprhs 1e-9
```

Both values are 1,000 times tighter than the current defaults. Tighter
tolerances can increase solve time and, for a poorly scaled model, can make
numerical difficulties more visible. They should therefore be changed together
with a recorded comparison of solver status, objective, primal infeasibility,
and run time.

Changing `lpmethod`, scaling, presolve, or thread settings should likewise be
treated as a solver experiment. To compare a generated case with a VEDA ground
truth, use the same options for both runs. A changed solver setting does not by
itself demonstrate a model-input difference.

## Checks after changing options

After rebuilding a CPLEX case, verify that:

1. the generated case contains `cplex.opt`;
2. the executor's GAMS command includes `OPTFILE=1`;
3. the staged run directory contains the same `cplex.opt`;
4. the GAMS listing shows CPLEX loading the option file, without an
   `Cannot open parameter file` message; and
5. the generated manifest's `cplex_options_template_sha256` is recorded with
   the run artefacts.

The case builder's test suite checks the first two conditions. The listing-file
check remains important because it verifies the native Windows solve rather
than only the Linux-side case generation.
