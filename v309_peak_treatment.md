# v309 peak treatment

## What changed

In v308 (Veda-built), 184 electricity generator candidates (solar, wind, geothermal, hydro, peakers, etc.) had their `PRC_ACTUNT` pointing at a commodity group (`<process>_NRGO`) instead of at `ELC`. In v309 (xl2times-built), `PRC_ACTUNT` points directly at `ELC`, and the `_NRGI`/`_NRGO` groups are no longer generated.

## Why it matters

TIMES only gives a process capacity credit in the `EQ_Peak` constraint if its primary commodity group is the commodity itself, or if `PRC_PKAF` is set (`pp_lvlpk.mod` lines 51-53). The v308 groups therefore silently removed these 184 candidates from the peak constraint. This made the v308 peak much tighter (binding in about 24 NI / 18 SI slices in 2050, against 6 NI / 0 SI in v309). It also led to more peaking capacity and, indirectly, higher residential gas.

## Evidence

Four solves of v309 inputs with groups re-added (2050 binding `EQ_PeakM` slices):

| Run | Binding slices | Objective |
|---|---|---|
| v309 base | 6 NI / 0 SI | 1,458,891 |
| + groups on batteries only | 6 / 0 | 1,458,891 |
| + groups on demand-flex only | 6 / 0 | 1,458,891 |
| + groups on the 189 other processes | 17 NI / 10 SI | 1,460,227 |
| same, plus `PRC_PKAF` on the 184 ELC generators | 6 NI / 0 SI | 1,458,891 |

The last row matches base exactly, so the groups removing peak credit explain the difference.

## Why we keep v309

The v308 behaviour was an artefact of the Veda group handling, not a modelling choice. v309 follows the TIMES default, where every generator counts toward the peak at its explicit `NCAP_PKCNT`. v309 derated margins are about 5-9% against the 5% reserve (`COM_PKRSV`).


