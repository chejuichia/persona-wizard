"""Base classes for lip-sync processing."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional

from ...core.config import settings


class LipSyncEngine(ABC):
    """Abstract base class for lip-sync engines."""
    
    def __init__(self, device: str = "cpu"):
        self.device = device
        self.config = self._get_default_config()
    
    @abstractmethod
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for the engine."""
        pass
    
    @abstractmethod
    def generate_video(self, 
                      image_path: Path, 
                      audio_path: Path, 
                      output_path: Path,
                      **kwargs) -> Dict[str, Any]:
        """Generate lip-sync video from image and audio."""
        pass


class LipSyncService(ABC):
    """Abstract base class for lip-sync services."""
    
    def __init__(self, device: str = "cpu"):
        self.device = device
        self.models_initialized = False
    
    @abstractmethod
    async def generate_video(self, 
                           face_image_path: str, 
                           audio_path: str, 
                           output_path: str,
                           progress_callback: Optional[callable] = None) -> Dict[str, Any]:
        """Generate lip-sync video from face image and audio."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the engine is available and properly configured."""
        pass
    
    def get_supported_formats(self) -> Dict[str, list]:
        """Get supported input/output formats."""
        return {
            "input_image": [".png", ".jpg", ".jpeg"],
            "input_audio": [".wav", ".mp3", ".m4a"],
            "output_video": [".mp4", ".avi", ".mov"]
        }


class LipSyncResult:
    """Result of lip-sync processing."""
    
    def __init__(self, 
                 output_path: Path,
                 duration_seconds: float,
                 size_px: int,
                 fps: int,
                 success: bool = True,
                 error: Optional[str] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        self.output_path = output_path
        self.duration_seconds = duration_seconds
        self.size_px = size_px
        self.fps = fps
        self.success = success
        self.error = error
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "output_path": str(self.output_path),
            "duration_seconds": self.duration_seconds,
            "size_px": self.size_px,
            "fps": self.fps,
            "success": self.success,
            "error": self.error,
            "metadata": self.metadata
        }
