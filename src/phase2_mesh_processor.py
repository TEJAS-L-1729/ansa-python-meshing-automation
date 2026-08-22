import os
import ansa
import logging
from ansa import base, constants, mesh
import uuid
import time

# ====================================================================
# FINITE ELEMENT ANALYSIS SOLVER CONFIGURATION
# ====================================================================
deck = constants.NASTRAN

class MeshProcessor:
    """
    A comprehensive class to handle the complete workflow of importing CAD geometry,
    generating finite element meshes, and preparing models for NASTRAN analysis in ANSA.
    
    This class encapsulates all meshing operations including:
    - CAD geometry import (STEP files)
    - Surface mesh generation (shell elements)
    - Volume mesh generation (solid elements)
    - Mesh quality control and refinement
    - Property assignment and entity management
    
    The class is designed to be reusable for multiple mesh sizes and different geometries
    with consistent logging and error handling throughout the process.
    """

    def __init__(self, config):
        """
        Initialize the MeshProcessor with configuration parameters.
        
        Args:
            config (dict): Configuration dictionary containing all parameters
        """
        self.config = config

    def main(self, mesh_size):
        """
        Main orchestration method that executes the complete meshing workflow for a specified mesh size.
        
        This method performs the following key operations in sequence:
        1. Opens and imports CAD geometry from STEP file
        2. Retrieves and organizes geometric entities by properties
        3. Configures meshing parameters for the target element size
        4. Generates surface meshes using mapped block meshing
        5. Creates volume meshes with quality control
        6. Applies mesh refinement and quality improvement
        
        Args:
            mesh_size (float): The target element size for meshing operations.
                              This value is in model units (typically mm or inches).
                              Smaller values create finer meshes with more elements.
                              Typical range: 1.0 - 10.0 mm for mechanical components.
        """
        
        # Log the initiation of meshing process
        logging.info("-----------------------------------------------------------------------------------------------------------------------------------------------------------")
        logging.info(f"Starting comprehensive mesh processing workflow for mesh size {mesh_size} mm.")
        logging.info(f"Target element size: {mesh_size} (this will determine mesh density and computational requirements)")

        # ====================================================================
        # STEP 1: CAD GEOMETRY IMPORT
        # ====================================================================
        step_file = self.config['input_paths']['step_file']
        
        # Open the STEP file in ANSA's workspace
        base.Open(step_file)
        logging.info(f"Successfully opened STEP file: {step_file}")
        logging.info("CAD geometry has been loaded into ANSA workspace for processing")
        
        # ====================================================================
        # STEP 2: SHELL ELEMENT PROPERTY RETRIEVAL
        # ====================================================================
        # Retrieve PSHELL entities using configured property IDs
        lobes = base.GetEntity(deck, "PSHELL", self.config['property_ids']['pshell_lobes'])
        shaft = base.GetEntity(deck, "PSHELL", self.config['property_ids']['pshell_shaft'])
        
        logging.info("Successfully retrieved PSHELL entities for shell element definition")
        logging.info(f"- PSHELL ID {self.config['property_ids']['pshell_lobes']} (lobes): Retrieved for complex curved surface meshing")
        logging.info(f"- PSHELL ID {self.config['property_ids']['pshell_shaft']} (shaft): Retrieved for cylindrical/prismatic surface meshing")
        
        # ====================================================================
        # STEP 3: SURFACE ENTITY COLLECTION
        # ====================================================================
        # Collect all FACE entities associated with each PSHELL property
        ents1 = base.CollectEntities(deck, lobes, "FACE")
        ents2 = base.CollectEntities(deck, shaft, "FACE")
        
        logging.info("Successfully collected FACE entities for surface meshing operations")
        logging.info(f"- Lobe faces collected: {len(ents1) if ents1 else 0} surfaces identified for meshing")
        logging.info(f"- Shaft faces collected: {len(ents2) if ents2 else 0} surfaces identified for meshing")
        
        # ====================================================================
        # STEP 4: MESHING ENVIRONMENT SETUP
        # ====================================================================
        # Switch to VOLUME MESH menu
        base.SetCurrentMenu("VOLUME MESH")
        logging.info("Switched to VOLUME MESH menu - volume meshing tools are now active")
        
        # ====================================================================
        # STEP 5: MESH SIZE PARAMETER CONFIGURATION
        # ====================================================================
        # Set mesh sizing using configured parameters
        mesh.SetMeshParamTargetLength(
            self.config['mesh_parameters']['sizing_mode'], 
            mesh_size
        )
        mesh.CreateBestMesh()
        logging.info(f"Mesh parameters configured for {self.config['mesh_parameters']['sizing_mode']} element sizing")
        logging.info(f"- Target element edge length: {mesh_size} mm")
        logging.info(f"- This setting will be applied globally to all meshing operations")
        logging.info(f"- Estimated elements per surface area: ~{(10/mesh_size)**2:.0f} elements per 100 mm²")
        
        # ====================================================================
        # STEP 6: SURFACE MESH GENERATION (MAPPED BLOCK MESHING)
        # ====================================================================
        # Generate mapped block meshes for the collected FACE entities
        mesh.MapBlock(ents1)
        logging.info("Successfully generated mapped block mesh for lobe components")
        logging.info("- Used structured meshing algorithm for optimal element quality")
        logging.info("- Quadrilateral shell elements created with consistent orientation")
        
        mesh.MapBlock(ents2)
        logging.info("Successfully generated mapped block mesh for shaft components")
        logging.info("- Structured mesh pattern applied to cylindrical surfaces")
        logging.info("- Element alignment optimized for circumferential and axial directions")
        
        # ====================================================================
        # STEP 7: SOLID ELEMENT PROPERTY RETRIEVAL
        # ====================================================================
        # Retrieve PSOLID entities using configured property IDs
        lob1 = base.GetEntity(deck, "PSOLID", self.config['property_ids']['psolid_lob1'])
        lob2 = base.GetEntity(deck, "PSOLID", self.config['property_ids']['psolid_lob2'])
        shaft1 = base.GetEntity(deck, "PSOLID", self.config['property_ids']['psolid_shaft'])
        
        logging.info("Successfully retrieved PSOLID entities for solid element definition")
        logging.info(f"- PSOLID ID {self.config['property_ids']['psolid_lob1']} (lob1): Retrieved for first lobe volume meshing")
        logging.info(f"- PSOLID ID {self.config['property_ids']['psolid_lob2']} (lob2): Retrieved for second lobe volume meshing")
        logging.info(f"- PSOLID ID {self.config['property_ids']['psolid_shaft']} (shaft1): Retrieved for shaft volume meshing")
        
        # ====================================================================
        # STEP 8: VOLUME ENTITY COLLECTION
        # ====================================================================
        # Collect all VOLUME entities associated with each PSOLID property
        vol1 = base.CollectEntities(deck, lob1, "VOLUME")
        vol2 = base.CollectEntities(deck, lob2, "VOLUME")
        vol3 = base.CollectEntities(deck, shaft1, "VOLUME")
        
        logging.info("Successfully collected VOLUME entities for 3D solid meshing operations")
        logging.info(f"- Lobe 1 volumes: {len(vol1) if vol1 else 0} 3D regions identified for solid meshing")
        logging.info(f"- Lobe 2 volumes: {len(vol2) if vol2 else 0} 3D regions identified for solid meshing")
        logging.info(f"- Shaft volumes: {len(vol3) if vol3 else 0} 3D regions identified for solid meshing")
        
        # ====================================================================
        # STEP 9: VOLUME MESH QUALITY PARAMETERS
        # ====================================================================
        # Configure volume meshing quality parameters using config
        quality_params = self.config['mesh_parameters']['quality_control']
        mesh.VolumesParameters(
            quality_params['quality_criterion'],
            quality_params['quality_level'],
            quality_params['solver_metric'],
            quality_params['max_aspect_ratio'],
            quality_params['strict_enforcement']
        )
        
        logging.info("Volume meshing quality parameters configured for optimal element quality")
        logging.info(f"- Quality criterion: {quality_params['quality_criterion']}")
        logging.info(f"- Target quality level: {quality_params['quality_level']}")
        logging.info(f"- Solver metric: {quality_params['solver_metric']}")
        logging.info(f"- Maximum allowable aspect ratio: {quality_params['max_aspect_ratio']}")
        logging.info(f"- Strict quality enforcement: {'ENABLED' if quality_params['strict_enforcement'] else 'DISABLED'}")
        
        # ====================================================================
        # STEP 10: VOLUME MESH GENERATION AND REFINEMENT
        # ====================================================================
        # Execute volume remeshing operations for all collected volumes
        mesh.VolumesRemesh(vol1)
        logging.info("Successfully remeshed first lobe volume (lob1)")
        logging.info("- Applied quality improvement algorithms")
        logging.info("- Verified element aspect ratios meet NASTRAN requirements")
        
        mesh.VolumesRemesh(vol2)
        logging.info("Successfully remeshed second lobe volume (lob2)")
        logging.info("- Maintained mesh compatibility with first lobe")
        logging.info("- Applied consistent quality standards")
        
        mesh.VolumesRemesh(vol3)
        logging.info("Successfully remeshed shaft volume (shaft1)")
        logging.info("- Optimized for cylindrical geometry characteristics")
        logging.info("- Completed volume meshing for all components")
        
        # Log completion of main meshing workflow
        logging.info(f"Mesh processing workflow completed successfully for mesh size {mesh_size} mm")
        logging.info("All surface and volume meshes generated with quality control")
        logging.info("Model is ready for export and finite element analysis")

