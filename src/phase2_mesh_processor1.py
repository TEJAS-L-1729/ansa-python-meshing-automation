"""
Phase 2 - Enhanced ANSA Meshing Automation
=============================================
Object-oriented, batch-capable, and fault-tolerant rewrite of Phase 1.

Key upgrades over Phase 1:
    - MeshProcessor class encapsulates the full workflow (reusable, extensible)
    - Config-driven parameters (paths, property IDs, quality thresholds, export
      settings) instead of hardcoded values, so the script adapts to new
      geometries/solvers without touching the workflow logic
    - Multi-scale batch processing across a list of target mesh sizes, enabling
      mesh convergence / sensitivity studies in a single run
    - Structured logging (timestamped INFO/ERROR) to file, capturing every
      step's success/failure and timing
    - try/except error recovery per mesh size so one bad configuration does
      not kill the whole batch
    - UUID / size-tagged output filenames to avoid collisions across runs

Reference: RVCE AS244AI Experiential Learning Report, Section 6.3 / Appendix 8.6.2.
"""

import os
import ansa
import logging
import uuid
import time
from ansa import base, constants, mesh

# ============================================================================
# SOLVER CONFIGURATION
# ============================================================================
deck = constants.NASTRAN


class MeshProcessor:
    """
    Encapsulates the complete workflow of importing CAD geometry, generating
    finite element meshes, and preparing models for NASTRAN analysis in ANSA.

    Responsibilities:
        - CAD geometry import (STEP files)
        - Surface mesh generation (shell elements, mapped block meshing)
        - Volume mesh generation (solid elements, quality-controlled)
        - Property/entity management (PSHELL, PSOLID, FACE, VOLUME)

    Designed to be instantiated once and invoked per mesh size via `main()`,
    with all tunables (paths, property IDs, quality thresholds) supplied
    through a config dict at construction time.
    """

    def __init__(self, config):
        self.config = config

    def main(self, mesh_size):
        """
        Executes the complete meshing workflow for a single target element size.

        Steps: CAD import -> shell property/entity retrieval -> mesh param
        setup -> mapped block surface meshing -> solid property/entity
        retrieval -> volume quality parameters -> volume remeshing.

        Args:
            mesh_size (float): target element edge length in mm.
        """
        logging.info("-----------------------------------")
        logging.info(f"Starting mesh processing workflow for mesh size {mesh_size} mm.")
        logging.info(f"Target element size: {mesh_size}")

        # --- STEP 1: CAD geometry import ---
        step_file = self.config["input_paths"]["step_file"]
        base.Open(step_file)
        logging.info(f"Successfully opened STEP file: {step_file}")

        # --- STEP 2: Shell property retrieval ---
        lobes = base.GetEntity(deck, "PSHELL", self.config["property_ids"]["pshell_lobes"])
        shaft = base.GetEntity(deck, "PSHELL", self.config["property_ids"]["pshell_shaft"])
        logging.info("Retrieved PSHELL entities for lobes and shaft")

        # --- STEP 3: Surface entity collection ---
        ents1 = base.CollectEntities(deck, lobes, "FACE")
        ents2 = base.CollectEntities(deck, shaft, "FACE")
        logging.info(f"- Lobe faces collected: {len(ents1) if ents1 else 0}")
        logging.info(f"- Shaft faces collected: {len(ents2) if ents2 else 0}")

        # --- STEP 4: Meshing environment + sizing setup ---
        base.SetCurrentMenu("VOLUME MESH")
        mesh.SetMeshParamTargetLength(
            self.config["mesh_parameters"]["sizing_mode"], mesh_size
        )
        mesh.CreateBestMesh()
        logging.info(f"Mesh sizing configured: {mesh_size} mm ({self.config['mesh_parameters']['sizing_mode']})")

        # --- STEP 5: Surface (shell) mesh generation ---
        mesh.MapBlock(ents1)
        logging.info("Generated mapped block mesh for lobe components")
        mesh.MapBlock(ents2)
        logging.info("Generated mapped block mesh for shaft components")

        # --- STEP 6: Solid property retrieval ---
        lob1 = base.GetEntity(deck, "PSOLID", self.config["property_ids"]["psolid_lob1"])
        lob2 = base.GetEntity(deck, "PSOLID", self.config["property_ids"]["psolid_lob2"])
        shaft1 = base.GetEntity(deck, "PSOLID", self.config["property_ids"]["psolid_shaft"])
        logging.info("Retrieved PSOLID entities for lob1, lob2, shaft1")

        # --- STEP 7: Volume entity collection ---
        vol1 = base.CollectEntities(deck, lob1, "VOLUME")
        vol2 = base.CollectEntities(deck, lob2, "VOLUME")
        vol3 = base.CollectEntities(deck, shaft1, "VOLUME")
        logging.info(
            f"Collected VOLUME entities - lob1: {len(vol1) if vol1 else 0}, "
            f"lob2: {len(vol2) if vol2 else 0}, shaft: {len(vol3) if vol3 else 0}"
        )

        # --- STEP 8: Volume mesh quality parameters ---
        qp = self.config["mesh_parameters"]["quality_control"]
        mesh.VolumesParameters(
            qp["quality_criterion"],
            qp["quality_level"],
            qp["solver_metric"],
            qp["max_aspect_ratio"],
            qp["strict_enforcement"],
        )
        logging.info(
            f"Quality params - criterion: {qp['quality_criterion']}, "
            f"metric: {qp['solver_metric']}, max AR: {qp['max_aspect_ratio']}, "
            f"strict: {qp['strict_enforcement']}"
        )

        # --- STEP 9: Volume mesh generation / refinement ---
        mesh.VolumesRemesh(vol1)
        logging.info("Remeshed lob1 volume")
        mesh.VolumesRemesh(vol2)
        logging.info("Remeshed lob2 volume")
        mesh.VolumesRemesh(vol3)
        logging.info("Remeshed shaft1 volume")

        logging.info(f"Mesh processing workflow completed for mesh size {mesh_size} mm")


