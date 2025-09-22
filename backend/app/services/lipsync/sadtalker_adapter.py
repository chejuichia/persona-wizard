"""SadTalker adapter for lip-sync video generation."""

import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional

import cv2
import numpy as np
from PIL import Image

from .base import LipSyncEngine, LipSyncResult
from .device import get_device, is_cuda_available
from ...core.config import settings

logger = logging.getLogger(__name__)


class SadTalkerAdapter(LipSyncEngine):
    """SadTalker adapter for lip-sync video generation."""
    
    def __init__(self, device: str = "cpu"):
        super().__init__(device)
        self.device = device
        self.ckpt_dir = settings.artifacts_dir / "video" / "sadtalker_ckpts"
        self.ckpt_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for SadTalker."""
        return {
            "size": settings.sadtalker_size,
            "fps": settings.sadtalker_fps,
            "enhancer": settings.sadtalker_enhancer,
            "mode": settings.video_mode,
            "device": self.device,
            "preprocess": "crop",  # crop, resize, full
            "still": True,  # Use still image mode for better quality
            "use_enhancer": settings.sadtalker_enhancer != "off",
        }
    
    def is_available(self) -> bool:
        """Check if SadTalker is available."""
        try:
            # Check if we have the required checkpoint files
            required_files = [
                "checkpoints/auido2pose_00300-model.pth",
                "checkpoints/auido2pose_00300-model.pth",
                "checkpoints/auido2pose_00300-model.pth",
            ]
            
            # For S0, we'll create a minimal implementation that works
            # without the full SadTalker installation
            return True
        except Exception as e:
            logger.warning(f"SadTalker not available: {e}")
            return False
    
    def generate_video(self, 
                      image_path: Path, 
                      audio_path: Path, 
                      output_path: Path,
                      **kwargs) -> LipSyncResult:
        """Generate lip-sync video using SadTalker."""
        try:
            # For S0, create a simple video that demonstrates the pipeline
            # This will be replaced with actual SadTalker integration in later phases
            return self._generate_sample_video(image_path, audio_path, output_path, **kwargs)
        except Exception as e:
            logger.error(f"Failed to generate video: {e}")
            return LipSyncResult(
                output_path=output_path,
                duration_seconds=0.0,
                size_px=self.config["size"],
                fps=self.config["fps"],
                success=False,
                error=str(e)
            )
    
    def _generate_sample_video(self, 
                              image_path: Path, 
                              audio_path: Path, 
                              output_path: Path,
                              **kwargs) -> LipSyncResult:
        """Generate a sample video for S0 demonstration."""
        try:
            # Load and resize the input image
            image = Image.open(image_path)
            size = self.config["size"]
            image = image.resize((size, size), Image.Resampling.LANCZOS)
            
            # Create a simple video by duplicating the image frame
            # This is a placeholder for the actual SadTalker integration
            fps = self.config["fps"]
            duration = 3.0  # 3 seconds for short mode
            total_frames = int(fps * duration)
            
            # Create video writer
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            video_writer = cv2.VideoWriter(
                str(output_path),
                fourcc,
                fps,
                (size, size)
            )
            
            # Convert PIL image to OpenCV format
            frame = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Write frames
            for _ in range(total_frames):
                video_writer.write(frame)
            
            video_writer.release()
            
            logger.info(f"Generated sample video: {output_path}")
            
            return LipSyncResult(
                output_path=output_path,
                duration_seconds=duration,
                size_px=size,
                fps=fps,
                success=True,
                metadata={
                    "engine": "sadtalker_sample",
                    "mode": "short",
                    "enhancer": "off",
                    "device": self.device
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to generate sample video: {e}")
            return LipSyncResult(
                output_path=output_path,
                duration_seconds=0.0,
                size_px=self.config["size"],
                fps=self.config["fps"],
                success=False,
                error=str(e)
            )
    
    def _download_checkpoints(self) -> bool:
        """Download SadTalker checkpoints (placeholder for S0)."""
        # This will be implemented in later phases
        logger.info("Checkpoint download not implemented in S0")
        return True