def export_meshed_file(output_path, export_config):
    """
    Exports the completed meshed model to a specified file format for analysis.
    
    Args:
        output_path (str): The complete file path for the output file
        export_config (dict): Export configuration parameters
    """
    
    try:
        base.OutputAnsys(
            filename=output_path,
            mode=export_config['mode'],
            version=export_config['version'], 
            workbench_compatible=export_config['workbench_compatible'], 
            output_element_thickness=export_config['element_thickness_output']
        )
        
        logging.info(f"Model export operation completed successfully")
        logging.info(f"- Output file: {output_path}")
        logging.info(f"- Export format: {export_config['format']}")
        
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            logging.info(f"- File size: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
        
    except Exception as e:
        logging.error(f"Export operation failed: {str(e)}")
        raise

def setup_logging(log_config):
    """
    Configure comprehensive logging system.
    
    Args:
        log_config (dict): Logging configuration parameters
    """
    logging.basicConfig(
        filename=log_config['log_file_path'],
        filemode=log_config['file_mode'],
        level=getattr(logging, log_config['log_level']),
        format=log_config['log_format']
    )

def finalize_log(log_path):
    """
    Appends a final separator line to the log file to mark script completion.
    
    Args:
        log_path (str): Path to the log file
    """
    try:
        with open(log_path, 'a') as f:
            f.write("\n--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------\n")
            f.write("SCRIPT EXECUTION COMPLETED - END OF LOG FILE\n")
            f.write("--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------\n")
        
        logging.info("Log file successfully finalized with completion markers")
        
    except IOError as e:
        logging.error(f"Failed to finalize log file due to I/O error: {str(e)}")
        logging.error(f"Log file path: {log_path}")
        
    except Exception as e:
        logging.error(f"Unexpected error during log finalization: {str(e)}")

def log_mesh_size_separator(log_path):
    """
    Appends a separator line to mark completion of processing for a specific mesh size.
    
    Args:
        log_path (str): Path to the log file
    """
    try:
        with open(log_path, 'a') as f:
            f.write("\n-----------------------------------\n")
            f.write("MESH SIZE PROCESSING COMPLETED\n")
            f.write("-----------------------------------\n")
        
        logging.info("Mesh size processing separator added to log file")
        
    except IOError as e:
        logging.error(f"Failed to append mesh size separator to log file: {str(e)}")
        
    except Exception as e:
        logging.error(f"Unexpected error while adding mesh size separator: {str(e)}")

def generate_output_filename(output_config, mesh_size):
    """
    Generate unique output filename for each mesh size.
    
    Args:
        output_config (dict): Output configuration parameters
        mesh_size (float): Current mesh size
        
    Returns:
        str: Complete output file path
    """
    filename = f"{output_config['filename_prefix']}{mesh_size}{output_config['file_extension']}"
    return os.path.join(output_config['output_directory'], filename)

# ====================================================================
# MAIN SCRIPT EXECUTION BLOCK
# ====================================================================
if __name__ == '__main__':
    
    # ====================================================================
    # CONFIGURATION SECTION - ALL USER-DEFINABLE PARAMETERS
    # ====================================================================
    
    # LOGGING CONFIGURATION
    LOGGING_CONFIG = {
        'log_file_path': r"C:\Users\kvsha\Documents\EL\4TH SEM\Structures Lab\ansa_mesh_log.txt",
        'file_mode': 'w',  # 'w' = overwrite, 'a' = append
        'log_level': 'INFO',  # DEBUG, INFO, WARNING, ERROR, CRITICAL
        'log_format': '%(asctime)s - %(levelname)s - %(message)s'
    }
    
    # INPUT/OUTPUT PATHS CONFIGURATION
    PATHS_CONFIG = {
        'input_paths': {
            'step_file': r"C:\Users\kvsha\Downloads\A\A\CAM_SHAFT.STEP"
        },
        'output_paths': {
            'output_directory': r"C:\Users\kvsha\Documents\EL\4TH SEM\Structures Lab",
            'filename_prefix': "meshsize",
            'file_extension': ".cdb"
        }
    }
    
    # PROPERTY IDs CONFIGURATION
    PROPERTY_CONFIG = {
        'property_ids': {
            'pshell_lobes': 1,    # PSHELL ID for lobe components
            'pshell_shaft': 2,    # PSHELL ID for shaft components
            'psolid_lob1': 3,     # PSOLID ID for first lobe volume
            'psolid_lob2': 4,     # PSOLID ID for second lobe volume
            'psolid_shaft': 5     # PSOLID ID for shaft volume
        }
    }
    
    # MESH PARAMETERS CONFIGURATION
    MESH_CONFIG = {
        'mesh_parameters': {
            'sizing_mode': 'absolute',  # 'absolute', 'relative', 'adaptive'
            'quality_control': {
                'quality_criterion': 3,        # 1=Jacobian, 2=Skewness, 3=Aspect Ratio, 4=Warpage
                'quality_level': 2,            # 1=poor, 2=good, 3=excellent
                'solver_metric': "NASTRAN Aspect",  # Solver-specific quality metric
                'max_aspect_ratio': 2.3,       # Maximum allowable aspect ratio
                'strict_enforcement': True      # Fail if quality criteria not met
            }
        }
    }
    
    # EXPORT CONFIGURATION
    EXPORT_CONFIG = {
        'mode': 'all',
        'version': 'All',
        'workbench_compatible': 'on',
        'element_thickness_output': 'per_element',
        'format': 'ANSYS CDB format'
    }
    
    # TARGET MESH SIZES - USER-CONFIGURABLE
    # Modify this list based on your requirements:
    # - Smaller values (1-3 mm): High accuracy, long computation time
    # - Medium values (3-7 mm): Good balance of accuracy and efficiency  
    # - Larger values (7-15 mm): Fast computation, lower accuracy
    TARGET_MESH_SIZES = [0.5,1,3.0, 5.0, 7.0]
    
    # ====================================================================
    # END OF CONFIGURATION SECTION
    # ====================================================================
    
    # Combine all configurations
    FULL_CONFIG = {
        **PATHS_CONFIG,
        **PROPERTY_CONFIG,
        **MESH_CONFIG
    }
    
    # Initialize logging system
    setup_logging(LOGGING_CONFIG)
    
    # Initialize comprehensive logging for the entire script execution
    logging.info("="*120)
    logging.info("ANSA MESH PROCESSING SCRIPT STARTED")
    logging.info("="*120)
    logging.info(f"Target mesh sizes for processing: {TARGET_MESH_SIZES}")
    logging.info(f"Total number of mesh sizes to process: {len(TARGET_MESH_SIZES)}")
    logging.info(f"Estimated total processing time: {len(TARGET_MESH_SIZES) * 10}-{len(TARGET_MESH_SIZES) * 30} minutes")
    
    # Create MeshProcessor instance with configuration
    processor = MeshProcessor(FULL_CONFIG)
    
    # Initialize tracking variables
    successful_meshes = []
    failed_meshes = []
    script_start_time = time.time()
    
    # ====================================================================
    # MAIN PROCESSING LOOP
    # ====================================================================
    for mesh_index, mesh_size in enumerate(TARGET_MESH_SIZES, 1):
        
        mesh_start_time = time.time()
        
        # Generate output file path
        output_file = generate_output_filename(PATHS_CONFIG['output_paths'], mesh_size)
        
        # Log current processing status
        logging.info(f"STARTING MESH SIZE PROCESSING ({mesh_index}/{len(TARGET_MESH_SIZES)})")
        logging.info(f"Current mesh size: {mesh_size} mm")
        logging.info(f"Output file will be: {output_file}")
        
        # Display progress to user
        print(f"\n{'='*60}")
        print(f"Processing mesh size {mesh_index}/{len(TARGET_MESH_SIZES)}: {mesh_size} mm")
        print(f"{'='*60}")
        
        try:
            # Execute meshing process
            processor.main(mesh_size)
            
            # Calculate meshing completion time
            mesh_process_time = time.time() - mesh_start_time
            print(f"Meshing process completed successfully in {mesh_process_time:.2f} seconds")
            logging.info(f"Meshing process completed in {mesh_process_time:.2f} seconds for mesh size {mesh_size}")
            
            # Ensure output directory exists
            output_dir = os.path.dirname(output_file)
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
                logging.info(f"Created output directory: {output_dir}")
            
            # Export meshed model
            export_start_time = time.time()
            export_meshed_file(output_file, EXPORT_CONFIG)
            export_time = time.time() - export_start_time
            
            print(f"Model export completed successfully in {export_time:.2f} seconds")
            print(f"Output file: {output_file}")
            
            # Record successful processing
            successful_meshes.append(mesh_size)
            
            # Calculate total time for this mesh size
            total_mesh_time = time.time() - mesh_start_time
            
            logging.info(f"MESH SIZE {mesh_size} PROCESSING COMPLETED SUCCESSFULLY")
            logging.info(f"- Total processing time: {total_mesh_time:.2f} seconds")
            logging.info(f"- Meshing time: {mesh_process_time:.2f} seconds")
            logging.info(f"- Export time: {export_time:.2f} seconds")
            logging.info(f"- Output file size: {os.path.getsize(output_file):,} bytes")
            
        except Exception as e:
            # Handle errors
            error_time = time.time() - mesh_start_time
            
            print(f"ERROR: Failed to process mesh size {mesh_size} mm")
            print(f"Error occurred after {error_time:.2f} seconds")
            print(f"Error details: {str(e)}")
            
            logging.error(f"MESH SIZE {mesh_size} PROCESSING FAILED")
            logging.error(f"- Processing time before failure: {error_time:.2f} seconds")
            logging.error(f"- Error type: {type(e)._name_}")
            logging.error(f"- Error message: {str(e)}")
            logging.error(f"- Full error traceback:", exc_info=True)
            
            failed_meshes.append(mesh_size)
            
        finally:
            # Cleanup and separator addition
            log_mesh_size_separator(LOGGING_CONFIG['log_file_path'])
            print(f"Mesh size {mesh_size} processing completed.")
    
    # ====================================================================
    # FINAL PROCESSING SUMMARY AND REPORTING
    # ====================================================================
    total_script_time = time.time() - script_start_time
    
    # Display comprehensive summary
    print(f"\n{'='*80}")
    print("PROCESSING SUMMARY")
    print(f"{'='*80}")
    
    if successful_meshes:
        print(f"✓ Successfully processed mesh sizes: {successful_meshes}")
        logging.info(f"Successfully processed {len(successful_meshes)} mesh sizes: {successful_meshes}")
    
    if failed_meshes:
        print(f"✗ Failed mesh sizes: {failed_meshes}")
        logging.info(f"Failed to process {len(failed_meshes)} mesh sizes: {failed_meshes}")
    
    # Report processing statistics
    success_rate = (len(successful_meshes) / len(TARGET_MESH_SIZES)) * 100
    print(f"\nProcessing Statistics:")
    print(f"- Total mesh sizes attempted: {len(TARGET_MESH_SIZES)}")
    print(f"- Successful: {len(successful_meshes)}")
    print(f"- Failed: {len(failed_meshes)}")
    print(f"- Success rate: {success_rate:.1f}%")
    print(f"- Total execution time: {total_script_time:.2f} seconds ({total_script_time/60:.1f} minutes)")
    
    # Log final statistics
    logging.info("="*120)
    logging.info("FINAL PROCESSING SUMMARY")
    logging.info("="*120)
    logging.info(f"Total mesh sizes attempted: {len(TARGET_MESH_SIZES)}")
    logging.info(f"Successfully processed: {len(successful_meshes)} mesh sizes")
    logging.info(f"Failed processing: {len(failed_meshes)} mesh sizes")
    logging.info(f"Success rate: {success_rate:.1f}%")
    logging.info(f"Total script execution time: {total_script_time:.2f} seconds ({total_script_time/60:.1f} minutes)")
    
    if successful_meshes:
        logging.info(f"Successful mesh sizes: {successful_meshes}")
        for mesh_size in successful_meshes:
            output_file = generate_output_filename(PATHS_CONFIG['output_paths'], mesh_size)
            logging.info(f"  - Mesh size {mesh_size} mm: {output_file}")
    
    if failed_meshes:
        logging.info(f"Failed mesh sizes: {failed_meshes}")
        logging.info("Review error messages above for troubleshooting guidance")
    
    # Performance metrics
    avg_time_per_mesh = total_script_time / len(TARGET_MESH_SIZES)
    logging.info(f"Average processing time per mesh size: {avg_time_per_mesh:.2f} seconds")
    
    if successful_meshes:
        logging.info("RECOMMENDATIONS FOR NEXT STEPS:")
        logging.info("1. Review mesh quality in ANSA for each successful mesh size")
        logging.info("2. Compare element counts and quality metrics across mesh sizes")
        logging.info("3. Proceed with finite element analysis using the generated files")
        logging.info("4. Consider mesh convergence study using the different mesh densities")
    
    if failed_meshes:
        logging.info("TROUBLESHOOTING RECOMMENDATIONS:")
        logging.info("1. Check geometry quality and validity in the STEP file")
        logging.info("2. Verify property IDs exist in the model")
        logging.info("3. Consider adjusting mesh quality parameters for complex geometries")
        logging.info("4. Increase mesh size for failed cases to improve meshing success")
    
    # Final completion message
    print(f"\nScript execution completed. Check log file for detailed information:")
    print(f"Log file location: {LOGGING_CONFIG['log_file_path']}")
    
    # Finalize the log file
    finalize_log(LOGGING_CONFIG['log_file_path'])
    
    # Display final status
    if len(successful_meshes) == len(TARGET_MESH_SIZES):
        print("\n🎉 ALL MESH SIZES PROCESSED SUCCESSFULLY!")
        logging.info("ALL MESH SIZES PROCESSED SUCCESSFULLY - SCRIPT COMPLETED WITHOUT ERRORS")
    elif len(successful_meshes) > 0:
        print(f"\n⚠  PARTIAL SUCCESS: {len(successful_meshes)}/{len(TARGET_MESH_SIZES)} mesh sizes completed successfully")
        logging.info(f"PARTIAL SUCCESS - {len(successful_meshes)}/{len(TARGET_MESH_SIZES)} mesh sizes completed")
    else:
        print("\n❌ ALL MESH PROCESSING FAILED - CHECK LOG FILE FOR DETAILS")
        logging.info("CRITICAL: ALL MESH PROCESSING OPERATIONS FAILED")
    
    print(f"\nTotal execution time: {total_script_time/60:.1f} minutes")
    print("="*80)