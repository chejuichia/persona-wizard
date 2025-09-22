"""Health check endpoints."""

import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from ..core.models import HealthResponse, DeviceInfo
from ..services.lipsync.device import detect_device, get_memory_info

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/healthz", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    try:
        return HealthResponse()
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")


@router.get("/readyz")
async def readiness_check():
    """Readiness check endpoint."""
    try:
        # Check if essential services are ready
        device_info = detect_device()
        
        # For S0, we just need basic functionality
        return JSONResponse(content={
            "ready": True,
            "device": device_info.model_dump(),
            "memory": get_memory_info(),
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "ready": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@router.get("/device")
async def get_device_info():
    """Get device information."""
    try:
        device_info = detect_device()
        memory_info = get_memory_info()
        
        return JSONResponse(content={
            "device": device_info.model_dump(),
            "memory": memory_info,
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Failed to get device info: {e}")
        raise HTTPException(status_code=500, detail="Failed to get device info")
