"""Device detection and configuration for lip-sync processing."""

import logging
from typing import Literal

import torch

from ...core.config import settings
from ...core.models import DeviceInfo

logger = logging.getLogger(__name__)


def detect_device() -> DeviceInfo:
    """Detect the best available device for processing."""
    cuda_available = torch.cuda.is_available()
    cuda_device_count = torch.cuda.device_count() if cuda_available else 0
    
    if settings.device == "auto":
        if cuda_available and cuda_device_count > 0:
            device = "cuda"
            memory_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            logger.info(f"Using CUDA device with {memory_gb:.1f}GB memory")
        else:
            device = "cpu"
            memory_gb = None
            logger.info("Using CPU device (CUDA not available)")
    elif settings.device == "cuda":
        if cuda_available:
            device = "cuda"
            memory_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        else:
            device = "cpu"
            memory_gb = None
            logger.warning("CUDA requested but not available, falling back to CPU")
    else:
        device = "cpu"
        memory_gb = None
    
    return DeviceInfo(
        device=device,
        cuda_available=cuda_available,
        cuda_device_count=cuda_device_count,
        memory_gb=memory_gb
    )


def get_device() -> str:
    """Get the current device string for PyTorch."""
    device_info = detect_device()
    return device_info.device


def is_cuda_available() -> bool:
    """Check if CUDA is available."""
    return detect_device().cuda_available


def get_memory_info() -> dict:
    """Get memory information for the current device."""
    device_info = detect_device()
    
    if device_info.device == "cuda" and device_info.memory_gb:
        return {
            "total_gb": device_info.memory_gb,
            "allocated_gb": torch.cuda.memory_allocated() / (1024**3),
            "cached_gb": torch.cuda.memory_reserved() / (1024**3),
        }
    else:
        import psutil
        memory = psutil.virtual_memory()
        return {
            "total_gb": memory.total / (1024**3),
            "available_gb": memory.available / (1024**3),
            "used_gb": memory.used / (1024**3),
        }
