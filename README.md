# Camshaft Meshing Automation in ANSA using Python

Object-oriented Python automation for generating quality-controlled, NASTRAN-ready hexahedral/pentahedral meshes of a two-lobe camshaft in **BETA CAE ANSA**, built as an Experiential Learning project (AS244AI — Aerospace Structures, RVCE, Even Semester 2024–25).

The project moves camshaft meshing from a manual, click-driven ANSA workflow to a fully scripted, logged, and batchable pipeline — enabling repeatable mesh-convergence studies (3 mm / 5 mm / 7 mm element sizes) with zero manual re-clicking between runs.

<p align="center">
  <img src="media/fig8.1-camshaft-cad-model-two-lobes.jpg" width="500" alt="Camshaft CAD model, two lobes, SolidWorks">
</p>

---

## Contributors

| Name | USN |
|---|---|
| Akula Uday Kiran | 1RV23AS004 |
| Movva Sai Lalitha Devi | 1RV23AS030 |
| Shanthosh KV | 1RV23AS053 |
| **Tejas L** | 1RV23AS061 |

Guided by **Dr. Benjamin Rohit**, Dept. of Aerospace Engineering, RV College of Engineering.

> Note: All intellectual property generated in this project belongs to RV College of Engineering per the department's standard coursework declaration. This repository is published for portfolio/demonstration purposes.

---

## 🙋 My Contribution
 
This was a 4-person team project. Here's specifically what I owned:
 
| Area | What I Did |
|---|---|
| 🧩 **CAD Modeling** | Built the SolidWorks camshaft model, including the PSHELL/PSOLID property groupings the meshing automation depends on |
| 🖱️ **Conventional Meshing** | Learned and carried out manual, GUI-driven ANSA meshing first — this is what informed the API call sequence and quality-criteria choices scripted later |
| 🐍 **Phase 1 Scripting** | Wrote [`phase1_basic_meshing.py`](src/phase1_basic_meshing.py) end-to-end — validating the core ANSA API call sequence on a single mesh size |
| 🤖 **Phase 2 Scripting** | Contributed to the `MeshProcessor` class, using AI-assisted coding for part of the implementation, then reviewing and adapting it against my working Phase 1 logic |
| 📏 **Quality Criteria Tuning** | Configured and validated aspect ratio, skewness, Jacobian, and warpage thresholds against NASTRAN guidelines for this rotating-machinery component |
| 🔄 **Import / Export Pipeline** | Owned CAD/STEP import and NASTRAN-compatible mesh export across all three mesh sizes in the convergence study |
 
### Skills Learnt
 
