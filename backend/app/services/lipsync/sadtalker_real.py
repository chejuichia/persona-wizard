"""
Real SadTalker implementation for lip-sync video generation using official SadTalker package.
Following the exact step-by-step reference implementation.
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import tempfile
import shutil

# Add backend directories to path for imports
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(backend_dir.parent))

from app.services.lipsync.base import LipSyncService

logger = logging.getLogger(__name__)

class RealSadTalkerService(LipSyncService):
    """Real SadTalker service using the official sadtalker-z package."""
    
    def __init__(self):
        super().__init__()
        self.models_initialized = False
        self.preprocess_model = None
        self.audio2coeff = None
        self.animate_from_coeff = None
        self.device = "cpu"  # Force CPU usage for compatibility
        
    async def _initialize_models(self):
        """Initialize SadTalker models following the exact reference implementation."""
        if self.models_initialized:
            return
            
        try:
            import sadtalker
            from sadtalker.utils.init_path import init_path
            from sadtalker.utils.preprocess import CropAndExtract
            from sadtalker.test_audio2coeff import Audio2Coeff
            from sadtalker.facerender.animate import AnimateFromCoeff
            from sadtalker.generate_batch import get_data
            from sadtalker.generate_facerender_batch import get_facerender_data
            
            # Store functions for later use
            self.get_data = get_data
            self.get_facerender_data = get_facerender_data
            
            # Initialize paths using backend models directory
            current_root_path = os.path.split(__file__)[0]
            backend_dir = os.path.abspath(os.path.join(current_root_path, "../../.."))
            checkpoint_dir = os.path.join(backend_dir, "models", "sadtalker", "checkpoints")
            config_dir = os.path.join(backend_dir, "models", "sadtalker", "config")
            
            # Create directories if they don't exist
            os.makedirs(checkpoint_dir, exist_ok=True)
            os.makedirs(config_dir, exist_ok=True)
            
            # Initialize paths with reference parameters
            sadtalker_paths = init_path(
                checkpoint_dir, 
                config_dir, 
                size=256,  # Default size from reference
                old_version=False,  # Use new safetensor version
                preprocess='crop'  # Default preprocess mode
            )
            
            # Initialize models exactly like the reference
            self.preprocess_model = CropAndExtract(sadtalker_paths, self.device)
            self.audio2coeff = Audio2Coeff(sadtalker_paths, self.device)
            self.animate_from_coeff = AnimateFromCoeff(sadtalker_paths, self.device)
            
            self.models_initialized = True
            logger.info("✅ SadTalker models initialized successfully using reference implementation")

        except FileNotFoundError as e:
            raise RuntimeError(f"SadTalker model files not found. Please download the required models. Error: {e}")
        except ImportError as e:
            raise RuntimeError(f"SadTalker module import failed. Ensure all dependencies are installed. Error: {e}")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize SadTalker models: {e}")

    async def generate_video(self, face_image_path: str, audio_path: str, output_path: str, progress_callback=None) -> Dict[str, Any]:
        """Generate video using the exact SadTalker reference implementation."""
        try:
            if not self.models_initialized:
                await self._initialize_models()

            if progress_callback:
                progress_callback("Starting SadTalker video generation...")

            # Create temporary directory for intermediate files
            with tempfile.TemporaryDirectory() as temp_dir:
                return await self._generate_video_reference(
                    face_image_path, audio_path, output_path, temp_dir, progress_callback
                )

        except Exception as e:
            logger.error(f"❌ Error in SadTalker video generation: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise RuntimeError(f"SadTalker video generation failed: {e}")

    async def _generate_video_reference(self, face_image_path: str, audio_path: str, output_path: str, temp_dir: str, progress_callback=None) -> Dict[str, Any]:
        """Generate video following the exact SadTalker reference implementation."""
        try:
            if progress_callback:
                progress_callback("Extracting 3DMM from source image...")

            # Step 1: Extract 3DMM from source image (exactly like reference)
            first_frame_dir = os.path.join(temp_dir, 'first_frame_dir')
            os.makedirs(first_frame_dir, exist_ok=True)
            
            logger.info('3DMM Extraction for source image')
            first_coeff_path, crop_pic_path, crop_info = self.preprocess_model.generate(
                face_image_path, 
                first_frame_dir, 
                'crop',  # preprocess mode
                source_image_flag=True, 
                pic_size=256
            )
            
            if first_coeff_path is None:
                raise RuntimeError("Can't get the coeffs of the input image")

            if progress_callback:
                progress_callback("Processing audio to coefficients...")

            # Step 2: Audio to coefficients (exactly like reference)
            # No reference eyeblink for now (ref_eyeblink_coeff_path=None)
            logger.info(f"🚀 Calling get_data with: first_coeff_path={first_coeff_path}, audio_path={audio_path}, device={self.device}")
            try:
                batch = self.get_data(first_coeff_path, audio_path, self.device, None, still=False)
                logger.info(f"✅ get_data completed. Batch keys: {list(batch.keys()) if batch else 'None'}")
                if batch and 'indiv_mels' in batch:
                    logger.info(f"✅ indiv_mels shape: {batch['indiv_mels'].shape if hasattr(batch['indiv_mels'], 'shape') else 'No shape'}")
                else:
                    logger.error(f"❌ Batch missing indiv_mels key. Available keys: {list(batch.keys()) if batch else 'None'}")
            except Exception as e:
                logger.error(f"❌ Error in get_data: {e}")
                raise
            
            logger.info(f"🚀 Calling audio2coeff.generate with batch and temp_dir={temp_dir}")
            try:
                coeff_path = self.audio2coeff.generate(batch, temp_dir, 0, None)  # pose_style=0, ref_pose_coeff_path=None
                logger.info(f"✅ audio2coeff.generate completed. Coeff path: {coeff_path}")
            except Exception as e:
                logger.error(f"❌ Error in audio2coeff.generate: {e}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                raise

            if progress_callback:
                progress_callback("Generating final video...")

            # Step 3: Generate facerender data (exactly like reference)
            data = self.get_facerender_data(
                coeff_path, 
                crop_pic_path, 
                first_coeff_path, 
                audio_path,
                batch_size=2,  # Default batch size from reference
                input_yaw_list=None,
                input_pitch_list=None, 
                input_roll_list=None,
                expression_scale=1.0,
                still_mode=False,
                preprocess='crop',
                size=256
            )

            # Step 4: Generate final video (exactly like reference)
            result = self.animate_from_coeff.generate(
                data, 
                temp_dir, 
                face_image_path, 
                crop_info,
                enhancer=None,  # No enhancer for now
                background_enhancer=None,
                preprocess='crop',
                img_size=256
            )

            # Copy result to final output path
            shutil.copy2(result, output_path)

            if progress_callback:
                progress_callback("Video generation completed!")

            return {
                "status": "success",
                "output_path": output_path,
                "duration": 0,  # Could calculate actual duration if needed
                "message": "SadTalker video generation completed successfully using reference implementation"
            }

        except Exception as e:
            logger.error(f"❌ Error in reference SadTalker video generation: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise RuntimeError(f"Reference SadTalker video generation failed: {e}")

    def is_available(self) -> bool:
        """Check if SadTalker is available and properly configured."""
        try:
            return self._check_sadtalker_availability()
        except Exception as e:
            logger.error(f"Error checking SadTalker availability: {e}")
            return False