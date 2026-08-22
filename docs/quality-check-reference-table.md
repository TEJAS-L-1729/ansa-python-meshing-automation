# ANSA Quality Criteria Reference

The full quality-criteria configuration screen used to validate this project's meshes, as displayed in ANSA's Solids quality-check panel (see `media/fig8.5-ideal-mesh-quality-check-table.jpg`).

| Criteria | Calculation Standard | Best | Good | Failed | Worst |
|---|---|---|---|---|---|
| Aspect Ratio | NASTRAN | 0 | 60 | 95 | 100 (penalty: 1.2247 / 3 / 8 / 15) |
| Skewness | FLUENT | 0 | 0.25 | 0.5 | 1 |
| **Warping** ✓ | IDEAS | 0 | 5 | 10 | 90 |
| Crash time step | LS-DYNA | 1 | 1.4E-6 | 1.E-6 | 0 |
| Squish | — | 0 | 0.15 | 0.3 | 1 |
| Jacobian | ANSA | 1 | 0.8 | 0.7 | 0 |
| Min / Max angle (tetras) | FLUENT | 0 / 0 | 40 / 90 | 20 / 120 | 0 / 180 |
| Min / Max angle (pentas) | FLUENT | 0 / 0 | 45 / 90 | 30 / 120 | 0 / 180 |
| Min / Max angle (hexas) | FLUENT | 0 / 0 | 60 / 110 | 30 / 140 | 0 / 180 |
| Stretch | — | 1 | 0.75 | 0.5 | 0 |
| Collapse | — | 1 | 0.9 | 0.75 | 0 |
| Mid point deviation % | — | 0 | 25 | 33.3 | 100 |
| Mid point alignment % | — | 50 | 40 | 33.3 | 0 |
| Multi violation | — | 0 | 1 | 2 | 4 |
| Non-orthogonality | OPENFOAM | 0 | 50 | 70 | 80 |
| Growth ratio | ANSA | 0.8 | 1 | 1.2 | 2 |
| Negative volume | PARTIAL | — | — | — | — |

`✓` = criterion actively enabled/checked in this project's quality panel run shown in the referenced screenshot.

## Per-mesh-size results against these criteria

See the main [README](../README.md#quality-checks-per-mesh-size) for the full 3 mm / 5 mm / 7 mm comparison table. Summary:

- **All three mesh sizes** cleared Aspect Ratio, Skewness, Warpage, and Jacobian within the "Good"–"Best" bands.
- No negative-volume or inverted (negative Jacobian) elements were produced at any tested mesh size.
- The **final production mesh** (used for downstream FE analysis) recorded a max skewness of 1.23 (NASTRAN standard) and a max aspect ratio of 8.5 — both within acceptable limits for structural analysis, though not as tight as the finer convergence-study meshes, since the final mesh uses a coarser global sizing for computational efficiency.