![ANSA](https://img.shields.io/badge/-ANSA%20Meshing-2E7D32?style=flat&logoColor=white)
![ANSA API](https://img.shields.io/badge/-ANSA%20Python%20API-1565C0?style=flat&logoColor=white)
![Mesh Quality](https://img.shields.io/badge/-NASTRAN%20Mesh%20Quality-B71C1C?style=flat&logoColor=white)
![CAD](https://img.shields.io/badge/-SolidWorks%20CAD-455A64?style=flat&logoColor=white)
![AI-Assisted Dev](https://img.shields.io/badge/-AI--Assisted%20Development-6A1B9A?style=flat&logoColor=white)
 
- Structured/mapped-block meshing methodology in ANSA, moving from GUI-driven to fully scripted
- Tuning NASTRAN-specific mesh quality thresholds (aspect ratio, skewness, Jacobian, warpage) for a rotating-machinery component
- Reviewing and validating AI-suggested code against domain requirements, rather than using it as-is
- Translating a SolidWorks CAD model into ANSA-ready entities as the starting point for an automated pipeline
- **System integration** — making sure a CAD model built independently of the meshing scripts still fed cleanly into the automated pipeline without manual rework
- **Iterative validation across a team workflow** — tuning quality-criteria thresholds against results the rest of the team would consume downstream, not just against a spec sheet in isolation
- **Technical documentation** — writing up methodology and results in a way a teammate (or a future reader) could follow without re-deriving the reasoning
--- 
## Problem Statement

A camshaft converts rotational motion into the reciprocating motion that opens/closes engine valves via two cam lobes mounted on a cylindrical shaft. Preparing this geometry for FE analysis (structural or NVH) requires:

1. Clean shell + volume meshing of geometrically distinct regions (curved lobes vs. cylindrical shaft), each of which behaves differently under structured (mapped block) meshing
2. Element quality that satisfies NASTRAN solver thresholds (aspect ratio, skewness, warpage, Jacobian) simultaneously — optimizing for one metric in isolation can degrade another
3. Repeating this process across multiple element sizes for a mesh convergence study, where results must be comparable (i.e. generated under identical quality settings) across runs

Doing this by hand in ANSA's GUI for every mesh size is slow, non-reproducible, and error-prone — every re-run means re-clicking through the same 10+ menu operations, with no guarantee that quality settings stayed identical between runs. This project scripts the entire workflow using **ANSA's Python API** (`ansa.base`, `ansa.constants`, `ansa.mesh`), turning a manual GUI procedure into a deterministic, version-controllable pipeline.

---

## Architecture

The automation was built in two phases, each preserved in `src/`:

| | **Phase 1** — `phase1_basic_meshing.py` | **Phase 2** — `phase2_mesh_processor.py` |
|---|---|---|
| Structure | Flat procedural script | Object-oriented — `MeshProcessor` class |
| Scope | Single hardcoded mesh size (3 mm) | Batch over any list of mesh sizes |
| Config | Hardcoded paths & property IDs | Externalized into config dicts (paths, property IDs, quality thresholds, export settings) |
| Error handling | None — fails hard | `try/except` per mesh size; one failure doesn't kill the batch |
| Logging | None | Timestamped `INFO`/`ERROR` log file, per-step |
| Output naming | Fixed filename (overwritten each run) | Size-tagged filenames — no collisions across a batch |
| Reporting | None | End-of-run summary: success rate, timing, per-size output paths |
| Idempotency | Re-running overwrites the same `.cdb` silently | Each mesh size gets a traceable, uniquely named output — safe to re-run without data loss |

Phase 1 exists deliberately as a throwaway validation script — it answers "does this exact sequence of ANSA API calls produce a valid mesh at all?" before any engineering effort goes into making it reusable. Phase 2 is the production version.

### Workflow (both phases follow the same 5-stage pipeline)

```
STEP file import
      │
      ▼
Shell property retrieval (PSHELL) → Surface (FACE) entity collection
      │
      ▼
Mesh size configuration → Mapped block surface (shell) meshing
      │
      ▼
Solid property retrieval (PSOLID) → Volume entity collection
      │
      ▼
Volume mesh quality parameters → VolumesRemesh (quality-controlled solid meshing)
      │
      ▼
Export to NASTRAN-compatible .cdb
```

<p align="center">
  <img src="media/fig6.1-uml-workflow-diagram.png" width="700" alt="UML diagram of the ANSAMeshingWorkFlow class architecture">
  <br><sub>Fig — UML class diagram for the full <code>ANSAMeshingWorkFlow</code> workflow, showing <code>FileManager</code>, <code>EntityManager</code>, and <code>MeshManager</code> as supporting collaborators around the main orchestration class.</sub>
</p>

---

## Design Rationale

A few implementation choices are worth calling out explicitly, since they aren't obvious from the code alone:

- **Mapped block meshing (`mesh.MapBlock`) over free/unstructured meshing** — the camshaft's lobes and shaft are both geometrically regular (extruded/revolved profiles), which makes them good candidates for structured, block-mapped quad/hex meshing. This trades some automation flexibility (mapped block meshing is pickier about surface topology) for meshes with better element regularity and fewer transition elements than a free tetrahedral mesh would produce.
- **Absolute sizing over relative sizing** (`SetMeshParamTargetLength("absolute", mesh_size)`) — ensures the target edge length is identical in physical units (mm) across every element on the model, which is what a mesh convergence study needs: comparing element counts/results at *known, fixed* element sizes rather than sizes relative to local feature dimensions.
- **Aspect Ratio as the primary volume quality criterion** (`quality_criterion=3`, NASTRAN-specific metric) — NASTRAN solid elements are particularly sensitive to element stretching during solve; aspect ratio was prioritized over skewness/warpage/Jacobian as the *enforced* (strict, fail-on-violation) criterion, while the other three are monitored/reported but not gating.
- **`max_aspect_ratio = 2.3`** — tighter than the generic "acceptable" NASTRAN guideline (~3–5), chosen deliberately to leave headroom before the mesh approaches values that would matter for solver convergence, given this is a rotating-machinery component where stress concentrations at the lobe/shaft transition are analysis-critical.
- **Property-ID-based entity retrieval** (`PSHELL`/`PSOLID` IDs `1`–`5`) rather than name- or geometry-based lookup — simplest and fastest to implement given the CAD model's property IDs are fixed and known ahead of time. This is also the automation's main portability limitation (see [Limitations](#limitations--assumptions) below).

---

## Phase 1 — Basic Automation

A direct, linear script validating that the core ANSA API call sequence works for a single geometry and mesh size, before wrapping it in the Phase 2 framework. Full source: [`src/phase1_basic_meshing.py`](src/phase1_basic_meshing.py).

**Key API calls used:**

| Call | Purpose |
|---|---|
| `base.Open()` | Imports the STEP CAD geometry into the ANSA workspace |
| `base.GetEntity(deck, type, id)` | Retrieves a specific property entity (PSHELL/PSOLID) by ID |
| `base.CollectEntities(deck, entity, type)` | Collects all sub-entities (FACE/VOLUME) belonging to a property |
| `mesh.SetMeshParamTargetLength("absolute", size)` | Sets a fixed, global target element edge length |
| `mesh.MapBlock(entities)` | Generates a **structured** quad shell mesh via mapped block meshing |
| `mesh.VolumesParameters(criterion, level, metric, max_AR, strict)` | Configures the acceptance thresholds for volume mesh quality |
| `mesh.VolumesRemesh(volumes)` | Generates/refines the solid (hex/penta) volume mesh under those thresholds |
| `base.OutputAnsys(...)` | Exports the finished mesh to a NASTRAN-compatible `.cdb` |

The pipeline runs in a fixed 6-step sequence: CAD import → shell property + face retrieval → mapped block surface mesh → solid property + volume retrieval → quality-controlled volume remesh → export. Each step depends on ANSA entity IDs assigned by the earlier steps, so the sequence is order-sensitive — the volume mesh cannot be generated before the surface mesh exists, and export cannot run before both are complete.

---

## Phase 2 — Enhanced Automation

Full source: [`src/phase2_mesh_processor.py`](src/phase2_mesh_processor.py).

### `MeshProcessor` class

Encapsulates the identical pipeline as Phase 1, but every hardcoded value (STEP file path, property IDs, mesh sizing mode, quality thresholds, export settings) is pulled from a `config` dict supplied at construction — the class itself carries no hardcoded geometry- or project-specific values, which is what makes it reusable across mesh sizes without editing the class body.

### Batch processing + fault tolerance

The main block iterates over `TARGET_MESH_SIZES = [3.0, 5.0, 7.0]`, wrapping each mesh size in its own `try/except`, so a failure at one element size (e.g. an invalid negative size) is logged and skipped rather than aborting the entire convergence study. A `finally` block guarantees the log separator is written regardless of success or failure, keeping the log file's structure consistent and parseable even after a partial-failure run.

At the end of the run, a summary block reports success rate, per-size timing, and output file paths — turning the log into a self-contained audit trail of the whole batch, rather than requiring a human to scroll back through raw ANSA console output.

### Logging architecture

Logging is file-based (not console-only) and structured as `timestamp - level - message`, deliberately chosen over print statements for two reasons: ANSA batch/headless runs don't always have an attached console to capture stdout, and a persistent log file lets a convergence study be audited *after* the fact — which mesh sizes succeeded, how long each stage took, and exactly where and why a failure occurred — without needing to re-run anything.

### Error-handling validation

To prove the `try/except` scaffolding actually works (rather than simply never triggering), the team deliberately fed the script an invalid mesh size (`-3.0 mm`) alongside valid ones. Result: the script logged the geometry import and entity collection as normal, then failed cleanly at the `VOLUME MESH` menu switch, logged the error with timing and traceback, and — critically — **continued on to process the remaining valid mesh sizes** instead of crashing.

```
2025-07-01 10:19:26,915 - INFO  - Switched to VOLUME MESH menu - volume meshing tools are now active
2025-07-01 10:19:26,919 - ERROR - MESH SIZE -3.0 PROCESSING FAILED
2025-07-01 10:19:26,919 - ERROR - - Processing time before failure: 1.23 seconds
2025-07-01 10:19:26,920 - INFO  - Mesh size processing separator added to log file
```

A sample full run log (all three mesh sizes succeeding) is included at [`docs/sample_run_log.txt`](docs/sample_run_log.txt).

---

## Mesh Quality Methodology

Every generated mesh is scored in ANSA against four geometric quality metrics before being accepted:

| Metric | What it measures | Acceptable range |
|---|---|---|
| **Aspect Ratio** | Deviation from an ideal (square/cubic) element shape — ratio of longest edge to shortest altitude | < 3 good, < 5–10 marginal |
| **Skewness** | Deviation of element angles from equilateral/regular | < 0.5 good, < 0.85 critical |
| **Jacobian** | Element shape/volume distortion; the determinant relating local to global coordinates — negative = inverted element | > 0.7 good, > 0.6 acceptable |
| **Warpage** | Out-of-plane deviation of quad shell faces from planarity | < 0.5 good, < 0.85 critical |

`mesh.VolumesParameters(3, 2, "NASTRAN Aspect", 2.3, True)` enforces **Aspect Ratio** (criterion `3`) at quality level `2` ("Good") against a NASTRAN-specific metric, capped at `2.3`, with strict enforcement — meshing fails rather than silently emitting a poor element. Skewness, Jacobian, and Warpage are computed and reported by ANSA's quality panel for every run but are not set as hard gating criteria in `VolumesParameters` — they are validated post-hoc against the results (see below) rather than blocking mesh generation directly.

### Element formulation

| Property ID | Type | Region | Resulting solid element | Resulting shell element |
|---|---|---|---|---|
| PSHELL 1 | Shell | Lobes (curved surfaces) | — | CQUAD4 (structured, mapped block) |
| PSHELL 2 | Shell | Shaft (cylindrical surfaces) | — | CQUAD4 (structured, mapped block) |
| PSOLID 3 | Solid | Lobe 1 volume | CHEXA / CPENTA | — |
| PSOLID 4 | Solid | Lobe 2 volume | CHEXA / CPENTA | — |
| PSOLID 5 | Solid | Shaft volume | CHEXA / CPENTA | — |

Pentahedral (wedge) elements appear at the lobe-to-shaft transition regions where the structured hexahedral grid cannot maintain a pure hex topology across the geometry's curvature discontinuity — this is expected and standard practice in structured meshing of non-prismatic rotating components.

---

## Results — Mesh Convergence Study (3 mm / 5 mm / 7 mm)

<table>
<tr>
<td width="33%"><img src="media/fig8.3-structured-mesh-element-size-3.jpg" alt="3mm mesh"></td>
<td width="33%"><img src="media/fig8.9-structured-mesh-element-size-5.jpg" alt="5mm mesh"></td>
<td width="33%"><img src="media/fig8.14-structured-mesh-element-size-7.jpg" alt="7mm mesh"></td>
</tr>
<tr>
<td align="center">3 mm — 64,071 volume elems</td>
<td align="center">5 mm — 15,356 volume elems</td>
<td align="center">7 mm — 5,352 volume elems</td>
</tr>
</table>

### Element counts

| Mesh Size | Shell (Quad/Tri) | Shell Total | Volume (Hexa/Penta) | Volume Total |
|---|---|---|---|---|
| 3 mm | 16,428 / 228 | 16,656 | 62,309 / 1,762 | 64,071 |
| 5 mm | 6,016 / 144 | 6,160 | 14,612 / 744 | 15,356 |
| 7 mm | 3,168 / 104 | 3,272 | 4,920 / 432 | 5,352 |

### Convergence trend

Going from 3 mm → 5 mm → 7 mm element edge length reduces the total volume element count by roughly **76% then 65%** at each step — consistent with the expected cubic (∝ 1/size³) scaling of element count with element size for a fixed-volume 3D solid, since halving the edge length roughly doubles element density along each axis. This is a useful sanity check when validating that the automation is actually respecting the requested target size rather than silently defaulting to a coarser mesh.

### Quality checks per mesh size

| Mesh Size | Aspect Ratio (min–max) | Skewness (min–max) | Jacobian, solids (min–max) | Warpage (min–max) |
|---|---|---|---|---|
| 3 mm | 1.00 (uniform) | 1.20 (avg) | 0.835 – 1.000 | 1.00 (ideal) |
| 5 mm | 1.018 – 1.654 | 0.0029 – 0.4766 | 0.977 – 1.000 | 0.0034 – 0.4299 |
| 7 mm | 1.018 – 1.654 | 0.0029 – 0.4766 | 0.825 – 1.000 | 1.00 (ideal) |

<table>
<tr><td><img src="media/fig8.4-element-size-3-aspect-ratio.jpg" alt="Elem 3 AR"></td>
<td><img src="media/fig8.8-element-size-3-jacobian.jpg" alt="Elem 3 Jacobian"></td></tr>
<tr><td align="center">Element size 3 — Aspect Ratio (all elements ideal, AR = 1.00)</td>
<td align="center">Element size 3 — Jacobian (0.835–1.0, high geometric accuracy)</td></tr>
</table>

<table>
<tr><td><img src="media/fig8.10-element-size-5-aspect-ratio.jpg" alt="Elem 5 AR"></td>
<td><img src="media/fig8.15-element-size-7-aspect-ratio.jpg" alt="Elem 7 AR"></td></tr>
<tr><td align="center">Element size 5 — Aspect Ratio (green band, 1.02–1.65)</td>
<td align="center">Element size 7 — Aspect Ratio (green-blue band, no red/critical elements)</td></tr>
</table>

All three mesh densities cleared every NASTRAN quality gate with no negative-Jacobian (inverted) elements and no elements flagged for critical skewness or warpage — see [`docs/quality-check-reference-table.md`](docs/quality-check-reference-table.md) for the full ANSA quality-criteria configuration (`fig8.5-ideal-mesh-quality-check-table.jpg`). Note that the coarsest mesh (7 mm) does **not** show materially worse quality metrics than the finest (3 mm) — this is a direct consequence of mapped block (structured) meshing preserving element regularity across sizes, unlike free/unstructured meshing where coarsening typically degrades quality near curved features.

### Final production mesh (used for downstream FE analysis)

| Element Type | Count |
|---|---|
| Hexahedral (solid) | 29,020 |
| Pentahedral (solid) | 332 |
| **Total solid elements** | **29,352** |
| Quad (shell) | 9,630 |
| Tri (shell) | 24 |

- **98.9%** hexahedral — favorable for numerical accuracy, convergence, and low numerical diffusion vs. tetrahedral-dominated meshes
- Max skewness (NASTRAN standard): **1.23** (well under the 2.0 threshold)
- Max aspect ratio: **8.5** — acceptable for structural analysis, though above the stricter 3–5 mm-scale convergence-study values, reflecting the coarser final production mesh sizing
- Squish and collapse metrics reported no critical failures — no degenerate or self-intersecting elements in the final mesh

<p align="center">
  <img src="media/fig8.19-final-mesh-jacobian-quality.jpg" width="600" alt="Final mesh Jacobian quality plot">
</p>

---

## Performance

| Mesh Size | Shell + Volume Mesh Time | Export Time | Total | Output File Size |
|---|---|---|---|---|
| 3 mm | 5.56 s | 0.41 s | 5.97 s | 18.85 MB |
| 5 mm | 2.76 s | 0.13 s | 2.89 s | 4.89 MB |
| 7 mm | 2.42 s | 0.06 s | 2.48 s | 1.90 MB |

Full 3-size batch: **~11.4 seconds** end-to-end (excludes ANSA GUI/license startup). Export time scales roughly linearly with element count (and therefore output file size), while meshing time scales sub-linearly — most of the fixed per-run overhead (geometry import, property retrieval) is size-independent.

---

## Sample Log Output (Phase 2, successful 3-size batch)

```
2025-07-01 10:16:37,631 - INFO - ANSA MESH PROCESSING SCRIPT STARTED
2025-07-01 10:16:37,632 - INFO - Target mesh sizes for processing: [3.0, 5.0, 7.0]
2025-07-01 10:16:37,632 - INFO - STARTING MESH SIZE PROCESSING (1/3)
2025-07-01 10:16:39,549 - INFO - Successfully opened STEP file: CAM_SHAFT.STEP
2025-07-01 10:16:41,923 - INFO - Successfully generated mapped block mesh for lobe components
2025-07-01 10:16:42,840 - INFO - Successfully remeshed first lobe volume (lob1)
2025-07-01 10:16:43,190 - INFO - Mesh processing workflow completed successfully for mesh size 3.0 mm
2025-07-01 10:16:43,598 - INFO - Model export operation completed successfully
2025-07-01 10:16:43,603 - INFO - MESH SIZE 3.0 PROCESSING COMPLETED SUCCESSFULLY
...
2025-07-01 10:16:48,991 - INFO - Successfully processed 3 mesh sizes: [3.0, 5.0, 7.0]
2025-07-01 10:16:49,003 - INFO - ALL MESH SIZES PROCESSED SUCCESSFULLY - SCRIPT COMPLETED WITHOUT ERRORS
```

---

## Repository Structure

```
camshaft-mesh-automation-ansa-python/
├── README.md
├── src/
│   ├── phase1_basic_meshing.py     # Basic single-size procedural script
│   └── phase2_mesh_processor.py    # OOP, config-driven, batch + logging
├── media/                          # Renders, quality plots, UML diagram
└── docs/
    ├── sample_run_log.txt          # Full log from a successful 3-size batch
    └── quality-check-reference-table.md
```

---

## Tech Stack

- **ANSA** (BETA CAE Systems) — CAE pre-processing / meshing environment
- **ANSA Python API** (`ansa.base`, `ansa.constants`, `ansa.mesh`) — scripting interface
- **Python** standard library — `logging`, `os`, `uuid`, `time`
- **NASTRAN** — target solver deck for property definitions and mesh export

## Requirements

- ANSA (BETA CAE Systems) with a valid license and Python scripting enabled
- Python 3.x (ANSA's embedded interpreter)
- A STEP/IGES camshaft assembly with PSHELL/PSOLID properties pre-assigned to lobe and shaft regions

## Running

From within ANSA's Python scripting console/shell, or via ANSA batch mode:

```bash
ansa -b -exec "python3 src/phase2_mesh_processor.py"
```

Edit the `PATHS_CONFIG`, `PROPERTY_CONFIG`, and `TARGET_MESH_SIZES` blocks at the bottom of `phase2_mesh_processor.py` to point at your own STEP file, property IDs, and desired mesh sizes.

## Limitations & Assumptions

- **Fixed property IDs**: the script assumes `PSHELL` IDs `1`/`2` and `PSOLID` IDs `3`/`4`/`5` are stable across re-exports of the CAD model. A CAD revision that changes ANSA's auto-assigned property numbering would require updating `PROPERTY_CONFIG` (or extending the script to resolve properties by name instead of ID).
- **Geometry-specific mapped blocking**: `mesh.MapBlock` requires clean, block-mappable surface topology. The automation does not include geometry repair/cleanup logic — it assumes the STEP file is already watertight and free of the small gaps/slivers that commonly break structured meshing.
- **Single component family**: the workflow is written for this specific two-lobe camshaft topology (2 shell properties, 3 solid properties). Extending it to camshafts with a different lobe count would require generalizing the property-ID lists into a loop rather than hardcoded named variables.
- **ANSA license / GUI dependency**: requires a licensed ANSA installation; not runnable as a standalone open-source Python package.

## Future Enhancements

- Adaptive mesh refinement based on local geometric curvature/complexity
- Resolving PSHELL/PSOLID entities by name rather than fixed ID, for robustness across CAD re-exports
- Extending the `MeshProcessor` config schema to support additional automotive/rotating-machinery components beyond the camshaft
- Coupling `TARGET_MESH_SIZES` selection with an optimization loop (DOE-driven) instead of a fixed list
- Cloud/headless batch execution for large-scale parametric studies
