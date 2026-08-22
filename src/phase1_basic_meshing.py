"""
Phase 1 - Basic ANSA Meshing Automation
=========================================
Establishes the fundamental meshing workflow for the camshaft (2 lobes + shaft).
Targets NASTRAN as the export solver format. This script is intentionally
minimal: no logging, no batching, no error recovery. It exists to validate
that the core ANSA Python API call sequence (import -> shell mesh -> volume
mesh -> quality control -> export) works end-to-end for a single mesh size
before Phase 2 wraps it in a production-grade automation framework.

Reference: RVCE AS244AI Experiential Learning Report, Section 6.2 / Appendix 8.5.
"""

import os
import ansa
from ansa import *

# Target solver deck for property/entity lookups and export format
deck = constants.NASTRAN


def main():
    # ------------------------------------------------------------------
    # 1. CAD geometry import
    # ------------------------------------------------------------------
    base.Open("<path-to>/input.STEP")

    # ------------------------------------------------------------------
    # 2. Shell property retrieval + surface entity collection
    # ------------------------------------------------------------------
    lobes = base.GetEntity(deck, "PSHELL", 1)   # complex curved lobe surfaces
    shaft = base.GetEntity(deck, "PSHELL", 2)   # cylindrical shaft surfaces
    ents1 = base.CollectEntities(deck, lobes, "FACE")
    ents2 = base.CollectEntities(deck, shaft, "FACE")

    # ------------------------------------------------------------------
    # 3. Surface (shell) mesh generation - mapped block meshing
    # ------------------------------------------------------------------
    base.SetCurrentMenu("VOLUME MESH")
    mesh.SetMeshParamTargetLength("absolute", 3)   # 3 mm target element edge length
    mesh.MapBlock(ents1)
    mesh.MapBlock(ents2)

    # ------------------------------------------------------------------
    # 4. Solid property retrieval + volume entity collection
    # ------------------------------------------------------------------
    lob1 = base.GetEntity(deck, "PSOLID", 3)    # first lobe volume
    lob2 = base.GetEntity(deck, "PSOLID", 4)    # second lobe volume
    shaft1 = base.GetEntity(deck, "PSOLID", 5)  # shaft volume
    vol1 = base.CollectEntities(deck, lob1, "VOLUME")
    vol2 = base.CollectEntities(deck, lob2, "VOLUME")
    vol3 = base.CollectEntities(deck, shaft1, "VOLUME")

    # ------------------------------------------------------------------
    # 5. Volume mesh generation with quality control
    #    criterion=3 (Aspect Ratio), level=2 (Good), max AR=2.3, strict=True
    # ------------------------------------------------------------------
    mesh.VolumesParameters(3, 2, "NASTRAN Aspect", 2.3, True)
    mesh.VolumesRemesh(vol1)
    mesh.VolumesRemesh(vol2)
    mesh.VolumesRemesh(vol3)

    # ------------------------------------------------------------------
    # 6. Export to NASTRAN-compatible .cdb
    # ------------------------------------------------------------------
    base.OutputAnsys(
        filename="<path-to>/output.cdb",
        mode="custom_mv_container",
        version="All",
        workbench_compatible="on",
        output_element_thickness="per_element",
    )


if __name__ == "__main__":
    main()