def export_meshed_file(output_path, export_config):
    """
    Exports the completed meshed model to a solver-compatible file.

    Args:
        output_path (str): full path for the output file.
        export_config (dict): mode / version / workbench_compatible /
            element_thickness_output / format settings.
    """
    try:
        base.OutputAnsys(
            filename=output_path,
            mode=export_config["mode"],
            version=export_config["version"],
            workbench_compatible=export_config["workbench_compatible"],
            output_element_thickness=export_config["element_thickness_output"],
        )
        logging.info("Model export operation completed successfully")
        logging.info(f"- Output file: {output_path}")
        logging.info(f"- Export format: {export_config['format']}")

        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            logging.info(f"- File size: {file_size:,} bytes ({file_size / 1024 / 1024:.2f} MB)")

    except Exception as e:
        logging.error(f"Export operation failed: {str(e)}")
        raise


def setup_logging(log_config):
    """Configures the timestamped file logging system."""
    logging.basicConfig(
        filename=log_config["log_file_path"],
        filemode=log_config["file_mode"],
        level=getattr(logging, log_config["log_level"]),
        format=log_config["log_format"],
    )


def finalize_log(log_path):
    """Appends a completion marker to the log file at the end of the run."""
    try:
        with open(log_path, "a") as f:
            f.write("\n" + "-" * 80 + "\n")
            f.write("SCRIPT EXECUTION COMPLETED - END OF LOG FILE\n")
            f.write("-" * 80 + "\n")
        logging.info("Log file successfully finalized")
    except IOError as e:
        logging.error(f"Failed to finalize log file due to I/O error: {str(e)}")
    except Exception as e:
        logging.error(f"Unexpected error during log finalization: {str(e)}")


def log_mesh_size_separator(log_path):
    """Appends a separator marking completion of one mesh size's processing."""
    try:
        with open(log_path, "a") as f:
            f.write("\n" + "-" * 60 + "\n")
            f.write("MESH SIZE PROCESSING COMPLETED\n")
            f.write("-" * 60 + "\n")
        logging.info("Mesh size processing separator added to log file")
    except IOError as e:
        logging.error(f"Failed to append mesh size separator to log file: {str(e)}")
    except Exception as e:
        logging.error(f"Unexpected error while adding mesh size separator: {str(e)}")


def generate_output_filename(output_config, mesh_size):
    """Builds a unique, traceable output filename per mesh size."""
    filename = f"{output_config['filename_prefix']}{mesh_size}{output_config['file_extension']}"
    return os.path.join(output_config["output_directory"], filename)


# ============================================================================
# MAIN SCRIPT EXECUTION BLOCK
# ============================================================================
if __name__ == "__main__":

    # ---- LOGGING CONFIGURATION ----
    LOGGING_CONFIG = {
        "log_file_path": r"<path-to>/ansa_mesh_log.txt",
        "file_mode": "w",          # 'w' = overwrite, 'a' = append
        "log_level": "INFO",       # DEBUG, INFO, WARNING, ERROR, CRITICAL
        "log_format": "%(asctime)s - %(levelname)s - %(message)s",
    }

    # ---- INPUT / OUTPUT PATHS ----
    PATHS_CONFIG = {
        "input_paths": {"step_file": r"<path-to>/CAM_SHAFT.STEP"},
        "output_paths": {
            "output_directory": r"<path-to>/Mesh",
            "filename_prefix": "meshsize",
            "file_extension": ".cdb",
        },
    }

    # ---- PROPERTY IDs (PSHELL / PSOLID) ----
    PROPERTY_CONFIG = {
        "property_ids": {
            "pshell_lobes": 1,
            "pshell_shaft": 2,
            "psolid_lob1": 3,
            "psolid_lob2": 4,
            "psolid_shaft": 5,
        }
    }

    # ---- MESH SIZING + QUALITY CONTROL ----
    MESH_CONFIG = {
        "mesh_parameters": {
            "sizing_mode": "absolute",
            "quality_control": {
                "quality_criterion": 3,          # 1=Jacobian, 2=Skewness, 3=Aspect Ratio, 4=Warpage
                "quality_level": 2,               # 1=poor, 2=good, 3=excellent
                "solver_metric": "NASTRAN Aspect",
                "max_aspect_ratio": 2.3,
                "strict_enforcement": True,
            },
        }
    }

    # ---- EXPORT SETTINGS ----
    EXPORT_CONFIG = {
        "mode": "all",
        "version": "All",
        "workbench_compatible": "on",
        "element_thickness_output": "per_element",
        "format": "ANSYS CDB format",
    }

    # ---- TARGET MESH SIZES FOR BATCH / CONVERGENCE STUDY ----
    TARGET_MESH_SIZES = [3.0, 5.0, 7.0]

    FULL_CONFIG = {**PATHS_CONFIG, **PROPERTY_CONFIG, **MESH_CONFIG}
    setup_logging(LOGGING_CONFIG)

    logging.info("=" * 80)
    logging.info("ANSA MESH PROCESSING SCRIPT STARTED")
    logging.info("=" * 80)
    logging.info(f"Target mesh sizes for processing: {TARGET_MESH_SIZES}")

    processor = MeshProcessor(FULL_CONFIG)
    successful_meshes = []
    failed_meshes = []
    script_start_time = time.time()

    for mesh_index, mesh_size in enumerate(TARGET_MESH_SIZES, 1):
        mesh_start_time = time.time()
        output_file = generate_output_filename(PATHS_CONFIG["output_paths"], mesh_size)

        logging.info(f"STARTING MESH SIZE PROCESSING ({mesh_index}/{len(TARGET_MESH_SIZES)})")
        print(f"\n{'=' * 60}\nProcessing mesh size {mesh_index}/{len(TARGET_MESH_SIZES)}: {mesh_size} mm\n{'=' * 60}")

        try:
            processor.main(mesh_size)
            mesh_process_time = time.time() - mesh_start_time
            logging.info(f"Meshing completed in {mesh_process_time:.2f}s for mesh size {mesh_size}")

            output_dir = os.path.dirname(output_file)
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            export_start_time = time.time()
            export_meshed_file(output_file, EXPORT_CONFIG)
            export_time = time.time() - export_start_time

            successful_meshes.append(mesh_size)
            total_mesh_time = time.time() - mesh_start_time
            logging.info(f"MESH SIZE {mesh_size} PROCESSING COMPLETED SUCCESSFULLY")
            logging.info(f"- Total: {total_mesh_time:.2f}s | Mesh: {mesh_process_time:.2f}s | Export: {export_time:.2f}s")
            logging.info(f"- Output file size: {os.path.getsize(output_file):,} bytes")

        except Exception as e:
            error_time = time.time() - mesh_start_time
            print(f"ERROR: Failed to process mesh size {mesh_size} mm - {str(e)}")
            logging.error(f"MESH SIZE {mesh_size} PROCESSING FAILED")
            logging.error(f"- Processing time before failure: {error_time:.2f}s")
            logging.error(f"- Error type: {type(e).__name__}")
            logging.error(f"- Error message: {str(e)}")
            logging.error("- Full error traceback:", exc_info=True)
            failed_meshes.append(mesh_size)

        finally:
            log_mesh_size_separator(LOGGING_CONFIG["log_file_path"])

    # ---- FINAL SUMMARY ----
    total_script_time = time.time() - script_start_time
    success_rate = (len(successful_meshes) / len(TARGET_MESH_SIZES)) * 100

    logging.info("=" * 80)
    logging.info("FINAL PROCESSING SUMMARY")
    logging.info("=" * 80)
    logging.info(f"Successfully processed: {len(successful_meshes)}/{len(TARGET_MESH_SIZES)} ({success_rate:.1f}%)")
    logging.info(f"Failed: {failed_meshes}")
    logging.info(f"Total script execution time: {total_script_time:.2f}s ({total_script_time / 60:.1f} min)")

    finalize_log(LOGGING_CONFIG["log_file_path"])

    if len(successful_meshes) == len(TARGET_MESH_SIZES):
        print("\nALL MESH SIZES PROCESSED SUCCESSFULLY")
    elif successful_meshes:
        print(f"\nPARTIAL SUCCESS: {len(successful_meshes)}/{len(TARGET_MESH_SIZES)} completed")
    else:
        print("\nALL MESH PROCESSING FAILED - CHECK LOG FILE")
